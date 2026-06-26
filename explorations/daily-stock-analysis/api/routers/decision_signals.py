"""Decision-signals router — aggregates the latest analysis run per watchlist ticker."""
from fastapi import APIRouter

import config
from api.db.sqlite import get_conn

router = APIRouter(prefix="/decision-signals", tags=["decision-signals"])


@router.get("/")
def list_signals() -> list[dict]:
    """For each watchlist ticker, return its most recent analysis signal."""
    conn = get_conn()
    try:
        out = []
        for region, spec in config.WATCHLIST.items():
            for sym in spec["tickers"]:
                row = conn.execute(
                    "SELECT symbol, signal, confidence, action, core_conclusion, created_at FROM analysis_runs "
                    "WHERE symbol=? ORDER BY created_at DESC LIMIT 1", (sym,)
                ).fetchone()
                if row:
                    out.append(dict(row))
                else:
                    out.append({"symbol": sym, "signal": None, "confidence": None,
                                "action": None, "core_conclusion": None, "created_at": None})
        return out
    finally:
        conn.close()
