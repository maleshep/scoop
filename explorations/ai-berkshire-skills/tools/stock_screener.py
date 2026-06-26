#!/usr/bin/env python3
"""stock_screener.py — momentum discovery + value validation screen.

Two layers:
  Layer 1 (momentum discovery): 60-day new high + volume confirmation -> candidate
  Layer 2 (value validation):    6-dimension score >= 3/6 -> buy signal
  Signal grading: 3/6 = probe 3% | 4/6 = standard 5% | 5-6/6 = conviction 8%

Improvements from the NVDA/AMD/MU backtest:
  1. Gross margin improving 2 consecutive quarters -> independent buy condition
  2. EPS beat > 30% -> independent condition for cyclicals (catches bottoms)
  3. Signal grading replaces the binary judgment

US + EU only. yfinance suffix conventions: US plain; EU .DE/.L/.PA/.AS.

Usage:
  python tools/stock_screener.py                   # scan the full watchlist
  python tools/stock_screener.py NVDA ASML.AS      # scan specific tickers
  python tools/stock_screener.py --update AAPL      # update AAPL fundamentals

The corporate proxy uses a self-signed CA that breaks curl_cffi TLS, so we
monkeypatch verify=False (same workaround as daily-stock-analysis).
"""
import json
import os
import sys
from datetime import datetime, timedelta
from collections import OrderedDict

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

# ============================================================
# Config
# ============================================================

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
FUND_FILE = os.path.join(DATA_DIR, "fundamentals.json")
WATCHLIST_FILE = os.path.join(DATA_DIR, "watchlist.json")

DEFAULT_WATCHLIST = {
    "us_ai_chip": ["NVDA", "AMD", "AVGO", "MRVL", "TSM", "QCOM"],
    "us_ai_app": ["GOOG", "META", "MSFT", "AMZN", "CRM", "NOW", "PLTR"],
    "us_ai_infra": ["ETN", "PWR", "VRT"],
    "us_financials": ["JPM", "BRK-B", "V"],
    "eu_semis": ["ASML.AS", "SAP.DE", "SIE.DE", "IFX.DE"],
    "eu_energy": ["SHEL.L", "TOT.PA"],
    "eu_industrial": ["AIR.PA"],
}


# ============================================================
# Price data (yfinance)
# ============================================================

def fetch_prices(ticker, days=120):
    """Daily OHLCV via yfinance. Returns list of {date, close, high, volume}."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=f"{days}d", auto_adjust=False)
        if hist.empty:
            return None
        rows = []
        for ts, row in hist.iterrows():
            rows.append({
                "date": ts.strftime("%Y-%m-%d"),
                "close": float(row["Close"]),
                "high": float(row["High"]),
                "volume": float(row["Volume"]),
            })
        return rows if len(rows) > 60 else None
    except Exception:
        return None


# ============================================================
# Fundamentals management
# ============================================================

def load_fundamentals():
    if os.path.exists(FUND_FILE):
        with open(FUND_FILE) as f:
            return json.load(f)
    return {}


def save_fundamentals(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(FUND_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def update_fundamental_interactive(ticker):
    funds = load_fundamentals()
    if ticker not in funds:
        funds[ticker] = {"quarters": {}}
    print(f"\n  Update {ticker} fundamentals")
    print(f"  Existing quarters: {', '.join(funds[ticker]['quarters'].keys()) or 'none'}")
    date = input("  Release date (YYYY-MM-DD): ").strip()
    label = input("  Label (e.g. Q1 2026): ").strip()
    rev_yoy = float(input("  Revenue YoY growth (%): "))
    gm = float(input("  Gross margin (%): "))
    eps_beat = float(input("  EPS beat (%): "))

    funds[ticker]["quarters"][date] = {
        "label": label, "rev_yoy": rev_yoy, "gm": gm, "eps_beat": eps_beat
    }
    save_fundamentals(funds)
    print(f"  Saved {ticker} {label}")


# ============================================================
# Layer 1: momentum discovery
# ============================================================

def check_momentum(prices):
    if len(prices) < 61:
        return None

    latest = prices[-1]
    close = latest["close"]

    past_60_highs = [p["high"] for p in prices[-61:-1]]
    is_60d_high = close > max(past_60_highs)

    vol_5 = sum(p["volume"] for p in prices[-5:]) / 5
    vol_20 = sum(p["volume"] for p in prices[-20:]) / 20
    vol_ratio = vol_5 / vol_20 if vol_20 > 0 else 0
    is_volume = vol_ratio > 1.5

    close_30d = prices[-31]["close"] if len(prices) > 30 else prices[0]["close"]
    pct_30d = (close - close_30d) / close_30d * 100

    recent_breakout = False
    for i in range(-5, 0):
        if prices[i]["close"] > max(p["high"] for p in prices[i - 60:i]):
            recent_breakout = True
            break

    triggered = (is_60d_high or recent_breakout) and is_volume

    return {
        "triggered": triggered,
        "close": round(close, 2),
        "date": latest["date"],
        "is_60d_high": is_60d_high,
        "vol_ratio": round(vol_ratio, 2),
        "pct_30d": round(pct_30d, 1),
    }


# ============================================================
# Layer 2: value validation (6-dim)
# ============================================================

def check_value(ticker, signal_date=None):
    funds = load_fundamentals()
    if ticker not in funds or not funds[ticker].get("quarters"):
        return None

    quarters = funds[ticker]["quarters"]
    sorted_q = sorted(quarters.items(), key=lambda x: x[0])

    if signal_date:
        valid = [(d, q) for d, q in sorted_q if d <= signal_date]
    else:
        valid = sorted_q

    if not valid:
        return None

    latest = valid[-1]
    prev = valid[-2] if len(valid) >= 2 else None
    prev2 = valid[-3] if len(valid) >= 3 else None

    d = latest[1]
    pd = prev[1] if prev else None
    pd2 = prev2[1] if prev2 else None

    checks = {}

    # 1. revenue acceleration
    checks["rev_accel"] = d["rev_yoy"] > pd["rev_yoy"] if pd else d["rev_yoy"] > 20
    # 2. gross margin direction
    checks["gm_expand"] = (d["gm"] > pd["gm"] or d["gm"] > 55) if pd else d["gm"] > 45
    # 3. EPS beat > 10%
    checks["eps_beat"] = d["eps_beat"] > 10
    # 4. high revenue growth > 15%
    checks["rev_high"] = d["rev_yoy"] > 15
    # 5. healthy gross margin > 40%
    checks["gm_healthy"] = d["gm"] > 40
    # 6. gross margin improving 2 consecutive quarters
    if pd and pd2:
        checks["gm_2q_improve"] = d["gm"] > pd["gm"] > pd2["gm"]
    elif pd:
        checks["gm_2q_improve"] = d["gm"] > pd["gm"]
    else:
        checks["gm_2q_improve"] = False

    score = sum(1 for v in checks.values() if v)

    independent_pass = False
    independent_reason = ""
    if checks.get("gm_2q_improve") and d["gm"] > 45:
        independent_pass = True
        independent_reason = "gross margin improving 2Q + >45%"
    if d["eps_beat"] > 30:
        independent_pass = True
        independent_reason = "EPS beat >30% (cyclical bottom signal)"

    return {
        "score": score, "max": 6, "checks": checks, "fund": d,
        "fund_date": latest[0], "fund_label": d.get("label", ""),
        "independent_pass": independent_pass, "independent_reason": independent_reason,
    }


# ============================================================
# Signal grading
# ============================================================

def grade_signal(momentum, value):
    if not momentum or not momentum["triggered"]:
        return "SKIP", "no momentum signal", ""
    if not value:
        return "WATCH", "momentum triggered, no fundamentals", "add fundamentals"
    score = value["score"]
    ind = value["independent_pass"]
    if score >= 5 or (score >= 4 and ind):
        return "BUY_8%", f"conviction ({score}/6)", "8% position"
    if score >= 4 or (score >= 3 and ind):
        return "BUY_5%", f"standard ({score}/6)", "5% position"
    if score >= 3:
        return "BUY_3%", f"probe ({score}/6)", "3% position"
    if ind:
        return "BUY_3%", f"independent pass: {value['independent_reason']}", "3% position"
    return "PASS", f"momentum but weak fundamentals ({score}/6)", "keep watching"


def scan_ticker(ticker, verbose=True):
    prices = fetch_prices(ticker)
    if not prices:
        if verbose:
            print(f"  {ticker:<10} no price data")
        return None

    momentum = check_momentum(prices)
    value = check_value(ticker)
    grade, reason, advice = grade_signal(momentum, value)

    result = {"ticker": ticker, "grade": grade, "reason": reason, "advice": advice,
              "momentum": momentum, "value": value}

    if verbose:
        m = momentum
        sym = {"BUY_8%": "!", "BUY_5%": "*", "BUY_3%": ".", "WATCH": "?", "PASS": " ", "SKIP": " "}
        s = sym.get(grade, " ")
        if grade.startswith("BUY"):
            print(f"  {s} {ticker:<10} ${m['close']:<9} 30d {m['pct_30d']:+}% vol {m['vol_ratio']}x  -> {grade} {reason}")
            if value:
                v = value
                print(f"      fund ({v['fund_label']}): rev {v['fund']['rev_yoy']}% gm {v['fund']['gm']}% eps_beat {v['fund']['eps_beat']}%")
                if v["independent_pass"]:
                    print(f"      * independent pass: {v['independent_reason']}")
        elif grade == "WATCH":
            print(f"  {s} {ticker:<10} ${m['close']:<9} 30d {m['pct_30d']:+}%  -> momentum triggered, add fundamentals")
        elif grade == "PASS":
            print(f"  {s} {ticker:<10} ${m['close']:<9}  -> {reason}")
    return result


def main():
    args = sys.argv[1:]

    if args and args[0] == "--update":
        ticker = args[1].upper() if len(args) > 1 else input("  Ticker: ").strip().upper()
        update_fundamental_interactive(ticker)
        return

    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "w") as f:
            json.dump(DEFAULT_WATCHLIST, f, indent=2)
        print(f"  Created default watchlist: {WATCHLIST_FILE}")

    if args:
        tickers = [t.upper() for t in args]
    else:
        with open(WATCHLIST_FILE) as f:
            wl = json.load(f)
        tickers = [s for syms in wl.values() for s in syms]

    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n{'='*70}")
    print(f"  Momentum + value screen  {today}")
    print(f"  Scanning {len(tickers)} tickers")
    print(f"{'='*70}\n")

    buy_signals, watch_signals = [], []
    for ticker in tickers:
        result = scan_ticker(ticker)
        if result:
            if result["grade"].startswith("BUY"):
                buy_signals.append(result)
            elif result["grade"] == "WATCH":
                watch_signals.append(result)

    print(f"\n{'='*70}")
    print(f"  Summary")
    print(f"{'='*70}")
    if buy_signals:
        print(f"\n  BUY signals: {len(buy_signals)}")
        for s in sorted(buy_signals, key=lambda x: x["grade"], reverse=True):
            m = s["momentum"]
            print(f"     {s['grade']:<8} {s['ticker']:<10} ${m['close']:<9} {s['reason']}")
    else:
        print("\n  no buy signals")
    if watch_signals:
        print(f"\n  Watch (add fundamentals): {len(watch_signals)}")
        for s in watch_signals:
            m = s["momentum"]
            print(f"     {s['ticker']:<10} ${m['close']:<9} 30d {m['pct_30d']:+}% -- run --update {s['ticker']}")
    print(f"\n  Fundamentals: {FUND_FILE}")
    print(f"  Watchlist:    {WATCHLIST_FILE}\n")


if __name__ == "__main__":
    main()
