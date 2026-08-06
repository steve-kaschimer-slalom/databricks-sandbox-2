import logging
import time
from functools import lru_cache
from typing import Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

from app.config import settings
from app.models import QueryResultResponse, TableSummary, SchemaTree

log = logging.getLogger(__name__)


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


def execute_query(sql: str, user_token: str | None = None) -> QueryResultResponse:  # noqa: ARG001 — user_token reserved for future per-user UC enforcement
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


def list_tables(catalog: str, schema: str, user_token: str | None = None) -> list[TableSummary]:  # noqa: ARG001
    sql = f"SELECT table_catalog, table_schema, table_name, table_type, comment FROM {catalog}.information_schema.tables WHERE table_schema = '{schema}' ORDER BY table_name"
    result = execute_query(sql)
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


def list_schemas(catalog: str, user_token: str | None = None) -> SchemaTree:  # noqa: ARG001
    # SHOW SCHEMAS requires no information_schema privileges
    result = execute_query(f'SHOW SCHEMAS IN {catalog}')
    name_idx = result.columns.index('databaseName') if 'databaseName' in result.columns else 0
    return SchemaTree(
        catalog=catalog,
        schemas=[row[name_idx] for row in result.rows],
    )

