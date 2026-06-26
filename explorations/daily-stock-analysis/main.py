"""Daily US/EU stock analysis — entrypoint.

Pipeline: fetch OHLCV + fundamentals -> fetch multi-source news -> LLM analysis
(GLM-5.2 by default, Claude fallback) -> markdown brief + gaps log.

Run:  python main.py
"""
import sys
import traceback
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # explorations/

import analyzer
import config
import data_fetcher
import news_fetcher
import notifier
import report
from shared.gaps import GapsLog


def run() -> str:
    run_id = datetime.now().strftime("%Y-%m-%d")
    gaps = GapsLog(project="daily-stocks", run_id=run_id, output_dir=config.OUTPUT_DIR)

    print(f"Fetching market data (yfinance, US + EU) | provider={config.MODEL_PROVIDER}...")
    data = data_fetcher.fetch_all()

    # Flag stale prices (market closed / weekend) as a gap per region.
    for region, rd in data.items():
        idx = rd["index"]
        if idx.get("change_1d_pct") is None:
            gaps.add(idx.get("symbol", region), "calendar", "blocker",
                     f"{region} index has no 1d change — market likely closed or holiday")

    analysis = {}
    for region, rd in data.items():
        idx = {k: v for k, v in rd["index"].items() if k != "history"}
        analysis[region] = {"index": idx, "tickers": []}
        for tk in rd["tickers"]:
            if "error" in tk:
                gaps.add(tk["symbol"], "price", "blocker", f"data fetch error: {tk['error']}")
                print(f"  [skip] {tk['symbol']}: {tk['error']}")
                continue
            print(f"  [{region}] {tk['symbol']} — news + analysis...")
            news = news_fetcher.fetch_news(tk["symbol"], gaps=gaps)
            result = analyzer.analyze_ticker(tk, news, region, idx, gaps=gaps)
            analysis[region]["tickers"].append(result)

    md = report.render(analysis)
    path = report.save(md)
    gaps_path = gaps.save()
    print(f"\nReport: {path}")
    print(f"Gaps:   {gaps_path}  ({len(gaps)} gaps)")
    notifier.notify(f"Daily Market Brief — {run_id}", md)
    return md


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
