"""
Agent 3: MBA Internship Radar
──────────────────────────────
Covers: Product, analytics, strategy, operations, consulting, digital business internships.
Tailored for: BITS Pilani Business Analytics & Management Students.

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
    "MBA Hiring Trends": build_google_news_rss_url(
        "MBA Business Analytics internship India product manager strategy consulting hiring 2026"
    ),
}

SEARCH_PROMPT = """You are a career advisor specialized in Business Analytics and MBA internships in India.
Search the web for active, recent summer and off-campus internship opportunities posted in the last 14 days.

Target Domains:
• Product Management (PM) / Associate Product Manager (APM) Intern
• Business Analytics / Data Strategy Intern
• Management Consulting / Strategy Intern
• Operations / Supply Chain / Revenue Ops Intern
• Digital Business / E-Commerce Intern

For each opportunity found, provide:
  - Role Title & Company Name
  - Domain / Function
  - Location (or Remote)
  - Direct Application Link (use Slack link format: <URL|Role at Company>)

List 5-8 verified opportunities. Keep descriptions to 1 concise line per listing.
Do NOT use markdown headers (no # or ##). Use plain text with bullet points.
"""

DIGEST_PROMPT = """You are an MBA career advisor preparing a daily internship brief for BITS Pilani Business Analytics students.

Combine the hiring news and live listings below into a crisp Slack message:

1. Lead with 2 bullet points on current MBA/Analytics internship hiring trends or corporate hiring announcements.
2. Follow with 5-8 actionable internship listings with direct links.
3. Format each listing cleanly: • <URL|Role Title at Company> — Domain | Location | Details
4. Use Slack link syntax strictly: <https://example.com|Text>
5. Keep it concise, high-value, and actionable.
6. Do NOT use markdown headers (no # or ##). Use plain text with bullet points.
"""

# ---------------------------------------------------------------------------
# Agent Logic
# ---------------------------------------------------------------------------


def gather_news() -> tuple[str, list[dict]]:
    """Fetch internship-related news via RSS."""
    all_articles = []
    for label, url in RSS_FEEDS.items():
        print(f"  📡 Fetching: {label}")
        articles = fetch_rss(url, count=5)
        all_articles.extend(articles)
    text = articles_to_text(all_articles) if all_articles else "No recent news found."
    return text, all_articles


def search_live_listings(fallback_articles: list[dict]) -> str:
    """Use Gemini + Google Search to find live internship postings."""
    print("  🔍 Searching for live MBA & Analytics internship listings...")
    fallback_query = "MBA Business Analytics internship India 2026 apply"
    return ask_gemini_with_search(
        SEARCH_PROMPT,
        fallback_articles=fallback_articles,
        fallback_query=fallback_query
    )


def generate_digest(news_text: str, search_results: str, fallback_articles: list[dict]) -> str:
    """Merge news + live listings into a single digest via Gemini."""
    combined_prompt = (
        f"{DIGEST_PROMPT}\n\n"
        f"--- HIRING NEWS ---\n{news_text}\n\n"
        f"--- LIVE INTERNSHIP LISTINGS ---\n{search_results}"
    )
    return ask_gemini(combined_prompt, fallback_articles=fallback_articles)


def run() -> str:
    """
    Main entry point.

    Returns the generated summary text (useful for the Morning Digest agent).
    """
    print("🎓 MBA Internship Radar starting...")
    header = format_header("🎓", "MBA & Analytics Internship Radar")

    news_text, articles = gather_news()
    search_results = search_live_listings(articles)
    body = generate_digest(news_text, search_results, articles)

    message = f"{header}\n\n{body}"
    post_to_slack(WEBHOOK_URL, message)
    print("🎓 MBA Internship Radar done.\n")
    return message


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run()
