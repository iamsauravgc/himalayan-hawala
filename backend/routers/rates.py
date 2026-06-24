from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy import text
from db.engine import engine
from utils import validate_currency

router = APIRouter()

@router.get("/live")
def get_live_rate(currency: str = Depends(validate_currency)):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT currency, buy_rate, sell_rate, mid_rate, recorded_at
            FROM exchange_rates
            WHERE currency = :currency
            ORDER BY recorded_at DESC
            LIMIT 1
        """), {"currency": currency})
        row = result.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"No rate data found for {currency}")
    return dict(row)

@router.get("/history")
def get_history(currency: str = Depends(validate_currency), days: int = Query(90, ge=1, le=365)):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT currency, mid_rate, recorded_at
            FROM exchange_rates
            WHERE currency = :currency
            AND recorded_at >= CURRENT_DATE - make_interval(days => :days)
            ORDER BY recorded_at ASC
        """), {"currency": currency, "days": days})
        rows = result.mappings().fetchall()
    return [dict(r) for r in rows]

@router.get("/currencies")
def list_currencies():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT currency FROM exchange_rates
            WHERE currency != 'INR'
            ORDER BY currency
        """))
        rows = result.mappings().fetchall()
    return [r['currency'] for r in rows]