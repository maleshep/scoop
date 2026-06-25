"""Render the analysis as a Markdown dashboard."""
from datetime import datetime
from pathlib import Path

import config

SIGNAL_EMOJI = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}
ACTION_LABEL = {
    "watch": "👀 Watch",
    "research_deeper": "🔬 Research",
    "no_action": "—",
}


def _fmt_pct(v) -> str:
    if v is None:
        return "—"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v}%"


def render(analysis: dict) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"# Daily Market Brief — {today}", ""]

    for region, rd in analysis.items():
        idx = rd["index"]
        lines.append(f"## {region} — {idx.get('symbol', '')}")
        lines.append(
            f"**Index:** {idx.get('price', '—')} "
            f"(1d {_fmt_pct(idx.get('change_1d_pct'))} · "
            f"1w {_fmt_pct(idx.get('change_1w_pct'))} · "
            f"1m {_fmt_pct(idx.get('change_1m_pct'))})"
        )
        lines.append("")

        # Action priority sort: research_deeper > watch > no_action
        priority = {"research_deeper": 0, "watch": 1, "no_action": 2}
        tickers = sorted(rd["tickers"], key=lambda t: priority.get(t.get("action"), 9))

        lines.append("| | Ticker | Price | 1d | 1w | 1m | Signal | Action |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for t in tickers:
            lines.append(
                f"| {SIGNAL_EMOJI.get(t.get('signal', 'neutral'), '⚪')} "
                f"| **{t['symbol']}** ({t.get('name', '')[:24]}) "
                f"| {t.get('price', '—')} {t.get('currency', '')} "
                f"| {_fmt_pct(t.get('change_1d_pct'))} "
                f"| {_fmt_pct(t.get('change_1w_pct'))} "
                f"| {_fmt_pct(t.get('change_1m_pct'))} "
                f"| {t.get('signal', 'neutral')} "
                f"| {ACTION_LABEL.get(t.get('action'), '—')} |"
            )
        lines.append("")

        # Detail blocks for anything worth attention
        for t in tickers:
            if t.get("action") in ("research_deeper", "watch") or t.get("confidence") == "high":
                lines.append(f"### {SIGNAL_EMOJI.get(t.get('signal'), '⚪')} {t['symbol']} — {t.get('name', '')}")
                lines.append(f"> {t.get('core_conclusion', '')}")
                if t.get("drivers"):
                    lines.append("**Drivers:**")
                    for d in t["drivers"]:
                        lines.append(f"- {d}")
                if t.get("risks"):
                    lines.append("**Risks:**")
                    for r in t["risks"]:
                        lines.append(f"- {r}")
                lines.append("")

    lines.append("---")
    lines.append("*Neutral signal = data-driven summary, not investment advice.*")
    return "\n".join(lines)


def save(markdown: str) -> Path:
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    fname = config.OUTPUT_DIR / f"brief-{datetime.now().strftime('%Y-%m-%d')}.md"
    fname.write_text(markdown, encoding="utf-8")
    return fname


if __name__ == "__main__":
    print("report module — call render(analysis) from main.py")
