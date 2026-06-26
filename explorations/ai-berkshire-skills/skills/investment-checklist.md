---
name: investment-checklist
description: A six-gate pre-buy screen applying Buffett-style value discipline. Tests one or more companies against circle of competence, business quality, moat depth, management trustworthiness, margin of safety, and position discipline — each rated 1-5 stars — followed by a mirror test and a rapid veto list. Designed to eliminate bad choices, not find the best. ~15-30 min per company.
---

# Buffett Value-Investing Pre-Buy Checklist

Run the pre-buy checklist on `$ARGUMENTS`.

**Input format**: one or more companies, separated by commas, spaces, or slashes. Examples: `AAPL MSFT NVDA` or `ASML.AS, SAP.DE, AIR.PA`.

## Execution flow

### Step 1: Parse input — identify every company to analyze

From `$ARGUMENTS`, resolve each company name/ticker. For each determine:
- Full name, ticker, exchange
- If private, mark "private" with a brief note (any indirect investment path) and skip the full checklist

### Step 1.5: AI research-bias warning

Quick richness grade (A/B/C) per company, noted in the report:

| Grade | Criteria | Impact on the checklist |
|---|---|---|
| A | Listed for years, ample data | Run normally, but beware the "consensus trap" — clear indicators ≠ true certainty |
| B | Limited data, some inferred | Tag every inferred metric with confidence; weight "good business" judgments by data reliability |
| C | Extremely scarce | Don't force-fill the six gates; honestly mark "insufficient data" and focus on verifiable core questions |

**Core principle**: the checklist exists to **eliminate bad choices**. For grade-C companies, "insufficient data" is neither pass nor fail — mark it honestly as a "grey zone requiring primary-source info," not a veto just because the AI couldn't fill the table.

Duan Yongping: there are two kinds of "don't understand" — one where the business is too complex, one where you haven't spent time. AI research's limitation is conflating "little material" with "don't understand."

### Step 2: Parallel data collection

Launch one background Task per company (all in parallel). Each collects:
1. **Profitability**: ROE (5-10yr trend), gross margin, net margin, free cash flow
2. **Valuation**: current price, market cap, PE (TTM), forward PE, PB, dividend yield
3. **Growth**: 3-yr revenue / profit growth
4. **Financial health**: debt level, capex needs, cash reserves, net cash / net debt
5. **Competitive landscape**: market share, main competitors, share trend
6. **Moat evidence**: specific evidence for brand / switching cost / network effect / scale / tech barrier
7. **Management record**: CEO track record, key decisions, ownership, capital allocation
8. **Recent events**: last 6 months — earnings, M&A, regulatory, management changes

### Step 3: Run the six-gate checklist per company

For each listed company, walk the six gates:

---

#### Gate 1: Do I understand this business? (circle of competence)

Answer:
- [ ] Can you state in one sentence how this company makes money?
- [ ] What will it most likely be doing in 10 years?
- [ ] What key variables determine success or failure?
- [ ] Is your knowledge of this industry from deep study or hearsay?

**Scoring** (1-5 stars):
- ★★★★★: Extremely simple, clear model, high 10-yr certainty (e.g. a consumer staple)
- ★★★★☆: Clear but technical — needs some domain knowledge
- ★★★☆☆: Understandable but 10-yr certainty low; fast-changing industry
- ★★☆☆☆: Complex business lines or industry in upheaval
- ★☆☆☆☆: Entirely outside your circle of competence

**Hard veto**: if you can't even articulate how it makes money, mark "outside circle of competence, skip analysis."

---

#### Gate 2: Is this a good business? (economic characteristics)

Use data; **key metrics must be computed precisely by the tool**:
```bash
python tools/financial_rigor.py verify-valuation \
  --price {price} --eps {EPS} --bvps {book_value_per_share} --fcf-per-share {FCF_per_share} --dividend {dividend}
```

| Metric | This company | Reference | Verdict |
|---|---|---|---|
| ROE (5-yr avg) | | >15% good, >20% excellent | |
| Gross margin | | >40% suggests pricing power | |
| Free cash flow | | persistently positive, ≈ net income | |
| Capex intensity | | asset-light beats asset-heavy | |
| Debt level | | interest-bearing debt / net income < 3 yrs | |

**Scoring** (1-5 stars):
- ★★★★★: ROE>25%, high margin, strong FCF, asset-light, low debt (all hit)
- ★★★★☆: 4 of 5
- ★★★☆☆: 3 of 5
- ★★☆☆☆: 2 of 5 or trend deteriorating
- ★☆☆☆☆: most miss or FCF persistently negative

---

#### Gate 3: Is the moat deep enough? (competitive advantage)

Check each:

| Moat type | Present? | Evidence | Widening or narrowing? |
|---|---|---|---|
| Brand / pricing power | | | |
| Switching cost | | | |
| Network effect | | | |
| Cost / scale advantage | | | |
| Tech / patent barrier | | | |

Additional test: if you gave a competitor $10B, could they replicate this business?

**Scoring** (1-5 stars):
- ★★★★★: Multiple overlapping moats, widening
- ★★★★☆: ≥ one strong stable moat
- ★★★☆☆: Moat exists but shallow, or trend unclear
- ★★☆☆☆: Moat eroding
- ★☆☆☆☆: No discernible moat

---

#### Gate 4: Is management trustworthy? (the people factor)

| Check | Assessment |
|---|---|
| Honesty (promise vs delivery) | |
| Capital allocation (buyback / dividend / M&A record) | |
| Shareholder alignment (ownership, compensation) | |
| Owner mindset (founder vs professional manager) | |
| Governance (related-party, goodwill, audit) | |
| Would it run without the CEO? | |

**Scoring** (1-5 stars):
- ★★★★★: Founder at helm, excellent capital allocation, fully aligned
- ★★★★☆: Excellent with minor blemishes
- ★★★☆☆: Competent but governance concerns
- ★★☆☆☆: Integrity or governance problems
- ★☆☆☆☆: Severe integrity issues (→ hard veto)

---

#### Gate 5: Is the price cheap enough? (margin of safety)

| Metric | Value | Historical percentile | Verdict |
|---|---|---|---|
| PE (TTM) | | | |
| Forward PE | | | |
| PB | | | |
| Dividend yield | | | |
| FCF yield | | | |

Additional test (**computed by tool — no mental arithmetic**):
```bash
python tools/financial_rigor.py three-scenario \
  --price {price} --eps {EPS} --shares {shares_in_billions} \
  --growth {optimistic} {neutral} {pessimistic} --pe {optimistic_PE} {neutral_PE} {pessimistic_PE} --currency {currency}
```
- Valuation range across three scenarios (take tool output)
- If you're wrong, how much can you lose buying at the current price?
- Would you double down if the stock halves?

**Scoring** (1-5 stars):
- ★★★★★: ≤50% of intrinsic value, extreme margin of safety
- ★★★★☆: ~70%, good margin of safety
- ★★★☆☆: Fairly valued, modest margin of safety
- ★★☆☆☆: Pricey, insufficient margin of safety
- ★☆☆☆☆: Severely overvalued

---

#### Gate 6: Position & decision discipline (guard against emotion)

Check the emotional signals:
- Are you buying out of FOMO?
- Are you buying because someone recommended it?
- Can you accept a 5-year trading halt?
- Can you write the buy thesis in ≤200 words?

---

### Step 4: Mirror test

For each company write the mirror-test statement:

> "I buy ___ at ___ because:
> 1. The essence of this business is ___ and I understand it;
> 2. Its moat is ___ and is widening/narrowing;
> 3. Management is ___ and is/is not trustworthy;
> 4. The current price is ___ of intrinsic value, with/without sufficient margin of safety;
> 5. Even if I'm wrong, downside is controllable/uncontrollable because ___."

**Can't complete it in 5 sentences = don't buy.** Mark "passed" or "failed."

---

### Step 5: Rapid veto list

For each company, check each item — trigger any one and mark "veto":
- [ ] Can't articulate how the company makes money
- [ ] 3 consecutive years of negative free cash flow with no improvement in sight
- [ ] Management has an integrity stain
- [ ] Competitive advantage being irreversibly eroded
- [ ] Relies on "the next buyer paying more" (greater-fool)
- [ ] Can't bear this position going to zero
- [ ] Buy reason is mainly "everyone's buying" or "it's been rising"
- [ ] Can't write the buy reason in ≤200 words

---

### Step 6: Comparison overview (mandatory for multiple companies)

When analyzing several, produce a comparison table:

| Company | Checklist pass? | Circle | Good biz | Moat | Mgmt | Margin | Core conclusion |
|---|---|---|---|---|---|---|---|
| | | ★☆☆☆☆ | ★☆☆☆☆ | ★☆☆☆☆ | ★☆☆☆☆ | ★☆☆☆☆ | |

---

### Step 7: Final conclusion & file write

For each company give an explicit verdict (don't hedge):
- ✅ **Passes checklist** (X/6 gates) — proceed to deep research
- ❌ **Fails checklist** — which red line was tripped
- ❓ **Grey zone** — what the key dispute is, and what the investor must decide
- N/A — private / not investable

Write the full report to `reports/{ticker}/{ticker}-checklist-{date}.md`.

## Output format

1. Each company gets its own section: six-gate scorecard + core-data table + key risks (3-5) + mirror test + explicit verdict
2. For multiple companies, append the comparison overview table at the end
3. All scores use ★ (1-5), no half-stars
4. Data must be dated; estimates marked "estimate"
5. End with a Buffett quote: "The first rule of investing is don't lose money"
6. Tone: direct, sharp, no filler. Quote Buffett / Munger / Duan sparingly as commentary

## Key principles

- **Better to miss than to err**: the checklist eliminates bad choices, it doesn't find the best
- **Honest about the circle of competence**: if you don't understand it, say so — don't force analysis
- **Margin of safety is the lifeline**: a great company bought too dear still loses money
- **Mirror test is non-negotiable**: if you can't articulate the reason, you don't buy — no exceptions
