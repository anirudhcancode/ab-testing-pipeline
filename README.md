# A/B Testing Analytics Pipeline

An end-to-end A/B testing system that simulates e-commerce experiments, runs statistical significance tests, and serves results via a REST API.

## Scenario

Testing two versions of a checkout button:
- Control A: Green button — "Complete Purchase" (baseline: 12% conversion)
- Variant B: Orange button — "Buy Now" (target: 14.5% conversion)

## Results

Metric             | Value
Conversion Control | 11.56%
Conversion Variant | 14.60%
Absolute Lift      | +3.04%
Relative Lift      | +26.30%
Z-statistic        | 4.508
P-value            | 0.000007
Significant        | Yes (alpha=0.05)
Recommendation     | Launch Variant B

## Architecture

Simulated Data → PostgreSQL → Statistical Analysis → FastAPI

## Tech Stack

- Statistics: scipy, statsmodels (z-test, confidence intervals)
- Data: pandas, numpy, PostgreSQL (Docker)
- Visualization: matplotlib, seaborn
- API: FastAPI, Uvicorn

## API Endpoints

GET  /             — Health check
GET  /experiment   — Full experiment results with statistical analysis
GET  /significance — Significance result and recommendation only
GET  /trends       — Daily conversion rates for both groups
POST /simulate     — Run a new simulation with custom parameters

## Setup

Prerequisites: Python 3.10+, Docker Desktop

Run PostgreSQL:
docker compose up -d

Install dependencies:
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Run the pipeline:
python src/simulate.py
python src/analyze.py

Start the API:
uvicorn api.main:app --reload

Test:
curl http://127.0.0.1:8000/experiment
curl http://127.0.0.1:8000/significance

## Key Concepts

- Z-test: tests whether the difference in conversion rates is statistically significant
- P-value: probability the result occurred by chance (below 0.05 = significant)
- Confidence interval: range where the true conversion rate lies with 95% certainty
- Absolute lift: raw difference in conversion rates (+3.04%)
- Relative lift: percentage improvement over control (+26.30%)