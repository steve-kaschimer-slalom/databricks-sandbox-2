# Patterns Repository

Reusable patterns established in this codebase. Reference these when extending the app or starting similar Databricks App projects.

---

## Pattern 1 — SQL-routed data access

**Problem:** The Databricks SDK's Unity Catalog REST methods (`schemas.list()`, `tables.list()`) require separate UC grants that a service principal may not have, even if it has full SQL Warehouse access.

**Solution:** Route all data access — including metadata queries — through `execute_query()` using standard SQL.

```python
# schemas
SHOW SCHEMAS IN {catalog}                                   # returns databaseName column
# tables
SELECT * FROM {catalog}.information_schema.tables
WHERE table_schema = '{schema}'
# ad-hoc
SELECT * FROM {catalog}.{schema}.{table} LIMIT 100
```

**When to use:** Any time you need catalog/schema/table metadata and cannot guarantee the SP has explicit UC REST privileges.

---

## Pattern 2 — Warehouse-backed service with `@lru_cache` client

**Problem:** Creating a `WorkspaceClient` on every request is wasteful; the SDK credential chain runs on every instantiation.

**Solution:** Cache the client and the resolved warehouse ID with `@lru_cache(maxsize=1)`.

```python
from functools import lru_cache
from databricks.sdk import WorkspaceClient

@lru_cache(maxsize=1)
def _client() -> WorkspaceClient:
    return WorkspaceClient()   # SDK reads DATABRICKS_* env vars automatically

@lru_cache(maxsize=1)
def _resolve_warehouse_id() -> str:
    if settings.databricks_warehouse_id:
        return settings.databricks_warehouse_id
    warehouses = list(_client().warehouses.list())
    if not warehouses:
        raise RuntimeError('No SQL Warehouses available')
    return warehouses[0].id
```

**Note:** `lru_cache` on module-level functions means the cache lives for the process lifetime. Fine for a single-process app; would need invalidation logic if credentials rotate in a long-running service.

---

## Pattern 3 — FastAPI SPA hosting

**Problem:** Databricks Apps runs a single process; there's no separate static hosting.

**Solution:** Mount the built React `dist/assets/` as `StaticFiles` and add a catch-all route that returns `index.html` for all unmatched GET paths.

```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

_dist = Path(__file__).resolve().parent.parent.parent / 'frontend' / 'dist'

if _dist.exists():
    app.mount('/assets', StaticFiles(directory=_dist / 'assets'), name='assets')

    @app.get('/{full_path:path}')
    def serve_spa(full_path: str) -> FileResponse:  # noqa: ARG001
        return FileResponse(_dist / 'index.html')
```

**Critical gotcha:** The parameter name `full_path` must exactly match the path variable `{full_path:path}`. A leading underscore (`_full_path`) causes FastAPI to treat it as a required query parameter, returning `{"detail":[{"type":"missing","loc":["query","_full_path"]}]}`.

**Mount order matters:** The `/assets` mount must be registered before the catch-all route, and all `/api` routes must be registered before the catch-all.

---

## Pattern 4 — Databricks Apps `requirements.txt` placement

**Problem:** Databricks Apps installs Python dependencies from the `requirements.txt` at the **repo root**, not from a subdirectory.

**Solution:** Keep a `requirements.txt` at the repo root with all backend dependencies. The `backend/requirements.txt` can mirror it for local dev tooling.

```
# repo root requirements.txt — this is what gets installed in production
fastapi
uvicorn[standard]
databricks-sdk
pydantic-settings
...
```

---

## Pattern 5 — Pydantic Settings with SDK passthrough vars

**Problem:** `backend/.env` contains `DATABRICKS_AZURE_*` vars that the SDK reads directly but that are not declared on the `Settings` model — causing Pydantic `ValidationError` on startup.

**Solution:** Set `extra='ignore'` in `SettingsConfigDict`.

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    databricks_host: str = ''
    databricks_token: str = ''
    # ...

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',          # SDK reads DATABRICKS_AZURE_* directly; don't declare them here
    )
```

---

## Pattern 6 — Frontend query pre-population via `sessionStorage`

**Problem:** Navigating from a table browser to a query editor requires passing SQL state across routes without polluting URL parameters or global state.

**Solution:** Write the SQL to `sessionStorage` before navigating; the Query page reads and clears it on mount.

```typescript
// TablesPage.tsx — producer
function openInQuery(tableFqn: string) {
    sessionStorage.setItem('pendingQuery', `SELECT *\nFROM ${tableFqn}\nLIMIT 100`)
    navigate('/query')
}

// QueryPage.tsx — consumer
const [sql, setSql] = useState(() => {
    const pending = sessionStorage.getItem('pendingQuery')
    if (pending) {
        sessionStorage.removeItem('pendingQuery')
        return pending
    }
    return ''
})
```

---

## Pattern 7 — Column-index access for SQL result rows

**Problem:** SQL result rows from `execute_query()` are `list[list[Any]]` — accessing by position is fragile if column order changes.

**Solution:** Build a column-name-to-index map from the returned `columns` list before iterating rows.

```python
result = execute_query(sql)
col = {name: idx for idx, name in enumerate(result.columns)}

rows = [
    SomeModel(
        name=row[col['table_name']],
        kind=row[col['table_type']],
    )
    for row in result.rows
]
```

---

## Pattern 8 — Databricks Apps `app.yaml` path resolution

**Problem:** The Databricks Apps runtime sets CWD to `/app/python/source_code/` — not the repo root — so relative paths in `app.yaml` must account for this.

**Solution:** Reference the backend entry point with its full path from the repo root.

```yaml
# app.yaml
command: ["python", "backend/run.py"]   # relative to /app/python/source_code/ which IS the repo root
```

Inside Python code, use `Path(__file__).resolve()` to build absolute paths rather than relying on CWD.

```python
# Resolves correctly regardless of CWD
_dist = Path(__file__).resolve().parent.parent.parent / 'frontend' / 'dist'
```

---

## Pattern 9 — User-scoped query execution with SP fallback

**Problem:** Queries run as the service principal bypass Unity Catalog per-user permissions. Running as the user requires a bearer token, but the Databricks SDK raises a credential-conflict error when a token is passed alongside the injected M2M credentials.

**Solution:** Use `requests` directly for user-scoped calls; fall back to the SDK service principal path when no forwarded token is present (local dev) or on 403.

```python
import requests

def execute_query(sql: str, user_token: str | None = None) -> QueryResultResponse:
    if user_token:
        try:
            return _execute_as_user(sql, user_token)
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 403:
                # Token missing sql scope — degrade gracefully
                return _execute_as_sp(sql)
            raise
    return _execute_as_sp(sql)

def _execute_as_user(sql: str, access_token: str) -> QueryResultResponse:
    resp = requests.post(
        f'{_host()}/api/2.0/sql/statements',
        json={'warehouse_id': _resolve_warehouse_id(), 'statement': sql, 'wait_timeout': '30s'},
        headers={'Authorization': f'Bearer {access_token}'},
        timeout=35,
    )
    resp.raise_for_status()
    ...
```

**When to use:** Any FastAPI endpoint that executes SQL on behalf of a Databricks Apps user. Pass `x_forwarded_access_token: str | None = Header(default=None)` and thread it through to the service.

**Prerequisite:** User Authorization must be enabled in the Databricks Apps UI settings **and** the `app.yaml` must declare the SQL warehouse as a resource with `CAN_USE` to include the `sql` scope in the forwarded token.

---

## Pattern 10 — User identity resolution via SCIM /Me

**Problem:** `X-Forwarded-User` contains an opaque internal Databricks user ID (e.g. `436568226980462@7405615634530034`), not a human-readable email.

**Solution:** Call `GET /api/2.0/preview/scim/v2/Me` with the forwarded access token and cache the result by internal ID for the process lifetime.

```python
_user_identity_cache: dict[str, str] = {}

def resolve_user_identity(forwarded_user: str, access_token: str | None = None) -> str:
    if forwarded_user in _user_identity_cache:
        return _user_identity_cache[forwarded_user]
    if access_token:
        host = settings.databricks_host.rstrip('/')
        if not host.startswith('http'):
            host = f'https://{host}'
        resp = requests.get(
            f'{host}/api/2.0/preview/scim/v2/Me',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        resolved = data.get('userName') or data.get('displayName') or forwarded_user
        _user_identity_cache[forwarded_user] = resolved
        return resolved
    _user_identity_cache[forwarded_user] = forwarded_user
    return forwarded_user
```

**When to use:** Any time you need to log or display who is performing an action. The internal user ID is not meaningful to operators reading logs.

**Note:** The `databricks_host` env var is stored without a scheme (`adb-XXXX.azuredatabricks.net`). Always prepend `https://` before building the URL.
