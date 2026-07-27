"""
Agent 5: Unstop Competitions
─────────────────────────────
Covers: Case comps, quizzes, hackathons, business contests, brand challenges.

Data source: Gemini with Google Search grounding (Unstop has no public API/RSS)
Posts to:    #unstop-competitions  (SLACK_WEBHOOK_UNSTOP_COMPETITIONS)
"""

import os
from agents.base_agent import (
    ask_gemini_with_search,
    ask_gemini,
    post_to_slack,
    format_header,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_UNSTOP_COMPETITIONS")

SEARCH_PROMPT = """Search the web — specifically unstop.com — for the latest active and upcoming
competitions, hackathons, and challenges for college students in India.

Look for:
• Case study competitions
• Business quizzes
• Hackathons (tech & business)
• Brand challenges & marketing contests
• Consulting case competitions

For EACH opportunity, provide:
  1. Competition name
  2. Organizer / brand
  3. Type (case comp, hackathon, quiz, brand challenge, etc.)
  4. Registration deadline (if available)
  5. Prize pool (if mentioned)
  6. Direct link to the listing on unstop.com

Find 6-10 active competitions. Prioritize those with deadlines in the next 30 days.
Do NOT use markdown headers (no # or ##). Use plain text with numbered list.
"""

FORMAT_PROMPT = """You are formatting competition listings for Slack.

Take the raw competition data below and format it as a clean Slack message:

1. Number each competition.
2. For each, show: *Name* by _Organizer_ | Type | Deadline: date | Prize: amount
   Link: <URL|Apply on Unstop>
3. Use Slack formatting: *bold* for names, _italic_ for organizers.
4. Add a separator line between entries.
5. At the end, add: "🔗 Browse all: <https://unstop.com/competitions|Unstop Competitions>"
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
