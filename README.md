# A/B Testing & Experimentation Analytics Pipeline

An end-to-end A/B testing platform that simulates e-commerce experiments, applies statistical significance testing, and serves results via a REST API.

## Scenario

Testing two versions of a checkout button across 10,000 users over 14 days:
- Control A: Green button — "Complete Purchase" (baseline: 12% conversion)
- Variant B: Orange button — "Buy Now" (target: 14.5% conversion)

## Results

| Metric | Control A | Variant B |
|---|---|---|
| Conversion Rate | 11.56% | 14.60% |
| Total Revenue | $51,792 | $60,321 |
| Revenue per User | $10.36 | $12.06 |
| Z-statistic | — | 4.508 |
| P-value | — | 0.000007 |
| Significant | — | Yes |

**Recommendation: Launch Variant B** — 26.3% relative conversion lift confirmed statistically significant.

## Architecture

Simulated Data → PostgreSQL → Statistical Analysis → FastAPI

## Tech Stack

- Statistics: statsmodels (z-test, confidence intervals), scipy
- Data: pandas, numpy, PostgreSQL (Docker)
- Visualization: matplotlib, seaborn
- API: FastAPI, Uvicorn

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | / | Health check |
| GET | /experiment | Full results with statistical analysis |
| GET | /significance | Significance result and recommendation |
| GET | /trends | Daily conversion rates for both groups |
| POST | /simulate | Run new simulation with custom parameters |

## Live Demo

https://ab-testing-pipeline.onrender.com/docs

## Setup

```bash
# Run PostgreSQL
docker compose up -d

# Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run pipeline
python src/simulate.py
python src/analyze.py

# Start API
uvicorn api.main:app --reload
```

## Key Concepts

- **Z-test**: Tests whether the difference in conversion rates is statistically significant
- **P-value**: Probability the result occurred by chance (below 0.05 = significant)
- **Confidence interval**: Range where the true conversion rate lies with 95% certainty
- **Absolute lift**: Raw difference in conversion rates (+3.04 percentage points)
- **Relative lift**: Percentage improvement over control (+26.30%)
- **Revenue per user**: The correct primary metric — conversion rate alone is incomplete