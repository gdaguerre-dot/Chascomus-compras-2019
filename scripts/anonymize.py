"""
Anonimiza el registro de compras: reemplaza nombres de secretarías y
proveedores por códigos estables, y descarta columnas identificatorias
(número de folio real, dependencia de detalle).

NOTA: el archivo fuente (con nombres reales) NO se publica en este repositorio.
Este script documenta el método; para correrlo hace falta el export original,
que se mantiene fuera de control de versiones por privacidad.

Uso:
    python scripts/anonymize.py data/orden_compra_2019_original.xlsx
"""

import sys
import json
import string
import pandas as pd


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/orden_compra_2019_original.xlsx"

    df = pd.read_excel(path, sheet_name="orden_compra")
    df["OC_FILL"] = df["ORDENCOMPRA"].ffill()
    real = df.drop_duplicates(subset=["OC_FILL", "IMPORTE", "PROVEEDOR"]).copy()
    real["MES"] = real["FECHA"].dt.month

    # Secretaría -> letra, ordenado por gasto real descendente (A = mayor gasto)
    jur_rank = real.groupby("JUR")["IMPORTE"].sum().sort_values(ascending=False)
    letters = list(string.ascii_uppercase)[: len(jur_rank)]
    jur_map = {name: f"Secretaría {letters[i]}" for i, name in enumerate(jur_rank.index)}

    # Proveedor -> código, ordenado por gasto real descendente (PROV-001 = mayor gasto)
    prov_rank = real.groupby("PROVEEDOR")["IMPORTE"].sum().sort_values(ascending=False)
    prov_map = {name: f"PROV-{i + 1:03d}" for i, name in enumerate(prov_rank.index)}

    real["JUR_ANON"] = real["JUR"].map(jur_map)
    real["PROV_ANON"] = real["PROVEEDOR"].map(prov_map)

    # ID de orden sintético (no es el folio real, solo preserva el orden cronológico)
    real_sorted = real.sort_values("FECHA").reset_index(drop=True)
    real_sorted["ORDEN_ID"] = [f"OC-{i + 1:05d}" for i in range(len(real_sorted))]

    out_csv = real_sorted[["ORDEN_ID", "FECHA", "PROV_ANON", "JUR_ANON", "IMPORTE"]].rename(
        columns={"PROV_ANON": "PROVEEDOR_COD", "JUR_ANON": "SECRETARIA_COD"}
    )
    out_csv.to_csv("data/compras_2019_anonimizado.csv", index=False, encoding="utf-8-sig")

    grp = (
        real.groupby(["JUR_ANON", "MES", "PROV_ANON"])["IMPORTE"]
        .agg(importe_sum="sum", importe_count="count")
        .reset_index()
    )
    jur_list_anon = [jur_map[k] for k in jur_rank.index]
    jur_idx = {j: i for i, j in enumerate(jur_list_anon)}
    rows = [
        [jur_idx[r.JUR_ANON], int(r.MES), r.PROV_ANON, round(float(r.importe_sum), 2), int(r.importe_count)]
        for r in grp.itertuples()
    ]

    totals = {
        "n_lineas_crudas": int(len(df)),
        "n_ordenes_reales": int(len(real)),
        "raw_sum_inflado": round(float(df["IMPORTE"].sum()), 2),
        "total_real": round(float(real["IMPORTE"].sum()), 2),
        "pct_sin_oc": round(100 * df["ORDENCOMPRA"].isna().sum() / len(df), 1),
        "n_proveedores": int(df["PROVEEDOR"].nunique()),
        "n_dependencias": int(df["DEPENDENCIA"].nunique()),
        "n_jur": int(df["JUR"].nunique()),
        "n_proveedores_una_orden": int((df["PROVEEDOR"].value_counts() == 1).sum()),
        "n_duplicadas": int(df.duplicated().sum()),
    }
    fine = {"jurNames": jur_list_anon, "rows": rows, "totals": totals}
    with open("docs/fine_data.js", "w", encoding="utf-8") as f:
        f.write("const FINE = " + json.dumps(fine, ensure_ascii=False) + ";")

    # Mapeos de referencia: NO se publican (ver .gitignore). Sirven solo para
    # regenerar el gráfico de red desde el sandbox local si hace falta.
    pd.DataFrame({"PROVEEDOR_REAL": list(prov_map.keys()), "PROVEEDOR_COD": list(prov_map.values())}).to_csv(
        "_mapping_proveedores_PRIVADO.csv", index=False
    )
    pd.DataFrame({"JUR_REAL": list(jur_map.keys()), "JUR_COD": list(jur_map.values())}).to_csv(
        "_mapping_jur_PRIVADO.csv", index=False
    )

    print(json.dumps(totals, indent=2, ensure_ascii=False))
    print("\nOK -> data/compras_2019_anonimizado.csv")
    print("OK -> docs/fine_data.js")
    print("OK -> _mapping_*_PRIVADO.csv (NO subir a git)")


if __name__ == "__main__":
    main()
