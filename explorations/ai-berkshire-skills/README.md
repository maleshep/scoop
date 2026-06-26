# ai-berkshire-skills

Value-investing deep-dive skills, ported from [xbtlin/ai-berkshire](https://github.com/xbtlin/ai-berkshire)
(Buffett/Munger/Duan/Li-Lu methodology systematized as Claude Code skills).

This is the **deep-dive companion** to `daily-stock-analysis`. The daily brief
scans and flags; these skills dive deep on the flags.

## Architecture

```
daily-stock-analysis brief ──(research_deeper flags)──▶ ai-berkshire skills
        │                                                      │
        └──── shared/gaps.py ◀───────────(logs what's uncertain)─┘
```

- The **daily brief** runs fast (yfinance + news + GLM) and emits per-ticker
  signals + an `action` field. Anything `research_deeper` is a candidate.
- The **ai-berkshire skills** take a flagged ticker and run the slow,
  fundamental, multi-perspective deep dive.
- Both write to the **shared gaps log** (`explorations/shared/gaps.py`):
  - daily-stocks records what the fast scan couldn't determine,
  - ai-berkshire reads those gaps so the deep dive knows what to resolve, and
    records its own residual gaps.

## Skills

| Skill | Status | When to use |
|---|---|---|
| `news-pulse` | ✅ English | Rapid (~10 min) attribution of a sharp price move. The direct trigger from the daily brief. |
| `investment-research` | ✅ English | Full four-master (Buffett/Munger/Duan/Li Lu) 7-module deep dive on one company. |
| `investment-checklist` | ✅ English | Six-gate pre-buy screen + mirror test + rapid veto. Eliminates bad choices. |
| `financial-data` | ✅ English | Spec for fetching + cross-validating financial data from ≥2 sources. |

All four skills are English-ported for the US+EU workflow. The original Chinese
versions are preserved as `*_zh.md` for fidelity to the upstream prompt
engineering. Tool paths in the English ports are relative (`tools/...`), run
from the repo root; the `_zh` files retain the upstream `~/ai-berkshire/...`
absolute paths and are kept for reference only.

## Tool: financial_rigor.py

`tools/financial_rigor.py` — verbatim from upstream, zero external deps
(Python stdlib only). Called automatically by the skills at validation
checkpoints:

- `verify-market-cap` — share price × shares vs reported
- `verify-valuation` — precise PE/PB/ROE/FCF yield (Decimal, not float)
- `cross-validate` — compare one metric across N sources, flag if >1% diverge
- `three-scenario` — optimistic/neutral/pessimistic target price
- `benford` — first-digit anomaly detection
- `calc` — arbitrary precise financial expression

## Tool: report_audit.py

`tools/report_audit.py` — the data spot-check exit gate for `investment-research`.
Stdlib-only, matches `financial_rigor.py`'s style. After a report is written,
the skill samples ~15% of the figures it cited, re-fetches each from a reliable
source, and compares fetched vs reported (Decimal precision):

- `extract --report <path>` — scan a report `.md`, emit a JSON template of
  sampled figures with `fetched_value` fields to fill
- `verdict --results '<json>' --report <name>` — ≤1% divergence across all
  items = PASS (publishable); any item >1% = REJECT (fix and re-audit)

## EU cross-validation gap

Third-party fundamental coverage for EU names is thinner and less consistent
than for US. macrotrends covers EU ADRs inconsistently; stockanalysis coverage
varies by exchange. `financial-data.md` handles this honestly: the annual
report is the tie-breaker, and where only one third-party source exists the
figure is tagged `[single-source]` rather than forcing a false cross-check.
Cash-flow and segment data are the most commonly missing on EU third-party
sites.

## Markets

US + EU only (matches the daily brief). yfinance suffix conventions:
`.DE` Xetra, `.L` LSE, `.PA` Paris, `.AS` Amsterdam.

## Model

GLM-5.2 via the HPC OpenAI-compatible endpoint (localhost:8103), same as the
daily brief. Claude-via-Merck-proxy as CI fallback.

## License & attribution

MIT. Ported from xbtlin/ai-berkshire — credit to the original author. Track
record claims (+69% 2024, +66% YTD 2025) are self-reported and unverifiable;
treat as marketing, not evidence. Not investment advice.
