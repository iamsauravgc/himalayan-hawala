import requests
import sys
import os
from datetime import date, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from db.connection import get_connection
from dotenv import load_dotenv

load_dotenv()


def fetch_chunk(from_date, to_date):
    nrb_api_url = os.getenv("NRB_API_URL")
    if not nrb_api_url:
        print("ERROR: NRB_API_URL environment variable is not set")
        return []
    url = f"{nrb_api_url}/rates?from={from_date}&to={to_date}&per_page=100&page=1"
    r = requests.get(url)
    data = r.json()
    return data.get("data", {}).get("payload", []) or []

def fetch_historical():
    conn = get_connection()
    cur = conn.cursor()
    count = 0

    end = date.today()
    start = end - timedelta(days=730)

    # fetch in 90-day chunks
    chunk_start = start
    while chunk_start < end:
        chunk_end = min(chunk_start + timedelta(days=90), end)
        print(f"Fetching {chunk_start} to {chunk_end}...")

        payload = fetch_chunk(
            chunk_start.strftime("%Y-%m-%d"),
            chunk_end.strftime("%Y-%m-%d")
        )

        for day in payload:
            day_date = day.get("date")
            for rate in day.get("rates", []):
                currency = rate.get("currency", {}).get("iso3", "")
                buy = rate.get("buy")
                sell = rate.get("sell")
                if not buy or not sell:
                    continue
                mid = round((float(buy) + float(sell)) / 2, 4)

                cur.execute("""
                    INSERT INTO exchange_rates (currency, buy_rate, sell_rate, mid_rate, recorded_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (currency, buy, sell, mid, day_date))
                count += 1

        chunk_start = chunk_end + timedelta(days=1)

    conn.commit()
    cur.close()
    conn.close()
    print(f"Done. Total records stored: {count}")

if __name__ == "__main__":
    fetch_historical()