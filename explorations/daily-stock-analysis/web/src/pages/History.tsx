import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

interface Run { run_id: string; symbol: string; region: string; signal: string | null; confidence: string | null; action: string | null; core_conclusion: string | null; created_at: string }

const BASE = import.meta.env.VITE_API_URL || '/api/v1'
const EMOJI: Record<string, string> = { bullish: '🟢', bearish: '🔴', neutral: '⚪' }

export function History() {
  const [runs, setRuns] = useState<Run[]>([])
  const [symbol, setSymbol] = useState('')
  const navigate = useNavigate()

  const load = () => {
    const q = symbol ? `?symbol=${symbol}` : ''
    fetch(`${BASE}/history/${q}`).then(r => r.json()).then(setRuns)
  }
  useEffect(() => { load() }, [])

  return (
    <div>
      <h1 style={{ fontSize: 22, margin: '0 0 16px' }}>History</h1>
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input value={symbol} onChange={e => setSymbol(e.target.value)} placeholder="Filter by symbol…" style={{ padding: '8px 10px', background: 'var(--color-panel)', color: 'var(--color-text)', border: '1px solid var(--color-border)', borderRadius: 4 }} />
        <button onClick={load} style={{ padding: '8px 16px', background: 'var(--color-panel2)', color: 'var(--color-text)', border: '1px solid var(--color-border)', borderRadius: 4, cursor: 'pointer' }}>Filter</button>
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse', background: 'var(--color-panel)', borderRadius: 8 }}>
        <thead><tr>{['Symbol', 'Signal', 'Confidence', 'Action', 'Conclusion', 'Time'].map(h => <th key={h} style={{ textAlign: 'left', padding: 8, borderBottom: '1px solid var(--color-border)', color: 'var(--color-muted)', fontSize: 11 }}>{h}</th>)}</tr></thead>
        <tbody>
          {runs.map(r => (
            <tr key={r.run_id} onClick={() => navigate(`/?run=${r.run_id}`)} style={{ cursor: 'pointer' }}>
              <td style={{ padding: 8, borderBottom: '1px solid var(--color-border)' }}><b>{r.symbol}</b></td>
              <td style={{ padding: 8, borderBottom: '1px solid var(--color-border)' }}>{EMOJI[r.signal || ''] || '—'} {r.signal || '—'}</td>
              <td style={{ padding: 8, borderBottom: '1px solid var(--color-border)', color: 'var(--color-muted)' }}>{r.confidence || '—'}</td>
              <td style={{ padding: 8, borderBottom: '1px solid var(--color-border)' }}>{r.action || '—'}</td>
              <td style={{ padding: 8, borderBottom: '1px solid var(--color-border)', fontSize: 12, color: 'var(--color-muted)', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.core_conclusion || '—'}</td>
              <td style={{ padding: 8, borderBottom: '1px solid var(--color-border)', color: 'var(--color-muted)', fontSize: 11 }}>{r.created_at.slice(0, 16)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
