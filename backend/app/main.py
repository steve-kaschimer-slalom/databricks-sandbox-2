import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import databricks

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger(__name__)

app = FastAPI(
    title='Databricks API',
    description='FastAPI backend for querying Azure Databricks workspace resources.',
    version='0.1.0',
)


@app.on_event('startup')
def _validate_config() -> None:
    import os
    databricks_vars = {k: v[:8] + '...' if len(v) > 8 else v for k, v in os.environ.items() if 'DATABRICKS' in k.upper() or 'WAREHOUSE' in k.upper()}
    _log.info('Databricks-related env vars present: %s', databricks_vars)
    missing = [name for name, val in [
        ('DATABRICKS_HOST', settings.databricks_host),
        ('DATABRICKS_WAREHOUSE_ID', settings.databricks_warehouse_id),
    ] if not val]
    if missing:
        _log.error('Missing required configuration: %s', ', '.join(missing))
    _log.info('DATABRICKS_HOST = %s', settings.databricks_host[:30] if settings.databricks_host else '<empty>')
    _log.info('DATABRICKS_WAREHOUSE_ID = %s', settings.databricks_warehouse_id[:8] if settings.databricks_warehouse_id else '<empty>')

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=['GET', 'POST'],
    allow_headers=['*'],
)

app.include_router(databricks.router)


@app.get('/health')
def health_check() -> dict[str, str]:
    return {'status': 'ok'}


# Serve the built React frontend — path is relative to this file's location
_frontend_dist = Path(__file__).resolve().parent.parent.parent / 'frontend' / 'dist'

if _frontend_dist.exists():
    app.mount('/assets', StaticFiles(directory=_frontend_dist / 'assets'), name='assets')

    # Catch-all: return index.html so React Router handles client-side navigation
    @app.get('/{full_path:path}')
    def serve_spa(full_path: str) -> FileResponse:  # noqa: ARG001
        return FileResponse(_frontend_dist / 'index.html')

