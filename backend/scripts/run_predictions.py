import sys
import os
import joblib
import pandas as pd
import glob
from datetime import timedelta
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from db.connection import get_connection

ML_DIR = os.path.join(os.path.dirname(__file__), '..', 'ml')

def get_engine():
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    name = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}")

def load_currency_data(currency):
    engine = get_engine()
    query = """
        SELECT mid_rate, recorded_at 
        FROM exchange_rates 
        WHERE currency = %(currency)s
        AND mid_rate IS NOT NULL
        ORDER BY recorded_at ASC
    """
    df = pd.read_sql(query, engine, params={"currency": currency})
    df['recorded_at'] = pd.to_datetime(df['recorded_at'])
    df = df.drop_duplicates(subset='recorded_at').sort_values('recorded_at')
    df = df.set_index('recorded_at').resample('D').ffill().reset_index()
    return df

def make_features(df):
    df['day_of_week'] = df['recorded_at'].dt.dayofweek
    df['month'] = df['recorded_at'].dt.month
    df['lag_1'] = df['mid_rate'].shift(1)
    df['lag_2'] = df['mid_rate'].shift(2)
    df['lag_3'] = df['mid_rate'].shift(3)
    df['lag_7'] = df['mid_rate'].shift(7)
    df['rolling_3'] = df['mid_rate'].rolling(3).mean()
    df['rolling_7'] = df['mid_rate'].rolling(7).mean()
    df['delta_1'] = df['mid_rate'].diff(1)
    df['delta_3'] = df['mid_rate'].diff(3)
    df['delta_7'] = df['mid_rate'].diff(7)
    return df

def get_available_models():
    pattern = os.path.join(ML_DIR, 'model_*.pkl')
    model_files = glob.glob(pattern)
    currencies = []
    for f in model_files:
        basename = os.path.basename(f)
        currency = basename.replace('model_', '').replace('.pkl', '')
        currencies.append(currency)
    return currencies

def run_predictions_for_currency(currency):
    print(f"\n=== Generating predictions for {currency} ===")

    model_path = os.path.join(ML_DIR, f'model_{currency}.pkl')
    if not os.path.exists(model_path):
        print(f"No model found for {currency}, skipping.")
        return

    saved = joblib.load(model_path)
    model = saved['model']
    features = saved['features']

    df = load_currency_data(currency)
    predictions = []
    current_rate = df['mid_rate'].iloc[-1]

    for i in range(7):
        df = make_features(df)
        last_row = df.iloc[[-1]][features]
        delta = model.predict(last_row)[0]
        next_rate = round(current_rate + delta, 4)
        next_date = df['recorded_at'].iloc[-1] + timedelta(days=1)

        margin = 0.5 * (1 + i * 0.5)
        conf_low = round(next_rate - margin, 4)
        conf_high = round(next_rate + margin, 4)

        predictions.append({
            'date': next_date,
            'rate': next_rate,
            'conf_low': conf_low,
            'conf_high': conf_high
        })

        new_row = pd.DataFrame([{
            'recorded_at': next_date,
            'mid_rate': next_rate
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        current_rate = next_rate

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM rate_predictions WHERE currency = %s",
        (currency,)
    )

    for p in predictions:
        cur.execute("""
            INSERT INTO rate_predictions (currency, predicted_for, predicted_rate, confidence_low, confidence_high)
            VALUES (%s, %s, %s, %s, %s)
        """, (currency, p['date'].date(), float(p['rate']), float(p['conf_low']), float(p['conf_high'])))
        print(f"{p['date'].date()} -> {p['rate']}")

    conn.commit()
    cur.close()
    conn.close()
    print(f"Predictions stored for {currency}.")

def run_predictions():
    currencies = get_available_models()

    if not currencies:
        print("No per-currency models found in ml/ directory.")
        print("Run ml/train_model.py first.")
        return

    print(f"Found models for: {', '.join(currencies)}")

    for currency in currencies:
        run_predictions_for_currency(currency)


def load_currency_data_upto(currency, cutoff):
    engine = get_engine()
    query = """
        SELECT mid_rate, recorded_at 
        FROM exchange_rates 
        WHERE currency = %(currency)s
        AND mid_rate IS NOT NULL
        AND recorded_at < %(cutoff)s
        ORDER BY recorded_at ASC
    """
    df = pd.read_sql(query, engine, params={"currency": currency, "cutoff": cutoff})
    df['recorded_at'] = pd.to_datetime(df['recorded_at'])
    df = df.drop_duplicates(subset='recorded_at').sort_values('recorded_at')
    df = df.set_index('recorded_at').resample('D').ffill().reset_index()
    return df


def run_backtest_for_currency(currency, cutoff_date):
    model_path = os.path.join(ML_DIR, f'model_{currency}.pkl')
    if not os.path.exists(model_path):
        return 0

    saved = joblib.load(model_path)
    model = saved['model']
    features_list = saved['features']

    df = load_currency_data_upto(currency, cutoff_date)
    if len(df) < 7:
        return 0

    predictions = []
    current_rate = df['mid_rate'].iloc[-1]

    for i in range(7):
        df = make_features(df)
        last_row = df.iloc[[-1]][features_list]
        delta = model.predict(last_row)[0]
        next_rate = round(current_rate + delta, 4)
        next_date = df['recorded_at'].iloc[-1] + timedelta(days=1)

        predictions.append({
            'date': next_date,
            'rate': next_rate,
        })

        new_row = pd.DataFrame([{
            'recorded_at': next_date,
            'mid_rate': next_rate
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        current_rate = next_rate

    conn = get_connection()
    cur = conn.cursor()
    count = 0
    for p in predictions:
        cur.execute("""
            INSERT INTO rate_predictions (currency, predicted_for, predicted_rate)
            VALUES (%s, %s, %s)
            ON CONFLICT (currency, predicted_for) DO NOTHING
        """, (currency, p['date'].date(), float(p['rate'])))
        count += 1

    conn.commit()
    cur.close()
    conn.close()
    return count


def generate_backtest_predictions():
    currencies = get_available_models()
    if not currencies:
        print("No models found for backtest predictions.")
        return

    from datetime import date, timedelta as td
    today = date.today()
    cutoffs = [today - td(days=d) for d in [30, 25, 20, 15, 10, 5]]

    total = 0
    for currency in currencies:
        for cutoff in cutoffs:
            count = run_backtest_for_currency(currency, cutoff)
            total += count
            print(f"Backtest {currency} from {cutoff}: {count} predictions")

    print(f"\nTotal backtest predictions stored: {total}")


if __name__ == "__main__":
    run_predictions()