import os
import json
import requests
import feedparser
from google import genai

# Load environment variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

# Initialize the modern Google GenAI Client
client = genai.Client(api_key=GEMINI_API_KEY)

TOPICS = {
    "🌐 General Business": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
    "💻 Tech & AI": "https://news.google.com/rss/search?q=artificial+intelligence+tech+business&hl=en-US&gl=US&ceid=US:en",
    "📈 Markets & Economy": "https://news.google.com/rss/search?q=stock+market+economy&hl=en-US&gl=US&ceid=US:en"
}

def fetch_topic_news(feed_url):
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries[:3]:
        articles.append({
            "title": entry.title,
            "link": entry.link
        })
    return articles

def generate_topic_digest(topic_name, articles):
    raw_text = ""
    for idx, a in enumerate(articles, 1):
        raw_text += f"{idx}. Title: {a['title']}\n   Link: {a['link']}\n\n"

    prompt = f"""
    You are an executive assistant summarizing news for the topic: {topic_name}.
    Review these news items and produce a crisp executive summary for Slack.

    Rules:
    - Return 2 bullet points explaining key updates.
    - Format links in Slack style: <URL|Article Title>.
    - Keep it concise and professional.
    
    Articles:
    {raw_text}
    """
    
    try:
        # Use the updated standard model for free tier
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"⚠️ Gemini API Error for {topic_name}: {e}")
        # Fallback: Output raw headlines if AI fails
        fallback_text = "*(AI Summary unavailable, raw headlines below)*\n"
        for a in articles:
            fallback_text += f"• <{a['link']}|{a['title']}>\n"
        return fallback_text

def run_news_agent():
    print("Starting news generation...")
    full_slack_message = "🚨 *Daily Multi-Topic Business Digest* 🚨\n\n"
    
    for topic_name, feed_url in TOPICS.items():
        print(f"Fetching: {topic_name}...")
        articles = fetch_topic_news(feed_url)
        if articles:
            topic_summary = generate_topic_digest(topic_name, articles)
            full_slack_message += f"### {topic_name}\n{topic_summary}\n\n---\n\n"
    
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

if __name__ == "__main__":
    run_news_agent()