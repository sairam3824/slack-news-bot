import os
import json
import requests
import feedparser
import google.generativeai as genai
from apscheduler.schedulers.blocking import BlockingScheduler

# ==========================================
# 1. LOAD CONFIGURATION FROM ENVIRONMENT
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

genai.configure(api_key=GEMINI_API_KEY)

# Define your 2-3 topics and their RSS Feed URLs
TOPICS = {
    "🌐 General Business": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
    "💻 Tech & AI": "https://news.google.com/rss/search?q=artificial+intelligence+tech+business&hl=en-US&gl=US&ceid=US:en",
    "📈 Markets & Economy": "https://news.google.com/rss/search?q=stock+market+economy&hl=en-US&gl=US&ceid=US:en"
}

def fetch_topic_news(feed_url):
    """Fetches top news articles for a specific topic."""
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries[:3]:  # Top 3 per topic
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "summary": entry.get("summary", "")
        })
    return articles

def generate_topic_digest(topic_name, articles):
    """Generates an AI summary for a single topic using Gemini."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    raw_text = ""
    for idx, a in enumerate(articles, 1):
        raw_text += f"{idx}. Title: {a['title']}\n   Link: {a['link']}\n\n"

    prompt = f"""
    You are an executive assistant summarizing news for the topic: {topic_name}.
    Review these news items and produce a crisp, executive summary for Slack.

    Rules:
    - Return 2 key bullet points explaining what happened and why it matters.
    - Format links in Slack style: <URL|Article Title>.
    - Keep it concise and professional.
    
    Articles:
    {raw_text}
    """
    
    response = model.generate_content(prompt)
    return response.text

def run_news_agent():
    """Main job that runs across all topics and posts to Slack."""
    print("⏰ Starting scheduled news run...")
    
    full_slack_message = "🚨 *Daily Multi-Topic Business Digest* 🚨\n\n"
    
    for topic_name, feed_url in TOPICS.items():
        print(f"Fetching topic: {topic_name}...")
        articles = fetch_topic_news(feed_url)
        if articles:
            topic_summary = generate_topic_digest(topic_name, articles)
            full_slack_message += f"### {topic_name}\n{topic_summary}\n\n---\n\n"
    
    # Send all topics in a single clean Slack message
    payload = {"text": full_slack_message}
    response = requests.post(
        SLACK_WEBHOOK_URL, 
        data=json.dumps(payload),
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        print("✅ Posted successfully to Slack!")
    else:
        print(f"❌ Failed to post to Slack: {response.text}")

# ==========================================
# 2. SCHEDULER SETUP (Cloud Runner)
# ==========================================
if __name__ == "__main__":
    print("Bot started! Running first check now...")
    run_news_agent()  # Run immediately on start
    
    scheduler = BlockingScheduler()
    # Schedule to run every day at 8:00 AM UTC (adjust hour as needed)
    scheduler.add_job(run_news_agent, 'cron', hour=8, minute=0)
    
    print("Scheduler activated. Waiting for next run...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass