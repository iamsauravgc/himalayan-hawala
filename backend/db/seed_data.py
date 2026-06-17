import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from db.connection import get_connection
from datetime import datetime, timedelta
import random

SENDERS = ["Ramesh Thapa", "Bikash Karki", "Sunil Rai"]
RECIPIENTS = ["Sita Thapa", "Maya Karki", "Gita Rai"]
PURPOSES = ["education", "medical", "living", "savings"]
STATUSES = ["completed", "completed", "completed", "pending"]

def seed():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM transfers;")

    base_rate = 148.0
    records = []

    for i in range(50):
        sender = SENDERS[i % 3]
        recipient = RECIPIENTS[i % 3]
        amount_usd = round(random.uniform(100, 1000), 2)
        rate = round(base_rate + random.uniform(-2, 5), 4)
        amount_npr = round(amount_usd * rate, 2)
        purpose = random.choice(PURPOSES)
        status = random.choice(STATUSES)
        days_ago = random.randint(1, 180)
        transferred_at = datetime.now() - timedelta(days=days_ago)

        records.append((sender, recipient, amount_usd, amount_npr, rate, purpose, status, transferred_at))

    cur.executemany("""
        INSERT INTO transfers (sender_name, recipient_name, amount_usd, amount_npr, rate_at_send, purpose, status, transferred_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, records)

    conn.commit()
    cur.close()
    conn.close()
    print(f"Seeded {len(records)} transfers.")

if __name__ == "__main__":
    seed()