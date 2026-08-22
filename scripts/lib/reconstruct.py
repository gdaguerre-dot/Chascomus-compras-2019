"""
Lógica única de reconstrucción de órdenes de compra reales a partir del
export crudo. Usada tanto por clean_and_aggregate.py (diagnóstico) como por
anonymize.py (limpieza + anonimización real), para que ambos scripts nunca
puedan divergir en cómo se resuelve el forward-fill / deduplicación.

Ver README.md, sección "Validation of order reconstruction", para el
detalle de por qué esta clave de deduplicación es la elegida y qué se
validó sobre ella.
"""

import pandas as pd


def reconstruct_real_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Reconstruye una fila por orden de compra real.

    Dos problemas de calidad del export original que esto corrige:
    1. ORDENCOMPRA solo está cargado en la primera línea de detalle de cada
       orden (celdas combinadas al exportar desde Excel) -> se completa con
       forward-fill sobre la columna ORDENCOMPRA.
    2. El IMPORTE se repite idéntico en cada línea de detalle de una misma
       orden -> sumarlo sin deduplicar infla el gasto real (~2.4x medido).

    La clave de deduplicación es (OC_FILL, IMPORTE, PROVEEDOR): dos líneas
    se consideran la misma orden real solo si comparten el mismo número de
    orden reconstruido, el mismo importe y el mismo proveedor.
    """
    df = df.copy()
    df["OC_FILL"] = df["ORDENCOMPRA"].ffill()
    return df.drop_duplicates(subset=["OC_FILL", "IMPORTE", "PROVEEDOR"]).copy()
