"""SQLite connection helper (WAL mode for concurrent-safe local access)."""
import sqlite3
from pathlib import Path

import config

DB_PATH = config.OUTPUT_DIR / "dsa.db"


def get_conn() -> sqlite3.Connection:
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = get_conn()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS analysis_runs (
                run_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                region TEXT,
                signal TEXT,
                confidence TEXT,
                core_conclusion TEXT,
                action TEXT,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_runs_symbol ON analysis_runs(symbol);
            CREATE INDEX IF NOT EXISTS idx_runs_created ON analysis_runs(created_at DESC);
            CREATE TABLE IF NOT EXISTS usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                provider TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                symbol TEXT,
                created_at TEXT NOT NULL
            );
            """
        )
        conn.commit()
    finally:
        conn.close()
    # portfolio/alerts tables live in schema.py
    from api.db.schema import init_portfolio_db
    init_portfolio_db()


def log_usage(provider: str, endpoint: str, symbol: str | None = None) -> None:
    from datetime import datetime
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO usage_log (date, provider, endpoint, symbol, created_at) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d"), provider, endpoint, symbol, datetime.now().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
