import logging
from pathlib import Path

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import databricks

app = FastAPI(
    title='Databricks API',
    description='FastAPI backend for querying Azure Databricks workspace resources.',
    version='0.1.0',
)


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

