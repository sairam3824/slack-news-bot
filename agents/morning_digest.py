"""
Agent 7: Morning Digest (Action Agent)
────────────────────────────────────────
Aggregates output from all 6 specialist agents, deduplicates, prioritizes,
ranks, and creates a single morning action brief tailored for BITS Pilani Business Analytics students.

Posts to: #morning-digest  (SLACK_WEBHOOK_MORNING_DIGEST)
"""

import os
from agents.base_agent import ask_gemini, post_to_slack, format_header

# Import all specialist agents
from agents import macro_economy
from agents import markets_business
from agents import mba_internships
from agents import analytics_roles
from agents import unstop_competitions
from agents import campus_opportunities

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_MORNING_DIGEST")

ACTION_PROMPT = """You are an executive career & intelligence strategist creating a TOP-10 Morning Action Brief for a BITS Pilani Business Analytics student.

You will receive the aggregated outputs from 6 specialist agents:
1. 🏦 Macro-Economy
2. 📊 Markets & Business
3. 🎓 MBA & Analytics Internships
4. 📈 Analytics Role Radar
5. 🏆 Unstop Competitions
6. 🎪 BITS Pilani (Pilani Campus) Opportunities

Your Job:

STEP 1 — DEDUPLICATE
Filter out any duplicate news items or repeated internship/competition listings.

STEP 2 — PRIORITIZE & RANK (TOP 10 ITEMS TOTAL)
Categorize items by actionability and urgency into 3 priority buckets:

  🔴 *ACT TODAY (Urgent < 48 hrs)* — Imminent application deadlines for internships/competitions or critical breaking events.
  🟡 *THIS WEEK (High Priority)* — Key job openings, upcoming case comps, and major tech/business industry shifts.
  🟢 *ON YOUR RADAR (Strategic Context)* — Essential macroeconomic signals, sector trends, or BITS campus announcements.

STEP 3 — FORMAT FOR SLACK
• Use Slack link syntax strictly: <https://example.com|Headline or Role Title>
• Keep each bullet point to ONE clear, high-density line.
• Do NOT use markdown headers (no # or ##). Use plain text with the emoji headers above.
• Include up to 10 bullet points maximum across all buckets combined.
"""

# ---------------------------------------------------------------------------
# Agent Registry
# ---------------------------------------------------------------------------

AGENTS = [
    ("🏦 Macro-Economy", macro_economy),
    ("📊 Markets & Business", markets_business),
    ("🎓 MBA Internships", mba_internships),
    ("📈 Analytics Roles", analytics_roles),
    ("🏆 Unstop Competitions", unstop_competitions),
    ("🎪 Campus Opportunities", campus_opportunities),
]

# ---------------------------------------------------------------------------
# Agent Logic
# ---------------------------------------------------------------------------


def collect_all_outputs() -> dict[str, str]:
    """
    Run all 6 specialist agents and collect their output.

    Returns a dict mapping agent label → generated message.
    """
    outputs = {}
    for label, agent_module in AGENTS:
        print(f"▶ Running {label}...")
        try:
            result = agent_module.run()
            outputs[label] = result
        except Exception as e:
            print(f"  ⚠️  {label} failed: {e}")
            outputs[label] = f"_(Agent update currently offline)_"
    return outputs


def build_combined_input(outputs: dict[str, str]) -> str:
    """Concatenate all agent outputs into a single text block for Gemini."""
    sections = []
    for label, text in outputs.items():
        sections.append(f"=== {label} ===\n{text}\n")
    return "\n".join(sections)


def generate_action_brief(combined: str) -> str:
    """Use Gemini to deduplicate, prioritize, and rank the top 10 items."""
    prompt = f"{ACTION_PROMPT}\n\n--- SPECIALIST AGENT OUTPUTS ---\n{combined}"
    return ask_gemini(prompt)


def run() -> str:
    """
    Main entry point for the Morning Digest.

    1. Runs all 6 specialist agents
    2. Collects their outputs
    3. Deduplicates & ranks via Gemini
    4. Posts the final action brief to #morning-digest
    """
    print("☀️  Morning Digest Agent starting...")
    print("=" * 50)

    # Step 1: Collect outputs from all agents
    outputs = collect_all_outputs()

    print("=" * 50)
    print("☀️  All agents complete. Building action brief...")

    # Step 2: Combine and generate ranked brief
    combined = build_combined_input(outputs)
    body = generate_action_brief(combined)

    # Step 3: Post to Slack
    header = format_header("☀️", "BITS Pilani Morning Action Brief")
    message = f"{header}\n\n{body}"
    post_to_slack(WEBHOOK_URL, message)

    print("☀️  Morning Digest Agent done.\n")
    return message


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run()
