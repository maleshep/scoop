"""Portfolio + alerts + decision-signals tables and repositories."""
import json
from datetime import datetime

from api.db.sqlite import get_conn


def init_portfolio_db() -> None:
    conn = get_conn()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS portfolio_holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                region TEXT,
                shares REAL NOT NULL,
                cost_basis REAL NOT NULL,
                added_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                threshold REAL NOT NULL,
                active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS alert_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id INTEGER NOT NULL,
                triggered_at TEXT NOT NULL,
                message TEXT NOT NULL,
                FOREIGN KEY (alert_id) REFERENCES alerts(id)
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


class PortfolioRepository:
    def list_holdings(self) -> list[dict]:
        conn = get_conn()
        try:
            return [dict(r) for r in conn.execute("SELECT * FROM portfolio_holdings ORDER BY added_at DESC").fetchall()]
        finally:
            conn.close()

    def add_holding(self, symbol: str, region: str, shares: float, cost_basis: float) -> dict:
        conn = get_conn()
        try:
            cur = conn.execute(
                "INSERT INTO portfolio_holdings (symbol, region, shares, cost_basis, added_at) VALUES (?, ?, ?, ?, ?)",
                (symbol.upper(), region, shares, cost_basis, datetime.now().isoformat()),
            )
            conn.commit()
            return {"id": cur.lastrowid, "symbol": symbol.upper(), "region": region, "shares": shares, "cost_basis": cost_basis}
        finally:
            conn.close()

    def delete_holding(self, hid: int) -> None:
        conn = get_conn()
        try:
            conn.execute("DELETE FROM portfolio_holdings WHERE id=?", (hid,))
            conn.commit()
        finally:
            conn.close()


class AlertRepository:
    def list_rules(self, active_only: bool = False) -> list[dict]:
        conn = get_conn()
        try:
            q = "SELECT * FROM alerts"
            if active_only:
                q += " WHERE active=1"
            q += " ORDER BY created_at DESC"
            return [dict(r) for r in conn.execute(q).fetchall()]
        finally:
            conn.close()

    def add_rule(self, symbol: str, rule_type: str, threshold: float) -> dict:
        conn = get_conn()
        try:
            cur = conn.execute(
                "INSERT INTO alerts (symbol, rule_type, threshold, active, created_at) VALUES (?, ?, ?, 1, ?)",
                (symbol.upper(), rule_type, threshold, datetime.now().isoformat()),
            )
            conn.commit()
            return {"id": cur.lastrowid, "symbol": symbol.upper(), "rule_type": rule_type, "threshold": threshold, "active": 1}
        finally:
            conn.close()

    def toggle_rule(self, aid: int, active: bool) -> None:
        conn = get_conn()
        try:
            conn.execute("UPDATE alerts SET active=? WHERE id=?", (1 if active else 0, aid))
            conn.commit()
        finally:
            conn.close()

    def delete_rule(self, aid: int) -> None:
        conn = get_conn()
        try:
            conn.execute("DELETE FROM alerts WHERE id=?", (aid,))
            conn.commit()
        finally:
            conn.close()

    def list_events(self, limit: int = 50) -> list[dict]:
        conn = get_conn()
        try:
            return [dict(r) for r in conn.execute(
                "SELECT ae.*, a.symbol, a.rule_type FROM alert_events ae JOIN alerts a ON ae.alert_id=a.id ORDER BY ae.triggered_at DESC LIMIT ?", (limit,)
            ).fetchall()]
        finally:
            conn.close()

    def record_event(self, alert_id: int, message: str) -> None:
        conn = get_conn()
        try:
            conn.execute("INSERT INTO alert_events (alert_id, triggered_at, message) VALUES (?, ?, ?)",
                         (alert_id, datetime.now().isoformat(), message))
            conn.commit()
        finally:
            conn.close()
