# Architecture

## Overview

A monorepo Databricks App consisting of a React/TypeScript SPA served by a Python/FastAPI backend. The backend executes SQL against an Azure Databricks SQL Warehouse and returns results to the frontend over a REST API.

The app is deployed on the **Databricks Apps** platform, which handles hosting, TLS, and OAuth M2M credential injection.

---

## Repository Structure

```
databricks-sandbox-2/
├── app.yaml                  # Databricks Apps entry point
├── requirements.txt          # Runtime deps (Databricks Apps reads from repo root)
├── frontend/
│   ├── src/
│   │   ├── api/              # Axios API client functions
│   │   ├── components/       # Shared UI components
│   │   ├── pages/            # Route-level page components
│   │   └── types/            # TypeScript interfaces mirroring backend models
│   └── dist/                 # Built output — committed and served by FastAPI
└── backend/
    ├── run.py                # Uvicorn entry point (referenced by app.yaml)
    └── app/
        ├── config.py         # Pydantic settings — reads env vars / .env
        ├── main.py           # FastAPI app, CORS, static file serving
        ├── models.py         # Pydantic response models
        ├── routers/
        │   └── databricks.py # /api/query, /api/schemas, /api/tables endpoints
        └── services/
            └── databricks_service.py  # SDK client + SQL execution logic
```

---

## Component Diagram

```mermaid
graph TD
    Browser["Browser (React SPA)"]
    FastAPI["FastAPI\n(backend/app/main.py)"]
    Router["API Router\n(/api/*)"]
    Service["DatabricksService\n(databricks_service.py)"]
    Warehouse["Azure Databricks\nSQL Warehouse"]
    UC["Unity Catalog\n(dbw_sandbox_sk)"]

    Browser -- "GET /  →  index.html" --> FastAPI
    Browser -- "GET /assets/*" --> FastAPI
    Browser -- "POST /api/query\nGET /api/schemas\nGET /api/tables" --> Router
    Router --> Service
    Service -- "statement_execution.execute_statement()" --> Warehouse
    Warehouse -- "SHOW SCHEMAS / SHOW TABLES / ad-hoc SQL" --> UC
    UC -- "result rows" --> Warehouse
    Warehouse -- "QueryResultResponse" --> Service
    Service --> Router
    Router -- "JSON" --> Browser
```

---

## Runtime Deployment

```
Databricks Apps platform
└── app.yaml  →  python backend/run.py
                 CWD: /app/python/source_code/
                 │
                 ├── uvicorn starts FastAPI on 0.0.0.0:8000
                 ├── frontend/dist/ is served as static files
                 └── auto-injected env vars:
                     DATABRICKS_HOST
                     DATABRICKS_CLIENT_ID       (OAuth M2M)
                     DATABRICKS_CLIENT_SECRET   (OAuth M2M)
```

**Critical:** `requirements.txt` must live at the **repo root** — the Databricks Apps runtime only reads from there, not from `backend/requirements.txt`.

---

## Authentication

| Context        | Mechanism                                       |
|----------------|-------------------------------------------------|
| Local dev      | `DATABRICKS_TOKEN` (PAT) in `backend/.env`      |
| Deployed app   | OAuth M2M via `DATABRICKS_CLIENT_ID` / `DATABRICKS_CLIENT_SECRET` auto-injected by the platform |

The Databricks Python SDK auto-detects credentials from environment variables using its built-in credential chain — no explicit auth code needed.

---

## Frontend → Backend Contract

All API calls use a relative base URL (`/api`) so they route through the same FastAPI process in both local dev (Vite proxy) and production (same-process serving).

| Endpoint              | Method | Purpose                              |
|-----------------------|--------|--------------------------------------|
| `/api/query`          | POST   | Execute ad-hoc SQL, return rows      |
| `/api/schemas`        | GET    | List schemas in a catalog            |
| `/api/tables`         | GET    | List tables in a catalog.schema      |
| `/health`             | GET    | Liveness check                       |

---

## Key Configuration

All settings live in `backend/app/config.py` as a Pydantic `BaseSettings` model.

| Setting                    | Default          | Source                        |
|----------------------------|------------------|-------------------------------|
| `databricks_host`          | `''`             | Env / `.env`                  |
| `databricks_token`         | `''`             | Env / `.env` (local only)     |
| `databricks_warehouse_id`  | `5288ab7cd99c4e09` | Hardcoded default (App resource injection unreliable) |
| `databricks_catalog`       | `dbw_sandbox_sk` | Hardcoded default             |
| `api_host`                 | `0.0.0.0`        | Env                           |
| `api_port`                 | `8000`           | Env                           |
