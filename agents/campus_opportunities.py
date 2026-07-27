"""
Agent 6: Campus Opportunities (BITS Pilani - Pilani Campus)
─────────────────────────────────────────────────────────────
Covers: BITS Pilani Campus events, clubs, departmental activities, competitions, talks, deadlines.
Tailored for: BITS Pilani (Pilani Campus) Business Analytics & Management Students.

Data source: Gemini with Google Search grounding
Posts to:    #campus-opportunities  (SLACK_WEBHOOK_CAMPUS_OPPORTUNITIES)
"""

import os
from agents.base_agent import (
    ask_gemini_with_search,
    ask_gemini,
    post_to_slack,
    format_header,
    today_str,
    fetch_rss,
    build_google_news_rss_url,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_CAMPUS_OPPORTUNITIES")

SEARCH_PROMPT = f"""Search the web specifically for upcoming events, student opportunities, and academic/club notices at BITS Pilani (Pilani Campus) around {today_str()}.

Focus areas for BITS Pilani (Pilani Campus):
• Management Association (BITSMAN / Dept of Management events & workshops)
• Technical & Cultural Fests: APOGEE, Oasis, BOSM updates & competition deadlines
• Student Clubs & Societies: DEVS, Consulting Club, Coding/Data Science Club, Finance Club
• Guest Lectures, Industry Talks, Webinars & Workshops on Campus
• Inter-college Hackathons, Case Competitions hosted at BITS Pilani
• Placement Unit (PU) / Practice School (PS) / Internship updates & peer projects

For each item found, provide:
  1. Event / Opportunity Name
  2. Organizing Body (Club, Department, Cell)
  3. Date / Deadline / Venue info
  4. Brief 1-line description
  5. Official or registration link (use Slack format: <URL|Link text>)

List 5-8 relevant events/notices for BITS Pilani students.
Do NOT use markdown headers (no # or ##). Use plain text.
"""

FORMAT_PROMPT = """You are formatting BITS Pilani (Pilani Campus) opportunity listings for Slack.

Take the raw data below and format it as a clean Slack message for Pilani campus students:

1. Number each item.
2. For each, display:
   • *<URL|Event Name>* | _Organizing Body_
     📅 Date/Deadline | Details
3. Use Slack formatting: *bold* for event names, _italic_ for organizers.
4. Add a clean separator `───` between entries.
5. End with: "📌 *BITS Pilani Campus Portal:* <https://www.bits-pilani.ac.in/pilani/|BITS Pilani Website>"
6. Do NOT use markdown headers (no # or ##). Use plain text.

Raw data:
{data}
"""

# ---------------------------------------------------------------------------
# Agent Logic
# ---------------------------------------------------------------------------


def search_campus_events() -> str:
    """Use Gemini + Google Search to discover BITS Pilani campus events."""
    print("  🔍 Searching for BITS Pilani (Pilani Campus) opportunities...")
    fallback_query = "BITS Pilani campus events APOGEE Oasis Department Management 2026"
    rss_fallback = fetch_rss(build_google_news_rss_url("BITS Pilani campus competition workshop 2026"), count=5)

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
    print("🎪 Campus Opportunities Agent starting...")
    header = format_header("🎪", "BITS Pilani (Pilani Campus) Radar")

    raw_results = search_campus_events()
    body = format_for_slack(raw_results)

    message = f"{header}\n\n{body}"
    post_to_slack(WEBHOOK_URL, message)
    print("🎪 Campus Opportunities Agent done.\n")
    return message


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run()
