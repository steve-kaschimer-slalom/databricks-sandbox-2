# Copilot Instructions

This is a Databricks App — a monorepo with a React/TypeScript frontend and a Python/FastAPI backend deployed on the Azure Databricks Apps platform.

Full documentation lives in `docs/`. Read `docs/architecture.md` first when starting a new session.

---

## Recommended Skills

Invoke these skills when working on the areas below — they carry workspace-specific guidance that prevents known pitfalls:

| Skill | When to use |
|---|---|
| `databricks-apps` | Any change to deployment, `app.yaml`, resource config, or the Apps platform itself |
| `databricks-apps-python` | FastAPI backend changes, SDK usage, OAuth auth, warehouse connectivity |
| `databricks-dbsql` | SQL queries, `SHOW SCHEMAS`, `information_schema`, warehouse tuning |
| `databricks-unity-catalog` | Permissions, catalog/schema grants, service principal access |
| `modern-web-guidance` | React, Tailwind, TanStack Query, frontend layout and components |

---

## Project Layout

```
app.yaml                    Databricks Apps entry point — command: ["python", "backend/run.py"]
requirements.txt            Root-level — this is what gets installed in production (not backend/requirements.txt)
frontend/src/               React SPA (Vite + TypeScript + Tailwind + TanStack Query + Recharts)
frontend/dist/              Built output — committed, served by FastAPI as static files
backend/app/config.py       Pydantic Settings — all configuration lives here
backend/app/main.py         FastAPI app, CORS, static file serving, SPA catch-all
backend/app/models.py       Pydantic response models shared with frontend types
backend/app/routers/        FastAPI routers — currently: databricks.py (/api/query, /api/schemas, /api/tables)
backend/app/services/       Business logic — currently: databricks_service.py
docs/                       Architecture, diagrams, decisions log, patterns
```

---

## Key Facts

- **Catalog:** `dbw_sandbox_sk` — this workspace does NOT have a `main` catalog. Any query against `main.*` will fail with TABLE_OR_VIEW_NOT_FOUND.
- **Warehouse ID:** `5288ab7cd99c4e09` — hardcoded as the default in `config.py`. App resource env var injection has been unreliable; do not remove this default.
- **Auth (deployed):** OAuth M2M via `DATABRICKS_CLIENT_ID` / `DATABRICKS_CLIENT_SECRET` — auto-injected by the Databricks Apps runtime. No token needed in `app.yaml` or code.
- **Auth (local):** PAT token in `backend/.env` (gitignored). `extra='ignore'` in Settings lets the SDK read `DATABRICKS_AZURE_*` vars that aren't declared on the model.
- **Frontend must be rebuilt** before deploying when any `frontend/src/` file changes: `cd frontend && npm run build`. The `dist/` folder is committed.
- **CWD at runtime** is `/app/python/source_code/` (the repo root). Use `Path(__file__).resolve()` for all file paths in Python code — never relative paths from CWD.

---

## Data Access Rules

All data access — including metadata (schemas, tables) — goes through `execute_query()` → SQL Warehouse. Do NOT use `WorkspaceClient.schemas.list()` or `WorkspaceClient.tables.list()`; the service principal lacks the UC REST API grants.

```python
SHOW SCHEMAS IN {catalog}                          # list schemas
SELECT * FROM {catalog}.information_schema.tables  # list tables with type info
```

---

## Brand / Styling

Tailwind custom colors (defined flat in `tailwind.config.js`, not nested):

| Token        | Hex       | Usage                        |
|--------------|-----------|------------------------------|
| `navy`       | `#003087` | Primary — headers, buttons   |
| `navy-dark`  | `#001f5e` | Hover states                 |
| `navy-light` | `#e6edf8` | Backgrounds, badges          |
| `gold`       | `#F5A800` | Accents, highlights          |
| `gold-dark`  | `#c98900` | Hover on gold elements       |
| `gold-light` | `#fef7e6` | Light gold backgrounds       |

Use `text-navy`, `bg-gold`, `border-navy-light`, etc. directly. Never nest under a prefix.

---

## Common Gotchas

1. **FastAPI SPA catch-all param name must match the route:** `/{full_path:path}` → `def serve_spa(full_path: str)`. An underscore prefix (`_full_path`) makes FastAPI require it as a query parameter.

2. **Mount order in FastAPI:** Register `/api` router → mount `/assets` StaticFiles → register `/{full_path:path}` catch-all. Reversing this breaks routing.

3. **`requirements.txt` location:** Databricks Apps only reads the root-level file. Adding deps only to `backend/requirements.txt` has no effect in production.

4. **`on_wait_timeout` parameter removed:** `databricks-sdk==0.28.0` does not export `CreateStatementRequestOnWaitTimeout`. Do not add this parameter to `execute_statement()`.

5. **`sessionStorage` for cross-page SQL:** Tables page writes `pendingQuery` to `sessionStorage` before navigating to `/query`. The Query page reads and clears it on mount.

6. **`lru_cache` on service functions:** `_client()` and `_resolve_warehouse_id()` are cached for the process lifetime. Do not add a `cache_clear()` call unless you have a specific reason (e.g., credential rotation).

---

## Running Locally

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py

# Frontend (separate terminal)
cd frontend
npm install
npm run dev        # Vite dev server on :5173 with proxy to :8000
```

---

## Deploying

1. If `frontend/src/` changed: `cd frontend && npm run build`
2. Commit all changes including `frontend/dist/`
3. Push to `main`
4. Trigger a redeploy from the Databricks Apps UI (or wait for auto-deploy if configured)
