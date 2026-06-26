"""AnalysisService — adapter over the existing engine.

Reuses data_fetcher / news_fetcher / analyzer directly. Enforces the JSON-safe
boundary: the raw _ticker_snapshot carries a pandas `history` DataFrame that
must never reach serialization — fetch_region already pops it, and we assert
here as a backstop.
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # explorations/

import analyzer
import config
import data_fetcher
import news_fetcher
from api.db import AnalysisRepository
from shared.gaps import GapsLog

# Region auto-detection by ticker suffix.
_EU_SUFFIXES = (".DE", ".L", ".PA", ".AS", ".MI", ".MC", ".SW")


def _detect_region(symbol: str) -> str:
    return "EU" if symbol.upper().endswith(_EU_SUFFIXES) else "US"


def _is_json_safe(d: dict) -> None:
    """Assert no pandas objects leaked into a value we're about to serialize."""
    for v in d.values():
        if hasattr(v, "to_json") or "DataFrame" in type(v).__name__:
            raise TypeError(f"non-serializable {type(v).__name__} in analysis payload")


class AnalysisService:
    def __init__(self, provider: analyzer.LLMProvider | None = None):
        self.provider = provider or analyzer.default_provider()
        self.repo = AnalysisRepository()

    def analyze_stock(self, symbol: str, region: str | None = None) -> dict:
        region = region or _detect_region(symbol)
        symbol = symbol.upper()
        run_id_stamp = datetime.now().strftime("%Y-%m-%d")
        gaps = GapsLog(project="daily-stocks", run_id=run_id_stamp, output_dir=Path("output"))

        # fetch_region gives the index + peer-ranked tickers (history already popped).
        rd = data_fetcher.fetch_region(region)
        idx = rd["index"]

        # Find the requested ticker within the region, or snapshot it ad hoc.
        tk = next((t for t in rd["tickers"] if t["symbol"] == symbol), None)
        if tk is None:
            # Off-watchlist symbol: snapshot directly, then strip the DataFrame.
            tk = data_fetcher._ticker_snapshot(symbol)
            tk.pop("history", None)
        if "error" in tk:
            gaps.add(symbol, "price", "blocker", f"data fetch error: {tk['error']}")
            return {"run_id": "", "symbol": symbol, "region": region,
                    "report": {"symbol": symbol, "error": tk["error"]}, "gaps": gaps.summary()}

        news = news_fetcher.fetch_news(symbol, gaps=gaps)
        result = analyzer.analyze_ticker_with(self.provider, tk, news, region, idx, gaps=gaps)
        _is_json_safe(result)

        from api.db.sqlite import log_usage
        log_usage(config.MODEL_PROVIDER, "analyze", symbol)
        run_id = self.repo.save(symbol, region, result)

        # Evaluate any alert rules for this symbol (inline, no scheduler).
        from api.services.alert_service import AlertService
        triggered = AlertService().evaluate(symbol, result)

        return {"run_id": run_id, "symbol": symbol, "region": region,
                "report": result, "gaps": gaps.summary(),
                "alert_triggers": triggered}

    def list_history(self, limit: int = 50, symbol: str | None = None) -> list[dict]:
        return self.repo.list(limit=limit, symbol=symbol)

    def get_run(self, run_id: str) -> dict | None:
        row = self.repo.get(run_id)
        if not row:
            return None
        row["payload"] = __import__("json").loads(row.pop("payload_json"))
        return row
