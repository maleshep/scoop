---
name: wechat-article
description: Three-agent collaboration to produce a publishable long-form article (author + editor + reader-reviewer). The author writes a deep draft from research; the editor refines structure and expression without lowering professionalism; the reader-reviewer audits from the target-audience perspective. Output is a publication-ready article. Use for translating research depth into readable prose. US + EU topics.
---

# Article — Author / Editor / Reader Three-Agent Collaboration

Produce a publishable long-form article on `$ARGUMENTS` (a topic).

**Input**: a topic description, e.g. "why Buffett doesn't buy tech stocks," "GLP-1 economics," "ASML's moat."

## Design

Three agents, distinct roles:
- **Author** — writes a deep first draft from research
- **Editor** — refines structure and expression; does NOT lower professional depth
- **Reader-reviewer** — audits from the target audience's perspective

## Execution

### Step 1: Author — deep draft

Research the topic (primary sources, ≥2-source cross-validation per `financial-data.md`), then write a 1500-3000 word draft:
- Lead with the conclusion (inverted pyramid)
- Data with sources; master-style questions explicit
- Clear sections, not a wall of text

### Step 2: Editor — refine (parallel with reader)

Keep all data and conclusions; make it readable:
- Structure: most-important first; trim tables; bullet heavy analysis; a recap every ~500 words
- Expression: translate hard terms via analogy; keep master quotes sharp; paragraphs ≤4 lines, sentences ≤30 words
- Reader-value test per section: can the reader make a decision? if not, rewrite or cut
- Format: short paragraphs, clear subheads, simple tables

### Step 3: Reader-reviewer — audit (parallel with editor)

Read as a value-investing-literate ordinary investor:
- Readability (30%) — minutes to read, skippable parts, confusing parts, fatigue
- Information value (30%) — deeper understanding? unique vs other analyses? redundant?
- Credibility (20%) — sourced? both sides? over-confident?
- Action guidance (20%) — does the reader know what to do?

Output:
```markdown
## Reader review
### Overall: X/10
### Strengths (2-3)
### Must-fix
### Suggested polish
### Questions the reader wants answered
### One-line summary
```

### Step 4: Author finalize

1. Address every "must-fix"
2. Selectively adopt "suggested polish"
3. Add "questions the reader wanted" where data supports
4. Final read-through for coherence

### Step 5: Fact-check gate

```bash
python tools/report_audit.py extract --report <article_path>
python tools/report_audit.py verdict --results '<filled_json>' --report {filename}
```
**PASS** → publishable; **REJECT** → fix and re-audit.

### Step 6: Output

Save to `reports/articles/{slug}-{date}.md`.

## Key principles

- **Editing isn't dumbing down** — it's making professional content readable
- **Reader review isn't a formality** — genuinely find faults from the reader's seat
- **Fact-check gate is non-negotiable** — no article ships on REJECT
- **Three roles, three perspectives** — author (depth), editor (clarity), reader (utility)
