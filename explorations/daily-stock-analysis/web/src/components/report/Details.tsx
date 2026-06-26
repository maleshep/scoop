import { type AnalysisReport } from '../../api/client'
import { fmtNum, fmtCap } from './helpers'

export function Details({ report: r }: { report: AnalysisReport }) {
  const macd = r.macd
  const rows: [string, string][] = [
    ['P/E (TTM)', fmtNum(r.pe_ratio)], ['Forward P/E', fmtNum(r.forward_pe)],
    ['P/B', fmtNum(r.price_to_book)], ['ROE', fmtNum(r.roe, '%')],
    ['Debt/Equity', fmtNum(r.debt_to_equity)], ['Profit margin', fmtNum(r.profit_margin)],
    ['Revenue growth', fmtNum(r.revenue_growth, '%')], ['Market cap', fmtCap(r.market_cap)],
    ['Dividend yield', fmtNum(r.dividend_yield, '%')], ['Analyst target', fmtNum(r.analyst_target_mean)],
    ['Recommendation', r.recommendation || '—'], ['Next earnings', r.next_earnings_date?.slice(0, 10) || '—'],
    ['RSI(14)', fmtNum(r.rsi_14)], ['MACD', macd ? `${macd.macd_line} / sig ${macd.signal_line} / h ${macd.histogram}` : '—'],
    ['20d avg volume', r.avg_volume_20d ? r.avg_volume_20d.toLocaleString() : '—'],
    ['20d volatility (ann.)', fmtNum(r.volatility_20d, '%')], ['Beta', fmtNum(r.beta)],
    ['Beta vs index', fmtNum(r.beta_vs_index)],
  ]
  return (
    <div style={{ background: 'var(--color-panel)', borderRadius: 8, padding: 14 }}>
      <h4 style={{ margin: '0 0 8px', color: 'var(--color-muted)', fontSize: 11, textTransform: 'uppercase' }}>Fundamentals & technicals</h4>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px 24px', fontSize: 12 }}>
        {rows.map(([k, v]) => (
          <div key={k} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border)', padding: '3px 0' }}>
            <span style={{ color: 'var(--color-muted)' }}>{k}</span>
            <span>{v}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
