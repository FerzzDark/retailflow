"""
Evaluacion de forecasting: split temporal y metricas.

Este modulo NO entrena nada. Define el "juez" antes que los modelos.

Convencion de formas (shapes):
    y_true, y_pred -> arrays (n_series, horizon)
    train          -> array  (n_series, n_train_days)
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ------------------------------------------------------------------ SPLIT ---

def temporal_split(matrix: pd.DataFrame, horizon: int = 28):
    """
    Corta la serie por FECHA, no al azar.

    matrix: DataFrame (filas = series, columnas = fechas ordenadas)
    Devuelve (train, test) donde test son los ultimos `horizon` dias.
    """
    if matrix.shape[1] <= horizon:
        raise ValueError(f"Se necesitan mas de {horizon} dias; hay {matrix.shape[1]}.")
    return matrix.iloc[:, :-horizon], matrix.iloc[:, -horizon:]


# ---------------------------------------------------------------- METRICAS ---

def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Error absoluto medio. En unidades del negocio."""
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Raiz del error cuadratico medio. Penaliza mas los errores grandes."""
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    CUIDADO: indefinido cuando y_true = 0. En retail intermitente eso pasa
    todo el tiempo, asi que se ignoran esos puntos -- lo que sesga la metrica.
    Se reporta por costumbre, pero NO es el criterio principal aqui.
    """
    mask = y_true != 0
    if mask.sum() == 0:
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def smape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """MAPE simetrico: acotado en [0, 200] y definido cuando y_true = 0."""
    denom = (np.abs(y_true) + np.abs(y_pred)) / 2
    mask = denom != 0
    if mask.sum() == 0:
        return 0.0
    return float(np.mean(np.abs(y_true[mask] - y_pred[mask]) / denom[mask]) * 100)


def rmsse(y_true: np.ndarray, y_pred: np.ndarray, train: np.ndarray) -> np.ndarray:
    """
    Root Mean Squared Scaled Error -- la metrica de la competencia M5.

        RMSSE = sqrt( mean((y - yhat)^2) / mean(diff(train)^2) )

    Interpretacion:
        < 1  -> mejor que repetir el valor de ayer
        = 1  -> igual de bueno que ese naive
        > 1  -> peor

    Es adimensional, asi que se pueden comparar series de volumenes distintos.
    """
    num = np.mean((y_true - y_pred) ** 2, axis=1)
    diffs = np.diff(train, axis=1)
    den = np.mean(diffs ** 2, axis=1)
    den = np.where(den == 0, np.nan, den)  # series planas no son escalables
    return np.sqrt(num / den)


def wrmsse(y_true, y_pred, train, weights) -> float:
    """RMSSE ponderado por importancia economica de cada serie."""
    scores = rmsse(y_true, y_pred, train)
    valid = ~np.isnan(scores)
    w = weights[valid] / weights[valid].sum()
    return float(np.sum(w * scores[valid]))


def evaluate(name, y_true, y_pred, train, weights=None) -> dict:
    """Calcula todas las metricas de un modelo."""
    scores = rmsse(y_true, y_pred, train)
    row = {
        "model": name,
        "MAE": mae(y_true, y_pred),
        "RMSE": rmse(y_true, y_pred),
        "MAPE": mape(y_true, y_pred),
        "sMAPE": smape(y_true, y_pred),
        "RMSSE": float(np.nanmean(scores)),
    }
    if weights is not None:
        row["WRMSSE"] = wrmsse(y_true, y_pred, train, weights)
    return row


def comparison_table(rows: list[dict]) -> pd.DataFrame:
    """Ordena los modelos por RMSSE (menor es mejor)."""
    return pd.DataFrame(rows).sort_values("RMSSE").reset_index(drop=True).round(4)