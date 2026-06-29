import logging
import os
import sys
from fastapi import APIRouter, Depends
from auth import verify_api_key

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

log = logging.getLogger("hawala")
router = APIRouter()


def run_seed():
    results = {}

    from scripts.fetch_rates import fetch_and_store_rates
    from scripts.fetch_historical import fetch_historical
    from scripts.fetch_news import fetch_articles, store_articles
    from scripts.run_predictions import run_predictions

    log.info("SEED: Fetching historical rates (730 days)...")
    try:
        fetch_historical()
        results["historical_rates"] = "ok"
        log.info("SEED: Historical rates done")
    except Exception as e:
        results["historical_rates"] = f"error: {e}"
        log.error("SEED: Historical rates failed: %s", e)

    log.info("SEED: Fetching today's rates...")
    try:
        fetch_and_store_rates()
        results["today_rates"] = "ok"
        log.info("SEED: Today's rates done")
    except Exception as e:
        results["today_rates"] = f"error: {e}"
        log.error("SEED: Today's rates failed: %s", e)

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

    log.info("SEED: Generating predictions...")
    try:
        run_predictions()
        results["predictions"] = "ok"
        log.info("SEED: Predictions done")
    except Exception as e:
        results["predictions"] = f"error: {e}"
        log.error("SEED: Predictions failed: %s", e)

    log.info("SEED: Fetching news...")
    try:
        articles = fetch_articles()
        store_articles(articles)
        results["news"] = f"{len(articles)} articles"
        log.info("SEED: News done (%d articles)", len(articles))
    except Exception as e:
        results["news"] = f"error: {e}"
        log.error("SEED: News failed: %s", e)

    return results


@router.post("/seed")
def seed_database(_auth: str = Depends(verify_api_key)):
    log.info("SEED: Starting full database seed")
    results = run_seed()
    all_ok = all(v == "ok" for v in results.values())
    return {"status": "ok" if all_ok else "partial", "results": results}
