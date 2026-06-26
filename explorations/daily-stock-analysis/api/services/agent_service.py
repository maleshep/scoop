"""AgentService — multi-turn strategy agent with tool calling + SSE.

Uses the GLM provider via the OpenAI SDK's function-calling loop. The system
prompt encodes the US/EU-relevant strategy patterns as prose guidance (YAML
loader is a Phase 3.5 follow-on). Emits SSE events so the frontend can show
thinking/tool calls/generation live.
"""
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Generator

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # explorations/

from openai import OpenAI
import config
from api.agent.tools import call_tool, tool_schemas
from api.db.sqlite import get_conn

SYSTEM_PROMPT = """You are a disciplined equity analysis agent for US + EU markets.
You answer questions about stocks by calling tools to fetch live data, then reasoning over it.

Strategy patterns you can apply (choose based on the user's question):
- bull_trend / ma_golden_cross: trend + moving-average alignment, momentum confirmation
- volume_breakout: 60-day high + volume confirmation
- growth_quality: ROE/margin/revenue-growth durability
- expectation_repricing: analyst target vs price, earnings catalysts
- event_driven: news-driven moves, catalyst attribution
- bottom_volume: oversold (RSI<30) + volume + reversal signals

Rules:
- Always call a tool before making a claim about current data; never fabricate prices/RSI/news.
- Cite the tool output behind each conclusion.
- Be concise. Distinguish catalyst from coincidence.
- You are not giving investment advice — neutral signal attribution.
- Return a clear answer with the evidence.
"""


class AgentService:
    def __init__(self):
        self.client = OpenAI(api_key=config.GLM_API_KEY, base_url=config.GLM_BASE_URL)
        self.model = config.GLM_MODEL

    def chat_stream(self, message: str, session_id: str | None = None) -> Generator[tuple[str, dict], None, None]:
        """Yield (event_name, data) tuples for the SSE streamer."""
        session_id = session_id or f"sess-{uuid.uuid4().hex[:10]}"
        self._save_session(session_id, message)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ]
        yield "thinking", {"session_id": session_id, "message": message}

        for step in range(6):  # cap tool rounds
            resp = self.client.chat.completions.create(
                model=self.model, max_tokens=2000, messages=messages, tools=tool_schemas(),
            )
            choice = resp.choices[0].message

            if choice.tool_calls:
                messages.append(choice.model_dump(exclude_none=True))
                for tc in choice.tool_calls:
                    name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments or "{}")
                    except json.JSONDecodeError:
                        args = {}
                    yield "tool_start", {"id": tc.id, "name": name, "args": args}
                    result = call_tool(name, **args)
                    yield "tool_done", {"id": tc.id, "name": name, "result": result[:2000]}
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
                continue

            # no tool calls -> final answer
            if choice.content:
                yield "generating", {"content": choice.content}
            self._save_message(session_id, "assistant", choice.content or "")
            yield "done", {"session_id": session_id}
            return

        yield "error", {"message": "agent exceeded max tool rounds without a final answer"}

    def _save_session(self, session_id: str, first_message: str) -> None:
        conn = get_conn()
        try:
            conn.execute("CREATE TABLE IF NOT EXISTS agent_sessions (session_id TEXT PRIMARY KEY, created_at TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS agent_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, role TEXT, content TEXT, created_at TEXT)")
            conn.execute("INSERT OR IGNORE INTO agent_sessions VALUES (?, ?)", (session_id, datetime.now().isoformat()))
            conn.execute("INSERT INTO agent_messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                         (session_id, "user", first_message, datetime.now().isoformat()))
            conn.commit()
        finally:
            conn.close()

    def _save_message(self, session_id: str, role: str, content: str) -> None:
        conn = get_conn()
        try:
            conn.execute("INSERT INTO agent_messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                         (session_id, role, content, datetime.now().isoformat()))
            conn.commit()
        finally:
            conn.close()

    def list_sessions(self) -> list[dict]:
        conn = get_conn()
        try:
            rows = conn.execute("SELECT * FROM agent_sessions ORDER BY created_at DESC LIMIT 50").fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def get_session(self, session_id: str) -> list[dict]:
        conn = get_conn()
        try:
            rows = conn.execute("SELECT role, content, created_at FROM agent_messages WHERE session_id=? ORDER BY id", (session_id,)).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()
