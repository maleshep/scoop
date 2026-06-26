---
name: bottleneck-hunter
description: AI-driven supply-chain bottleneck arbitrage. For a stated mega-trend (e.g. "AI compute," "EV transition," "GLP-1"), asks not "what does AI recommend" but "if this trend keeps expanding, which link runs out first?" Maps the supply chain, identifies the binding constraint, and finds the companies that supply that constraint (the bottleneck holders capture the value). US + EU only.
---

# Bottleneck Hunter — Supply-Chain Bottleneck Arbitrage

Scan a mega-trend for its binding supply-chain constraint, on `$ARGUMENTS` (a super-trend).

## Core idea

Don't ask "what stocks does this trend lift" — ask "if this trend keeps expanding, **which link runs out first?**" The binding constraint is where value accrues. Find the companies that supply that constraint.

## Execution flow

### Step 1: Decompose the trend's supply chain

Map every link from raw input to end demand:
| Layer | Input → output | Key players | Capacity | Lead time |
e.g. for "AI compute": silicon wafers → litho equipment → foundry → HBM → packaging → GPU → datacenter → power → cooling.

### Step 2: Find the binding constraint

For each layer, assess:
- Capacity utilization (running near 100%?)
- Lead time / order book (stretching?)
- Pricing power (are margins expanding?)
- Expansion difficulty (how long to add capacity?)

The binding constraint is the layer where: demand exceeds supply, expansion is hard/slow, and pricing power is rising. There may be more than one.

### Step 3: Bottleneck-holder companies

For the binding layer, who supplies it?
- Pure-plays vs diversified
- Capacity expansion plans (are they the ones who can grow?)
- Moat (tech, scale, certification, customer lock-in)
- Valuation (has the market priced in the bottleneck, or is it still misread?)

### Step 4: Duration + alternatives

- How long does the bottleneck last? (capacity coming online? substitution possible?)
- What relaxes it? (new tech, new entrants, demand deceleration)
- When it relaxes, who gets commoditized?

### Step 5: Output

```markdown
# {trend} — Bottleneck Hunter
**Date**: {today}

## 1. Supply-chain map
## 2. Binding constraint(s) identified
[layer + evidence: utilization / lead time / pricing / expansion difficulty]
## 3. Bottleneck-holder companies
| Company | Ticker | Exposure | Capacity plan | Moat | Valuation |
## 4. Duration + what relaxes it
## 5. Ranking: best bottleneck plays + why
## 6. Risks (substitution, new capacity, demand break)
```

Save to `reports/{trend}-bottleneck-{date}.md`.

## Key principles

- **The bottleneck captures the value** — not the sexiest layer, the scarcest one
- **Capacity + lead time + pricing power are the tells** — utilization near 100%, stretching lead times, expanding margins
- **Duration matters** — a bottleneck that relaxes in 2 quarters is a trade, not an investment
- **Watch for substitution** — every bottleneck invites a workaround; price the risk of the workaround succeeding
