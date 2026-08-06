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
def _client() -> WorkspaceClient:
    return WorkspaceClient(
        host=settings.databricks_host or None,
        token=settings.databricks_token or None,
    )


@lru_cache(maxsize=1)
def _resolve_warehouse_id() -> str:
    """Use the configured warehouse ID, or fall back to the first available warehouse."""
    if settings.databricks_warehouse_id:
        return settings.databricks_warehouse_id
    warehouses = list(_client().warehouses.list())
    if not warehouses:
        raise RuntimeError('No SQL Warehouses found in this workspace. Create one and set DATABRICKS_WAREHOUSE_ID.')
    warehouse_id = warehouses[0].id or ''
    log.warning('DATABRICKS_WAREHOUSE_ID not set — using first available warehouse: %s (%s)', warehouses[0].name, warehouse_id)
    return warehouse_id


def execute_query(sql: str) -> QueryResultResponse:
    """Execute a SQL statement against the configured warehouse and return tabular results."""
    client = _client()
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


def list_tables(catalog: str, schema: str) -> list[TableSummary]:
    client = _client()
    tables = client.tables.list(catalog_name=catalog, schema_name=schema)
    return [
        TableSummary(
            catalog=t.catalog_name or catalog,
            schema_name=t.schema_name or schema,
            table_name=t.name or '',
            table_type=t.table_type.value if t.table_type else 'UNKNOWN',
            comment=t.comment,
        )
        for t in tables
    ]


def list_schemas(catalog: str) -> SchemaTree:
    client = _client()
    schemas = client.schemas.list(catalog_name=catalog)
    return SchemaTree(
        catalog=catalog,
        schemas=[s.name or '' for s in schemas],
    )

