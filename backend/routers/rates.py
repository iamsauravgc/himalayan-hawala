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

@router.get("/live")
def get_live_rate():
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT currency, buy_rate, sell_rate, mid_rate, recorded_at
            FROM exchange_rates
            WHERE currency = 'USD'
            ORDER BY recorded_at DESC
            LIMIT 1
        """))
        row = result.mappings().fetchone()
    return dict(row)

@router.get("/history")
def get_history(days: int = 90):
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT currency, mid_rate, recorded_at
            FROM exchange_rates
            WHERE currency = 'USD'
            AND recorded_at >= NOW() - INTERVAL ':days days'
            ORDER BY recorded_at ASC
        """), {"days": days})
        rows = result.mappings().fetchall()
    return [dict(r) for r in rows]