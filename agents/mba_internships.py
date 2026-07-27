"""
Agent 3: MBA Internship Radar
──────────────────────────────
Covers: Product, analytics, strategy, operations, consulting, digital business internships.

Data sources: Google News RSS + Gemini with Google Search grounding
Posts to:     #mba-internships  (SLACK_WEBHOOK_MBA_INTERNSHIPS)
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

WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_MBA_INTERNSHIPS")

RSS_FEEDS = {
    "MBA Internship News": build_google_news_rss_url(
        "MBA internship India product management analytics strategy consulting 2026"
    ),
}

SEARCH_PROMPT = """You are an MBA internship scout. Search the web for the latest MBA internship
openings in India posted in the last 7 days.

Focus on these domains:
• Product management internships
• Analytics / data strategy internships
• Strategy & consulting internships
• Operations & supply chain internships
• Digital business / e-commerce internships

For each opportunity found, provide:
  - Company name
  - Role title
  - Location (or Remote)
  - Source link (use Slack link format: <URL|Title>)

List 5-8 opportunities. If you cannot find enough recent openings, note that clearly.
Do NOT use markdown headers (no # or ##). Use plain text with bullet points.
"""

DIGEST_PROMPT = """You are an MBA career advisor preparing a morning internship brief.

You will receive two sets of information:
1. Recent news about MBA internship hiring
2. Live internship listings found via web search

Combine them into a single Slack message with these rules:
1. Lead with 2-3 bullets on hiring trends or noteworthy company announcements.
2. Follow with 5-8 actionable internship listings (company, role, link).
3. Use Slack link syntax: <https://example.com|Role at Company>
4. Keep it concise and actionable.
5. Do NOT use markdown headers (no # or ##). Use plain text with bullet points.
"""

# ---------------------------------------------------------------------------
# Agent Logic
# ---------------------------------------------------------------------------


def gather_news() -> str:
    """Fetch internship-related news via RSS."""
    all_articles = []
    for label, url in RSS_FEEDS.items():
        print(f"  📡 Fetching: {label}")
        articles = fetch_rss(url, count=5)
        all_articles.extend(articles)
    return articles_to_text(all_articles) if all_articles else "No recent news found."


def search_live_listings() -> str:
    """Use Gemini + Google Search to find live internship postings."""
    print("  🔍 Searching for live internship listings...")
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
    print("🎓 MBA Internship Radar starting...")
    header = format_header("🎓", "MBA Internship Radar")

    news_text = gather_news()
    search_results = search_live_listings()
    body = generate_digest(news_text, search_results)

    message = f"{header}\n\n{body}"
    post_to_slack(WEBHOOK_URL, message)
    print("🎓 MBA Internship Radar done.\n")
    return message


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run()
