import { useState, useRef } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Play, Clock, Download } from 'lucide-react'
import { runQuery } from '../api/databricks'
import type { QueryResult } from '../types/databricks'

const PLACEHOLDER_SQL = `-- Write your SQL here. The warehouse and catalog are pre-configured in the backend.
SELECT *
FROM samples.nyctaxi.trips
LIMIT 100`

function ResultTable({ result }: { result: QueryResult }) {
  return (
    <div className="overflow-auto rounded-lg border border-gray-100">
      <table className="w-full text-left text-sm">
        <thead className="bg-navy text-white text-xs">
          <tr>
            {result.columns.map((col) => (
              <th key={col} className="py-2.5 px-3 font-medium whitespace-nowrap">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {result.rows.map((row, rowIdx) => (
            <tr
              key={rowIdx}
              className="border-t border-gray-100 hover:bg-gray-50"
            >
              {row.map((cell, colIdx) => (
                <td
                  key={colIdx}
                  className="py-2 px-3 text-gray-900 whitespace-nowrap max-w-xs truncate"
                >
                  {cell === null ? (
                    <span className="text-gray-300 italic">null</span>
                  ) : (
                    String(cell)
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function downloadCsv(result: QueryResult) {
  const header = result.columns.join(',')
  const body = result.rows
    .map((row) => row.map((cell) => (cell === null ? '' : `"${String(cell).replace(/"/g, '""')}"`)).join(','))
    .join('\n')
  const blob = new Blob([`${header}\n${body}`], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'query-result.csv'
  a.click()
  URL.revokeObjectURL(url)
}

export default function QueryPage() {
  const pending = sessionStorage.getItem('pendingQuery')
  if (pending) {
    sessionStorage.removeItem('pendingQuery')
  }
  const [sql, setSql] = useState(pending ?? PLACEHOLDER_SQL)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const { mutate, data: result, isPending, error, reset } = useMutation({
    mutationFn: () => runQuery(sql),
  })

  function handleRun() {
    reset()
    mutate()
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Ctrl+Enter / Cmd+Enter to run
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      handleRun()
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-navy">Query Editor</h1>
          <p className="text-sm text-gray-600 mt-1">
            Execute SQL against your Databricks SQL Warehouse
          </p>
        </div>
      </div>

      <div className="card p-0 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2.5 bg-gray-50 border-b border-gray-100">
          <span className="text-xs font-medium text-gray-600">SQL</span>
          <span className="text-xs text-gray-300">Ctrl + Enter to run</span>
        </div>
        <textarea
          ref={textareaRef}
          value={sql}
          onChange={(e) => setSql(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={10}
          spellCheck={false}
          className="w-full px-4 py-3 font-mono text-sm text-gray-900 bg-white
                     focus:outline-none resize-y border-b border-gray-100"
        />
        <div className="flex items-center justify-between px-4 py-2.5">
          <button
            onClick={handleRun}
            disabled={isPending || !sql.trim()}
            className="btn-primary flex items-center gap-2 text-sm disabled:opacity-60"
          >
            <Play size={14} />
            {isPending ? 'Running…' : 'Run Query'}
          </button>
          {result && (
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5 text-xs text-gray-600">
                <Clock size={12} />
                {result.execution_time_ms}ms · {result.row_count} rows
              </span>
              <button
                onClick={() => downloadCsv(result)}
                className="flex items-center gap-1.5 text-xs text-navy hover:underline"
              >
                <Download size={12} />
                Export CSV
              </button>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="card border-red-200 bg-red-50 text-red-700 text-sm font-mono">
          {(error as Error).message}
        </div>
      )}

      {result && result.rows.length > 0 && <ResultTable result={result} />}

      {result && result.rows.length === 0 && (
        <div className="card text-center text-gray-600 text-sm py-10">
          Query returned 0 rows.
        </div>
      )}
    </div>
  )
}
