import { useState, useEffect } from 'react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'

interface Holding { id: number; symbol: string; region: string; shares: number; cost_basis: number; added_at: string }

const BASE = import.meta.env.VITE_API_URL || '/api/v1'
const COLORS = ['#1565c0', '#2e7d32', '#b8860b', '#c62828', '#6a1b9a', '#00838f', '#ef6c00', '#4e342e']

export function Portfolio() {
  const [holdings, setHoldings] = useState<Holding[]>([])
  const [form, setForm] = useState({ symbol: '', shares: '', cost_basis: '' })

  const load = () => fetch(`${BASE}/portfolio/holdings`).then(r => r.json()).then(setHoldings)
  useEffect(() => { load() }, [])

  const add = async () => {
    if (!form.symbol || !form.shares || !form.cost_basis) return
    await fetch(`${BASE}/portfolio/holdings`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol: form.symbol, shares: parseFloat(form.shares), cost_basis: parseFloat(form.cost_basis) }),
    })
    setForm({ symbol: '', shares: '', cost_basis: '' })
    load()
  }

  const del = async (id: number) => { await fetch(`${BASE}/portfolio/holdings/${id}`, { method: 'DELETE' }); load() }

  const totalCost = holdings.reduce((s, h) => s + h.shares * h.cost_basis, 0)
  const pieData = holdings.map(h => ({ name: h.symbol, value: +(h.shares * h.cost_basis).toFixed(0) }))

  return (
    <div>
      <h1 style={{ fontSize: 22, margin: '0 0 16px' }}>Portfolio</h1>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <div>
          <h3 style={{ color: 'var(--color-muted)', fontSize: 13, textTransform: 'uppercase', marginBottom: 8 }}>Holdings</h3>
          {holdings.length === 0 ? <div style={{ color: 'var(--color-muted)' }}>No holdings yet.</div> : (
            <table style={{ width: '100%', borderCollapse: 'collapse', background: 'var(--color-panel)', borderRadius: 8 }}>
              <thead><tr>{['Symbol', 'Region', 'Shares', 'Cost', 'Value', ''].map(h => <th key={h} style={{ textAlign: 'left', padding: 8, borderBottom: '1px solid var(--color-border)', color: 'var(--color-muted)', fontSize: 11 }}>{h}</th>)}</tr></thead>
              <tbody>
                {holdings.map(h => (
                  <tr key={h.id}>
                    <td style={{ padding: 8, borderBottom: '1px solid var(--color-border)' }}><b>{h.symbol}</b></td>
                    <td style={{ padding: 8, borderBottom: '1px solid var(--color-border)', color: 'var(--color-muted)' }}>{h.region}</td>
                    <td style={{ padding: 8, borderBottom: '1px solid var(--color-border)' }}>{h.shares}</td>
                    <td style={{ padding: 8, borderBottom: '1px solid var(--color-border)' }}>${h.cost_basis}</td>
                    <td style={{ padding: 8, borderBottom: '1px solid var(--color-border)' }}>${(h.shares * h.cost_basis).toFixed(0)}</td>
                    <td style={{ padding: 8, borderBottom: '1px solid var(--color-border)' }}><button onClick={() => del(h.id)} style={{ background: 'none', border: 'none', color: '#ff6b6b', cursor: 'pointer' }}>✕</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <div style={{ marginTop: 8, fontSize: 13 }}>Total cost basis: <b>${totalCost.toFixed(0)}</b></div>
        </div>
        <div>
          <h3 style={{ color: 'var(--color-muted)', fontSize: 13, textTransform: 'uppercase', marginBottom: 8 }}>Add holding</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxWidth: 300 }}>
            <input placeholder="Symbol (AAPL)" value={form.symbol} onChange={e => setForm({ ...form, symbol: e.target.value })} style={inputStyle} />
            <input placeholder="Shares" type="number" value={form.shares} onChange={e => setForm({ ...form, shares: e.target.value })} style={inputStyle} />
            <input placeholder="Cost basis" type="number" value={form.cost_basis} onChange={e => setForm({ ...form, cost_basis: e.target.value })} style={inputStyle} />
            <button onClick={add} style={{ padding: '8px 16px', background: 'var(--color-blue)', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer' }}>Add</button>
          </div>
          {pieData.length > 0 && (
            <div style={{ marginTop: 16, height: 240 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart><Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={(e) => e.name}>
                  {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie><Tooltip /><Legend /></PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

const inputStyle = { padding: '8px 10px', background: 'var(--color-panel)', color: 'var(--color-text)', border: '1px solid var(--color-border)', borderRadius: 4, fontSize: 14 } as const
