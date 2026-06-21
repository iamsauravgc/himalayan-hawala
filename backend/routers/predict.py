import math
from fastapi import APIRouter, Query, Depends
from sqlalchemy import text
from db.engine import engine
from utils import validate_currency

router = APIRouter()

@router.get("/")
def get_predictions(currency: str = Depends(validate_currency)):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT currency, predicted_for, predicted_rate, confidence_low, confidence_high
            FROM rate_predictions
            WHERE currency = :currency
            ORDER BY predicted_for ASC
        """), {"currency": currency})
        rows = result.mappings().fetchall()
    return [dict(r) for r in rows]

@router.get("/currencies")
def list_prediction_currencies():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT currency FROM rate_predictions
            WHERE currency != 'INR'
            ORDER BY currency
        """))
        rows = result.mappings().fetchall()
    return [r['currency'] for r in rows]

@router.get("/backtest")
def backtest(currency: str = Depends(validate_currency)):
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT
              rp.predicted_for AS date,
              rp.predicted_rate,
              rp.created_at,
              er.mid_rate AS actual_rate,
              rp.predicted_rate - er.mid_rate AS error,
              ABS(rp.predicted_rate - er.mid_rate) AS abs_error,
              (SELECT mid_rate FROM exchange_rates
               WHERE currency = rp.currency
                 AND recorded_at < rp.created_at
               ORDER BY recorded_at DESC
               LIMIT 1) AS rate_at_pred
            FROM rate_predictions rp
            JOIN exchange_rates er
              ON er.currency = rp.currency
              AND er.rate_date = rp.predicted_for
            WHERE rp.currency = :currency
              AND er.mid_rate IS NOT NULL
            ORDER BY rp.predicted_for ASC
        """), {"currency": currency}).mappings().fetchall()

    if not rows:
        return {
            "currency": currency,
            "count": 0, "mae": None, "rmse": None, "mape": None,
            "direction_accuracy": None, "simulated_gain_npr": None,
            "results": []
        }

    results = []
    total_abs_error = 0.0
    total_sq_error = 0.0
    total_pct_error = 0.0
    correct_dir = 0
    simulated_gain = 0.0

    for r in rows:
        predicted = float(r["predicted_rate"])
        actual = float(r["actual_rate"])
        abs_err = float(r["abs_error"])
        err = float(r["error"])
        pct = abs(round(err / actual * 100, 2)) if actual != 0 else 0.0
        rate_at_pred = float(r["rate_at_pred"]) if r["rate_at_pred"] else actual

        pred_up = predicted > rate_at_pred
        actual_up = actual > rate_at_pred
        if pred_up == actual_up and actual != rate_at_pred:
            correct_dir += 1

        gain = 1000.0 * (actual - rate_at_pred) if pred_up else 1000.0 * (rate_at_pred - actual)
        simulated_gain += gain

        total_abs_error += abs_err
        total_sq_error += err * err
        total_pct_error += pct

        results.append({
            "date": str(r["date"]),
            "predicted": round(predicted, 4),
            "actual": round(actual, 4),
            "error": round(err, 4),
            "abs_error": round(abs_err, 4),
            "error_pct": round(pct, 2),
        })

    n = len(results)
    mae = round(total_abs_error / n, 4)
    rmse = round(math.sqrt(total_sq_error / n), 4)
    mape = round(total_pct_error / n, 2)
    direction_accuracy = round(correct_dir / n * 100, 1)
    simulated_gain_npr = round(simulated_gain, 2)

    return {
        "currency": currency,
        "count": n,
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "direction_accuracy": direction_accuracy,
        "simulated_gain_npr": simulated_gain_npr,
        "results": results,
    }