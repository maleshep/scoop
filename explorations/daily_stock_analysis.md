# daily_stock_analysis — Architecture Digest

**Repo:** https://github.com/ZhuLinsen/daily_stock_analysis
**Local clone:** `C:/Users/M316235/repo/temp/daily_stock_analysis/`
**Date reviewed:** 2026-06-23

## 1. Project shape

A-share / HK / US multi-market AI stock analysis. Fetches market data from 11+ sources, runs LLM-powered analysis via multi-agent pipeline, fans out to 13 notification channels.

**Layout:**
- `main.py` (58K chars monolithic CLI), `server.py` (FastAPI), `webui.py`
- `src/` — 162 Python files, ~90K LoC across 14 subpackages
- `data_provider/` — 11 fetchers (akshare, baostock, yfinance, tushare…) implementing strategy pattern
- `src/agent/` — Multi-agent ReAct loop with skills/strategies/tools
- `src/llm/` — Backend abstraction over LiteLLM (Phase 1; one backend only)
- `src/notification_sender/` — 13 sender implementations, one per channel
- `api/` — FastAPI routes
- `tests/` — 203 test files

## 2. Core abstractions (load-bearing)

1. **`StockAnalysisPipeline`** — `src/core/pipeline.py:82+`. Orchestrates data → context → LLM → signal → notify. ThreadPoolExecutor for concurrent multi-stock.
2. **`DataFetcherManager`** — `data_provider/base.py:90+`. Strategy pattern over `BaseFetcher` ABC. Failover, rate-limiting, circuit breakers.
3. **`AgentOrchestrator` / `AgentExecutor`** — `src/agent/orchestrator.py:75+`, `executor.py`. Two interchangeable runners. Factory swaps via `AGENT_ARCH` config.
4. **`GenerationBackend` Protocol** — `src/llm/generation_backend.py:81+`. Unified LLM interface with `GenerationErrorCode` enum, capability flags, `GenerationResult` dataclass. One impl: `LiteLLMGenerationBackend`.
5. **`NotificationService`** — `src/notification.py`. Single analysis → multi-channel fanout. Channel resolution via `notification_routing.py`.
6. **`AnalysisContextBuilder`** — `src/services/analysis_context_builder.py`. Assembles typed `AnalysisContextPack` with weighted data-quality scoring.

## 3. Patterns worth copying

**Multi-provider LLM routing** (`src/llm/backend_registry.py:56-79`):
```python
def resolve_generation_backend_id(config) -> str:
    backend_id = normalize_backend_id(config.generation_backend, default=LITELLM_BACKEND_ID)
    if backend_id not in SUPPORTED_GENERATION_BACKENDS:
        raise _unsupported_backend_error(...)
    return backend_id
```
Registry-driven. `SUPPORTED_GENERATION_BACKENDS = frozenset({LITELLM_BACKEND_ID})` makes adding backends explicit. Protocol + capability flags let you degrade gracefully per-feature.

**Notification fanout** — Single `NotificationService.send()` iterates configured channels. Each `*_sender.py` is ~50-100 LoC. Pure composition, no inheritance.

**Data source normalization** (`data_provider/base.py:69-100`) — Prefix/suffix stripping with explicit allowlist. Centralized validation prevents fetcher-specific drift.

**Structured error model** — `GenerationError(error_code, stage, retryable, fallbackable, backend, details)` with free-string `stage` (`generation`, `validation`, `fallback`). Avoids version churn.

## 4. Things to skip

- **`main.py` (58K chars)** — Monolithic CLI + bootstrap. Lazy pipeline descriptor (`_LazyPipelineDescriptor`) is over-engineered.
- **Dual executor/orchestrator** — Duplicate interfaces; factory swap adds complexity without payoff for non-stock domain.
- **`services/` bloated** — 40+ files with single-purpose guards (`phase_decision_guardrail`, `daily_market_context_guardrail`). Symptom of domain-rule accretion.
- **Chinese-market hardcoding** — `is_bse_code`, `STOCK_NAME_MAP`, `market_profile.py` assume A-share semantics (北交所 BSE, 涨跌停, 停牌). Not portable.

## 5. Tech debt / red flags

- **`main.py` 58K chars** — hard to review, mixed concerns.
- **Dual agent paths** — unclear migration status.
- **203 tests but no contract tests for `GenerationBackend`** — the most copy-worthy piece is undertested.
- **Prompt templates scattered** across `src/agent/skills/`, `templates/`, inline strings. No single registry.
- **`.env.example` is 45K** — too many knobs.
- **`Phase 1` comment on `generation_backend.py:11`** — abstraction is incomplete, only LiteLLM wired.

## 6. Verdict

**Moderately portable.** Load-bearing abstractions (`GenerationBackend`, `DataFetcherManager`, notification fanout, `GenerationError`) are domain-agnostic and cleanly separated.

**Most copy-worthy pattern:** the **LLM backend abstraction** (`GenerationBackend` Protocol + `backend_registry.py`). Cleanest piece, most reusable for a research/learning app with multi-model routing.

**Engagement verdict:** Fork-and-extend only if you keep the fork small — use `src/llm/` + `src/notification_sender/` + `data_provider/base.py` patterns. Avoid `src/core/pipeline.py` and `src/agent/`. **Read-only is safer** if you're not adopting Chinese-market specifics.
