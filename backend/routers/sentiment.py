import logging
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import text
from db.engine import engine
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from utils import validate_currency
from slowapi import Limiter
from slowapi.util import get_remote_address

load_dotenv()

log = logging.getLogger("hawala")
router = APIRouter()
last_refresh = {}

limiter = Limiter(key_func=get_remote_address)

@router.get("/")
def get_sentiment(currency: str = Query(default=None)):
    query = """
        SELECT headline, url, source, sentiment, sentiment_score, currency, published_at, fetched_at
        FROM news_sentiment
    """
    params = {}
    if currency:
        currency = validate_currency(currency)
        query += " WHERE currency = :currency"
        params["currency"] = currency
    query += " ORDER BY fetched_at DESC LIMIT 20"

    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        rows = result.mappings().fetchall()
    return [dict(r) for r in rows]

@router.post("/refresh")
def refresh_news(
    currency: str = Depends(validate_currency)
):
    global last_refresh
    now = datetime.now()
    if currency in last_refresh and now - last_refresh[currency] < timedelta(seconds=60):
        raise HTTPException(status_code=429, detail="Please wait 60 seconds between refreshes")
    from scripts.fetch_news import fetch_articles, store_articles
    try:
        articles = fetch_articles()
        store_articles(articles, currency)
        last_refresh[currency] = now
        log.info("News refresh completed: %d articles stored", len(articles))
        return {"status": "refreshed", "count": len(articles), "currency": currency}
    except Exception as e:
        log.error("News refresh failed: %s", str(e))
        raise HTTPException(status_code=502, detail=f"Failed to fetch news: {str(e)}")

@router.get("/summary")
def get_sentiment_summary(currency: str = Query(default=None)):
    query = "SELECT sentiment, COUNT(*) as count FROM news_sentiment"
    params = {}
    if currency:
        currency = validate_currency(currency)
        query += " WHERE currency = :currency"
        params["currency"] = currency
    query += " GROUP BY sentiment"

    with engine.connect() as conn:
        result = conn.execute(text(query), params)
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
        "currency": currency,
        "breakdown": summary,
        "signal": signal,
        "explanation": explanation
    }