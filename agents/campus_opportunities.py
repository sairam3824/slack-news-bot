"""
Agent 6: Campus Opportunities (BITS Pilani)
────────────────────────────────────────────
Covers: BITS Pilani events, clubs, competitions, talks, deadlines, peer opportunities.

Data source: Gemini with Google Search grounding (no official RSS/API)
Posts to:    #campus-opportunities  (SLACK_WEBHOOK_CAMPUS_OPPORTUNITIES)
"""

import os
from agents.base_agent import (
    ask_gemini_with_search,
    ask_gemini,
    post_to_slack,
    format_header,
    today_str,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_CAMPUS_OPPORTUNITIES")

SEARCH_PROMPT = f"""Search the web for the latest events, opportunities, and activities at
BITS Pilani (Pilani campus) happening in the coming weeks from {today_str()}.

Look across these sources:
• Official BITS Pilani website and social media
• BITS Pilani club pages (technical clubs, cultural clubs, business clubs)
• BITS Pilani fest pages (APOGEE, BOSM, Oasis)
• Unstop listings by BITS Pilani student bodies
• LinkedIn / Instagram posts about BITS Pilani events

Find information about:
• Upcoming campus events, fests, and workshops
• Club recruitment drives and auditions
• Inter-college competitions hosted on campus
• Guest talks, webinars, and seminars
• Application deadlines for campus programs
• Peer opportunities (study groups, project teams, mentorship)

For each opportunity, provide:
  1. Event / opportunity name
  2. Organizing body (club, department, committee)
  3. Date or deadline
  4. Brief description (1 line)
  5. Link (if available)

Find 5-8 items. Prioritize upcoming deadlines.
Do NOT use markdown headers (no # or ##). Use plain text.
"""

FORMAT_PROMPT = """You are formatting campus opportunity listings for Slack.

Take the raw data below and format it as a clean Slack message:

1. Number each item.
2. For each, show:
   *Event Name* | _Organizing Body_
   📅 Date/Deadline | Brief description
   🔗 <URL|Link> (if available)
3. Use Slack formatting: *bold* for event names, _italic_ for organizers.
4. Add a ─── separator between entries.
5. End with: "📌 Stay updated with your campus community!"
6. Do NOT use markdown headers (no # or ##). Use plain text.

Raw data:
{data}
"""

# ---------------------------------------------------------------------------
# Agent Logic
# ---------------------------------------------------------------------------


def search_campus_events() -> str:
    """Use Gemini + Google Search to discover BITS Pilani campus events."""
    print("  🔍 Searching for BITS Pilani campus opportunities...")
    return ask_gemini_with_search(SEARCH_PROMPT)


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
    header = format_header("🎪", "BITS Pilani Campus Radar")

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
