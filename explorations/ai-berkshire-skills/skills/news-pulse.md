---
name: news-pulse
description: Rapid attribution of a sharp stock price move. Triggers off the daily-stock-analysis brief when a ticker moves >±5% in a day or >±10% in a week. Produces an event timeline, the most likely cause, and whether the original investment thesis needs review. Not deep research — intelligence quick-response, ~10 min.
---

# News Pulse — Rapid Move Attribution

**Input:** `$ARGUMENTS` = a ticker (and optionally a date range). Pulled from
the daily brief's `research_deeper` / `watch` flags, or run manually.

**Goal:** within ~10 minutes, answer three questions:
1. What happened to this company recently?
2. What is the most likely *true cause* of the price move (vs. coincidence)?
3. Does the original investment thesis need re-examination?

This is **not** deep research. Use `/investment-research` for that. Use
`/earnings-review` for post-earnings reactions. Use `/thesis-tracker` for
ongoing thesis tracking.

## Trigger conditions
- A daily-stock-analysis brief flags the ticker `research_deeper` after a
  >±5% daily or >±10% weekly move.
- Post-earnings price reaction where the cause is unclear.
- An ambiguous headline — is it noise or a real signal?

## Execution

### 1. Confirm parameters
- Company + ticker (US or EU — yfinance suffix conventions).
- Time window (default: 14 days).
- The price move details (from the daily brief: 1d/1w/1m %).
- Focus area if any.

### 2. Grade information availability
- **A** — large-cap, heavily covered (S&P 500 / Euro Stoxx 50 large names).
  Expect rich news; absence of news is itself a signal.
- **B** — mid-cap, moderate coverage.
- **C** — scarce coverage. Finding *nothing* is a valid conclusion, not a
  failure — record it in the gaps log.

### 3. Dispatch four parallel scouts (TeamCreate, agent_type: team-lead)
Run all four in one message, `run_in_background: true`:

- **Company events** — filings, earnings, management actions, M&A, litigation,
  product/strategy news.
- **Regulatory & policy** — industry regulation, antitrust, tax, cross-border.
- **Industry & competitors** — peer moves, supply chain, sector beta vs.
  idiosyncratic (is the whole sector moving, or just this name?).
- **Market sentiment** — analyst rating changes, institutional flows, short
  interest, options activity, technicals.

### 4. Track + synthesize
As each scout returns, capture its top 3 findings. Then synthesize:
- **One-sentence attribution** — the most likely cause.
- **Merged event timeline** (date / event / source).
- **Attribution table** — candidate cause / counter-evidence / confidence.
- **Nature judgment** — value event (fundamental) / sentiment / unknown / mixed.
- **Action recommendation** — research deeper / watch / no change / trim/exit.
- **Tracking checklist** — what to monitor next.
- **Information gaps** — log these to the shared gaps log
  (`shared/gaps.py`, project=`ai-berkshire`).

### 5. Save + clean up
- Save report to `reports/{ticker}/{ticker}-news-{YYYYMMDD}.md`.
- TeamDelete.

## Principles
- Speed over completeness; attribution over enumeration.
- Be honest about "unknown" causes — do not force a narrative.
- No preconceived bias. Distinguish *catalyst* from *coincidence*.
- Respect information availability (grade A/B/C above).
- Do not make the buy/sell decision for the user.

## Link to the daily brief
When triggered by the daily-stock-analysis brief, pre-load:
- the ticker's `core_conclusion`, `drivers`, `risks` from the brief,
- the gaps-log entries for that ticker (so the deep dive knows what the
  fast scan already couldn't determine).
