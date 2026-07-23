"""
Orquestador del pipeline medallion (local).

Ejecuta las tres capas en orden: Bronze -> Silver -> Gold.

Uso:
    python pipelines/run_pipeline.py
    python pipelines/run_pipeline.py --from silver
"""
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipelines.bronze import ingest_local
from pipelines.silver import transform_local
from pipelines.gold import aggregate_local

LAYERS = [
    ("bronze", ingest_local.run),
    ("silver", transform_local.run),
    ("gold", aggregate_local.run),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="RetailFlow - pipeline medallion local")
    parser.add_argument(
        "--from", dest="start_at", default="bronze",
        choices=[name for name, _ in LAYERS],
        help="Capa desde la que empezar (por defecto: bronze)",
    )
    args = parser.parse_args()

    start_index = [name for name, _ in LAYERS].index(args.start_at)
    total_start = time.perf_counter()

    for name, run_layer in LAYERS[start_index:]:
        print("=" * 70)
        print(f"CAPA: {name.upper()}")
        print("=" * 70)
        layer_start = time.perf_counter()
        try:
            run_layer()
        except Exception as exc:
            print(f"\nFALLO en la capa {name}: {exc}")
            return 1
        print(f"--> {name} completada en {time.perf_counter() - layer_start:.1f}s\n")

    print("=" * 70)
    print(f"PIPELINE OK - tiempo total: {time.perf_counter() - total_start:.1f}s")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())