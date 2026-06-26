export function fmtPct(v: number | null | undefined): string {
  if (v === null || v === undefined) return '—'
  const sign = v > 0 ? '+' : ''
  return `${sign}${v}%`
}

export function fmtNum(v: number | null | undefined, suffix = ''): string {
  if (v === null || v === undefined) return '—'
  return `${typeof v === 'number' ? v.toFixed(2) : v}${suffix}`
}

export function fmtCap(v: number | null | undefined): string {
  if (v === null || v === undefined) return '—'
  for (const [unit, factor] of [['T', 1e12], ['B', 1e9], ['M', 1e6]] as const) {
    if (v >= factor) return `$${(v / factor).toFixed(2)}${unit}`
  }
  return `$${v.toLocaleString()}`
}

export function pctClass(v: number | null | undefined): string {
  if (v === null || v === undefined) return 'var(--color-muted)'
  if (v > 0) return '#69db7c'
  if (v < 0) return '#ff6b6b'
  return 'var(--color-muted)'
}

export function signalEmoji(s: string | undefined): string {
  return { bullish: '🟢', bearish: '🔴', neutral: '⚪' }[s || 'neutral'] || '⚪'
}

export function sparklineSvg(closes: number[] | undefined, width = 120, height = 30): string {
  const pts = (closes || []).filter((c): c is number => c != null)
  if (pts.length < 2) return ''
  const lo = Math.min(...pts), hi = Math.max(...pts)
  const span = hi - lo || 1
  const step = width / (pts.length - 1)
  const color = pts[pts.length - 1] >= pts[0] ? '#2e7d32' : '#c62828'
  const points = pts.map((c, i) => `${(i * step).toFixed(1)},${(height - ((c - lo) / span) * height).toFixed(1)}`).join(' ')
  return `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg"><polyline fill="none" stroke="${color}" stroke-width="1.2" points="${points}"/></svg>`
}
