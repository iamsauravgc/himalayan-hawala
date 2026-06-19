from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import rates, predict, transfers, sentiment, alerts

app = FastAPI(title="HimalayanHawala API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rates.router, prefix="/api/rates", tags=["rates"])
app.include_router(predict.router, prefix="/api/predict", tags=["predict"])
app.include_router(transfers.router, prefix="/api/transfers", tags=["transfers"])
app.include_router(sentiment.router, prefix="/api/sentiment", tags=["sentiment"]) 
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])

@app.get("/")
def root():
    return {"status": "HimalayanHawala API running"}