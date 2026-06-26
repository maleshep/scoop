---
name: investment-team
description: Multi-agent comprehensive company research. Spawns a 5-role team (team-lead + 4 parallel analysts: business, financial, industry, risk — each from a master's perspective: Duan/Buffett/Munger/Li Lu) via the Task/Agent tools, collects their reports via SendMessage, and synthesizes a final investment memo with a Buffett checklist and tiered recommendations. The deep companion to investment-research, using true parallel agents for depth. ~20-40 min. US + EU only.
---

# Investment Team — Four-Role Parallel Analysis Framework

Run a team-based investment research on `$ARGUMENTS` (a single US or EU ticker). Uses the `Task`/`Agent` tools to create a genuine multi-agent parallel research team.

## Execution flow

### Step 1: Show the team framework

Present this team structure to the user; on confirmation, launch:

| Role | Responsibility | Framework |
|---|---|---|
| **team-lead** (you) | Orchestrate, synthesize, write the final report | Four-master synthesis |
| **business-analyst** | Business model & moat | Duan Yongping |
| **financial-analyst** | Financials & valuation | Buffett |
| **industry-researcher** | Industry & competition | Munger |
| **risk-assessor** | Risk & management | Li Lu |

### Step 1.5: AI research-bias assessment

Before creating the team, present the company's "AI-researchability" grade:

| Grade | Characteristics | Research-strategy adjustment |
|---|---|---|
| A (rich) | Listed for years, heavy coverage | Team focuses on **counter-tests** and **non-consensus views** — avoid "correct platitudes" matching the market |
| B (moderate) | Recently listed, limited coverage | Every inferred figure tagged with confidence; team-lead marks "data sufficiency" in synthesis |
| C (scarce) | Obscure / new / emerging market | Team switches to "first-principles mode": don't chase report completeness, focus on a few core business-essence questions |

**Reminder**: more material ≠ higher certainty. AI-output confidence ≠ true investment certainty. Certainty comes from the business model, not from data volume.

Communicate the grade to each agent — it shapes how they research.

### Step 2: Create the team

Use TeamCreate:
- `team_name`: `{company}-research` (lowercase, e.g. `aapl-research`)
- `agent_type`: `team-lead`

### Step 3: Create four tasks

Use TaskCreate for each (subject, description, activeForm):

#### Task 1 — Business-model analysis
- subject: `Analyze {company} business model, moat, and customer value`
- description: business essence + revenue structure; platform/product flywheel; moat (brand/switching/network/scale/tech, each verified); customer value; segment synergies; Duan's "good business" test (differentiation, pricing power, durable advantage); search latest filings and industry reports.

#### Task 2 — Financial & valuation analysis
- subject: `Analyze {company} financials, profitability, and valuation`
- description: 3-5yr revenue/net-income/operating-profit trend; ROE/ROA/gross margin/operating margin; cash flow (operating, free, capex); balance-sheet health (cash, debt, liquidity); valuation (PE/PS/PB/EV vs history and peers); margin of safety.
  **Financial-rigor verification (mandatory — call the tool via Bash, no mental arithmetic)**:
  - market cap: `python tools/financial_rigor.py verify-market-cap --price {price} --shares {shares} --reported {reported} --currency {currency}`
  - valuation: `python tools/financial_rigor.py verify-valuation --price {price} --eps {EPS} --bvps {bvps}`
  - cross-validate: `python tools/financial_rigor.py cross-validate --field {field} --values '{json}' --unit {unit}`
  - three-scenario: `python tools/financial_rigor.py three-scenario --price {price} --eps {EPS} --shares {shares_bn} --growth {opt} {neut} {pess} --pe {opt} {neut} {pess}`
  - embed tool output in the report as the verification record

#### Task 3 — Industry & competition analysis
- subject: `Analyze the {industry} landscape and {company}'s competitive position`
- description: market size/growth/penetration; competitor share and strategy; per-competitor threat assessment; segment-level landscape; trends (tech, policy, entrants); value chain; search latest industry data.

#### Task 4 — Risk & management assessment
- subject: `Assess {company} investment risk and management quality`
- description: CEO competence/integrity/vision/capital allocation/decision track record; regulatory risk; competitive risk; business risk (new-segment losses, expansion); macro/cyclical risk; governance (ownership, related-party, shareholder returns); 10-yr outlook and what could disrupt the model.

### Step 4: Launch four parallel agents

Use the Agent tool to launch all four **in a single message** (parallel):

Each agent:
- `subagent_type`: `general-purpose`
- `run_in_background`: `true`
- `team_name`: the team name
- `name`: the role (business-analyst / financial-analyst / industry-researcher / risk-assessor)

Agent prompt template:
```
You are the "{role}" in the {company} research team, analyzing {company} from {master}'s investment perspective.

Complete task #{n}: {subject}

Requirements:
{description}

Method:
- Use WebSearch for the latest public information (filings, industry reports, news)
- Financial data must come from ≥2 independent sources per skills/financial-data.md (US: macrotrends + stockanalysis + SEC EDGAR; EU: stockanalysis + the daily brief's yfinance snapshot + annual report). >1% divergence must be flagged.
- Tag sources; go deep, don't stay on the surface.

Output:
- Detailed report, Markdown tables for key data
- Each dimension needs a clear conclusion and rating
- End with the dimension's overall conclusion

When done:
1. TaskUpdate task #{n} to completed
2. SendMessage the full report to team-lead
```

### Step 5: Receive reports and track progress

- Show a live progress table (which agents are done, which still researching)
- As each report arrives, update progress and surface its 3-5 key findings
- Wait for all four

### Step 6: Shut down team members

Once all reports are in, send each agent a `shutdown_request` via SendMessage.

### Step 7: Synthesize the final report

Combine the four reports into this structure:

#### 1. One-sentence conclusion
> 50-100 words: worth investing? core logic.

#### 2. Four-dimension scorecard
| Dimension | Framework | Score (1-5★) | Core judgment |
|---|---|---|---|

Overall: X / 5

#### 3. Key data at a glance
Financials + operating metrics (last 2 years compared)

#### 4. Per-dimension summary
3-5 top findings each

#### 5. Investment thesis (Bull vs Bear)
- 🟢 Bull (5-7 points)
- 🔴 Bear (5-7 points)

#### 6. Buffett pre-buy checklist
| # | Check | Pass? | Note |
10 core checks

#### 7. Final recommendation
- Qualitative table (business quality / management / valuation / timing)
- Tiered action table (aggressive / balanced / conservative → recommendation + price range)
- Catalysts (add signals 3-5, trim signals 3-5)

#### 8. Summary paragraph
100-200 words

### Step 8: Save the report

Write the final report to `reports/{ticker}/{ticker}-investment-team-{date}.md` (date YYYY-MM-DD).

### Step 9: Data audit (exit gate)

```bash
python tools/report_audit.py extract --report <report_path>
# fill fetched_value / fetched_source per skills/financial-data.md
python tools/report_audit.py verdict --results '<filled_json>' --report <report_filename>
```
**PASS** all → publishable; **REJECT** any → fix and re-audit.

### Step 10: Clean up

TeamDelete.

## Key notes

1. **Four agents must launch in parallel** — call the Agent tool four times in one message
2. **Agents report via SendMessage** — message passing, not file collaboration
3. **Data accuracy** — agents use WebSearch for latest data, cross-validate key figures
4. **Explicit conclusions** — don't hedge on buy/watch/avoid and price ranges
5. **Every analysis cites data sources**
6. **Be patient** — four agents need several minutes; update the user live
7. **Anti-bias** — in synthesis, team-lead must assess whether each agent was limited by data sufficiency or over-converged with consensus; the final report includes the richness grade + an "AI research limitations" statement
8. **Honesty under scarcity** — leave blanks marked "insufficient data" rather than filling the framework with speculation
