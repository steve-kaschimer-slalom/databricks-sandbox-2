# Databricks Analytics

A full-stack [Databricks App](https://docs.databricks.com/en/dev-tools/databricks-apps/index.html) for querying and visualizing business data from Azure Databricks SQL Warehouses.

## Project Structure

```
├── app.yaml        Databricks Apps deployment config
├── frontend/       React + Vite + TypeScript + Tailwind CSS
└── backend/        Python + FastAPI + Databricks SDK
```

## How It Works

When deployed as a Databricks App, `DATABRICKS_HOST` and `DATABRICKS_TOKEN` are **automatically injected** by the runtime — no manual credential setup required in production.

The backend exposes four endpoints:

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/me` | Resolve the current user's email from the forwarded identity header |
| `POST` | `/api/query` | Execute SQL against the configured SQL Warehouse |
| `GET` | `/api/schemas?catalog=` | List schemas in a Unity Catalog |
| `GET` | `/api/tables?catalog=&schema=` | List tables in a schema |

## Frontend

**Stack:** React 18, Vite 5, TypeScript, Tailwind CSS, TanStack Query, Recharts, React Router

### Pages

- **Dashboard** — KPI cards + bar chart driven by configurable SQL queries. Replace the `SUMMARY_QUERIES` and `CHART_QUERY` constants in `DashboardPage.tsx` with your business tables.
- **Query** — Ad-hoc SQL editor with CSV export. Ctrl+Enter to run. Queries execute under the signed-in user's identity so Unity Catalog enforces their permissions.
- **Tables** — Unity Catalog browser with one-click "Query this table" shortcut.

### Setup

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
```

## Backend

**Stack:** Python 3.11+, FastAPI, Databricks SDK for Python, pydantic-settings, Uvicorn

### Local Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Set DATABRICKS_HOST, DATABRICKS_TOKEN, and DATABRICKS_WAREHOUSE_ID
python run.py    # http://localhost:8000/docs
```

### Customizing Business Queries

Add domain-specific endpoints in `backend/app/routers/databricks.py` by calling `databricks_service.execute_query(sql, user_token=x_forwarded_access_token)` with your own SQL. The service executes as the signed-in user when a forwarded access token is present (Databricks Apps injects this automatically), falling back to the service principal for local dev.

## Deploying as a Databricks App

```bash
databricks apps deploy --source-code-path .
```

The `app.yaml` at the root tells Databricks Apps to start the FastAPI backend. The Vite frontend must be built first (`npm run build`) and served as static files, or deployed separately.

