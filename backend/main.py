import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from routers import rates, predict, sentiment, alerts

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
log = logging.getLogger("hawala")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

sys.path.insert(0, os.path.dirname(__file__))
from scripts.fetch_rates import fetch_and_store_rates
from scripts.fetch_news import fetch_articles, store_articles


async def run_rates_scheduler():
    try:
        await asyncio.to_thread(fetch_and_store_rates)
    except Exception as e:
        log.error("Rates fetch on startup failed: %s", e)

    while True:
        now = datetime.now()
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        wait = (next_midnight - now).total_seconds()
        await asyncio.sleep(wait)

        try:
            await asyncio.to_thread(fetch_and_store_rates)
        except Exception as e:
            log.error("Rates daily fetch failed: %s", e)


async def run_news_scheduler():
    try:
        articles = await asyncio.to_thread(fetch_articles)
        await asyncio.to_thread(store_articles, articles)
    except Exception as e:
        log.error("News fetch on startup failed: %s", e)

    while True:
        await asyncio.sleep(6 * 3600)
        try:
            articles = await asyncio.to_thread(fetch_articles)
            await asyncio.to_thread(store_articles, articles)
        except Exception as e:
            log.error("News scheduled fetch failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task_rates = asyncio.create_task(run_rates_scheduler())
    task_news = asyncio.create_task(run_news_scheduler())
    yield
    task_rates.cancel()
    task_news.cancel()


app = FastAPI(title="HimalayanHawala API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(rates.router, prefix="/api/rates", tags=["rates"])
app.include_router(predict.router, prefix="/api/predict", tags=["predict"])
app.include_router(sentiment.router, prefix="/api/sentiment", tags=["sentiment"]) 
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])

@app.get("/")
def root():
    return {"status": "HimalayanHawala API running"}