import { useEffect, useState } from 'react'

type Theme = 'light' | 'dark'

function getSystemTheme(): Theme {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function applyTheme(theme: Theme) {
  const html = document.documentElement
  const meta = document.querySelector<HTMLMetaElement>('meta[name="color-scheme"]')
  if (theme === 'dark') {
    html.classList.add('dark')
    if (meta) meta.content = 'dark'
  } else {
    html.classList.remove('dark')
    if (meta) meta.content = 'light'
  }
}

export function useTheme() {
  // Resolve initial theme: saved preference, or fall back to system
  const [theme, setThemeState] = useState<Theme>(() => {
    const saved = localStorage.getItem('color-scheme') as Theme | null
    return saved ?? getSystemTheme()
  })

  // Keep html class + meta tag in sync whenever theme changes
  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  // React to OS-level changes when the user hasn't pinned a preference
  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = (e: MediaQueryListEvent) => {
      const saved = localStorage.getItem('color-scheme')
      if (!saved) {
        setThemeState(e.matches ? 'dark' : 'light')
      }
    }
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])

  function toggle() {
    const system = getSystemTheme()
    const next: Theme = theme === 'dark' ? 'light' : 'dark'

    if (next === system) {
      // Back to system default — clear the pin so OS changes are followed again
      localStorage.removeItem('color-scheme')
    } else {
      localStorage.setItem('color-scheme', next)
    }
    setThemeState(next)
  }

  return { theme, toggle }
}
