import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine
from statsmodels.stats.proportion import proportions_ztest, proportion_confint
import warnings
warnings.filterwarnings("ignore")

import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://fraud_user:fraud_pass@localhost:5432/fraud_db"
)

engine = create_engine(DATABASE_URL)

app = FastAPI(
    title="A/B Testing Analytics API",
    description="Statistical analysis of A/B experiment results",
    version="1.0.0"
)

class ExperimentConfig(BaseModel):
    n_users: int = 10000
    control_rate: float = 0.12
    variant_rate: float = 0.145
    duration_days: int = 14

def load_data():
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM ab_experiment", conn)
    return df

def run_analysis(df: pd.DataFrame) -> dict:
    control = df[df["group_name"] == "control"]
    variant = df[df["group_name"] == "variant"]

    n_control = len(control)
    n_variant = len(variant)
    conv_control = control["converted"].sum()
    conv_variant = variant["converted"].sum()

    rate_control = conv_control / n_control
    rate_variant = conv_variant / n_variant

    absolute_lift = rate_variant - rate_control
    relative_lift = absolute_lift / rate_control

    count = np.array([conv_variant, conv_control])
    nobs = np.array([n_variant, n_control])
    z_stat, p_value = proportions_ztest(count, nobs)

    ci_control = proportion_confint(conv_control, n_control, alpha=0.05)
    ci_variant = proportion_confint(conv_variant, n_variant, alpha=0.05)

    is_significant = bool(p_value < 0.05)

    rev_control = control[control["converted"] == 1]["revenue"].mean()
    rev_variant = variant[variant["converted"] == 1]["revenue"].mean()

    return {
        "experiment": "checkout_button_test",
        "sample_sizes": {"control": n_control, "variant": n_variant},
        "conversions": {"control": int(conv_control), "variant": int(conv_variant)},
        "conversion_rates": {
            "control": round(rate_control, 4),
            "variant": round(rate_variant, 4)
        },
        "confidence_intervals": {
            "control": [round(ci_control[0], 4), round(ci_control[1], 4)],
            "variant": [round(ci_variant[0], 4), round(ci_variant[1], 4)]
        },
        "lift": {
            "absolute": round(absolute_lift, 4),
            "relative": round(relative_lift, 4)
        },
        "statistical_test": {
            "z_statistic": round(float(z_stat), 4),
            "p_value": round(float(p_value), 6),
            "alpha": 0.05,
            "is_significant": is_significant
        },
        "revenue": {
            "avg_order_value_control": round(float(rev_control), 2),
            "avg_order_value_variant": round(float(rev_variant), 2),
            "total_revenue_control": round(float(control["revenue"].sum()), 2),
            "total_revenue_variant": round(float(variant["revenue"].sum()), 2)
        },
        "recommendation": "Launch Variant B" if is_significant and rate_variant > rate_control else "Keep Control A"
    }

@app.get("/")
def root():
    return {"status": "A/B Testing API is running"}

@app.get("/experiment")
def get_experiment():
    try:
        df = load_data()
        return run_analysis(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/significance")
def get_significance():
    try:
        df = load_data()
        results = run_analysis(df)
        return {
            "is_significant": results["statistical_test"]["is_significant"],
            "p_value": results["statistical_test"]["p_value"],
            "z_statistic": results["statistical_test"]["z_statistic"],
            "recommendation": results["recommendation"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trends")
def get_trends():
    try:
        df = load_data()
        daily = df.groupby(["day", "group_name"])["converted"].agg(
            ["mean", "sum", "count"]
        ).reset_index()
        daily.columns = ["day", "group", "conversion_rate", "conversions", "users"]
        daily["conversion_rate"] = daily["conversion_rate"].round(4)
        return daily.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate")
def simulate_experiment(config: ExperimentConfig):
    try:
        np.random.seed(42)
        records = []
        for i in range(config.n_users):
            group = "control" if i % 2 == 0 else "variant"
            rate = config.control_rate if group == "control" else config.variant_rate
            converted = int(np.random.binomial(1, rate))
            records.append({"group": group, "converted": converted})

        df = pd.DataFrame(records)
        control = df[df["group"] == "control"]
        variant = df[df["group"] == "variant"]

        n_c, n_v = len(control), len(variant)
        conv_c = control["converted"].sum()
        conv_v = variant["converted"].sum()
        rate_c = conv_c / n_c
        rate_v = conv_v / n_v

        count = np.array([conv_v, conv_c])
        nobs = np.array([n_v, n_c])
        z_stat, p_value = proportions_ztest(count, nobs)

        return {
            "config": config.model_dump(),
            "results": {
                "control_rate": round(rate_c, 4),
                "variant_rate": round(rate_v, 4),
                "absolute_lift": round(rate_v - rate_c, 4),
                "relative_lift": round((rate_v - rate_c) / rate_c, 4),
                "p_value": round(float(p_value), 6),
                "is_significant": bool(p_value < 0.05),
                "recommendation": "Launch Variant" if p_value < 0.05 and rate_v > rate_c else "Keep Control"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))