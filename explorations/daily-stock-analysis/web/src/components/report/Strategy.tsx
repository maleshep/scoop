import { type AnalysisReport } from '../../api/client'

export function Strategy({ report: r }: { report: AnalysisReport }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
      <div style={{ background: 'var(--color-panel)', borderRadius: 8, padding: 14 }}>
        <h4 style={{ margin: '0 0 8px', color: 'var(--color-muted)', fontSize: 11, textTransform: 'uppercase' }}>Drivers</h4>
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, lineHeight: 1.5 }}>
          {(r.drivers || []).map((d, i) => <li key={i}>{d}</li>)}
        </ul>
      </div>
      <div style={{ background: 'var(--color-panel)', borderRadius: 8, padding: 14 }}>
        <h4 style={{ margin: '0 0 8px', color: 'var(--color-muted)', fontSize: 11, textTransform: 'uppercase' }}>Risks</h4>
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, lineHeight: 1.5 }}>
          {(r.risks || []).map((d, i) => <li key={i}>{d}</li>)}
        </ul>
      </div>
    </div>
  )
}
