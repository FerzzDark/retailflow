"""
Gold layer (local): modelo dimensional y agregados de negocio.

Responsabilidad de Gold: entregar tablas LISTAS PARA CONSUMO.
Aqui ya no se limpia: se modela y se agrega.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SILVER_DIR = ROOT / "data" / "silver"
GOLD_DIR = ROOT / "data" / "gold"


def build_dim_product(silver: pd.DataFrame) -> pd.DataFrame:
    """Dimension producto: atributos que describen QUE se vende."""
    return (
        silver[["item_id", "dept_id", "cat_id"]]
        .drop_duplicates()
        .sort_values("item_id")
        .reset_index(drop=True)
    )


def build_dim_store(silver: pd.DataFrame) -> pd.DataFrame:
    """Dimension tienda: atributos que describen DONDE se vende."""
    return (
        silver[["store_id", "state_id"]]
        .drop_duplicates()
        .sort_values("store_id")
        .reset_index(drop=True)
    )


def build_dim_calendar(silver: pd.DataFrame) -> pd.DataFrame:
    """Dimension calendario: atributos que describen CUANDO se vende."""
    dim = (
        silver[["date", "d", "wm_yr_wk", "wday", "month", "year",
                "event_name_1", "event_type_1", "is_weekend"]]
        .drop_duplicates(subset=["date"])
        .sort_values("date")
        .reset_index(drop=True)
    )
    dim["is_event"] = dim["event_name_1"].notna().astype("int8")
    return dim


def build_fact_sales(silver: pd.DataFrame) -> pd.DataFrame:
    """
    Tabla de hechos: las METRICAS, mas las claves foraneas hacia las dimensiones.
    Grano: producto x tienda x dia.
    """
    return silver[[
        "item_id", "store_id", "date",
        "units", "sell_price", "revenue",
        "snap_flag", "is_active",
    ]].copy()


def build_weekly_category_sales(silver: pd.DataFrame) -> pd.DataFrame:
    """Agregado semanal por categoria y tienda (alimenta el dashboard)."""
    return (
        silver.groupby(["cat_id", "store_id", "wm_yr_wk"], as_index=False)
        .agg(
            total_units=("units", "sum"),
            total_revenue=("revenue", "sum"),
            avg_daily_units=("units", "mean"),
            active_items=("item_id", "nunique"),
        )
        .sort_values(["cat_id", "store_id", "wm_yr_wk"])
        .reset_index(drop=True)
    )


def build_abc_classification(silver: pd.DataFrame) -> pd.DataFrame:
    """
    Clasificacion ABC (principio de Pareto) por ingreso acumulado.

    A = productos que acumulan el primer 80% del ingreso  -> control estricto
    B = los que llevan del 80% al 95%                     -> control moderado
    C = el 5% restante                                    -> control ligero
    """
    rev = (
        silver.groupby("item_id", as_index=False)
        .agg(total_revenue=("revenue", "sum"), total_units=("units", "sum"))
        .sort_values("total_revenue", ascending=False)
        .reset_index(drop=True)
    )

    total = rev["total_revenue"].sum()
    rev["revenue_share"] = rev["total_revenue"] / total
    rev["cumulative_share"] = rev["revenue_share"].cumsum()

    def classify(cum: float) -> str:
        if cum <= 0.80:
            return "A"
        if cum <= 0.95:
            return "B"
        return "C"

    rev["abc_class"] = rev["cumulative_share"].apply(classify)
    return rev


def run() -> None:
    print(f"GOLD | leyendo de {SILVER_DIR}")
    silver = pd.read_parquet(SILVER_DIR / "silver_sales_daily.parquet")
    print(f"GOLD | silver: {len(silver):,} filas")

    outputs = {
        "dim_product": build_dim_product(silver),
        "dim_store": build_dim_store(silver),
        "dim_calendar": build_dim_calendar(silver),
        "fact_sales": build_fact_sales(silver),
        "weekly_category_sales": build_weekly_category_sales(silver),
        "abc_classification": build_abc_classification(silver),
    }

    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    for name, df in outputs.items():
        out = GOLD_DIR / f"{name}.parquet"
        df.to_parquet(out, index=False)
        print(f"GOLD | {name:<24} {len(df):>10,} filas -> {out.name}")

    abc = outputs["abc_classification"]
    resumen = (
        abc.groupby("abc_class")
        .agg(productos=("item_id", "count"), ingreso=("total_revenue", "sum"))
    )
    resumen["% productos"] = (resumen["productos"] / len(abc) * 100).round(1)
    resumen["% ingreso"] = (resumen["ingreso"] / abc["total_revenue"].sum() * 100).round(1)
    print("\nGOLD | Resumen ABC (Pareto):")
    print(resumen[["productos", "% productos", "% ingreso"]].to_string())
    print("\nGOLD | OK")


if __name__ == "__main__":
    run()