"""Agent router — POST /chat/stream (SSE), GET /sessions, GET /sessions/{id}."""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from api.agent.sse import stream
from api.services import AgentService

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat/stream")
def chat_stream(body: dict) -> StreamingResponse:
    message = body.get("message", "")
    session_id = body.get("session_id")
    service = AgentService()

    def gen():
        yield from stream(lambda: service.chat_stream(message, session_id))

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.get("/sessions")
def list_sessions() -> list[dict]:
    return AgentService().list_sessions()


@router.get("/sessions/{session_id}")
def get_session(session_id: str) -> list[dict]:
    return AgentService().get_session(session_id)


@router.get("/skills")
def skills() -> list[dict]:
    """The strategy patterns the agent can apply (prose guidance for now)."""
    return [
        {"name": s, "description": d}
        for s, d in [
            ("bull_trend", "Trend + moving-average alignment, momentum confirmation"),
            ("ma_golden_cross", "Golden cross MA setup"),
            ("volume_breakout", "60-day high + volume confirmation"),
            ("growth_quality", "ROE/margin/revenue-growth durability"),
            ("expectation_repricing", "Analyst target vs price, earnings catalysts"),
            ("event_driven", "News-driven moves, catalyst attribution"),
            ("hot_theme", "Sector/theme momentum"),
            ("bottom_volume", "Oversold (RSI<30) + volume + reversal signals"),
            ("box_oscillation", "Range-bound mean reversion"),
            ("emotion_cycle", "Sentiment-cycle positioning"),
            ("shrink_pullback", "Pullback-in-uptrend entry"),
        ]
    ]
