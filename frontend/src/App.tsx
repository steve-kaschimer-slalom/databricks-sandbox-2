import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import DashboardPage from './pages/DashboardPage'
import QueryPage from './pages/QueryPage'
import TablesPage from './pages/TablesPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="query" element={<QueryPage />} />
          <Route path="tables" element={<TablesPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
