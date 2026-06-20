import re
from fastapi import HTTPException

def validate_currency(currency: str) -> str:
    c = currency.strip().upper()
    if not re.match(r'^[A-Z]{3}$', c):
        raise HTTPException(status_code=400, detail="Currency must be a 3-letter ISO code")
    if c == 'INR':
        raise HTTPException(status_code=400, detail="INR is not supported")
    return c

def validate_lang(lang: str) -> str:
    if lang not in ("en", "ne"):
        raise HTTPException(status_code=400, detail="Language must be 'en' or 'ne'")
    return lang
