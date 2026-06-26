const BASE = import.meta.env.VITE_API_URL || '/api/v1'

export interface ToolEvent { id: string; name: string; args: any; result?: string }
export interface ChatMessage { role: 'user' | 'assistant'; content: string; tools?: ToolEvent[]; streaming?: boolean }

export async function streamChat(
  message: string,
  sessionId: string | undefined,
  onEvent: (name: string, data: any) => void,
  signal?: AbortSignal,
): Promise<void> {
  const resp = await fetch(`${BASE}/agent/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
    signal,
  })
  if (!resp.body) throw new Error('no stream body')
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const events = buffer.split('\n\n')
    buffer = events.pop() || ''
    for (const block of events) {
      const lines = block.split('\n')
      let name = '', data = ''
      for (const ln of lines) {
        if (ln.startsWith('event: ')) name = ln.slice(7).trim()
        else if (ln.startsWith('data: ')) data += ln.slice(6)
      }
      if (name && data) {
        try { onEvent(name, JSON.parse(data)) } catch { onEvent(name, data) }
      }
    }
  }
}

export async function listSessions(): Promise<{ session_id: string; created_at: string }[]> {
  const r = await fetch(`${BASE}/agent/sessions`)
  return r.json()
}

export async function getSession(id: string): Promise<{ role: string; content: string; created_at: string }[]> {
  const r = await fetch(`${BASE}/agent/sessions/${id}`)
  return r.json()
}
