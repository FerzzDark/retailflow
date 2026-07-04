# Architecture

## Overview
RetailFlow follows a layered architecture separating data engineering, ML, serving, and presentation.

## Medallion Architecture

### Bronze Layer (Raw)
- Ingests raw M5 CSVs into Google Cloud Storage
- Loads into BigQuery with no transformation
- Preserves original data for reproducibility
- Tables: bronze_sales, bronze_calendar, bronze_prices

### Silver Layer (Cleaned)
- Joins sales, calendar, and price data
- Unpivots wide day-columns into long daily grain
- Handles nulls, standardizes types, parses dates
- Enriches with calendar features
- Table: silver_sales_daily

### Gold Layer (Business-ready)
- Business aggregations by category, store, week
- Supply chain KPIs: turnover, trend, seasonality
- Star schema: dim_product, dim_store, dim_calendar, fact_sales

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Medallion architecture | Industry standard; clear raw/clean/business separation |
| BigQuery | Serverless, scales to 46M rows, free tier sufficient |
| LightGBM | Top performer on M5; handles many series efficiently |
| Temporal validation | Time series need chronological splits, never random |
| FastAPI | Async, auto Swagger docs, Pydantic validation |
| Monorepo | Unified narrative for portfolio |
