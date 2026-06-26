"""Server-Sent Events helper for the agent stream.

Events: thinking, tool_start, tool_done, generating, done, error.
Each event is `event: <name>\\ndata: <json>\\n\\n`.
"""
import json
from typing import Generator


def event(name: str, data: dict) -> str:
    return f"event: {name}\ndata: {json.dumps(data, default=str, ensure_ascii=False)}\n\n"


def stream(handler: callable) -> Generator[str, None, None]:
    """Run a handler that yields (event_name, data) tuples; wrap as SSE."""
    try:
        for name, data in handler():
            yield event(name, data)
    except Exception as e:
        yield event("error", {"message": str(e)})
