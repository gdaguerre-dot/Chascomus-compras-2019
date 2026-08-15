# Boletín de Compras Municipales · Chascomús 2019

**Caso de estudio de calidad de datos, análisis de compras públicas y análisis de redes sociales (ARS), a partir del registro real de órdenes de compra 2019 de la Municipalidad de Chascomús.**

🔗 **[Ver el dashboard interactivo](https://TU-USUARIO.github.io/TU-REPO/)** *(reemplazar con el link de GitHub Pages una vez publicado)*

![Red de compras municipales 2019](assets/red_compras_2019.png)

---

## Por qué este proyecto

Este trabajo nace de un informe previo de análisis de redes sociales (ARS) aplicado a las compras municipales de 2019 (incluido en `docs/informe_ars_original.md`), que modelaba secretarías y proveedores como una red bimodal para identificar centralidad, intermediación y comunidades.

Tomé la base de datos original que sustentaba ese informe y le apliqué un proceso de auditoría de calidad de datos, reconstrucción de series reales, un tablero de transparencia con filtros interactivos, y una reconstrucción del grafo de red — como ejercicio de portfolio para demostrar el circuito completo: **de un archivo de gestión municipal crudo a un producto de datos usable.**

## El hallazgo principal

La base cruda **repite el importe total de cada orden de compra en cada línea de detalle** que la compone (una orden con 5 ítems aparece 5 veces con el mismo monto). Sumar la columna `IMPORTE` sin corregir esto **infla el gasto real en 2,38x**:

| | Monto |
|---|---|
| Suma cruda de la columna IMPORTE | $1.012.868.439 |
| **Gasto real 2019 (corregido)** | **$426.096.932** |

Además, el número de orden de compra (folio) **solo está completo en el 29,4% de las líneas** — se reconstruyó con relleno hacia adelante (forward-fill), asumiendo que cada línea de detalle hereda el folio de la primera fila de su orden. A partir de fines de abril de 2019 el campo prácticamente deja de cargarse, lo que sugiere una falla de trazabilidad en el proceso de carga, no un dato faltante al azar.

Ver la metodología completa en [`docs/index.html`](docs/index.html) (sección "Nota sobre calidad de datos") y en el código de [`scripts/clean_and_aggregate.py`](scripts/clean_and_aggregate.py).

## Qué contiene el repositorio

```
├── data/
│   ├── orden_compra_2019_original.xlsx   # fuente cruda (línea de detalle, 28.525 filas)
│   └── compras_2019_limpio.csv           # una fila por orden real, ya deduplicada (13.715 filas)
├── docs/
│   ├── index.html                        # dashboard interactivo (GitHub Pages)
│   └── fine_data.js                      # datos agregados (secretaría × mes × proveedor)
├── assets/
│   └── red_compras_2019.png              # red proveedor–secretaría
├── scripts/
│   ├── clean_and_aggregate.py            # limpieza + agregación reproducible
│   └── build_network_graph.py            # generación del grafo de red
└── README.md
```

## El dashboard

- **KPIs y monto real vs. inflado**, con la corrección de datos como pieza central, no como nota al pie.
- **Filtro interactivo por secretaría**: al hacer clic en cualquier fila de la sección "Gasto por secretaría", todo el tablero (KPIs, gasto mensual, ranking de proveedores) se recalcula para esa secretaría, calculado en el navegador a partir del set agregado (sin backend).
- **Índice de concentración de proveedores (HHI)** por secretaría, con semáforo bajo / moderado / alto.
- **Ranking de proveedores** por monto real adjudicado.
- **Red proveedor–secretaría** (ver más abajo), como puente con el informe ARS original.

## La red proveedor–secretaría

`assets/red_compras_2019.png` reconstruye la red bimodal del informe original: nodos de secretaría (tamaño = gasto) conectados a los 70 proveedores de mayor adjudicación real (tamaño = monto, color = secretaría dominante). A diferencia del informe original, acá el grafo se reconstruye **sobre el monto real deduplicado**, no sobre el importe crudo repetido por línea.

Se regenera con:

```bash
python scripts/build_network_graph.py data/compras_2019_limpio.csv
```

## Cómo reproducir todo desde cero

```bash
pip install pandas openpyxl networkx matplotlib

# 1) Limpieza + agregación (genera data/compras_2019_limpio.csv y docs/fine_data.js)
python scripts/clean_and_aggregate.py data/orden_compra_2019_original.xlsx

# 2) Grafo de red (genera assets/red_compras_2019.png)
python scripts/build_network_graph.py data/compras_2019_limpio.csv

# 3) Ver el dashboard localmente
cd docs && python -m http.server 8000
# abrir http://localhost:8000
```

## Publicar en GitHub Pages

1. Subir el repositorio a GitHub (ver pasos abajo).
2. En **Settings → Pages**, elegir la rama `main` y la carpeta `/docs` como fuente.
3. GitHub publica el sitio en `https://TU-USUARIO.github.io/TU-REPO/` en 1–2 minutos.

## Pasos para subir el repo a GitHub

```bash
cd chascomus-compras-2019
git init
git add .
git commit -m "Boletín de compras municipales 2019: dashboard, red y auditoría de datos"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/TU-REPO.git
git push -u origin main
```

Luego activar GitHub Pages como se indica arriba.

## Limitaciones y lo que queda abierto

- La deduplicación por (orden, proveedor, importe) es una reconstrucción razonable pero no perfecta: si dos compras distintas de un mismo proveedor el mismo día coincidieran en el importe exacto, se contarían como una sola. Ameritaría cotejarse contra el sistema de origen.
- No hay forma, con este export, de saber *por qué* dejó de cargarse el folio de orden desde fines de abril de 2019 — es la pregunta más valiosa para llevarle al área que genera el reporte.
- Las cifras están en pesos argentinos corrientes de 2019 (sin ajuste por inflación).

## Origen de los datos

Fuente: `orden_compra_2019.xls`, Municipalidad de Chascomús, Dirección de Modernización. Este repositorio es un ejercicio de portfolio personal y no constituye un informe oficial del municipio.

## Contexto

Este proyecto complementa el informe original *"Investigando órdenes de compra, un enfoque desde el análisis de redes sociales (ARS)"* (incluido como referencia en `docs/informe_ars_original.md`), que trabajó la misma base de 2019 con foco en centralidad, intermediación y modularidad de la red secretaría–proveedores.
