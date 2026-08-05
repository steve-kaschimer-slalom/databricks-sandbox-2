from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    allow_methods=['GET'],
    allow_headers=['*'],
)

app.include_router(databricks.router)


@app.get('/health')
def health_check() -> dict[str, str]:
    return {'status': 'ok'}
