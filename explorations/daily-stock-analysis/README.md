# daily-stock-analysis (PoC)

A daily market brief for **US and EU equities** — fetches price/technicals + news,
runs an LLM analysis, and emits a markdown dashboard. Inspired by
[ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis),
scoped to US (S&P 500 large-caps) and EU (Euro Stoxx 50 large-caps) only.

Part of the scoop sandbox — a PoC for the "stock" half of a stock + video-generator
vision. Pairs with the ai-berkshire skill set for deep fundamental dives on
anything flagged `research_deeper` here.

## Pipeline

```
yfinance (US + EU)  →  news (yfinance / Tavily)  →  Claude Sonnet  →  markdown brief
```

## Run

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in ANTHROPIC_API_KEY (or rely on ~/.claude/settings.json)
python main.py
```

Output: `output/brief-YYYY-MM-DD.md`

## Files

| File | Role |
|---|---|
| `config.py` | Watchlist (US + EU tickers + indices), model, paths, env loading |
| `data_fetcher.py` | yfinance OHLCV + fundamentals; patches curl_cffi SSL for the corp proxy |
| `news_fetcher.py` | Per-ticker news (yfinance built-in, optional Tavily) |
| `analyzer.py` | LLM prompt + Claude call → JSON dashboard per ticker |
| `report.py` | Markdown dashboard renderer |
| `notifier.py` | Email stub (off until SMTP configured) |
| `main.py` | Entrypoint — orchestrates the pipeline |

## Watchlist

- **US** — `^GSPC` index + AAPL, MSFT, NVDA, JPM, XOM
- **EU** — `^STOXX` index + SAP.DE, SHEL.L, ASML.AS, AIR.PA, SIE.DE

Edit `config.WATCHLIST` to change coverage. EU tickers use yfinance exchange
suffixes (`.DE` Xetra, `.L` LSE, `.PA` Paris, `.AS` Amsterdam).

## Corporate environment notes

Two workarounds this PoC depends on (Merck corp net):
1. **yfinance SSL** — the proxy uses a self-signed CA that breaks `curl_cffi`.
   `data_fetcher.py` monkeypatches `curl_cffi.requests.Session.request` to
   `verify=False` (same pattern as the scoop lnkd.in resolver).
2. **Anthropic auth** — the Merck "palantir" proxy uses a Bearer JWT
   (`ANTHROPIC_AUTH_TOKEN`), not the SDK's default `x-api-key`. `analyzer.py`
   passes the token as an `Authorization: Bearer` header. Credentials are read
   from `~/.claude/settings.json` because they don't inherit into subprocesses.

## Not investment advice

Signals are data-driven summaries of the day's price action + news, not
trading recommendations.
