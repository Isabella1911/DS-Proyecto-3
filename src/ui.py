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


# Etiqueta, color de texto y fondo (tags de Carbon: blue 20, gray 20, purple 20)
TIPO_INFO = {
    "observado": ("Dato observado", "#0043ce", "#d0e2ff"),
    "interpretacion": ("Interpretación", "#393939", "#e0e0e0"),
    "estimacion": ("Estimación", "#6929c4", "#e8daff"),
    "base": ("Versión base", "#8e6a00", "#fcf4d6"),
}

FUENTE_DATOS = ("Fuentes: INGUAT (movilidad por telefonía móvil, flujo migratorio, ocupación y oferta hotelera, "
                "boletines de ocupación y encuesta en puestos fronterizos). Uso académico; no constituyen cifras oficiales.")

# Nota de fuente de cada mosaico, como en las publicaciones de las agencias estadisticas. Se busca por la
# clave del mosaico; todas cierran con "elaboración propia".
_TEL_M = "INGUAT, movilidad por telefonía móvil, base mensual (hoja Atitlan)"
_TEL_D = "INGUAT, movilidad por telefonía móvil, base diaria (hoja Atitlan)"
_MIG = "INGUAT, base de flujo migratorio 2009–2026"
_OCUP = "INGUAT, índice de ocupación hotelera mensual 2023–2025"
_OFERTA = "INGUAT, oferta hotelera 2022–2026 (cortes anuales)"
_BOL = "INGUAT, boletines de ocupación hotelera 2023, 2024 y 2025"
_FRON = "INGUAT, encuesta de perfil del visitante en puestos fronterizos (BD complementaria)"
FUENTES_MOSAICO = {
    "m1-mun": [_TEL_M], "m1-seg": [_TEL_M], "m1-top": [_TEL_M], "m1-estadia": [_TEL_M],
    "m2-diaria": [_TEL_D], "m2-lift": [_TEL_D], "m2-semana": [_TEL_D], "m2-estimacion": [_TEL_M, _MIG],
    "m2-validacion": [_TEL_M, _MIG], "m2-perfil": [_MIG], "m2-consistencia": [_TEL_M, _TEL_D],
    "m3-cap-anual": [_OFERTA], "m3-cap-tipo": [_OFERTA], "m3-ocup": [_OCUP], "m3-heat": [_OCUP],
    "m3-ventana": [_TEL_M, _BOL, _OCUP], "m3-inventario": [_BOL, _OFERTA, _OCUP], "m3-hosp": [_FRON], "m3-puesto": [_FRON], "m3-sub": [_TEL_M],
    "m4-cuadrante": [_TEL_M, _TEL_D], "m4-mapa": [_TEL_M, "mapa base © OpenStreetMap, © CARTO"],
    "m4-matriz": [_TEL_M, _TEL_D], "m4-huella": [_TEL_D], "m4-mercados": [_TEL_M], "m4-estac": [_TEL_M],
    "m4-serie": [_TEL_M], "m4-semana": [_TEL_D], "m4-paises": [_TEL_M],
    "inicio-cobertura": ["INGUAT, todas las fuentes del observatorio"], "cal-cobertura": ["INGUAT, todas las fuentes del observatorio"],
}

MESES_CORTOS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

# Barra de Plotly igual en todas las graficas: solo "descargar imagen" (PNG). Sin zoom, paneo, lazo
# ni seleccion por caja; la unica interaccion es el clic de las graficas enlazadas.
CONFIG_PLOTLY = {
    "displaylogo": False,
    "modeBarButtons": [["toImage"]],
    "toImageButtonOptions": {"format": "png", "scale": 2},
    "scrollZoom": False,
}

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
.ot-sec { font-size: 1.125rem; font-weight: 600; color: #161616; margin: 1rem 0 .1rem; padding-bottom: .35rem; border-bottom: 1px solid #c6c6c6; }
.ot-tt { font-size: .9375rem; font-weight: 600; color: #161616; line-height: 1.3; }
.ot-ts { font-size: .75rem; color: #6f6f6f; margin-top: .15rem; line-height: 1.4; }
.ot-tags { display: flex; gap: .375rem; justify-content: flex-start; align-items: center; flex-wrap: wrap; margin-top: .45rem; min-height: 1.1rem; }
.ot-src { font-size: .6875rem; color: #6f6f6f; line-height: 1.45; border-top: 1px solid #e0e0e0; padding-top: .4rem; margin-top: .1rem; }
.ot-src b { font-weight: 600; color: #525252; }
.ot-tag { font-size: .6875rem; line-height: 1.1rem; padding: 0 .5rem; border-radius: 1rem; white-space: nowrap; }
[class*="st-key-tile-"] [data-testid="stPopover"] button { border: none; background: transparent; min-height: 1.75rem; padding: 0 .25rem; color: #525252; }
[class*="st-key-tile-"] [data-testid="stPopover"] button:hover { background: #e8e8e8; color: #161616; }
[class*="st-key-tile-"] [data-testid="stPopover"] button div[aria-hidden="true"] { display: none; }
.ot-clic { color: #0f62fe; background: #ffffff; border: 1px solid #0f62fe; line-height: 1rem; }
.ot-chip { font-size: .6875rem; line-height: 1.1rem; padding: 0 .5rem; background: #161616; color: #ffffff; border-radius: 1rem; white-space: normal; }

/* tabla de recomendaciones (conclusiones) */
.ot-tabla-recs { width: 100%; border-collapse: collapse; font-size: .8125rem; color: #393939; }
.ot-tabla-recs th { text-align: left; font-weight: 600; color: #161616; border-bottom: 2px solid #161616; padding: .4rem .5rem; }
.ot-tabla-recs td { vertical-align: top; border-bottom: 1px solid #e0e0e0; padding: .5rem; line-height: 1.45; }
.ot-tabla-recs .ot-tag { background: #e8e8e8; color: #161616; display: inline-block; margin-top: .3rem; }
@media (max-width: 640px) {
  .ot-tabla-recs thead { display: none; }
  .ot-tabla-recs tr, .ot-tabla-recs td { display: block; width: 100%; }
  .ot-tabla-recs td { border-bottom: none; padding: .25rem 0; }
  .ot-tabla-recs tr { border-bottom: 1px solid #e0e0e0; padding: .4rem 0; }
}

/* indicadores */
.ot-kpis { display: grid; grid-template-columns: repeat(var(--n, 4), minmax(0, 1fr)); gap: .75rem; }
.ot-kpi { background: #ffffff; border: 1px solid #e0e0e0; padding: .9rem 1rem .8rem; display: flex; flex-direction: column; gap: .2rem; }
.ot-kpi .l { font-size: .75rem; color: #525252; min-height: 2.1em; line-height: 1.4; }
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

/* enlace al modulo siguiente */
[class*="st-key-siguiente-"] { background: #ffffff; border: 1px solid #e0e0e0; border-left: 3px solid #0f62fe; padding: .75rem 1rem !important; gap: .25rem; margin-top: .5rem; }
.ot-sig { font-size: .875rem; color: #393939; line-height: 1.5; }

/* accesos de la portada */
[class*="st-key-acceso-"] { background: #ffffff; border: 1px solid #e0e0e0; padding: 1rem !important; min-height: 10.5rem; justify-content: space-between; }
.ot-acc-t { font-size: 1rem; font-weight: 600; color: #161616; }
.ot-acc-d { font-size: .8125rem; color: #525252; line-height: 1.5; margin-top: .3rem; }

[data-testid="stCaptionContainer"] { color: #6f6f6f; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { font-size: .7rem; line-height: 1.45; }

/* pie institucional */
.ot-pie { margin-top: 2rem; padding-top: .9rem; border-top: 1px solid #c6c6c6; font-size: .75rem; color: #525252; line-height: 1.6; display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem; }
.ot-pie b { color: #161616; font-weight: 600; }

/* tableta: menos margen y encabezado en una columna */
@media (max-width: 1024px) {
  .ot-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .ot-pie { grid-template-columns: 1fr; gap: .5rem; }
  /* con la barra lateral plegada el logo flota arriba a la izquierda: se deja espacio y fondo opaco */
  [data-testid="stMainBlockContainer"] { padding: 3.25rem 1.25rem 2.5rem; }
  [data-testid="stHeader"] { background: #f4f4f4; }
  .ot-head { gap: 1rem; }
}
/* celular: Streamlit apila las columnas debajo de 640 px; se ordena el encabezado de cada mosaico */
@media (max-width: 640px) {
  [data-testid="stMainBlockContainer"] { padding: 3.25rem .75rem 2rem; }
  .ot-head { flex-direction: column; align-items: flex-start; gap: .5rem; }
  .ot-meta { text-align: left; white-space: normal; }
  .ot-h1 { font-size: 1.4rem; }
  .ot-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .5rem; }
  .ot-kpi .v { font-size: 1.5rem; }
  [class*="st-key-tile-"], [class*="st-key-filtros-"] { padding: .75rem .75rem .5rem !important; }
  /* encabezado del mosaico: titulo a la izquierda e icono de informacion a la derecha, sin apilarse */
  [class*="st-key-tile-"] [data-testid="stHorizontalBlock"]:has(.ot-tags) { flex-wrap: nowrap; align-items: flex-start; gap: .5rem; }
  [class*="st-key-tile-"] [data-testid="stHorizontalBlock"]:has(.ot-tags) > [data-testid="stColumn"]:nth-child(1) { flex: 1 1 0 !important; min-width: 0 !important; width: auto !important; }
  [class*="st-key-tile-"] [data-testid="stHorizontalBlock"]:has(.ot-tags) > [data-testid="stColumn"]:nth-child(2) { flex: 0 0 auto !important; min-width: 0 !important; width: auto !important; }
  /* en pantallas tactiles la barra de Plotly queda siempre visible y tapa la leyenda */
  .modebar-container { display: none; }
}
</style>
"""


def _clave(*partes: object) -> str:
    """Clave estable entre ejecuciones para contenedores con estilo propio."""
    return f"{crc32('|'.join(map(str, partes)).encode()):x}"


def estilo_global() -> None:
    st.html(_CSS)


def encabezado_pagina(seccion: str, titulo: str, descripcion: str | None = None, meta: str | None = None) -> None:
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
def mosaico(clave: str, titulo: str, subtitulo: str, tipo: str, ayuda: str, filtro: str | None = None,
            enlazada: bool = False, fuente: str | None = None):
    """Mosaico de una visualizacion: titulo, subtitulo con unidades y periodo, etiquetas (tipo de dato,
    pista de interaccion, filtro activo) en una sola linea, la nota metodologica detras del icono de
    informacion y, al pie, la fuente. Las graficas que filtran a otras (enlazada=True) llevan la pista
    'Clic para filtrar'."""
    with st.container(key=f"tile-{clave}"):
        izq, info = st.columns([0.94, 0.06], vertical_alignment="top", gap="small")
        chip = f'<span class="ot-chip">Filtro activo: {html.escape(filtro)}</span>' if filtro else ""
        clic = ('<span class="ot-tag ot-clic" title="Haga clic en la gráfica para filtrar; doble clic para limpiar">'
                'Clic para filtrar</span>') if enlazada else ""
        izq.html(f'<div class="ot-tt">{html.escape(titulo)}</div><div class="ot-ts">{subtitulo}</div>'
                 f'<div class="ot-tags">{_tag(tipo)}{clic}{chip}</div>')
        with info.popover("", icon=":material/info:", help="Nota metodológica"):
            st.markdown(ayuda)
        yield
        origen = fuente or "; ".join(FUENTES_MOSAICO.get(clave, []))
        if origen:
            st.html(f'<div class="ot-src"><b>Fuente:</b> {html.escape(origen)}. Elaboración propia.</div>')


def grafica(fig, key: str, enlazada: bool = False):
    """Muestra una figura con la barra de Plotly uniforme. Las enlazadas responden al clic en un punto
    o barra (on_select) y devuelven la seleccion."""
    extra = {"on_select": "rerun", "selection_mode": "points"} if enlazada else {}
    return st.plotly_chart(fig, key=key, width="stretch", config=CONFIG_PLOTLY, **extra)


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


def indicadores(items: list[dict], columnas: int | None = None) -> None:
    """Fila de indicadores en una cuadricula uniforme (columnas = len(items) por defecto; 2 en tableta y
    celular). Cada item: etiqueta, valor y, opcionalmente, delta (fraccion) con delta_texto, o contexto;
    y serie para la minigrafica."""
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
    st.html(f'<div class="ot-kpis" style="--n:{columnas or len(items)}">{"".join(celdas)}</div>')


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


def siguiente(pagina: str, titulo: str, puente: str, icono: str = ":material/arrow_forward:") -> None:
    """Cierre de un modulo: una frase que conecta con la pregunta del siguiente y el enlace a el.

    Si la pagina corre sola (pruebas de una pagina sin app.py) el enlace no existe y se muestra solo el texto."""
    with st.container(key=f"siguiente-{_clave(pagina)}"):
        st.html(f'<div class="ot-nl">Continúa en</div><div class="ot-sig">{puente}</div>')
        try:
            st.page_link(pagina, label=titulo, icon=icono)
        except st.errors.StreamlitAPIException:
            st.markdown(f"**{titulo}**")


def pie_institucional(fecha_corte: str, generado: str) -> None:
    """Pie de cada pagina: autoria, fuentes, fecha de corte, forma de citar y aviso de uso."""
    st.html(
        '<div class="ot-pie"><div><b>Observatorio de Inteligencia Turística del Lago de Atitlán.</b> Proyecto académico del '
        'Grupo 3, CC3084 Data Science, Universidad del Valle de Guatemala, con datos institucionales del INGUAT '
        'compartidos para uso docente. Las cifras no constituyen estadística oficial y no deben citarse fuera de '
        f'ese contexto.<br>Cita sugerida: Grupo 3 UVG (2026). <i>Observatorio de Inteligencia Turística del Lago de '
        f'Atitlán</i>. Datos con corte al {fecha_corte}.</div>'
        f'<div><b>Fecha de corte de los datos:</b> {fecha_corte}<br><b>Última actualización:</b> {generado}<br>'
        '<b>Contacto metodológico:</b> página Acerca del observatorio</div></div>'
    )


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
