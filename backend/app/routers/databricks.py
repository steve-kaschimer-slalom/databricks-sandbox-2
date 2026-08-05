import logging

from fastapi import APIRouter, HTTPException, Query

from app.models import QueryResultResponse, TableSummary, SchemaTree
from app.services import databricks_service

log = logging.getLogger(__name__)

router = APIRouter(prefix='/api', tags=['data'])


@router.post('/query', response_model=QueryResultResponse)
def run_query(body: dict) -> QueryResultResponse:
    """Execute an ad-hoc SQL statement against the configured SQL Warehouse."""
    sql: str = body.get('sql', '').strip()
    if not sql:
        raise HTTPException(status_code=400, detail='`sql` field is required')
    try:
        return databricks_service.execute_query(sql)
    except RuntimeError as exc:
        log.error('Query failed: %s', exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        log.exception('Unexpected error executing query')
        raise HTTPException(status_code=502, detail=f'Databricks error: {exc}') from exc


@router.get('/schemas', response_model=SchemaTree)
def schemas(catalog: str = Query(default='main')) -> SchemaTree:
    """List all schemas within a catalog."""
    try:
        return databricks_service.list_schemas(catalog)
    except Exception as exc:
        log.exception('Error fetching schemas for catalog=%s', catalog)
        raise HTTPException(status_code=502, detail=f'Databricks error: {exc}') from exc


@router.get('/tables', response_model=list[TableSummary])
def tables(
    catalog: str = Query(default='main'),
    schema: str = Query(...),
) -> list[TableSummary]:
    """List all tables within a catalog.schema."""
    try:
        return databricks_service.list_tables(catalog, schema)
    except Exception as exc:
        log.exception('Error fetching tables for %s.%s', catalog, schema)
        raise HTTPException(status_code=502, detail=f'Databricks error: {exc}') from exc

        raise HTTPException(status_code=502, detail=f'Databricks error: {exc}') from exc

