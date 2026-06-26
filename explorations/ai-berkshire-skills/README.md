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
| `news-pulse` | ✅ English port | Rapid (~10 min) attribution of a sharp price move. The direct trigger from the daily brief. |
| `investment-research` | 🇨🇳 Chinese only (`_zh.md`) | Full four-master comprehensive deep dive on one company. Port pending. |
| `investment-checklist` | 🇨🇳 Chinese only (`_zh.md`) | Six-gate pre-buy screen. Port pending. |
| `financial-data` | 🇨🇳 Chinese only (`_zh.md`) | Spec for fetching + cross-validating financial data from ≥2 sources. Port pending. |

Original Chinese versions preserved as `*_zh.md` for fidelity to the upstream
prompt engineering. English ports are added incrementally; the `_zh` files are
the source of truth until a port is written.

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
