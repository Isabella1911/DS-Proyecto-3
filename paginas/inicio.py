"""Inicio: el lago como protagonista.

Estructura "mapa protagonista" (como los observatorios de Colorado o Canarias): los 10 municipios sobre el
mapa del lago y, a la derecha, un panel que muestra la vista del lago o el pueblo en el que se hace clic.
Debajo, la lectura rapida (a los modulos se entra desde la barra lateral).

La portada usa la identidad institucional azul (src/estilo.py, AZULES). Todo su CSS se limita a
`stMain:has(.ot-hero)`, asi que no afecta el diseno de los modulos.
"""

import html
from urllib.parse import quote

import streamlit as st

from src import indicadores as ind
from src import territorio as te
from src.datos import origenes, tabla
from src.estilo import AZULES as A
from src.estilo import COLORES_CLASE, formato_numero
from src.graficas import fig_mapa_lago
from src.ui import aviso_sinteticos

m = tabla("mensual")
d = tabla("diaria")


@st.cache_data(show_spinner=False)
def _perfil(m, d):
    p = te.clasificar(te.perfil_completo(m, d))
    return p.assign(clase=p["clase_regla"])


k = ind.kpis_demanda(m)
perfil = _perfil(m, d)
lift = ind.lift_eventos(ind.serie_diaria(d))

DESCRIPCION_CLASE = {
    "Hub comercial": "Puerta de entrada del lago: concentra el volumen, los servicios y el transporte.",
    "Larga estancia": "Estadías largas y peso alto de extranjeros: turismo de retiro y aprendizaje.",
    "Visita corta": "Visitas de paso, más dependientes del fin de semana y de las festividades.",
}

# Silueta de los tres volcanes del lago (San Pedro, Toliman y Atitlan) sobre el agua. Va como imagen de
# fondo: st.html elimina los <svg> sueltos de este tamano.
_SVG_VOLCANES = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 220">
<path d="M120 220 L250 92 Q262 80 274 92 L410 220 Z" fill="#ffffff" fill-opacity=".08"/>
<path d="M300 220 L420 70 Q432 56 446 70 L600 200 L600 220 Z" fill="#ffffff" fill-opacity=".12"/>
<path d="M215 220 L330 118 Q340 109 350 118 L470 220 Z" fill="#ffffff" fill-opacity=".10"/>
<path d="M0 176 Q75 166 150 176 T300 176 T450 176 T600 176 L600 220 L0 220 Z" fill="{A['profundo']}" fill-opacity=".35"/>
<path d="M60 190 Q105 183 150 190 T240 190" fill="none" stroke="#ffffff" stroke-opacity=".35" stroke-width="1.5"/>
<path d="M300 200 Q350 193 400 200 T500 200 T600 200" fill="none" stroke="#ffffff" stroke-opacity=".28" stroke-width="1.5"/>
</svg>"""
VOLCANES = "data:image/svg+xml," + quote(_SVG_VOLCANES)

P = '[data-testid="stMain"]:has(.ot-hero)'
st.html(f"""
<style>
{P} {{ background: linear-gradient(180deg, {A['bruma']} 0%, #f5fafd 420px, #ffffff 100%); }}

/* banda principal (compacta: el protagonista es el mapa) */
.ot-hero {{ position: relative; overflow: hidden; border-radius: 14px; padding: 1.4rem 2rem 1.5rem; color: #fff;
  background: linear-gradient(118deg, {A['profundo']} 0%, {A['oscuro']} 30%, {A['medio']} 58%, {A['guate']} 82%, {A['claro']} 100%);
  box-shadow: 0 10px 30px rgba(0, 49, 77, .22); }}
.ot-hero-txt {{ position: relative; z-index: 1; max-width: 44rem; }}
.ot-hero-crumb {{ font-size: .72rem; letter-spacing: .1em; text-transform: uppercase; color: {A['cielo']}; font-weight: 600; }}
.ot-hero h1 {{ font-size: 2.2rem; font-weight: 300; line-height: 1.1; margin: .35rem 0 .5rem; color: #fff; padding: 0; }}
.ot-hero p {{ font-size: .9rem; line-height: 1.55; color: rgba(255, 255, 255, .9); margin: 0; }}
.ot-hero-chips {{ display: flex; flex-wrap: wrap; gap: .5rem; margin-top: .9rem; }}
.ot-hero-chips span {{ font-size: .72rem; padding: .25rem .7rem; border-radius: 999px; color: #fff;
  background: rgba(255, 255, 255, .14); border: 1px solid rgba(255, 255, 255, .28); }}
.ot-hero-art {{ position: absolute; right: 0; bottom: 0; width: 46%; max-width: 620px; aspect-ratio: 600 / 220;
  background: url("{VOLCANES}") right bottom / contain no-repeat; pointer-events: none; }}

/* titulos de seccion */
.ot-sec {{ display: flex; align-items: center; gap: .6rem; margin: .9rem 0 .1rem; }}
.ot-sec span {{ font-size: .75rem; letter-spacing: .1em; text-transform: uppercase; font-weight: 600; color: {A['medio']}; white-space: nowrap; }}
.ot-sec::after {{ content: ""; flex: 1; height: 1px; background: linear-gradient(90deg, {A['cielo']}, transparent); }}

/* mosaicos de la portada */
{P} [class*="st-key-tile-inicio-"] {{ border: 1px solid #d3e9f4; border-radius: 12px; background: #fff;
  box-shadow: 0 2px 10px rgba(0, 74, 115, .07); padding: 1.1rem 1.25rem .9rem !important; }}
{P} [class*="st-key-tile-inicio-"] .ot-tt {{ color: {A['oscuro']}; }}
{P} [class*="st-key-tile-inicio-mapa"] {{ padding: .9rem .9rem .6rem !important; }}
{P} [class*="st-key-tile-inicio-mapa"] [data-testid="stPlotlyChart"] {{ border-radius: 8px; overflow: hidden; }}
.ot-pista {{ font-size: .75rem; color: #4b6475; }}
.ot-pista b {{ color: {A['medio']}; font-weight: 600; }}
{P} [class*="st-key-nota-"] {{ border-left-color: {A['claro']}; }}
{P} [class*="st-key-nota-observado"] {{ border-left-color: {A['guate']}; }}
{P} [class*="st-key-tile-inicio-reglas"] li::marker {{ color: {A['guate']}; }}

/* panel lateral: vista del lago o del pueblo seleccionado */
{P} [class*="st-key-tile-inicio-panel"] {{ padding: 0 !important; overflow: hidden; gap: 0; }}
.ot-pn-h {{ padding: 1.1rem 1.25rem 1rem; color: #fff;
  background: linear-gradient(135deg, {A['profundo']} 0%, {A['medio']} 70%, {A['guate']} 100%); }}
.ot-pn-k {{ font-size: .7rem; letter-spacing: .1em; text-transform: uppercase; color: {A['cielo']}; font-weight: 600; }}
.ot-pn-n {{ font-size: 1.6rem; font-weight: 300; line-height: 1.15; margin: .2rem 0 .35rem; }}
.ot-pn-s {{ font-size: .78rem; color: rgba(255, 255, 255, .85); line-height: 1.45; }}
.ot-pn-badge {{ display: inline-flex; align-items: center; gap: .4rem; font-size: .72rem; font-weight: 600; padding: .2rem .6rem;
  border-radius: 999px; background: #fff; color: {A['profundo']}; margin-bottom: .45rem; }}
.ot-pn-badge i {{ width: .6rem; height: .6rem; border-radius: 50%; display: inline-block; }}
.ot-pn-b {{ padding: .35rem 1.25rem .4rem; }}
.ot-pn-r {{ display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; padding: .62rem 0;
  border-bottom: 1px solid #e3f0f7; }}
.ot-pn-r:last-child {{ border-bottom: none; }}
.ot-pn-l {{ font-size: .78rem; color: #4b6475; }}
.ot-pn-l small {{ display: block; font-size: .7rem; color: #7b93a3; margin-top: .1rem; }}
.ot-pn-v {{ font-size: 1.25rem; font-weight: 400; color: {A['profundo']}; white-space: nowrap; font-variant-numeric: tabular-nums; }}
.ot-pn-clases {{ display: flex; flex-wrap: wrap; gap: .4rem; }}
.ot-pn-clases span {{ display: inline-flex; align-items: center; gap: .35rem; font-size: .72rem; color: {A['profundo']};
  background: {A['bruma']}; border-radius: 999px; padding: .15rem .55rem; }}
.ot-pn-clases i {{ width: .55rem; height: .55rem; border-radius: 50%; display: inline-block; }}
.ot-pn-merc {{ font-size: .8rem; color: {A['profundo']}; text-align: right; line-height: 1.5; }}
{P} [class*="st-key-tile-inicio-panel"] [data-testid="stPageLink"] {{ padding: 0 1.25rem 1rem; }}

/* boton del panel lateral (enlace al modulo 4) */
{P} [data-testid="stPageLink"] a {{ background: {A['guate']}; border-radius: 6px; padding: .35rem .9rem;
  width: fit-content; transition: background .15s; }}
{P} [data-testid="stPageLink"] a:hover {{ background: {A['oscuro']}; }}
{P} [data-testid="stPageLink"] a * {{ color: #fff !important; }}

@media (max-width: 640px) {{
  .ot-hero {{ padding: 1.25rem 1.1rem 4.5rem; margin-top: 1.75rem; }}
  .ot-hero h1 {{ font-size: 1.8rem; }}
  .ot-hero-art {{ width: 100%; }}
}}
</style>
""")

st.html(f"""
<div class="ot-hero">
  <div class="ot-hero-txt">
    <div class="ot-hero-crumb">Observatorio de Inteligencia Turística · Grupo 3</div>
    <h1>Lago de Atitlán, Sololá</h1>
    <p>Demanda, oferta y presión sobre el territorio de los 10 municipios ribereños, para que el INGUAT y los
    gestores locales decidan con evidencia.</p>
    <div class="ot-hero-chips">
      <span>Mapa interactivo del lago</span>
      <span>10 municipios ribereños</span>
      <span>4 módulos de análisis</span>
    </div>
  </div>
  <div class="ot-hero-art"></div>
</div>
""")
aviso_sinteticos(origenes())


def seccion(texto: str) -> None:
    st.html(f'<div class="ot-sec"><span>{texto}</span></div>')


def fila(etiqueta: str, valor: str, detalle: str = "") -> str:
    det = f"<small>{html.escape(detalle)}</small>" if detalle else ""
    return f'<div class="ot-pn-r"><div class="ot-pn-l">{html.escape(etiqueta)}{det}</div><div class="ot-pn-v">{valor}</div></div>'


def punto(clase: str) -> str:
    return f'<i style="background:{COLORES_CLASE.get(clase, "#898781")}"></i>'


# Seleccion del mapa (se lee antes de dibujar para resaltar el pueblo elegido)
estado = st.session_state.get("inicio_mapa")
puntos = estado.selection.points if estado and estado.selection else []
sel = puntos[0]["customdata"][0] if puntos and puntos[0].get("customdata") else None
sel = sel if sel in perfil.index else None

seccion("El lago y sus 10 municipios")
c_mapa, c_panel = st.columns([0.66, 0.34], gap="small")

with c_mapa, st.container(key="tile-inicio-mapa"):
    st.plotly_chart(fig_mapa_lago(perfil, te.COORDENADAS, te.CONTORNO_LAGO, te.VOLCANES, sel), key="inicio_mapa", on_select="rerun",
                    selection_mode="points", width="stretch", config={"displayModeBar": False, "scrollZoom": False, "doubleClick": "reset"})
    st.html('<div class="ot-pista"><b>Haz clic en un pueblo</b> para ver su perfil · tamaño = visitantes por mes · '
            'doble clic en el mapa para volver al lago · contorno esquemático</div>')

with c_panel, st.container(key="tile-inicio-panel"):
    if sel is None:
        conteo = perfil["clase"].value_counts()
        clases = "".join(f"<span>{punto(c)}{c}: {conteo.get(c, 0)}</span>" for c in te.CLASES)
        st.html(
            '<div class="ot-pn-h"><div class="ot-pn-k">Vista del lago</div><div class="ot-pn-n">10 municipios</div>'
            '<div class="ot-pn-s">Cifras de la suma de municipios: un visitante puede contar en varios pueblos.</div></div>'
            '<div class="ot-pn-b">'
            + fila("Visitantes por mes", formato_numero(k["visitantes_mes"]), "suma de municipios (cota superior)")
            + fila("Estadía media ponderada", f"{k['estadia_media']:.2f} días", "turistas con pernocta")
            + fila("Visitantes extranjeros", f"{k['pct_extranjeros']:.0%}", "del total de visitantes")
            + fila("Festividad de mayor impacto", html.escape(str(lift["lift"].idxmax())),
                   f"Lift {lift['lift'].max():+.0%} frente a un día regular")
            + f'<div class="ot-pn-r"><div class="ot-pn-clases">{clases}</div></div></div>'
        )
        st.page_link("paginas/m4_municipios.py", label="Ver la red de municipios", icon=":material/hub:")
    else:
        r = perfil.loc[sel]
        rango = int(perfil["visitantes_mes"].rank(ascending=False)[sel])
        med_est = perfil["estadia_media"].median()
        top = ind.top_paises(ind.filtrar(m, [sel]), 3)
        mercados = "<br>".join(f"{html.escape(str(p))} · {v:.0%}" for p, v in top["pct"].items()) or "Sin dato"
        evento = r.get("evento_max")
        st.html(
            f'<div class="ot-pn-h"><div class="ot-pn-k">Municipio</div><div class="ot-pn-n">{html.escape(sel)}</div>'
            f'<div class="ot-pn-badge">{punto(r["clase"])}{r["clase"]}</div>'
            f'<div class="ot-pn-s">{DESCRIPCION_CLASE.get(r["clase"], "")}</div></div>'
            '<div class="ot-pn-b">'
            + fila("Visitantes por mes", formato_numero(r["visitantes_mes"]), f"{rango}.º de {len(perfil)} en volumen")
            + fila("Estadía media ponderada", f"{r['estadia_media']:.2f} días",
                   f"mediana del lago: {med_est:.2f} días")
            + fila("Visitantes extranjeros", f"{r['pct_extranjeros']:.0%}", f"lago: {k['pct_extranjeros']:.0%}")
            + fila("Presión de fin de semana", f"{r['presion_finde']:.2f}×", "sáb-dom frente a lun-vie")
            + (fila("Festividad de mayor impacto", html.escape(str(evento)), f"Lift {r['lift_max']:+.0%}")
               if isinstance(evento, str) else "")
            + f'<div class="ot-pn-r"><div class="ot-pn-l">Principales mercados extranjeros</div>'
              f'<div class="ot-pn-merc">{mercados}</div></div></div>'
        )
        st.page_link("paginas/m4_municipios.py", label="Ver el perfil completo", icon=":material/hub:")

seccion("Cómo leer el tablero")
with st.container(key="tile-inicio-reglas"):
    st.html('<div class="ot-tt">Reglas que respeta el tablero</div><div class="ot-ts">Según la guía metodológica</div>')
    st.markdown(
        "- Un mes sin dato es **'Sin dato'**, nunca cero.\n"
        "- La estadía media **se pondera** (Σ días-persona / Σ visitantes); nunca se promedia la permanencia.\n"
        "- La base diaria **no se suma** para obtener el mes.\n"
        "- Los municipios **no se suman** como total del lago sin advertirlo.\n"
        "- Personas y porcentajes nunca comparten eje."
    )
