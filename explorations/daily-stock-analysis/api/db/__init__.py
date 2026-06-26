"""AnalysisRepository — persist + query analysis runs."""
import json
import uuid
from datetime import datetime

from api.db.sqlite import get_conn


class AnalysisRepository:
    def save(self, symbol: str, region: str, payload: dict) -> str:
        run_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        conn = get_conn()
        try:
            conn.execute(
                """INSERT INTO analysis_runs
                   (run_id, symbol, region, signal, confidence, core_conclusion, action, created_at, payload_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id, symbol, region,
                    payload.get("signal"), payload.get("confidence"),
                    payload.get("core_conclusion"), payload.get("action"),
                    datetime.now().isoformat(),
                    json.dumps(payload, default=str, ensure_ascii=False),
                ),
            )
            conn.commit()
            return run_id
        finally:
            conn.close()

    def list(self, limit: int = 50, symbol: str | None = None) -> list[dict]:
        conn = get_conn()
        try:
            if symbol:
                rows = conn.execute(
                    "SELECT * FROM analysis_runs WHERE symbol=? ORDER BY created_at DESC LIMIT ?",
                    (symbol, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM analysis_runs ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get(self, run_id: str) -> dict | None:
        conn = get_conn()
        try:
            row = conn.execute("SELECT * FROM analysis_runs WHERE run_id=?", (run_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
