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

@router.get("/{user_name}")
def get_transfers(user_name: str):
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM transfers
            WHERE sender_name = :name OR recipient_name = :name
            ORDER BY transferred_at DESC
        """), {"name": user_name})
        rows = result.mappings().fetchall()
    return [dict(r) for r in rows]