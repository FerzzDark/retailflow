"""Tests for the RetailFlow API."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_forecast_structure():
    resp = client.get("/forecast/FOODS_1_001?store_id=CA_1&horizon=28")
    assert resp.status_code == 200
    data = resp.json()
    assert data["item_id"] == "FOODS_1_001"
    assert data["horizon_days"] == 28
    assert isinstance(data["forecast"], list)


def test_forecast_invalid_horizon():
    resp = client.get("/forecast/FOODS_1_001?horizon=200")
    assert resp.status_code == 400
