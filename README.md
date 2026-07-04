<div align="center">

# 🔄 RetailFlow

### Supply Chain Forecasting & Analytics Platform

*End-to-end data platform: ingesta → pipeline medallion → forecasting → API → dashboard*

![Python](https://img.shields.io/badge/Python-3.11-blue)
![BigQuery](https://img.shields.io/badge/GCP-BigQuery-orange)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688)
![Angular](https://img.shields.io/badge/Angular-17-red)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

</div>

---

## 📌 Overview

RetailFlow is an end-to-end supply chain analytics platform built on the **M5 Forecasting dataset** (Walmart, 46M+ rows of daily sales across 5 years). It demonstrates the complete lifecycle of a data product:

1. **Data Engineering** — Raw ingestion and a medallion architecture pipeline (Bronze → Silver → Gold) on BigQuery
2. **Data Science** — Demand forecasting models (baseline → SARIMA/Prophet → LightGBM) with rigorous temporal evaluation
3. **Backend** — A FastAPI service serving real-time predictions and supply chain KPIs
4. **Frontend** — An Angular dashboard for interactive exploration
5. **DevOps** — Dockerized deployment with CI/CD via GitHub Actions

> **Why this project?** It shows the full picture — from messy raw data to a deployed, tested, documented product — not just an isolated notebook.

---

## 🏗️ Architecture

```
   M5 Raw Data          Medallion Pipeline           ML Layer          Serving Layer
  ┌───────────┐        ┌────────────────────┐      ┌───────────┐      ┌───────────┐
  │ CSV → GCS │  ───>  │ Bronze → Silver →  │ ───> │ Forecast  │ ───> │  FastAPI  │
  │           │        │       Gold         │      │  Models   │      │  Backend  │
  └───────────┘        │    (BigQuery)      │      └───────────┘      └─────┬─────┘
                       └────────────────────┘                              │
                                 │                                          v
                                 v                                    ┌───────────┐
                         ┌──────────────┐                             │  Angular  │
                         │ Data Quality │                             │ Dashboard │
                         │ (pytest +    │                             └───────────┘
                         │  pandera)    │
                         └──────────────┘
```

Full architecture docs in [`/docs/architecture.md`](docs/architecture.md).

---

## 📁 Repository Structure

```
retailflow/
├── pipelines/          # Data engineering (medallion architecture)
│   ├── bronze/         # Raw ingestion to GCS + BigQuery
│   ├── silver/         # Cleaning, normalization, enrichment
│   └── gold/           # Business aggregations + star schema
├── ml/                 # Data science
│   ├── notebooks/      # EDA and model experimentation
│   ├── src/            # Reusable training/eval code
│   └── models/         # Serialized trained models
├── api/                # FastAPI backend
│   ├── app/            # Endpoints, schemas, model serving
│   └── tests/          # API tests
├── frontend/           # Angular dashboard
├── tests/              # Data quality + integration tests
├── docs/               # Architecture, decisions, data dictionary
├── scripts/            # Utility scripts (setup, run, deploy)
└── .github/workflows/  # CI/CD pipelines
```

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/FerzzDark/retailflow.git
cd retailflow

# Setup environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run data quality tests
pytest tests/

# Run the API locally
cd api && uvicorn app.main:app --reload

# Run the frontend
cd frontend && npm install && ng serve
```

Detailed setup in [`/docs/setup.md`](docs/setup.md).

---

## 📊 Results

*(Se completa al terminar la Fase 2)*

| Model | MAPE | RMSE | WRMSSE |
|-------|------|------|--------|
| Naive baseline | — | — | — |
| SARIMA | — | — | — |
| LightGBM | — | — | — |

---

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Data Engineering** | Python, BigQuery, Google Cloud Storage, SQL |
| **Data Science** | pandas, LightGBM, Prophet, statsmodels, scikit-learn |
| **Data Quality** | pytest, pandera |
| **Backend** | FastAPI, Pydantic, uvicorn |
| **Frontend** | Angular 17, Chart.js, TypeScript |
| **DevOps** | Docker, GitHub Actions, Render/Cloud Run |

---

## 📈 Project Status

- [x] Phase 0 — Setup & foundations
- [ ] Phase 1 — Medallion pipeline
- [ ] Phase 2 — Forecasting models
- [ ] Phase 3 — API
- [ ] Phase 4 — Dashboard
- [ ] Phase 5 — Deployment

---

## 👤 Author

**Joaquin Arévalo Alcántara** — Computer Science student @ UPC
[LinkedIn](https://www.linkedin.com/in/joaquín-arévalo-alcántara-data) · [GitHub](https://github.com/FerzzDark)

## 📄 License

MIT — see [LICENSE](LICENSE)
