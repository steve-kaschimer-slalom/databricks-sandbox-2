import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import DashboardPage from './pages/DashboardPage'
import QueryPage from './pages/QueryPage'
import TablesPage from './pages/TablesPage'
import ErrorBoundary from './components/ErrorBoundary'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<ErrorBoundary><DashboardPage /></ErrorBoundary>} />
          <Route path="query" element={<ErrorBoundary><QueryPage /></ErrorBoundary>} />
          <Route path="tables" element={<ErrorBoundary><TablesPage /></ErrorBoundary>} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
