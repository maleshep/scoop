"""Configuration: tickers, model, paths. US + EU markets only."""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")


def _claude_settings_env() -> dict:
    """Read the user-level Claude Code settings.json env block.

    The auth token + proxy base URL live there (ANTHROPIC_AUTH_TOKEN /
    ANTHROPIC_BASE_URL), but they don't reliably inherit into subprocesses
    spawned from the agent. Reading the file directly is robust.
    """
    path = Path.home() / ".claude" / "settings.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("env", {}) or {}
    except Exception:
        return {}


_CLAUDE_ENV = _claude_settings_env()

def _pick(env_key: str, default: str = "") -> str:
    """Prefer the settings.json value when present (subprocess env is unreliable
    for the corp auth token, and may carry a local-relay URL instead)."""
    return _CLAUDE_ENV.get(env_key) or os.environ.get(env_key) or default


ANTHROPIC_API_KEY = _pick("ANTHROPIC_API_KEY")
ANTHROPIC_AUTH_TOKEN = _pick("ANTHROPIC_AUTH_TOKEN")
ANTHROPIC_BASE_URL = _pick("ANTHROPIC_BASE_URL")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")

MODEL = _pick("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# Analyzer model provider. "glm" uses the direct HPC OpenAI-compatible endpoint
# (localhost:8103); "claude" uses the Merck palantir Bearer-proxy. GLM is the
# default — cheaper, 1M context, and the anti-reward-hacking module suits the
# neutral-signal discipline. Claude is the CI fallback when HPC isn't tunnelled.
MODEL_PROVIDER = os.environ.get("MODEL_PROVIDER", "glm").lower()

# GLM via HPC SSH tunnel (see Zed settings: "HPC GLM")
GLM_BASE_URL = os.environ.get("GLM_BASE_URL", "http://localhost:8103/v1")
GLM_MODEL = os.environ.get("GLM_MODEL", "glm-5.2")
GLM_API_KEY = os.environ.get("GLM_API_KEY", "sk-dummy")
OUTPUT_DIR = ROOT / "output"
HISTORY_PERIOD = "3mo"  # OHLCV lookback for technicals

# Two regional groups. Keep the PoC small — 5 US large-caps + 5 EU large-caps,
# plus each region's benchmark index. Tickers use yfinance suffix conventions:
# US: plain symbol; EU: exchange suffix (.DE Xetra, .L LSE, .PA Paris, .AS Aebit).
WATCHLIST = {
    "US": {
        "index": "^GSPC",  # S&P 500
        "tickers": ["AAPL", "MSFT", "NVDA", "JPM", "XOM"],
    },
    "EU": {
        "index": "^STOXX",  # STOXX Europe 600 (broad EU benchmark; ^STOXX50E = Euro Stoxx 50)
        "tickers": ["SAP.DE", "SHEL.L", "ASML.AS", "AIR.PA", "SIE.DE"],
    },
}

# Email notify only fires if all SMTP vars are present.
SMTP = {
    "host": os.environ.get("SMTP_HOST", ""),
    "port": int(os.environ.get("SMTP_PORT", "587")),
    "user": os.environ.get("SMTP_USER", ""),
    "pass": os.environ.get("SMTP_PASS", ""),
    "to": os.environ.get("EMAIL_TO", ""),
}


def email_enabled() -> bool:
    return all([SMTP["host"], SMTP["user"], SMTP["pass"], SMTP["to"]])
