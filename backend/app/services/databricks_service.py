"""
SQL execution service for Databricks Apps.

DATABRICKS_HOST and DATABRICKS_TOKEN are auto-injected by the Databricks Apps
runtime. WorkspaceClient() with no arguments picks them up via the SDK's
unified credential chain.
"""
import time
from functools import lru_cache
from typing import Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

from app.config import settings
from app.models import QueryResultResponse, TableSummary, SchemaTree


@lru_cache(maxsize=1)
def _client() -> WorkspaceClient:
    return WorkspaceClient(
        host=settings.databricks_host or None,
        token=settings.databricks_token or None,
    )


def execute_query(sql: str) -> QueryResultResponse:
    """Execute a SQL statement against the configured warehouse and return tabular results."""
    client = _client()
    start = time.monotonic()

    response = client.statement_execution.execute_statement(
        warehouse_id=settings.databricks_warehouse_id,
        statement=sql,
        wait_timeout='30s',
        on_wait_timeout='CANCEL',
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

