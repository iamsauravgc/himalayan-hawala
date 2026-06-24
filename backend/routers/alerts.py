from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from db.engine import engine
from datetime import datetime, timedelta

from utils import validate_currency, validate_lang

router = APIRouter()
last_alert = {}

def generate_alert_text(currency, live_rate, trend, sentiment_signal):
    direction = "rise" if trend > 0 else "fall"
    action = "send money now" if trend > 0 else "wait before sending"
    if sentiment_signal == "BULLISH":
        outlook = "positive market sentiment supports this outlook."
    elif sentiment_signal == "BEARISH":
        outlook = "cautious market sentiment suggests monitoring rates."
    else:
        outlook = "market sentiment is neutral."
    return (
        f"The {currency}/NPR rate is currently {live_rate:.2f} with an expected "
        f"{direction} of {abs(trend):.2f} NPR over the next 7 days. "
        f"It is advisable to {action}; {outlook}"
    )

def translate_to_nepali(text):
    return text

@router.get("/generate")
def generate_alert(
    currency: str = Depends(validate_currency),
    lang: str = Depends(validate_lang)
):
    try:
        now = datetime.now()
        if currency in last_alert and now - last_alert[currency] < timedelta(seconds=30):
            raise HTTPException(status_code=429, detail="Please wait 30 seconds between alerts")
        last_alert[currency] = now
        with engine.connect() as conn:
            rate_row = conn.execute(text("""
                SELECT mid_rate FROM exchange_rates
                WHERE currency = :currency
                ORDER BY recorded_at DESC LIMIT 1
            """), {"currency": currency}).mappings().fetchone()

            predictions = conn.execute(text("""
                SELECT predicted_rate FROM rate_predictions
                WHERE currency = :currency
                ORDER BY predicted_for DESC
                LIMIT 7
            """), {"currency": currency}).mappings().fetchall()

            sentiment_row = conn.execute(text("""
                SELECT 
                    SUM(CASE WHEN sentiment='positive' THEN 1 ELSE 0 END) as pos,
                    SUM(CASE WHEN sentiment='negative' THEN 1 ELSE 0 END) as neg
                FROM news_sentiment
                WHERE currency = :currency
            """), {"currency": currency}).mappings().fetchone()

        if not rate_row or not predictions:
            return {"lang": lang, "alert": "Insufficient data for analysis.", "currency": currency}

        live_rate = float(rate_row['mid_rate'])
        pred_rates = [float(r['predicted_rate']) for r in reversed(predictions)]
        trend = pred_rates[-1] - pred_rates[0] if pred_rates else 0
        sentiment_signal = "BULLISH" if sentiment_row['pos'] > sentiment_row['neg'] else "BEARISH" if sentiment_row['neg'] > sentiment_row['pos'] else "NEUTRAL"

        alert_en = generate_alert_text(currency, live_rate, trend, sentiment_signal)

        if lang == "ne":
            alert_ne = translate_to_nepali(alert_en)
            return {"lang": "ne", "alert": alert_ne, "alert_en": alert_en, "currency": currency}

        return {
            "lang": "en",
            "alert": alert_en,
            "currency": currency,
            "live_rate": live_rate,
            "trend": round(trend, 2),
            "sentiment": sentiment_signal
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"lang": lang, "alert": "Alert generation unavailable.", "currency": currency, "error": str(e)}