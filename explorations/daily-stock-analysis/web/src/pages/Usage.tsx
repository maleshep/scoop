import { useState, useEffect } from 'react'

interface UsageSummary { total: number; by_provider: Record<string, number>; by_date: Record<string, number>; rows: { date: string; provider: string; endpoint: string; calls: number }[] }

const BASE = import.meta.env.VITE_API_URL || '/api/v1'

export function Usage() {
  const [data, setData] = useState<UsageSummary | null>(null)
  useEffect(() => { fetch(`${BASE}/usage/summary`).then(r => r.json()).then(setData) }, [])

  if (!data) return <div style={{ color: 'var(--color-muted)' }}>Loading…</div>
  const dates = Object.entries(data.by_date).sort((a, b) => b[0].localeCompare(a[0]))
  const maxCalls = Math.max(1, ...dates.map(([, c]) => c))

  return (
    <div>
      <h1 style={{ fontSize: 22, margin: '0 0 16px' }}>Usage</h1>
      <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <Card label="Total calls" value={data.total} />
        {Object.entries(data.by_provider).map(([p, c]) => <Card key={p} label={p} value={c} />)}
      </div>
      <div style={{ background: 'var(--color-panel)', borderRadius: 8, padding: 16 }}>
        <h3 style={{ margin: '0 0 12px', fontSize: 13, color: 'var(--color-muted)', textTransform: 'uppercase' }}>Calls per day</h3>
        {dates.length === 0 ? <div style={{ color: 'var(--color-muted)' }}>No usage logged yet. Run an analysis to see it here.</div> : dates.map(([d, c]) => (
          <div key={d} style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
            <span style={{ width: 90, fontSize: 12, color: 'var(--color-muted)' }}>{d}</span>
            <div style={{ height: 18, width: `${(c / maxCalls) * 100}%`, minWidth: 2, background: 'var(--color-blue)', borderRadius: 3 }} />
            <span style={{ fontSize: 12 }}>{c}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function Card({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ background: 'var(--color-panel)', borderRadius: 8, padding: 14, minWidth: 120 }}>
      <div style={{ fontSize: 22, fontWeight: 700 }}>{value}</div>
      <div style={{ fontSize: 12, color: 'var(--color-muted)' }}>{label}</div>
    </div>
  )
}
