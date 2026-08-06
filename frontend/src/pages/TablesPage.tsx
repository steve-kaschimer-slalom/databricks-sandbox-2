import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Database, Table2, ChevronRight, TerminalSquare } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { fetchSchemas, fetchTables } from '../api/databricks'
import Spinner from '../components/Spinner'

const DEFAULT_CATALOG = 'dbw_sandbox_sk'

export default function TablesPage() {
  const [catalog] = useState(DEFAULT_CATALOG)
  const [selectedSchema, setSelectedSchema] = useState<string | null>(null)
  const navigate = useNavigate()

  const schemasQuery = useQuery({
    queryKey: ['schemas', catalog],
    queryFn: () => fetchSchemas(catalog),
  })

  const tablesQuery = useQuery({
    queryKey: ['tables', catalog, selectedSchema],
    queryFn: () => fetchTables(catalog, selectedSchema!),
    enabled: !!selectedSchema,
  })

  function openInQuery(tableFqn: string) {
    const sql = `SELECT *\nFROM ${tableFqn}\nLIMIT 100`
    // Pass SQL via sessionStorage so QueryPage can pre-populate it
    sessionStorage.setItem('pendingQuery', sql)
    navigate('/query')
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-navy">Tables</h1>
        <p className="text-sm text-gray-600 mt-1">
          Browse Unity Catalog — <code className="bg-gray-100 px-1 rounded">{catalog}</code>
        </p>
      </div>

      <div className="flex gap-4">
        {/* Schema list */}
        <div className="w-56 flex-shrink-0">
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-2.5 bg-navy text-white text-xs font-medium flex items-center gap-2">
              <Database size={13} />
              Schemas
            </div>
            {schemasQuery.isLoading ? (
              <div className="py-6 flex justify-center"><Spinner /></div>
            ) : schemasQuery.error ? (
              <div className="py-6 text-center text-red-600 text-xs">Failed to load schemas.</div>
            ) : (
              <ul>
                {schemasQuery.data?.schemas.map((schema) => (
                  <li key={schema}>
                    <button
                      onClick={() => setSelectedSchema(schema)}
                      className={`w-full text-left flex items-center justify-between px-4 py-2.5 text-sm border-b border-gray-100 transition-colors ${
                        selectedSchema === schema
                          ? 'bg-navy/5 text-navy font-medium'
                          : 'text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      <span className="truncate">{schema}</span>
                      <ChevronRight size={13} className="flex-shrink-0" />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Table list */}
        <div className="flex-1 min-w-0">
          {!selectedSchema ? (
            <div className="card flex items-center justify-center h-40 text-gray-600 text-sm">
              Select a schema to view its tables.
            </div>
          ) : tablesQuery.isLoading ? (
            <div className="card flex items-center justify-center h-40">
              <Spinner size={28} />
            </div>
          ) : tablesQuery.error ? (
            <div className="card flex items-center justify-center h-40 text-red-600 text-sm">
              Failed to load tables.
            </div>
          ) : (
            <div className="card p-0 overflow-hidden">
              <div className="px-4 py-2.5 bg-navy text-white text-xs font-medium flex items-center gap-2">
                <Table2 size={13} />
                {selectedSchema} · {tablesQuery.data?.length ?? 0} tables
              </div>
              <table className="w-full text-left">
                <thead className="bg-gray-50 text-xs text-gray-600 uppercase">
                  <tr>
                    <th className="py-2.5 px-4">Table</th>
                    <th className="py-2.5 px-4">Type</th>
                    <th className="py-2.5 px-4">Comment</th>
                    <th className="py-2.5 px-4" />
                  </tr>
                </thead>
                <tbody>
                  {tablesQuery.data?.map((table) => (
                    <tr
                      key={table.table_name}
                      className="border-t border-gray-100 hover:bg-gray-50"
                    >
                      <td className="py-2.5 px-4 font-medium text-navy text-sm">
                        {table.table_name}
                      </td>
                      <td className="py-2.5 px-4">
                        <span className="badge-pending">{table.table_type}</span>
                      </td>
                      <td className="py-2.5 px-4 text-sm text-gray-600 max-w-xs truncate">
                        {table.comment ?? '—'}
                      </td>
                      <td className="py-2.5 px-4">
                        <button
                          onClick={() =>
                            openInQuery(
                              `${table.catalog}.${table.schema_name}.${table.table_name}`
                            )
                          }
                          className="flex items-center gap-1.5 text-xs text-navy hover:underline"
                        >
                          <TerminalSquare size={12} />
                          Query
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
