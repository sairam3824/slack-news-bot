"""
main.py — Legacy entry point (kept for backward compatibility).

Runs the full Morning Digest agent, which internally runs all 6 specialist agents.
For individual agents, use:  python -m agents.<agent_name>
"""

from agents.morning_digest import run

if __name__ == "__main__":
    run()