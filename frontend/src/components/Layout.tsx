import { NavLink, Outlet } from 'react-router-dom'
import { LayoutDashboard, TerminalSquare, Table2, Flame, UserCircle } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { fetchCurrentUser } from '../api/databricks'
import ThemeToggle from './ThemeToggle'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/query', label: 'Query', icon: TerminalSquare, end: false },
  { to: '/tables', label: 'Tables', icon: Table2, end: false },
]

export default function Layout() {
  const { data: currentUser } = useQuery({
    queryKey: ['me'],
    queryFn: fetchCurrentUser,
    staleTime: Infinity,
  })

  return (
    <div className="min-h-screen flex flex-col bg-white dark:bg-[#0f1117]">
      <header className="bg-navy dark:bg-[#0d1526] text-white shadow-md dark:shadow-none dark:border-b dark:border-[#2a3045]">
        <div className="max-w-screen-xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Flame className="text-gold" size={28} />
            <div>
              <span className="text-lg font-bold tracking-tight">Kaschimer</span>
              <span className="ml-2 text-gray-300 text-sm font-light">Databricks Analytics</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {currentUser?.email ? (
              <div className="flex items-center gap-2 text-sm text-gray-300">
                <UserCircle size={18} className="text-gold" />
                <span>{currentUser.email}</span>
              </div>
            ) : (
              <span className="text-xs text-gray-300 hidden sm:block">
                Azure Databricks Intelligence Platform
              </span>
            )}
            <ThemeToggle />
          </div>
        </div>
      </header>

      <div className="flex flex-1 max-w-screen-xl mx-auto w-full px-6 py-6 gap-6">
        <nav className="w-56 flex-shrink-0">
          <ul className="flex flex-col gap-1">
            {navItems.map(({ to, label, icon: Icon, end }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  end={end}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-2.5 rounded-md text-sm font-medium transition-colors duration-150 ${
                      isActive
                        ? 'bg-navy text-white dark:bg-navy/80'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-navy dark:text-gray-400 dark:hover:bg-[#1a1f2e] dark:hover:text-white'
                    }`
                  }
                >
                  <Icon size={18} />
                  {label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <main className="flex-1 min-w-0">
          <Outlet />
        </main>
      </div>

      <footer className="bg-navy-dark dark:bg-[#0a0e1a] text-gray-300 text-center text-xs py-3">
        © {new Date().getFullYear()} Kaschimer — Internal Analytics Platform
      </footer>
    </div>
  )
}
