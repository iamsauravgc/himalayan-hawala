from fastapi import APIRouter, Query
from sqlalchemy import text
from db.engine import engine

router = APIRouter()

@router.get("/live")
def get_live_rate(currency: str = Query("USD", description="Currency code")):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT currency, buy_rate, sell_rate, mid_rate, recorded_at
            FROM exchange_rates
            WHERE currency = :currency
            ORDER BY recorded_at DESC
            LIMIT 1
        """), {"currency": currency})
        row = result.mappings().fetchone()
    return dict(row)

@router.get("/history")
def get_history(currency: str = Query("USD", description="Currency code"), days: int = 90):
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