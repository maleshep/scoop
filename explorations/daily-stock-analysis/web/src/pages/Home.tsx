import { useState } from 'react'
import { analysisApi } from '../api/analysis'
import type { AnalyzeResponse, StockSearchResult, HistoryItem } from '../api/client'
import { StockAutocomplete } from '../components/StockAutocomplete'
import { ReportSummary } from '../components/report/ReportSummary'
import { fmtPct, signalEmoji } from '../components/report/helpers'

export function Home() {
  const [selected, setSelected] = useState<StockSearchResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [error, setError] = useState('')
  const [history, setHistory] = useState<HistoryItem[]>([])

  const run = async () => {
    if (!selected) return
    setLoading(true); setError(''); setResult(null)
    try {
      const res = await analysisApi.analyze(selected.symbol, selected.region)
      setResult(res)
      const h = await analysisApi.history(8)
      setHistory(h)
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message)
    } finally { setLoading(false) }
  }

  return (
    <div>
      <h1 style={{ margin: '0 0 16px', fontSize: 22 }}>Daily Stock Analysis</h1>
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <StockAutocomplete onSelect={setSelected} />
        <button onClick={run} disabled={!selected || loading}
          style={{ padding: '10px 20px', background: loading ? 'var(--color-panel2)' : 'var(--color-blue)', color: 'white', border: 'none', borderRadius: 6, cursor: loading ? 'wait' : 'pointer', fontSize: 14 }}>
          {loading ? 'Analyzing…' : 'Analyze'}
        </button>
      </div>
      {error && <div style={{ color: '#ff6b6b', marginBottom: 16 }}>{error}</div>}
      {loading && <div style={{ color: 'var(--color-muted)', padding: 24 }}>Fetching data + news, calling GLM-5.2… this takes ~30s</div>}
      {result && <ReportSummary report={result.report} gaps={result.gaps} />}

      {!result && !loading && history.length === 0 && (
        <div style={{ marginTop: 24 }}>
          <button onClick={() => analysisApi.history(8).then(setHistory)}
            style={{ background: 'none', border: '1px solid var(--color-border)', color: 'var(--color-muted)', padding: '6px 12px', borderRadius: 4, cursor: 'pointer' }}>
            Load recent history
          </button>
        </div>
      )}
      {history.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h3 style={{ fontSize: 14, color: 'var(--color-muted)', marginBottom: 8 }}>Recent runs</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {history.map(h => (
              <button key={h.run_id} onClick={() => analysisApi.getRun(h.run_id).then(d => setResult({ run_id: d.run_id, symbol: d.symbol, region: d.region, report: d.payload, gaps: { project: 'daily-stocks', run_id: d.run_id, total: 0, by_severity: {}, entries: [] } }))}
                style={{ textAlign: 'left', background: 'var(--color-panel)', border: '1px solid var(--color-border)', borderRadius: 6, padding: '8px 12px', cursor: 'pointer', color: 'var(--color-text)', display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                <span>{signalEmoji(h.signal || 'neutral')} <b>{h.symbol}</b> · {h.action} · {(h.core_conclusion || '').slice(0, 80)}</span>
                <span style={{ color: 'var(--color-muted)', fontSize: 11 }}>{h.created_at.slice(0, 16)}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
