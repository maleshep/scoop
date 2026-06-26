"""Agent tools — each wraps an engine function for the LLM tool-calling loop.

Tools are plain Python callables registered in a ToolRegistry. The agent
service describes them to the LLM and dispatches calls by name.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # explorations/

import data_fetcher
import news_fetcher

_EU_SUFFIXES = (".DE", ".L", ".PA", ".AS", ".MI", ".MC", ".SW")


def _region(symbol: str) -> str:
    return "EU" if symbol.upper().endswith(_EU_SUFFIXES) else "US"


def _strip_history(d: dict) -> dict:
    d.pop("history", None)
    return d


def get_quote(symbol: str) -> dict:
    """Realtime price + daily/weekly/monthly % change + currency."""
    tk = _strip_history(data_fetcher._ticker_snapshot(symbol))
    return {
        "symbol": tk.get("symbol"), "price": tk.get("price"), "currency": tk.get("currency"),
        "change_1d_pct": tk.get("change_1d_pct"), "change_1w_pct": tk.get("change_1w_pct"),
        "change_1m_pct": tk.get("change_1m_pct"), "name": tk.get("name"),
    }


def get_technicals(symbol: str) -> dict:
    """RSI, MACD, volume, volatility, beta."""
    tk = _strip_history(data_fetcher._ticker_snapshot(symbol))
    return {
        "symbol": tk.get("symbol"), "rsi_14": tk.get("rsi_14"), "macd": tk.get("macd"),
        "avg_volume_20d": tk.get("avg_volume_20d"), "volatility_20d": tk.get("volatility_20d"),
        "beta": tk.get("beta"), "beta_vs_index": tk.get("beta_vs_index"),
    }


def get_fundamentals(symbol: str) -> dict:
    """P/E, forward P/E, P/B, ROE, debt/equity, margins, analyst target, earnings date."""
    tk = _strip_history(data_fetcher._ticker_snapshot(symbol))
    return {
        "symbol": tk.get("symbol"), "pe_ratio": tk.get("pe_ratio"), "forward_pe": tk.get("forward_pe"),
        "price_to_book": tk.get("price_to_book"), "roe": tk.get("roe"),
        "debt_to_equity": tk.get("debt_to_equity"), "profit_margin": tk.get("profit_margin"),
        "revenue_growth": tk.get("revenue_growth"), "market_cap": tk.get("market_cap"),
        "dividend_yield": tk.get("dividend_yield"), "analyst_target_mean": tk.get("analyst_target_mean"),
        "recommendation": tk.get("recommendation"), "next_earnings_date": tk.get("next_earnings_date"),
        "sector": tk.get("sector"), "industry": tk.get("industry"),
    }


def get_news(symbol: str) -> list[dict]:
    """Recent news headlines with source tags."""
    items = news_fetcher.fetch_news(symbol)
    return [{"title": n.get("title", ""), "url": n.get("url", ""), "sources": n.get("sources", [])} for n in items]


def get_index(region: str) -> dict:
    """Regional benchmark index snapshot."""
    region = region.upper()
    if region not in ("US", "EU"):
        return {"error": f"unknown region {region}; use US or EU"}
    rd = data_fetcher.fetch_region(region)
    idx = rd["index"]
    return {"symbol": idx.get("symbol"), "price": idx.get("price"),
            "change_1d_pct": idx.get("change_1d_pct"), "region": region}


def compare_peers(symbol: str) -> dict:
    """The ticker's move vs its regional peers + the index."""
    region = _region(symbol)
    rd = data_fetcher.fetch_region(region)
    peers = []
    for tk in rd["tickers"]:
        _strip_history(tk)
        peers.append({"symbol": tk.get("symbol"), "change_1d_pct": tk.get("change_1d_pct"),
                      "change_1d_vs_index": tk.get("change_1d_vs_index"),
                      "change_1d_pct_rank": tk.get("change_1d_pct_rank")})
    return {"symbol": symbol, "region": region, "index_change_1d_pct": rd["index"].get("change_1d_pct"), "peers": peers}


# Registry: name -> (callable, description, params)
TOOL_REGISTRY: dict[str, dict] = {
    "get_quote": {"fn": get_quote, "desc": "Get the current price and 1d/1w/1m % change for a ticker.", "params": {"symbol": {"type": "string", "description": "Ticker, e.g. AAPL or SAP.DE"}}},
    "get_technicals": {"fn": get_technicals, "desc": "Get RSI, MACD, volume, volatility, beta for a ticker.", "params": {"symbol": {"type": "string", "description": "Ticker"}}},
    "get_fundamentals": {"fn": get_fundamentals, "desc": "Get P/E, forward P/E, P/B, ROE, debt/equity, margins, analyst target, next earnings date.", "params": {"symbol": {"type": "string", "description": "Ticker"}}},
    "get_news": {"fn": get_news, "desc": "Get recent news headlines for a ticker with source tags.", "params": {"symbol": {"type": "string", "description": "Ticker"}}},
    "get_index": {"fn": get_index, "desc": "Get the regional benchmark index (US or EU) snapshot.", "params": {"region": {"type": "string", "description": "US or EU"}}},
    "compare_peers": {"fn": compare_peers, "desc": "Compare a ticker's daily move against its regional peers and the index.", "params": {"symbol": {"type": "string", "description": "Ticker"}}},
}


def call_tool(name: str, **kwargs) -> str:
    """Execute a tool by name; returns a JSON string result or an error string."""
    entry = TOOL_REGISTRY.get(name)
    if not entry:
        return json.dumps({"error": f"unknown tool: {name}"})
    try:
        result = entry["fn"](**kwargs)
        return json.dumps(result, default=str)
    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {e}"})


def tool_schemas() -> list[dict]:
    """OpenAI-style tool schemas for the LLM."""
    return [
        {"type": "function", "function": {
            "name": name,
            "description": t["desc"],
            "parameters": {"type": "object", "properties": t["params"], "required": list(t["params"].keys())},
        }}
        for name, t in TOOL_REGISTRY.items()
    ]
