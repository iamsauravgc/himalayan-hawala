from fastapi import APIRouter
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import requests
import os

load_dotenv()

router = APIRouter()

def get_engine():
    return create_engine(
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )

def generate_alert_text(live_rate, trend, sentiment_signal):
    prompt = f"""Current USD/NPR rate: {live_rate}
7-day trend: rate will {"fall" if trend < 0 else "rise"} by {abs(round(trend, 2))} NPR
Market sentiment: {sentiment_signal}

Write a 2-sentence clear, actionable recommendation for someone sending money to Nepal."""

    r = requests.post(
        "https://router.huggingface.co/together/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"},
        json={
            "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    result = r.json()
    try:
        return result['choices'][0]['message']['content'].strip()
    except (KeyError, IndexError):
        return "Rate analysis unavailable."

def translate_to_nepali(text):
    r = requests.post(
        "https://router.huggingface.co/together/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"},
        json={
            "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "messages": [{"role": "user", "content": f"Translate this to Nepali, output only the translation: {text}"}]
        }
    )
    result = r.json()
    try:
        return result['choices'][0]['message']['content'].strip()
    except (KeyError, IndexError):
        return text

@router.get("/generate")
def generate_alert(lang: str = "en"):
    engine = get_engine()

    with engine.connect() as conn:
        rate_row = conn.execute(text("""
            SELECT mid_rate FROM exchange_rates
            WHERE currency = 'USD'
            ORDER BY recorded_at DESC LIMIT 1
        """)).mappings().fetchone()

        predictions = conn.execute(text("""
            SELECT predicted_rate FROM rate_predictions
            ORDER BY predicted_for ASC
        """)).mappings().fetchall()

        sentiment_row = conn.execute(text("""
            SELECT 
                SUM(CASE WHEN sentiment='positive' THEN 1 ELSE 0 END) as pos,
                SUM(CASE WHEN sentiment='negative' THEN 1 ELSE 0 END) as neg
            FROM news_sentiment
        """)).mappings().fetchone()

    live_rate = float(rate_row['mid_rate'])
    trend = float(predictions[-1]['predicted_rate']) - float(predictions[0]['predicted_rate']) if predictions else 0
    sentiment_signal = "BULLISH" if sentiment_row['pos'] > sentiment_row['neg'] else "BEARISH" if sentiment_row['neg'] > sentiment_row['pos'] else "NEUTRAL"

    alert_en = generate_alert_text(live_rate, trend, sentiment_signal)

    if lang == "ne":
        alert_ne = translate_to_nepali(alert_en)
        return {"lang": "ne", "alert": alert_ne, "alert_en": alert_en}

    return {
        "lang": "en",
        "alert": alert_en,
        "live_rate": live_rate,
        "trend": round(trend, 2),
        "sentiment": sentiment_signal
    }