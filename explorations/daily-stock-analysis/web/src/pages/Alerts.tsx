import { useState, useEffect } from 'react'

interface Rule { id: number; symbol: string; rule_type: string; threshold: number; active: number; created_at: string }
interface Event { id: number; alert_id: number; symbol: string; rule_type: string; triggered_at: string; message: string }

const BASE = import.meta.env.VITE_API_URL || '/api/v1'
const RULE_TYPES = ['rsi_above', 'rsi_below', 'price_above', 'price_below', 'signal_change']

export function Alerts() {
  const [rules, setRules] = useState<Rule[]>([])
  const [events, setEvents] = useState<Event[]>([])
  const [form, setForm] = useState({ symbol: '', rule_type: 'rsi_below', threshold: '30' })

  const load = () => {
    fetch(`${BASE}/alerts/rules`).then(r => r.json()).then(setRules)
    fetch(`${BASE}/alerts/events`).then(r => r.json()).then(setEvents)
  }
  useEffect(() => { load() }, [])

  const add = async () => {
    if (!form.symbol) return
    await fetch(`${BASE}/alerts/rules`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol: form.symbol, rule_type: form.rule_type, threshold: parseFloat(form.threshold) }),
    })
    setForm({ ...form, symbol: '' })
    load()
  }
  const toggle = async (r: Rule) => { await fetch(`${BASE}/alerts/rules/${r.id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ active: !r.active }) }); load() }
  const del = async (id: number) => { await fetch(`${BASE}/alerts/rules/${id}`, { method: 'DELETE' }); load() }

  return (
    <div>
      <h1 style={{ fontSize: 22, margin: '0 0 16px' }}>Alerts</h1>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <div>
          <h3 style={{ color: 'var(--color-muted)', fontSize: 13, textTransform: 'uppercase', marginBottom: 8 }}>Rules</h3>
          {rules.length === 0 ? <div style={{ color: 'var(--color-muted)' }}>No rules. Alerts fire inline when you analyze a matching ticker on the Home page.</div> : rules.map(r => (
            <div key={r.id} style={{ background: 'var(--color-panel)', borderRadius: 6, padding: 10, marginBottom: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 13 }}><b>{r.symbol}</b> · {r.rule_type} {r.threshold} {r.active ? '🟢' : '⚪'}</span>
              <span>
                <button onClick={() => toggle(r)} style={{ background: 'none', border: '1px solid var(--color-border)', color: 'var(--color-muted)', borderRadius: 3, padding: '2px 8px', cursor: 'pointer', marginRight: 4, fontSize: 11 }}>{r.active ? 'disable' : 'enable'}</button>
                <button onClick={() => del(r.id)} style={{ background: 'none', border: 'none', color: '#ff6b6b', cursor: 'pointer' }}>✕</button>
              </span>
            </div>
          ))}
          <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 8, maxWidth: 320 }}>
            <input placeholder="Symbol (AAPL)" value={form.symbol} onChange={e => setForm({ ...form, symbol: e.target.value })} style={inputStyle} />
            <select value={form.rule_type} onChange={e => setForm({ ...form, rule_type: e.target.value })} style={inputStyle}>
              {RULE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
            <input placeholder="Threshold (e.g. 30 for RSI, 280 for price)" value={form.threshold} onChange={e => setForm({ ...form, threshold: e.target.value })} style={inputStyle} />
            <button onClick={add} style={{ padding: '8px 16px', background: 'var(--color-blue)', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer' }}>Add rule</button>
          </div>
        </div>
        <div>
          <h3 style={{ color: 'var(--color-muted)', fontSize: 13, textTransform: 'uppercase', marginBottom: 8 }}>Trigger history</h3>
          {events.length === 0 ? <div style={{ color: 'var(--color-muted)' }}>No triggers yet.</div> : events.map(e => (
            <div key={e.id} style={{ background: 'var(--color-panel)', borderRadius: 6, padding: 10, marginBottom: 6, fontSize: 13 }}>
              <b>{e.symbol}</b> · {e.message}
              <div style={{ color: 'var(--color-muted)', fontSize: 11, marginTop: 4 }}>{e.triggered_at.slice(0, 16)}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

const inputStyle = { padding: '8px 10px', background: 'var(--color-panel)', color: 'var(--color-text)', border: '1px solid var(--color-border)', borderRadius: 4, fontSize: 14 } as const
