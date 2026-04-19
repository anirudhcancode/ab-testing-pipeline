import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import random

# Database connection
DB_USER = "fraud_user"
DB_PASSWORD = "fraud_pass"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "fraud_db"

engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Experiment configuration
EXPERIMENT = {
    "name": "checkout_button_test",
    "control": {
        "name": "Control A",
        "description": "Green button — Complete Purchase",
        "conversion_rate": 0.12  # 12% baseline conversion
    },
    "variant": {
        "name": "Variant B",
        "description": "Orange button — Buy Now",
        "conversion_rate": 0.145  # 14.5% — we expect this to win
    },
    "n_users": 10000,
    "duration_days": 14
}

def simulate_experiment(config: dict) -> pd.DataFrame:
    print(f"Simulating experiment: {config['name']}")
    print(f"Total users: {config['n_users']}")
    print(f"Duration: {config['duration_days']} days")

    np.random.seed(42)
    random.seed(42)

    records = []
    start_date = datetime(2024, 1, 1)

    for i in range(config["n_users"]):
        # Assign user to control or variant (50/50 split)
        group = "control" if i % 2 == 0 else "variant"
        conversion_rate = config[group]["conversion_rate"]

        # Random timestamp within experiment duration
        day_offset = random.randint(0, config["duration_days"] - 1)
        hour_offset = random.randint(0, 23)
        timestamp = start_date + timedelta(days=day_offset, hours=hour_offset)

        # Simulate conversion — did the user purchase?
        converted = int(np.random.binomial(1, conversion_rate))

        # Simulate revenue if converted
        revenue = round(np.random.exponential(85), 2) if converted else 0.0

        # Simulate session duration in seconds
        session_duration = int(np.random.normal(180, 60))
        session_duration = max(10, session_duration)

        records.append({
            "user_id": f"user_{i+1:05d}",
            "group": group,
            "group_label": config[group]["name"],
            "timestamp": timestamp,
            "day": day_offset + 1,
            "converted": converted,
            "revenue": revenue,
            "session_duration": session_duration
        })

    df = pd.DataFrame(records)
    print(f"\nSimulation complete:")
    print(f"  Control users:  {len(df[df['group']=='control'])}")
    print(f"  Variant users:  {len(df[df['group']=='variant'])}")
    print(f"  Control conversions: {df[df['group']=='control']['converted'].sum()}")
    print(f"  Variant conversions: {df[df['group']=='variant']['converted'].sum()}")
    print(f"  Control conversion rate: {df[df['group']=='control']['converted'].mean():.4f}")
    print(f"  Variant conversion rate: {df[df['group']=='variant']['converted'].mean():.4f}")
    return df

def create_table(engine):
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ab_experiment (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(20),
                group_name VARCHAR(20),
                group_label VARCHAR(50),
                timestamp TIMESTAMP,
                day INTEGER,
                converted INTEGER,
                revenue FLOAT,
                session_duration INTEGER
            );
        """))
        conn.commit()
    print("\nTable created successfully")

def save_data(df: pd.DataFrame, engine):
    df_save = df.rename(columns={"group": "group_name"})
    df_save.to_sql("ab_experiment", engine, if_exists="replace", index=False)
    print(f"Saved {len(df_save)} rows to PostgreSQL")

if __name__ == "__main__":
    df = simulate_experiment(EXPERIMENT)
    create_table(engine)
    save_data(df, engine)
    print("\nPhase 1 complete!")