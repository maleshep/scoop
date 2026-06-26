---
name: industry-funnel
description: Funnel-style value-investing screen from the whole market down to 3 finalists, for a stated industry or theme. Layer 1 casts wide (don't miss any important name), each layer applies tighter quality/valuation filters, ending with 3 deep-dive candidates. Use when you have a theme ("AI compute," "GLP-1," "European defense") and want a shortlist worth deep research. US + EU only.
---

# Industry Funnel — From Whole Market to 3 Finalists

Run a funnel screen on `$ARGUMENTS` (an industry or investment theme), narrowing layer by layer to 3 deep-dive candidates.

## When to use

You name an industry/theme ("AI compute," "innovative drugs," "humanoid robotics," "European defense") and want to:
1. Not miss any important name (cast wide)
2. Apply quality + valuation filters
3. End with 3 worth a deep dive

## Execution flow

### Layer 1 — Wide net (all candidates)

WebSearch + the watchlist to enumerate every relevant listed name:
- Pure-plays and diversified names with material exposure
- Across US and EU exchanges
- Include recently-listed and mid-caps (don't only grab megacaps)

Target 20-40 names. Output the full list with ticker, exchange, one-line business, and exposure relevance.

### Layer 2 — Quality gate (de-merit screen)

Run `/quality-screen` (the 7-metric de-merit) on every name from Layer 1. Eliminate the definite non-first-rate. Exempt-pass names (Costco/Amazon-type) survive.

Output: pass / exclude / exempt-pass, with the failing metric and value.

### Layer 3 — Valuation + moat gate

For survivors, apply:
- Valuation vs history (PE/PB/FCF yield percentile) and vs peers
- Moat strength (brand / switching / network / scale / tech) — widening or narrowing?
- Growth quality (revenue + margin trend, not one-year spikes)
- Capital allocation (buyback / dividend / debt discipline)

Score each 1-5 on the four axes; rank.

### Layer 4 — Finalist selection (top 3)

Pick the top 3 by Layer-3 score, with deliberate diversity:
- not all the same sub-segment
- at least one with a contrarian/overlooked angle if available
- note why the 4th-5th were dropped

### Layer 5 — Output

```markdown
# {theme} — Industry Funnel
**Date**: {today}

## Layer 1: Wide net ({N} names)
[table: ticker / exchange / business / exposure]

## Layer 2: Quality gate
| Name | Result | Note |
[pass / exclude / exempt-pass]

## Layer 3: Valuation + moat scoring
| Name | Valuation | Moat | Growth | Cap-alloc | Total | Rank |

## Layer 4: Top 3 finalists
1. {name} — why
2. {name} — why
3. {name} — why
(dropped: {4th}, {5th} — why)

## Next steps
Run /investment-team on each finalist.
```

Save to `reports/{theme}-funnel-{date}.md`.

## Key principles

- **Wide first, narrow later** — the value of Layer 1 is not missing names, not judging them
- **Quality before valuation** — a cheap bad business is still bad
- **Diversity in the top 3** — don't hand back three copies of the same bet
- **Explicit on what's dropped and why** — the cut list is as informative as the finalists
