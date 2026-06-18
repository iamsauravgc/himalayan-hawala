from fastapi import APIRouter
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

router = APIRouter()

def get_engine():
    return create_engine(
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )

@router.get("/")
def get_sentiment():
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT headline, source, sentiment, sentiment_score, published_at
            FROM news_sentiment
            ORDER BY published_at DESC
            LIMIT 20
        """))
        rows = result.mappings().fetchall()
    return [dict(r) for r in rows]

@router.get("/summary")
def get_sentiment_summary():
    engine = get_engine()
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