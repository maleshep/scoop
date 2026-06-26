import { useState, useEffect } from 'react'

interface SysConfig {
  model_provider: string
  glm_model: string
  watchlist: Record<string, { index: string; tickers: string[] }>
  anthropic_configured: boolean
  glm_configured: boolean
  email_enabled: boolean
}

const BASE = import.meta.env.VITE_API_URL || '/api/v1'

export function Settings() {
  const [cfg, setCfg] = useState<SysConfig | null>(null)
  const [watchlistText, setWatchlistText] = useState('')

  const load = () => fetch(`${BASE}/system/config`).then(r => r.json()).then(c => { setCfg(c); setWatchlistText(JSON.stringify(c.watchlist, null, 2)) })
  useEffect(() => { load() }, [])

  const setProvider = async (provider: string) => {
    await fetch(`${BASE}/system/config`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ model_provider: provider }) })
    load()
  }
  const saveWatchlist = async () => {
    try {
      const wl = JSON.parse(watchlistText)
      await fetch(`${BASE}/system/config`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ watchlist: wl }) })
      load()
    } catch { alert('Invalid JSON') }
  }

  if (!cfg) return <div style={{ color: 'var(--color-muted)' }}>Loading…</div>
  return (
    <div>
      <h1 style={{ fontSize: 22, margin: '0 0 16px' }}>Settings</h1>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 700 }}>
        <div style={{ background: 'var(--color-panel)', borderRadius: 8, padding: 16 }}>
          <h3 style={{ margin: '0 0 8px', fontSize: 13, color: 'var(--color-muted)', textTransform: 'uppercase' }}>Model provider</h3>
          <div style={{ display: 'flex', gap: 8 }}>
            {['glm', 'claude'].map(p => (
              <button key={p} onClick={() => setProvider(p)} style={{
                padding: '8px 16px', border: '1px solid var(--color-border)', borderRadius: 4, cursor: 'pointer',
                background: cfg.model_provider === p ? 'var(--color-blue)' : 'var(--color-panel2)',
                color: cfg.model_provider === p ? 'white' : 'var(--color-text)', fontSize: 14,
              }}>{p === 'glm' ? `GLM-5.2 (${cfg.glm_model})` : 'Claude (Sonnet)'} {cfg.model_provider === p ? '✓' : ''}</button>
            ))}
          </div>
          <div style={{ marginTop: 8, fontSize: 12, color: 'var(--color-muted)' }}>
            GLM configured: {cfg.glm_configured ? '✓' : '✗'} · Claude configured: {cfg.anthropic_configured ? '✓' : '✗'} · Email: {cfg.email_enabled ? '✓' : '✗'}
          </div>
        </div>
        <div style={{ background: 'var(--color-panel)', borderRadius: 8, padding: 16 }}>
          <h3 style={{ margin: '0 0 8px', fontSize: 13, color: 'var(--color-muted)', textTransform: 'uppercase' }}>Watchlist (JSON, in-memory)</h3>
          <textarea value={watchlistText} onChange={e => setWatchlistText(e.target.value)} rows={12} style={{ width: '100%', background: 'var(--color-panel2)', color: 'var(--color-text)', border: '1px solid var(--color-border)', borderRadius: 4, padding: 8, fontFamily: 'monospace', fontSize: 12 }} />
          <button onClick={saveWatchlist} style={{ marginTop: 8, padding: '8px 16px', background: 'var(--color-blue)', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer' }}>Save watchlist</button>
          <div style={{ fontSize: 11, color: 'var(--color-muted)', marginTop: 4 }}>In-memory only; resets on restart.</div>
        </div>
      </div>
    </div>
  )
}
