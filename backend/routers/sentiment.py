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
from auth import verify_api_key
from slowapi import Limiter
from slowapi.util import get_remote_address

load_dotenv()

log = logging.getLogger("hawala")
router = APIRouter()
last_refresh = {}

limiter = Limiter(key_func=get_remote_address)

@router.get("/")
def get_sentiment(currency: str = Query(default=None), _auth: str = Depends(verify_api_key)):
    if currency:
        currency = validate_currency(currency)
    query = """
        SELECT headline, url, source, sentiment, sentiment_score, currency, published_at, fetched_at
        FROM news_sentiment
        WHERE (:currency IS NULL OR currency = :currency)
        ORDER BY fetched_at DESC LIMIT 20
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"currency": currency})
        rows = result.mappings().fetchall()
    return [dict(r) for r in rows]

@router.post("/refresh")
def refresh_news(
    currency: str = Depends(validate_currency),
    _auth: str = Depends(verify_api_key)
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
        raise HTTPException(status_code=502, detail="Failed to fetch news from external source")

@router.get("/summary")
def get_sentiment_summary(currency: str = Query(default=None), _auth: str = Depends(verify_api_key)):
    if currency:
        currency = validate_currency(currency)
    query = """
        SELECT sentiment, COUNT(*) as count FROM news_sentiment
        WHERE (:currency IS NULL OR currency = :currency)
        GROUP BY sentiment
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"currency": currency})
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