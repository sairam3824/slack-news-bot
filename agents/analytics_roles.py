"""
Agent 4: Analytics Role Radar
──────────────────────────────
Covers: Data analyst, BI, business analyst, growth, PM intern, revenue ops roles.
Tailored for: BITS Pilani Business Analytics Students.

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
    "Analytics Hiring Trends": build_google_news_rss_url(
        "data analyst business analyst hiring India tech business intelligence 2026"
    ),
}

SEARCH_PROMPT = """You are a specialized talent scout for Business Analytics & Data roles in India.
Search the web for active open roles posted in the last 14 days suitable for entry-level / early career Business Analytics grads.

Target Roles:
• Data Analyst (Junior / Trainee / Intern)
• Business Analyst (BA)
• Business Intelligence (BI) Analyst / Developer
• Product Analyst / Growth Analyst
• Revenue Operations (RevOps) Analyst
• Associate Data Scientist / Decision Science Analyst

For each role found, provide:
  - Role Title & Company
  - Core Skillset (SQL, Python, PowerBI/Tableau, Machine Learning, Excel)
  - Location (India / Hybrid / Remote)
  - Direct Application Link (use Slack link format: <URL|Role at Company>)

List 5-8 verified opportunities. Keep descriptions to 1 line per entry.
Do NOT use markdown headers (no # or ##). Use plain text with bullet points.
"""

DIGEST_PROMPT = """You are an analytics career strategist preparing a daily roles briefing for BITS Pilani Business Analytics students.

Combine the news and live job listings below into a structured Slack message:

1. Lead with 2 bullet points on demand trends in data analytics, AI tools, or top hiring industries in India.
2. Follow with 5-8 actionable job openings with direct application links.
3. Format each listing cleanly: • <URL|Role Title at Company> — Key Skills | Location
4. Use Slack link syntax strictly: <https://example.com|Text>
5. Keep it concise, professional, and actionable.
6. Do NOT use markdown headers (no # or ##). Use plain text with bullet points.
"""

# ---------------------------------------------------------------------------
# Agent Logic
# ---------------------------------------------------------------------------


def gather_news() -> tuple[str, list[dict]]:
    """Fetch analytics hiring news via RSS."""
    all_articles = []
    for label, url in RSS_FEEDS.items():
        print(f"  📡 Fetching: {label}")
        articles = fetch_rss(url, count=5)
        all_articles.extend(articles)
    text = articles_to_text(all_articles) if all_articles else "No recent news found."
    return text, all_articles


def search_live_listings(fallback_articles: list[dict]) -> str:
    """Use Gemini + Google Search to find live analytics role postings."""
    print("  🔍 Searching for live analytics & business analyst roles...")
    fallback_query = "data analyst business analyst hiring India 2026 apply"
    return ask_gemini_with_search(
        SEARCH_PROMPT,
        fallback_articles=fallback_articles,
        fallback_query=fallback_query
    )


def generate_digest(news_text: str, search_results: str, fallback_articles: list[dict]) -> str:
    """Merge news + live listings into a single digest via Gemini."""
    combined_prompt = (
        f"{DIGEST_PROMPT}\n\n"
        f"--- ANALYTICS INDUSTRY NEWS ---\n{news_text}\n\n"
        f"--- LIVE ROLE LISTINGS ---\n{search_results}"
    )
    return ask_gemini(combined_prompt, fallback_articles=fallback_articles)


def run() -> str:
    """
    Main entry point.

    Returns the generated summary text (useful for the Morning Digest agent).
    """
    print("📈 Analytics Role Radar starting...")
    header = format_header("📈", "Analytics Role Radar")

    news_text, articles = gather_news()
    search_results = search_live_listings(articles)
    body = generate_digest(news_text, search_results, articles)

    message = f"{header}\n\n{body}"
    post_to_slack(WEBHOOK_URL, message)
    print("📈 Analytics Role Radar done.\n")
    return message


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run()
