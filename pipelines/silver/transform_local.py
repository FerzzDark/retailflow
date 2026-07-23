"""
Silver layer (local): limpieza, unpivot y enriquecimiento.

Grano de salida: una fila = un producto, en una tienda, en un dia.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BRONZE_DIR = ROOT / "data" / "bronze"
SILVER_DIR = ROOT / "data" / "silver"

ID_COLS = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]


def unpivot_sales(sales: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte el formato ANCHO del M5 en formato LARGO.

    Antes:   id | item_id | ... | d_1 | d_2 | ... | d_1913
    Despues: id | item_id | ... | d   | units
    """
    day_cols = [c for c in sales.columns if c.startswith("d_")]
    long_df = sales.melt(
        id_vars=ID_COLS,
        value_vars=day_cols,
        var_name="d",
        value_name="units",
    )
    print(f"  unpivot: {len(sales):,} filas x {len(day_cols):,} dias -> {len(long_df):,} filas")
    return long_df


def join_calendar(long_df: pd.DataFrame, calendar: pd.DataFrame) -> pd.DataFrame:
    """Trae la fecha real y los atributos de calendario usando la clave 'd'."""
    cal_cols = [
        "d", "date", "wm_yr_wk", "wday", "month", "year",
        "event_name_1", "event_type_1", "snap_CA", "snap_TX", "snap_WI",
    ]
    df = long_df.merge(calendar[cal_cols], on="d", how="left")
    if df["date"].isna().any():
        raise ValueError("Hay filas sin fecha: fallo el join con calendario.")
    return df


def join_prices(df: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    """
    Trae el precio semanal. Clave compuesta: store_id + item_id + wm_yr_wk.
    LEFT JOIN: si no hay precio, el producto no estaba a la venta esa semana.
    """
    return df.merge(prices, on=["store_id", "item_id", "wm_yr_wk"], how="left")


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Features derivadas de negocio y calendario."""
    snap_map = {"CA": "snap_CA", "TX": "snap_TX", "WI": "snap_WI"}
    df["snap_flag"] = 0
    for state, col in snap_map.items():
        mask = df["state_id"] == state
        df.loc[mask, "snap_flag"] = df.loc[mask, col]

    # En el M5, wday 1=sabado y 2=domingo
    df["is_weekend"] = df["wday"].isin([1, 2]).astype(int)

    # Si no hay precio, el item no estaba activo en el surtido esa semana
    df["is_active"] = df["sell_price"].notna().astype(int)

    df["revenue"] = df["units"] * df["sell_price"].fillna(0)
    return df


def clean_types(df: pd.DataFrame) -> pd.DataFrame:
    """Tipos explicitos: nunca dejar que pandas adivine."""
    df["date"] = pd.to_datetime(df["date"])
    df["units"] = df["units"].astype("int32")
    df["sell_price"] = df["sell_price"].astype("float64")
    df["snap_flag"] = df["snap_flag"].astype("int8")
    df["is_weekend"] = df["is_weekend"].astype("int8")
    df["is_active"] = df["is_active"].astype("int8")
    return df


def run() -> None:
    print(f"SILVER | leyendo de {BRONZE_DIR}")
    sales = pd.read_parquet(BRONZE_DIR / "bronze_sales.parquet")
    calendar = pd.read_parquet(BRONZE_DIR / "bronze_calendar.parquet")
    prices = pd.read_parquet(BRONZE_DIR / "bronze_prices.parquet")

    df = unpivot_sales(sales)
    df = join_calendar(df, calendar)
    df = join_prices(df, prices)
    df = add_features(df)
    df = clean_types(df)

    keep = [
        "id", "item_id", "dept_id", "cat_id", "store_id", "state_id",
        "date", "d", "wm_yr_wk", "wday", "month", "year",
        "units", "sell_price", "revenue",
        "event_name_1", "event_type_1", "snap_flag", "is_weekend", "is_active",
    ]
    df = df[keep].sort_values(["id", "date"]).reset_index(drop=True)

    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    out = SILVER_DIR / "silver_sales_daily.parquet"
    df.to_parquet(out, index=False)

    print(f"SILVER | grano: producto x tienda x dia")
    print(f"SILVER | filas: {len(df):,}  columnas: {df.shape[1]}")
    print(f"SILVER | rango de fechas: {df['date'].min().date()} -> {df['date'].max().date()}")
    print(f"SILVER | items activos (con precio): {df['is_active'].mean():.1%}")
    print(f"SILVER | escrito {out.relative_to(ROOT)}")
    print("SILVER | OK")


if __name__ == "__main__":
    run()