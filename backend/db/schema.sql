-- Exchange rates from NRB API
CREATE TABLE IF NOT EXISTS exchange_rates (
  id SERIAL PRIMARY KEY,
  currency VARCHAR(10),
  buy_rate DECIMAL(10,4),
  sell_rate DECIMAL(10,4),
  mid_rate DECIMAL(10,4),
  recorded_at TIMESTAMP DEFAULT NOW()
);

-- ML model predictions
CREATE TABLE IF NOT EXISTS rate_predictions (
  id SERIAL PRIMARY KEY,
  currency VARCHAR(10) NOT NULL DEFAULT 'USD',
  predicted_for DATE,
  predicted_rate DECIMAL(10,4),
  confidence_low DECIMAL(10,4),
  confidence_high DECIMAL(10,4),
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE (currency, predicted_for)
);

-- News + FinBERT sentiment
CREATE TABLE IF NOT EXISTS news_sentiment (
  id SERIAL PRIMARY KEY,
  headline TEXT UNIQUE,
  url TEXT,
  source VARCHAR(100),
  sentiment VARCHAR(20),
  sentiment_score DECIMAL(5,4),
  published_at TIMESTAMP,
  fetched_at TIMESTAMP DEFAULT NOW()
);
