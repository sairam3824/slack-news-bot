"""
Agent 1: Macro-Economy
──────────────────────
Covers: India economy, RBI, inflation, policy, global macro, oil, employment, trade.

Data sources: Google News RSS feeds
Posts to:     #macro-economy  (SLACK_WEBHOOK_MACRO_ECONOMY)
"""

import os
from agents.base_agent import (
    fetch_rss,
    articles_to_text,
    ask_gemini,
    post_to_slack,
    format_header,
    build_google_news_rss_url,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_MACRO_ECONOMY")

RSS_FEEDS = {
    "India Economy & Policy": build_google_news_rss_url(
        "India economy RBI inflation monetary policy"
    ),
    "Global Macro & Trade": build_google_news_rss_url(
        "global macro oil prices trade employment India"
    ),
}

SYSTEM_PROMPT = """You are a macro-economy analyst preparing a morning brief for an MBA student.

You will receive recent news articles. Produce a Slack-formatted summary with these rules:

1. Write 4-5 bullet points covering the most important updates across:
   • RBI / monetary policy / interest rates
   • Inflation & consumer prices
   • Oil prices, trade & geopolitics
   • Employment & labour market
   • Global macro impact on India

2. Format each bullet as:  • <URL|Headline> — one-line insight.
3. Use Slack link syntax: <https://example.com|Click here>
4. Keep it concise, analytical, and professional.
5. Do NOT use markdown headers (no # or ##). Use plain text with bullet points.
"""

# ---------------------------------------------------------------------------
# Agent Logic
# ---------------------------------------------------------------------------


def gather_articles() -> list[dict]:
    """Fetch articles from all configured RSS feeds."""
    all_articles = []
    for label, url in RSS_FEEDS.items():
        print(f"  📡 Fetching: {label}")
        articles = fetch_rss(url, count=5)
        all_articles.extend(articles)
    return all_articles


def generate_summary(articles: list[dict]) -> str:
    """Use Gemini to produce a macro-economy digest from raw articles."""
    raw = articles_to_text(articles)
    prompt = f"{SYSTEM_PROMPT}\n\nArticles:\n{raw}"
    return ask_gemini(prompt)


def run() -> str:
    """
    Main entry point.

    Returns the generated summary text (useful for the Morning Digest agent).
    """
    print("🏦 Macro-Economy Agent starting...")
    header = format_header("🏦", "Macro-Economy Digest")

    articles = gather_articles()
    if not articles:
        body = "_No articles found today._"
    else:
        body = generate_summary(articles)

    message = f"{header}\n\n{body}"
    post_to_slack(WEBHOOK_URL, message)
    print("🏦 Macro-Economy Agent done.\n")
    return message


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run()
