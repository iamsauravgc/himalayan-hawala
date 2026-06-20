from fastapi import APIRouter, Query, Depends
from sqlalchemy import text
from db.engine import engine
from utils import validate_currency

router = APIRouter()

@router.get("/")
def get_predictions(currency: str = Depends(validate_currency)):
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
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT currency FROM rate_predictions
            WHERE currency != 'INR'
            ORDER BY currency
        """))
        rows = result.mappings().fetchall()
    return [r['currency'] for r in rows]