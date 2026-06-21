import sys
import os
import time
import requests
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from db.connection import get_connection
from dotenv import load_dotenv

load_dotenv()

EVERYTHING_QUERY = "Nepal rupee exchange rate OR Nepali remittance NPR OR USD NPR forecast OR Federal Reserve interest rate Asia OR emerging market currency forex OR Nepal economy trade deficit"


def fetch_articles():
    articles = []
    api_key = os.getenv("NEWS_API_KEY")

    r = requests.get(
        "https://newsapi.org/v2/everything",
        params={
            "q": EVERYTHING_QUERY,
            "language": "en",
            "pageSize": 10,
            "sortBy": "publishedAt",
            "apiKey": api_key
        }
    )
    r.raise_for_status()
    data = r.json()
    if data.get("status") == "ok":
        articles += data.get("articles", [])
        print(f"  everything -> {len(data.get('articles', []))} articles")

    time.sleep(1)

    r = requests.get(
        "https://newsapi.org/v2/top-headlines",
        params={
            "country": "us",
            "category": "business",
            "pageSize": 5,
            "apiKey": api_key
        }
    )
    r.raise_for_status()
    data = r.json()
    if data.get("status") == "ok":
        articles += data.get("articles", [])
        print(f"  top-headlines -> {len(data.get('articles', []))} articles")

    seen = set()
    unique = []
    for a in articles:
        t = a.get('title', '')
        if t and t not in seen and t != "[Removed]":
            seen.add(t)
            unique.append(a)

    print(f"Total unique articles: {len(unique)}")
    return unique

def run_finbert(headline):
    api_key = os.getenv("HF_API_KEY")
    r = requests.post(
        "https://router.huggingface.co/hf-inference/models/ProsusAI/finbert",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"inputs": headline}
    )
    r.raise_for_status()
    result = r.json()
    if isinstance(result, list) and len(result) > 0:
        scores = result[0]
        best = max(scores, key=lambda x: x['score'])
        return best['label'], round(best['score'], 4)
    return "neutral", 0.5

def store_articles(articles, currency='USD'):
    conn = get_connection()
    cur = conn.cursor()
    count = 0

    for a in articles:
        headline = a.get("title", "")
        url = a.get("url", "")
        source = a.get("source", {}).get("name", "")
        published_at = a.get("publishedAt")

        if not headline:
            continue

        print(f"Running FinBERT: {headline[:60].encode('ascii', 'replace').decode()}...")
        sentiment, score = run_finbert(headline)
        print(f"  -> {sentiment} ({score})")

        cur.execute("""
            INSERT INTO news_sentiment (headline, url, source, sentiment, sentiment_score, currency, published_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (headline) DO UPDATE
            SET sentiment = EXCLUDED.sentiment,
                sentiment_score = EXCLUDED.sentiment_score,
                url = EXCLUDED.url,
                source = EXCLUDED.source,
                currency = EXCLUDED.currency,
                fetched_at = NOW()
        """, (headline, url, source, sentiment, score, currency, published_at))
        count += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"\nStored {count} articles with sentiment.")

if __name__ == "__main__":
    import sys
    currency = sys.argv[1] if len(sys.argv) > 1 else 'USD'
    articles = fetch_articles()
    store_articles(articles, currency)
