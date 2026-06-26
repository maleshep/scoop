"""Multi-source news aggregation per ticker.

Sources (in priority order, all optional except yfinance):
  1. yfinance built-in  — free, no key, US+EU coverage
  2. Finnhub            — free tier (60 calls/min), company news + press releases
  3. Tavily             — financial-topic web search, broadest corpus

Items are deduped by normalized title and tagged with their source(s).
A GapsLog records thin/conflicting coverage so the analyzer knows what's weak.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # explorations/

import config
import data_fetcher  # noqa: F401  (applies the curl_cffi SSL patch)
from shared.gaps import GapsLog


def _norm(title: str) -> str:
    return "".join(c.lower() for c in title if c.isalnum())[:80]


def _yfinance_news(symbol: str, limit: int = 5) -> list[dict]:
    import yfinance as yf

    try:
        items = yf.Ticker(symbol).news or []
    except Exception:
        return []
    out = []
    for it in items[:limit]:
        content = it.get("content", {}) if isinstance(it, dict) else {}
        title = content.get("title") or it.get("title", "")
        if not title:
            continue
        out.append(
            {
                "title": title,
                "published": str(content.get("pubDate") or it.get("providerPublishTime") or ""),
                "summary": (content.get("summary") or "")[:280],
                "source": "yfinance",
            }
        )
    return out


def _finnhub_news(symbol: str, limit: int = 5) -> list[dict]:
    if not config.FINNHUB_API_KEY:
        return []
    try:
        import finnhub
    except ImportError:
        return []
    try:
        client = finnhub.Client(api_key=config.FINNHUB_API_KEY)
        # Finnhub wants the date range; use a wide recent window.
        from datetime import datetime, timedelta

        to_ = datetime.now()
        from_ = to_ - timedelta(days=7)
        items = client.company_news(
            symbol, _from=from_.strftime("%Y-%m-%d"), to=to_.strftime("%Y-%m-%d")
        )
    except Exception:
        return []
    out = []
    for it in (items or [])[:limit]:
        out.append(
            {
                "title": it.get("headline", ""),
                "published": str(it.get("datetime", "")),
                "summary": (it.get("summary") or "")[:280],
                "source": "finnhub",
            }
        )
    return out


def _tavily_news(symbol: str, limit: int = 5) -> list[dict]:
    if not config.TAVILY_API_KEY:
        return []
    try:
        from tavily import TavilyClient
    except ImportError:
        return []
    try:
        client = TavilyClient(api_key=config.TAVILY_API_KEY)
        res = client.search(
            query=f"{symbol} stock news today", max_results=limit, topic="finance"
        )
    except Exception:
        return []
    out = []
    for r in res.get("results", []):
        out.append(
            {
                "title": r.get("title", ""),
                "published": r.get("published_date", ""),
                "summary": (r.get("content") or "")[:280],
                "source": "tavily",
            }
        )
    return out


def fetch_news(symbol: str, gaps: GapsLog | None = None) -> list[dict]:
    """Aggregate news across all configured sources, dedupe by title."""
    raw = _yfinance_news(symbol) + _finnhub_news(symbol) + _tavily_news(symbol)

    # Dedupe — keep the first source seen for each normalized title, but record
    # if multiple sources carried the same story (a corroboration signal).
    by_norm: dict[str, dict] = {}
    corroborated = 0
    for item in raw:
        key = _norm(item["title"])
        if not key:
            continue
        if key in by_norm:
            by_norm[key]["sources"].add(item["source"])
            corroborated += 1
        else:
            by_norm[key] = {**item, "sources": {item["source"]}}

    items = list(by_norm.values())
    for it in items:
        it["sources"] = sorted(it["sources"])

    # Gap logging
    if gaps is not None:
        if not items:
            gaps.add(symbol, "news", "blocker", "no news from any source")
        elif len(items) == 1:
            gaps.add(symbol, "news", "weak", f"only {len(items)} news item — no cross-source corroboration")
        if items and corroborated == 0 and config.TAVILY_API_KEY and config.FINNHUB_API_KEY:
            gaps.add(symbol, "news", "weak", "multiple sources configured but no story corroborated across >1 source")
    return items


if __name__ == "__main__":
    from shared.gaps import GapsLog

    gaps = GapsLog(project="daily-stocks", run_id="news-smoke")
    for sym in ["AAPL", "SAP.DE"]:
        print(f"\n=== {sym} ===")
        items = fetch_news(sym, gaps=gaps)
        for n in items[:3]:
            print(f"  [{','.join(n['sources'])}] {n['title'][:80]}")
    print(f"\n--- gaps ({len(gaps)}) ---")
    for e in gaps.entries:
        print(f"  [{e['severity']}] {e['subject']} {e['category']}: {e['note']}")
