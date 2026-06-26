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


def _rsi(closes, period: int = 14) -> float | None:
    """Wilder's RSI on a close-price series."""
    if len(closes) <= period:
        return None
    deltas = closes.diff().dropna()
    gains = deltas.clip(lower=0)
    losses = -deltas.clip(upper=0)
    # Wilder smoothing == EMA with alpha = 1/period
    avg_gain = gains.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]
    avg_loss = losses.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - 100 / (1 + rs), 2)


def _macd(closes):
    """MACD(12,26,9): macd_line, signal_line, histogram."""
    if len(closes) < 35:
        return None
    ema12 = closes.ewm(span=12, adjust=False).mean()
    ema26 = closes.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    hist = macd_line - signal_line
    return {
        "macd_line": round(float(macd_line.iloc[-1]), 4),
        "signal_line": round(float(signal_line.iloc[-1]), 4),
        "histogram": round(float(hist.iloc[-1]), 4),
    }


def _safe(call, default=None):
    try:
        return call()
    except Exception:
        return default


def _ticker_snapshot(symbol: str) -> dict:
    t = yf.Ticker(symbol)
    hist = t.history(period=config.HISTORY_PERIOD, auto_adjust=False)
    if hist.empty:
        return {"symbol": symbol, "error": "no data"}

    close = hist["Close"]
    vol = hist.get("Volume")
    last = float(close.iloc[-1])

    def _pct(days: int) -> float | None:
        if len(close) <= days:
            return None
        prev = float(close.iloc[-1 - days])
        return round((last - prev) / prev * 100, 2) if prev else None

    # Technicals from the already-fetched history (no extra API call).
    technicals = {
        "rsi_14": _rsi(close),
        "macd": _macd(close),
        "avg_volume_20d": round(float(vol.tail(20).mean()), 0) if vol is not None and len(vol) >= 20 else None,
        "volatility_20d": round(
            float(close.pct_change().tail(20).std() * (252 ** 0.5) * 100), 2
        ) if len(close) >= 21 else None,
    }

    # Fundamentals + earnings/analyst from the single get_info() call and
    # a couple of cheap accessor calls on the same Ticker object.
    info = {}
    try:
        raw = t.get_info() or {}
        info = {
            "name": raw.get("longName") or raw.get("shortName") or symbol,
            "currency": raw.get("currency", ""),
            "pe_ratio": raw.get("trailingPE"),
            "forward_pe": raw.get("forwardPE"),
            "market_cap": raw.get("marketCap"),
            "dividend_yield": raw.get("dividendYield"),
            "price_to_book": raw.get("priceToBook"),
            "roe": raw.get("returnOnEquity"),
            "debt_to_equity": raw.get("debtToEquity"),
            "profit_margin": raw.get("profitMargins"),
            "revenue_growth": raw.get("revenueGrowth"),
            "eps_trailing": raw.get("trailingEps"),
            "sector": raw.get("sector"),
            "industry": raw.get("industry"),
            "beta": raw.get("beta"),
            "recommendation": raw.get("recommendationKey"),
        }
    except Exception:
        info = {"name": symbol}

    info["analyst_target_mean"] = _safe(lambda: t.analyst_price_targets.get("mean"))
    info["next_earnings_date"] = _safe(lambda: str(t.calendar.get("Earnings Date")[0]) if t.calendar else None)

    # Lightweight history series for the dashboard sparkline — keep the
    # heavy DataFrame out of the saved JSON.
    sparkline = [round(float(x), 2) for x in close.tail(65).tolist()]

    return {
        "symbol": symbol,
        "name": info.get("name", symbol),
        "currency": info.get("currency", ""),
        "price": round(last, 2),
        "change_1d_pct": _pct(1),
        "change_1w_pct": _pct(5),
        "change_1m_pct": _pct(21),
        "pe_ratio": info.get("pe_ratio"),
        "forward_pe": info.get("forward_pe"),
        "market_cap": info.get("market_cap"),
        "dividend_yield": info.get("dividend_yield"),
        "price_to_book": info.get("price_to_book"),
        "roe": info.get("roe"),
        "debt_to_equity": info.get("debt_to_equity"),
        "profit_margin": info.get("profit_margin"),
        "revenue_growth": info.get("revenue_growth"),
        "eps_trailing": info.get("eps_trailing"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "beta": info.get("beta"),
        "recommendation": info.get("recommendation"),
        "analyst_target_mean": info.get("analyst_target_mean"),
        "next_earnings_date": info.get("next_earnings_date"),
        "rsi_14": technicals["rsi_14"],
        "macd": technicals["macd"],
        "avg_volume_20d": technicals["avg_volume_20d"],
        "volatility_20d": technicals["volatility_20d"],
        "sparkline": sparkline,
        "history": hist,
    }


def fetch_region(region: str) -> dict:
    """Fetch a region's index + all watchlist tickers, then compute
    beta-vs-index and peer-relative move ranks in pure post-processing."""
    spec = config.WATCHLIST[region]
    out = {"region": region, "index": {}, "tickers": []}

    idx_snap = _ticker_snapshot(spec["index"])
    idx_hist = idx_snap["history"]
    out["index"] = {k: v for k, v in idx_snap.items() if k != "history"}

    for sym in spec["tickers"]:
        out["tickers"].append(_ticker_snapshot(sym))

    idx_close = idx_hist["Close"] if not idx_hist.empty else None
    idx_1d = out["index"].get("change_1d_pct")

    # Peer-relative ranks within this region's watchlist (0 = worst, 1 = best).
    moves = [tk.get("change_1d_pct") for tk in out["tickers"] if tk.get("change_1d_pct") is not None]
    n = len(moves)

    for tk in out["tickers"]:
        hist = tk.get("history")
        # Beta vs the regional index over the lookback window.
        if hist is not None and not hist.empty and idx_close is not None and len(hist) >= 30:
            tk_close = hist["Close"]
            joined = tk_close.pct_change().dropna().align(idx_close.pct_change().dropna(), join="inner")[0]
            idx_aligned = idx_close.pct_change().dropna().align(tk_close.pct_change().dropna(), join="inner")[1]
            var_idx = float(idx_aligned.var())
            if var_idx and var_idx > 0:
                beta = float(joined.cov(idx_aligned) / var_idx)
                tk["beta_vs_index"] = round(beta, 2)
        tk.pop("history", None)  # strip heavy DF before analysis/dash

        # Excess move vs index + percentile rank within the region.
        if tk.get("change_1d_pct") is not None and idx_1d is not None:
            tk["change_1d_vs_index"] = round(tk["change_1d_pct"] - idx_1d, 2)
        if tk.get("change_1d_pct") is not None and n > 1:
            rank = sum(1 for m in moves if m < tk["change_1d_pct"])
            tk["change_1d_pct_rank"] = round(rank / (n - 1), 2)

    return out


def fetch_all() -> dict[str, dict]:
    return {region: fetch_region(region) for region in config.WATCHLIST}


if __name__ == "__main__":
    import json

    data = fetch_all()
    for region, d in data.items():
        idx = d["index"]
        print(f"\n=== {region} index {idx['symbol']} @ {idx['price']} (1d {idx['change_1d_pct']}%) ===")
        for tk in d["tickers"]:
            if "error" in tk:
                print(f"  {tk['symbol']:10} ERROR {tk['error']}")
            else:
                print(
                    f"  {tk['symbol']:10} {tk['price']:>10} (1d {tk['change_1d_pct']}%) "
                    f"RSI {tk.get('rsi_14')} P/E {tk.get('pe_ratio')} sector {tk.get('sector')!r}"
                )
