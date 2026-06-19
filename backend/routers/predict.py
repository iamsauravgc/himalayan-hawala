from fastapi import APIRouter, Query
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
def get_predictions(currency: str = Query("USD", description="Currency code")):
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT currency, predicted_for, predicted_rate, confidence_low, confidence_high
            FROM rate_predictions
            WHERE currency = :currency
            ORDER BY predicted_for ASC
        """), {"currency": currency})
        rows = result.mappings().fetchall()
    return [dict(r) for r in rows]

@router.get("/currencies")
def list_prediction_currencies():
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT currency FROM rate_predictions ORDER BY currency
        """))
        rows = result.mappings().fetchall()
    return [r['currency'] for r in rows]