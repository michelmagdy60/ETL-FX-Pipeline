import requests
import json
from datetime import datetime
from sqlalchemy import create_engine
import pandas as pd

# ── Configuration ──────────────────────────────────────────
API_KEY  = "1f4f99a8617f436bbf3f2b6015531e4a"
BASE_URL = "https://openexchangerates.org/api"

# Paste your real Neon connection string here
DB_URL = "postgresql://neondb_owner:npg_2MvTqJb0QCIj@ep-rough-glitter-aptuq4vm-pooler.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"


# ── Step 1: Extract ────────────────────────────────────────
def fetch_rates():
    url = f"{BASE_URL}/latest.json?app_id={API_KEY}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    print(f"Fetched {len(data['rates'])} currency rates")
    return data


# ── Step 2: Transform ──────────────────────────────────────
def transform_rates(raw_data):
    rates         = raw_data["rates"]
    base_currency = raw_data["base"]
    timestamp     = raw_data["timestamp"]

    df = pd.DataFrame([
        {
            "fetch_date":      datetime.utcfromtimestamp(timestamp).date(),
            "base_currency":   base_currency,
            "target_currency": currency,
            "exchange_rate":   rate,
            "rate_vs_eur":     rate / rates.get("EUR", 1),
        }
        for currency, rate in rates.items()
    ])

    df = df.dropna()
    df = df[df["exchange_rate"] > 0]
    df["fetch_date"] = pd.to_datetime(df["fetch_date"])

    print(f"Transformed {len(df)} rows")
    return df


# ── Step 3: Load ───────────────────────────────────────────
def load_to_postgres(df):
    engine = create_engine(DB_URL)

    df.to_sql(
        name="exchange_rates",
        con=engine,
        if_exists="append",
        index=False,
        method="multi"
    )
    print(f"Loaded {len(df)} rows into PostgreSQL")


# ── Run the pipeline ───────────────────────────────────────
if __name__ == "__main__":
    raw = fetch_rates()
    df  = transform_rates(raw)
    load_to_postgres(df)
    print("Pipeline complete!")
