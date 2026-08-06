---
inclusion: always
---

# Brand & UI Conventions

This file covers the Tailwind color palette, reusable CSS component classes, and UI patterns used throughout the frontend. Follow these conventions for all new components and pages.

---

## Color Palette

Colors are defined **flat** in `tailwind.config.js` under `theme.extend.colors`. Use them as direct utility class names — never nest under a prefix.

| Token | Hex | Tailwind class examples | Usage |
|---|---|---|---|
| `navy` | `#003087` | `bg-navy`, `text-navy`, `border-navy` | Primary — headers, buttons, active nav |
| `navy-dark` | `#001F5B` | `bg-navy-dark`, `hover:bg-navy-dark` | Hover states, footer background |
| `navy-light` | `#0047B3` | `hover:bg-navy-light` | Button hover (see `.btn-primary`) |
| `gold` | `#F5A800` | `bg-gold`, `text-gold`, `border-gold` | Accents, highlights, icons |
| `gold-dark` | `#CC8C00` | `hover:bg-gold-dark` | Hover on gold elements |
| `gold-light` | `#FFD04D` | `bg-gold-light`, `text-gold-light` | Light gold backgrounds |
| `white` | `#FFFFFF` | `bg-white`, `text-white` | Page background (light mode), card backgrounds, header text |
| `gray-50` | `#F5F5F5` | `bg-gray-50` | Table headers, subtle backgrounds |
| `gray-100` | `#E8E8E8` | `border-gray-100`, `bg-gray-100` | Card borders, dividers |
| `gray-300` | `#AAAAAA` | `text-gray-300` | Muted / disabled text |
| `gray-600` | `#666666` | `text-gray-600` | Secondary text, labels |
| `gray-900` | `#1A1A1A` | `text-gray-900` | Primary body text |

> **Never** use Tailwind's built-in gray scale (e.g. `gray-400`, `gray-700`) — those are overridden by the custom palette above and may not resolve as expected.

---

## Box Shadows

Two custom shadow tokens are defined in `tailwind.config.js`:

| Token | Class | Usage |
|---|---|---|
| `card` | `shadow-card` | Default card shadow (`0 2px 8px rgba(0,48,135,0.12)`) |
| `card-hover` | `shadow-card-hover` | Elevated card on hover (`0 4px 16px rgba(0,48,135,0.2)`) |

---

## Typography

- **Font family:** Inter (loaded via CSS), falling back to `system-ui` and `sans-serif`.
- **Headings** (`h1`–`h6`) get `text-navy font-semibold` via `@layer base` in `index.css` (dark mode: `text-white`).
- **Page background:** `bg-white` light / `dark:bg-[#0f1117]` dark
- **Page titles:** `text-2xl font-bold text-navy`
- **Section titles:** `text-base font-semibold text-navy`
- **Body / secondary text:** `text-sm text-gray-600`
- **Code snippets inline:** `<code className="bg-gray-100 px-1 rounded">`

---

## Reusable Component Classes (defined in `index.css`)

These classes are available globally via Tailwind `@layer components`. Use them instead of repeating utility strings.

### Buttons

```tsx
// Primary action (navy background)
<button className="btn-primary">Save</button>

// Secondary action (gold background)
<button className="btn-secondary">Cancel</button>

// With icon — add flex and gap
<button className="btn-primary flex items-center gap-2 text-sm">
  <SomeIcon size={15} />
  Label
</button>

// Disabled state
<button className="btn-primary disabled:opacity-60" disabled={isLoading}>…</button>
```

### Cards

```tsx
// Standard card
<div className="card">…</div>

// Card with hover elevation
<div className="card-hover">…</div>

// Card with accent border (e.g. info/warning callout)
<div className="card border-l-4 border-l-gold">…</div>

// Card with no padding (use when the content controls its own padding)
<div className="card p-0 overflow-hidden">…</div>
```

### Stat / KPI Cards

```tsx
<div className="stat-card">
  <span className="stat-label">Total Records</span>
  <span className="stat-value">1,234</span>
  <span className="stat-delta-positive">+5.2%</span>   {/* green */}
  <span className="stat-delta-negative">-1.1%</span>   {/* red */}
</div>
```

### Status Badges

```tsx
<span className="badge-running">Running</span>    {/* gold/amber */}
<span className="badge-success">Success</span>    {/* green */}
<span className="badge-failed">Failed</span>      {/* red */}
<span className="badge-pending">Pending</span>    {/* gray */}

// For custom badge content, compose from badge-status:
<span className="badge-status bg-navy-light text-white">Custom</span>
```

---

## Layout Conventions

The app uses a fixed shell defined in `Layout.tsx`:

```
<header>          navy background, Flame icon (gold), app title, user email top-right
  <nav>           left sidebar, 56px wide (w-56), NavLink items with active state
  <main>          flex-1, min-w-0, receives <Outlet /> content
<footer>          navy-dark background, centered copyright line
```

Page content inside `<main>` should:
- Use `<div className="flex flex-col gap-6">` as the top-level wrapper
- Open with a `flex items-center justify-between` header row containing the page title + any action buttons
- Keep `max-w-screen-xl mx-auto` scoping at the layout level — don't re-apply inside pages

---

## Data Display Patterns

### Tables

```tsx
<div className="card p-0 overflow-hidden">
  {/* Colored header bar */}
  <div className="px-4 py-2.5 bg-navy text-white text-xs font-medium flex items-center gap-2">
    <SomeIcon size={13} />
    Section Title
  </div>
  <table className="w-full text-left text-sm">
    <thead className="bg-gray-50 text-xs text-gray-600 uppercase">
      <tr>
        <th className="py-2.5 px-4">Column</th>
      </tr>
    </thead>
    <tbody>
      <tr className="border-t border-gray-100 hover:bg-gray-50">
        <td className="py-2.5 px-4 text-gray-900">Value</td>
      </tr>
    </tbody>
  </table>
</div>
```

### Charts (Recharts)

- Use `<ResponsiveContainer width="100%" height={280}>` inside a `.card`
- Grid lines: `<CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />`
- Axis ticks: `tick={{ fontSize: 11, fill: 'var(--chart-tick)' }}`
- Bar fill: `fill="#003087"` (navy) with `radius={[3, 3, 0, 0]}`
- Tooltip: `contentStyle={{ fontSize: 12, borderColor: 'var(--chart-grid)', backgroundColor: 'var(--chart-tooltip-bg)', color: 'var(--chart-tooltip-text)' }}`
- Chart cursor: `cursor={{ fill: 'rgba(0,48,135,0.05)' }}`

> Recharts uses inline styles so Tailwind `dark:` variants don't apply. Always use the CSS custom properties above — they are defined on `:root` and `.dark` in `index.css` and switch automatically with the theme.

### Loading states

Use `<Spinner />` from `frontend/src/components/Spinner.tsx`. It accepts an optional `size` prop (number, px).

```tsx
import Spinner from '../components/Spinner'

// Inline loading within a fixed-height container
<div className="h-64 flex items-center justify-center">
  <Spinner size={32} />
</div>
```

### Null / empty values

- Null cells in result tables: `<span className="text-gray-300 italic">null</span>`
- Missing optional string: render `—` (em dash)
- Empty result set: centered card with `text-gray-600 text-sm py-10`

---

## Icons

Uses **Lucide React** (`lucide-react`). Import named icons individually:

```tsx
import { LayoutDashboard, TerminalSquare, Table2, Flame, UserCircle, RefreshCw } from 'lucide-react'
```

Standard sizes: `size={13}` for dense UI (table headers, badges), `size={15}–{18}` for nav and buttons, `size={28}` for the header brand icon.

---

## Accessibility Notes

- All interactive elements (`<button>`, `<NavLink>`) include `focus:outline-none focus:ring-2 focus:ring-gold focus:ring-offset-2` via the `.btn-primary` / `.btn-secondary` classes.
- Color is never the sole indicator of state — badges use both background color and text label.
- `aria-label` should be added to icon-only buttons.

---

## Dark Mode

The app supports dark/light mode via Tailwind's `darkMode: 'class'` strategy. The `dark` class is toggled on `<html>` by the `useTheme` hook (`src/hooks/useTheme.ts`).

### Adding dark mode to new components

Use `dark:` variants alongside every light-mode colour utility:

```tsx
// Text
<p className="text-gray-600 dark:text-gray-400">Secondary text</p>

// Backgrounds
<div className="bg-white dark:bg-[#1a1f2e]">Card content</div>

// Borders
<div className="border border-gray-100 dark:border-[#2a3045]">…</div>

// Hover
<button className="hover:bg-gray-50 dark:hover:bg-[#0f1117]">…</button>
```

### Dark surface palette

These hex values are used inline (not in `tailwind.config.js`). They are the canonical dark mode surfaces for this app:

| Surface | Value | Usage |
|---|---|---|
| Page background | `#0f1117` | `body`, table headers, textarea |
| Card / panel | `#1a1f2e` | `.card`, content panels |
| Header / section header bars | `#0d1526` | Navy header bars inside cards |
| Footer | `#0a0e1a` | `<footer>` |
| Border | `#2a3045` | All borders in dark mode |
| Border hover | `#3a4060` | Hovered card borders |

### CSS custom properties for third-party components

Any library that uses inline styles (e.g. Recharts) cannot use Tailwind `dark:` variants. Use these CSS custom properties instead — defined on `:root` (light) and `.dark` in `index.css`:

| Property | Light | Dark |
|---|---|---|
| `--chart-grid` | `#E8E8E8` | `#2a3045` |
| `--chart-tick` | `#666666` | `#9ca3af` |
| `--chart-tooltip-bg` | `#ffffff` | `#1a1f2e` |
| `--chart-tooltip-text` | `#1A1A1A` | `#f3f4f6` |

### ThemeToggle component

`src/components/ThemeToggle.tsx` — drop this into any header. It reads/writes via `useTheme` and renders a Sun or Moon icon. No props needed.

```tsx
import ThemeToggle from '../components/ThemeToggle'

// In a header:
<div className="flex items-center gap-3">
  {/* ...other header content... */}
  <ThemeToggle />
</div>
```
