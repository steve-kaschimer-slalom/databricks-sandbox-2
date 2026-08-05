export interface QueryResult {
  columns: string[]
  rows: (string | number | boolean | null)[][]
  row_count: number
  execution_time_ms: number
}

export interface TableSummary {
  catalog: string
  schema_name: string
  table_name: string
  table_type: string
  comment: string | null
}

export interface SchemaTree {
  catalog: string
  schemas: string[]
}

