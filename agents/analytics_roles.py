"""
Agent 4: Analytics Role Radar
──────────────────────────────
Covers: Data analyst, BI, business analyst, growth, PM intern, revenue ops roles.

Data sources: Google News RSS + Gemini with Google Search grounding
Posts to:     #analytics-roles  (SLACK_WEBHOOK_ANALYTICS_ROLES)
"""

import os
from agents.base_agent import (
    fetch_rss,
    articles_to_text,
    ask_gemini,
    ask_gemini_with_search,
    post_to_slack,
    format_header,
    build_google_news_rss_url,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_ANALYTICS_ROLES")

RSS_FEEDS = {
    "Analytics Hiring News": build_google_news_rss_url(
        "data analyst business analyst hiring India internship 2026"
    ),
}

SEARCH_PROMPT = """You are a job scout specializing in analytics and data roles.
Search the web for the latest openings in India posted in the last 7 days.

Focus on these roles:
• Data Analyst (intern or entry-level)
• Business Intelligence (BI) Analyst
• Business Analyst
• Growth Analyst / Growth PM
• PM Intern / Associate Product Manager
• Revenue Operations Analyst

For each role found, provide:
  - Company name
  - Role title
  - Location (or Remote)
  - Source link (use Slack link format: <URL|Title>)

List 5-8 openings. If you cannot find enough recent openings, note that clearly.
Do NOT use markdown headers (no # or ##). Use plain text with bullet points.
"""

DIGEST_PROMPT = """You are a career advisor preparing an analytics-roles morning brief.

You will receive two sets of information:
1. Recent news about analytics/data hiring
2. Live role listings found via web search

Combine them into a single Slack message:
1. Lead with 2-3 bullets on analytics hiring trends.
2. Follow with 5-8 actionable role listings (company, role, link).
3. Use Slack link syntax: <https://example.com|Role at Company>
4. Keep it concise and actionable.
5. Do NOT use markdown headers (no # or ##). Use plain text with bullet points.
"""

# ---------------------------------------------------------------------------
# Agent Logic
# ---------------------------------------------------------------------------


def gather_news() -> str:
    """Fetch analytics hiring news via RSS."""
    all_articles = []
    for label, url in RSS_FEEDS.items():
        print(f"  📡 Fetching: {label}")
        articles = fetch_rss(url, count=5)
        all_articles.extend(articles)
    return articles_to_text(all_articles) if all_articles else "No recent news found."


def search_live_listings() -> str:
    """Use Gemini + Google Search to find live analytics role postings."""
    print("  🔍 Searching for live analytics roles...")
    return ask_gemini_with_search(SEARCH_PROMPT)


def generate_digest(news_text: str, search_results: str) -> str:
    """Merge news + live listings into a single digest via Gemini."""
    combined_prompt = (
        f"{DIGEST_PROMPT}\n\n"
        f"--- NEWS ---\n{news_text}\n\n"
        f"--- LIVE LISTINGS ---\n{search_results}"
    )
    return ask_gemini(combined_prompt)


def run() -> str:
    """
    Main entry point.

    Returns the generated summary text (useful for the Morning Digest agent).
    """
    print("📈 Analytics Role Radar starting...")
    header = format_header("📈", "Analytics Role Radar")

    news_text = gather_news()
    search_results = search_live_listings()
    body = generate_digest(news_text, search_results)

    message = f"{header}\n\n{body}"
    post_to_slack(WEBHOOK_URL, message)
    print("📈 Analytics Role Radar done.\n")
    return message


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run()
