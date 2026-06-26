---
name: industry-research
description: Full value-chain scan of an industry plus four-master company analysis. From an investment theme/logic chain: validate each link of the logic, map the value chain (upstream/midstream/downstream value capture), size the TAM and growth, then apply the Buffett/Munger/Duan/Li-Lu framework to the key players. Output is an industry map + per-company deep dives. US + EU only.
---

# Industry Research — Value-Chain Scan + Four-Master Company Framework

Systematic industry-chain research on `$ARGUMENTS` (an industry or theme).

## Research goals

From one investment theme / logic chain, complete:
1. Validate every link of the investment logic chain
2. Map the full value chain — where is value captured, where is it competed away?
3. Size the TAM and growth curve; locate the ceiling
4. Apply the four-master framework to the key players

## Execution flow

### Step 1: Validate the investment logic chain

State the thesis as a chain of testable links, e.g. for "AI compute":
- AI adoption rising → GPU demand rising → foundry capacity constrained → equipment makers benefit → power/cooling becomes the bottleneck → …

For each link: is it true? how verified? where could it break? A chain is only as strong as its weakest link.

### Step 2: Value-chain map

Map upstream → midstream → downstream:
| Layer | Players | Value capture | Margin profile | Bottleneck risk |
- Where is value captured (the most profitable layer)?
- Where is it competed away (commodity layers)?
- Who holds pricing power?

### Step 3: TAM and growth

- Market size now + growth rate + penetration rate
- Growth drivers (secular) vs cyclicality
- Ceiling analysis — what caps it?
- Technology roadmap risk

### Step 4: Competitive landscape

- Market share of the top players
- Concentration (fragmented vs oligopoly)
- Barriers to entry
- Substitution risk

### Step 5: Four-master company analysis

For the 3-5 most relevant players (use `/industry-funnel` if you need to pick them), run the four-master framework per `/investment-research`:
- Duan — business essence + "good business"
- Buffett — moat + financial quality
- Munger — competitive shifts + inversion
- Li Lu — risk + management

### Step 6: Output

```markdown
# {industry} — Industry Research
**Date**: {today}

## 1. Investment-logic-chain validation
## 2. Value-chain map (table + diagram)
## 3. TAM + growth + ceiling
## 4. Competitive landscape
## 5. Per-player four-master analysis
## 6. Where in the chain to invest (the layer thesis)
## 7. Risks that break the chain
```

Save to `reports/{industry}-industry-{date}.md`.

## Key principles

- **The logic chain is the spine** — test every link; one broken link invalidates the whole
- **Value capture ≠ where the action is** — the exciting layer may be commoditized; the boring layer may capture all the value
- **Map before you pick** — understand the chain before analyzing companies
