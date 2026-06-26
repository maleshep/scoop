"""LLM analysis: turn price + technicals + news into a structured dashboard.

Uses Claude Sonnet via the Anthropic SDK. Returns a JSON object per ticker:
{
  "symbol", "name", "signal": "bullish|bearish|neutral",
  "confidence": "low|medium|high",
  "core_conclusion": "<2-3 sentences>",
  "drivers": ["<driver 1>", "<driver 2>"],
  "risks": ["<risk 1>"],
  "action": "watch|no_action|research_deeper"
}
"""
import json
import sys
from pathlib import Path
from typing import Protocol

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # explorations/

import anthropic

import config


class LLMProvider(Protocol):
    """A chat-completion provider that returns a parsed JSON object.

    Extracted from the original _call_glm/_call_claude dispatch so the API
    service layer (and the agent) can depend on an interface, not globals.
    """

    def chat(self, system: str, user: str, max_tokens: int = 2000) -> str: ...


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").lstrip("json").strip()
    return json.loads(text)


class GLMProvider:
    """GLM-5.2 via the direct HPC OpenAI-compatible endpoint (localhost:8103).

    GLM emits reasoning in a separate `reasoning_content` field and the final
    answer in `content`. max_tokens is generous because reasoning consumes
    budget before the answer is emitted.
    """

    def chat(self, system: str, user: str, max_tokens: int = 2000) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=config.GLM_API_KEY, base_url=config.GLM_BASE_URL)
        resp = client.chat.completions.create(
            model=config.GLM_MODEL,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""

    def chat_json(self, system: str, user: str, max_tokens: int = 2000) -> dict:
        return _parse_json(self.chat(system, user, max_tokens))


class ClaudeProvider:
    """Claude via the Merck palantir Bearer-proxy (CI fallback)."""

    def chat(self, system: str, user: str, max_tokens: int = 2000) -> str:
        if config.ANTHROPIC_AUTH_TOKEN and config.ANTHROPIC_BASE_URL:
            client = anthropic.Anthropic(
                api_key="bearer-auth",  # required by SDK, ignored by proxy
                base_url=config.ANTHROPIC_BASE_URL,
                default_headers={"Authorization": f"Bearer {config.ANTHROPIC_AUTH_TOKEN}"},
            )
        else:
            client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model=config.MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in resp.content if block.type == "text")

    def chat_json(self, system: str, user: str, max_tokens: int = 2000) -> dict:
        return _parse_json(self.chat(system, user, max_tokens))


def default_provider() -> LLMProvider:
    """Select the provider from config.MODEL_PROVIDER (glm default, claude fallback)."""
    if config.MODEL_PROVIDER == "glm":
        return GLMProvider()
    return ClaudeProvider()


_PROVIDER: LLMProvider | None = None


def _get_provider() -> LLMProvider:
    global _PROVIDER
    if _PROVIDER is None:
        _PROVIDER = default_provider()
    return _PROVIDER


SYSTEM_PROMPT = """You are a disciplined equity analyst producing a CONCISE daily brief.
You are NOT giving investment advice — you summarize price action, technicals, and news into a neutral signal.

Rules:
- Signal reflects the balance of the day's evidence, not a long-term call.
- Cite the specific data point or news item behind each driver/risk.
- If data is thin or contradictory, set confidence to "low" and signal to "neutral".
- "action" is about research priority, not trading: "watch" = monitor for a developing story;
  "research_deeper" = worth a fundamental dive; "no_action" = nothing notable today.
- Return ONLY valid JSON matching the schema. No markdown fences, no prose.
"""

SCHEMA = {
    "symbol": "string",
    "name": "string",
    "signal": "bullish | bearish | neutral",
    "confidence": "low | medium | high",
    "core_conclusion": "2-3 sentence summary of today's price action and why",
    "drivers": ["1-3 short bullets, each tied to a data point or headline"],
    "risks": ["1-2 short bullets"],
    "action": "watch | no_action | research_deeper",
}


def _fmt(v, suffix=""):
    if v is None:
        return "n/a"
    return f"{v}{suffix}"


def _user_prompt(tk: dict, news: list[dict], region: str, index: dict) -> str:
    news_lines = "\n".join(f"- {n['title']}" for n in news) or "(no news found)"
    macd = tk.get("macd") or {}
    return f"""REGION: {region}
REGION INDEX: {index.get('symbol')} @ {index.get('price')} (1d {index.get('change_1d_pct')}% | 1w {index.get('change_1w_pct')}% | 1m {index.get('change_1m_pct')}%)

TICKER: {tk['symbol']} — {tk.get('name','')} ({tk.get('sector','?')} / {tk.get('industry','?')})
PRICE: {tk['price']} {tk.get('currency','')}  (1d {tk['change_1d_pct']}% | 1w {tk['change_1w_pct']}% | 1m {tk['change_1m_pct']}%)
EXCESS MOVE vs INDEX: {tk.get('change_1d_vs_index','n/a')}%  | peer rank {tk.get('change_1d_pct_rank','n/a')} (0=worst, 1=best in region)

FUNDAMENTALS:
  P/E {tk.get('pe_ratio')} | forward P/E {tk.get('forward_pe')} | P/B {tk.get('price_to_book')} | EPS {tk.get('eps_trailing')}
  ROE {tk.get('roe')} | debt/equity {tk.get('debt_to_equity')} | profit margin {tk.get('profit_margin')} | revenue growth {tk.get('revenue_growth')}
  market_cap {tk.get('market_cap')} | div_yield {tk.get('dividend_yield')}
  analyst target mean {tk.get('analyst_target_mean')} | recommendation {tk.get('recommendation')} | next earnings {tk.get('next_earnings_date')}

TECHNICALS:
  RSI(14) {tk.get('rsi_14')} | MACD {macd.get('macd_line')} / signal {macd.get('signal_line')} / hist {macd.get('histogram')}
  20d avg volume {tk.get('avg_volume_20d')} | 20d volatility(ann.) {tk.get('volatility_20d')}% | beta {tk.get('beta')} / beta_vs_index {tk.get('beta_vs_index')}

RECENT NEWS:
{news_lines}

Produce the JSON dashboard. Schema:
{json.dumps(SCHEMA, indent=2)}
"""


def _call_llm(prompt: str) -> dict:
    """Analyze a prompt through the configured LLM provider; returns parsed JSON."""
    return _get_provider().chat_json(SYSTEM_PROMPT, prompt)


def analyze_ticker_with(provider: LLMProvider, tk: dict, news: list[dict], region: str, index: dict, gaps=None) -> dict:
    """Run analysis with an explicit provider (used by the API/agent layers)."""
    prompt = _user_prompt(tk, news, region, index)
    if gaps is not None:
        if tk.get("pe_ratio") is None:
            gaps.add(tk["symbol"], "fundamentals", "weak", "P/E ratio missing — valuation context absent")
        if tk.get("change_1d_pct") is None:
            gaps.add(tk["symbol"], "price", "blocker", "no 1-day price change — cannot assess daily direction")
        if not news:
            gaps.add(tk["symbol"], "news", "blocker", "no news items — conclusion is technicals-only")
        if tk.get("rsi_14") is None:
            gaps.add(tk["symbol"], "technicals", "weak", "RSI missing — momentum context absent")
        if tk.get("next_earnings_date") is None:
            gaps.add(tk["symbol"], "calendar", "weak", "earnings date missing — catalyst timing unknown")
        if tk.get("analyst_target_mean") is None:
            gaps.add(tk["symbol"], "consensus", "weak", "no analyst target — valuation benchmark absent")
    try:
        result = provider.chat_json(SYSTEM_PROMPT, prompt)
        result["price"] = tk["price"]
        result["change_1d_pct"] = tk["change_1d_pct"]
        result["change_1w_pct"] = tk["change_1w_pct"]
        result["change_1m_pct"] = tk["change_1m_pct"]
        result["change_1d_vs_index"] = tk.get("change_1d_vs_index")
        result["change_1d_pct_rank"] = tk.get("change_1d_pct_rank")
        result["currency"] = tk.get("currency", "")
        result["sector"] = tk.get("sector")
        result["industry"] = tk.get("industry")
        result["pe_ratio"] = tk.get("pe_ratio")
        result["forward_pe"] = tk.get("forward_pe")
        result["price_to_book"] = tk.get("price_to_book")
        result["roe"] = tk.get("roe")
        result["debt_to_equity"] = tk.get("debt_to_equity")
        result["profit_margin"] = tk.get("profit_margin")
        result["revenue_growth"] = tk.get("revenue_growth")
        result["market_cap"] = tk.get("market_cap")
        result["dividend_yield"] = tk.get("dividend_yield")
        result["analyst_target_mean"] = tk.get("analyst_target_mean")
        result["recommendation"] = tk.get("recommendation")
        result["next_earnings_date"] = tk.get("next_earnings_date")
        result["rsi_14"] = tk.get("rsi_14")
        result["macd"] = tk.get("macd")
        result["avg_volume_20d"] = tk.get("avg_volume_20d")
        result["volatility_20d"] = tk.get("volatility_20d")
        result["beta"] = tk.get("beta")
        result["beta_vs_index"] = tk.get("beta_vs_index")
        result["sparkline"] = tk.get("sparkline", [])
        result["news"] = [{"title": n.get("title", ""), "url": n.get("url", ""), "sources": n.get("sources", [])} for n in news]
        return result
    except Exception as e:
        if gaps is not None:
            gaps.add(tk["symbol"], "llm", "blocker", f"analysis call failed: {e}")
        return {
            "symbol": tk["symbol"], "name": tk.get("name", tk["symbol"]),
            "signal": "neutral", "confidence": "low",
            "core_conclusion": f"Analysis failed: {e}", "drivers": [], "risks": [],
            "action": "no_action", "price": tk["price"],
            "change_1d_pct": tk["change_1d_pct"], "change_1w_pct": tk["change_1w_pct"],
            "change_1m_pct": tk["change_1m_pct"], "currency": tk.get("currency", ""),
            "error": str(e),
        }


def analyze_ticker(tk: dict, news: list[dict], region: str, index: dict, gaps=None) -> dict:
    prompt = _user_prompt(tk, news, region, index)

    # Record data-side gaps before calling the LLM, so we know what evidence
    # the conclusion was (or wasn't) built on.
    if gaps is not None:
        if tk.get("pe_ratio") is None:
            gaps.add(tk["symbol"], "fundamentals", "weak", "P/E ratio missing — valuation context absent")
        if tk.get("change_1d_pct") is None:
            gaps.add(tk["symbol"], "price", "blocker", "no 1-day price change — cannot assess daily direction")
        if not news:
            gaps.add(tk["symbol"], "news", "blocker", "no news items — conclusion is technicals-only")
        if tk.get("rsi_14") is None:
            gaps.add(tk["symbol"], "technicals", "weak", "RSI missing — momentum context absent")
        if tk.get("next_earnings_date") is None:
            gaps.add(tk["symbol"], "calendar", "weak", "earnings date missing — catalyst timing unknown")
        if tk.get("analyst_target_mean") is None:
            gaps.add(tk["symbol"], "consensus", "weak", "no analyst target — valuation benchmark absent")

    try:
        result = _call_llm(prompt)
        result["price"] = tk["price"]
        result["change_1d_pct"] = tk["change_1d_pct"]
        result["change_1w_pct"] = tk["change_1w_pct"]
        result["change_1m_pct"] = tk["change_1m_pct"]
        result["change_1d_vs_index"] = tk.get("change_1d_vs_index")
        result["change_1d_pct_rank"] = tk.get("change_1d_pct_rank")
        result["currency"] = tk.get("currency", "")
        result["sector"] = tk.get("sector")
        result["industry"] = tk.get("industry")
        result["pe_ratio"] = tk.get("pe_ratio")
        result["forward_pe"] = tk.get("forward_pe")
        result["price_to_book"] = tk.get("price_to_book")
        result["roe"] = tk.get("roe")
        result["debt_to_equity"] = tk.get("debt_to_equity")
        result["profit_margin"] = tk.get("profit_margin")
        result["revenue_growth"] = tk.get("revenue_growth")
        result["market_cap"] = tk.get("market_cap")
        result["dividend_yield"] = tk.get("dividend_yield")
        result["analyst_target_mean"] = tk.get("analyst_target_mean")
        result["recommendation"] = tk.get("recommendation")
        result["next_earnings_date"] = tk.get("next_earnings_date")
        result["rsi_14"] = tk.get("rsi_14")
        result["macd"] = tk.get("macd")
        result["avg_volume_20d"] = tk.get("avg_volume_20d")
        result["volatility_20d"] = tk.get("volatility_20d")
        result["beta"] = tk.get("beta")
        result["beta_vs_index"] = tk.get("beta_vs_index")
        result["sparkline"] = tk.get("sparkline", [])
        result["news"] = [{"title": n.get("title", ""), "url": n.get("url", ""), "sources": n.get("sources", [])} for n in news]
        return result
    except Exception as e:
        if gaps is not None:
            gaps.add(tk["symbol"], "llm", "blocker", f"analysis call failed: {e}")
        return {
            "symbol": tk["symbol"],
            "name": tk.get("name", tk["symbol"]),
            "signal": "neutral",
            "confidence": "low",
            "core_conclusion": f"Analysis failed: {e}",
            "drivers": [],
            "risks": [],
            "action": "no_action",
            "price": tk["price"],
            "change_1d_pct": tk["change_1d_pct"],
            "change_1w_pct": tk["change_1w_pct"],
            "change_1m_pct": tk["change_1m_pct"],
            "currency": tk.get("currency", ""),
            "error": str(e),
        }


if __name__ == "__main__":
    import data_fetcher

    data = data_fetcher.fetch_all()
    region = "US"
    rd = data[region]
    tk = rd["tickers"][0]
    import news_fetcher

    news = news_fetcher.fetch_news(tk["symbol"])
    print(json.dumps(analyze_ticker(tk, news, region, rd["index"]), indent=2))
