---
name: earnings-team
description: Multi-agent earnings deep-read. Three phases — (1) four master-perspective agents read the earnings in parallel (Duan on business essence, Buffett on cash quality, Munger on competitive shifts, Li Lu on risk signals), (2) team-lead synthesizes a research draft finding consensus and contradictions, (3) an editor agent rewrites it as a publishable article while a reader-reviewer agent audits it. Produces a final article plus per-master research notes. For important companies' key earnings. ~30-50 min. US + EU only.
---

# Earnings Team — Four-Master Parallel Read + Publish

Run a team earnings deep-read on `$ARGUMENTS`.

**Input format**: `company period`, e.g. `AAPL 2026Q2`, `ASML.AS 2025 annual`, `MSFT latest`.

## Design philosophy

A good earnings analysis solves two problems:
1. **You understand the future** — needs four distinct deep perspectives
2. **The reader understands the value** — needs editorial polish and a reader-perspective quality gate

Three phases:
- **Phase 1 · Research**: four masters read in parallel (Duan on business essence, Buffett on financial quality, Munger on competitive shifts, Li Lu on risk signals)
- **Phase 2 · Synthesis**: team-lead combines the four views into a research draft
- **Phase 3 · Publish**: editor agent rewrites it as an article + reader-reviewer agent raises issues → team-lead finalizes

---

## Phase 1: Four-master parallel research

### Step 1: Fetch primary sources

Launch a background agent to fetch in parallel:

| Source | Where | Priority |
|---|---|---|
| Earnings release (原文) | Company IR, SEC EDGAR (US), company IR (EU) | highest |
| Earnings call transcript | Seeking Alpha, company IR, Motley Fool | highest |
| Shareholder letter | Extracted from annual report | high (annual only) |
| Prior-period release/transcript | same | high (for promise-tracking) |

**Source-availability grade**:
| Grade | Characteristics | Impact |
|---|---|---|
| A | Full primary text | Run all steps |
| B | Partial primary or third-party summary | Mark "non-primary"; reduce footnote analysis weight |
| C | Only news + data-site summaries | Focus on core data deltas; skip footnote mining; mark "primary sources thin" |

Communicate the grade to each agent — it shapes analysis depth.

### Step 2: Show the team framework

| Phase | Role | Master / stance | Core question |
|---|---|---|---|
| Research | **Team Lead** (you) | Coordinator | Orchestrate, synthesize, finalize |
| Research | Business-essence reader | Duan Yongping | Did the business get better or worse? |
| Research | Financial-quality auditor | Buffett | Is the money real or fake? |
| Research | Competitive-shift reader | Munger | How is the landscape changing? |
| Research | Risk-signal hunter | Li Lu | What is management hiding? |
| Publish | Editor | Article writer | Rewrite the research draft into a readable article |
| Publish | Reader-reviewer | Ordinary investor | Can the reader follow it? Is it useful? |

### Step 3: Launch four parallel research agents

Use the Agent tool to launch all four **in one message**.

---

#### Agent 1: Business essence (Duan)

**Core question: did the business get better or worse?**

> Duan: "Investing is buying a business. Reading earnings isn't about numbers — it's about whether the business changed."

1. **Revenue structure**: by segment/region, what's accelerating/decelerating; growth from volume or price?
2. **Customer value**: DAU/MAU/paying users, ARPU, retention — strengthening or weakening?
3. **Moat signals**: margin change (pricing power), share change (barriers), switching-cost/network signals
4. **"Good business" test**: Duan's three (differentiation, pricing power, durable advantage) — change this period; heavier or lighter business?
5. **Management product intuition**: concrete vs bureaucratic language; insightful or disconnected

Output: tag each item 🟢 improved / 🟡 flat / 🔴 deteriorated; Duan-style summary.

---

#### Agent 2: Financial quality (Buffett)

**Core question: real money or fake money? Did the margin of safety change?**

> Buffett: "The first thing I do with any earnings is turn to the cash-flow statement."

1. **Core data + verification**: revenue/gross/operating/net — GAAP and non-GAAP; the gap and its trend; ≥2-source cross-validate:
```bash
python tools/financial_rigor.py cross-validate --field revenue --values '{"src1": v1, "src2": v2}' --unit {unit}
```
2. **Cash flow (most important)**: operating CF / net income (>100% good, <80% warn); FCF = operating CF − capex; capex mix (maintenance vs growth); buybacks + dividends
3. **Earnings quality**: receivables growth vs revenue; inventory growth vs revenue; operating-CF vs net-income gap; sudden capitalization; non-recurring income share
4. **Balance-sheet health**: net cash/debt change; receivables/inventory days; goodwill/intangible impairment risk
5. **Valuation & margin-of-safety update**:
```bash
python tools/financial_rigor.py verify-market-cap --price {price} --shares {shares} --reported {reported} --currency {currency}
python tools/financial_rigor.py verify-valuation --price {price} --eps {EPS} --bvps {bvps}
python tools/financial_rigor.py three-scenario --price {price} --eps {EPS} --shares {shares_bn} --growth {opt} {neut} {pess} --pe {opt} {neut} {pess}
```

Output: every computation with tool output; quality signal lights 🟢/🟡/🔴; Buffett-style summary.

---

#### Agent 3: Competitive landscape (Munger)

**Core question: what competitive shift does this earnings reveal?**

> Munger: "I want to know where I'll die, so I don't go there."

1. **Inferred from data**: revenue growth vs industry; margin change (competition easing/tightening); marketing spend ratio (costlier acquisition?); R&D (proactive or forced to follow?)
2. **Peer comparison**: same-period key metrics vs main competitors (if reported); growth/margin/spend; who's winning?
3. **Management's competition discussion**: tone on the call — confident or anxious? new threats named?
4. **Industry-trend signals**: tech change (AI/new platforms); regulatory; demand trends
5. **Munger inversion**: what could kill this company? does this earnings point at those threats? in 5 years, is this a turning point?

Output: landscape verdict (strengthening / flat / deteriorating); peer comparison table; Munger inversion note.

---

#### Agent 4: Risk-signal hunter (Li Lu)

**Core question: what is management hiding? which signals are blinking?**

> Li Lu: "The most important thing in investing is avoiding permanent capital loss."

1. **Management tone analysis**: read MD&A and call line by line, tagging signals: 🟢 candid (admits problems) / 🟢 clear (quantified targets); 🔴 vague (empty words) / 🔴 deflective (non-answers) / 🔴 externalized blame
2. **Promise tracking**: last period's specific promises vs this period's delivery, item by item
3. **Footnotes & hidden info**: related-party, equity-comp dilution, contingent liabilities; accounting-policy changes; segment margin gaps; customer/supplier concentration
4. **Call Q&A picks**: the 3-5 sharpest analyst questions + management response quality score
5. **Permanent-loss risk**: any signal of permanent capital loss; regulatory/compliance/litigation; irreversible bad decisions

Output: management credibility ★1-5; promise-fulfillment rate; risk-signal list; Li Lu summary.

---

### Step 4: Track progress

Show live:
```
📊 {company} {period} earnings-read progress
Phase 1 · Research
  ☐ Duan · business essence    ⏳
  ☐ Buffett · financial quality ⏳
  ☐ Munger · competition        ⏳
  ☐ Li Lu · risk signals        ⏳
Phase 2 · Synthesis             ⏸
Phase 3 · Publish               ⏸
```
Update per report; surface 3-5 core findings each.

---

## Phase 2: Team-lead synthesis

Once all four arrive, team-lead produces the research draft.

**Synthesis is not assembly — it's finding cross-cuts and contradictions:**
1. **Consensus**: what all four agree on (highest confidence)
2. **Contradictions**: e.g. Duan says business improved but Munger says competition worsened — these are the most valuable findings
3. **Blind spots**: what none of the four stressed — is that the most important thing?

### Research-draft structure

```markdown
# {company} {period} Earnings Deep-Read
**Four-master parallel | {date}**

## 1. One-sentence conclusion
> 50-100 words: beat/in-line/miss, core change, thesis impact.

## 2. The three most important changes this period
Focus on what matters; ~100 words each.

## 3. Four-master scorecard
| View | Master | Core question | Conclusion | Score | vs prior |

## 4. Key data at a glance
Financials + operating metrics (this vs prior vs YoY)

## 5. Per-view deep analysis
3-5 top findings each

## 6. Management tone & promise tracking
Promise-fulfillment table + tone-change analysis

## 7. What would each master do?
| Master | If holding | If not holding | Why |

## 8. Conclusion
1. Beat/in-line/miss?
2. Thesis impact: strengthen / none / weaken / break
3. Next catalyst
4. Action
```

---

## Phase 3: Edit + reader review

After the research draft, launch two agents **in parallel**:

### Agent 5: Editor (article rewrite)

Keep all data and conclusions; make it readable for non-professional investors. Not "dumbed down" — "not tiring to read."

1. **Title + opening**: informative, not clickbait; lead with the most important conclusion in 100 words
2. **Structure**: inverted pyramid (top 3 changes first); trim tables; bullet heavy analysis; a "recap" every ~500 words
3. **Expression**: translate hard terms via analogy ("operating CF 30% below net income" → "earned 100 but only 70 reached the pocket"); keep the master quotes sharp and memorable; paragraphs ≤4 lines, sentences ≤30 words
4. **Reader value test**: after each section — can the reader make a decision? if not, rewrite or cut; end with an explicit "so what?" for holders and watchers
5. **Format**: short paragraphs, clear subheads, simple tables, 1000-3000 words

Output: the rewritten article.

### Agent 6: Reader-reviewer (ordinary investor)

Read as a value-investing-literate ordinary investor who holds/watches the name.

1. **Readability (30%)**: minutes to read? skippable parts? confusing parts? rhythm fatigue?
2. **Information value (30%)**: deeper understanding after reading? "oh, so that's why" moments? what's unique vs other analyses? what's redundant?
3. **Credibility (20%)**: data sourced? both sides shown? over-confident judgments? master quotes apt?
4. **Action guidance (20%)**: do you know what to do? specific advice for holders vs watchers? next catalysts/watch items?

Output:
```markdown
## Reader review
### Overall score: X/10
### Strengths (2-3)
### Must-fix (hard errors)
### Suggested polish
### Questions the reader wants answered but the article didn't
### One-line summary
```

### Team-lead finalize

1. Address every "must-fix" item
2. Selectively adopt "suggested polish"
3. Add "questions the reader wanted answered" where data supports it
4. Final read-through for coherence

---

## Output files

```
reports/{ticker}/
├── {ticker}-earnings-{period}.md              ← final article
├── {ticker}-earnings-{period}-research-draft.md ← four-master synthesis (internal)
├── {ticker}-earnings-{period}-duan.md          ← business essence
├── {ticker}-earnings-{period}-buffett.md       ← financial quality
├── {ticker}-earnings-{period}-munger.md       ← competition
├── {ticker}-earnings-{period}-lilu.md         ← risk signals
└── {ticker}-earnings-{period}-reader-review.md ← reader review
```

## Data audit (exit gate)

```bash
python tools/report_audit.py extract --report reports/{ticker}/{ticker}-earnings-{period}.md
python tools/report_audit.py verdict --results '<filled_json>' --report {filename}
```
**PASS** → publishable; **REJECT** → fix and re-audit.

## Relation to other skills

| Skill | Role | When |
|---|---|---|
| `/earnings-review` | single-agent earnings read | quick pass, one perspective |
| **`/earnings-team` (this)** | **6-agent team read + publish** | **important company, key earnings, depth + publishing** |
| `/investment-team` | 4-agent full company research | first time researching a company |

## Key principles

- **Read the original, not summaries** — fetch primary sources wherever possible
- **Four views aren't four departments** — they must cross-check and challenge, not each talk past the others
- **Team-lead's value is synthesis** — find intersections and contradictions, not assemble
- **Explicit conclusions** — "broadly in line with some notable points" is forbidden
- **Inversion throughout** — every positive finding carries a counter-argument
- **Editing isn't lowering professionalism** — it's making professional content readable
- **Reader review isn't a formality** — genuinely find faults from the reader's seat
- **Data accuracy** — cross-validate; verify with financial_rigor.py
