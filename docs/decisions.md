# Decisions Log

Architectural and implementation decisions made during the initial build, with rationale and trade-offs noted.

---

## ADR-001 — Databricks Apps as the deployment target

**Date:** 2026-08  
**Status:** Adopted

**Decision:** Deploy as a Databricks App on the Azure Databricks Apps platform rather than as a standalone Azure service (App Service, Container Apps, etc.).

**Rationale:**
- Auth is handled by the platform — no token management in app code for deployed environments.
- Co-located with the data — no network egress or firewall rules needed to reach the SQL Warehouse.
- Single deployment unit: the platform handles TLS, availability, and scaling.

**Trade-offs:**
- Runtime environment is opaque (CWD is `/app/python/source_code/`, not the repo root).
- `requirements.txt` must be at the repo root, not inside `backend/` — differs from standard Python project layout.
- Resource env var injection (e.g., `DATABRICKS_WAREHOUSE_ID`) has been unreliable in practice; warehouse ID is hardcoded as a default instead.

---

## ADR-002 — FastAPI serves the React frontend as static files

**Date:** 2026-08  
**Status:** Adopted

**Decision:** The built React `dist/` output is mounted inside FastAPI via `StaticFiles` and a SPA catch-all route, rather than using a separate static file host.

**Rationale:**
- Databricks Apps runs a single process per app — there is no separate static hosting tier.
- Eliminates CORS complexity: API and frontend share the same origin.
- Single `app.yaml` command covers both concerns.

**Trade-offs:**
- Frontend must be rebuilt (`npm run build`) before deploying — the `dist/` folder is committed to the repo.
- FastAPI handles static file I/O, which is less efficient than a dedicated CDN, but acceptable for an internal PoC.

**Implementation note:** The SPA catch-all route parameter must exactly match the path variable name `{full_path:path}` → `def serve_spa(full_path: str)`. A leading underscore (`_full_path`) causes FastAPI to treat it as a required query parameter.

---

## ADR-003 — SQL-based schema/table discovery instead of Unity Catalog REST API

**Date:** 2026-08  
**Status:** Adopted

**Decision:** `list_schemas()` uses `SHOW SCHEMAS IN {catalog}` and `list_tables()` uses `{catalog}.information_schema.tables` via the warehouse, rather than `WorkspaceClient.schemas.list()` / `WorkspaceClient.tables.list()`.

**Rationale:**
- The service principal has SQL Warehouse compute access but not the Unity Catalog REST API `USE CATALOG` / `USE SCHEMA` grants needed for the SDK catalog browser methods.
- SQL-based discovery reuses the existing `execute_query()` path — no separate auth surface.
- `SHOW SCHEMAS` does not require `information_schema` privileges, making it more broadly compatible.

**Trade-offs:**
- Each schema/table list request consumes a warehouse query slot (minor for a PoC).
- `information_schema.tables` requires the catalog to support it — confirmed working for `dbw_sandbox_sk`.

---

## ADR-004 — Pydantic `BaseSettings` with `extra='ignore'`

**Date:** 2026-08  
**Status:** Adopted

**Decision:** `SettingsConfigDict(extra='ignore')` is set on the `Settings` model.

**Rationale:**
- `backend/.env` (used for local dev) contains Azure service principal vars (`DATABRICKS_AZURE_CLIENT_ID`, etc.) that the Databricks SDK reads directly from the environment — they do not need to be declared on the Settings model.
- Without `extra='ignore'`, Pydantic raises a `ValidationError` on startup when those vars are present in `.env`.

---

## ADR-005 — `_resolve_warehouse_id()` fallback with `@lru_cache`

**Date:** 2026-08  
**Status:** Adopted

**Decision:** If `DATABRICKS_WAREHOUSE_ID` is not set, the service lists available warehouses and uses the first one. The resolved ID is cached via `@lru_cache(maxsize=1)`.

**Rationale:**
- Databricks Apps resource env var injection for SQL Warehouses has been unreliable in this workspace; a hardcoded default is now the primary path, but the fallback prevents a hard crash if neither is available.
- `lru_cache` ensures the warehouse list call happens at most once per process lifetime.

**Trade-offs:**
- "First available" is non-deterministic if multiple warehouses exist. Acceptable for a PoC; production should pin the warehouse ID explicitly.

---

## ADR-006 — Default catalog is `dbw_sandbox_sk`, not `main`

**Date:** 2026-08  
**Status:** Adopted

**Decision:** `databricks_catalog` defaults to `dbw_sandbox_sk` in `config.py` and `DEFAULT_CATALOG` in `TablesPage.tsx`.

**Rationale:**
- The workspace default catalog is `dbw_sandbox_sk`. The common Unity Catalog default of `main` does not exist here — queries against `main.information_schema.*` return `TABLE_OR_VIEW_NOT_FOUND`.

**Note:** If this app is deployed to a different workspace, this default must be updated.

---

## ADR-007 — Brand colors via Tailwind custom palette

**Date:** 2026-08  
**Status:** Adopted

**Decision:** Brand colors (`navy` = `#003087`, `gold` = `#F5A800`) are defined at the top level of `tailwind.config.js` `theme.extend.colors`, not nested under a `<business_namw>` prefix.

**Rationale:**
- Flat names (`text-navy`, `bg-gold`) are shorter and work directly with Tailwind's `@apply` directive in `index.css`.
- Nested names (`text-<business_name>-navy`) require updating all utility classes if the prefix changes.

---

## ADR-008 — Per-user query execution via `X-Forwarded-Access-Token`

**Date:** 2026-08  
**Status:** Adopted

**Decision:** When **User Authorization** is enabled in the Databricks Apps UI, every query is executed under the signed-in user's forwarded OAuth token instead of the service principal. The service principal path is kept as a fallback for local dev only.

**Rationale:**
- Unity Catalog enforces row-level, column-level, and schema-level permissions at the warehouse level — but only when the query runs as the user, not as a service principal.
- Using the forwarded token requires zero additional configuration per user: Databricks Apps injects `X-Forwarded-Access-Token` automatically once User Authorization is enabled.
- The `sql` scope is included in the forwarded token when the `app.yaml` declares the SQL warehouse as a resource with `CAN_USE` permission.

**Trade-offs:**
- Users need a fresh session (new login or incognito window) after User Authorization is first enabled to receive a token with the `sql` scope — existing sessions retain the old token until expiry.
- Each user must have `CAN_USE` on the warehouse and appropriate UC grants (`USE CATALOG`, `USE SCHEMA`, `SELECT`) granted externally via Databricks SQL or Terraform.

**Implementation note:** A 403 from the SQL Statements API is treated as a "missing scope" signal and triggers the SP fallback rather than surfacing an error to the user.

---

## ADR-009 — `requests` library for user-scoped HTTP calls instead of SDK

**Date:** 2026-08  
**Status:** Adopted

**Decision:** All user-scoped HTTP calls (SQL statement execution, SCIM identity resolution) use the `requests` library directly with `Authorization: Bearer {user_token}`, rather than instantiating a `WorkspaceClient(token=user_token)`.

**Rationale:**
- The Databricks Python SDK raises `ConfigAttributeError: more than one authorization method configured` when `token=` is passed while `DATABRICKS_CLIENT_ID` / `DATABRICKS_CLIENT_SECRET` are present in the environment. Both are present in deployed Databricks Apps.
- Direct HTTP calls have no credential-chain validation; passing the bearer token in the `Authorization` header is the canonical REST API pattern.

**Trade-offs:**
- Loses SDK convenience wrappers (pagination, retry, type-safe response models) for user-scoped calls. Acceptable because both call sites (`/api/2.0/sql/statements` and `/api/2.0/preview/scim/v2/Me`) have simple, stable schemas.
- The service principal `WorkspaceClient` is still used for warehouse discovery and local dev fallback — SDK stays in the dependency tree.
