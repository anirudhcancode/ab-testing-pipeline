import pandas as pd
import numpy as np
from scipy import stats
from sqlalchemy import create_engine
from statsmodels.stats.proportion import proportions_ztest, proportion_confint
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
warnings.filterwarnings("ignore")

# Database connection
DB_USER = "fraud_user"
DB_PASSWORD = "fraud_pass"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "fraud_db"

engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

def load_data(engine) -> pd.DataFrame:
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM ab_experiment", conn)
    print(f"Loaded {len(df)} rows from PostgreSQL")
    return df

def compute_stats(df: pd.DataFrame) -> dict:
    control = df[df["group_name"] == "control"]
    variant = df[df["group_name"] == "variant"]

    # Basic counts
    n_control = len(control)
    n_variant = len(variant)
    conv_control = control["converted"].sum()
    conv_variant = variant["converted"].sum()

    # Conversion rates
    rate_control = conv_control / n_control
    rate_variant = conv_variant / n_variant

    # Absolute and relative lift
    absolute_lift = rate_variant - rate_control
    relative_lift = absolute_lift / rate_control

    # Z-test for proportions
    count = np.array([conv_variant, conv_control])
    nobs = np.array([n_variant, n_control])
    z_stat, p_value = proportions_ztest(count, nobs)

    # Confidence intervals (95%)
    ci_control = proportion_confint(conv_control, n_control, alpha=0.05)
    ci_variant = proportion_confint(conv_variant, n_variant, alpha=0.05)

    # Statistical significance
    alpha = 0.05
    is_significant = p_value < alpha

    # Revenue analysis
    rev_control = control[control["converted"] == 1]["revenue"].mean()
    rev_variant = variant[variant["converted"] == 1]["revenue"].mean()
    total_rev_control = control["revenue"].sum()
    total_rev_variant = variant["revenue"].sum()

    results = {
        "experiment": "checkout_button_test",
        "n_control": n_control,
        "n_variant": n_variant,
        "conversions_control": int(conv_control),
        "conversions_variant": int(conv_variant),
        "rate_control": round(rate_control, 4),
        "rate_variant": round(rate_variant, 4),
        "absolute_lift": round(absolute_lift, 4),
        "relative_lift": round(relative_lift, 4),
        "z_statistic": round(z_stat, 4),
        "p_value": round(p_value, 6),
        "ci_control_lower": round(ci_control[0], 4),
        "ci_control_upper": round(ci_control[1], 4),
        "ci_variant_lower": round(ci_variant[0], 4),
        "ci_variant_upper": round(ci_variant[1], 4),
        "is_significant": is_significant,
        "confidence_level": "95%",
        "avg_revenue_control": round(rev_control, 2),
        "avg_revenue_variant": round(rev_variant, 2),
        "total_revenue_control": round(total_rev_control, 2),
        "total_revenue_variant": round(total_rev_variant, 2),
        "recommendation": "Launch Variant B" if is_significant and rate_variant > rate_control else "Keep Control A"
    }
    return results

def print_results(results: dict):
    print("\n" + "="*50)
    print("A/B TEST RESULTS")
    print("="*50)
    print(f"\nExperiment: {results['experiment']}")
    print(f"\nSample sizes:")
    print(f"  Control:  {results['n_control']:,} users")
    print(f"  Variant:  {results['n_variant']:,} users")
    print(f"\nConversion rates:")
    print(f"  Control:  {results['rate_control']*100:.2f}%  [{results['ci_control_lower']*100:.2f}% - {results['ci_control_upper']*100:.2f}%]")
    print(f"  Variant:  {results['rate_variant']*100:.2f}%  [{results['ci_variant_lower']*100:.2f}% - {results['ci_variant_upper']*100:.2f}%]")
    print(f"\nLift:")
    print(f"  Absolute: +{results['absolute_lift']*100:.2f}%")
    print(f"  Relative: +{results['relative_lift']*100:.2f}%")
    print(f"\nStatistical test:")
    print(f"  Z-statistic: {results['z_statistic']}")
    print(f"  P-value:     {results['p_value']}")
    print(f"  Significant: {results['is_significant']} (alpha=0.05)")
    print(f"\nRevenue:")
    print(f"  Avg order value Control: ${results['avg_revenue_control']}")
    print(f"  Avg order value Variant: ${results['avg_revenue_variant']}")
    print(f"  Total revenue Control:   ${results['total_revenue_control']:,.2f}")
    print(f"  Total revenue Variant:   ${results['total_revenue_variant']:,.2f}")
    print(f"\nRECOMMENDATION: {results['recommendation']}")
    print("="*50)

def plot_results(df: pd.DataFrame, results: dict):
    os.makedirs("data", exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("A/B Test Results — Checkout Button", fontsize=14, fontweight='bold')

    # Plot 1 — Conversion rates with confidence intervals
    groups = ["Control A\n(Green)", "Variant B\n(Orange)"]
    rates = [results["rate_control"], results["rate_variant"]]
    errors = [
        results["rate_control"] - results["ci_control_lower"],
        results["rate_variant"] - results["ci_variant_lower"]
    ]
    colors = ["#2ecc71", "#e67e22"]
    bars = axes[0].bar(groups, rates, color=colors, width=0.5, yerr=errors,
                       capsize=8, error_kw={"linewidth": 2})
    axes[0].set_title("Conversion Rate\nwith 95% Confidence Intervals")
    axes[0].set_ylabel("Conversion Rate")
    axes[0].set_ylim(0, 0.20)
    for bar, rate in zip(bars, rates):
        axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.003,
                    f"{rate*100:.2f}%", ha="center", fontweight="bold")

    # Plot 2 — Daily conversion rates
    daily = df.groupby(["day", "group_name"])["converted"].mean().reset_index()
    for group, color, label in [("control", "#2ecc71", "Control A"), ("variant", "#e67e22", "Variant B")]:
        data = daily[daily["group_name"] == group]
        axes[1].plot(data["day"], data["converted"], color=color, label=label,
                    linewidth=2, marker="o", markersize=4)
    axes[1].set_title("Daily Conversion Rate\nOver Experiment Duration")
    axes[1].set_xlabel("Day")
    axes[1].set_ylabel("Conversion Rate")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # Plot 3 — Revenue comparison
    rev_data = df[df["converted"] == 1].groupby("group_name")["revenue"].mean()
    rev_colors = ["#2ecc71", "#e67e22"]
    rev_bars = axes[2].bar(["Control A", "Variant B"],
                           [results["avg_revenue_control"], results["avg_revenue_variant"]],
                           color=rev_colors, width=0.5)
    axes[2].set_title("Average Order Value\nper Converted User")
    axes[2].set_ylabel("Average Revenue ($)")
    for bar, val in zip(rev_bars, [results["avg_revenue_control"], results["avg_revenue_variant"]]):
        axes[2].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f"${val:.2f}", ha="center", fontweight="bold")

    plt.tight_layout()
    plt.savefig("data/ab_test_results.png", dpi=150, bbox_inches="tight")
    print("\nChart saved to data/ab_test_results.png")

if __name__ == "__main__":
    df = load_data(engine)
    results = compute_stats(df)
    print_results(results)
    plot_results(df, results)
    print("\nPhase 2 complete!")