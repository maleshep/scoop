export function Diagnostics({ gaps }: { gaps: { entries: any[]; total: number } }) {
  const sevColor: Record<string, string> = { blocker: '#ff6b6b', weak: '#ffd43b', conflict: '#74c0fc' }
  return (
    <div style={{ background: 'var(--color-panel)', borderRadius: 8, padding: 14 }}>
      <h4 style={{ margin: '0 0 8px', color: 'var(--color-muted)', fontSize: 11, textTransform: 'uppercase' }}>
        Gaps ({gaps.total}) — what this analysis could not determine
      </h4>
      {gaps.entries.map((g, i) => (
        <div key={i} style={{ fontSize: 12, padding: '3px 0', color: 'var(--color-text)' }}>
          <span style={{ color: sevColor[g.severity] || 'var(--color-muted)', fontWeight: 600 }}>[{g.severity}]</span>{' '}
          <span style={{ color: 'var(--color-muted)' }}>{g.subject} · {g.category}:</span> {g.note}
        </div>
      ))}
    </div>
  )
}
