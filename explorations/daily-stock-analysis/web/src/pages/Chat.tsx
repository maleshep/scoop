export function Chat() {
  return <Placeholder title="Agent Chat" note="Phase 3 — multi-turn strategy agent with SSE streaming." />
}

export function Placeholder({ title, note }: { title: string; note: string }) {
  return (
    <div>
      <h1 style={{ fontSize: 22 }}>{title}</h1>
      <div style={{ color: 'var(--color-muted)', padding: 24, background: 'var(--color-panel)', borderRadius: 8, marginTop: 16 }}>
        {note}
      </div>
    </div>
  )
}
