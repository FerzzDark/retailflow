"""
Modelos baseline de forecasting + ejecucion de la comparativa.

Uso:
    python ml/src/run_baselines.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ml.src.evaluation import comparison_table, evaluate, temporal_split

SILVER_PATH = ROOT / "data" / "silver" / "silver_sales_daily.parquet"
HORIZON = 28


def load_matrix() -> pd.DataFrame:
    """
    Matriz de series: filas = producto-tienda, columnas = fecha.
    Este pivot es lo contrario del melt de Silver -- y esta bien: Silver es
    formato de almacenamiento, esto es formato de modelado.
    """
    silver = pd.read_parquet(SILVER_PATH, columns=["id", "date", "units"])
    return silver.pivot(index="id", columns="date", values="units").sort_index(axis=1)


def revenue_weights(matrix_index: pd.Index, last_days: int = 28) -> np.ndarray:
    """Peso economico = ingreso en los ultimos dias del train (criterio M5)."""
    silver = pd.read_parquet(SILVER_PATH, columns=["id", "date", "revenue"])
    cutoff_end = silver["date"].max() - pd.Timedelta(days=HORIZON)
    cutoff_start = cutoff_end - pd.Timedelta(days=last_days)
    window = silver[(silver["date"] > cutoff_start) & (silver["date"] <= cutoff_end)]
    rev = window.groupby("id")["revenue"].sum().reindex(matrix_index).fillna(0)
    total = rev.sum()
    return (rev / total).to_numpy() if total > 0 else np.full(len(rev), 1 / len(rev))


# --------------------------------------------------------------- BASELINES ---

def forecast_zero(train, horizon):
    """Control: predecir siempre cero."""
    return np.zeros((train.shape[0], horizon))


def forecast_naive(train, horizon):
    """Repite el ultimo valor observado."""
    return np.repeat(train[:, -1][:, None], horizon, axis=1)


def forecast_seasonal_naive(train, horizon, period=7):
    """Repite ciclicamente la ultima semana: captura estacionalidad sin parametros."""
    tiled = np.tile(train[:, -period:], (1, int(np.ceil(horizon / period))))
    return tiled[:, :horizon]


def forecast_moving_average(train, horizon, window=28):
    """Media de los ultimos `window` dias, constante en el horizonte."""
    return np.repeat(train[:, -window:].mean(axis=1)[:, None], horizon, axis=1)


def main() -> int:
    if not SILVER_PATH.exists():
        print("No existe data/silver/. Corre: python pipelines/run_pipeline.py")
        return 1

    matrix = load_matrix()
    print(f"BASELINES | series: {matrix.shape[0]:,}  dias: {matrix.shape[1]:,}")

    train_df, test_df = temporal_split(matrix, horizon=HORIZON)
    train = train_df.to_numpy(dtype=float)
    y_true = test_df.to_numpy(dtype=float)

    print(f"BASELINES | train: {train_df.columns.min().date()} -> {train_df.columns.max().date()}")
    print(f"BASELINES | test : {test_df.columns.min().date()} -> {test_df.columns.max().date()}")

    weights = revenue_weights(matrix.index)

    models = {
        "zero": forecast_zero(train, HORIZON),
        "naive": forecast_naive(train, HORIZON),
        "seasonal_naive_7": forecast_seasonal_naive(train, HORIZON, period=7),
        "moving_average_7": forecast_moving_average(train, HORIZON, window=7),
        "moving_average_28": forecast_moving_average(train, HORIZON, window=28),
    }

    rows = [evaluate(n, y_true, p, train, weights) for n, p in models.items()]
    table = comparison_table(rows)

    print("\nBASELINES | Comparativa (menor es mejor; RMSSE < 1 supera al naive):\n")
    print(table.to_string(index=False))

    best = table.iloc[0]
    print(f"\nBASELINES | Mejor baseline: {best['model']} (RMSSE={best['RMSSE']})")
    print("BASELINES | Este es el numero que cualquier modelo de Fase 2 debe superar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())