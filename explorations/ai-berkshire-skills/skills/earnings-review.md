---
name: earnings-review
description: Single-agent earnings deep-read from primary sources. Fetches the earnings release, call transcript, and shareholder letter directly (not summaries), then extracts core financials, analyzes management tone, tracks prior promises, mines footnotes for hidden info, and gives an explicit beat/in-line/miss verdict with thesis impact. For a quick one-perspective pass; use /earnings-team for the multi-agent deep read. US + EU only.
---

# Earnings Review — Primary-Source Deep Read

Run a primary-source earnings deep-read on `$ARGUMENTS`.

**Input format**: `company period`, e.g. `AAPL 2026Q2`, `ASML.AS 2025 annual`, `MSFT latest` (defaults to most recent).

> "I never read sell-side reports, only the original filings." — Li Lu
> "I read 500 pages a day. That's how knowledge compounds." — Buffett

## Design philosophy

Most AI research tools rely on secondary information (news, report summaries, data sites). Buffett and Li Lu's core skill is reading **primary sources** — annual reports, quarterly filings, call transcripts.

Secondary information is filtered, lagged, and context-stripped. This skill reads primary sources and focuses on what Buffett and Li Lu actually look at.

## Execution flow

### Pre-step: source-availability grade

| Grade | Characteristics | Impact |
|---|---|---|
| A | Full primary text (10-K / annual / call transcript) | Run all steps |
| B | Partial primary or third-party summary | Mark "non-primary"; reduce footnote analysis weight |
| C | Only news + data-site summaries | Focus on core data deltas; skip footnote mining; mark "primary sources thin" |

### Step 1: Fetch primary sources

Launch background agents **in parallel** to fetch:
1. **Earnings release (原文)**: company IR, SEC EDGAR (US 10-K/10-Q), company IR (EU)
2. **Call transcript**: Seeking Alpha, company IR, Motley Fool
3. **Shareholder letter** (if annual): read in full
4. **Investor / analyst-day materials** (if recent)

If full primary text is unavailable, assemble from standard sources per `skills/financial-data.md` (US: macrotrends + stockanalysis; EU: stockanalysis + yfinance + annual report), but mark "non-primary, third-party summary" and flag >1% two-source divergence.

### Step 2: Core financial extraction & verification

#### 2.1 Income statement
| Metric | This period | Prior | YoY change | Guidance | Met? |
Must cover: total + segment/region revenue; gross profit + margin; operating profit + margin (GAAP and non-GAAP); net income (mind non-recurring); EPS (basic vs diluted).

#### 2.2 Cash-flow statement (Buffett's priority)
| Metric | This period | Prior | Change | Watch |
Must cover: operating CF / net income ratio (>100% good, <80% warn); capex mix (maintenance vs growth); FCF = operating CF − capex; buybacks + dividends; period-end cash.

#### 2.3 Balance-sheet health
Must cover: cash + short-term investments vs interest-bearing debt; net cash/debt trend; receivables days (loosening credit to fill revenue?); inventory days (building up?); goodwill/intangible share (impairment risk?).

**Verify with the tool**:
```bash
python tools/financial_rigor.py cross-validate --field revenue --values '{"filing": v1, "yahoo": v2}' --unit {unit}
python tools/financial_rigor.py verify-market-cap --price {price} --shares {shares} --reported {reported} --currency {currency}
python tools/financial_rigor.py verify-valuation --price {price} --eps {EPS} --bvps {bvps} --fcf-per-share {fcf}
```

### Step 3: MD&A close read

This is where Buffett and Li Lu spend the most time — not the numbers, but **how management talks**.

#### 3.1 Management tone analysis
Read MD&A / call line by line, tag signals:
| Signal | Expression | Example |
|---|---|---|
| 🟢 candid | admits problems, gives causes | "margin fell because we over-invested in X" |
| 🟢 clear | concrete strategy, quantified targets | "grow X share from 15% to 20% in 12 months" |
| 🔴 vague | "we believe," "long term," no substance | "we are confident about the future" |
| 🔴 deflective | avoids the question, changes topic | asked about margin, talks about revenue growth |
| 🔴 externalized | blames macro/industry/competitors | "due to the macro environment..." |

#### 3.2 Promise tracking
Extract last period's specific promises; compare to this period's delivery:
| Prior promise | This-period delivery | Verdict |
✅ met / ❌ missed / ⚠️ partial

> Duan: "The simplest test of management is whether they did what they said."

#### 3.3 Key-question identification
Sharpest analyst questions from the call Q&A + management response quality:
| Question | Response | Quality (1-5) | Evasive? |

### Step 4: Footnotes & hidden info

- [ ] **Related-party**: terms fair?
- [ ] **Equity comp**: option/RSU dilution; strike prices
- [ ] **Contingent liabilities**: litigation, guarantees, off-balance-sheet
- [ ] **Accounting-policy changes**: revenue recognition, depreciation lives
- [ ] **Segments**: margin gaps — good business subsidizing bad?
- [ ] **Customer/supplier concentration**: top-5 share

Anomaly checks:
- [ ] receivables growth > revenue (channel-stuffing?)
- [ ] inventory growth > revenue (building up?)
- [ ] operating CF < net income and gap widening (earnings quality?)
- [ ] capex capitalized spiking (beautifying profit?)
- [ ] non-recurring income share rising

### Step 5: Historical comparison

Place this period in a ≥4-quarter (or 3-year) series:
| Metric | Q-4 | Q-3 | Q-2 | Q-1 | This | Trend |
Watch: margin trend; revenue acceleration; cash-flow quality; capex intensity.

Vs management guidance:
| Metric | Prior guidance | Actual | Deviation | Read |

### Step 6: Output the review

```
1. Key data at a glance (one-page table)
2. The three most important changes this period (≤500 words)
3. Management tone & promise tracking
4. Hidden info in footnotes
5. Key questions (call Q&A picks)
6. Relation to the investment thesis (if holding)
7. Conclusion: what did this earnings change?
```

The conclusion must answer explicitly:
1. **Beat, in-line, or miss?** (no "broadly in line" with two-sided hedging)
2. **Thesis impact**: strengthen / none / weaken / break
3. **Next catalyst to watch?**
4. **If holding**: add / hold / trim?

### Step 7: Save

Write to `reports/{ticker}/{ticker}-earnings-{period}.md`.

### Step 8: Data audit (exit gate)
```bash
python tools/report_audit.py extract --report reports/{ticker}/{ticker}-earnings-{period}.md
python tools/report_audit.py verdict --results '<filled_json>' --report {filename}
```
**PASS** → publish; **REJECT** → fix and re-audit.

## Key principles

- **Read the original, not summaries**
- **Watch the change, not the absolute** — trend > number
- **Listen to tone, not just content**
- **Check footnotes, not just the body** — the devil is in the details
- **Conclude, don't summarize** — the point is a judgment, not a recap
