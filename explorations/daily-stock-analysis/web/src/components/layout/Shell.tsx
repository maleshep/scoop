import { type ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { useTheme } from 'next-themes'
import { TrendingUp, MessageSquare, Briefcase, Bell, Activity, History, BarChart3, Settings as SettingsIcon } from 'lucide-react'

const NAV = [
  { to: '/', label: 'Home', icon: TrendingUp },
  { to: '/chat', label: 'Agent', icon: MessageSquare },
  { to: '/portfolio', label: 'Portfolio', icon: Briefcase },
  { to: '/alerts', label: 'Alerts', icon: Bell },
  { to: '/decision-signals', label: 'Signals', icon: Activity },
  { to: '/history', label: 'History', icon: History },
  { to: '/usage', label: 'Usage', icon: BarChart3 },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
]

export function Shell({ children }: { children: ReactNode }) {
  const { theme, setTheme } = useTheme()
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <aside style={{
        width: 200, background: 'var(--color-panel)', borderRight: '1px solid var(--color-border)',
        padding: '16px 0', flexShrink: 0,
      }}>
        <div style={{ padding: '0 16px 16px', fontWeight: 700, fontSize: 15, color: 'var(--color-text)' }}>
          📈 DSA
        </div>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === '/'}
              style={({ isActive }) => ({
                display: 'flex', alignItems: 'center', gap: 10, padding: '8px 16px',
                color: isActive ? 'var(--color-text)' : 'var(--color-muted)',
                background: isActive ? 'var(--color-panel2)' : 'transparent',
                textDecoration: 'none', fontSize: 13, borderLeft: isActive ? '2px solid var(--color-blue)' : '2px solid transparent',
              })}>
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div style={{ padding: '16px', marginTop: 'auto' }}>
          <button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            style={{ background: 'var(--color-panel2)', color: 'var(--color-muted)', border: '1px solid var(--color-border)', borderRadius: 4, padding: '4px 10px', fontSize: 12, cursor: 'pointer' }}>
            {theme === 'dark' ? '☀ Light' : '🌙 Dark'}
          </button>
        </div>
      </aside>
      <main style={{ flex: 1, padding: 24, overflowY: 'auto' }}>
        {children}
      </main>
    </div>
  )
}
