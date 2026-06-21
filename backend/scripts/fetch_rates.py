import requests
import sys
import os
from datetime import date
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from db.connection import get_connection
from dotenv import load_dotenv

load_dotenv()

NRB_API_URL = os.getenv("NRB_API_URL")

def fetch_and_store_rates():
    today = date.today().strftime("%Y-%m-%d")
    url = f"{NRB_API_URL}/rates?from={today}&to={today}&per_page=1&page=1"
    
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    rates = data.get("data", {}).get("payload", [])
    if not rates:
        print("No rates returned.")
        return

    day_rates = rates[0].get("rates", [])

    conn = get_connection()
    cur = conn.cursor()

    for rate in day_rates:
        currency = rate.get("currency", {}).get("iso3", "")
        buy = rate.get("buy")
        sell = rate.get("sell")
        mid = round((float(buy) + float(sell)) / 2, 4) if buy and sell else None

        cur.execute("""
            INSERT INTO exchange_rates (currency, buy_rate, sell_rate, mid_rate, rate_date)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (currency, rate_date) DO UPDATE
            SET buy_rate = EXCLUDED.buy_rate,
                sell_rate = EXCLUDED.sell_rate,
                mid_rate = EXCLUDED.mid_rate,
                recorded_at = NOW()
        """, (currency, buy, sell, mid, today))

    conn.commit()
    cur.close()
    conn.close()
    print(f"Stored {len(day_rates)} rates for {today}.")

if __name__ == "__main__":
    fetch_and_store_rates()