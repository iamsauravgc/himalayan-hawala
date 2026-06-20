import logging
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from db.engine import engine
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("hawala")
router = APIRouter()
last_refresh = None

@router.get("/")
def get_sentiment():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT headline, url, source, sentiment, sentiment_score, published_at
            FROM news_sentiment
            ORDER BY published_at DESC
            LIMIT 20
        """))
        rows = result.mappings().fetchall()
    return [dict(r) for r in rows]

@router.post("/refresh")
def refresh_news():
    global last_refresh
    now = datetime.now()
    if last_refresh and now - last_refresh < timedelta(seconds=60):
        raise HTTPException(status_code=429, detail="Please wait 60 seconds between refreshes")
    from scripts.fetch_news import fetch_articles, store_articles
    articles = fetch_articles()
    store_articles(articles)
    last_refresh = now
    log.info("News refresh completed: %d articles stored", len(articles))
    return {"status": "refreshed", "count": len(articles)}

@router.get("/summary")
def get_sentiment_summary():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT sentiment, COUNT(*) as count
            FROM news_sentiment
            GROUP BY sentiment
        """))
        rows = result.mappings().fetchall()
    
    total = sum(r['count'] for r in rows)
    summary = {r['sentiment']: r['count'] for r in rows}
    
    positive = summary.get('positive', 0)
    negative = summary.get('negative', 0)
    
    if positive > negative:
        signal = "BULLISH"
        explanation = "More positive financial news — NPR may strengthen."
    elif negative > positive:
        signal = "BEARISH"
        explanation = "More negative financial news — NPR may weaken."
    else:
        signal = "NEUTRAL"
        explanation = "Mixed signals — rate likely stable."

    return {
        "total": total,
        "breakdown": summary,
        "signal": signal,
        "explanation": explanation
    }