"""Daily US/EU stock analysis — entrypoint.

Pipeline: fetch OHLCV + fundamentals -> fetch news -> LLM analysis -> markdown report.

Run:  python main.py
"""
import sys
import traceback
from datetime import datetime

import analyzer
import config
import data_fetcher
import news_fetcher
import notifier
import report


def run() -> str:
    print("Fetching market data (yfinance, US + EU)...")
    data = data_fetcher.fetch_all()

    analysis = {}
    for region, rd in data.items():
        idx = {k: v for k, v in rd["index"].items() if k != "history"}
        analysis[region] = {"index": idx, "tickers": []}
        for tk in rd["tickers"]:
            if "error" in tk:
                print(f"  [skip] {tk['symbol']}: {tk['error']}")
                continue
            print(f"  [{region}] {tk['symbol']} — fetching news + analysis...")
            news = news_fetcher.fetch_news(tk["symbol"])
            result = analyzer.analyze_ticker(tk, news, region, idx)
            analysis[region]["tickers"].append(result)

    md = report.render(analysis)
    path = report.save(md)
    print(f"\nReport written: {path}")
    notifier.notify(f"Daily Market Brief — {datetime.now():%Y-%m-%d}", md)
    return md


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
