import axios from 'axios'
import type { QueryResult, TableSummary, SchemaTree } from '../types/databricks'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 60_000,
})

export const runQuery = (sql: string): Promise<QueryResult> =>
  apiClient.post<QueryResult>('/query', { sql }).then((r) => r.data)

export const fetchSchemas = (catalog = 'main'): Promise<SchemaTree> =>
  apiClient.get<SchemaTree>('/schemas', { params: { catalog } }).then((r) => r.data)

export const fetchTables = (catalog: string, schema: string): Promise<TableSummary[]> =>
  apiClient.get<TableSummary[]>('/tables', { params: { catalog, schema } }).then((r) => r.data)

