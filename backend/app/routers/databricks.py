import logging

from fastapi import APIRouter, Header, HTTPException, Query

from app.models import QueryResultResponse, TableSummary, SchemaTree
from app.services import databricks_service

log = logging.getLogger(__name__)

router = APIRouter(prefix='/api', tags=['data'])


@router.get('/me')
def me(
    x_forwarded_user: str | None = Header(default=None),
    remote_user: str | None = Header(default=None),
    x_databricks_user: str | None = Header(default=None),
    x_forwarded_access_token: str | None = Header(default=None),
) -> dict:
    raw_identity = x_forwarded_user or remote_user or x_databricks_user
    log.info('Identity headers — X-Forwarded-User: %s  Remote-User: %s  X-Databricks-User: %s', x_forwarded_user, remote_user, x_databricks_user)
    if raw_identity:
        email = databricks_service.resolve_user_identity(raw_identity, access_token=x_forwarded_access_token)
    else:
        email = None
    return {'email': email}


@router.post('/query', response_model=QueryResultResponse)
def run_query(
    body: dict,
    x_forwarded_access_token: str | None = Header(default=None),
    x_forwarded_user: str | None = Header(default=None),
) -> QueryResultResponse:
    sql: str = body.get('sql', '').strip()
    if not sql:
        raise HTTPException(status_code=400, detail='`sql` field is required')
    if x_forwarded_user:
        log.info('Query submitted by %s', databricks_service.resolve_user_identity(x_forwarded_user, access_token=x_forwarded_access_token))
    try:
        return databricks_service.execute_query(sql, user_token=x_forwarded_access_token)
    except RuntimeError as exc:
        log.error('Query failed: %s', exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        log.exception('Unexpected error executing query')
        raise HTTPException(status_code=502, detail=f'Databricks error: {exc}') from exc


@router.get('/schemas', response_model=SchemaTree)
def schemas(
    catalog: str = Query(default='dbw_sandbox_sk'),
    x_forwarded_access_token: str | None = Header(default=None),
) -> SchemaTree:
    try:
        return databricks_service.list_schemas(catalog, user_token=x_forwarded_access_token)
    except Exception as exc:
        log.exception('Error fetching schemas for catalog=%s', catalog)
        raise HTTPException(status_code=502, detail=f'Databricks error: {exc}') from exc


@router.get('/tables', response_model=list[TableSummary])
def tables(
    catalog: str = Query(default='dbw_sandbox_sk'),
    schema: str = Query(...),
    x_forwarded_access_token: str | None = Header(default=None),
) -> list[TableSummary]:
    try:
        return databricks_service.list_tables(catalog, schema, user_token=x_forwarded_access_token)
    except Exception as exc:
        log.exception('Error fetching tables for %s.%s', catalog, schema)
        raise HTTPException(status_code=502, detail=f'Databricks error: {exc}') from exc

