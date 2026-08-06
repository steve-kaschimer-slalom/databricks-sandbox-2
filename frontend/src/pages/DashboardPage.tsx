import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { RefreshCw, AlertCircle } from 'lucide-react'
import { runQuery } from '../api/databricks'
import Spinner from '../components/Spinner'

// Replace these SQL statements with queries against your actual Delta tables
const SUMMARY_QUERIES = [
  {
    id: 'row_count',
    label: 'Example: Row Count',
    sql: "SELECT COUNT(*) AS value, 'Total Records' AS label FROM samples.nyctaxi.trips",
  },
  {
    id: 'avg_fare',
    label: 'Example: Avg Fare',
    sql: "SELECT ROUND(AVG(fare_amount), 2) AS value, 'Avg Fare (USD)' AS label FROM samples.nyctaxi.trips",
  },
] as const

const CHART_QUERY =
  "SELECT pickup_zip AS category, COUNT(*) AS count FROM samples.nyctaxi.trips GROUP BY pickup_zip ORDER BY count DESC LIMIT 10"

function KpiCard({ label, value, loading }: { label: string; value: string; loading?: boolean }) {
  return (
    <div className="stat-card">
      <span className="stat-label">{label}</span>
      {loading ? <Spinner size={22} /> : <span className="stat-value">{value}</span>}
    </div>
  )
}

export default function DashboardPage() {
  const [chartRefreshKey, setChartRefreshKey] = useState(0)

  const kpiQueries = SUMMARY_QUERIES.map((q) =>
    // eslint-disable-next-line react-hooks/rules-of-hooks
    useQuery({
      queryKey: ['kpi', q.id],
      queryFn: () => runQuery(q.sql),
    })
  )

  const chartQuery = useQuery({
    queryKey: ['dashboard-chart', chartRefreshKey],
    queryFn: () => runQuery(CHART_QUERY),
  })

  const chartData =
    chartQuery.data?.rows.map((row) => ({
      category: String(row[0] ?? ''),
      count: Number(row[1] ?? 0),
    })) ?? []

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-navy dark:text-white">Dashboard</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Business data from your Databricks SQL Warehouse
          </p>
        </div>
        <button
          onClick={() => setChartRefreshKey((k) => k + 1)}
          className="btn-primary flex items-center gap-2 text-sm"
        >
          <RefreshCw size={15} />
          Refresh
        </button>
      </div>

      <div className="card border-l-4 border-l-gold text-sm text-gray-600 dark:text-gray-400">
        <div className="flex items-start gap-2">
          <AlertCircle size={16} className="text-gold mt-0.5 flex-shrink-0" />
          <span>
            The queries on this page use the Databricks sample{' '}
            <code className="bg-gray-100 dark:bg-[#0f1117] dark:text-gray-300 px-1 rounded">
              samples.nyctaxi.trips
            </code>{' '}
            dataset. Replace the SQL in{' '}
            <code className="bg-gray-100 dark:bg-[#0f1117] dark:text-gray-300 px-1 rounded">
              DashboardPage.tsx
            </code>{' '}
            with your own business tables.
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiQueries.map((q, i) => (
          <KpiCard
            key={SUMMARY_QUERIES[i].id}
            label={SUMMARY_QUERIES[i].label}
            loading={q.isLoading}
            value={
              q.isLoading
                ? ''
                : q.error
                ? 'Error'
                : String(q.data?.rows[0]?.[0] ?? '—')
            }
          />
        ))}
      </div>

      <div className="card">
        <h2 className="text-base font-semibold text-navy dark:text-white mb-4">
          Top 10 Pickup Zones by Trip Count
        </h2>
        {chartQuery.isLoading ? (
          <div className="h-64 flex items-center justify-center">
            <Spinner size={32} />
          </div>
        ) : chartQuery.error ? (
          <div className="h-64 flex items-center justify-center text-red-600 dark:text-red-400 text-sm">
            Query failed — check the browser console for details.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartData} margin={{ top: 4, right: 8, left: 0, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid, #E8E8E8)" />
              <XAxis
                dataKey="category"
                tick={{ fontSize: 11, fill: 'var(--chart-tick, #666)' }}
                angle={-45}
                textAnchor="end"
              />
              <YAxis tick={{ fontSize: 11, fill: 'var(--chart-tick, #666)' }} />
              <Tooltip
                contentStyle={{
                  fontSize: 12,
                  borderColor: 'var(--chart-grid, #E8E8E8)',
                  backgroundColor: 'var(--chart-tooltip-bg, #fff)',
                  color: 'var(--chart-tooltip-text, #1A1A1A)',
                }}
                cursor={{ fill: 'rgba(0,48,135,0.05)' }}
              />
              <Bar dataKey="count" fill="#003087" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
