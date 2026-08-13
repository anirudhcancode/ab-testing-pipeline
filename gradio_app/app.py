import os
import gradio as gr
import numpy as np
import pandas as pd
from statsmodels.stats.proportion import proportions_ztest, proportion_confint

# Same data-generation approach as src/simulate.py's simulate_experiment()
# (binomial conversion draws, exponential(85) revenue on conversion) and the
# same statistical logic as src/analyze.py's compute_stats() — just
# parameterized by the sliders instead of fixed config, and run in memory
# instead of round-tripping through PostgreSQL.


def simulate(control_rate, variant_rate, n_per_group):
    n_per_group = int(n_per_group)
    control_conv = np.random.binomial(1, control_rate, n_per_group)
    variant_conv = np.random.binomial(1, variant_rate, n_per_group)

    control_rev = np.where(control_conv == 1, np.random.exponential(85, n_per_group), 0.0)
    variant_rev = np.where(variant_conv == 1, np.random.exponential(85, n_per_group), 0.0)

    df = pd.DataFrame({
        "group_name": ["control"] * n_per_group + ["variant"] * n_per_group,
        "converted": np.concatenate([control_conv, variant_conv]),
        "revenue": np.concatenate([control_rev, variant_rev]),
    })
    return df


def compute_stats(df: pd.DataFrame) -> dict:
    control = df[df["group_name"] == "control"]
    variant = df[df["group_name"] == "variant"]

    n_control = len(control)
    n_variant = len(variant)
    conv_control = control["converted"].sum()
    conv_variant = variant["converted"].sum()

    rate_control = conv_control / n_control
    rate_variant = conv_variant / n_variant

    absolute_lift = rate_variant - rate_control
    relative_lift = absolute_lift / rate_control if rate_control > 0 else float("nan")

    count = np.array([conv_variant, conv_control])
    nobs = np.array([n_variant, n_control])
    z_stat, p_value = proportions_ztest(count, nobs)

    ci_control = proportion_confint(conv_control, n_control, alpha=0.05)
    ci_variant = proportion_confint(conv_variant, n_variant, alpha=0.05)

    is_significant = p_value < 0.05

    return {
        "n_control": n_control,
        "n_variant": n_variant,
        "rate_control": rate_control,
        "rate_variant": rate_variant,
        "absolute_lift": absolute_lift,
        "relative_lift": relative_lift,
        "z_statistic": z_stat,
        "p_value": p_value,
        "ci_control": ci_control,
        "ci_variant": ci_variant,
        "is_significant": is_significant,
        "recommendation": "Launch Variant B" if is_significant and rate_variant > rate_control else "Keep Control A",
    }


def run(control_rate_pct, variant_rate_pct, n_per_group):
    control_rate = control_rate_pct / 100
    variant_rate = variant_rate_pct / 100

    df = simulate(control_rate, variant_rate, n_per_group)
    r = compute_stats(df)

    verdict = (
        f"✅ **Statistically significant at 95% confidence** (p = {r['p_value']:.6f})"
        if r["is_significant"]
        else f"⚪ **Not statistically significant at 95% confidence** (p = {r['p_value']:.6f})"
    )

    result_md = f"""
### {verdict}

**Recommendation:** {r['recommendation']}

| Metric | Control | Variant |
|---|---|---|
| Sample size | {r['n_control']:,} | {r['n_variant']:,} |
| Conversion rate | {r['rate_control']*100:.2f}% | {r['rate_variant']*100:.2f}% |
| 95% CI | [{r['ci_control'][0]*100:.2f}%, {r['ci_control'][1]*100:.2f}%] | [{r['ci_variant'][0]*100:.2f}%, {r['ci_variant'][1]*100:.2f}%] |

**Lift:** {r['absolute_lift']*100:+.2f}pp absolute · {r['relative_lift']*100:+.2f}% relative

**Z-statistic:** {r['z_statistic']:.4f} · **P-value:** {r['p_value']:.6f}
"""
    return result_md


description = """
Set a control conversion rate, a treatment (variant) conversion rate, and a
sample size per group, then run the simulation. This generates synthetic
per-user conversion data (binomial draws at the rates you set — same approach
as `src/simulate.py`) and runs the exact `compute_stats()` z-test logic from
`src/analyze.py` on it live, instead of only showing the one fixed seeded
result on the main demo page.

Data is freshly randomized on every run, so re-running the same inputs will
show natural sampling variance — that's expected, not a bug.
"""

demo = gr.Interface(
    fn=run,
    inputs=[
        gr.Slider(1, 50, value=12, step=0.5, label="Control Conversion Rate (%)"),
        gr.Slider(1, 50, value=14.5, step=0.5, label="Treatment Conversion Rate (%)"),
        gr.Slider(100, 20000, value=5000, step=100, label="Sample Size (per group)"),
    ],
    outputs=gr.Markdown(label="Results"),
    title="A/B Testing — Live Statistical Simulation",
    description=description,
    live=True,
    flagging_mode="never",
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))
