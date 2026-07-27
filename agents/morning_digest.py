"""
Agent 7: Morning Digest (Action Agent)
────────────────────────────────────────
Aggregates output from all 6 specialist agents, deduplicates, prioritizes,
ranks, and creates a single morning action brief.

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

ACTION_PROMPT = """You are an executive action agent creating a TOP-10 morning brief.

You have received outputs from 6 specialist agents:
1. 🏦 Macro-Economy
2. 📊 Markets & Business
3. 🎓 MBA Internship Radar
4. 📈 Analytics Role Radar
5. 🏆 Unstop Competitions
6. 🎪 BITS Pilani Campus

Your job:

STEP 1 — DEDUPLICATE
Remove any items that appear in multiple agent outputs.

STEP 2 — PRIORITIZE & RANK
Rank the top 10 items by urgency using this priority order:
  P1 (🔴 Act Today):     Deadlines within 48 hours
  P2 (🟡 This Week):     Deadlines within 7 days or breaking news
  P3 (🟢 On Your Radar): Important but no immediate deadline

STEP 3 — FORMAT
Create a Slack message with this structure:

🔴 *ACT TODAY*
• [item] — deadline / action required

🟡 *THIS WEEK*
• [item] — deadline / action required

🟢 *ON YOUR RADAR*
• [item] — why it matters

Use Slack link syntax: <URL|Title>
Keep each item to ONE line.
Do NOT use markdown headers (no # or ##). Use plain text with the emoji + bold pattern above.
Maximum 10 items total across all priority levels.
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
            outputs[label] = f"_(Agent failed: {e})_"
    return outputs


def build_combined_input(outputs: dict[str, str]) -> str:
    """Concatenate all agent outputs into a single text block for Gemini."""
    sections = []
    for label, text in outputs.items():
        sections.append(f"=== {label} ===\n{text}\n")
    return "\n".join(sections)


def generate_action_brief(combined: str) -> str:
    """Use Gemini to deduplicate, prioritize, and rank the top 10 items."""
    prompt = f"{ACTION_PROMPT}\n\n--- AGENT OUTPUTS ---\n{combined}"
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
    header = format_header("☀️", "Morning Action Brief")
    message = f"{header}\n\n{body}"
    post_to_slack(WEBHOOK_URL, message)

    print("☀️  Morning Digest Agent done.\n")
    return message


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run()
