---
name: thesis-tracker
description: Post-buy discipline system. On first use, builds an investment thesis (5-sentence core thesis, falsifiable assumption checklist, red-line sell conditions, valuation anchors) and saves it; on subsequent uses, re-checks every assumption and red line against the latest data and scores thesis health 1-10. Prevents the "research → buy → pray" failure mode. US + EU only.
---

# Thesis Tracker — Post-Buy Discipline System

Run a thesis-tracking check on `$ARGUMENTS`.

**Input format**:
- `company` — first use builds the thesis; later uses track
- `company build thesis` — force-rebuild
- `company quarterly check` — check against the latest earnings

> "Buying is just the start. The real work is continuous tracking while holding." — Li Lu
> "When the facts change, I change my mind. What do you do?" — Keynes

## Design philosophy

Most investors: research → buy → pray. No systematic post-buy tracking means:
- Hold when you should sell ("wait, it'll come back")
- Panic-sell when you shouldn't ("down 20%, was I wrong?")
- Forget why you bought ("why did I buy this again?")

Buffett and Li Lu write down sell conditions *before* buying, then check thesis integrity every quarter.

## Execution flow

### Step 1: Determine mode

Check if `reports/{ticker}-thesis.md` exists:
- absent → **build thesis** mode
- present → **tracking check** mode
- absent but user says it exists → ask for the path

---

## Mode A: Build the thesis

### A0: Data collection

WebSearch for current price, valuation (PE/PB/dividend yield), latest earnings core data — to fill the valuation anchor. If a `/investment-research` or `/investment-team` report exists, read it first.

Verify valuation with `python tools/financial_rigor.py verify-valuation`.

### A1: Core thesis (≤200 words, mandatory)

Answer each in one sentence:
```
I buy {company} at {price}, because:
1. The essence of this business is ___, and I understand how it makes money
2. Its moat is ___, and is widening/stable
3. Management is ___, trustworthy because ___
4. The current price is ___ of intrinsic value; the margin of safety comes from ___
5. Even if I'm wrong, downside is controllable because ___
```
**If you can't complete 5 sentences, the thesis itself is flawed — the buy wasn't clear enough.**

### A2: Core-assumption checklist

Decompose the thesis into falsifiable assumptions:
| # | Assumption | How to verify | Frequency | Status |
| 1 | e.g. revenue growth sustains ≥15% | quarterly revenue growth | each quarter | 🟢 holds |
| 2 | e.g. gross margin stable ≥60% | quarterly gross margin | each quarter | 🟢 holds |
| 3 | e.g. management keeps buying back | buyback announcements / cash-flow | each quarter | 🟢 holds |
| 4 | e.g. competitors don't break through | industry data / peer earnings | semi-annual | 🟢 holds |

Usually 3-7. Too few = shallow thinking; too many = unfocused thesis.

### A3: Red-line list (any trigger = must re-evaluate)

| # | Red line | Severity | Action on trigger |
| 1 | Management integrity problem (fraud, related-party) | fatal | exit immediately |
| 2 | Core business revenue down 2 consecutive quarters | severe | cut 50%, re-evaluate |
| 3 | Moat breached (competitor reaches parity) | severe | deep research, consider exit |
| 4 | Regulation fundamentally changes the model | severe | re-value intrinsic value |
| 5 | Large unplanned management disposition | warning | investigate |

> Duan: "There are only three reasons to sell: 1. you were wrong; 2. the fundamentals changed; 3. you found something better."

### A4: Valuation anchors

| Metric | At buy | Optimistic | Neutral | Pessimistic |
| price | | | | |
| PE | | | | |
| market cap | | | | |
| intrinsic-value estimate | | | | |
| margin of safety | | | | |

### A5: Save

Write `reports/{ticker}-thesis.md` with: build date, buy price + position, core thesis (5 sentences), assumption checklist, red-line list, valuation anchors, tracking log (empty initially).

---

## Mode B: Tracking check

### B1: Load the thesis

Read `reports/{ticker}-thesis.md`: core thesis, assumptions, red lines, last check.

### B2: Collect latest data

WebSearch: latest earnings (if new), recent events (management, regulation, competition), current price + valuation, insider transactions.

### B3: Check each assumption

| # | Assumption | Prior status | Latest evidence | Current status | Change |
| 1 | Revenue growth ≥15% | 🟢 holds | Q4 growth 12% | 🟡 weakening | ⚠️ |
| 2 | Gross margin ≥60% | 🟢 holds | 61.2% | 🟢 holds | — |

Status:
- 🟢 **holds** — data supports it
- 🟡 **weakening** — still acceptable, trend unfavorable
- 🔴 **damaged** — data clearly doesn't support it
- ⚫ **broken** — assumption overturned

### B4: Red-line check

| # | Red line | Triggered? | Evidence |
| 1 | Management integrity | ❌ | — |
| 2 | Core business down 2 quarters | ❌ | — |

**Any red line triggered → flag prominently with an explicit action recommendation.**

### B5: Valuation update

| Metric | At buy | Last check | Now | Change |
| price | | | | |
| PE (TTM) | | | | |
| intrinsic-value estimate | | | | |
| margin of safety | | | | |

### B6: Output

```
1. Thesis health score (/10)
2. Assumption-check results (table)
3. Red-line-check results (table)
4. Key changes this period (≤500 words)
5. Valuation update
6. Conclusion & action
7. Focus for next check
```

**Health formula**: 10 − (⚫broken ×3) − (🔴damaged ×2) − (🟡weakening ×1) − (red-lines-triggered ×5); floor 1, ceiling 10.

| Score | Meaning | Action |
|:---:|---|---|
| 9-10 | thesis intact | hold |
| 7-8 | minor weakening | hold, watch the weakening assumptions |
| 5-6 | thesis pressured | cut, re-evaluate |
| ≤4 | thesis broken | exit |
