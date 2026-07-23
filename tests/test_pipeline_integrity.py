"""
Tests de integridad sobre los DATOS REALES del pipeline.

Autocontenido: no depende de conftest.py ni de fixtures.
Se saltan automaticamente si no existen los parquet (p.ej. en CI).

Correr con: pytest tests/ -v
"""
from functools import lru_cache
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SILVER_PATH = ROOT / "data" / "silver" / "silver_sales_daily.parquet"
GOLD_DIR = ROOT / "data" / "gold"

requires_silver = pytest.mark.skipif(
    not SILVER_PATH.exists(),
    reason="No existe data/silver/. Corre: python pipelines/run_pipeline.py",
)
requires_gold = pytest.mark.skipif(
    not (GOLD_DIR / "fact_sales.parquet").exists(),
    reason="No existe data/gold/. Corre: python pipelines/run_pipeline.py",
)


@lru_cache(maxsize=None)
def load(name: str) -> pd.DataFrame:
    """Lee un parquet UNA sola vez y lo cachea para todos los tests."""
    path = SILVER_PATH if name == "silver" else GOLD_DIR / f"{name}.parquet"
    return pd.read_parquet(path)


# ---------------------------------------------------------------- SILVER ---

@requires_silver
def test_silver_no_fanout():
    """
    El test mas importante: los joins no deben duplicar ni perder filas.
    Filas esperadas = numero de series x numero de dias.
    """
    silver = load("silver")
    n_series = silver["id"].nunique()
    n_days = silver["date"].nunique()
    assert len(silver) == n_series * n_days, (
        f"Fan-out detectado: {len(silver):,} filas != "
        f"{n_series:,} series x {n_days:,} dias"
    )


@requires_silver
def test_silver_no_duplicate_grain():
    """El grano declarado (serie, dia) debe ser unico."""
    dupes = load("silver").duplicated(subset=["id", "date"]).sum()
    assert dupes == 0, f"{dupes:,} filas duplicadas en el grano (id, date)"


@requires_silver
def test_silver_keys_not_null():
    """Las claves nunca pueden ser nulas."""
    silver = load("silver")
    for key in ["id", "item_id", "store_id", "date"]:
        nulls = silver[key].isna().sum()
        assert nulls == 0, f"{nulls:,} nulos en columna clave '{key}'"


@requires_silver
def test_silver_units_non_negative():
    """No existen ventas negativas en el M5."""
    assert (load("silver")["units"] >= 0).all()


@requires_silver
def test_silver_price_positive_when_present():
    """Si hay precio, debe ser mayor que cero (nulo si es valido)."""
    priced = load("silver")["sell_price"].dropna()
    assert (priced > 0).all(), "Hay precios <= 0"


@requires_silver
def test_silver_revenue_consistent():
    """revenue debe ser exactamente units * sell_price cuando hay precio."""
    silver = load("silver")
    m = silver["sell_price"].notna()
    expected = silver.loc[m, "units"] * silver.loc[m, "sell_price"]
    assert ((silver.loc[m, "revenue"] - expected).abs() < 1e-6).all()


@requires_silver
def test_silver_complete_series():
    """Cada serie debe tener el mismo numero de dias: sin huecos temporales."""
    counts = load("silver").groupby("id").size()
    assert counts.nunique() == 1, (
        f"Series con distinto numero de dias: min={counts.min()}, max={counts.max()}"
    )


@requires_silver
def test_silver_flags_are_binary():
    """Los flags solo admiten 0 o 1."""
    silver = load("silver")
    for col in ["snap_flag", "is_weekend", "is_active"]:
        assert set(silver[col].unique()) <= {0, 1}, f"'{col}' tiene valores fuera de 0/1"


# ------------------------------------------------------------------ GOLD ---

@requires_gold
def test_gold_fact_matches_silver():
    """Gold no debe perder filas respecto a Silver."""
    assert len(load("fact_sales")) == len(load("silver"))


@requires_gold
def test_gold_dim_product_unique():
    """Una dimension debe tener una fila por entidad: sin duplicados."""
    assert load("dim_product")["item_id"].is_unique


@requires_gold
def test_gold_weekly_reconciles():
    """
    Test de RECONCILIACION: el agregado semanal debe sumar exactamente
    lo mismo que el detalle diario.
    """
    silver, weekly = load("silver"), load("weekly_category_sales")
    assert abs(weekly["total_units"].sum() - silver["units"].sum()) < 1
    assert abs(weekly["total_revenue"].sum() - silver["revenue"].sum()) < 0.01


@requires_gold
def test_gold_abc_covers_all_products():
    """Todo producto debe recibir una clase ABC."""
    abc, dim = load("abc_classification"), load("dim_product")
    assert len(abc) == len(dim)
    assert set(abc["abc_class"]) <= {"A", "B", "C"}


@requires_gold
def test_gold_abc_shares_sum_to_one():
    """Las participaciones de ingreso deben sumar 100%."""
    assert abs(load("abc_classification")["revenue_share"].sum() - 1.0) < 1e-6


@requires_gold
def test_gold_abc_is_sorted_by_revenue():
    """La clasificacion ABC exige orden descendente de ingreso."""
    assert load("abc_classification")["total_revenue"].is_monotonic_decreasing