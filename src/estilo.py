"""Paleta y estilo compartidos por todas las visualizaciones (heredado del Lab 10).

Regla del tablero: cada color significa SIEMPRE lo mismo en toda la aplicacion.
- Origen (nacional / extranjero) y segmento (turista / excursionista) -> categoricos fijos.
- Observado en tinta negra; Estimacion en violeta con linea discontinua.
- Magnitudes (mapas de calor) -> una sola tonalidad de azul, de claro a oscuro.
- Estados (alerta, bien) -> colores reservados, nunca usados para series.
"""

from __future__ import annotations

import plotly.graph_objects as go

# Categoricos del observatorio. Cada color significa SIEMPRE lo mismo en todas las paginas.
# Azul / naranja vienen de la paleta validada del Lab 10 (pasan la prueba de daltonismo entre si).
COLORES_ORIGEN = {"Nacional": "#2a78d6", "Extranjero": "#eb6834"}
COLORES_SEGMENTO = {"Turista (> 1 día)": "#1baf7a", "Excursionista (< 1 día)": "#e87ba4"}
COLOR_EVENTO = "#eda100"          # dias con festividad (marcadores y franjas)
COLOR_REAL = "#161616"            # dato observado: tinta
COLOR_HISTORIA = "#898781"        # referencia / contexto: gris
COLOR_ESTIMADO = "#8a3ffc"        # toda Estimacion: violeta y linea discontinua
COLOR_DESTACADO = "#0f62fe"       # elemento seleccionado en una grafica enlazada
COLOR_OCUPACION = "#005d5d"       # ocupacion hotelera (modulo 3)
COLORES_CLASE = {
    "Hub comercial": "#0d366b",
    "Larga estancia": "#008300",
    "Visita corta": "#9f1853",
    "Intermedio": "#898781",
}

# Secuencial (magnitud): azul claro -> oscuro
SECUENCIAL_AZUL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
ESCALA_SECUENCIAL = [[i / (len(SECUENCIAL_AZUL) - 1), c] for i, c in enumerate(SECUENCIAL_AZUL)]

# Divergente (polaridad respecto a una base, p. ej. indice 2019 = 100):
# rojo = por debajo de la base, gris = igual, azul = por encima. Solo en mapas de calor con barra de color.
ESCALA_DIVERGENTE = [
    [0.0, "#d25757"],
    [0.25, "#e66767"],
    [0.5, "#f0efec"],
    [0.75, "#6da7ec"],
    [1.0, "#4a8ee0"],
]

# Estados reservados
ESTADO = {"bien": "#0ca30c", "alerta": "#fab219", "critico": "#d03b3b"}

# Tinta y superficies
SUPERFICIE = "#ffffff"
TINTA = "#161616"
TINTA_SECUNDARIA = "#525252"
TINTA_TENUE = "#6f6f6f"
CUADRICULA = "#e0e0e0"
EJE = "#c6c6c6"

# Misma familia que la interfaz (IBM Plex Sans); "IBM Plex Sans" es el nombre instalado que usa kaleido al exportar
FUENTE = 'PlexSans, "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif'


def aplicar_estilo(fig: go.Figure, alto: int = 420) -> go.Figure:
    """Ejes y cuadricula discretos para que el dato sea lo que resalta."""
    fig.update_layout(
        height=alto,
        font=dict(family=FUENTE, size=12, color=TINTA_SECUNDARIA),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=8, t=8, b=8),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            title_text="",
            font=dict(color=TINTA_SECUNDARIA),
        ),
        hoverlabel=dict(bgcolor="white", font=dict(family=FUENTE, color=TINTA), bordercolor=CUADRICULA),
        separators=".,",
        bargap=0.25,
    )
    fig.update_xaxes(
        showgrid=False, linecolor=EJE, automargin=True, tickfont=dict(color=TINTA_TENUE), title_font=dict(color=TINTA_SECUNDARIA)
    )
    fig.update_yaxes(
        automargin=True,
        gridcolor=CUADRICULA,
        zeroline=False,
        linecolor=EJE,
        tickfont=dict(color=TINTA_TENUE),
        title_font=dict(color=TINTA_SECUNDARIA),
    )
    return fig


MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def formato_numero(valor: float) -> str:
    """12345678 -> '12.3 M'; 45678 -> '45.7 mil'."""
    if abs(valor) >= 1_000_000:
        return f"{valor / 1_000_000:,.1f} M"
    if abs(valor) >= 1_000:
        return f"{valor / 1_000:,.1f} mil"
    return f"{valor:,.0f}"
