"""Bridge: daily brief -> ai-berkshire deep dive.

Reads the latest daily-stock-analysis output (analysis-{date}.json +
gaps-daily-stocks-{date}.json), picks tickers flagged research_deeper,
loads their gaps, and invokes the news-pulse skill for each. Writes a
deep-dive report per ticker and a merged deep-dive index.

Usage:
    python runner.py                    # process today's brief
    python runner.py --date 2026-06-26  # process a specific date
    python runner.py --ticker AAPL      # force a single ticker
    python runner.py --dry-run          # show what would run, don't invoke
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # explorations/

from shared.gaps import GapsLog

ROOT = Path(__file__).resolve().parent
BRIEF_DIR = ROOT.parent / "daily-stock-analysis" / "output"
REPORT_DIR = ROOT / "reports"
OUTPUT_DIR = ROOT / "output"


def find_latest_brief(date: str | None = None) -> tuple[str, Path, Path]:
    """Return (date_str, analysis_json_path, gaps_json_path)."""
    if date:
        date_str = date
    else:
        analyses = sorted(BRIEF_DIR.glob("analysis-*.json"))
        if not analyses:
            raise SystemExit(f"No analysis-*.json found in {BRIEF_DIR}. Run daily-stock-analysis first.")
        date_str = analyses[-1].stem.replace("analysis-", "")
    analysis_path = BRIEF_DIR / f"analysis-{date_str}.json"
    gaps_path = BRIEF_DIR / f"gaps-daily-stocks-{date_str}.json"
    if not analysis_path.exists():
        raise SystemExit(f"Analysis file not found: {analysis_path}")
    return date_str, analysis_path, gaps_path


def extract_flagged_tickers(analysis_path: Path) -> list[dict]:
    """Return tickers whose action == research_deeper, with brief context."""
    data = json.loads(analysis_path.read_text(encoding="utf-8"))
    flagged = []
    for region, rd in data.items():
        for t in rd.get("tickers", []):
            if t.get("action") == "research_deeper":
                t["region"] = region
                flagged.append(t)
    return flagged


def load_gaps_for_ticker(gaps_path: Path, symbol: str) -> list[dict]:
    """Read the daily-stocks gaps JSON and filter to this ticker. Returns []
    if the gaps file is absent (clean run)."""
    if not gaps_path.exists():
        return []
    data = json.loads(gaps_path.read_text(encoding="utf-8"))
    return [e for e in data.get("entries", []) if e.get("subject") == symbol]


def build_skill_arguments(ticker: dict, gaps: list[dict]) -> str:
    """Assemble the $ARGUMENTS string news-pulse.md expects."""
    gap_lines = "\n".join(f"  - [{g['severity']}] {g['category']}: {g['note']}" for g in gaps) or "  (none)"
    drivers = "\n  ".join(ticker.get("drivers", [])) or "(none)"
    risks = "\n  ".join(ticker.get("risks", [])) or "(none)"
    return (
        f"TICKER: {ticker['symbol']}\n"
        f"NAME: {ticker.get('name', '')}\n"
        f"REGION: {ticker.get('region', '')}\n"
        f"SECTOR: {ticker.get('sector', '?')}\n"
        f"PRICE: {ticker.get('price')} {ticker.get('currency', '')} "
        f"(1d {ticker.get('change_1d_pct')}% | 1w {ticker.get('change_1w_pct')}% | 1m {ticker.get('change_1m_pct')}%)\n"
        f"RSI: {ticker.get('rsi_14')} | P/E: {ticker.get('pe_ratio')} | forward P/E: {ticker.get('forward_pe')}\n"
        f"BRIEF CONCLUSION: {ticker.get('core_conclusion', '')}\n"
        f"BRIEF DRIVERS:\n  {drivers}\n"
        f"BRIEF RISKS:\n  {risks}\n"
        f"KNOWN GAPS (from the fast scan — resolve these):\n{gap_lines}\n"
        f"WINDOW: 14 days"
    )


def run_news_pulse(arguments: str) -> str:
    """Invoke the news-pulse skill via the Claude Code CLI. Returns its output."""
    try:
        result = subprocess.run(
            ["claude", "-p", f"/news-pulse {arguments}"],
            capture_output=True, text=True, timeout=900, encoding="utf-8",
        )
        if result.returncode != 0:
            return f"[skill invocation failed: {result.stderr.strip()[:500]}]"
        return result.stdout
    except FileNotFoundError:
        return ("[claude CLI not found on PATH — invoke manually with:\n"
                f"  claude -p \"/news-pulse {arguments[:120]}...\"]")
    except subprocess.TimeoutExpired:
        return "[skill timed out after 900s]"


def save_deep_dive(symbol: str, markdown: str, date_str: str) -> Path:
    """Write reports/{symbol}/{symbol}-news-{date}.md and update the index."""
    ticker_dir = REPORT_DIR / symbol
    ticker_dir.mkdir(parents=True, exist_ok=True)
    path = ticker_dir / f"{symbol}-news-{date_str}.md"
    path.write_text(markdown, encoding="utf-8")

    index_path = REPORT_DIR / f"deep-dive-index-{date_str}.md"
    header = f"# Deep-Dive Index — {date_str}\n\n| Ticker | Report |\n|---|---|\n"
    row = f"| {symbol} | [{path.name}]({symbol}/{path.name}) |\n"
    if index_path.exists():
        lines = index_path.read_text(encoding="utf-8").splitlines()
        if not any(symbol in ln for ln in lines):
            lines.append(row)
        index_path.write_text("\n".join(lines), encoding="utf-8")
    else:
        index_path.write_text(header + row, encoding="utf-8")
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", help="Process a specific date's brief (YYYY-MM-DD)")
    ap.add_argument("--ticker", help="Force a single ticker symbol")
    ap.add_argument("--dry-run", action="store_true", help="Show flagged tickers, don't invoke the skill")
    args = ap.parse_args()

    date_str, analysis_path, gaps_path = find_latest_brief(args.date)
    flagged = extract_flagged_tickers(analysis_path)
    if args.ticker:
        flagged = [t for t in flagged if t["symbol"] == args.ticker] or [
            {"symbol": args.ticker, "name": args.ticker, "region": "?", "core_conclusion": "(forced)",
             "drivers": [], "risks": [], "change_1d_pct": None, "change_1w_pct": None,
             "change_1m_pct": None, "price": None, "currency": "", "sector": None,
             "rsi_14": None, "pe_ratio": None, "forward_pe": None}
        ]

    print(f"Brief: {analysis_path.name}")
    print(f"Gaps:  {gaps_path.name}{' (absent — clean run)' if not gaps_path.exists() else ''}")
    print(f"Flagged research_deeper: {len(flagged)} -> {[t['symbol'] for t in flagged]}")
    if not flagged:
        print("Nothing to deep-dive today.")
        return

    gaps_out = GapsLog(project="ai-berkshire", run_id=date_str, output_dir=OUTPUT_DIR)

    for t in flagged:
        symbol = t["symbol"]
        tk_gaps = load_gaps_for_ticker(gaps_path, symbol)
        arguments = build_skill_arguments(t, tk_gaps)
        print(f"\n=== {symbol} ===")
        print(arguments)
        if args.dry_run:
            print("[dry-run — skipping skill invocation]")
            continue
        print(f"[invoking /news-pulse ...]")
        report_md = run_news_pulse(arguments)
        path = save_deep_dive(symbol, report_md, date_str)
        print(f"[saved {path}]")
        if report_md.startswith("["):
            gaps_out.add(symbol, "skill", "blocker", f"news-pulse invocation did not produce output: {report_md[:120]}")

    gaps_out_path = gaps_out.save()
    if len(gaps_out):
        print(f"\nai-berkshire gaps: {gaps_out_path} ({len(gaps_out)})")
    print("\nDone.")


if __name__ == "__main__":
    main()
