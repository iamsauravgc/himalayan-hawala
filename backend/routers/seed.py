import logging
import os
import sys
import threading
from fastapi import APIRouter, Depends
from auth import verify_api_key

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

log = logging.getLogger("hawala")
router = APIRouter()

_seed_status = {"running": False, "results": {}, "status": "idle"}


def _run_seed():
    global _seed_status
    results = {}

    from db.engine import engine
    from sqlalchemy import text as sql_text

    from scripts.fetch_rates import fetch_and_store_rates
    from scripts.fetch_historical import fetch_historical
    from scripts.fetch_news import fetch_articles, store_articles
    from scripts.run_predictions import run_predictions

    log.info("SEED: Clearing old data...")
    try:
        with engine.connect() as conn:
            conn.execute(sql_text("DELETE FROM rate_predictions"))
            conn.execute(sql_text("DELETE FROM exchange_rates"))
            conn.execute(sql_text("DELETE FROM news_sentiment"))
            conn.commit()
        results["clear_data"] = "ok"
        log.info("SEED: Old data cleared")
    except Exception as e:
        results["clear_data"] = f"error: {e}"
        log.error("SEED: Failed to clear data: %s", e)
    _seed_status["results"] = results

    log.info("SEED: Fetching historical rates (730 days)...")
    try:
        fetch_historical()
        results["historical_rates"] = "ok"
        log.info("SEED: Historical rates done")
    except Exception as e:
        results["historical_rates"] = f"error: {e}"
        log.error("SEED: Historical rates failed: %s", e)
    _seed_status["results"] = results

    log.info("SEED: Fetching today's rates...")
    try:
        fetch_and_store_rates()
        results["today_rates"] = "ok"
        log.info("SEED: Today's rates done")
    except Exception as e:
        results["today_rates"] = f"error: {e}"
        log.error("SEED: Today's rates failed: %s", e)
    _seed_status["results"] = results

    log.info("SEED: Training ML models...")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ml'))
        from train_model import train
        train()
        results["ml_training"] = "ok"
        log.info("SEED: ML training done")
    except Exception as e:
        results["ml_training"] = f"error: {e}"
        log.error("SEED: ML training failed: %s", e)
    _seed_status["results"] = results

    log.info("SEED: Generating predictions...")
    try:
        run_predictions()
        results["predictions"] = "ok"
        log.info("SEED: Predictions done")
    except Exception as e:
        results["predictions"] = f"error: {e}"
        log.error("SEED: Predictions failed: %s", e)
    _seed_status["results"] = results

    log.info("SEED: Fetching news...")
    try:
        articles = fetch_articles()
        store_articles(articles)
        results["news"] = f"{len(articles)} articles"
        log.info("SEED: News done (%d articles)", len(articles))
    except Exception as e:
        results["news"] = f"error: {e}"
        log.error("SEED: News failed: %s", e)
    _seed_status["results"] = results

    has_errors = any(v.startswith("error") for v in results.values())
    _seed_status["status"] = "ok" if not has_errors else "partial"
    _seed_status["running"] = False
    log.info("SEED: Complete — status=%s", _seed_status["status"])


@router.post("/seed")
def seed_database(_auth: str = Depends(verify_api_key)):
    global _seed_status
    if _seed_status["running"]:
        return {"status": "already_running", "message": "Seed is already in progress"}
    _seed_status = {"running": True, "results": {}, "status": "running"}
    t = threading.Thread(target=_run_seed, daemon=True)
    t.start()
    return {"status": "started", "message": "Seed started — check /api/seed/status for progress"}


@router.get("/seed/status")
def seed_status(_auth: str = Depends(verify_api_key)):
    return _seed_status
