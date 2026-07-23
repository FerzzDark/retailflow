"""
Bronze layer (local): ingesta cruda de los CSV del M5 a formato Parquet.

Responsabilidad de Bronze: LEER el dato crudo y PERSISTIRLO tal cual,
sin limpiar ni transformar.
"""
from pathlib import Path

import pandas as pd

# --- Rutas -----------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
BRONZE_DIR = ROOT / "data" / "bronze"

# --- Alcance del subset ----------------------------------------------------
CAT_FILTER = "FOODS"
STORE_FILTER = "CA_1"


def ingest_calendar() -> pd.DataFrame:
    """Lee calendar.csv sin transformar."""
    df = pd.read_csv(RAW_DIR / "calendar.csv")
    print(f"  calendar        -> {df.shape[0]:>8,} filas x {df.shape[1]} columnas")
    return df


def ingest_prices() -> pd.DataFrame:
    """Lee sell_prices.csv, acotado a la tienda del subset."""
    df = pd.read_csv(RAW_DIR / "sell_prices.csv")
    if STORE_FILTER:
        df = df[df["store_id"] == STORE_FILTER]
    print(f"  sell_prices     -> {df.shape[0]:>8,} filas x {df.shape[1]} columnas")
    return df


def ingest_sales() -> pd.DataFrame:
    """
    Lee sales_train_validation.csv (formato ANCHO: d_1 ... d_1913).
    NO se despivotea aqui: eso es trabajo de Silver.
    """
    df = pd.read_csv(RAW_DIR / "sales_train_validation.csv")
    if CAT_FILTER:
        df = df[df["cat_id"] == CAT_FILTER]
    if STORE_FILTER:
        df = df[df["store_id"] == STORE_FILTER]
    print(f"  sales (ancho)   -> {df.shape[0]:>8,} filas x {df.shape[1]} columnas")
    return df


def run() -> None:
    """Ejecuta la ingesta completa de la capa Bronze."""
    if not RAW_DIR.exists():
        raise FileNotFoundError(f"No existe {RAW_DIR}. Descarga el M5 de Kaggle.")

    BRONZE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"BRONZE | leyendo de {RAW_DIR}")
    print(f"BRONZE | subset: cat={CAT_FILTER} store={STORE_FILTER}")

    tables = {
        "bronze_calendar": ingest_calendar(),
        "bronze_prices": ingest_prices(),
        "bronze_sales": ingest_sales(),
    }

    for name, df in tables.items():
        if df.empty:
            raise ValueError(f"{name} quedo vacia. Revisa los filtros del subset.")
        out = BRONZE_DIR / f"{name}.parquet"
        df.to_parquet(out, index=False)
        print(f"BRONZE | escrito {out.relative_to(ROOT)}")

    print("BRONZE | OK")


if __name__ == "__main__":
    run()