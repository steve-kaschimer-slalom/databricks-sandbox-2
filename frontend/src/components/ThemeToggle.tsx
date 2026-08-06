import { Sun, Moon } from 'lucide-react'
import { useTheme } from '../hooks/useTheme'

export default function ThemeToggle() {
  const { theme, toggle } = useTheme()
  const isDark = theme === 'dark'

  return (
    <button
      onClick={toggle}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      className="p-2 rounded-md text-gray-300 hover:text-white hover:bg-white/10
                 transition-colors duration-200
                 focus:outline-none focus-visible:ring-2 focus-visible:ring-gold
                 focus-visible:ring-offset-2 focus-visible:ring-offset-navy"
    >
      {isDark ? <Sun size={18} aria-hidden="true" /> : <Moon size={18} aria-hidden="true" />}
    </button>
  )
}
