"""
Agent 5: Unstop Competitions
─────────────────────────────
Covers: Case comps, business analytics hackathons, quizzes, brand challenges on Unstop.
Tailored for: BITS Pilani Business Analytics & Management Students.

Data source: Gemini with Google Search grounding (Unstop search)
Posts to:    #unstop-competitions  (SLACK_WEBHOOK_UNSTOP_COMPETITIONS)
"""

import os
from agents.base_agent import (
    ask_gemini_with_search,
    ask_gemini,
    post_to_slack,
    format_header,
    fetch_rss,
    build_google_news_rss_url,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_UNSTOP_COMPETITIONS")

SEARCH_PROMPT = """Search the web — specifically unstop.com — for the latest active and upcoming
competitions, hackathons, case challenges, and corporate contests in India suitable for business analytics and MBA/engineering students.

Target Categories:
• Corporate Case Competitions (e.g. Tata, Reliance, Mahindra, L'Oreal, Flipkart, TVS, Hero)
• Business Analytics & Data Science Hackathons
• Strategy & Management Quizzes
• Brand Challenges & Product Design Contests

For EACH opportunity found, provide:
  1. Competition Name
  2. Organizer / Corporate Brand
  3. Category (Case Comp, Analytics Hackathon, Business Quiz, Brand Challenge)
  4. Registration Deadline & Prize Pool
  5. Direct Application Link on unstop.com (use format: <URL|Apply on Unstop>)

List 6-8 active competitions with upcoming deadlines.
Do NOT use markdown headers (no # or ##). Use plain text.
"""

FORMAT_PROMPT = """You are formatting competition listings for Slack for BITS Pilani students.

Take the raw competition data below and produce a clean, structured Slack message:

1. Number each competition.
2. For each, display:
   • *<URL|Competition Name>* by _Organizer_ | Category
     🏆 Prize & Deadline info
3. Use Slack markdown syntax: *bold* for names, _italic_ for organizers.
4. Add a clean separator `───` between entries.
5. End with: "🔗 *Explore all competitions:* <https://unstop.com/competitions|Unstop Portal>"
6. Do NOT use markdown headers (no # or ##). Use plain text.

Raw data:
{data}
"""

# ---------------------------------------------------------------------------
# Agent Logic
# ---------------------------------------------------------------------------


def search_competitions() -> str:
    """Use Gemini + Google Search to discover active Unstop competitions."""
    print("  🔍 Searching Unstop for active competitions...")
    fallback_query = "Unstop case competition analytics hackathon 2026 apply"
    rss_fallback = fetch_rss(build_google_news_rss_url("Unstop competition case challenge India 2026"), count=5)
    
    return ask_gemini_with_search(
        SEARCH_PROMPT,
        fallback_articles=rss_fallback,
        fallback_query=fallback_query
    )


def format_for_slack(raw_data: str) -> str:
    """Re-format raw search results into clean Slack message."""
    prompt = FORMAT_PROMPT.format(data=raw_data)
    return ask_gemini(prompt)


def run() -> str:
    """
    Main entry point.

    Returns the generated summary text (useful for the Morning Digest agent).
    """
    print("🏆 Unstop Competitions Agent starting...")
    header = format_header("🏆", "Unstop Competitions Radar")

    raw_results = search_competitions()
    body = format_for_slack(raw_results)

    message = f"{header}\n\n{body}"
    post_to_slack(WEBHOOK_URL, message)
    print("🏆 Unstop Competitions Agent done.\n")
    return message


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run()
