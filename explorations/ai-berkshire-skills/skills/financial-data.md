---
name: financial-data
description: Specification for fetching and cross-validating company financial data. Every key figure must come from ≥2 independent sources, with >1% divergence flagged. US + EU only. Called automatically by investment-research and investment-checklist at their validation checkpoints.
---

# Financial Data — Fetch & Cross-Validation Spec

Applies to all research involving company financials. **Every key figure must come from ≥2 independent sources; divergence >1% must be flagged.**

US + EU only (matches the daily brief). yfinance suffix conventions: US plain symbol; EU `.DE` Xetra, `.L` LSE, `.PA` Paris, `.AS` Amsterdam.

---

## Source priority

### US (AAPL, MSFT, NVDA, JPM, XOM, …)

| Priority | Source | URL | How |
|---|---|---|---|
| 1 (primary) | **macrotrends** | macrotrends.net/stocks/charts/{ticker} | direct, no signup |
| 2 (secondary) | **stockanalysis** | stockanalysis.com/stocks/{ticker}/financials | direct, no signup |
| raw primary | SEC EDGAR | sec.gov/cgi-bin/browse-edgar | 10-K / 10-Q full text |

### EU (SAP.DE, SHEL.L, ASML.AS, AIR.PA, SIE.DE, …)

| Priority | Source | URL | How |
|---|---|---|---|
| 1 (primary) | **stockanalysis** | stockanalysis.com/quote/{exchange}:{ticker}/financials | direct, no signup |
| 2 (secondary) | **daily brief yfinance snapshot** | the analysis-{date}.json from daily-stock-analysis | price, P/E, forward P/E, ROE, debt/equity, margin — already fetched |
| raw primary | **company IR / annual report** | investor-relations page | annual / interim report PDF |

> **EU gap — be honest**: third-party fundamental coverage for EU names is thinner and less consistent than for US. macrotrends covers EU ADRs inconsistently; stockanalysis coverage varies by exchange. Treat the annual report as the tie-breaker, and where only one third-party source exists, tag the figure `[single-source]` rather than forcing a false cross-check. Cash-flow and segment data are the most commonly missing on EU third-party sites.

---

## Execution spec

### Step 1: fetch

For each metric (revenue, net income, gross margin, operating cash flow, debt ratio, …), fetch from **source 1** and **source 2** independently.

### Step 2: compute divergence and flag

```
divergence = |source1 − source2| / source1 × 100%
```

| Divergence | Action |
|---|---|
| ≤ 1% | ✅ consistent — take source 1, cite both |
| 1% – 5% | ⚠️ flag "data diverges" — note both values and the likely cause (FX / accounting definition) |
| > 5% | ❌ flag "major divergence" — must check the raw filing; do not use without resolution |

### Step 3: presentation format

Every key figure must be annotated:

```
Revenue: $123.9B ✅
  - macrotrends: $124.1B
  - stockanalysis: $123.7B
  - divergence: 0.3%
```

Divergence example:
```
Net income: $24.5B ⚠️ data diverges
  - macrotrends: $24.5B (GAAP)
  - stockanalysis: $27.8B (Non-GAAP)
  - divergence: 13.5% — cause: accounting definition (GAAP vs Non-GAAP)
```

---

## Common divergence causes (not necessarily errors)

| Cause | Note |
|---|---|
| GAAP vs Non-GAAP | Most common, especially for profit metrics |
| FX translation | EUR / GBP / USD conversion at different dates |
| Fiscal-year definition | Calendar year vs fiscal year (e.g. Apple's FY ends in October) |
| Consolidation scope | Minority interest included or not |
| Update lag | One platform hasn't refreshed the latest period |

---

## Special rules

1. **Private companies**: only one source — tag the figure `[estimate]`, skip cross-validation
2. **Quarterly vs annual**: prefer annual for cross-validation; quarterly data lags on some platforms
3. **Raw filing wins**: if both sources disagree with the annual report, defer to the report and flag the sources as erroneous

---

## Quick index

| Scenario | Primary | Secondary |
|---|---|---|
| AAPL | macrotrends.net/stocks/charts/AAPL | stockanalysis.com/stocks/aapl |
| MSFT | macrotrends.net/stocks/charts/MSFT | stockanalysis.com/stocks/msft |
| NVDA | macrotrends.net/stocks/charts/NVDA | stockanalysis.com/stocks/nvda |
| JPM | macrotrends.net/stocks/charts/JPM | stockanalysis.com/stocks/jpm |
| XOM | macrotrends.net/stocks/charts/XOM | stockanalysis.com/stocks/xom |
| SAP.DE | stockanalysis.com/quote/xetr:SAP/financials | yfinance snapshot + SAP IR annual report |
| SHEL.L | stockanalysis.com/quote/lon:SHEL/financials | yfinance snapshot + Shell annual report |
| ASML.AS | stockanalysis.com/quote/aex:ASML/financials | yfinance snapshot + ASML annual report |
| AIR.PA | stockanalysis.com/quote/par:AIR/financials | yfinance snapshot + Airbus annual report |
| SIE.DE | stockanalysis.com/quote/xetr:SIE/financials | yfinance snapshot + Siemens annual report |
