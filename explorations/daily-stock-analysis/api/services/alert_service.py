"""AlertService — evaluates alert rules against a fresh analysis result.

No scheduler; evaluation is inline, called by AnalysisService after each run.
Supported rule_types: rsi_above, rsi_below, signal_change, price_above, price_below.
"""
from api.db import AlertRepository


class AlertService:
    def __init__(self):
        self.repo = AlertRepository()

    def evaluate(self, symbol: str, report: dict) -> list[dict]:
        """Check all active rules for this symbol; record + return any triggered."""
        triggered = []
        symbol = symbol.upper()
        for rule in self.repo.list_rules(active_only=True):
            if rule["symbol"] != symbol:
                continue
            msg = self._check(rule, report)
            if msg:
                self.repo.record_event(rule["id"], msg)
                triggered.append({"rule": rule, "message": msg})
        return triggered

    def _check(self, rule: dict, r: dict) -> str | None:
        rt = rule["rule_type"]
        th = rule["threshold"]
        if rt == "rsi_above" and r.get("rsi_14") is not None and r["rsi_14"] > th:
            return f"RSI {r['rsi_14']} crossed above {th}"
        if rt == "rsi_below" and r.get("rsi_14") is not None and r["rsi_14"] < th:
            return f"RSI {r['rsi_14']} crossed below {th}"
        if rt == "price_above" and r.get("price") is not None and r["price"] > th:
            return f"Price {r['price']} crossed above {th}"
        if rt == "price_below" and r.get("price") is not None and r["price"] < th:
            return f"Price {r['price']} crossed below {th}"
        if rt == "signal_change" and r.get("signal") == th_str_to_signal(th):
            return f"Signal changed to {r['signal']}"
        return None


def th_str_to_signal(th: float) -> str:
    # threshold stored as float but signal_change uses 1=bullish,2=bearish,3=neutral
    return {1: "bullish", 2: "bearish", 3: "neutral"}.get(int(th), "")
