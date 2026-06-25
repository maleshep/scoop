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

import anthropic

import config


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


def _user_prompt(tk: dict, news: list[dict], region: str, index: dict) -> str:
    news_lines = "\n".join(f"- {n['title']}" for n in news) or "(no news found)"
    return f"""REGION: {region}
REGION INDEX: {index.get('symbol')} @ {index.get('price')} (1d {index.get('change_1d_pct')}% | 1w {index.get('change_1w_pct')}% | 1m {index.get('change_1m_pct')}%)

TICKER: {tk['symbol']} — {tk.get('name','')}
PRICE: {tk['price']} {tk.get('currency','')}  (1d {tk['change_1d_pct']}% | 1w {tk['change_1w_pct']}% | 1m {tk['change_1m_pct']}%)
FUNDAMENTALS: P/E {tk.get('pe_ratio')} | market_cap {tk.get('market_cap')} | div_yield {tk.get('dividend_yield')}

RECENT NEWS:
{news_lines}

Produce the JSON dashboard. Schema:
{json.dumps(SCHEMA, indent=2)}
"""


def _call_llm(prompt: str) -> dict:
    # Corporate environment routes Anthropic through the Merck "palantir" proxy
    # which authenticates with a Bearer JWT (ANTHROPIC_AUTH_TOKEN), NOT the
    # SDK's default x-api-key. When the token+base URL are set, pass the token
    # as an Authorization header and give the SDK a dummy api_key (it requires
    # one but the proxy ignores it). Outside the corp net, a plain API key works.
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
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in resp.content if block.type == "text").strip()
    # strip accidental markdown fences
    if text.startswith("```"):
        text = text.strip("`").lstrip("json").strip()
    return json.loads(text)


def analyze_ticker(tk: dict, news: list[dict], region: str, index: dict) -> dict:
    prompt = _user_prompt(tk, news, region, index)
    try:
        result = _call_llm(prompt)
        # keep the raw price/technical data alongside the LLM output
        result["price"] = tk["price"]
        result["change_1d_pct"] = tk["change_1d_pct"]
        result["change_1w_pct"] = tk["change_1w_pct"]
        result["change_1m_pct"] = tk["change_1m_pct"]
        result["currency"] = tk.get("currency", "")
        return result
    except Exception as e:
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
