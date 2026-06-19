from fastapi import APIRouter
from sqlalchemy import text
from db.engine import engine

router = APIRouter()

@router.get("/{user_name}")
def get_transfers(user_name: str):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM transfers
            WHERE sender_name = :name OR recipient_name = :name
            ORDER BY transferred_at DESC
        """), {"name": user_name})
        rows = result.mappings().fetchall()
    return [dict(r) for r in rows]