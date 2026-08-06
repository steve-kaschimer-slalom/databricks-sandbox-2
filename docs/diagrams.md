# Sequence & State Diagrams

## Query Execution Sequence

End-to-end flow when a user runs SQL from the Query page.

```mermaid
sequenceDiagram
    actor User
    participant QueryPage as QueryPage.tsx
    participant API as /api/query (FastAPI)
    participant Service as databricks_service.py
    participant Warehouse as SQL Warehouse

    User->>QueryPage: Types SQL, presses Ctrl+Enter
    QueryPage->>API: POST /api/query { sql }
    API->>Service: execute_query(sql)
    Service->>Warehouse: execute_statement(warehouse_id, sql, wait_timeout=30s)
    Warehouse-->>Service: StatementResponse (SUCCEEDED + result rows)
    Service-->>API: QueryResultResponse { columns, rows, row_count, execution_time_ms }
    API-->>QueryPage: 200 JSON
    QueryPage-->>User: Renders result table
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
    Check -- Yes --> UseConfigured[Use configured ID\n5288ab7cd99c4e09]
    Check -- No --> List[client.warehouses.list()]
    List --> Any{Any warehouses?}
    Any -- Yes --> UseFirst[Use first warehouse\nlog warning]
    Any -- No --> Raise[raise RuntimeError]
    UseConfigured --> Execute[execute_statement]
    UseFirst --> Execute
    Raise --> HTTP502[HTTP 502 to client]
```
