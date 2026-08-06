# Sequence & State Diagrams

## Query Execution Sequence

End-to-end flow when a user runs SQL from the Query page. Databricks Apps injects `X-Forwarded-Access-Token` on every request when User Authorization is enabled.

```mermaid
sequenceDiagram
    actor User
    participant QueryPage as QueryPage.tsx
    participant AppsProxy as Apps Proxy
    participant API as /api/query (FastAPI)
    participant Service as databricks_service.py
    participant Warehouse as SQL Warehouse

    User->>QueryPage: Types SQL, presses Ctrl+Enter
    QueryPage->>AppsProxy: POST /api/query { sql }
    AppsProxy->>API: POST /api/query + X-Forwarded-Access-Token
    API->>Service: execute_query(sql, user_token)
    Service->>Warehouse: POST /api/2.0/sql/statements (Bearer user_token)
    Note over Warehouse: UC enforces user's GRANT/REVOKE
    Warehouse-->>Service: StatementResponse (SUCCEEDED + result rows)
    Service-->>API: QueryResultResponse { columns, rows, row_count, execution_time_ms }
    API-->>QueryPage: 200 JSON
    QueryPage-->>User: Renders result table
```

---

## User Identity Resolution Sequence

How the app resolves `X-Forwarded-User` (an opaque internal ID) to a human-readable email, displayed in the header.

```mermaid
sequenceDiagram
    actor User
    participant Layout as Layout.tsx
    participant API as /api/me (FastAPI)
    participant Service as databricks_service.py
    participant SCIM as Databricks SCIM API

    User->>Layout: App load
    Layout->>API: GET /api/me
    API->>Service: resolve_user_identity(x_forwarded_user, access_token)
    alt cache hit
        Service-->>API: cached email
    else first request for this user
        Service->>SCIM: GET /api/2.0/preview/scim/v2/Me (Bearer user_token)
        SCIM-->>Service: { userName: "steve.kaschimer@slalom.com", ... }
        Service-->>API: email (cached for process lifetime)
    end
    API-->>Layout: { email: "steve.kaschimer@slalom.com" }
    Layout-->>User: Displays email top-right
```

---

## Schema Browser Sequence

Flow when a user opens the Tables page and clicks a schema.

```mermaid
sequenceDiagram
    actor User
    participant TablesPage as TablesPage.tsx
    participant SchemasAPI as /api/schemas (FastAPI)
    participant TablesAPI as /api/tables (FastAPI)
    participant Service as databricks_service.py
    participant Warehouse as SQL Warehouse

    User->>TablesPage: Navigates to /tables
    TablesPage->>SchemasAPI: GET /api/schemas?catalog=dbw_sandbox_sk
    SchemasAPI->>Service: list_schemas("dbw_sandbox_sk")
    Service->>Warehouse: SHOW SCHEMAS IN dbw_sandbox_sk
    Warehouse-->>Service: rows [ ["default"], ["finance"], ... ]
    Service-->>SchemasAPI: SchemaTree { catalog, schemas[] }
    SchemasAPI-->>TablesPage: 200 JSON
    TablesPage-->>User: Renders schema list

    User->>TablesPage: Clicks a schema
    TablesPage->>TablesAPI: GET /api/tables?catalog=dbw_sandbox_sk&schema=default
    TablesAPI->>Service: list_tables("dbw_sandbox_sk", "default")
    Service->>Warehouse: SELECT ... FROM dbw_sandbox_sk.information_schema.tables WHERE table_schema = 'default'
    Warehouse-->>Service: rows
    Service-->>TablesAPI: TableSummary[]
    TablesAPI-->>TablesPage: 200 JSON
    TablesPage-->>User: Renders table list

    User->>TablesPage: Clicks "Query" on a table
    TablesPage-->>User: Navigates to /query with SQL pre-populated
```

---

## SPA Routing State Diagram

How the React app routes between pages and what state transitions each page manages.

```mermaid
stateDiagram-v2
    [*] --> Dashboard : app load → /
    Dashboard --> Query : nav click or KPI drill-down
    Dashboard --> Tables : nav click
    Query --> Tables : nav click
    Tables --> Query : "Query" button sets sessionStorage + navigate /query
    Query --> Dashboard : nav click
    Tables --> Dashboard : nav click

    state Query {
        [*] --> Idle
        Idle --> Executing : Ctrl+Enter / Run button
        Executing --> Success : HTTP 200
        Executing --> Error : HTTP 4xx/5xx or timeout
        Success --> Idle : user edits SQL
        Error --> Idle : user edits SQL
        Success --> [*] : CSV export (download, stays in Success)
    }

    state Tables {
        [*] --> LoadingSchemas
        LoadingSchemas --> SchemasLoaded : GET /api/schemas 200
        LoadingSchemas --> SchemasError : GET /api/schemas error
        SchemasLoaded --> LoadingTables : user selects schema
        LoadingTables --> TablesLoaded : GET /api/tables 200
        LoadingTables --> TablesError : GET /api/tables error
        TablesLoaded --> LoadingTables : user selects different schema
    }
```

---

## Warehouse ID Resolution Flow

How the backend resolves which SQL Warehouse to use at startup.

```mermaid
flowchart TD
    Start([Request arrives]) --> Check{settings.databricks_warehouse_id set?}
    Check -- Yes --> UseConfigured["Use configured ID<br/>5288ab7cd99c4e09"]
    Check -- No --> List["client.warehouses.list()"]
    List --> Any{Any warehouses?}
    Any -- Yes --> UseFirst["Use first warehouse<br/>log warning"]
    Any -- No --> Raise[raise RuntimeError]
    UseConfigured --> Execute[execute_statement]
    UseFirst --> Execute
    Raise --> HTTP502[HTTP 502 to client]
```
