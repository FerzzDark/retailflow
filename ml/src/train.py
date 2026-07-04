"""
Demand forecasting — model training and evaluation.

Implements a progression from baseline to advanced models:
  1. Naive baseline (moving average)
  2. Statistical (SARIMA / Prophet)
  3. ML (LightGBM with engineered features)

Uses temporal validation (never random splits for time series).
"""
import numpy as np
import pandas as pd


def temporal_train_test_split(df: pd.DataFrame, date_col: str, cutoff: str):
    """Split chronologically — training before cutoff, test after."""
    train = df[df[date_col] < cutoff].copy()
    test = df[df[date_col] >= cutoff].copy()
    return train, test


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Percentage Error (ignores zero-actual points)."""
    mask = y_true != 0
    if mask.sum() == 0:
        return np.nan
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root Mean Squared Error."""
    return np.sqrt(np.mean((y_true - y_pred) ** 2))


def naive_baseline(train: pd.DataFrame, horizon: int, window: int = 28):
    """Predict future demand as the moving average of recent sales."""
    recent_mean = train["units"].tail(window).mean()
    return np.full(horizon, recent_mean)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer features for the ML model: lags, rolling stats, calendar."""
    df = df.sort_values("date").copy()
    # Lag features
    for lag in [7, 14, 28]:
        df[f"lag_{lag}"] = df["units"].shift(lag)
    # Rolling means
    for window in [7, 28]:
        df[f"rolling_mean_{window}"] = df["units"].shift(1).rolling(window).mean()
    return df


def train_lightgbm(train: pd.DataFrame, features: list):
    """Train a LightGBM regressor. Imported lazily to keep baseline light."""
    import lightgbm as lgb

    X = train[features].fillna(0)
    y = train["units"]
    model = lgb.LGBMRegressor(
        n_estimators=200,
        learning_rate=0.05,
        num_leaves=31,
        random_state=42,
    )
    model.fit(X, y)
    return model


if __name__ == "__main__":
    print("Training pipeline — see notebooks/ for full experimentation")
