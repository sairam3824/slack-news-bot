"""
base_agent.py — Shared utilities for all agents.

Provides:
  - Gemini client initialization
  - RSS feed fetching
  - Gemini text generation (plain + Google Search grounding)
  - Slack message posting
  - Consistent message formatting
"""

import os
import json
import datetime
import requests
import feedparser
from google import genai
from google.genai import types


# ---------------------------------------------------------------------------
# Clients & Config
# ---------------------------------------------------------------------------

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_ID = "gemini-2.5-flash"

_client = None


def get_client():
    """Lazy-initialize the Gemini client (shared across agents in one process)."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


# ---------------------------------------------------------------------------
# RSS Helpers
# ---------------------------------------------------------------------------

def fetch_rss(feed_url: str, count: int = 5) -> list[dict]:
    """
    Parse an RSS feed and return the top *count* entries.

    Returns a list of dicts: [{title, link, published}, ...]
    """
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries[:count]:
        articles.append({
            "title": entry.get("title", "No title"),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
        })
    return articles


def articles_to_text(articles: list[dict]) -> str:
    """Format a list of article dicts into numbered plain text for prompts."""
    lines = []
    for idx, a in enumerate(articles, 1):
        lines.append(f"{idx}. {a['title']}\n   Link: {a['link']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Gemini Helpers
# ---------------------------------------------------------------------------

def ask_gemini(prompt: str) -> str:
    """Call Gemini 2.5 Flash with a plain text prompt. Returns response text."""
    client = get_client()
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"⚠️  Gemini API error: {e}")
        return f"_(AI summary unavailable: {e})_"


def ask_gemini_with_search(prompt: str) -> str:
    """
    Call Gemini 2.5 Flash with Google Search grounding enabled.
    The model will automatically search the web when needed.
    """
    client = get_client()
    google_search_tool = types.Tool(google_search=types.GoogleSearch())
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[google_search_tool],
            ),
        )
        return response.text
    except Exception as e:
        print(f"⚠️  Gemini Search-Grounded API error: {e}")
        return f"_(AI search unavailable: {e})_"


# ---------------------------------------------------------------------------
# Slack Helpers
# ---------------------------------------------------------------------------

def post_to_slack(webhook_url: str, message: str) -> bool:
    """Post a message to a Slack channel via incoming webhook."""
    if not webhook_url:
        print("❌ No webhook URL provided — skipping Slack post.")
        return False

    payload = {"text": message}
    try:
        resp = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        if resp.status_code == 200:
            print("✅ Posted to Slack successfully.")
            return True
        else:
            print(f"❌ Slack error ({resp.status_code}): {resp.text}")
            return False
    except requests.RequestException as e:
        print(f"❌ Slack request failed: {e}")
        return False


# ---------------------------------------------------------------------------
# Formatting Helpers
# ---------------------------------------------------------------------------

def today_str() -> str:
    """Return today's date as a readable string (e.g. '27 Jul 2026')."""
    return datetime.date.today().strftime("%d %b %Y")


def format_header(emoji: str, title: str) -> str:
    """Build a consistent Slack message header."""
    return f"{emoji} *{title}* — {today_str()}\n{'─' * 40}"


def build_google_news_rss_url(query: str, country: str = "IN", lang: str = "en") -> str:
    """
    Build a Google News RSS search URL.

    Args:
        query:   Search terms (spaces will be URL-encoded).
        country: Country code (default IN for India).
        lang:    Language code (default en).
    """
    encoded = requests.utils.quote(query)
    return (
        f"https://news.google.com/rss/search?"
        f"q={encoded}&hl={lang}-{country}&gl={country}&ceid={country}:{lang}"
    )
