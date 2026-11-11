"""Paleta y estilo compartidos por todas las visualizaciones (heredado del Lab 10).

Regla del tablero: cada color significa SIEMPRE lo mismo en toda la aplicacion.
- Origen (nacional / extranjero) y segmento (turista / excursionista) -> categoricos fijos.
- Observado en tinta negra; Estimacion en violeta con linea discontinua.
- Magnitudes (mapas de calor) -> una sola tonalidad de azul, de claro a oscuro.
- Estados (alerta, bien) -> colores reservados, nunca usados para series.
"""

from __future__ import annotations

from contextvars import ContextVar

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
    "Visita corta": "#0f8b8d",  # teal (portada); el modulo 4 lo reasigna a su paleta
    "Intermedio": "#898781",
}

# Identidad institucional (portada y barra lateral): derivados del azul #0084bb, de profundo a bruma.
# El blanco sobre AZUL_PROFUNDO..AZUL_MEDIO cumple contraste AA; sobre AZUL_GUATE solo en texto grande.
AZULES = {
    "profundo": "#00314d",
    "oscuro": "#004a73",
    "medio": "#0067a0",
    "guate": "#0084bb",
    "claro": "#4fb0dc",
    "cielo": "#a9daf0",
    "bruma": "#e3f3fa",
}

# Identidad de cada seccion: degradado (inicio -> fin) y color de acento legible sobre blanco (iconos, texto).
# Se usa en la barra lateral y queda disponible para el encabezado de cada modulo.
# `banda`: 4 paradas del encabezado (de oscuro a brillante, el texto blanco va sobre la parte oscura);
# `profundo`: titulos y cifras.
GRADIENTES_MODULO = {
    "inicio": {"desde": "#0084bb", "hasta": "#4fb0dc", "acento": "#0067a0"},
    "m1_demanda": {"desde": "#d62839", "hasta": "#f77f00", "acento": "#c4262f", "profundo": "#6d0f1c",
                   "banda": ["#c4262f", "#d93a2b", "#ec5f22", "#f7941d"]},
    "m2_temporal": {"desde": "#f77f00", "hasta": "#fcbf49", "acento": "#c25e00", "profundo": "#6b3200",
                    "banda": ["#d35f00", "#e8760a", "#f39c12", "#fbc04a"]},
    "m3_oferta": {"desde": "#d9c22e", "hasta": "#2d9f5a", "acento": "#1b7a43", "profundo": "#0f4d2b",
                  "banda": ["#1e8a4c", "#2f9a56", "#5bb25a", "#c9c829"]},
    "m4_municipios": {"desde": "#4cc9f0", "hasta": "#7b2cbf", "acento": "#6a2bb0", "profundo": "#2a0b5e",
                      "banda": ["#6a2bb0", "#7b4fd0", "#6f8fe0", "#4cc9f0"]},
    "calidad": {"desde": "#8d9aa6", "hasta": "#c3ccd4", "acento": "#55626e"},
    "acerca": {"desde": "#8d9aa6", "hasta": "#c3ccd4", "acento": "#55626e"},
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

# ---------------------------------------------------------------------------------------------
# Graficas con el color de su modulo
#
# Cada modulo reasigna los colores base a su familia (rojo/naranja, naranja/amarillo, verde, celeste/morado).
# Dentro de una pagina cada color sigue significando una sola cosa, y los pares que se comparan (nacional vs.
# extranjero, turista vs. excursionista, clases) se separan por claridad ademas de por tono. La Estimacion
# conserva su linea discontinua y su rotulo. La conversion se hace al final de aplicar_estilo segun el tema
# activo de la pagina (lo fija encabezado_pagina), asi las funciones de graficas no cambian.

_BASE_SECUENCIAL = SECUENCIAL_AZUL + ["#e5eefb"]
_BASE = {
    "nacional": COLORES_ORIGEN["Nacional"], "extranjero": COLORES_ORIGEN["Extranjero"],
    "turista": COLORES_SEGMENTO["Turista (> 1 día)"], "excursionista": COLORES_SEGMENTO["Excursionista (< 1 día)"],
    "evento": COLOR_EVENTO, "estimado": COLOR_ESTIMADO, "destacado": COLOR_DESTACADO, "ocupacion": COLOR_OCUPACION,
    "hub": COLORES_CLASE["Hub comercial"], "larga": COLORES_CLASE["Larga estancia"], "corta": COLORES_CLASE["Visita corta"],
    # Neutros de las graficas: tinta del dato observado, gris de contexto (otros departamentos, serie base),
    # grises claros de barras de referencia y del extremo bajo de las escalas, cuadricula y ejes
    "tinta": COLOR_REAL, "contexto": COLOR_HISTORIA, "claro": "#d0d0d0", "muy_claro": "#f2f2f2",
    "cuadricula": "#e0e0e0", "eje": "#c6c6c6",
}
# Neutros de cada modulo: tinta = tono profundo; contexto = version apagada del tono (se distingue del dato
# principal y de los eventos); claros, cuadricula y ejes = tintes suaves
_NEUTROS = {
    "m1_demanda": {"tinta": "#6d0f1c", "contexto": "#e0a092", "claro": "#f6cfc4", "muy_claro": "#fdf0ec",
                   "cuadricula": "#f6dcd5", "eje": "#e9b7aa"},
    "m2_temporal": {"tinta": "#6b3200", "contexto": "#c99a6b", "claro": "#f7dcb8", "muy_claro": "#fff6ea",
                    "cuadricula": "#f5e3cc", "eje": "#e6c49c"},
    "m3_oferta": {"tinta": "#0f4d2b", "contexto": "#a9c9a8", "claro": "#cfe5c4", "muy_claro": "#f1f8ec",
                  "cuadricula": "#dcebd6", "eje": "#b9d4b0"},
    "m4_municipios": {"tinta": "#2a0b5e", "contexto": "#b3a6d6", "claro": "#d9d0f0", "muy_claro": "#f4f0fb",
                      "cuadricula": "#e4def3", "eje": "#c5b8e6"},
}
_RAMPAS = {
    "m1_demanda": ["#fde4dc", "#fbbfa8", "#f7956f", "#ef6b43", "#d9442d", "#b02a26", "#7a1020"],
    "m2_temporal": ["#fff1d6", "#fdd99a", "#fbbd5c", "#f59e2c", "#e07b10", "#b45a05", "#7a3b00"],
    "m3_oferta": ["#eef6d8", "#cfe8a6", "#9fd17f", "#62b56a", "#2f9a56", "#1b7a43", "#0f4d2b"],
    "m4_municipios": ["#e2f6fd", "#b3e5f7", "#7fc8ee", "#7f9fe3", "#7b6fd0", "#6a2bb0", "#3a1078"],
}
_CATEGORICOS = {
    "m1_demanda": {"nacional": "#a51d2d", "extranjero": "#f28c28", "turista": "#d9442d", "excursionista": "#f9b98a",
                   "destacado": "#5c0b17", "evento": "#f2a900", "estimado": "#5c0b17"},
    "m2_temporal": {"nacional": "#a14a00", "extranjero": "#f7b538", "turista": "#e07000", "excursionista": "#fcd98a",
                    "evento": "#f2a900", "estimado": "#e8590c", "destacado": "#c2410c"},
    "m3_oferta": {"nacional": "#16673a", "extranjero": "#c9b52a", "turista": "#2f9a56", "excursionista": "#d9c22e",
                  "ocupacion": "#1b7a43", "destacado": "#0b3d22", "estimado": "#0b3d22"},
    "m4_municipios": {"nacional": "#6a2bb0", "extranjero": "#3fb8e6", "turista": "#1fa6d6", "excursionista": "#c3a6f0",
                      "hub": "#3a1078", "larga": "#1fa6d6", "corta": "#b5179e", "destacado": "#24094f",
                      "estimado": "#24094f", "evento": "#b5179e"},
}
# Divergente (indice frente a una base): por debajo en la punta clara del modulo, por encima en la oscura
_DIVERGENTES = {
    "m3_oferta": ["#b08900", "#d9c22e", "#f0efec", "#62b56a", "#1b7a43"],
    "m4_municipios": ["#1fa6d6", "#86d3f0", "#f0efec", "#a98ae0", "#6a2bb0"],
}


def _mapa_tema(tema: str) -> dict[str, str]:
    mapa = {}
    rampa = _RAMPAS[tema]
    for i, c in enumerate(_BASE_SECUENCIAL):
        mapa[c.lower()] = rampa[min(i, len(rampa) - 1)] if i < len(SECUENCIAL_AZUL) else rampa[0]
    for clave, c in {**_NEUTROS[tema], **_CATEGORICOS[tema]}.items():
        mapa[_BASE[clave].lower()] = c
    if tema in _DIVERGENTES:
        for (_, base), nuevo in zip(ESCALA_DIVERGENTE, _DIVERGENTES[tema]):
            mapa[base.lower()] = nuevo
    return mapa


PALETAS_GRAFICAS = {tema: _mapa_tema(tema) for tema in _RAMPAS}
_TEMA_ACTIVO: ContextVar[str | None] = ContextVar("tema_activo", default=None)


def usar_tema(tema: str | None) -> None:
    """Fija el tema de la pagina en curso (cada sesion de Streamlit corre en su propio hilo)."""
    _TEMA_ACTIVO.set(tema if tema in PALETAS_GRAFICAS else None)


def color(base: str) -> str:
    """Color base -> color del tema activo (para HTML hecho a mano, como las etiquetas de clase)."""
    tema = _TEMA_ACTIVO.get()
    return PALETAS_GRAFICAS[tema].get(base.lower(), base) if tema else base


def _recolorear(fig: go.Figure, mapa: dict[str, str]) -> None:
    def r(x):
        if isinstance(x, str):
            return mapa.get(x.lower(), x)
        if isinstance(x, (list, tuple)):
            return [r(i) for i in x]
        if isinstance(x, dict):
            return {k: r(v) for k, v in x.items()}
        return x

    d = fig.to_dict()
    fig.data = ()
    fig.add_traces(r(d["data"]))
    fig.layout = r(d["layout"])


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
    tema = _TEMA_ACTIVO.get()
    if tema:
        _recolorear(fig, PALETAS_GRAFICAS[tema])
    return fig


MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def formato_numero(valor: float) -> str:
    """12345678 -> '12.3 M'; 45678 -> '45.7 mil'."""
    if abs(valor) >= 1_000_000:
        return f"{valor / 1_000_000:,.1f} M"
    if abs(valor) >= 1_000:
        return f"{valor / 1_000:,.1f} mil"
    return f"{valor:,.0f}"
