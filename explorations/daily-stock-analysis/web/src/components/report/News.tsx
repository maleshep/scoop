import { type NewsItem } from '../../api/client'

export function News({ news }: { news?: NewsItem[] }) {
  if (!news || news.length === 0) return null
  return (
    <div style={{ background: 'var(--color-panel)', borderRadius: 8, padding: 14 }}>
      <h4 style={{ margin: '0 0 8px', color: 'var(--color-muted)', fontSize: 11, textTransform: 'uppercase' }}>Recent news</h4>
      {news.map((n, i) => (
        <div key={i} style={{ padding: '4px 0', fontSize: 12 }}>
          {n.url ? (
            <a href={n.url} target="_blank" rel="noopener" style={{ color: '#74c0fc', textDecoration: 'none' }}>
              {n.title}
            </a>
          ) : <span>{n.title}</span>}
          {n.sources && n.sources.length > 0 && (
            <span style={{ color: 'var(--color-muted)', marginLeft: 8, fontSize: 11 }}>
              {n.sources.join(', ')}
            </span>
          )}
        </div>
      ))}
    </div>
  )
}
