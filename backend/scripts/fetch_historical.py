import requests
import sys
import os
from datetime import date, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from db.connection import get_connection
from dotenv import load_dotenv

load_dotenv()

NRB_API_URL = os.getenv("NRB_API_URL")

def fetch_historical(from_date, to_date):
    url = f"{NRB_API_URL}/rates?from={from_date}&to={to_date}&per_page=100&page=1"
    
    response = requests.get(url)
    data = response.json()
    
    payload = data.get("data", {}).get("payload", [])
    total_pages = data.get("data", {}).get("pagination", {}).get("pages", 1)
    
    all_days = payload.copy()
    
    for page in range(2, total_pages + 1):
        r = requests.get(f"{url}&page={page}")
        d = r.json()
        all_days += d.get("data", {}).get("payload", [])
        print(f"Fetched page {page}/{total_pages}")
    
    conn = get_connection()
    cur = conn.cursor()
    count = 0

    for day in all_days:
        day_date = day.get("date")
        for rate in day.get("rates", []):
            currency = rate.get("currency", {}).get("iso3", "")
            buy = rate.get("buy")
            sell = rate.get("sell")
            mid = round((float(buy) + float(sell)) / 2, 4) if buy and sell else None

            cur.execute("""
                INSERT INTO exchange_rates (currency, buy_rate, sell_rate, mid_rate, recorded_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (currency, buy, sell, mid, day_date))
            count += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Done. Stored {count} rate records.")

if __name__ == "__main__":
    to_date = date.today().strftime("%Y-%m-%d")
    from_date = (date.today() - timedelta(days=730)).strftime("%Y-%m-%d")
    print(f"Fetching from {from_date} to {to_date}...")
    fetch_historical(from_date, to_date)