"""
Genera assets/red_compras_2019.png: red bimodal proveedor <-> secretaría,
totalmente anonimizada (secretarías como letras, proveedores como códigos),
con layout radial agrupado por secretaría dominante para maximizar legibilidad.

Uso:
    python scripts/build_network_graph.py data/compras_2019_anonimizado.csv
"""

import sys
import hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TOP_N_PROVIDERS = 60
JUR_ORDER = [f"Secretaría {c}" for c in "ABCDEFGHIJ"]
COLORS = ["#8A3226", "#93752F", "#1B2A44", "#3D5A3D", "#6B4E9E",
          "#2A6F7A", "#B7621A", "#7A5230", "#4A4A6A", "#8C6B4F"]
JUR_COLORS = {j: COLORS[i] for i, j in enumerate(JUR_ORDER)}


def stable_rand(seed_str: str, lo: float, hi: float) -> float:
    """Pseudo-random pero determinístico, para que el layout sea reproducible."""
    h = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    frac = (h % 100000) / 100000
    return lo + frac * (hi - lo)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/compras_2019_anonimizado.csv"
    real = pd.read_csv(path, encoding="utf-8-sig")
    real = real.rename(columns={"PROVEEDOR_COD": "PROV_ANON", "SECRETARIA_COD": "JUR_ANON"})

    vc = real["PROV_ANON"].value_counts()
    multi = vc[vc > 1].index
    filt = real[real["PROV_ANON"].isin(multi)]

    top_prov = filt.groupby("PROV_ANON")["IMPORTE"].sum().sort_values(ascending=False).head(TOP_N_PROVIDERS).index
    filt2 = filt[filt["PROV_ANON"].isin(top_prov)]

    jur_spend = filt2.groupby("JUR_ANON")["IMPORTE"].sum().reindex(JUR_ORDER).fillna(0)
    prov_spend = filt2.groupby("PROV_ANON")["IMPORTE"].sum()
    prov_edges = filt2.groupby(["PROV_ANON", "JUR_ANON"])["IMPORTE"].sum().reset_index()

    prov_info = {}
    for p in top_prov:
        sub = prov_edges[prov_edges["PROV_ANON"] == p].sort_values("IMPORTE", ascending=False)
        prov_info[p] = {"dom": sub.iloc[0]["JUR_ANON"], "deg": len(sub), "edges": sub}

    # layout radial: secretarías en el anillo exterior, proveedores agrupados
    # cerca de su secretaría dominante (y hacia el centro si compran a varias)
    n_jur = len(JUR_ORDER)
    R = 10.0
    jur_angle = {j: 2 * np.pi * i / n_jur - np.pi / 2 for i, j in enumerate(JUR_ORDER)}
    jur_pos = {j: (R * np.cos(a), R * np.sin(a)) for j, a in jur_angle.items()}

    prov_pos = {}
    for p in top_prov:
        info = prov_info[p]
        angle = jur_angle[info["dom"]] + stable_rand(p + "a", -0.62, 0.62)
        deg_factor = min(info["deg"], 4) / 4.0
        radius = max(stable_rand(p + "r", 6.4, 8.6) - deg_factor * 3.0, 2.2)
        prov_pos[p] = (radius * np.cos(angle), radius * np.sin(angle))

    fig, ax = plt.subplots(figsize=(15, 15), facecolor="#ECE9DE")
    ax.set_facecolor("#ECE9DE")

    max_edge = prov_edges["IMPORTE"].max()
    for p in top_prov:
        x1, y1 = prov_pos[p]
        for _, r in prov_info[p]["edges"].iterrows():
            x2, y2 = jur_pos[r["JUR_ANON"]]
            lw = 0.25 + 1.8 * (np.log1p(r["IMPORTE"]) / np.log1p(max_edge))
            alpha = 0.14 if prov_info[p]["edges"].shape[0] > 1 else 0.22
            ax.plot([x1, x2], [y1, y2], color=JUR_COLORS[r["JUR_ANON"]], alpha=alpha,
                     linewidth=lw, zorder=1, solid_capstyle="round")

    max_prov_spend = prov_spend.max()
    for p in top_prov:
        x, y = prov_pos[p]
        size = 45 + 620 * (prov_spend[p] / max_prov_spend)
        ax.scatter(x, y, s=size, color=JUR_COLORS[prov_info[p]["dom"]], alpha=0.88,
                   edgecolors="#F7F5EC", linewidths=0.7, zorder=3)

    for j in JUR_ORDER:
        x, y = jur_pos[j]
        size = 2600 + 5200 * (jur_spend[j] / jur_spend.max())
        ax.scatter(x, y, s=size, color=JUR_COLORS[j], alpha=0.97, edgecolors="#1B2A44",
                   linewidths=2.2, zorder=4)
        ax.annotate(j.replace("Secretaría ", ""), (x, y), fontsize=15, fontweight="bold",
                    color="#F7F5EC", ha="center", va="center", zorder=5, family="monospace")

    top6 = prov_spend.sort_values(ascending=False).head(6).index
    for p in top6:
        x, y = prov_pos[p]
        ax.annotate(p, (x, y), fontsize=8.5, color="#1B2A44", ha="center", va="center",
                    zorder=6, family="monospace", fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.22", fc="#F7F5EC", ec="#B7AF98", alpha=0.92, linewidth=0.6))

    ax.set_title("Red de compras — municipio bonaerense, 2019\nProveedores (top 60 por monto real) ↔ Secretarías (anonimizado)",
                 fontsize=17, fontweight="bold", color="#1B2A44", family="serif", pad=18)
    ax.text(0.5, -0.015, "Tamaño = monto real adjudicado · Color = secretaría dominante del proveedor · Nombres reemplazados por códigos",
            transform=ax.transAxes, ha="center", fontsize=10, color="#625D4C", family="monospace")

    ax.set_xlim(-13, 13)
    ax.set_ylim(-13, 13)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    plt.savefig("assets/red_compras_2019.png", dpi=190, facecolor="#ECE9DE", bbox_inches="tight")
    print(f"nodos={len(top_prov) + n_jur} enlaces={len(prov_edges)}")
    print("OK -> assets/red_compras_2019.png")


if __name__ == "__main__":
    main()
