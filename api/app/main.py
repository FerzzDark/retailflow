"""
RetailFlow API — serves demand forecasts and supply chain KPIs.

Run locally with: uvicorn app.main:app --reload
Swagger docs at: http://localhost:8000/docs
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI(
    title="RetailFlow API",
    description="Demand forecasting and supply chain analytics for retail",
    version="0.1.0",
)


class ForecastPoint(BaseModel):
    date: str
    predicted_units: float


class ForecastResponse(BaseModel):
    item_id: str
    store_id: str
    horizon_days: int
    forecast: List[ForecastPoint]


class KPIResponse(BaseModel):
    store_id: str
    total_revenue: float
    avg_daily_units: float
    abc_a_products: int


@app.get("/health")
def health_check():
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/forecast/{item_id}", response_model=ForecastResponse)
def get_forecast(item_id: str, store_id: str = "CA_1", horizon: int = 28):
    """
    Return a demand forecast for a given product in a given store.

    In production this loads the trained model and generates predictions.
    Currently returns a stub structure until Phase 2/3 wiring is complete.
    """
    if horizon < 1 or horizon > 90:
        raise HTTPException(status_code=400, detail="Horizon must be 1-90 days")

    # Placeholder forecast — replaced by real model in Phase 3
    forecast = [
        ForecastPoint(date=f"2016-05-{d:02d}", predicted_units=0.0)
        for d in range(1, min(horizon, 28) + 1)
    ]
    return ForecastResponse(
        item_id=item_id,
        store_id=store_id,
        horizon_days=horizon,
        forecast=forecast,
    )


@app.get("/kpis/{store_id}", response_model=KPIResponse)
def get_kpis(store_id: str):
    """Return supply chain KPIs for a given store."""
    # Placeholder — reads from BigQuery gold layer in Phase 3
    return KPIResponse(
        store_id=store_id,
        total_revenue=0.0,
        avg_daily_units=0.0,
        abc_a_products=0,
    )
