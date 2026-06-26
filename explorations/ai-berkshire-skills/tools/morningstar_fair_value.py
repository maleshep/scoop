#!/usr/bin/env python3
"""morningstar_fair_value.py — fetch all Morningstar stocks with a fair-value
estimate, compute the upside %, output the Top 100 (US + EU universes).

Uses curl_cffi with verify=False to survive the corporate self-signed proxy.
"""

import csv
import json
import os
import time
from datetime import datetime

import warnings
warnings.filterwarnings("ignore")

import curl_cffi.requests as _crequests
from curl_cffi.requests import Session as _CurlSession

_orig = _CurlSession.request


def _no_verify(self, *a, **k):
    k["verify"] = False
    return _orig(self, *a, **k)


_CurlSession.request = _no_verify

# US (NASDAQ + NYSE) and EU (Xetra + Euronext + LSE) universes
API_BASE = (
    "https://lt.morningstar.com/api/rest.svc/klr5zyak8x/security/screener"
    "?page={page}&pageSize={page_size}"
    "&sortOrder=FairValueEstimate%20desc"
    "&outputType=json&version=1"
    "&languageId=en-US&currencyId=USD"
    "&universeIds=E0EXG%24XNAS%7CE0EXG%24XNYS%7CE0EXG%24XETR%7CE0EXG%24XPAR%7CE0EXG%24XAMS%7CE0EXG%24XLON"
    "&securityDataPoints=SecId%7CName%7CPriceCurrency%7CTenforeId%7CClosePrice"
    "%7CStarRatingM255%7CQuantitativeFairValue%7CFairValueEstimate"
    "%7CAssessmentOfFairValueUncertainty%7CEconomicMoat%7CIndustryName%7CSectorName"
    "&filters=FairValueEstimate:notnull"
)

PAGE_SIZE = 100
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def fetch_page(page: int) -> dict:
    url = API_BASE.format(page=page, page_size=PAGE_SIZE)
    resp = _crequests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    return json.loads(resp.text)


def extract_ticker(tenforeid: str) -> str:
    if not tenforeid:
        return ""
    parts = tenforeid.split(".")
    return parts[-1] if len(parts) >= 3 else tenforeid


def main():
    print(f"\n{'='*80}")
    print(f"  Morningstar fair-value screen  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*80}\n")

    print("  Fetching page 1...")
    data = fetch_page(1)
    total = data.get("total", 0)
    all_rows = data.get("rows", [])
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    print(f"  {total} stocks, {total_pages} pages\n")

    for page in range(2, total_pages + 1):
        if page % 10 == 0 or page == total_pages:
            print(f"  Fetching page {page}/{total_pages}...")
        try:
            data = fetch_page(page)
            rows = data.get("rows", [])
            if not rows:
                break
            all_rows.extend(rows)
            time.sleep(0.3)
        except Exception as e:
            print(f"  page {page} failed: {e}")
            time.sleep(1)

    print(f"\n  {len(all_rows)} records fetched")

    stocks = []
    for row in all_rows:
        fair_value = row.get("FairValueEstimate")
        close_price = row.get("ClosePrice")
        if not fair_value or not close_price or close_price <= 0:
            continue
        ticker = extract_ticker(row.get("TenforeId", ""))
        upside = (fair_value - close_price) / close_price * 100
        stocks.append({
            "ticker": ticker, "name": row.get("Name", ""),
            "close_price": round(close_price, 2), "fair_value": round(fair_value, 2),
            "upside_pct": round(upside, 1), "star_rating": row.get("StarRatingM255", ""),
            "moat": row.get("EconomicMoat", ""),
            "uncertainty": row.get("AssessmentOfFairValueUncertainty", ""),
            "sector": row.get("SectorName", ""), "industry": row.get("IndustryName", ""),
        })

    stocks.sort(key=lambda x: x["upside_pct"], reverse=True)

    print(f"\n{'='*80}")
    print(f"  Top 100 by upside")
    print(f"{'='*80}\n")
    print(f"  {'#':>4} {'ticker':<10} {'name':<35} {'price':>10} {'fair':>10} {'upside':>8} {'star':>5} {'moat':<8} {'industry':<20}")
    print(f"  {'-'*4} {'-'*10} {'-'*35} {'-'*10} {'-'*10} {'-'*8} {'-'*5} {'-'*8} {'-'*20}")

    for i, s in enumerate(stocks[:100], 1):
        stars = "*" * int(s["star_rating"]) if s["star_rating"] else "N/A"
        print(
            f"  {i:>4} {s['ticker']:<10} {s['name'][:35]:<35} "
            f"${s['close_price']:>9,.2f} ${s['fair_value']:>9,.2f} "
            f"{s['upside_pct']:>+7.1f}% {stars:>5} {s['moat']:<8} {s['industry'][:20]:<20}"
        )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    csv_path = os.path.join(OUTPUT_DIR, f"morningstar_fair_value_{today}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "rank", "ticker", "name", "close_price", "fair_value",
            "upside_pct", "star_rating", "moat", "uncertainty", "sector", "industry"
        ])
        writer.writeheader()
        for i, s in enumerate(stocks, 1):
            writer.writerow({"rank": i, **s})

    print(f"\n  Full data: {csv_path}")
    print(f"  {len(stocks)} stocks (sorted by upside)\n")

    if stocks:
        undervalued = [s for s in stocks if s["upside_pct"] > 0]
        overvalued = [s for s in stocks if s["upside_pct"] < 0]
        print(f"  Summary:")
        print(f"     undervalued: {len(undervalued)} ({len(undervalued)/len(stocks)*100:.0f}%)")
        print(f"     overvalued:  {len(overvalued)} ({len(overvalued)/len(stocks)*100:.0f}%)")
        if undervalued:
            avg = sum(s["upside_pct"] for s in undervalued) / len(undervalued)
            print(f"     avg upside (undervalued): +{avg:.1f}%")
        wide = [s for s in stocks if s["moat"] == "Wide" and s["upside_pct"] > 0]
        print(f"     wide-moat + undervalued: {len(wide)}")


if __name__ == "__main__":
    main()
