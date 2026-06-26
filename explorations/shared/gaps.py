"""Shared gaps log — records what an analysis run could NOT determine.

Used by both daily-stock-analysis and ai-berkshire-skills so that deep-dive
runs know exactly what the fast scan left uncertain, instead of guessing.

A "gap" is an observation about missing/weak/conflicting evidence, NOT a
finding. Findings go in the brief; gaps go here. Each gap carries a severity:

  - "blocker": a conclusion cannot be drawn without this (e.g. no price data)
  - "weak":    a conclusion was drawn but on thin evidence (e.g. 1 news item)
  - "conflict": sources disagree (e.g. two feeds give different sentiment)

Usage:
    gaps = GapsLog(project="daily-stocks", run_id="2026-06-26")
    gaps.add("AAPL", "news", "weak", "only 1 news item from yfinance; no Tavily cross-check")
    gaps.save()  # -> output/gaps-<project>-<date>.json
"""
import json
from datetime import datetime
from pathlib import Path


class GapsLog:
    def __init__(self, project: str, run_id: str | None = None, output_dir: Path | None = None):
        self.project = project
        self.run_id = run_id or datetime.now().strftime("%Y-%m-%d")
        self.output_dir = output_dir or (Path(__file__).resolve().parent.parent / project / "output")
        self.entries: list[dict] = []
        self.started_at = datetime.now().isoformat()

    def add(self, subject: str, category: str, severity: str, note: str) -> None:
        if severity not in ("blocker", "weak", "conflict"):
            raise ValueError(f"severity must be blocker|weak|conflict, got {severity}")
        self.entries.append(
            {
                "subject": subject,      # e.g. "AAPL" or a ticker / topic
                "category": category,    # e.g. "news", "fundamentals", "technicals", "price", "calendar"
                "severity": severity,
                "note": note,
            }
        )

    def summary(self) -> dict:
        by_sev = {"blocker": 0, "weak": 0, "conflict": 0}
        for e in self.entries:
            by_sev[e["severity"]] += 1
        return {
            "project": self.project,
            "run_id": self.run_id,
            "started_at": self.started_at,
            "total": len(self.entries),
            "by_severity": by_sev,
            "entries": self.entries,
        }

    def save(self) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / f"gaps-{self.project}-{self.run_id}.json"
        path.write_text(json.dumps(self.summary(), indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def __len__(self) -> int:
        return len(self.entries)
