"""Acerca del observatorio: definiciones, paleta de color, limitaciones y equipo."""

import streamlit as st

from src.estilo import COLOR_ESTIMADO, COLOR_EVENTO, COLOR_OCUPACION, COLOR_REAL, COLORES_CLASE, COLORES_ORIGEN, COLORES_SEGMENTO
from src.ui import encabezado_pagina

encabezado_pagina(
    "Metodología",
    "Acerca del observatorio",
    "Definiciones de los indicadores, significado de los colores y límites de las fuentes.",
)

st.subheader("Indicadores principales")
st.markdown(
    r"""
| Indicador | Fórmula | Regla |
|---|---|---|
| Visitantes promedio por mes | $\frac{1}{T}\sum_t \sum_{p,s} V_{t,p,s}$ | Solo meses observados; nacionales y extranjeros juntos o por separado |
| Días-persona promedio por mes | $\frac{1}{T}\sum_t \sum_{p,s} DP_{t,p,s}$ | |
| Estadía media ponderada | $\dfrac{\sum DP_{s=\text{>1 día}}}{\sum V_{s=\text{>1 día}}}$ | Solo turistas con pernocta; **nunca** se promedia `permanencia_prom` |
| % turistas | $\dfrac{\sum V_{s=\text{>1 día}}}{\sum V}$ | Excursionistas (< 24 h) con permanencia 1 por definición |
| Lift de festividad | $\dfrac{\overline{V}_{\text{evento}}}{\overline{V}_{\text{regular}}} - 1$ | Base diaria; promedio por día, no suma |
| Tasa implícita de ocupación | $\dfrac{\sum DP_{s=\text{>1 día}}}{\text{plazas cama} \times \text{días del mes}}$ | Solo ventana sep–dic 2025; suma de municipios |
| Afluencia relativa | $100 \cdot \overline{V}_{\text{municipio}} / \overline{V}_{\text{Panajachel}}$ | Índice, nunca participación sobre una suma |
| Clase del municipio | Regla del cuadrante y k-medias ($k = 3$) | Variables: log volumen, estadía, % extranjeros, presión de fin de semana |
| Presión de fin de semana | $\dfrac{\overline{V}_{\text{sáb,dom}}}{\overline{V}_{\text{lun–vie}}}$ | Solo días regulares |
| Estimación ene–feb 2026 (A) | $\hat D_t = \dfrac{\sum_{obs} D}{\sum_{obs} M}\, M_t$ | $M$ = llegadas internacionales (base de migración) |
| MAPE | $\frac{100}{n}\sum \frac{\lvert \hat D_t - D_t\rvert}{D_t}$ | Validación dejando un mes fuera |
"""
)

st.subheader("Paleta de color")
st.caption("Cada color significa siempre lo mismo en todo el tablero. Base: paleta validada para daltonismo del Lab 10.")
items = (
    [(k, v) for k, v in COLORES_ORIGEN.items()]
    + [(k, v) for k, v in COLORES_SEGMENTO.items()]
    + [("Dato observado", COLOR_REAL), ("Estimación (línea discontinua)", COLOR_ESTIMADO), ("Festividad", COLOR_EVENTO),
       ("Ocupación hotelera", COLOR_OCUPACION)]
    + [(f"Clase: {k}", v) for k, v in COLORES_CLASE.items()]
)
st.html("".join(
    f'<div style="display:flex;align-items:center;gap:.6rem;margin:.25rem 0"><span style="width:28px;height:14px;'
    f'background:{c};display:inline-block"></span><code>{c}</code><span>{t}</span></div>' for t, c in items))

st.subheader("Limitaciones")
st.markdown(
    "- **Datos sintéticos en esta versión**: las bases institucionales son confidenciales; el tablero lee los reales "
    "si se colocan en `data/raw/` (o en la carpeta de `OBS_DATOS`).\n"
    "- La telefonía no cubre enero y febrero de 2026: no hay comparación interanual directa 2025 vs 2026.\n"
    "- Los nacionales incorporan factor de expansión: se reportan separados de los extranjeros.\n"
    "- Hotelería formal y plataformas digitales (Airbnb) son universos distintos.\n"
    "- El corte de oferta 2026 es parcial (primer trimestre, con valores repetidos del año previo)."
)

st.subheader("Equipo · Grupo 3")
st.markdown(
    "- Anthony Lou Schwank\n- Christa Isabella Obando Guzmán\n- Fabian Prado Dluzniewski\n- Luis Fernando Mendoza Alvarez\n\n"
    "CC3084 Data Science, Universidad del Valle de Guatemala, 2026."
)
