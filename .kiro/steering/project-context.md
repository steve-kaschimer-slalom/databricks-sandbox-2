---
inclusion: always
---

# Project Context

This is a **Databricks App** monorepo — a React/TypeScript SPA served by a Python/FastAPI backend, deployed on the Azure Databricks Apps platform.

Read this file at the start of every session. It captures workspace-specific facts that prevent common mistakes.

---

## Repository Layout

```
app.yaml                    Databricks Apps entry point → command: ["python", "backend/run.py"]
requirements.txt            Root-level only — this is what Databricks Apps installs in production
frontend/src/               React SPA (Vite + TypeScript + Tailwind + TanStack Query + Recharts)
frontend/dist/              Built output — committed to repo, served by FastAPI as static files
backend/app/config.py       Pydantic Settings — all configuration here
backend/app/main.py         FastAPI app, CORS, static file serving, SPA catch-all
backend/app/models.py       Pydantic response models (mirrored by frontend/src/types/databricks.ts)
backend/app/routers/        FastAPI routers — databricks.py (/api/me, /api/query, /api/schemas, /api/tables)
backend/app/services/       Business logic — databricks_service.py
docs/                       Architecture, decisions (ADRs), patterns, diagrams — treat as long-term memory
```

---

## Workspace-Specific Constants

| Fact | Value |
|---|---|
| **Default catalog** | `dbw_sandbox_sk` — this workspace does NOT have a `main` catalog. Any query against `main.*` will fail. |
| **Warehouse ID** | `5288ab7cd99c4e09` — hardcoded default in `config.py` and `app.yaml`. App resource env var injection has been unreliable; do not remove this default. |
| **App name** | Kaschimer — Databricks Analytics |

---

## Authentication

| Context | Mechanism |
|---|---|
| **Deployed** | OAuth M2M via `DATABRICKS_CLIENT_ID` / `DATABRICKS_CLIENT_SECRET` — auto-injected by the Databricks Apps runtime. No token needed in `app.yaml` or code. |
| **Local dev** | PAT token (`DATABRICKS_TOKEN`) in `backend/.env` (gitignored). |

The Databricks Python SDK auto-detects credentials from env vars — no explicit auth code needed.

### Per-user query execution (deployed)

When **User Authorization** is enabled in the Databricks Apps UI:
- `X-Forwarded-User` — opaque internal Databricks user ID
- `X-Forwarded-Access-Token` — short-lived OAuth token scoped to the signed-in user, including the `sql` scope

Every query runs as the end user; Unity Catalog enforces their grants. The SP is a fallback only.

**Important:** The Databricks SDK raises a credential-conflict error when `token=user_token` is passed while `DATABRICKS_CLIENT_ID`/`DATABRICKS_CLIENT_SECRET` are in the environment. All user-scoped HTTP calls therefore use `requests` directly — not the SDK.

---

## Data Access Rules

All data access — **including metadata** (schemas, tables) — goes through `execute_query()` → SQL Warehouse. Do NOT use `WorkspaceClient.schemas.list()` or `WorkspaceClient.tables.list()`; the service principal lacks the UC REST API grants.

```python
# List schemas
SHOW SCHEMAS IN {catalog}                                       # returns 'databaseName' column

# List tables
SELECT * FROM {catalog}.information_schema.tables
WHERE table_schema = '{schema}'
ORDER BY table_name
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/me` | GET | Resolve current user email via SCIM /Me |
| `/api/query` | POST | Execute ad-hoc SQL as the signed-in user |
| `/api/schemas` | GET | List schemas in a catalog |
| `/api/tables` | GET | List tables in a catalog.schema |
| `/health` | GET | Liveness check |

All frontend API calls use relative `/api` base URL — no hardcoded host anywhere in frontend code.

---

## Local Development

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r ../requirements.txt
python run.py                   # starts on :8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                     # Vite dev server on :5173, proxies /api → :8000
```

---

## Deploying

1. If any `frontend/src/` file changed: `cd frontend && npm run build`
2. Commit all changes **including `frontend/dist/`**
3. Push to `main`
4. Trigger a redeploy from the Databricks Apps UI (or wait for auto-deploy if configured)

---

## Common Gotchas

1. **`requirements.txt` must be at repo root.** Databricks Apps only reads the root-level file. Adding deps only to `backend/requirements.txt` has no effect in production.

2. **FastAPI SPA catch-all param name must match the route exactly.** `/{full_path:path}` → `def serve_spa(full_path: str)`. A leading underscore (`_full_path`) makes FastAPI treat it as a required query parameter.

3. **FastAPI mount order matters.** Register `/api` router first → mount `/assets` StaticFiles → register `/{full_path:path}` catch-all last. Reversing this breaks routing.

4. **`on_wait_timeout` removed.** `databricks-sdk==0.28.0` does not export `CreateStatementRequestOnWaitTimeout`. Do not add this parameter to `execute_statement()`.

5. **`sessionStorage` for cross-page SQL.** `TablesPage` writes `pendingQuery` to `sessionStorage` before navigating to `/query`. `QueryPage` reads and clears it on mount.

6. **`lru_cache` on service functions.** `_sp_client()` and `_resolve_warehouse_id()` are cached for the process lifetime. Do not add a `cache_clear()` call unless credential rotation is explicitly needed.

7. **`DATABRICKS_HOST` is stored without scheme.** Always prepend `https://` before building URLs manually: `host = settings.databricks_host.rstrip('/'); host = host if host.startswith('http') else f'https://{host}'`.

8. **Use `Path(__file__).resolve()` for all file paths in Python.** The CWD at Databricks Apps runtime is `/app/python/source_code/` — never rely on relative paths from CWD.

---

## Key Design Decisions (summary — full ADRs in `docs/decisions.md`)

- **Databricks Apps deployment** — auth, TLS, and hosting handled by platform; no Azure infra to manage.
- **FastAPI serves the React frontend** — single process, no CORS complexity, `dist/` committed and mounted as StaticFiles.
- **SQL-based schema/table discovery** — SP lacks UC REST API grants; all metadata queries go through the warehouse.
- **`requests` for user-scoped calls** — SDK raises credential-conflict when passed a user token alongside injected M2M creds.
- **`extra='ignore'` on Pydantic Settings** — prevents `ValidationError` from `DATABRICKS_AZURE_*` vars in `.env` that the SDK reads directly.

---

## Skills to Invoke by Task

When working in these areas, load the corresponding skill for workspace-specific guidance before proceeding.

| Task area | Skill |
|---|---|
| Deployment, `app.yaml`, resource config, Apps platform | `databricks-apps` |
| FastAPI backend, Databricks SDK, auth, warehouse connectivity | `databricks-apps-python` |
| SQL queries, `information_schema`, warehouse tuning, stored procedures | `databricks-dbsql` |
| Unity Catalog permissions, GRANT/REVOKE, row/column security | `databricks-unity-catalog` |
| React, Tailwind, TanStack Query, Recharts, frontend components | `modern-web-guidance` |
| Databricks Jobs, DABs, multi-task DAGs, triggers | `databricks-jobs` |
| Lakebase (Postgres), branching, synced tables | `databricks-lakebase` |
| Managed ingestion pipelines (Salesforce, SQL Server, etc.) | `databricks-lakeflow-connect` |
| Clusters, serverless compute, Databricks Connect | `databricks-execution-compute` |
| CLI, profile management, workspace exploration | `databricks-core` |
| Looking up official Databricks documentation | `databricks-docs` |
| UX design, KPI screens, chart layout, IBCS notation | `databricks-app-design` |
