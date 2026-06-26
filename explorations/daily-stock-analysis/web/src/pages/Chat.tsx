import { useState, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { streamChat, type ChatMessage, type ToolEvent } from '../api/agent'

export function Chat() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | undefined>()
  const abortRef = useRef<AbortController | null>(null)

  const send = async () => {
    if (!input.trim() || loading) return
    const userMsg: ChatMessage = { role: 'user', content: input }
    const assistantMsg: ChatMessage = { role: 'assistant', content: '', tools: [], streaming: true }
    setMessages(m => [...m, userMsg, assistantMsg])
    setInput('')
    setLoading(true)
    const ctrl = new AbortController()
    abortRef.current = ctrl
    try {
      await streamChat(userMsg.content, sessionId, (name, data) => {
        if (name === 'thinking' && data.session_id) setSessionId(data.session_id)
        if (name === 'tool_start') {
          setMessages(m => {
            const copy = [...m]
            const last = copy[copy.length - 1]
            last.tools = [...(last.tools || []), { id: data.id, name: data.name, args: data.args }]
            return copy
          })
        }
        if (name === 'tool_done') {
          setMessages(m => {
            const copy = [...m]
            const last = copy[copy.length - 1]
            const t = (last.tools || []).find(t => t.id === data.id)
            if (t) t.result = data.result
            return copy
          })
        }
        if (name === 'generating') {
          setMessages(m => {
            const copy = [...m]
            copy[copy.length - 1].content += data.content || ''
            return copy
          })
        }
        if (name === 'done' || name === 'error') {
          setMessages(m => {
            const copy = [...m]
            copy[copy.length - 1].streaming = false
            if (name === 'error') copy[copy.length - 1].content += `\n\n⚠️ ${data.message}`
            return copy
          })
        }
      }, ctrl.signal)
    } catch (e: any) {
      if (e.name !== 'AbortError') {
        setMessages(m => { const c = [...m]; c[c.length - 1].content += `\n\n⚠️ ${e.message}`; return c })
      }
    } finally {
      setLoading(false)
      abortRef.current = null
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 48px)' }}>
      <h1 style={{ fontSize: 22, margin: '0 0 16px' }}>Strategy Agent</h1>
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
        {messages.length === 0 && (
          <div style={{ color: 'var(--color-muted)', padding: 24 }}>
            Ask the agent anything about a US/EU stock — it calls live data tools (quote, technicals, fundamentals, news, peers) and reasons over them.
            <br />e.g. "Why is AAPL down today? Is it a buy?" or "Compare ASML and SAP technically."
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} style={{
            background: m.role === 'user' ? 'var(--color-panel2)' : 'var(--color-panel)',
            borderRadius: 8, padding: 14, alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: m.role === 'user' ? '70%' : '95%',
          }}>
            {m.tools && m.tools.length > 0 && (
              <div style={{ marginBottom: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
                {m.tools.map((t, j) => (
                  <details key={j} style={{ fontSize: 12, color: 'var(--color-muted)' }}>
                    <summary style={{ cursor: 'pointer' }}>🔧 {t.name}({JSON.stringify(t.args).slice(0, 60)}) {t.result ? '✓' : '⏳'}</summary>
                    <pre style={{ fontSize: 11, overflowX: 'auto', color: 'var(--color-text)', margin: '4px 0' }}>{t.result?.slice(0, 600)}</pre>
                  </details>
                ))}
              </div>
            )}
            {m.content && (
              <div className="prose-invert" style={{ fontSize: 14, lineHeight: 1.6 }}>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
              </div>
            )}
            {m.streaming && !m.content && <span style={{ color: 'var(--color-muted)' }}>…</span>}
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
          placeholder="Ask about a stock…"
          style={{ flex: 1, padding: '10px 12px', background: 'var(--color-panel)', color: 'var(--color-text)', border: '1px solid var(--color-border)', borderRadius: 6, fontSize: 14 }}
        />
        <button onClick={send} disabled={loading || !input.trim()}
          style={{ padding: '10px 20px', background: loading ? 'var(--color-panel2)' : 'var(--color-blue)', color: 'white', border: 'none', borderRadius: 6, cursor: loading ? 'wait' : 'pointer', fontSize: 14 }}>
          {loading ? '…' : 'Send'}
        </button>
      </div>
    </div>
  )
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
