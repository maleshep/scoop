---
name: portfolio-review
description: Portfolio management — the step from "researching companies" to "managing a portfolio." Takes a holdings list (e.g. `AAPL 30%, MSFT 20%, ASML 20%, JPM 15%, cash 15%`), assesses concentration risk, correlation, position sizing vs conviction, cash buffer, and thesis integrity per holding, then recommends rebalancing, adds, trims, and exits. Not stock-picking — portfolio construction. US + EU only.
---

# Portfolio Review — From Researching Companies to Managing a Portfolio

Review `$ARGUMENTS` (a holdings list).

**Input**:
- `AAPL 30%, MSFT 20%, ASML.AS 20%, JPM 15%, cash 15%`
- or `AAPL 500sh @275, MSFT 100sh @352, ...`
- or `my portfolio` (if `reports/portfolio-latest.md` exists)

## Design philosophy

Good company ≠ good portfolio. A portfolio adds:
- **Concentration risk** — even great companies can correlate
- **Position sizing** — does the weight match conviction?
- **Cash buffer** — dry powder for opportunities
- **Thesis integrity** — is every holding still thesis-intact?

## Execution flow

### Step 1: Parse holdings + fetch state

Resolve each line to ticker, shares/weight, cost basis. WebSearch current price, weight, unrealized P&L.

### Step 2: Concentration + correlation

- Single-position weight (flag >20%)
- Sector concentration (flag one sector >40%)
- Theme overlap (e.g. three AI-exposed names = one bet disguised)
- Correlation estimate (which holdings move together?)
- Cash weight (too low <5% = no dry powder; too high >30% = no conviction)

### Step 3: Position sizing vs conviction

For each holding, cross-reference its thesis (if `reports/{ticker}-thesis.md` exists, read the health score):
| Holding | Weight | Thesis health | Conviction | Sizing verdict |
Flag: high weight + weakening thesis (overweight a deteriorating story); low weight + strong thesis (under-invested conviction).

### Step 4: Thesis integrity sweep

Run a light thesis-tracker check on each holding (assumptions + red lines). Any red line triggered → exit candidate.

### Step 5: Rebalance recommendations

- **Trim**: overweight + weakening thesis, or concentration breach
- **Add**: underweight + strong thesis + margin of safety re-emerging
- **Exit**: thesis broken, or correlation reducing diversification without conviction
- **Cash**: target buffer + deployment plan for specific watchlist names at specific prices

### Step 6: Output

```markdown
# Portfolio Review
**Date**: {today}

## 1. Holdings snapshot
| Ticker | Weight | Cost | Price | P&L | Thesis health |
## 2. Concentration + correlation analysis
## 3. Position sizing vs conviction
## 4. Thesis integrity sweep
## 5. Rebalance plan
| Action | Holding | From → To | Why |
## 6. Watchlist + deployment prices
## 7. One-sentence portfolio verdict
```

Save to `reports/portfolio-review-{date}.md` (and update `portfolio-latest.md`).

## Key principles

- **A portfolio is more than its parts** — correlation and sizing matter as much as stock quality
- **Weight should track conviction + thesis health**, not just past returns
- **Cash is a position** — dry powder has option value
- **Exit discipline** — a broken thesis should be cut regardless of P&L
