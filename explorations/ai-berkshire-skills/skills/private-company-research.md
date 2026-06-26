---
name: private-company-research
description: Multi-agent parallel deep research for unlisted companies (SpaceX, Stripe, OpenAI, a private startup). Designed for the information-scarce regime: the goal is to reconstruct the company's true value — not the market valuation, but what the business is actually worth — from whatever primary signals exist (funding rounds, hires, product, supply chain, public filings if any). Outputs a valuation range with explicit confidence and a primary-verification question list. US + EU only.
---

# Private Company Research — Multi-Agent Deep Research Under Scarcity

Team-based deep research on `$ARGUMENTS` (an unlisted company).

**Goal**: under inherently scarce information, reconstruct the company's **true value** — not the market valuation, but what the business is actually worth.

## Framework

Launch parallel agents:
1. **Funding + valuation signals** — rounds, valuations, investors, terms if leaked
2. **Business essence** — revenue model, unit economics if inferrable, customer base
3. **People** — founders, key hires, track record, churn
4. **Product + moat** — what's the wedge, is it defensible, what would a competitor with $10B do
5. **Supply chain + ecosystem** — suppliers, partners, dependencies
6. **Public filings + regulatory** — any SEC/EC filings, antitrust, lobbying, permits
7. **Risk + downside** — what kills it, permanent-loss scenarios

## Execution

### Step 1: Scarcity grade

| Grade | Characteristics | Approach |
|---|---|---|
| A | Some primary signals (filings, round terms, hires) | Reasoned estimate with tagged confidence |
| B | Mostly secondary (press, analysts) | Range estimate, heavily caveated |
| C | Near-zero | First-principles only; output is questions, not a number |

### Step 2: Parallel data collection

One background agent per dimension above. All use WebSearch + WebFetch. Tag every figure `[estimate]` / `[single-source]` / `[inferred]`.

### Step 3: Synthesize a valuation range

- Reverse-engineer from the last round's valuation × implied growth
- Compare to public comps (which listed company is the closest business)
- Build a rough DCF on inferred fundamentals, with explicit assumption ranges
- Output: a wide valuation range with confidence and the assumptions driving it

### Step 4: Primary-verification question list

End with the questions AI cannot answer from public material — the ones a primary source (employee, investor, customer, supplier) would need to resolve. This is the honest output under scarcity.

### Step 5: Output

```markdown
# {company} — Private Company Research
**Date**: {today}  **Scarcity grade**: {A/B/C}

## 1. One-sentence verdict
## 2. Business essence + revenue model
## 3. People
## 4. Product + moat
## 5. Funding + valuation signals
## 6. Supply chain + ecosystem
## 7. Risks + downside
## 8. Valuation range (with assumptions + confidence)
## 9. Primary-verification questions (what AI can't resolve)
```

Save to `reports/{company}-private-{date}.md`.

## Key principles

- **Honesty under scarcity** — "insufficient data" marked, not filled with speculation
- **True value ≠ market valuation** — the round price is a signal, not the answer
- **Tag every figure** — `[estimate]` / `[single-source]` / `[inferred]`
- **The question list is the output** — under scarcity, knowing what you don't know is the deliverable
