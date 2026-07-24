"""
Diagnostico de las series antes de modelar.

Responde preguntas que definen el diseno del modelo:
  1. Que tan intermitente es la demanda? (proporcion de ceros)
  2. Como se clasifica cada serie segun Syntetos-Boylan?
  3. Cuantas series estan muertas o aun no habian nacido?
  4. Hay estacionalidad semanal y efecto SNAP que valga la pena modelar?

Uso:
    python ml/src/diagnose_series.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

SILVER_PATH = ROOT / "data" / "silver" / "silver_sales_daily.parquet"
HORIZON = 28


def section(title: str) -> None:
    print(f"\n{'=' * 68}\n{title}\n{'=' * 68}")


def first_sale_index(row: np.ndarray) -> int:
    """Indice del primer dia con venta > 0. Devuelve -1 si nunca vendio."""
    nz = np.flatnonzero(row > 0)
    return int(nz[0]) if nz.size else -1


def classify_syntetos_boylan(adi: float, cv2: float) -> str:
    """
    Clasificacion de Syntetos-Boylan para demanda intermitente.

    ADI  = intervalo medio entre demandas (dias entre ventas)
    CV^2 = varianza relativa del tamano de la demanda cuando ocurre

    Cortes clasicos: ADI = 1.32, CV^2 = 0.49
    """
    if np.isnan(adi) or np.isnan(cv2):
        return "sin_demanda"
    if adi < 1.32 and cv2 < 0.49:
        return "smooth"        # regular y estable -> facil de predecir
    if adi < 1.32 and cv2 >= 0.49:
        return "erratic"       # frecuente pero volumen volatil
    if adi >= 1.32 and cv2 < 0.49:
        return "intermittent"  # esporadica pero volumen estable
    return "lumpy"             # esporadica Y volatil -> la mas dificil


def main() -> int:
    if not SILVER_PATH.exists():
        print("No existe data/silver/. Corre: python pipelines/run_pipeline.py")
        return 1

    silver = pd.read_parquet(SILVER_PATH, columns=["id", "date", "units", "sell_price"])
    matrix = silver.pivot(index="id", columns="date", values="units").sort_index(axis=1)
    values = matrix.to_numpy(dtype=float)
    n_series, n_days = values.shape

    section("1. INTERMITENCIA GLOBAL")
    zero_share = (values == 0).mean()
    print(f"Series: {n_series:,}   Dias: {n_days:,}   Observaciones: {values.size:,}")
    print(f"Dias con CERO ventas: {zero_share:.1%}")
    print(f"Media global de unidades/dia: {values.mean():.2f}")
    print(f"Mediana de unidades/dia: {np.median(values):.2f}")

    section("2. CICLO DE VIDA DE LAS SERIES")
    first_idx = np.array([first_sale_index(r) for r in values])
    never_sold = (first_idx == -1).sum()
    born_late = (first_idx > 0).sum()
    last_window = values[:, -90:]
    dead = (last_window.sum(axis=1) == 0).sum()

    print(f"Series que nunca vendieron nada:        {never_sold:>6,}")
    print(f"Series con ceros iniciales (no nacidas): {born_late:>6,}")
    print(f"Series sin ventas en los ultimos 90 dias:{dead:>6,}")
    if born_late:
        delay = first_idx[first_idx > 0]
        print(f"Retraso de lanzamiento -> mediana {np.median(delay):.0f} dias, max {delay.max():,} dias")
    pre_launch_zeros = sum(idx for idx in first_idx if idx > 0)
    print(f"Ceros ANTES del primer lanzamiento: {pre_launch_zeros:,} "
          f"({pre_launch_zeros / values.size:.1%} de todas las observaciones)")

    section("3. CLASIFICACION SYNTETOS-BOYLAN")
    rows = []
    for i in range(n_series):
        row = values[i]
        start = first_idx[i]
        if start == -1:
            rows.append(("sin_demanda", np.nan, np.nan))
            continue
        active = row[start:]                    # solo vida util del producto
        nonzero = active[active > 0]
        adi = len(active) / len(nonzero)        # dias por evento de demanda
        cv2 = (nonzero.std() / nonzero.mean()) ** 2 if nonzero.mean() > 0 else np.nan
        rows.append((classify_syntetos_boylan(adi, cv2), adi, cv2))

    diag = pd.DataFrame(rows, columns=["class", "ADI", "CV2"], index=matrix.index)
    summary = diag["class"].value_counts().rename("series").to_frame()
    summary["%"] = (summary["series"] / n_series * 100).round(1)
    print(summary.to_string())
    print(f"\nADI mediano: {diag['ADI'].median():.2f} dias entre ventas")
    print(f"CV^2 mediano: {diag['CV2'].median():.2f}")

    section("4. ESTACIONALIDAD SEMANAL Y SNAP")
    daily = silver.groupby("date")["units"].sum()
    by_weekday = daily.groupby(daily.index.dayofweek).mean()
    names = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
    overall = by_weekday.mean()
    print("Unidades medias por dia de semana (indice 100 = promedio):")
    for i, name in enumerate(names):
        idx = by_weekday.loc[i] / overall * 100
        bar = "#" * int(idx / 4)
        print(f"  {name}  {by_weekday.loc[i]:>9,.0f}  {idx:>5.1f}  {bar}")
    spread = by_weekday.max() / by_weekday.min()
    print(f"\nRatio max/min entre dias: {spread:.2f}x "
          f"({'estacionalidad relevante' if spread > 1.15 else 'estacionalidad debil'})")

    snap = pd.read_parquet(SILVER_PATH, columns=["date", "units", "snap_flag"])
    snap_means = snap.groupby("snap_flag")["units"].mean()
    if len(snap_means) == 2:
        lift = (snap_means[1] / snap_means[0] - 1) * 100
        print(f"\nVentas medias sin SNAP: {snap_means[0]:.3f}")
        print(f"Ventas medias con SNAP: {snap_means[1]:.3f}")
        print(f"Efecto SNAP: {lift:+.1f}%")

    section("5. IMPLICACIONES PARA EL MODELO")
    lumpy_share = (diag["class"].isin(["lumpy", "intermittent"]).sum() / n_series)
    print(f"- {zero_share:.0%} de ceros -> metricas porcentuales (MAPE) no sirven; usar RMSSE/WRMSSE.")
    print(f"- {lumpy_share:.0%} de series intermitentes o lumpy -> modelo GLOBAL mejor que uno por serie.")
    if pre_launch_zeros:
        print("- Hay ceros pre-lanzamiento -> enmascararlos para no ensenar 'demanda cero' falsa.")
    if dead:
        print(f"- {dead:,} series sin ventas recientes -> evaluar si excluirlas del entrenamiento.")
    if spread > 1.15:
        print("- Estacionalidad semanal presente -> incluir dia de semana como feature.")
    print("- Lags y medias moviles son las features base; el mejor baseline fue una media movil.")
    return 0


if __name__ == "__main__":
    sys.exit(main())