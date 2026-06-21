"""Run once: adds rate_date and currency columns to existing tables."""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from db.connection import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute("""
    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='exchange_rates' AND column_name='rate_date'
        ) THEN
            ALTER TABLE exchange_rates ADD COLUMN rate_date DATE;
            UPDATE exchange_rates SET rate_date = recorded_at::date WHERE rate_date IS NULL;
            ALTER TABLE exchange_rates ALTER COLUMN rate_date SET NOT NULL;
            DROP INDEX IF EXISTS uq_exchange_rates_currency_date;
            ALTER TABLE exchange_rates ADD CONSTRAINT uq_exchange_rates_currency_date UNIQUE (currency, rate_date);
        END IF;
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='news_sentiment' AND column_name='currency'
        ) THEN
            ALTER TABLE news_sentiment ADD COLUMN currency VARCHAR(10) DEFAULT 'USD';
        END IF;
    END $$;
""")

conn.commit()
cur.close()
conn.close()
print("Migration complete.")
