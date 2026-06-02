# A/B Testing & Experimentation Analytics Pipeline

An end-to-end A/B testing platform that simulates e-commerce experiments, applies rigorous statistical significance testing, and serves all results via a live REST API.

## The Problem

How do you know if a product change actually works? If you change something for everyone and sales go up, was it the change — or a holiday, a competitor's sale, or random variation? Without a controlled experiment, you cannot know. A/B testing solves this by showing two versions simultaneously to randomly split groups, keeping everything else constant. This is how Amazon, Netflix, and Google make product decisions.

## The Experiment

Tested two checkout button designs across 10,000 users over 14 days:
- **Control A:** Green button — "Complete Purchase" (baseline: ~12% conversion)
- **Variant B:** Orange button — "Buy Now" (target: ~14.5% conversion)

## Results

| Metric | Control A (Green) | Variant B (Orange) |
|---|---|---|
| Conversion Rate | 11.56% | **14.60% (+26.3%)** |
| Total Revenue | $51,792 | **$60,321 (+$8,528)** |
| Revenue per User | $10.36 | **$12.06** |
| Avg Order Value | $89.61 | $82.63 |
| Conversions | 578 / 5,000 | **730 / 5,000** |
| Z-statistic | — | 4.508 |
| P-value | — | 0.000007 |

**Recommendation: Launch Variant B** — 26.3% relative conversion lift confirmed statistically significant.

## The Hidden Insight

Variant B had a **lower** average order value ($82.63 vs $89.61) but **higher** total revenue. This is why conversion rate alone is an incomplete metric. The correct primary metric is **revenue per user** — which Variant B wins decisively ($12.06 vs $10.36). This distinction separates good analysis from great analysis.

## Live Demo

**API:** https://ab-testing-pipeline.onrender.com/docs

**Demo Page:** https://anirudhcancode.github.io/portfolio/ab-demo.html

## Architecture
Statistical Distributions (Beta, Log-Normal)
↓
Simulated Experiment Data (10,000 users, 14 days)
↓
PostgreSQL (Cloud — Render)
↓
Z-Test + Confidence Intervals + Lift Metrics
↓
FastAPI REST Endpoints
## Key Statistical Concepts

**Z-test for proportions**
Used to determine whether the difference in conversion rates is statistically significant or random chance.

**P-value: 0.000007**
If the two buttons were identical, you would observe a gap this large by luck only 0.0007% of the time. The standard threshold is 5% (p < 0.05). We are 7,000x more significant than the threshold.

**Z-statistic: 4.508**
4.5 standard deviations from zero. Anything above 1.96 is significant at 95% confidence.

**Statistical power**
The probability a test detects a real difference if one exists. Standard is 80%. Running too few users = underpowered test = missing real improvements.

**Novelty effect**
Users sometimes behave differently just because something looks new. Running for 14 days across multiple days of the week controls for this. The /trends endpoint shows daily conversion rates to check.

**Absolute vs relative lift**
- Absolute: 14.60% - 11.56% = 3.04 percentage points
- Relative: 3.04 / 11.56 = 26.3% improvement over baseline
- Always report both — relative lift sounds more impressive but absolute tells you the real business impact.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | / | Health check |
| GET | /experiment | Full results with statistical analysis |
| GET | /significance | Significance result and recommendation |
| GET | /trends | Daily conversion rates for both groups |
| POST | /simulate | Run new simulation with custom parameters |

## Tech Stack

| Layer | Technology |
|---|---|
| Statistics | statsmodels (z-test), scipy (confidence intervals) |
| Data | pandas, numpy |
| Storage | PostgreSQL (Render) |
| API | FastAPI, Uvicorn |
| Deployment | Render |

## Setup

```bash
# Start PostgreSQL
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

## Dataset

Simulated using realistic statistical distributions:
- Conversion rates: Beta distribution
- Order values: Log-normal distribution (matches real e-commerce data)

## Portfolio

https://anirudhcancode.github.io/portfolio