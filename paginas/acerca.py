"""Acerca del observatorio: definiciones, paleta de color, limitaciones y equipo."""

import streamlit as st

from src.estilo import (
    COLOR_DESTACADO, COLOR_ESTIMADO, COLOR_EVENTO, COLOR_HISTORIA, COLOR_OCUPACION, COLOR_REAL, COLORES_CLASE, COLORES_ORIGEN,
    COLORES_SEGMENTO, SIMBOLOS_CLASE, TRAZOS_CLASE, contraste,
)
from src.ui import encabezado_pagina

FORMA_ES = {"circle": "círculo", "diamond": "rombo", "square": "cuadrado"}
TRAZO_ES = {"solid": "línea continua", "dash": "guiones", "dot": "punteada"}

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
st.markdown(
    "Tres reglas de teoría del color guían la paleta:\n\n"
    "1. **Tono para categorías, luminosidad para magnitudes.** Las categorías (origen, segmento, clase) usan tonos "
    "distintos; las magnitudes (mapas de calor) usan un solo tono de azul que va de claro a oscuro, porque el ojo ordena "
    "la luminosidad sin necesidad de leyenda.\n"
    "2. **Contraste suficiente.** Todo color de dato llega al menos a **3:1** contra el fondo blanco de los mosaicos "
    "(WCAG 1.4.11, marcas gráficas). Los colores de segmento y festividad se oscurecieron lo justo para lograrlo, sin "
    "cambiar su tono.\n"
    "3. **Nunca solo el color.** Los pares que una persona con daltonismo podría confundir llevan una segunda señal "
    "(WCAG 1.4.1): el excursionista tiene trama de puntos y cada clase de municipio tiene su propia forma y trazo.\n\n"
    "El tema es claro y fijo: los contrastes se midieron contra superficies claras y el tablero no ofrece modo oscuro, "
    "para que ninguna gráfica pierda legibilidad."
)
PALETA = [
    ("Nacional", COLORES_ORIGEN["Nacional"], "Azul y naranja son complementarios: el par que mejor se separa con cualquier tipo de daltonismo."),
    ("Extranjero", COLORES_ORIGEN["Extranjero"], "Naranja cálido para el visitante internacional, foco de la promoción del INGUAT."),
    ("Turista (> 1 día)", COLORES_SEGMENTO["Turista (> 1 día)"], "Verde: pernocta y permanencia."),
    ("Excursionista (< 1 día)", COLORES_SEGMENTO["Excursionista (< 1 día)"], "Rosa con trama de puntos: con deuteranopia el verde y el rosa se acercan, la trama los separa."),
    ("Dato observado", COLOR_REAL, "Tinta negra: lo medido es lo que más resalta."),
    ("Estimación", COLOR_ESTIMADO, "Violeta y línea discontinua: un tono que no se usa para nada más, para que una estimación nunca se lea como dato."),
    ("Festividad", COLOR_EVENTO, "Ámbar: color de aviso, se distingue sobre la serie gris."),
    ("Selección / filtro", COLOR_DESTACADO, "Azul interactivo de IBM Carbon: marca lo que se eligió con un clic."),
    ("Contexto", COLOR_HISTORIA, "Gris: referencias y series de fondo, para no competir con el dato."),
    ("Ocupación hotelera", COLOR_OCUPACION, "Verde azulado oscuro: porcentajes de hoteles, distintos de las personas."),
] + [(f"Clase: {k}", v, f"Marcador {FORMA_ES[SIMBOLOS_CLASE[k]]}, {TRAZO_ES[TRAZOS_CLASE[k]]}. Con protanopia el "
       "azul marino y el vino se acercan; la forma los separa.")
     for k, v in COLORES_CLASE.items() if k != "Intermedio"]
filas = "".join(
    f'<tr><td><span style="width:28px;height:14px;background:{c};display:inline-block;vertical-align:middle"></span> '
    f'<code>{c}</code></td><td>{t}</td><td style="text-align:right;font-variant-numeric:tabular-nums">'
    f'{contraste(c):.1f}:1</td><td>{p}</td></tr>' for t, c, p in PALETA)
st.html(
    '<div style="overflow-x:auto"><table style="border-collapse:collapse;font-size:.8125rem;width:100%">'
    '<thead><tr style="text-align:left;border-bottom:1px solid #c6c6c6"><th>Color</th><th>Significado</th>'
    '<th style="text-align:right">Contraste</th><th>Por qué</th></tr></thead>'
    f'<tbody>{filas}</tbody></table></div>'
    '<style>td,th{padding:.35rem .5rem;border-bottom:1px solid #e0e0e0;vertical-align:top}</style>'
)

st.subheader("Limitaciones")
st.markdown(
    "- **Datos sintéticos en esta versión**: las bases institucionales son confidenciales; el tablero lee los reales "
    "si se colocan en `data/raw/` (o en la carpeta de `OBS_DATOS`) y se reprocesa solo al detectar archivos nuevos.\n"
    "- Solo se usan los registros de los 10 municipios del lago (Sololá); otros destinos de las bases se reportan en "
    "Calidad de los datos y se excluyen.\n"
    "- La telefonía no cubre enero y febrero de 2026: no hay comparación interanual directa 2025 vs 2026.\n"
    "- Los nacionales incorporan factor de expansión: se reportan separados de los extranjeros.\n"
    "- Hotelería formal y plataformas digitales (Airbnb) son universos distintos.\n"
    "- El corte de oferta 2026 es parcial (primer trimestre, con valores repetidos del año previo).\n"
    "- Las encuestas disponibles no traen factor de expansión: no se usaron, porque no representan al total de visitantes.\n"
    "- k-medias con 10 municipios es un contraste de la regla, no una clasificación independiente; su estabilidad se "
    "reporta en el módulo 4."
)

st.subheader("Equipo · Grupo 3")
st.markdown(
    "- Anthony Lou Schwank\n- Christa Isabella Obando Guzmán\n- Fabian Prado Dluzniewski\n- Luis Fernando Mendoza Alvarez\n\n"
    "CC3084 Data Science, Universidad del Valle de Guatemala, 2026."
)
