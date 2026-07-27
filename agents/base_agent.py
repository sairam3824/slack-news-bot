"""
base_agent.py — Shared utilities for all agents.

Provides:
  - Gemini client initialization
  - Model fallback & retry handling (2.5-flash -> 2.0-flash -> 1.5-flash)
  - RSS feed fetching
  - Graceful fallback formatting (no raw 429 error codes in Slack)
  - Gemini text generation (plain + Google Search grounding)
  - Slack message posting
  - BITS Pilani Business Analytics tailored message formatting
"""

import os
import json
import time
import datetime
import requests
import feedparser
from google import genai
from google.genai import types


# ---------------------------------------------------------------------------
# Clients & Config
# ---------------------------------------------------------------------------

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Candidate models in order of preference
MODEL_CANDIDATES = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]

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
    try:
        feed = feedparser.parse(feed_url)
        articles = []
        for entry in feed.entries[:count]:
            articles.append({
                "title": entry.get("title", "No title"),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
            })
        return articles
    except Exception as e:
        print(f"⚠️ RSS fetch error for {feed_url}: {e}")
        return []


def articles_to_text(articles: list[dict]) -> str:
    """Format a list of article dicts into numbered plain text for prompts."""
    lines = []
    for idx, a in enumerate(articles, 1):
        lines.append(f"{idx}. {a['title']}\n   Link: {a['link']}")
    return "\n".join(lines)


def format_fallback_articles(articles: list[dict], title_prefix: str = "Key Updates") -> str:
    """
    Format raw RSS articles cleanly into Slack markdown when AI generation fails.
    Prevents ugly raw API tracebacks (like 429 RESOURCE_EXHAUSTED) in Slack.
    """
    if not articles:
        return "_No articles found at this moment. Please check back later._"

    lines = ["*(AI summary offline due to API rate limits — showing top news below)*\n"]
    seen_links = set()
    for a in articles:
        link = a.get("link", "")
        title = a.get("title", "News Article")
        if not link or link in seen_links:
            continue
        seen_links.add(link)
        lines.append(f"• <{link}|{title}>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Gemini Helpers with Retry & Model Fallback
# ---------------------------------------------------------------------------

def ask_gemini(prompt: str, fallback_articles: list[dict] = None) -> str:
    """
    Call Gemini with multi-model fallback (2.5-flash -> 2.0-flash -> 1.5-flash).
    If all fail, returns a clean Slack-formatted fallback without raw error codes.
    """
    client = get_client()

    for model_id in MODEL_CANDIDATES:
        try:
            print(f"  🤖 Trying Gemini model: {model_id}...")
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"  ⚠️ Model {model_id} failed: {e}")
            time.sleep(1)

    print("❌ All Gemini models failed.")
    return format_fallback_articles(fallback_articles or [])


def ask_gemini_with_search(prompt: str, fallback_articles: list[dict] = None, fallback_query: str = None) -> str:
    """
    Call Gemini with Google Search grounding with multi-model fallback.
    If search grounding fails or is rate-limited, attempts fallback to RSS query or raw links.
    """
    client = get_client()
    google_search_tool = types.Tool(google_search=types.GoogleSearch())

    for model_id in MODEL_CANDIDATES:
        try:
            print(f"  🔍 Trying Search-Grounded Gemini model: {model_id}...")
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[google_search_tool],
                ),
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"  ⚠️ Search-grounded {model_id} failed: {e}")
            time.sleep(1)

    print("❌ Search-grounded Gemini failed completely.")
    if fallback_query:
        rss_url = build_google_news_rss_url(fallback_query)
        fetched = fetch_rss(rss_url, count=6)
        if fetched:
            return format_fallback_articles(fetched)

    return format_fallback_articles(fallback_articles or [])


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

