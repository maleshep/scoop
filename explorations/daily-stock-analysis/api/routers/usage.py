"""Usage router — LLM call counts by day + provider."""
from fastapi import APIRouter

from api.db.sqlite import get_conn

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/summary")
def summary(days: int = 30) -> dict:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT date, provider, endpoint, COUNT(*) as calls FROM usage_log "
            "WHERE date >= date('now', ?) GROUP BY date, provider, endpoint ORDER BY date DESC",
            (f"-{days} days",),
        ).fetchall()
        by_provider: dict[str, int] = {}
        by_date: dict[str, int] = {}
        for r in rows:
            by_provider[r["provider"]] = by_provider.get(r["provider"], 0) + r["calls"]
            by_date[r["date"]] = by_date.get(r["date"], 0) + r["calls"]
        total = sum(by_provider.values())
        return {"total": total, "by_provider": by_provider, "by_date": by_date, "rows": [dict(r) for r in rows]}
    finally:
        conn.close()
