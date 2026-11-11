"""Componentes de interfaz del tablero.

El lenguaje visual sigue la estructura de IBM Carbon para productos de datos: escala de
grises g10, mosaicos blancos de borde fino, tipografia IBM Plex Sans, etiquetas pequenas
y la explicacion de cada grafica detras de un icono de informacion. Los contenedores
usan `key`; Streamlit les agrega la clase `st-key-<key>` y el CSS se engancha a ella.
"""

from __future__ import annotations

import html
from contextlib import contextmanager
from zlib import crc32

import pandas as pd
import streamlit as st

from src import ilustraciones
from src.estilo import GRADIENTES_MODULO, usar_tema


# Etiqueta, color de texto y fondo (tags de Carbon: blue 20, gray 20, purple 20)
TIPO_INFO = {
    "observado": ("Observado", "#0043ce", "#d0e2ff"),
    "interpretacion": ("Interpretación", "#393939", "#e0e0e0"),
    "estimacion": ("Estimación", "#6929c4", "#e8daff"),
    "base": ("Versión base", "#8e6a00", "#fcf4d6"),
}


MESES_CORTOS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

_CSS = """
<style>
[data-testid="stMainBlockContainer"] { max-width: 1440px; padding: 1.25rem 2rem 3rem; }
[data-testid="stDecoration"] { display: none; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebarContent"] { padding-top: .25rem; }
[data-testid="stVerticalBlock"] { gap: .75rem; }

/* encabezado de pagina */
.ot-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 2rem; padding: .25rem 0 .75rem; }
.ot-crumb { font-size: .75rem; color: #6f6f6f; margin-bottom: .2rem; }
.ot-h1 { font-size: 1.75rem; font-weight: 400; line-height: 1.25; color: #161616; margin: 0; }
.ot-desc { font-size: .875rem; color: #525252; margin: .35rem 0 0; max-width: 56rem; line-height: 1.45; }
.ot-meta { font-size: .75rem; color: #6f6f6f; text-align: right; white-space: nowrap; line-height: 1.6; }
.ot-meta b { color: #161616; font-weight: 500; }

/* mosaicos */
[class*="st-key-tile-"], [class*="st-key-filtros-"] { background: #ffffff; border: 1px solid #e0e0e0; padding: 1rem 1rem .75rem !important; gap: .5rem; }
[class*="st-key-filtros-"] { padding: .75rem 1rem .25rem !important; }
.ot-tt { font-size: .9375rem; font-weight: 600; color: #161616; line-height: 1.3; }
.ot-ts { font-size: .75rem; color: #6f6f6f; margin-top: .15rem; line-height: 1.4; }
.ot-tags { display: flex; gap: .4rem; justify-content: flex-end; align-items: center; flex-wrap: wrap; padding-top: .1rem; }
.ot-tag { font-size: .6875rem; line-height: 1.1rem; padding: 0 .5rem; border-radius: 1rem; white-space: nowrap; }
[class*="st-key-tile-"] [data-testid="stPopover"] button { border: none; background: transparent; min-height: 1.75rem; padding: 0 .25rem; color: #525252; }
[class*="st-key-tile-"] [data-testid="stPopover"] button:hover { background: #e8e8e8; color: #161616; }
[class*="st-key-tile-"] [data-testid="stPopover"] button div[aria-hidden="true"] { display: none; }
.ot-chip { font-size: .6875rem; line-height: 1.1rem; padding: 0 .5rem; background: #161616; color: #ffffff; white-space: nowrap; max-width: 22rem; overflow: hidden; text-overflow: ellipsis; }

/* indicadores */
.ot-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: .75rem; }
.ot-kpi { background: #ffffff; border: 1px solid #e0e0e0; padding: .9rem 1rem .8rem; display: flex; flex-direction: column; gap: .2rem; }
.ot-kpi .l { font-size: .75rem; color: #525252; }
.ot-kpi .row { display: flex; justify-content: space-between; align-items: flex-end; gap: .75rem; }
.ot-kpi .v { font-size: 1.875rem; font-weight: 300; color: #161616; line-height: 1.15; font-variant-numeric: tabular-nums; letter-spacing: -.01em; }
.ot-kpi .d { font-size: .75rem; color: #525252; font-variant-numeric: tabular-nums; }
.ot-kpi .d .up { color: #198038; font-weight: 600; }
.ot-kpi .d .down { color: #da1e28; font-weight: 600; }
.ot-kpi svg { flex: none; }

/* notas bajo las graficas */
[class*="st-key-nota-"] { border-left: 2px solid #8d8d8d; padding: .1rem 0 .1rem .75rem !important; gap: 0; }
[class*="st-key-nota-observado"] { border-left-color: #0f62fe; }
[class*="st-key-nota-estimacion"] { border-left-color: #8a3ffc; }
[class*="st-key-nota-"] p { font-size: .8125rem; color: #393939; line-height: 1.5; margin-bottom: .2rem; }
.ot-nl { font-size: .6875rem; color: #6f6f6f; margin-bottom: .1rem; }

/* accesos de la portada */
[class*="st-key-acceso-"] { background: #ffffff; border: 1px solid #e0e0e0; padding: 1rem !important; min-height: 10.5rem; justify-content: space-between; }
.ot-acc-t { font-size: 1rem; font-weight: 600; color: #161616; }
.ot-acc-d { font-size: .8125rem; color: #525252; line-height: 1.5; margin-top: .3rem; }

[data-testid="stCaptionContainer"] { color: #6f6f6f; }

/* barra lateral blanca; cada enlace lleva el degradado de su seccion (reglas por pagina en _css_navegacion) */
[data-testid="stSidebar"] { border-right: 1px solid #e0e0e0; }
[data-testid="stSidebarHeader"] { padding-bottom: .5rem; border-bottom: 1px solid #f0f0f0; margin-bottom: .5rem; }
[data-testid="stNavSectionHeader"] { text-transform: uppercase; letter-spacing: .08em; font-size: .6875rem !important; font-weight: 600; }
[data-testid="stNavSectionHeader"] * { color: #8d8d8d !important; }
[data-testid="stSidebarNavLink"] { position: relative; border-radius: 6px; margin: 1px 0; padding-left: .85rem !important;
  transition: background .15s; }
[data-testid="stSidebarNavLink"]::before { content: ""; position: absolute; left: 0; top: 7px; bottom: 7px; width: 4px;
  border-radius: 4px; background: linear-gradient(180deg, var(--g-desde), var(--g-hasta)); opacity: .35; transition: opacity .15s, top .15s, bottom .15s; }
[data-testid="stSidebarNavLink"] span { color: #393939 !important; }
[data-testid="stSidebarNavLink"] [data-testid="stIconMaterial"] { color: var(--g-acento) !important; }
[data-testid="stSidebarNavLink"]:hover { background: linear-gradient(90deg, var(--g-tinte), transparent 85%); }
[data-testid="stSidebarNavLink"]:hover::before { opacity: .8; }
[data-testid="stSidebarNavLink"][aria-current="page"] { background: linear-gradient(90deg, var(--g-tinte-fuerte), var(--g-tinte-hasta) 65%, transparent); }
[data-testid="stSidebarNavLink"][aria-current="page"]::before { opacity: 1; top: 4px; bottom: 4px; }
[data-testid="stSidebarNavLink"][aria-current="page"] span { color: #161616 !important; font-weight: 600; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { font-size: .7rem; line-height: 1.45; }
</style>
"""


def _clave(*partes: object) -> str:
    """Clave estable entre ejecuciones para contenedores con estilo propio."""
    return f"{crc32('|'.join(map(str, partes)).encode()):x}"


def _tinte(hex_color: str, alfa: float) -> str:
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r}, {g}, {b}, {alfa})"


def _solido(hex_color: str, alfa: float) -> str:
    """El color mezclado sobre blanco, como hex solido (sin transparencia)."""
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(255 + (c - 255) * alfa):02x}" for c in (r, g, b))


def _css_navegacion() -> str:
    """Variables de color de cada enlace de la barra lateral segun su pagina (src/estilo.py, GRADIENTES_MODULO).
    La portada es la pagina por defecto: su enlace no lleva nombre en la URL, asi que es la regla base."""
    def variables(g: dict) -> str:
        return (f"--g-desde: {g['desde']}; --g-hasta: {g['hasta']}; --g-acento: {g['acento']}; "
                f"--g-tinte: {_tinte(g['desde'], .07)}; --g-tinte-fuerte: {_tinte(g['desde'], .16)}; "
                f"--g-tinte-hasta: {_tinte(g['hasta'], .12)};")

    reglas = [f'[data-testid="stSidebarNavLink"] {{ {variables(GRADIENTES_MODULO["inicio"])} }}']
    reglas += [f'[data-testid="stSidebarNavLink"][href*="/{pagina}"] {{ {variables(g)} }}'
               for pagina, g in GRADIENTES_MODULO.items() if pagina != "inicio"]
    return "<style>\n" + "\n".join(reglas) + "\n</style>"


def estilo_global() -> None:
    st.html(_CSS + _css_navegacion())


def _css_tema(tema: str) -> str:
    """Identidad del modulo con el lenguaje de la portada: una banda de color (la unica pieza en degradado)
    y debajo mosaicos blancos redondeados de borde tenue, con titulos y cifras en el tono profundo del modulo y
    un acento solido en los indicadores. Todo se limita a la pagina que contiene .ot-tema-<tema>."""
    g = GRADIENTES_MODULO[tema]
    d, a, p = g["desde"], g["acento"], g["profundo"]
    b0, b1, b2, b3 = g["banda"]
    P = f'[data-testid="stMain"]:has(.ot-tema-{tema})'
    borde = _solido(a, .22)
    fondo, suave, claro = _solido(d, .045), _solido(a, .07), _solido(a, .14)
    return f"""<style>
{P} {{ background: {fondo}; }}

/* banda principal: misma forma y degradado que la de la portada, con los colores del modulo y su ilustracion */
{P} .ot-banda {{ position: relative; overflow: hidden; display: flex; align-items: center; min-height: 10.5rem;
  padding: 1.4rem 2rem 1.5rem; margin-bottom: .35rem; border-radius: 14px; color: #fff;
  background: linear-gradient(118deg, {b0} 0%, {b1} 30%, {b2} 58%, {b3} 100%); box-shadow: 0 10px 30px {_tinte(b0, .22)}; }}
{P} .ot-banda-txt {{ position: relative; z-index: 1; max-width: 44rem; }}
{P} .ot-banda .ot-crumb {{ color: rgba(255, 255, 255, .88); font-weight: 600; letter-spacing: .1em; text-transform: uppercase;
  font-size: .72rem; margin: 0; }}
{P} .ot-banda .ot-h1 {{ color: #fff; font-size: 2.2rem; font-weight: 300; line-height: 1.1; margin: .4rem 0 0; }}
{P} .ot-banda .ot-crumb, {P} .ot-banda .ot-h1 {{ text-shadow: 0 1px 2px {_tinte(p, .25)}; }}
{P} .ot-banda-art {{ position: absolute; right: 0; bottom: 0; height: 100%; aspect-ratio: 600 / 220; max-width: 62%;
  background: url("{ilustraciones.url(tema, b0)}") right bottom / contain no-repeat; pointer-events: none; }}
@media (max-width: 640px) {{ {P} .ot-banda {{ margin-top: 1.75rem; min-height: 9.5rem; align-items: flex-start; }}
  {P} .ot-banda-art {{ height: 60%; max-width: 100%; }} {P} .ot-banda .ot-h1 {{ font-size: 1.7rem; }} }}

/* superficies solidas: fondo tenido, mosaicos blancos con borde superior de color, indicadores y filtros en
   tinte solido del modulo */
{P} [class*="st-key-tile-"] {{ background: #ffffff; border: 1px solid {borde}; border-top: 4px solid {a};
  border-radius: 12px; box-shadow: 0 2px 10px {_tinte(p, .06)}; }}
{P} [class*="st-key-filtros-"] {{ background: {suave}; border: 1px solid {borde}; border-radius: 12px; }}
{P} .ot-tt {{ color: {p}; }}
{P} .ot-kpi {{ background: {suave}; border: 1px solid {borde}; border-left: 5px solid {a}; border-radius: 10px; }}
{P} .ot-kpi .l {{ color: {a}; font-weight: 600; }}
{P} .ot-kpi .v {{ color: {p}; font-weight: 400; }}
{P} .ot-kpi polyline {{ stroke: {a}; }}
{P} .ot-kpi circle {{ fill: {p}; }}
{P} .ot-chip {{ background: {a}; border-radius: 999px; padding: 0 .6rem; }}
{P} [class*="st-key-nota-"] {{ background: {suave}; border-radius: 0 8px 8px 0; padding: .4rem .6rem .3rem .75rem !important; }}
{P} [data-testid="stExpander"] details {{ border-radius: 10px; border-color: {borde}; background: {claro}; }}
{P} [data-testid="stExpander"] details > div {{ background: #ffffff; }}

/* controles con la paleta del modulo (en lugar del gris del tema) */
{P} [data-testid="stSelectbox"] [role="group"] {{ background: #ffffff; border: 1px solid {borde}; border-radius: 8px; }}
{P} [data-testid="stSelectbox"] [role="group"]:hover {{ border-color: {a}; }}
{P} button[data-variant="segmented_control"] {{ background: #ffffff; border-color: {borde}; color: {p}; }}
{P} button[data-variant="segmented_control"]:hover {{ background: {suave}; border-color: {a}; color: {p}; }}
{P} button[data-variant="segmented_control"][data-selected="true"] {{ background: {a}; border-color: {a}; color: #ffffff; }}
{P} button[data-variant="segmented_control"][data-selected="true"] * {{ color: #ffffff; }}
{P} [data-testid="stCheckbox"] label > span + div {{ background: {borde}; }}
{P} [data-testid="stCheckbox"] label[data-selected="true"] > span + div {{ background: {a}; }}
{P} [data-testid="stSlider"] div:has(> div > input[type="range"]) {{ background: {a}; box-shadow: 0 0 0 3px {_tinte(a, .18)}; }}
/* la pista se dibuja con un degradado en linea (negro = rango elegido): una capa del acento en modo "screen"
   vuelve el negro del color del modulo y el gris claro casi blanco, sin perder que tramo esta elegido */
{P} [data-testid="stSlider"] [role="group"] > div > div:first-child:empty {{ position: relative; }}
{P} [data-testid="stSlider"] [role="group"] > div > div:first-child:empty::after {{ content: ""; position: absolute; inset: 0;
  background: {a}; mix-blend-mode: screen; border-radius: inherit; pointer-events: none; }}
{P} [data-testid="stSlider"] [data-testid="stSliderThumbValue"],
{P} [data-testid="stSlider"] [data-testid="stSliderTickBarMin"],
{P} [data-testid="stSlider"] [data-testid="stSliderTickBarMax"] {{ color: {p}; }}
{P} [data-testid="stTable"] table {{ border-collapse: collapse; width: 100%; font-size: .8rem; }}
{P} [data-testid="stTable"] th {{ background: {suave}; color: {p}; font-weight: 600; border-bottom: 2px solid {a}; }}
{P} [data-testid="stTable"] td, {P} [data-testid="stTable"] th {{ border-color: {borde}; padding: .35rem .6rem; }}
{P} [data-testid="stTable"] tbody tr:hover td {{ background: {suave}; }}
</style>"""


def encabezado_pagina(seccion: str, titulo: str, descripcion: str | None = None, meta: str | None = None,
                      tema: str | None = None) -> None:
    """Encabezado de pagina. Con `tema` (clave de GRADIENTES_MODULO) se dibuja como la banda de la portada,
    con el degradado y la ilustracion del modulo, y solo lleva el modulo y el titulo (la descripcion y la
    cobertura se omiten); la pagina toma ademas sus acentos y la paleta de graficas."""
    usar_tema(tema)
    if tema:
        st.html(
            _css_tema(tema)
            + f'<div class="ot-banda ot-tema-{tema}"><div class="ot-banda-txt"><div class="ot-crumb">{html.escape(seccion)}</div>'
            f'<h1 class="ot-h1">{html.escape(titulo)}</h1></div><div class="ot-banda-art"></div></div>'
        )
        return
    desc = f'<p class="ot-desc">{descripcion}</p>' if descripcion else ""
    der = f'<div class="ot-meta">{meta}</div>' if meta else ""
    st.html(
        f'<div class="ot-head"><div><div class="ot-crumb">{html.escape(seccion)}</div>'
        f'<h1 class="ot-h1">{html.escape(titulo)}</h1>{desc}</div>{der}</div>'
    )


def _tag(tipo: str) -> str:
    texto, color, fondo = TIPO_INFO[tipo]
    return f'<span class="ot-tag" style="color:{color};background:{fondo}">{texto}</span>'


@contextmanager
def mosaico(clave: str, titulo: str, subtitulo: str, tipo: str, ayuda: str, filtro: str | None = None):
    """Mosaico de una visualizacion: titulo, subtitulo con unidades y alcance, etiqueta de
    tipo de dato, chip del filtro cruzado activo y la explicacion en un icono de informacion."""
    with st.container(key=f"tile-{clave}"):
        izq, der, info = st.columns([0.62, 0.32, 0.06], vertical_alignment="top", gap="small")
        izq.html(f'<div class="ot-tt">{html.escape(titulo)}</div><div class="ot-ts">{subtitulo}</div>')
        chip = f'<span class="ot-chip" title="{html.escape(filtro)}">Filtrado por: {html.escape(filtro)}</span>' if filtro else ""
        # La etiqueta de tipo (Observado / Estimacion) ya no se dibuja; solo el chip del filtro activo
        der.html(f'<div class="ot-tags">{chip}</div>')
        with info.popover("", icon=":material/info:", help="Acerca de esta gráfica"):
            st.markdown(ayuda)
        yield


def _sparkline(valores: list[float], ancho: int = 96, alto: int = 30) -> str:
    v = [float(x) for x in valores if pd.notna(x)]
    if len(v) < 2:
        return ""
    lo, hi = min(v), max(v)
    rango = hi - lo or 1.0
    pts = [(i * (ancho - 4) / (len(v) - 1) + 2, alto - 3 - (y - lo) / rango * (alto - 6)) for i, y in enumerate(v)]
    camino = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    x, y = pts[-1]
    return (
        f'<svg width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}" aria-hidden="true">'
        f'<polyline points="{camino}" fill="none" stroke="#8d8d8d" stroke-width="1.25"/>'
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" fill="#161616"/></svg>'
    )


def indicadores(items: list[dict]) -> None:
    """Fila de indicadores. Cada item: etiqueta, valor y, opcionalmente, delta (fraccion) con
    delta_texto, o contexto; y serie para la minigrafica."""
    celdas = []
    for it in items:
        if it.get("delta") is not None:
            d = it["delta"]
            clase, flecha = ("up", "▲") if d >= 0 else ("down", "▼")
            pie = f'<span class="{clase}">{flecha} {abs(d):.0%}</span> {html.escape(it.get("delta_texto", ""))}'
        else:
            pie = html.escape(it.get("contexto", ""))
        celdas.append(
            f'<div class="ot-kpi"><div class="l">{html.escape(it["etiqueta"])}</div>'
            f'<div class="row"><div class="v">{html.escape(it["valor"])}</div>{_sparkline(it.get("serie", []))}</div>'
            f'<div class="d">{pie}</div></div>'
        )
    st.html(f'<div class="ot-kpis">{"".join(celdas)}</div>')


def nota(tipo: str, texto: str) -> None:
    """Lectura breve bajo una grafica, marcada como observado, interpretacion o estimacion."""
    with st.container(key=f"nota-{tipo}-{_clave(texto)}"):
        st.html(f'<div class="ot-nl">{TIPO_INFO[tipo][0]}</div>')
        st.markdown(texto)


@contextmanager
def barra_filtros(nombre: str):
    with st.container(key=f"filtros-{nombre}"):
        yield


def personalizar_vista(opciones: dict[str, str], key: str) -> set[str]:
    """Menu para elegir que graficas de la pagina se muestran."""
    with st.popover("Personalizar vista", icon=":material/tune:", width="stretch"):
        elegidas = st.pills(
            "Gráficas visibles", list(opciones), format_func=lambda k: opciones[k],
            selection_mode="multi", default=list(opciones), key=key,
        )
    return set(elegidas or [])


def encabezado_con_vista(seccion: str, titulo: str, descripcion: str | None, meta: str, opciones: dict[str, str], key: str) -> set[str]:
    """Encabezado de pagina con el menu de vista a la derecha."""
    izq, der = st.columns([0.82, 0.18], vertical_alignment="bottom")
    with izq:
        encabezado_pagina(seccion, titulo, descripcion)
    with der:
        st.html(f'<div class="ot-meta" style="margin-bottom:.4rem">{meta}</div>')
        visibles = personalizar_vista(opciones, key)
    if not visibles:
        st.info("Todas las gráficas están ocultas. Actívelas desde **Personalizar vista**.", icon=":material/visibility_off:")
    return visibles


def sin_datos(mensaje: str) -> None:
    st.warning(mensaje, icon=":material/search_off:")


def aviso_sinteticos(origenes: dict[str, str]) -> None:
    """Banda visible cuando alguna fuente es sintetica (nunca se presenta como dato real)."""
    sint = [f for f, o in origenes.items() if o == "sintetico"]
    if sint:
        st.warning(
            "**Datos sintéticos de demostración.** Las bases institucionales son confidenciales; estas cifras "
            "tienen la misma estructura pero son inventadas y no deben citarse.",
            icon=":material/science:",
        )
