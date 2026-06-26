import { useState, useRef, useEffect } from 'react'
import { analysisApi } from '../api/analysis'
import type { StockSearchResult } from '../api/client'

const WATCHLIST = [
  { symbol: 'AAPL', name: 'Apple', region: 'US' }, { symbol: 'MSFT', name: 'Microsoft', region: 'US' },
  { symbol: 'NVDA', name: 'NVIDIA', region: 'US' }, { symbol: 'JPM', name: 'JPMorgan', region: 'US' },
  { symbol: 'XOM', name: 'Exxon Mobil', region: 'US' },
  { symbol: 'SAP.DE', name: 'SAP SE', region: 'EU' }, { symbol: 'SHEL.L', name: 'Shell', region: 'EU' },
  { symbol: 'ASML.AS', name: 'ASML', region: 'EU' }, { symbol: 'AIR.PA', name: 'Airbus', region: 'EU' },
  { symbol: 'SIE.DE', name: 'Siemens', region: 'EU' },
]

export function StockAutocomplete({ onSelect }: { onSelect: (s: StockSearchResult) => void }) {
  const [q, setQ] = useState('')
  const [suggestions, setSuggestions] = useState<StockSearchResult[]>([])
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  useEffect(() => {
    if (!q.trim()) { setSuggestions([]); return }
    const lower = q.toLowerCase()
    const local = WATCHLIST.filter(w =>
      w.symbol.toLowerCase().includes(lower) || w.name.toLowerCase().includes(lower)
    )
    setSuggestions(local)
    analysisApi.searchStocks(q).then((remote: StockSearchResult[]) => {
      const merged = [...local]
      for (const r of remote) {
        if (!merged.some(m => m.symbol === r.symbol)) merged.push(r)
      }
      setSuggestions(merged.slice(0, 10))
    }).catch(() => {})
    setActive(0)
  }, [q])

  const pick = (s: StockSearchResult) => { onSelect(s); setQ(`${s.symbol} — ${s.name}`); setOpen(false) }

  return (
    <div ref={ref} style={{ position: 'relative', flex: 1 }}>
      <input
        value={q}
        onChange={e => { setQ(e.target.value); setOpen(true) }}
        onFocus={() => setOpen(true)}
        onKeyDown={e => {
          if (!open) return
          if (e.key === 'ArrowDown') { e.preventDefault(); setActive(a => Math.min(a + 1, suggestions.length - 1)) }
          if (e.key === 'ArrowUp') { e.preventDefault(); setActive(a => Math.max(a - 1, 0)) }
          if (e.key === 'Enter' && suggestions[active]) pick(suggestions[active])
        }}
        placeholder="Search ticker or name (e.g. AAPL, SAP.DE)…"
        style={{ width: '100%', padding: '10px 12px', background: 'var(--color-panel)', color: 'var(--color-text)', border: '1px solid var(--color-border)', borderRadius: 6, fontSize: 14 }}
      />
      {open && suggestions.length > 0 && (
        <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, background: 'var(--color-panel)', border: '1px solid var(--color-border)', borderRadius: 6, marginTop: 2, zIndex: 10, maxHeight: 300, overflowY: 'auto' }}>
          {suggestions.map((s, i) => (
            <div key={s.symbol} onClick={() => pick(s)}
              style={{ padding: '8px 12px', cursor: 'pointer', background: i === active ? 'var(--color-panel2)' : 'transparent', display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
              <span><b>{s.symbol}</b> <span style={{ color: 'var(--color-muted)' }}>{s.name}</span></span>
              <span style={{ color: 'var(--color-muted)', fontSize: 11 }}>{s.region}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
