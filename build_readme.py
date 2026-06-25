"""Build a clean research index README from posts.json."""

import json
import re
from pathlib import Path

# Prefer the GitHub-enriched file when present; fall back to the raw parsed
# snapshot so the README can be regenerated even without the enrichment step.
ENRICHED_FILE = Path(__file__).parent / "data" / "posts-github.json"
DATA_FILE = Path(__file__).parent / "data" / "posts.json"
OUT_FILE = Path(__file__).parent / "README.md"


def ts_to_hours(ts: str) -> float:
    """Convert a relative timestamp like '16h', '1d', '2w' to hours.

    Smaller = more recent. Used only for sorting.
    """
    s = ts.strip().lower()
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(\w+)$", s)
    if not m:
        return 1e9
    val = float(m.group(1))
    unit = m.group(2)
    multipliers = {
        "s": 1 / 3600,
        "sec": 1 / 3600,
        "secs": 1 / 3600,
        "second": 1 / 3600,
        "seconds": 1 / 3600,
        "m": 1 / 60,
        "min": 1 / 60,
        "mins": 1 / 60,
        "minute": 1 / 60,
        "minutes": 1 / 60,
        "h": 1,
        "hr": 1,
        "hrs": 1,
        "hour": 1,
        "hours": 1,
        "d": 24,
        "day": 24,
        "days": 24,
        "w": 24 * 7,
        "wk": 24 * 7,
        "wks": 24 * 7,
        "week": 24 * 7,
        "weeks": 24 * 7,
        "mo": 24 * 30,
        "mon": 24 * 30,
        "month": 24 * 30,
        "months": 24 * 30,
        "y": 24 * 365,
        "yr": 24 * 365,
        "year": 24 * 365,
        "years": 24 * 365,
    }
    return val * multipliers.get(unit, 1e9)


def first_line(text: str, max_len: int = 80) -> str:
    """First non-empty line of post text, trimmed and truncated to ~max_len chars."""
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^[#\-\*\•\→\>\d\.\)\s]+", "", line).strip()
        if not line:
            continue
        if len(line) > max_len:
            cut = line[:max_len]
            if " " in cut:
                cut = cut[: cut.rfind(" ")]
            line = cut.rstrip(",;:.") + "…"
        return line
    return "(no title)"


def md_escape(s) -> str:
    """Escape pipe characters and newlines for markdown table cells."""
    if s is None:
        return ""
    return str(s).replace("|", "\\|").replace("\n", " ").strip()


# Category rules: (category_name, [keywords])  — first match wins.
# Order matters: specific ML/data topics are checked BEFORE the broad
# "AI Agents" bucket so that e.g. an RL-training post mentioning "agents"
# lands in ML Research rather than AI Agents.
CATEGORIES = [
    (
        "RAG & Retrieval",
        [
            "rag",
            "retrieval",
            "retriev",
            "embedding",
            "vector db",
            "vector database",
            "faiss",
            "chroma",
            "pinecone",
            "milvus",
            "qdrant",
            "pixelrag",
            "graphrag",
            "lightrag",
            "hyper-rag",
            "kg-gen",
            "knowledge graph",
            "chunk",
            "rerank",
            "reranking",
            "hybrid search",
            "semantic search",
            "retrieval augmented",
        ],
    ),
    (
        "ML Research & Training",
        [
            "rl",
            "reinforcement",
            "training",
            "fine-tun",
            "finetun",
            "lora",
            "qlora",
            "transformer",
            "llm",
            "gpu",
            "benchmark",
            "grpo",
            "ppo",
            "rlhf",
            "dpo",
            "ipo",
            "kto",
            "deepseek",
            "gpt",
            "gemma",
            "llama",
            "mistral",
            "qwen",
            "moe",
            "expert",
            "quantiz",
            "gguf",
            "pretrain",
            "backprop",
            "gradient",
            "checkpoint",
            "distill",
            "alignment",
            "safety",
            "reward",
            "policy gradient",
            "actor-critic",
            "value function",
            "model release",
            "open-weight",
            "open weight",
            "anti-hacking",
            "verifier",
            "long-horizon",
            "vlm",
            "vision-language",
            "multimodal",
            "diffusion",
            "stable diffusion",
            "sft",
            "supervised",
            "unsloth",
            "2-bit",
            "1-bit",
            "packed-sequence",
            "double-buffer",
            "routing",
            "inference",
            "kv cache",
            "attention",
            "context window",
            "context length",
            "spars",
            "pruning",
            "speculative",
            "decoding",
            "tokeniz",
            "tokenizer",
            "awq",
            "gptq",
        ],
    ),
    (
        "Data Science & Analytics",
        [
            "data science",
            "analytics",
            "visualization",
            "pandas",
            "numpy",
            "eda",
            "exploratory",
            "notebook",
            "jupyter",
            "polars",
            "duckdb",
            "causal",
            "bayesian",
            "pymc",
            "statistic",
            "econometr",
            "forecast",
            "time series",
            "timeseries",
            "dashboard",
            "tableau",
            "power bi",
            "matplotlib",
            "seaborn",
            "plotly",
            "streamlit",
            "gradio",
            "marketing mix",
            "adstock",
            "saturation",
            "structural equation",
            "mediation",
            "confound",
            "dag",
            "do-calculus",
            "path analysis",
        ],
    ),
    (
        "AI Agents & Coding Tools",
        [
            "agent",
            "agentic",
            "claude code",
            "cursor",
            "copilot",
            "coder agent",
            "coding agent",
            "mcp",
            "ide",
            "code assistant",
            "dev agent",
            "sub-agent",
            "multi-agent",
            "orchestrator",
            "codex",
            "opencode",
            "openclaw",
            "windsurf",
            "code completion",
            "pair programming",
        ],
    ),
    (
        "Open Source & Tools",
        [
            "open-source",
            "opensource",
            "open source",
            "github",
            "apache",
            "mit license",
            "apache-2.0",
            "stars",
            "self-host",
            "self host",
            "docker",
            "docker compose",
            "kubernetes",
            "k8s",
            "library",
            "package",
            "framework",
            "toolkit",
            "cli",
            "command-line",
            "developer tool",
            "devtool",
            "sdk",
            "api",
            "rest api",
        ],
    ),
    (
        "Career & Learning",
        [
            "career",
            "job",
            "interview",
            "hire",
            "hiring",
            "recruit",
            "resume",
            "cv",
            "portfolio",
            "learn",
            "course",
            "tutorial",
            "book",
            "roadmap",
            "study",
            "lesson",
            "curriculum",
            "bootcamp",
            "workshop",
            "webinar",
            "free course",
            "certification",
            "mentor",
            "skill",
            "upskill",
            "salary",
            "compensation",
            "newsletter",
            "youtube",
            "podcast",
        ],
    ),
    (
        "Infrastructure & DevOps",
        [
            "infrastructure",
            "devops",
            "kubernetes",
            "terraform",
            "ansible",
            "ci/cd",
            "pipeline",
            "deployment",
            "deploy",
            "cloud",
            "aws",
            "azure",
            "gcp",
            "serverless",
            "container",
            "orchestration",
            "monitoring",
            "observability",
            "logging",
            "tracing",
            "prometheus",
            "grafana",
        ],
    ),
]

# Category display order (after categorization). Non-existent cats are skipped.
CAT_ORDER = [c for c, _ in CATEGORIES] + ["Other AI/ML"]


def categorize(text: str) -> str:
    t = text.lower()
    for name, keywords in CATEGORIES:
        for kw in keywords:
            # Use word boundaries for short keywords to avoid false positives
            # (e.g. "ide" matching "guide", "rl" matching "url", "dag"
            # matching "damage"). Longer keywords use substring matching so
            # prefixes like "fine-tun" still match "fine-tuning".
            if len(kw) <= 4:
                if re.search(r"\b" + re.escape(kw) + r"\b", t):
                    return name
            elif kw in t:
                return name
    return "Other AI/ML"


def links_cell(post: dict) -> str:
    url = post.get("postUrl")
    parts = [f"[Post]({url})" if url else "Post"]
    if post.get("linkInComments"):
        parts.append("💬")
    # GitHub repos (extracted from comments). Stable, direct links — unlike
    # lnkd.in which expires in ~24h.
    for repo in post.get("githubRepos", [])[:2]:
        owner_repo = repo["url"].replace("https://github.com/", "")
        parts.append(f"[🐙 {owner_repo}]({repo['url']})")
    # Cap at 2 external links to keep the table readable
    for i, link in enumerate(post.get("externalLinks", [])[:2]):
        parts.append(f"[Link{i + 1}]({link})")
    return " ".join(parts)


def anchor_for(cat: str) -> str:
    raw = cat.lower().replace(" ", "-").replace("&", "").replace("/", "")
    while "--" in raw:
        raw = raw.replace("--", "-")
    return raw.strip("-")


def build():
    # Prefer the GitHub-enriched file when present
    src = ENRICHED_FILE if ENRICHED_FILE.exists() else DATA_FILE
    raw = json.loads(src.read_text(encoding="utf-8"))
    # Enrichment wraps posts in an envelope with metadata; the plain snapshot
    # is a bare array. Normalize to a flat list.
    posts = raw["posts"] if isinstance(raw, dict) and "posts" in raw else raw
    # Sort by recency (smallest hours value = most recent)
    posts_sorted = sorted(posts, key=lambda p: ts_to_hours(p.get("timestamp") or "1y"))

    # Group by category, preserving sort order within each group
    by_cat: dict = {}
    for p in posts_sorted:
        cat = categorize(p.get("text", ""))
        by_cat.setdefault(cat, []).append(p)

    lines = []
    lines.append("# Research & Learning Hub")
    lines.append("")
    lines.append(
        "A curated index of AI, ML, data science, and developer-tooling "
        "posts saved from my feed. Sorted by recency within each category."
    )
    lines.append("")
    lines.append(f"**Total posts:** {len(posts_sorted)}")
    lines.append("")
    lines.append("**By category:**")
    lines.append("")
    for cat in CAT_ORDER:
        if cat in by_cat:
            lines.append(f"- {cat}: {len(by_cat[cat])}")
    lines.append("")
    lines.append("💬 = link shared in the comments of the post.")
    lines.append("")
    lines.append("## Contents")
    lines.append("")
    for cat in CAT_ORDER:
        if cat in by_cat:
            lines.append(f"- [{cat}](#{anchor_for(cat)}) — {len(by_cat[cat])} posts")
    lines.append("")

    for cat in CAT_ORDER:
        if cat not in by_cat:
            continue
        lines.append(f"## {cat}")
        lines.append("")
        lines.append("| # | Title | Author | Saved | Links |")
        lines.append("|---|-------|--------|-------|-------|")
        for i, p in enumerate(by_cat[cat], 1):
            title = md_escape(first_line(p.get("text", "")))
            author = md_escape(p.get("authorName", ""))
            saved = md_escape(p.get("timestamp", ""))
            links = links_cell(p)
            lines.append(f"| {i} | **{title}** | {author} | {saved} | {links} |")
        lines.append("")

    OUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"Wrote {OUT_FILE} with {len(posts_sorted)} posts in {len(by_cat)} categories."
    )
    for cat in CAT_ORDER:
        if cat in by_cat:
            print(f"  {cat}: {len(by_cat[cat])}")


if __name__ == "__main__":
    build()
