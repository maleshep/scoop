import { type AnalysisReport } from '../../api/client'
import { fmtPct, fmtNum, signalEmoji, sparklineSvg } from './helpers'

const ACTION_LABEL: Record<string, string> = {
  watch: '👀 Watch', research_deeper: '🔬 Research', no_action: '—',
}

export function Overview({ report: r }: { report: AnalysisReport }) {
  return (
    <div style={{ background: 'var(--color-panel)', borderRadius: 8, padding: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <h2 style={{ margin: 0, fontSize: 18 }}>
          {signalEmoji(r.signal)} {r.symbol} — {r.name || ''}
        </h2>
        <span style={{ color: 'var(--color-muted)', fontSize: 13 }}>
          {r.price} {r.currency} · 1d {fmtPct(r.change_1d_pct)} · 1w {fmtPct(r.change_1w_pct)} · 1m {fmtPct(r.change_1m_pct)}
        </span>
      </div>
      <div dangerouslySetInnerHTML={{ __html: sparklineSvg(r.sparkline, 280, 50) }}
        style={{ marginTop: 8, opacity: 0.95 }} />
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
        {r.sector && <Pill>{r.sector}</Pill>}
        {r.rsi_14 != null && <Pill>RSI {fmtNum(r.rsi_14)}</Pill>}
        {r.pe_ratio != null && <Pill>P/E {fmtNum(r.pe_ratio)}</Pill>}
        {r.forward_pe != null && <Pill>Fwd P/E {fmtNum(r.forward_pe)}</Pill>}
        {r.volatility_20d != null && <Pill>vol {fmtNum(r.volatility_20d, '%')}</Pill>}
        {r.beta_vs_index != null && <Pill>β {fmtNum(r.beta_vs_index)}</Pill>}
        {r.analyst_target_mean != null && <Pill>target ${fmtNum(r.analyst_target_mean)}</Pill>}
        {r.next_earnings_date && <Pill>⚙ {r.next_earnings_date.slice(0, 10)}</Pill>}
        <Pill highlight={r.action}>{ACTION_LABEL[r.action] || r.action}</Pill>
      </div>
      <div style={{ marginTop: 10, padding: '10px 12px', background: 'var(--color-panel2)', borderRadius: 4, borderLeft: '2px solid var(--color-blue)', fontSize: 13 }}>
        {r.core_conclusion}
      </div>
    </div>
  )
}

function Pill({ children, highlight }: { children: React.ReactNode; highlight?: string }) {
  const bg = highlight === 'research_deeper' ? 'rgba(198,40,40,.25)' : highlight === 'watch' ? 'rgba(21,101,192,.25)' : 'var(--color-panel2)'
  const color = highlight === 'research_deeper' ? '#ff8787' : highlight === 'watch' ? '#74c0fc' : 'var(--color-muted)'
  return <span style={{ background: bg, color, padding: '2px 8px', borderRadius: 10, fontSize: 11 }}>{children}</span>
}
