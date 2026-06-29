import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
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


REQUIRED_ENV_VARS = [
    "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD",
    "NRB_API_URL", "NEWS_API_KEY", "HF_API_KEY",
    "CORS_ORIGINS", "API_AUTH_TOKEN",
]

def check_env():
    missing = [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]
    if missing:
        log.warning("Missing environment variables: %s", ", ".join(missing))
    else:
        log.info("All required environment variables are set")


@asynccontextmanager
async def lifespan(app: FastAPI):
    check_env()
    task_rates = asyncio.create_task(run_rates_scheduler())
    task_news = asyncio.create_task(run_news_scheduler())
    yield
    task_rates.cancel()
    task_news.cancel()


app = FastAPI(title="HimalayanHawala API", lifespan=lifespan)

cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:3000")
cors_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)
app.add_middleware(SecurityHeadersMiddleware)

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.exception("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

app.include_router(rates.router, prefix="/api/rates", tags=["rates"])
app.include_router(predict.router, prefix="/api/predict", tags=["predict"])
app.include_router(sentiment.router, prefix="/api/sentiment", tags=["sentiment"]) 
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])

@app.get("/api/health")
def health():
    missing = [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]
    return {
        "status": "ok",
        "missing_env_vars": missing,
        "env_ok": len(missing) == 0,
    }


@app.get("/")
def root():
    return {"status": "HimalayanHawala API running"}