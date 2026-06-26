# ai-berkshire-skills

Value-investing deep-dive system, ported from [xbtlin/ai-berkshire](https://github.com/xbtlin/ai-berkshire)
(Buffett/Munger/Duan Yongping/Li Lu methodology systematized as Claude Code skills).
The **deep-dive companion** to `daily-stock-analysis`: the daily brief scans
and flags; this system dives deep on the flags.

## Three-layer architecture

The port faithfully reproduces upstream's three-layer design — the agent layer
is the core, not an afterthought:

```
Layer 1 — Skills (markdown prompt templates, skills/*.md)
   │   invoked as /news-pulse, /investment-team, etc.
   ▼
Layer 2 — Agents (runtime, orchestrated from skill markdown via the Task/Agent tools)
   │   e.g. investment-team spawns 4 parallel analysts (business/financial/industry/risk)
   │        who report back via SendMessage; earnings-team spawns 4 masters + editor + reader
   ▼
Layer 3 — Tools (Python, tools/*.py)
       financial_rigor.py (Decimal valuation), report_audit.py (exit gate),
       stock_screener.py (momentum+value), morningstar_fair_value.py (undervalued discovery)
```

There are **no `.claude/agents/` config files and no MCP** — the agent layer is
Claude Code's native `Task`/`Agent` tool orchestration, scripted from skill
markdown at runtime (this matches upstream exactly). Skills call agents; agents
call tools via Bash; tools are pure Python.

## Boundary with daily-stock-analysis

```
daily-stock-analysis/                 ai-berkshire-skills/
  ├─ main.py  (the brief engine)       ├─ skills/   (layer 1)
  ├─ data_fetcher, analyzer, ...       ├─ tools/    (layer 3)
  └─ output/                           ├─ runner.py (brief → deep-dive bridge)
      ├─ analysis-{date}.json ──read──▶└─ reports/
      └─ gaps-daily-stocks-{date}.json
            ▲
            │ shared/gaps.py  (the ONLY shared module — one-way: daily writes, berkshire reads)
```

These are **separate sibling folders with no cross-imports**. The only contact
point is `shared/gaps.py` and two read-only files (the analysis JSON + gaps
JSON). ai-berkshire never imports a daily-stock-analysis module; the daily
brief never calls an ai-berkshire skill. The link is one-way.

## How the deep dive triggers

`runner.py` reads the latest `analysis-{date}.json` + `gaps-daily-stocks-{date}.json`,
picks tickers flagged `research_deeper`, loads each ticker's gaps, and invokes a
skill per ticker via `claude -p "/<skill> <args>"`. Default skill is
`investment-team` (the multi-agent deep dive); `--skill news-pulse` for the
~10-min rapid attribution.

```
python runner.py                       # deep-dive today's flagged tickers
python runner.py --ticker AAPL         # force one ticker
python runner.py --skill news-pulse    # quick attribution instead of full team
python runner.py --dry-run             # show what would run, don't invoke
```

## Skills (all 18 English-ported)

### Multi-agent (the agent layer — where depth comes from)
| Skill | Agents | When |
|---|---|---|
| `investment-team` | team-lead + 4 parallel analysts (business/financial/industry/risk, one per master) | First-time deep research on a company |
| `earnings-team` | 4 masters + editor + reader-reviewer (7 roles, 3 phases) | Important company's key earnings + publishable article |
| `private-company-research` | multi-agent parallel | Unlisted companies (SpaceX, Stripe, OpenAI) |
| `wechat-article` | author + editor + reader (3 agents) | Turn research into a publishable article |

### Single-agent
| Skill | When |
|---|---|
| `news-pulse` | Rapid (~10 min) attribution of a sharp move |
| `investment-research` | Full 7-module four-master deep dive (single agent) |
| `investment-checklist` | 6-gate pre-buy screen + mirror test + veto |
| `earnings-review` | Single-agent primary-source earnings read |
| `thesis-tracker` | Post-buy discipline: build + track the thesis (health 1-10) |
| `industry-funnel` | Whole-market → 3 finalists screen |
| `industry-research` | Value-chain scan + per-player four-master |
| `quality-screen` | 7-metric de-merit exclusion (+ 3 exemptions) |
| `management-deep-dive` | CEO track record + integrity + key-person risk |
| `bottleneck-hunter` | Supply-chain bottleneck arbitrage for a mega-trend |
| `portfolio-review` | Concentration/correlation/sizing across a holdings list |
| `deep-company-series` | 8-article deep series with fact-check gate |
| `dyp-ask` | Role-play Duan Yongping as a thinking partner |
| `financial-data` | ≥2-source cross-validation spec (the data contract) |

The 4 upstream Chinese originals are preserved as `*_zh.md` for fidelity; the
English ports are the working source. Tool paths in the English ports are
relative (`tools/...`), run from the repo root.

## Tools (layer 3)

| Tool | Purpose |
|---|---|
| `tools/financial_rigor.py` | Decimal-precision market cap, valuation, cross-validation, 3-scenario, Benford (verbatim from upstream) |
| `tools/report_audit.py` | Data spot-check exit gate — `extract` samples ~15% of a report's cited figures, `verdict` compares fetched vs reported (≤1% pass) |
| `tools/stock_screener.py` | Two-layer screen — momentum discovery (60-day high + volume) then 6-dim value validation; signal grading 3/6 probe · 4/6 standard · 5-6/6 conviction |
| `tools/morningstar_fair_value.py` | Fetch all Morningstar fair-value stocks (US + EU universes), compute upside, output Top 100 CSV |

Not ported (out of US+EU scope): `ashare_data.py` (A-share only), `xueqiu_scraper.py` (China platform), `momentum_backtest*.py` (hardcoded NVDA/AMD/MU reference data), `log-command.sh` (usage analytics hook).

## EU cross-validation gap

Third-party fundamental coverage for EU names is thinner and less consistent
than for US. macrotrends covers EU ADRs inconsistently; stockanalysis coverage
varies by exchange. `financial-data.md` handles this honestly: the annual
report is the tie-breaker, and where only one third-party source exists the
figure is tagged `[single-source]` rather than forcing a false cross-check.

## Markets & model

US + EU only (matches the daily brief). yfinance suffixes: `.DE` Xetra, `.L`
LSE, `.PA` Paris, `.AS` Amsterdam. GLM-5.2 via the HPC OpenAI-compatible
endpoint (localhost:8103); Claude-via-Merck-proxy as fallback.

## License & attribution

MIT. Ported from xbtlin/ai-berkshire — credit to the original author. Track
record claims (+69% 2024, +66% YTD 2025) are self-reported and unverifiable;
treat as marketing, not evidence. Not investment advice.

