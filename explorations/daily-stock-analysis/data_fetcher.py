"""Fetch OHLCV + basic fundamentals via yfinance for US and EU tickers.

The corporate proxy uses a self-signed CA that breaks yfinance's curl_cffi
TLS verification. We monkeypatch curl_cffi to skip cert verification, the
same workaround documented in the scoop PIPELINE.md for lnkd.in resolution.
"""
import warnings

warnings.filterwarnings("ignore")

import curl_cffi.requests as _crequests  # noqa: E402
from curl_cffi.requests import Session as _CurlSession  # noqa: E402

_orig_request = _CurlSession.request


def _no_verify(self, *args, **kwargs):
    kwargs["verify"] = False
    return _orig_request(self, *args, **kwargs)


_CurlSession.request = _no_verify

import yfinance as yf  # noqa: E402

import config  # noqa: E402


def _ticker_snapshot(symbol: str) -> dict:
    t = yf.Ticker(symbol)
    hist = t.history(period=config.HISTORY_PERIOD, auto_adjust=False)
    if hist.empty:
        return {"symbol": symbol, "error": "no data"}

    close = hist["Close"]
    last = float(close.iloc[-1])
    # Technicals from the lookback window
    def _pct(days: int) -> float | None:
        if len(close) <= days:
            return None
        prev = float(close.iloc[-1 - days])
        return round((last - prev) / prev * 100, 2) if prev else None

    info = {}
    try:
        raw = t.get_info() or {}
        info = {
            "name": raw.get("longName") or raw.get("shortName") or symbol,
            "currency": raw.get("currency", ""),
            "pe_ratio": raw.get("trailingPE"),
            "market_cap": raw.get("marketCap"),
            "dividend_yield": raw.get("dividendYield"),
        }
    except Exception:
        pass

    return {
        "symbol": symbol,
        "name": info.get("name", symbol),
        "currency": info.get("currency", ""),
        "price": round(last, 2),
        "change_1d_pct": _pct(1),
        "change_1w_pct": _pct(5),
        "change_1m_pct": _pct(21),
        "pe_ratio": info.get("pe_ratio"),
        "market_cap": info.get("market_cap"),
        "dividend_yield": info.get("dividend_yield"),
        "history": hist,
    }


def fetch_region(region: str) -> dict:
    """Fetch a region's index + all watchlist tickers."""
    spec = config.WATCHLIST[region]
    out = {"region": region, "index": {}, "tickers": []}
    out["index"] = {k: v for k, v in _ticker_snapshot(spec["index"]).items() if k != "history"}
    out["index"]["history"] = _ticker_snapshot(spec["index"])["history"]
    for sym in spec["tickers"]:
        out["tickers"].append(_ticker_snapshot(sym))
    return out


def fetch_all() -> dict[str, dict]:
    return {region: fetch_region(region) for region in config.WATCHLIST}


if __name__ == "__main__":
    import json

    data = fetch_all()
    # Strip the heavy history for a quick console summary
    for region, d in data.items():
        idx = d["index"]
        print(f"\n=== {region} index {idx['symbol']} @ {idx['price']} (1d {idx['change_1d_pct']}%) ===")
        for tk in d["tickers"]:
            if "error" in tk:
                print(f"  {tk['symbol']:10} ERROR {tk['error']}")
            else:
                print(f"  {tk['symbol']:10} {tk['price']:>10} (1d {tk['change_1d_pct']}%)  {tk['name']}")
