#!/usr/bin/env python3
"""Report Audit Toolkit — data spot-check exit gate for investment research.

Called by the investment-research skill after a report is written: samples ~15%
of the figures cited in the report, requires each to be re-fetched from ≥1
reliable source, and compares fetched vs reported. Any item diverging >1%
fails the report (must be fixed and re-audited before publishing).

Zero external dependencies — Python stdlib only (argparse, json, re, random,
decimal). Matches the style of financial_rigor.py.

Usage (called automatically by the investment-research skill):
    python tools/report_audit.py extract --report reports/AAPL/AAPL-deep-research-2026-06-26.md
    # ... fill fetched_value / fetched_source / fetched_value2 / fetched_source2 ...
    python tools/report_audit.py verdict --results '<filled_json>' --report AAPL-deep-research-2026-06-26.md
"""

import argparse
import json
import random
import re
import sys
from decimal import Decimal, InvalidOperation

# Regex for a money/quantity figure cited in a report.
# Captures things like $123.4B, 1,239亿, 510.0, 33.35x, 13.5%, €998M.
_NUM = re.compile(
    r"(?P<prefix>[$€£¥]?\s*)"
    r"(?P<value>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"\s*(?P<unit>万亿|亿|万亿港元|万亿人民币|万亿[TB]|[TBMKtbmk]|x|%)?"
)


def _to_float(s: str):
    try:
        return float(str(s).replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def _scan_figures(text: str) -> list[dict]:
    """Extract candidate cited figures with a few words of surrounding context."""
    figures = []
    seen = set()
    for m in _NUM.finditer(text):
        val = _to_float(m.group("value"))
        if val is None or val == 0:
            continue
        ctx_start = max(0, m.start() - 40)
        context = text[ctx_start:m.end() + 10].replace("\n", " ").strip()
        key = (round(val, 4), m.group("unit") or "")
        if key in seen:
            continue
        seen.add(key)
        figures.append({
            "reported_value": val,
            "unit": m.group("unit") or "",
            "context": context,
        })
    return figures


def extract(report_path: str, sample_pct: float = 0.15) -> list[dict]:
    """Read a report .md, extract cited figures, sample ~15%, emit a template."""
    with open(report_path, encoding="utf-8") as f:
        text = f.read()
    figures = _scan_figures(text)
    if not figures:
        return []
    k = max(1, round(len(figures) * sample_pct))
    rng = random.Random(42)  # deterministic for reproducibility
    sample = rng.sample(figures, min(k, len(figures)))
    for item in sample:
        item["fetched_value"] = None
        item["fetched_source"] = ""
        item["fetched_value2"] = None
        item["fetched_source2"] = ""
    return sample


def verdict(results: list[dict], report_name: str = "") -> dict:
    """Compare fetched values against reported. ≤1% divergence = pass."""
    print("=" * 60)
    print(f"Report Audit Verdict — {report_name}")
    print("=" * 60)
    print(f"  Items audited: {len(results)}")
    print()

    all_pass = True
    rows = []
    for i, r in enumerate(results, 1):
        reported = _to_float(r.get("reported_value"))
        fetched = _to_float(r.get("fetched_value"))
        if reported is None or fetched is None:
            status = "❌ MISSING"
            dev = None
            all_pass = False
        else:
            try:
                dev = abs(Decimal(str(fetched)) - Decimal(str(reported))) / abs(Decimal(str(reported))) * 100
                dev = float(dev)
            except (InvalidOperation, ZeroDivisionError):
                dev = None
                status = "❌ ERROR"
            else:
                status = "✅" if dev <= 1.0 else ("⚠️" if dev <= 5.0 else "❌")
                if dev > 1.0:
                    all_pass = False
        ctx = (r.get("context") or "")[:50]
        print(f"  {status} [{i}] {reported} {r.get('unit','')}  "
              f"fetched={fetched} ({r.get('fetched_source','')})  "
              f"dev={dev:.2f}%  | {ctx}")
        rows.append({"reported": reported, "fetched": fetched, "deviation_pct": dev,
                     "status": status, "context": r.get("context", "")})

    print()
    if all_pass:
        print("  ✅ PASS — every audited item ≤1% divergence. Report publishable.")
    else:
        print("  ❌ REJECT — at least one item >1%. Fix the figures and re-audit.")
    return {"report": report_name, "items": len(results), "all_pass": all_pass, "rows": rows}


def main():
    parser = argparse.ArgumentParser(
        description="Report Audit Toolkit — research report data spot-check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s extract --report reports/AAPL/AAPL-deep-research-2026-06-26.md
  %(prog)s verdict --results '<filled_json>' --report AAPL-deep-research-2026-06-26.md
        """)
    sub = parser.add_subparsers(dest="command", required=True)

    ex = sub.add_parser("extract", help="Extract a ~15% sample of cited figures")
    ex.add_argument("--report", required=True, help="Path to the report .md")
    ex.add_argument("--sample-pct", type=float, default=0.15)
    ex.add_argument("--out", default="", help="Optional output .json path")

    ve = sub.add_parser("verdict", help="Compare fetched vs reported values")
    ve.add_argument("--results", required=True, help="JSON array of audit results")
    ve.add_argument("--report", default="", help="Report filename (for labeling)")

    args = parser.parse_args()

    if args.command == "extract":
        items = extract(args.report, args.sample_pct)
        out = json.dumps(items, indent=2, ensure_ascii=False)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(out)
            print(f"Wrote {len(items)} audit items to {args.out}")
        else:
            print(out)
    elif args.command == "verdict":
        results = json.loads(args.results)
        verdict(results, args.report)


if __name__ == "__main__":
    main()
