---
name: investment-research
description: Full fundamental deep-dive research on a single company, using the Buffett/Munger/Duan Yongping/Li Lu four-master framework. Seven modules — business essence, moat, management, valuation/margin of safety, industry trend, inversion/risk — with programmatic data cross-validation via financial_rigor.py and a data-audit exit gate. Slow, thorough, ~30-60 min. Triggers off a daily-stock-analysis brief's research_deeper flag or standalone.
---

# Investment Research — Buffett / Munger / Duan Yongping / Li Lu Four-Master Framework

Systematic investment research on `$ARGUMENTS` (a single US or EU ticker, optionally with a focus area).

## Research framework

Based on the methodologies of Buffett, Munger, Duan Yongping, and Li Lu. Execute the seven modules in order.

### Pre-step: AI research-bias self-check (mandatory)

Before researching, assess the company's "AI-researchability" and surface data bias.

**Information-richness grade**:
| Grade | Characteristics | AI research trap | Mitigation |
|---|---|---|---|
| A (rich) | Listed for years, heavy analyst coverage, dense media | Consensus is strong; AI output converges on market pricing; little alpha | Stress the counter-test: why don't smart people buy it? What risk is being ignored? |
| B (moderate) | Listed 1-3 years, limited coverage, some data inferred | AI may fill gaps with "reasonable estimates" that look complete but are false certainty | Tag every inferred figure with confidence; distinguish "evidence-based estimate" from "fabricated filler" |
| C (scarce) | Recently listed / obscure / emerging market, almost no coverage | AI, lacking material, becomes over-cautious and misjudges "can't see clearly = bad" | Use first-principles questions (below) to extract the business essence from limited information |

**First-principles method for grade-C companies**:
When public material is thin, don't patch together a "complete-looking" report. Focus on these underlying questions:
1. Who are the customers? Why do they pay? Do they have alternatives?
2. What drives repeat purchases — habit, lock-in, or continuous new value?
3. Could a competitor with $10B replicate this business?
4. What key decisions has management made? What do those decisions reveal about their judgment and values?

**Bias checklist** (maintain throughout):
- [ ] Does my "certainty" come from the business essence, or from the volume of material?
- [ ] If I halved the material on this company, would my conclusion change?
- [ ] Is my output nearly identical to market consensus? If so, where is my information edge?
- [ ] Am I underweighting the possibility that "public material is scarce but the business is excellent"?

Write the richness grade at the top of the report, and in the final conclusion distinguish "AI research confidence" from "actual investment certainty."

### Step 1: Data collection

> **Data-source spec**: see `skills/financial-data.md`. Every financial figure must come from ≥2 independent sources; >1% divergence must be flagged.
> - US: macrotrends (primary) + stockanalysis (secondary), SEC EDGAR for raw filings
> - EU: stockanalysis (primary) + the daily brief's yfinance snapshot (secondary), company IR / annual report for raw filings

Launch background agents (Task tool) to collect from the web:
1. Revenue structure: most recent fiscal year + last 4 quarters segment revenue, growth, gross margin
2. Financial metrics: 5-year revenue, net income, gross margin, operating margin, free cash flow, cash reserves
3. Competitive landscape: market share, main competitors compared
4. Business model & moat: source of core competitive advantage
5. Technology: core tech stack, R&D spend
6. Management: founder/CEO track record, ownership %, key decisions
7. Industry outlook: TAM, growth forecasts
8. Risk factors: geopolitical, regulatory, supply chain
9. Current valuation: market cap, PE, PS, PEG, EV/Revenue
10. Bull and bear core theses

#### Data cross-validation (mandatory — use the financial-rigor tool)

After collection, **you must call `tools/financial_rigor.py`** to programmatically verify key figures, eliminating LLM mental-arithmetic error.

**Must-verify data points**:
- Total shares outstanding (from the exchange, Yahoo, StockAnalysis — ≥2 sources)
- Current price and market cap (**manually compute price × shares and compare to reported**, to catch unit errors)
- Most recent fiscal-year revenue and net income (annual report + ≥1 third-party source)
- Cash reserves and net cash (cash + short-term investments − total debt; mind definition differences)
- Management ownership % (distinguish economic interest from voting power; note dual-class structures)

**Mandatory verification steps (call the tool via Bash)**:

Step 1 — market-cap check (exact Decimal, not float):
```bash
python tools/financial_rigor.py verify-market-cap \
  --price {price} --shares {shares} --reported {reported_mktcap} --currency {currency}
```

Step 2 — multi-source cross-validation:
```bash
python tools/financial_rigor.py cross-validate \
  --field {field} --values '{"source1": value, "source2": value}' --unit {unit}
```
Run separately for revenue, net income, cash reserves.

Step 3 — precise valuation-ratio check (PE/PB/ROE/FCF yield):
```bash
python tools/financial_rigor.py verify-valuation \
  --price {price} --eps {EPS} --bvps {book_value_per_share} --fcf-per-share {FCF_per_share} --dividend {dividend_per_share}
```

**Rules**:
1. ≥2 independent sources for every key figure
2. On divergence, prefer the annual report / exchange filing and note the cause
3. **Every computed figure must be verified by the tool — no LLM mental arithmetic**
4. Embed tool output in the report appendix "Key-data cross-validation record"
5. If the tool reports ❌ excessive divergence, diagnose before continuing
6. Run from the repo root so the relative `tools/` path resolves

**Common errors to guard against**:
- Market-cap units: billions vs millions vs local currency — easy to drop/add a zero
- FCF definition: capex treatment differs across sources (leases, acquisitions)
- Debt definition: operating-lease liabilities included or not
- Ownership: dual-class companies' economic interest ≠ voting power

### Step 2: Business-essence analysis — Duan Yongping's "right business"

- Define the business in one sentence
- Revenue structure breakdown (table)
- 5-year profitability trend (chart)
- Business-model canvas: one-time sale vs subscription/repeat? hardware vs software vs platform?
- Ecosystem stickiness / customer lock-in strength
- Gross margin vs peers — explain why high/low
- Operating leverage
- **Duan-style question**: what's good about this business? If you had to describe it in one sentence, what is it?

### Step 3: Moat assessment — Buffett's "economic moat"

Verify the five moat types:

| Moat type | Test |
|---|---|
| Brand / pricing power | Can it raise prices without losing volume? |
| Switching cost | How costly is customer migration to a competitor? |
| Network effect | Does the product get better as users grow? |
| Scale advantage | How large is the cost advantage from scale? |
| Tech / patent barrier | How many years ahead is the tech? Can it be copied? |

Assess moat trend: widened or narrowed over 5 years? Forecast the next 5.

**Buffett-style question**: will this moat still exist in 10 years? What could destroy it?

### Step 4: Inversion & risk list — Munger's "invert, always invert"

- List every path by which this company could fail (table: path / probability / impact)
- Historical analogy: find companies that were in a similar position — what happened?
- Cross-disciplinary: network-effect theory, tech-adoption curves, game-theoretic competition
- Bias self-check: narrative bias, anchoring, survivorship bias
- Collect the core bear thesis

**Munger-style question**: where am I most likely wrong? Why would a smart person not buy / short this?

### Step 5: Management assessment — Duan's "right people" + Buffett's "managerial integrity"

- CEO/founder key-decision review (table: date / decision / outcome / score)
- Capital-allocation skill: R&D return, M&A success, buyback timing
- Shareholder alignment: management ownership, compensation, disposition
- Organizational capability: team stability, key-person risk
- Culture

**Duan-style question**: if the CEO retired, would this company stay competitive?

### Step 6: Industry & civilization trend — Li Lu's "civilization-evolution framework"

- Is the industry in a civilization-level paradigm shift?
- Historical tech-revolution analogy (steam / electricity / internet / AI)
- TAM growth curve and ceiling
- Position in the industry value chain
- Technology roadmap risk
- Customer / supplier concentration

**Li Lu-style question**: looking back from 20 years on, is this company "the Standard Oil of this era" or "a fleeting 3Com"?

### Step 7: Valuation & margin of safety — Buffett's "intrinsic value" + Duan's "right price"

- Current market pricing (key-ratio table) — **verified by tool**
- Reverse DCF: what growth is the current price implying?
- Three-scenario valuation — **computed by tool, no mental arithmetic**:
```bash
python tools/financial_rigor.py three-scenario \
  --price {price} --eps {EPS} --shares {shares_in_billions} \
  --growth {optimistic} {neutral} {pessimistic} \
  --pe {optimistic_PE} {neutral_PE} {pessimistic_PE} --years 3 --currency {currency}
```
- vs own historical valuation
- vs peer valuation

**Duan-style question**: if the market closed for 5 years tomorrow, would you hold at this price?

### Step 8: Synthesis memo

Summary table:

| Dimension | Conclusion | Confidence |
|---|---|---|
| Business quality (Duan) | | |
| Moat (Buffett) | | |
| Management (Duan + Buffett) | | |
| Biggest risk (Munger) | | |
| Civilizational trend (Li Lu) | | |
| Valuation (Buffett + Duan) | | |

Final decision table:

| Strategy | Recommendation |
|---|---|
| If empty-handed | |
| If holding | |
| Sell signal | |
| Add signal | |

Simulated commentary from the four masters (in blockquotes).

## Output requirements

1. Every analysis must cite data with sources
2. Use Markdown tables for key data
3. Each module ends with the corresponding master's "question"
4. Write the full report to `reports/{ticker}/{ticker}-deep-research-{date}.md`
5. Conclusions must be explicit — buy / watch / avoid
6. Valuation must give a concrete price range
7. **Report top** must include the richness grade (A/B/C) and an "AI research limitations" statement
8. **Report end** must distinguish "AI analysis confidence" from "investment certainty" — the former depends on data volume, the latter on business essence. Tell the reader which conclusions rest on sufficient data and which on inference from limited information
9. For grade-C companies, end with a "questions requiring primary-source verification" list — field research, product experience, supply-chain interviews to fill AI's blind spots

## Data audit (exit gate — mandatory before publishing)

After writing the report to file, run a data spot-check and only publish on pass.

**Step 1 — extract a spot-check list (15% random sample):**
```bash
python tools/report_audit.py extract --report <report_path>
```
Outputs a JSON template, each item with `fetched_value` (to fill).

**Step 2 — fetch & verify:**
For each item, fetch the figure per `skills/financial-data.md` (US: macrotrends + stockanalysis; EU: stockanalysis + yfinance + annual report) and fill `fetched_value` / `fetched_source` / `fetched_value2` / `fetched_source2`.

**Step 3 — verdict:**
```bash
python tools/report_audit.py verdict --results '<filled_JSON>' --report <report_filename>
```

- **PASS**: every spot-check item ≤1% divergence → report publishable
- **REJECT**: any item >1% → fix the figure and re-audit until pass
