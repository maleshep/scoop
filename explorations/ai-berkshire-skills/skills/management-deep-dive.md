---
name: management-deep-dive
description: Deep research on a company's management — "buying a stock is buying the person." Reviews the CEO/founder's track record decision-by-decision, capital-allocation skill, integrity (promise vs delivery), owner mindset vs hired-hand, governance (related-party, compensation, audit), and key-person risk (would it survive the CEO leaving?). Input is a company or `person company`. US + EU only.
---

# Management Deep Dive — Buying a Stock Is Buying the Person

Deep research on `$ARGUMENTS`.

**Input**: `company` or `person company`, e.g. `JPM`, `Tim Cook AAPL`, `Christiane Deputy SAP`.

> "Buying a stock is buying the person. Find someone you trust, then hold long." — Duan Yongping

## Execution flow

### Step 1: Identify the subject

Resolve CEO/founder (and key lieutenants if flagged). Determine: tenure, founder vs professional, ownership %, compensation structure.

### Step 2: Decision-by-decision review

Build a table of the CEO's key decisions:
| Date | Decision | Context | Outcome | Score (1-5) | What it reveals |

Cover: strategic bets, M&A, capital-return decisions, crisis responses, product calls. The point is not to list decisions but to read judgment and values from them.

### Step 3: Capital-allocation skill

- R&D return: did R&D spending convert to revenue/margin?
- M&A success rate: accretive or destructive? price discipline?
- Buyback timing: buying at highs (bad) or lows (good)?
- Dividend policy: sustainable, growing, or cut in stress?
- Debt use: conservative or reckless?

### Step 4: Integrity assessment

- **Promise vs delivery**: pull prior-year guidance/commitments, compare to delivery (use the earnings-review promise-tracking method)
- **Communication tone**: candid vs vague/deflective/externalizing
- **Related-party transactions**: fairness
- **Compensation alignment**: pay tied to long-term value or short-term metrics?
- **Disposition pattern**: planned sales vs unplanned dumps

### Step 5: Owner mindset vs hired hand

- Founder still at the helm? economic interest aligned with voting power?
- Skin in the game: ownership % relative to compensation
- Long-term vs quarterly orientation: do decisions favor the 10-year horizon?
- Culture signals: does the leadership team stay, or is there churn?

### Step 6: Governance

- Ownership structure (dual-class? controlled?)
- Related-party transactions
- Board independence and quality
- Audit quality and accounting conservatism
- Goodwill and impairment honesty

### Step 7: Key-person risk

- If the CEO left tomorrow, would the company stay competitive?
- Is there a succession plan? a "bench"?
- How much of the moat is institutional vs personal?

### Step 8: Output

```markdown
# {company} — Management Deep Dive
**Subject**: {name}, {role} since {year}

## 1. One-sentence verdict
## 2. Decision review table
## 3. Capital-allocation scorecard
## 4. Integrity assessment (promise-tracking + tone)
## 5. Owner mindset vs hired hand
## 6. Governance
## 7. Key-person risk
## 8. Duan-style question: if the CEO retired, would it stay competitive?
## 9. Management score (1-5★) + verdict
```

Save to `reports/{ticker}/{ticker}-management-{date}.md`.

## Key principles

- Decisions over words — judge by what they did, not what they said
- Promise-tracking is the integrity test
- Skin in the game > compensation structure
- The key-person question is the real one: is the moat institutional or personal?
