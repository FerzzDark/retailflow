<div align="center">

# RetailFlow

### Supply Chain Forecasting & Analytics Platform

*End-to-end data platform: ingesta → pipeline medallion → forecasting → API → dashboard*

![Python](https://img.shields.io/badge/Python-3.11-blue)
![pandas](https://img.shields.io/badge/pandas-2.2-150458)
![Parquet](https://img.shields.io/badge/storage-Parquet-50ABF1)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688)
![Tests](https://img.shields.io/badge/tests-19%20passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

</div>

---

## Overview

RetailFlow is an end-to-end supply chain analytics platform built on the **M5 Forecasting dataset** (Walmart — daily unit sales across 5 years and 3 US states). It demonstrates the complete lifecycle of a data product:

1. **Data Engineering** — Medallion pipeline (Bronze → Silver → Gold) processing 2.7M daily sales records
2. **Data Quality** — 19 automated tests including join-cardinality and reconciliation checks
3. **Data Science** — Demand forecasting (baseline → statistical → LightGBM) with temporal validation
4. **Backend** — FastAPI service serving predictions and supply chain KPIs
5. **Frontend** — Angular dashboard for interactive exploration

> **Why this project?** It shows the full picture — from raw wide-format CSVs to a tested, documented, reproducible data product — not just an isolated notebook.

---

## Architecture

```
   M5 Raw CSVs           Medallion Pipeline            ML Layer          Serving Layer
  ┌───────────┐        ┌────────────────────┐       ┌───────────┐      ┌───────────┐
  │ data/raw/ │  ───>  │ Bronze → Silver →  │  ───> │ Forecast  │ ───> │  FastAPI  │
  │  (Kaggle) │        │       Gold         │       │  Models   │      │  Backend  │
  └───────────┘        │  (pandas/Parquet)  │       └───────────┘      └─────┬─────┘
                       └────────────────────┘                                │
                                 │                                            v
                                 v                                      ┌───────────┐
                         ┌──────────────┐                               │  Angular  │
                         │ Data Quality │                               │ Dashboard │
                         │ (pytest +    │                               └───────────┘
                         │  pandera)    │
                         └──────────────┘
```

The pipeline runs **locally on pandas + Parquet**. A BigQuery migration path is kept in
`pipelines/silver/transform.sql` and `pipelines/gold/aggregate.sql` for Phase 5.

Full architecture docs in [`/docs/architecture.md`](docs/architecture.md).

---

## Quick Start

```bash
# Clone
git clone https://github.com/FerzzDark/retailflow.git
cd retailflow

# Environment
python -m venv venv
venv\Scripts\activate          # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt

# Download the M5 dataset from Kaggle into data/raw/
# https://www.kaggle.com/c/m5-forecasting-accuracy/data

# Run the full medallion pipeline
python pipelines/run_pipeline.py

# Or start from a specific layer
python pipelines/run_pipeline.py --from silver

# Run the test suite
pytest tests/ -v
```

---

## Pipeline Results

Development scope: category **FOODS**, store **CA_1** (configurable in `pipelines/bronze/ingest_local.py`).

| Layer | Output | Rows | Time |
|-------|--------|------:|-----:|
| **Bronze** | 3 raw tables → Parquet | 1,437 series × 1,913 days | 6.4s |
| **Silver** | `silver_sales_daily` | 2,748,981 | 4.1s |
| **Gold** | star schema + 2 business views | 2,748,981 facts | 1.3s |
| | | **Total** | **11.9s** |

**Coverage:** 2011-01-29 → 2016-04-24 · 1,437 products · 274 weeks · 80.8% of
product-days have an active price (the rest are products not yet introduced).

### ABC Classification (Pareto)

| Class | Products | % of catalog | % of revenue |
|-------|---------:|-------------:|-------------:|
| **A** | 559 | 38.9% | 80.0% |
| **B** | 466 | 32.4% | 15.0% |
| **C** | 412 | 28.7% | 5.0% |

> **Finding:** FOODS shows a *flatter* Pareto curve than the textbook 80/20 — it takes
> 39% of the catalog to reach 80% of revenue. This is consistent with grocery demand
> being broadly distributed across staples rather than concentrated in a few hero SKUs.
> Running the same analysis on HOBBIES would be expected to concentrate further.

---

## Data Quality

19 tests across two levels:

- **Contract tests** (`test_data_quality.py`) — pandera schemas validated against synthetic
  data. Always run, including in CI.
- **Integrity tests** (`test_pipeline_integrity.py`) — run against the real 2.7M-row output.
  Skip cleanly when `data/` is absent, so CI stays green without shipping datasets.

Notable checks:

| Test | What it catches |
|------|-----------------|
| `test_silver_no_fanout` | Joins silently multiplying rows via incomplete keys |
| `test_silver_complete_series` | Temporal gaps — series with missing days |
| `test_gold_weekly_reconciles` | Aggregates that don't sum back to the daily detail |
| `test_silver_revenue_consistent` | Derived metrics drifting from their inputs |

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Medallion architecture** | Bronze stays byte-faithful to source, so any bug downstream is reprocessable without re-downloading |
| **Local pandas + Parquet first** | Fast iteration, no cloud credentials or cost during development; BigQuery migration deferred to Phase 5 |
| **Parquet over CSV** | Columnar, compressed, and type-preserving. Measured: reading 3 Parquet + melting 2.7M rows (4.1s) is *faster* than parsing the source CSVs (6.4s) |
| **Subset for development** | FOODS × CA_1 keeps the full pipeline under 12s, enabling tight feedback loops |
| **ABC by cumulative revenue** | Classifies by Pareto contribution, not percentile-of-count — the latter forces an 80/20 result instead of measuring it |
| **Skippable integrity tests** | Real-data tests locally, green CI remotely, without committing datasets |
| **Monorepo** | Unified narrative from ingestion to dashboard |

---

## Repository Structure

```
retailflow/
├── pipelines/
│   ├── bronze/ingest_local.py       # Raw CSV → Parquet (subset scoping)
│   ├── silver/transform_local.py    # Unpivot + joins + features
│   ├── gold/aggregate_local.py      # Star schema + KPIs + ABC
│   ├── run_pipeline.py              # Orchestrator (--from LAYER)
│   └── */*.sql                      # BigQuery migration path (Phase 5)
├── ml/                              # Forecasting models
├── api/                             # FastAPI backend
├── frontend/                        # Angular dashboard
├── tests/                           # Contract + integrity tests
├── docs/                            # Architecture, data dictionary
└── .github/workflows/ci.yml         # CI
```

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Data Engineering** | Python, pandas, Parquet · BigQuery (Phase 5) |
| **Data Quality** | pytest, pandera |
| **Data Science** | LightGBM, Prophet, statsmodels, scikit-learn |
| **Backend** | FastAPI, Pydantic, uvicorn |
| **Frontend** | Angular, Chart.js, TypeScript |
| **DevOps** | GitHub Actions, Docker |

---

## Project Status

- [x] **Phase 0** — Setup, structure, CI
- [x] **Phase 1** — Medallion pipeline + data quality (2.7M rows, 19 tests)
- [ ] **Phase 2** — Forecasting models (baseline → SARIMA/Prophet → LightGBM)
- [ ] **Phase 3** — API serving real predictions
- [ ] **Phase 4** — Angular dashboard
- [ ] **Phase 5** — BigQuery migration + deployment

### Forecasting Results

*Populated in Phase 2.*

| Model | MAPE | RMSE | WRMSSE |
|-------|------|------|--------|
| Naive baseline | — | — | — |
| SARIMA | — | — | — |
| LightGBM | — | — | — |

---

## Author

**Joaquin Arévalo Alcántara** — Computer Science student @ UPC
[LinkedIn](https://www.linkedin.com/in/joaquín-arévalo-alcántara-data) · [GitHub](https://github.com/FerzzDark)

## 📄 License

MIT — see [LICENSE](LICENSE)