import logging
import time
from functools import lru_cache
from typing import Any

import requests
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

from app.config import settings
from app.models import QueryResultResponse, TableSummary, SchemaTree

log = logging.getLogger(__name__)


# user_token -> (sql_scoped_token, monotonic_expiry)
_token_exchange_cache: dict[str, tuple[str, float]] = {}


def _exchange_token_for_sql_scope(user_token: str) -> str | None:
    """RFC 8693 token exchange: swap the forwarded token for one with the sql scope."""
    client_id = settings.databricks_client_id
    client_secret = settings.databricks_client_secret
    if not client_id or not client_secret:
        return None
    now = time.monotonic()
    cached = _token_exchange_cache.get(user_token)
    if cached and now < cached[1]:
        return cached[0]
    resp = requests.post(
        f'{_host()}/oidc/v1/token',
        data={
            'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
            'subject_token': user_token,
            'subject_token_type': 'urn:ietf:params:oauth:token-type:access_token',
            'requested_token_type': 'urn:ietf:params:oauth:token-type:access_token',
            'scope': 'sql',
        },
        auth=(client_id, client_secret),
        timeout=10,
    )
    if not resp.ok:
        log.debug('Token exchange failed %s: %s', resp.status_code, resp.text)
        return None
    sql_token = resp.json().get('access_token')
    if sql_token:
        _token_exchange_cache[user_token] = (sql_token, now + 55 * 60)  # re-exchange before 1h expiry
    return sql_token


# Keyed by Databricks internal user ID; populated on first request per user
_user_identity_cache: dict[str, str] = {}


def resolve_user_identity(forwarded_user: str, access_token: str | None = None) -> str:
    if forwarded_user in _user_identity_cache:
        return _user_identity_cache[forwarded_user]
    if access_token:
        try:
            # Direct SCIM call avoids SDK credential-conflict validation
            host = settings.databricks_host.rstrip('/')
            if not host.startswith('http'):
                host = f'https://{host}'
            url = f'{host}/api/2.0/preview/scim/v2/Me'
            resp = requests.get(url, headers={'Authorization': f'Bearer {access_token}'}, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            resolved = data.get('userName') or data.get('displayName') or forwarded_user
            _user_identity_cache[forwarded_user] = resolved
            return resolved
        except Exception as exc:
            log.warning('Could not resolve user identity for %s: %s', forwarded_user, exc)
    _user_identity_cache[forwarded_user] = forwarded_user
    return forwarded_user


@lru_cache(maxsize=1)
def _host() -> str:
    host = settings.databricks_host.rstrip('/')
    return host if host.startswith('http') else f'https://{host}'


@lru_cache(maxsize=1)
def _sp_client() -> WorkspaceClient:
    # Service principal client — used only for warehouse discovery and local dev fallback
    return WorkspaceClient(
        host=settings.databricks_host or None,
        token=settings.databricks_token or None,
    )


@lru_cache(maxsize=1)
def _resolve_warehouse_id() -> str:
    if settings.databricks_warehouse_id:
        return settings.databricks_warehouse_id
    warehouses = list(_sp_client().warehouses.list())
    if not warehouses:
        raise RuntimeError('No SQL Warehouses found in this workspace. Create one and set DATABRICKS_WAREHOUSE_ID.')
    warehouse_id = warehouses[0].id or ''
    log.warning('DATABRICKS_WAREHOUSE_ID not set — using first available warehouse: %s (%s)', warehouses[0].name, warehouse_id)
    return warehouse_id


def execute_query(sql: str, user_token: str | None = None) -> QueryResultResponse:
    if user_token:
        sql_token = _exchange_token_for_sql_scope(user_token) or user_token
        try:
            return _execute_as_user(sql, sql_token)
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 403:
                log.warning('User token missing sql scope, falling back to SP for query execution')
                return _execute_as_sp(sql)
            raise
    # Local dev fallback — no forwarded token present
    return _execute_as_sp(sql)


def _execute_as_user(sql: str, access_token: str) -> QueryResultResponse:
    warehouse_id = _resolve_warehouse_id()
    start = time.monotonic()
    resp = requests.post(
        f'{_host()}/api/2.0/sql/statements',
        json={'warehouse_id': warehouse_id, 'statement': sql, 'wait_timeout': '30s'},
        headers={'Authorization': f'Bearer {access_token}'},
        timeout=35,
    )
    if not resp.ok:
        log.debug('Statement Execution API %s: %s', resp.status_code, resp.text)
        resp.raise_for_status()
    data = resp.json()
    state = data.get('status', {}).get('state', '')
    if state != 'SUCCEEDED':
        error = data.get('status', {}).get('error', {})
        raise RuntimeError(f"Query failed: {error.get('message', state)}")
    elapsed_ms = int((time.monotonic() - start) * 1000)
    columns = [col['name'] for col in data.get('manifest', {}).get('schema', {}).get('columns', [])]
    rows = [list(row) for row in data.get('result', {}).get('data_array', []) or []]
    return QueryResultResponse(columns=columns, rows=rows, row_count=len(rows), execution_time_ms=elapsed_ms)


def _execute_as_sp(sql: str) -> QueryResultResponse:
    client = _sp_client()
    warehouse_id = _resolve_warehouse_id()
    start = time.monotonic()
    response = client.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql,
        wait_timeout='30s',
    )

    if response.status and response.status.state not in (
        StatementState.SUCCEEDED,
    ):
        error_msg = (
            response.status.error.message
            if response.status.error
            else str(response.status.state)
        )
        raise RuntimeError(f'Query failed: {error_msg}')

    elapsed_ms = int((time.monotonic() - start) * 1000)
    manifest = response.manifest
    result = response.result

    columns: list[str] = []
    if manifest and manifest.schema and manifest.schema.columns:
        columns = [col.name or '' for col in manifest.schema.columns]

    rows: list[list[Any]] = []
    if result and result.data_array:
        rows = [list(row) for row in result.data_array]

    return QueryResultResponse(
        columns=columns,
        rows=rows,
        row_count=len(rows),
        execution_time_ms=elapsed_ms,
    )


def list_tables(catalog: str, schema: str, user_token: str | None = None) -> list[TableSummary]:
    sql = f"SELECT table_catalog, table_schema, table_name, table_type, comment FROM {catalog}.information_schema.tables WHERE table_schema = '{schema}' ORDER BY table_name"
    result = execute_query(sql, user_token=user_token)
    col = {name: idx for idx, name in enumerate(result.columns)}
    return [
        TableSummary(
            catalog=row[col['table_catalog']],
            schema_name=row[col['table_schema']],
            table_name=row[col['table_name']],
            table_type=row[col['table_type']],
            comment=row[col['comment']] if col.get('comment') is not None else None,
        )
        for row in result.rows
    ]


def list_schemas(catalog: str, user_token: str | None = None) -> SchemaTree:
    # SHOW SCHEMAS requires no information_schema privileges
    result = execute_query(f'SHOW SCHEMAS IN {catalog}', user_token=user_token)
    name_idx = result.columns.index('databaseName') if 'databaseName' in result.columns else 0
    return SchemaTree(
        catalog=catalog,
        schemas=[row[name_idx] for row in result.rows],
    )

