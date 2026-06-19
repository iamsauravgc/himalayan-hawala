import sys
import os
import pickle
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

MIN_RECORDS = 100

def get_engine():
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    name = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}")

def get_currencies():
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT currency, COUNT(*) as cnt
            FROM exchange_rates
            WHERE mid_rate IS NOT NULL
            AND currency != 'INR'
            GROUP BY currency
            HAVING COUNT(*) >= :min_records
            ORDER BY currency
        """), {"min_records": MIN_RECORDS})
        return [row._mapping['currency'] for row in result]

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
    return df

def engineer_features(df):
    df['recorded_at'] = pd.to_datetime(df['recorded_at'])
    df = df.drop_duplicates(subset='recorded_at').reset_index(drop=True)
    df = df.sort_values('recorded_at').reset_index(drop=True)
    df = df.set_index('recorded_at').resample('D').ffill().reset_index()

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

    df['target_delta'] = df['mid_rate'].shift(-1) - df['mid_rate']

    df = df.dropna().reset_index(drop=True)
    return df

def train_for_currency(currency):
    print(f"\n=== Training model for {currency} ===")

    df = load_currency_data(currency)
    print(f"Loaded {len(df)} records.")

    df = engineer_features(df)
    print(f"After feature engineering: {len(df)} records.")

    if len(df) < MIN_RECORDS:
        print(f"Skipping {currency}: only {len(df)} records after engineering (need {MIN_RECORDS}).")
        return

    features = [
        'day_of_week', 'month',
        'lag_1', 'lag_2', 'lag_3', 'lag_7',
        'rolling_3', 'rolling_7',
        'delta_1', 'delta_3', 'delta_7'
    ]

    X = df[features]
    y = df['target_delta']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    print("Training Random Forest...")
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=8,
        min_samples_split=5,
        random_state=42
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    mae_delta = mean_absolute_error(y_test, preds)
    print(f"MAE on delta: {mae_delta:.4f} {currency}/day")

    last_rates = df.loc[X_test.index, 'mid_rate']
    predicted_rates = last_rates.values + preds
    actual_rates = last_rates.values + y_test.values
    mae_rate = mean_absolute_error(actual_rates, predicted_rates)
    print(f"MAE on actual rate: {mae_rate:.4f} {currency}")

    model_path = os.path.join(os.path.dirname(__file__), f'model_{currency}.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump({'model': model, 'features': features}, f)
    print(f"Model saved to {model_path}")

def train():
    currencies = get_currencies()

    if not currencies:
        print("No currencies found with enough history.")
        return

    print(f"Found currencies with >= {MIN_RECORDS} records: {', '.join(currencies)}")

    for currency in currencies:
        train_for_currency(currency)

if __name__ == "__main__":
    train()