# Himalayan Hawala

Remittance intelligence dashboard for Nepal's forex market. Combines NRB exchange rates, ML-based 7-day forecasts, and FinBERT news sentiment into a single-page dashboard.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, Recharts, Tailwind CSS 4 |
| Backend | FastAPI 0.137, Uvicorn |
| Database | PostgreSQL, SQLAlchemy, psycopg2 |
| ML | scikit-learn Random Forest, joblib |
| External APIs | NRB Nepal (rates), NewsAPI (articles), HuggingFace (FinBERT sentiment) |

## System Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │
│  │ Live Rate  │  │ 7-Day      │  │ Smart      │  │ News           │  │
│  │ + Chart    │  │ Forecast   │  │ Alert      │  │ Feed + Refresh │  │
│  │ + Backtest │  │ Projection │  │ (client-   │  │ (sentiment     │  │
│  │            │  │ (BULLISH/  │  │  side)     │  │  pills)        │  │
│  │            │  │  BEARISH)  │  │            │  │                │  │
│  └────────────┘  └────────────┘  └────────────┘  └────────────────┘  │
└──────────────────────────┬────────────────────────────────────────────┘
                           │ HTTP (port 3000 → 8000)
                           ▼
┌───────────────────────────────────────────────────────────────────────┐
│                        API GATEWAY (FastAPI)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │ /api/rates   │  │ /api/predict │  │ /api/sentiment│  │ /api/    │  │
│  │ · live       │  │ · /          │  │ · /          │  │ alerts/  │  │
│  │ · history    │  │ · currencies │  │ · summary    │  │ generate │  │
│  │ · currencies │  │ · backtest   │  │ · refresh    │  │          │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘  │
└──────────────────────────┬────────────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ exchange_rates  │ │ rate_predictions│ │ news_sentiment  │
│ · buy/sell/mid  │ │ · predicted_for │ │ · headline/url  │
│ · currency/date │ │ · rate + conf   │ │ · sentiment     │
│                 │ │ · created_at    │ │ · currency      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
         │                   ▲
         │                   │
         ▼                   │
┌─────────────────┐          │
│  Scripts        │          │
│ fetch_rates.py  ├──────────┘
│ fetch_historical│
│ fetch_news.py   │
│ run_preds.py    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│ ML Models (21 Random Forests)   │
│ model_USD.pkl ... model_THB.pkl │
│ Trained by ml/train_model.py    │
│ Features: lag_1/2/3/7, rolling  │
│ 3/7, delta 1/3/7, day/mon      │
└─────────────────────────────────┘
```

## Data Flow

```
NRB API ──(daily)──> fetch_rates.py ──upsert──> exchange_rates table
NewsAPI ──(6h)──> fetch_news.py ──FinBERT──> news_sentiment table
exchange_rates ──> train_model.py ──> 21 model_*.pkl files
model_*.pkl ──> run_predictions.py ──> rate_predictions table
Frontend ──> FastAPI ──> PostgreSQL ──> JSON responses
```

## ML Methodology

**Model:** Random Forest Regressor (200 trees, max_depth=8) predicting daily delta (next rate − current rate). One model per currency (21 total).

**Features:** `day_of_week`, `month`, lags (1/2/3/7 days), rolling averages (3/7 days), deltas (1/3/7 days).

**Prediction:** 7-day iterative forecast — each day's predicted rate feeds into the next. Confidence interval expands linearly: margin = `0.5 × (1 + day_index × 0.5)`. Training requires 100+ records per currency, 80/20 chronological split.

**Backtest metrics:** MAE, RMSE, MAPE, Direction Accuracy (%), Simulated Gain (NPR) — computed by joining predictions against realized rates.

## API Endpoints

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/` | — | Health check |
| GET | `/api/rates/currencies` | — | All tracked currency codes (excl. INR) |
| GET | `/api/rates/live` | `currency` | Latest buy/sell/mid rate |
| GET | `/api/rates/history` | `currency`, `days` (1–365, default 90) | Historical mid rates |
| GET | `/api/predict/` | `currency` | 7-day forecast with confidence bands |
| GET | `/api/predict/currencies` | — | Currencies with predictions |
| GET | `/api/predict/backtest` | `currency` | Model accuracy: MAE, RMSE, direction %, simulated gain |
| GET | `/api/sentiment/` | `currency` (optional) | Latest 20 news articles with sentiment |
| GET | `/api/sentiment/summary` | `currency` (optional) | Sentiment breakdown + BULLISH/BEARISH/NEUTRAL signal |
| POST | `/api/sentiment/refresh` | `currency` | Fetch fresh news (60s rate limit per currency) |
| GET | `/api/alerts/generate` | `currency`, `lang` (en/ne) | Text recommendation (30s rate limit per currency) |

## Local Setup

```bash
# Backend
cd backend
python -m venv venv; venv\Scripts\activate  # Windows
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

**.env variables:**
```
DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
NRB_API_URL=https://www.nrb.org.np/api/forex/v1
NEWS_API_KEY=your_key
HF_API_KEY=your_key
```

## Data Pipelines

| Script | Trigger | What it does |
|--------|---------|-------------|
| `scripts/fetch_rates.py` | Backend startup + daily midnight | Pulls latest NRB rates, upserts into `exchange_rates` |
| `scripts/fetch_historical.py` | Manual (one-time) | Seeds 730 days of NRB history |
| `scripts/fetch_news.py` | Backend startup + every 6h, or POST /refresh | Queries NewsAPI → FinBERT sentiment → `news_sentiment` |
| `scripts/run_predictions.py` | Manual (after training) | Loads `.pkl` models, generates 7-day predictions per currency |
| `ml/train_model.py` | Manual | Trains Random Forest per currency, saves `model_*.pkl` |
