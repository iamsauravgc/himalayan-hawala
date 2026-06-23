# Himalayan Hawala - Remittance Intelligence Platform

## Overview

Himalayan Hawala is a sophisticated remittance intelligence platform that provides real-time currency forecasting and market sentiment analysis for Nepal's foreign exchange market. The platform combines machine learning, financial news analysis, and official NRB data to deliver actionable insights for remittance senders and financial service providers.

## ML Approach & Methodology

### Core Algorithm
- **Model Type**: Random Forest Regressor for delta prediction
- **Target Variable**: Daily currency rate changes (delta)
- **Features**: 
  - Temporal: Day of week, month
  - Lag features: 1, 2, 3, and 7-day historical rates
  - Moving averages: 3-day and 7-day rolling averages
  - Rate changes: 1, 3, and 7-day deltas
- **Prediction Horizon**: 7-day forward projections
- **Confidence Intervals**: Dynamic margins expanding with forecast horizon

### Training Process
1. **Data Collection**: Historical exchange rates from NRB API (2+ years)
2. **Feature Engineering**: Lag features, moving averages, and rate deltas
3. **Model Training**: Random Forest with 200 trees, max depth 8
4. **Validation**: 80/20 train-test split with chronological ordering
5. **Deployment**: One model per currency (23+ major currencies supported)

### Model Performance Metrics
- **MAE**: Mean Absolute Error in NPR per day
- **RMSE**: Root Mean Square Error for volatility assessment
- **MAPE**: Mean Absolute Percentage Error for relative accuracy
- **Direction Accuracy**: Correct prediction of rate movements
- **Backtesting**: Simulated gains based on historical predictions

## Data Sources

### 1. Official Exchange Rate Data
- **Provider**: Nepal Rastra Bank (NRB)
- **API Endpoint**: `https://www.nrb.org.np/api/forex/v1`
- **Frequency**: Daily updates
- **Coverage**: 30+ currency pairs against NPR
- **Quality**: Official central bank rates (buy/sell/mid)

### 2. Financial News Intelligence
- **Source**: NewsAPI.org
- **Query**: "Nepal rupee exchange rate OR Nepali remittance NPR OR USD NPR forecast OR Federal Reserve interest rate Asia OR emerging market currency forex OR Nepal economy trade deficit"
- **Processing**: FinBERT sentiment analysis
- **Frequency**: Every 6 hours
- **Languages**: English news with Nepali translation support

### 3. ML Model Training Data
- **Historical Range**: 730+ days (2+ years)
- **Currencies**: Major global currencies (excluding INR)
- **Minimum Records**: 100+ data points per currency
- **Update Frequency**: Monthly retraining pipeline

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React/Next.js)                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │   Dashboard     │    │   Currency      │    │   Smart Alerts  │  │
│  │   Charts        │    │   Selector      │    │   (AI-generated)│  │
│  │   + Predictions │    │   + News Feed   │    │   + Backtest    │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API GATEWAY (FastAPI)                         │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │   Rates API     │    │   Predict API   │    │   Sentiment API │  │
│  │   • Live Rates  │    │   • 7-day Forecast│  │   • News Feed   │  │
│  │   • History     │    │   • Backtest     │    │   • Sentiment   │  │
│  │   • Currencies  │    │   • Model Info   │    │   • Refresh     │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA PIPELINES                               │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │   Scheduler     │    │   NRB Fetch     │    │   News Fetch    │  │
│  │   • Rates       │    │   • Daily       │    │   • FinBERT     │  │
│  │   • News        │    │   • Historical  │    │   • Sentiment   │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA STORE (PostgreSQL)                       │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │ exchange_rates  │    │ rate_predictions │    │ news_sentiment  │  │
│  │ • buy/sell/mid  │    │ • AI forecasts   │    │ • FinBERT       │  │
│  │ • daily rates   │    │ • confidence     │    │ • sentiment     │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ML MODELS (Pickle)                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │ model_USD.pkl   │    │ model_EUR.pkl   │    │ model_JPY.pkl   │  │
│  │ model_THB.pkl   │    │ model_GBP.pkl   │    │ ... (23+ total) │  │
│  │ model_CNY.pkl   │    │ model_AUD.pkl   │    │                 │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Real-Time Dashboard
- **Live Rates**: Current buy/sell/mid rates with NPR precision
- **7-Day Forecast**: AI-generated rate predictions with confidence bands
- **Market Signal**: Bullish/Bearish/Neutral indicators
- **Smart Alerts**: Actionable recommendations for remittance decisions

### 2. Advanced Analytics
- **Backtesting**: Historical model performance with simulated gains
- **Sentiment Analysis**: Financial news sentiment scoring
- **Multi-currency Support**: 23+ global currencies tracked
- **Nepali Language**: Bilingual interface for accessibility

### 3. Professional APIs
- **RESTful API**: Full programmatic access
- **Rate Limiting**: API key protection for production use
- **CORS Support**: Cross-origin requests for web integration
- **Security Headers**: Enterprise-grade security

## Setup & Deployment

### Prerequisites
```bash
# Backend
python >= 3.8
PostgreSQL >= 9.6
Redis (optional, for caching)

# Frontend
Node.js >= 18
npm >= 9
```

### Local Development
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m db.migrate_001  # Run migrations
python main.py  # Start API server

# Frontend
cd frontend
npm install
npm run dev  # Start development server
```

### Production Deployment
```bash
# Environment Variables
cp .env.example .env
# Configure database, API keys, etc.

# Database Migration
python -m db.migrate_001

# Data Collection
python scripts/fetch_historical.py  # Initial data
python scripts/fetch_rates.py  # Daily rates
python scripts/fetch_news.py  # News collection

# Model Training
python ml/train_model.py  # Train ML models

# Prediction Generation
python scripts/run_predictions.py  # Generate forecasts

# API Server
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Docker Deployment
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# frontend/Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
CMD ["npm", "start"]
```

## Model Training & Updates

### Training Pipeline
1. **Data Requirements**: 100+ records per currency
2. **Feature Engineering**: Automatic lag features and moving averages
3. **Model Selection**: Random Forest (tuned hyperparameters)
4. **Validation**: Out-of-sample testing with MAE calculation
5. **Persistence**: Pickle format for production deployment

### Retraining Schedule
- **Frequency**: Monthly or when new data available
- **Trigger**: Data quality threshold check
- **Process**: Automated via cron jobs
- **Validation**: Performance comparison with previous models

### Model Monitoring
- **Drift Detection**: Feature distribution monitoring
- **Performance Tracking**: MAE, RMSE, MAPE metrics
- **Alerting**: Performance degradation notifications
- **A/B Testing**: New model validation before deployment

## API Documentation

### Rates API (`/api/rates`)
- **GET /live?currency=USD** - Current exchange rate
- **GET /history?currency=USD&days=90** - Historical rates
- **GET /currencies** - Supported currencies list

### Predictions API (`/api/predict`)
- **GET /** - 7-day forecast for currency
- **GET /currencies** - Available prediction currencies
- **GET /backtest?currency=USD** - Model performance metrics

### Sentiment API (`/api/sentiment`)
- **GET /** - Latest financial news
- **GET /summary** - Market sentiment analysis
- **POST /refresh** - Force news refresh (API key required)

### Alerts API (`/api/alerts`)
- **GET /generate?currency=USD&lang=en** - AI-generated recommendations
- **GET /generate?currency=USD&lang=ne** - Nepali language recommendations

## Monitoring & Evaluation

### Key Metrics
- **API Performance**: Response times, error rates
- **Model Accuracy**: MAE, RMSE, MAPE, direction accuracy
- **Data Quality**: Completeness, freshness, consistency
- **User Engagement**: Dashboard interactions, alert usage

### Alert Thresholds
- **Model Performance**: MAE > 0.5 NPR triggers review
- **Data Freshness**: Rates > 24 hours old
- **API Usage**: Rate limiting alerts
- **System Health**: Database connection failures

### Reporting
- **Daily**: Model performance summary
- **Weekly**: Accuracy trends and alerts
- **Monthly**: Comprehensive performance report
- **Ad-hoc**: Custom analysis requests

## Testing & Quality Assurance

### Unit Tests
- **API Endpoints**: FastAPI test clients
- **ML Models**: Scikit-learn validation
- **Database**: SQLAlchemy integration tests
- **Sentiment**: FinBERT integration tests

### Integration Tests
- **End-to-End**: Full pipeline validation
- **Load Testing**: API performance under stress
- **Data Pipeline**: Complete data flow verification
- **Model Deployment**: Model serving validation

### CI/CD Pipeline
- **Code Quality**: Linting, type checking
- **Security**: Dependency vulnerability scanning
- **Testing**: Automated test suite execution
- **Deployment**: Containerized deployment

## Contributing

### Development Guidelines
1. **Code Style**: Follow existing patterns and conventions
2. **Testing**: Write comprehensive unit and integration tests
3. **Documentation**: Update README and API docs
4. **Performance**: Optimize database queries and ML inference

### Model Contribution
1. **Data Collection**: Ensure 100+ records per currency
2. **Feature Engineering**: Maintain consistency with existing features
3. **Validation**: Document model performance metrics
4. **Testing**: Validate against historical data

### Bug Reports
1. **Reproduction Steps**: Clear, actionable steps
2. **Expected Behavior**: What should happen
3. **Actual Behavior**: What actually happens
4. **Environment**: OS, versions, configuration

## License

MIT License - Free for commercial and non-commercial use.

## Contact

For support, questions, or collaboration:
- **GitHub Issues**: Project repository
- **Documentation**: API docs and user guides
- **Community**: Developer discussions and forums

## Future Enhancements

### Planned Features
1. **Multi-language Support**: Additional languages beyond English/Nepali
2. **WebSocket Updates**: Real-time dashboard updates
3. **Mobile App**: Native iOS/Android application
4. **Enterprise API**: Advanced features for financial institutions

### ML Improvements
1. **Ensemble Models**: Combine multiple algorithms
2. **Deep Learning**: Neural network alternatives
3. **Time Series**: Advanced forecasting techniques
4. **Reinforcement Learning**: Adaptive trading strategies

## Performance Benchmarks

### Typical Response Times
- **Live Rates**: < 50ms
- **Predictions**: < 100ms
- **News Feed**: < 150ms
- **Alerts**: < 200ms

### Model Inference
- **Prediction Generation**: < 10ms per currency
- **Confidence Calculation**: < 5ms
- **Memory Usage**: < 100MB per model
- **CPU Usage**: < 10% on modern hardware

---

This README provides a comprehensive overview of the Himalayan Hawala platform, covering its ML methodology, data sources, architecture, and deployment procedures. The platform combines sophisticated machine learning with real-time data processing to deliver actionable insights for Nepal's foreign exchange market.