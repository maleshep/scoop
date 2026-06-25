"""Fetch recent news per ticker.

Primary: yfinance's built-in news feed (free, no key, US+EU coverage).
Optional: Tavily search for richer financial-news context (set TAVILY_API_KEY).
"""
import config
import data_fetcher  # noqa: F401  (ensures the curl_cffi SSL patch is applied)


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
        pub = content.get("pubDate") or it.get("providerPublishTime") or ""
        summary = content.get("summary", "") or ""
        out.append({"title": title, "published": str(pub), "summary": summary[:300]})
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
        return [
            {"title": r.get("title", ""), "published": "", "summary": r.get("content", "")[:300]}
            for r in res.get("results", [])
        ]
    except Exception:
        return []


def fetch_news(symbol: str) -> list[dict]:
    # Prefer Tavily when configured (better financial-news corpus), fall back to yfinance.
    if config.TAVILY_API_KEY:
        news = _tavily_news(symbol)
        if news:
            return news
    return _yfinance_news(symbol)


if __name__ == "__main__":
    for sym in ["AAPL", "SAP.DE"]:
        print(f"\n=== {sym} ===")
        for n in fetch_news(sym)[:3]:
            print(f"  - {n['title'][:90]}  ({n['published'][:16]})")
