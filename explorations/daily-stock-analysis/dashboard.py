"""Render the analysis as a self-contained HTML dashboard.

One file per run, no server. Jinja2 template + inline SVG sparklines.
"""
import json
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

import config

TEMPLATES = Path(__file__).resolve().parent / "templates"


def sparkline_svg(closes: list[float], width: int = 120, height: int = 30) -> str:
    """Inline SVG <polyline> of a close-price series, min-max scaled."""
    closes = [c for c in (closes or []) if c is not None]
    if len(closes) < 2:
        return ""
    lo, hi = min(closes), max(closes)
    span = hi - lo or 1.0
    step = width / (len(closes) - 1)
    pts = [
        f"{round(i * step, 1)},{round(height - ((c - lo) / span) * height, 1)}"
        for i, c in enumerate(closes)
    ]
    up = closes[-1] >= closes[0]
    color = "#2e7d32" if up else "#c62828"
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<polyline fill="none" stroke="{color}" stroke-width="1.2" '
        f'points="{" ".join(pts)}"/></svg>'
    )


def _fmt_pct(v) -> str:
    if v is None:
        return "—"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v}%"


def _fmt_num(v, suffix="") -> str:
    if v is None:
        return "—"
    return f"{v}{suffix}"


def _fmt_cap(v) -> str:
    if v is None:
        return "—"
    for unit, factor in (("T", 1e12), ("B", 1e9), ("M", 1e6)):
        if v >= factor:
            return f"${v / factor:.2f}{unit}"
    return f"${v:,.0f}"


def render_html(analysis: dict, gaps, run_id: str) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=True)
    env.globals.update(
        sparkline=sparkline_svg,
        fmt_pct=_fmt_pct,
        fmt_num=_fmt_num,
        fmt_cap=_fmt_cap,
        signal_emoji=lambda s: {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}.get(s, "⚪"),
        action_label=lambda a: {
            "watch": "👀 Watch", "research_deeper": "🔬 Research", "no_action": "—",
        }.get(a, "—"),
    )
    priority = {"research_deeper": 0, "watch": 1, "no_action": 2}
    for rd in analysis.values():
        rd["tickers"].sort(key=lambda t: priority.get(t.get("action"), 9))
    template = env.get_template("dashboard.html.j2")
    gaps_summary = gaps.summary() if hasattr(gaps, "summary") else {"total": 0, "by_severity": {}}
    return template.render(
        analysis=analysis,
        gaps=gaps_summary,
        run_id=run_id,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        analysis_json=json.dumps(analysis, default=str, ensure_ascii=False),
    )


def save(html: str, run_id: str) -> Path:
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    path = config.OUTPUT_DIR / f"dashboard-{run_id}.html"
    path.write_text(html, encoding="utf-8")
    return path


if __name__ == "__main__":
    print("dashboard module — call render_html(analysis, gaps, run_id) from main.py")
