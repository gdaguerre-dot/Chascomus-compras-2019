"""
Limpieza de órdenes de compra 2019 (antes de anonimizar).
=============================================================================

Reconstruye el gasto real a partir del export crudo de compras, corrigiendo
dos problemas de calidad de datos encontrados en el archivo original:

1. El número de orden de compra (ORDENCOMPRA) solo está cargado en la primera
   línea de detalle de cada orden; el resto de las líneas quedan en blanco
   (patrón típico de celdas combinadas al exportar desde Excel). Se reconstruye
   con forward-fill.

2. El importe de la orden se repite idéntico en cada línea de detalle que la
   compone. Sumar la columna IMPORTE sin deduplicar infla el gasto real en ~2,4x.

La lógica de reconstrucción vive en scripts/lib/reconstruct.py, compartida
con anonymize.py, para que ambos scripts nunca puedan divergir.

NOTA: el archivo fuente (con nombres reales) NO se publica en este repositorio,
por privacidad. Este script documenta el método de limpieza; para reproducir
los datos publicados hace falta correr esto y luego scripts/anonymize.py
(que ya incluye internamente este mismo paso).

Uso:
    python scripts/clean_and_aggregate.py data/orden_compra_2019_original.xlsx
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from lib.reconstruct import reconstruct_real_orders


def load_raw(path: str) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name="orden_compra")


def data_quality_report(df: pd.DataFrame, real: pd.DataFrame) -> dict:
    return {
        "n_lineas_crudas": int(len(df)),
        "n_ordenes_reales": int(len(real)),
        "raw_sum_inflado": round(float(df["IMPORTE"].sum()), 2),
        "total_real": round(float(real["IMPORTE"].sum()), 2),
        "factor_inflacion": round(float(df["IMPORTE"].sum() / real["IMPORTE"].sum()), 2),
        "pct_lineas_sin_oc": round(100 * df["ORDENCOMPRA"].isna().sum() / len(df), 1),
        "n_proveedores": int(df["PROVEEDOR"].nunique()),
        "n_dependencias": int(df["DEPENDENCIA"].nunique()),
        "n_jur": int(df["JUR"].nunique()),
        "n_proveedores_una_orden": int((df["PROVEEDOR"].value_counts() == 1).sum()),
        "n_filas_duplicadas": int(df.duplicated().sum()),
    }


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/orden_compra_2019_original.xlsx"
    df = load_raw(path)
    real = reconstruct_real_orders(df)
    report = data_quality_report(df, real)

    import json
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("\nEste script solo diagnostica. Para generar los archivos publicados")
    print("(CSV anonimizado + datos del dashboard), correr scripts/anonymize.py")


if __name__ == "__main__":
    main()
