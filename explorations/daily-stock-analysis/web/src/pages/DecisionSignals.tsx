import { useState, useEffect } from 'react'

interface Signal { symbol: string; signal: string | null; confidence: string | null; action: string | null; core_conclusion: string | null; created_at: string | null }

const BASE = import.meta.env.VITE_API_URL || '/api/v1'
const EMOJI: Record<string, string> = { bullish: '🟢', bearish: '🔴', neutral: '⚪' }

export function DecisionSignals() {
  const [signals, setSignals] = useState<Signal[]>([])
  useEffect(() => { fetch(`${BASE}/decision-signals/`).then(r => r.json()).then(setSignals) }, [])

  const byAction = (a: string | null) => signals.filter(s => s.action === a)
  const counts = {
    research_deeper: byAction('research_deeper').length,
    watch: byAction('watch').length,
    no_action: byAction('no_action').length,
  }

  return (
    <div>
      <h1 style={{ fontSize: 22, margin: '0 0 16px' }}>Decision Signals</h1>
      <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <Card label="🔬 Research deeper" value={counts.research_deeper} color="#ff8787" />
        <Card label="👀 Watch" value={counts.watch} color="#74c0fc" />
        <Card label="— No action" value={counts.no_action} color="var(--color-muted)" />
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse', background: 'var(--color-panel)', borderRadius: 8 }}>
        <thead><tr>{['Symbol', 'Signal', 'Confidence', 'Action', 'Conclusion', 'Last run'].map(h => <th key={h} style={{ textAlign: 'left', padding: 8, borderBottom: '1px solid var(--color-border)', color: 'var(--color-muted)', fontSize: 11 }}>{h}</th>)}</tr></thead>
        <tbody>
          {signals.map(s => (
            <tr key={s.symbol}>
              <td style={{ padding: 8, borderBottom: '1px solid var(--color-border)' }}><b>{s.symbol}</b></td>
              <td style={{ padding: 8, borderBottom: '1px solid var(--color-border)' }}>{EMOJI[s.signal || ''] || '—'} {s.signal || '—'}</td>
              <td style={{ padding: 8, borderBottom: '1px solid var(--color-border)', color: 'var(--color-muted)' }}>{s.confidence || '—'}</td>
              <td style={{ padding: 8, borderBottom: '1px solid var(--color-border)' }}>{s.action || '—'}</td>
              <td style={{ padding: 8, borderBottom: '1px solid var(--color-border)', fontSize: 12, color: 'var(--color-muted)', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.core_conclusion || '—'}</td>
              <td style={{ padding: 8, borderBottom: '1px solid var(--color-border)', color: 'var(--color-muted)', fontSize: 11 }}>{s.created_at?.slice(0, 16) || 'never'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Card({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div style={{ background: 'var(--color-panel)', borderRadius: 8, padding: 14, minWidth: 140 }}>
      <div style={{ fontSize: 22, fontWeight: 700, color }}>{value}</div>
      <div style={{ fontSize: 12, color: 'var(--color-muted)' }}>{label}</div>
    </div>
  )
}
