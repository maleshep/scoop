---
name: deep-company-series
description: Write an 8-article deep series on a single company for public publishing. The core IP is not "can write" but "can fact-check" — 99% of finance articles fail the fact-check standard this skill enforces. Each article is researched from primary sources, cross-validated, and audited before publishing. Input is a company; output is 8 long-form articles + a publishing plan. US + EU only.
---

# Deep Company Series — 8 Long Articles on One Company

Write an 8-article deep series on `$ARGUMENTS` (a company), for public publishing.

> The core IP is not "can write" — it's "can fact-check." 99% of finance articles violate this skill's fact-check standard.

## Execution flow

### Step 1: Series plan (8 angles)

Design 8 distinct articles, each a non-overlapping angle:
1. Business essence — what is this business, really?
2. Moat — what protects it?
3. Financial quality — real money or paper?
4. Management — buying the person
5. Industry + value chain — where does value accrue?
6. Risks + inversion — how does it die?
7. Valuation + margin of safety — what's it worth?
8. 10-year outlook — standard oil or 3Com?

Confirm the plan with the user before writing.

### Step 2: Per-article research + draft (sequential or parallel)

For each article:
1. Research from primary sources (filings, transcripts, IR) + ≥2-source cross-validation per `financial-data.md`
2. Verify every number with `financial_rigor.py` — no mental arithmetic
3. Draft the article (1500-3000 words), keeping the master-style questions explicit

### Step 3: Fact-check gate (mandatory per article)

Before any article ships:
```bash
python tools/report_audit.py extract --report <article_path>
# re-fetch each sampled figure from a reliable source
python tools/report_audit.py verdict --results '<filled_json>' --report <filename>
```
**PASS** (all ≤1%) → publishable. **REJECT** → fix and re-audit. No article ships on REJECT.

### Step 4: Publishing plan

- Order + cadence (which article first, why)
- Cross-links between articles
- A series recap / index page
- Distribution notes (where to publish)

### Step 5: Output

```
reports/{ticker}/deep-series/
├── 00-index.md
├── 01-business-essence.md
├── 02-moat.md
├── 03-financial-quality.md
├── 04-management.md
├── 05-industry-value-chain.md
├── 06-risks-inversion.md
├── 07-valuation-margin-of-safety.md
└── 08-ten-year-outlook.md
```

## Key principles

- **Fact-check is the moat** — the differentiator is accuracy, not prose
- **Primary sources, not summaries** — read the filing, not the recap
- **Every number verified** — `financial_rigor.py` + `report_audit.py`
- **8 distinct angles** — no overlap; each article earns its place
- **No article ships on REJECT** — the audit gate is non-negotiable
