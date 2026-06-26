---
name: quality-screen
description: A 7-metric "de-merit" screen that rapidly excludes non-first-rate companies. Hard exclusion on 10-yr avg ROE <8%, 5-yr cumulative FCF negative, interest coverage <2x, long-term gross margin <15%, operating CF/net income <0.7, long-term net margin <5%, 5-yr share dilution >20% (non-M&A) — with 3 carve-out exemptions (strategic-investment, deliberate-thin-margin, high-turnover-thin-margin like Costco). Goal: never kill a great company, but exclude definite non-first-rate ones. Supports single stocks, industries, indices, or themes. US + EU only.
---

# Quality Screen — 7-Metric Rapid Exclusion of Non-First-Rate Companies

Run the de-merit screen on `$ARGUMENTS`.

**Input format**:
| Input | Example | Behavior |
|---|---|---|
| single stock | `AAPL, MSFT, ASML.AS` | screen each |
| industry | `global cloud computing` | search the top 15-20 listed names, screen each |
| index | `S&P 500` `NASDAQ 100` `Euro Stoxx 50` | pull constituents, screen each |
| theme | `global AI compute chain` | search related companies, screen each |

Industry/index/theme modes add: pass-rate stats, in-industry ranking, sector comparison.

## Design principles

- **Goal**: never kill a great company, but exclude definite non-first-rate ones
- **Logic**: 7 hard metrics + 3 exemptions — prefer false-positives to false-negatives
- **Scope**: all listed companies (banks/insurers skip metric 3, interest coverage)

## 7 de-merit metrics

| # | Metric | Exclude if | Measures |
|---|---|---|---|
| 1 | 10-yr average ROE | < 8% | capital efficiency — does shareholder equity beat the opportunity cost |
| 2 | 5-yr cumulative FCF | negative | real cash — are profits "paper wealth" |
| 3 | Interest coverage (EBIT/interest) | < 2x | debt safety — ability to service interest |
| 4 | Long-term gross margin | < 15% | pricing power — product/service differentiation |
| 5 | Operating CF / net income (5-yr avg) | < 0.7 | earnings quality — does profit convert to cash |
| 6 | Long-term net margin | < 5% | resilience — does profit vanish on revenue volatility |
| 7 | 5-yr total share dilution | > 20% (non-M&A) | shareholder interest — is management diluting you |

## 3 exemptions

### Exemption A — strategic-investment (for metric 1)
Exempt metric 1 (ROE) if all three hold:
1. Listed < 10 years
2. Gross margin > 30% (proves the model has pricing power)
3. Operating CF positive the last 2 years (proves cash-generation has begun)

Logic: high gross margin + cash turning positive means the model works; ROE is low only because still investing. Canonical case: Amazon in its build-out phase.

### Exemption B — deliberate-thin-margin (for metric 6)
Exempt metric 6 (net margin) if:
1. Gross margin > 30% (can earn but chooses not to)
2. Net margin recovered to ≥5% the last 2 years, or a clear upward trend

Logic: high gross margin = pricing power; low net margin is a strategic choice (reinvestment), not incapacity. Canonical case: Amazon.

### Exemption C — high-turnover-thin-margin (for metrics 4 and 6)
Exempt metrics 4 and 6 if all three hold:
1. ROE > 20% (low margin but extreme capital return)
2. Operating CF / net income > 1.0 (earnings quality sound)
3. Business model is "membership / platform commission / high-turnover thin-margin" (profit not in product mark-up)

Logic: some first-rate companies hide profit in membership fees, turnover efficiency, or platform take-rates — not gross margin. Canonical case: Costco (gross ~12%, net ~2.5%, but ROE 25%+, renewal 90%+).

## Execution flow

### Step 1: Parse input — determine scope

- specific companies → **single-stock mode**, go to step 2
- industry / index / theme → **batch mode**: WebSearch the top 15-20 listed names (industry), pull constituents (index), or search 15-30 related companies (theme); list them for confirmation; batch in parallel if >30

Resolve each to full name, ticker, exchange.

### Step 2: Parallel data collection

One background agent per company, WebSearch:
1. **ROE**: 10-yr (or since listing), compute average
2. **FCF**: 5-yr operating CF and capex, compute cumulative
3. **Interest coverage**: latest EBIT and interest expense
4. **Gross margin**: 5-yr trend
5. **Operating CF / net income**: 5-yr ratio, average
6. **Net margin**: 10-yr trend, average
7. **Share count**: 5 yrs ago vs now, compute dilution

Source priority: annual report > analyst reports > financial data platforms.

### Step 3: Test each metric

Per company, test all 7: ✅ pass / ❌ fail / ⚠️ boundary (with value). On a fail, check the matching exemption.

### Step 4: Output

```markdown
# Quality-screen results
**Date**: {today}  **Companies**: {N}

## Summary
| Company | ①ROE | ②FCF | ③Int.cov | ④GM | ⑤OCF/NI | ⑥NM | ⑦Dilution | Result |
| xxx | ✅ 24% | ✅ | ✅ | ✅ 56% | ✅ | ✅ 30% | ✅ | **pass** |
| yyy | ❌ 3% | ❌ | ❌ | ✅ 20% | ✅ | ❌ 2% | ✅ | **exclude** |
| zzz | ⚠️→✅ | ✅ | ✅ | ✅ 35% | ✅ | ⚠️→✅ | ✅ | **exempt-pass** |

## Passed (N)
[list]

## Excluded (N)
| Company | Failed metric | Value | Reason |

## Exempt-pass (N)
[with the exemption applied and why]
```

## Key principles

- **Never kill a great company** — exemptions exist precisely for Costco / Amazon / build-phase names
- **Data must be dated**; estimates marked "estimate"
- **Banks/insurers** skip metric 3
- **Conclusion explicit** — pass / exclude / exempt-pass, no hedging
