"""Modulo 4 · Red territorial y caracterizacion de los 10 municipios (reto del grupo 3).

Cuadrante analitico volumen x estadia media x % extranjeros que clasifica a los pueblos en hubs
comerciales (puertas de entrada), larga estancia/retiro y visita corta; la clasificacion por regla se
contrasta con k-medias y se valida con la dinamica diaria (fin de semana y festividades) de cada pueblo.
Vista enlazada: un clic en un municipio del cuadrante abre su perfil y lo marca en la matriz.
"""

from __future__ import annotations

import streamlit as st

from src import indicadores as ind
from src import territorio as te
from src.datos import corto, origenes, tabla
from src.estilo import COLORES_CLASE, color, formato_numero
from src.graficas import (
    fig_cuadrante, fig_estacionalidad_clase, fig_huella_semanal, fig_matriz_perfiles, fig_mensual_origen,
    fig_mercados_clase, fig_patron_semanal, fig_top_paises,
)
from src.normalizar import MUNICIPIOS
from src.ui import aviso_sinteticos, barra_filtros, encabezado_pagina, indicadores, mosaico

m = tabla("mensual")
d = tabla("diaria")


@st.cache_data(show_spinner=False)
def _perfil(m, d):
    return te.clasificar(te.perfil_completo(m, d))


perfil = _perfil(m, d)

encabezado_pagina(
    "Módulo 4 · Reto del destino",
    "Red territorial de los 10 municipios",
    "¿Qué papel juega cada pueblo del lago? Se distinguen las puertas de entrada (mucho volumen), los destinos de "
    "larga estancia (pocos visitantes, mayoría extranjera, muchas noches) y los de visita corta (excursiones, sobre "
    "todo de nacionales y en fin de semana).",
    "Telefonía mensual y diaria<br><b>10 municipios</b>",
    tema="m4_municipios",
)
aviso_sinteticos(origenes())

with barra_filtros("m4"):
    metodo = st.segmented_control(
        "Clasificación", ["Regla del cuadrante", "k-medias"], default="Regla del cuadrante", key="m4_metodo",
        help="Regla: cortes interpretables sobre volumen, estadía y % extranjeros. k-medias: agrupa a los pueblos "
        "por parecido en 4 variables estandarizadas, sin reglas fijas; sirve de contraste.",
    ) or "Regla del cuadrante"
col_clase = "clase_regla" if metodo == "Regla del cuadrante" else "clase_kmedias"
perfil["clase"] = perfil[col_clase]
clases = perfil["clase"]
por_clase = te.perfil_por_clase(perfil, "clase")

n_clase = clases.value_counts()
indicadores([
    {"etiqueta": "Hubs comerciales", "valor": str(n_clase.get("Hub comercial", 0)),
     "contexto": ", ".join(corto(x) for x in perfil.index[clases == "Hub comercial"])},
    {"etiqueta": "Larga estancia", "valor": str(n_clase.get("Larga estancia", 0)),
     "contexto": ", ".join(corto(x) for x in perfil.index[clases == "Larga estancia"])},
    {"etiqueta": "Visita corta", "valor": str(n_clase.get("Visita corta", 0)), "contexto": "excursiones de un día"},
    {"etiqueta": "Coincidencia regla / k-medias", "valor": f"{perfil['coinciden'].sum()} de {len(perfil)}",
     "contexto": "municipios con la misma clase en ambos métodos"},
])

# --- Cuadrante (origen del enlace) -------------------------------------------------------------------
estado = st.session_state.get("m4_cuadrante")
puntos = estado.selection.points if estado and estado.selection else []
sel = next((p["customdata"][0] for p in puntos if p.get("customdata") and p["customdata"][0] in MUNICIPIOS), None)

c1, c2 = st.columns([1.5, 1], gap="small")
with c1, mosaico(
    "m4-cuadrante", "Cuadrante analítico de los municipios",
    f"Volumen × estadía media · tamaño: % de extranjeros · color: clase ({metodo.lower()}) · clic para ver el perfil",
    "interpretacion",
    "**¿Qué tipo de destino es cada pueblo?**\n\n- Eje X: visitantes promedio por mes (escala logarítmica).\n"
    "- Eje Y: estadía media ponderada de los turistas con pernocta.\n- Tamaño: % de visitantes extranjeros.\n\n"
    "Las líneas punteadas son las medianas del lago. **Regla:** hub comercial = volumen ≥ 60 % del mayor; larga "
    "estancia = estadía sobre la mediana y mayoría extranjera; visita corta = el resto. **k-medias** agrupa por "
    "parecido en volumen, estadía, % extranjeros y presión de fin de semana.",
    filtro=corto(sel) if sel else None,
):
    st.plotly_chart(fig_cuadrante(perfil, sel), key="m4_cuadrante", on_select="rerun", selection_mode="points", width="stretch")

with c2, st.container(key="tile-m4-clases"):
    st.html('<div class="ot-tt">Cómo es cada clase</div><div class="ot-ts">Promedio simple de sus municipios</div>')
    for clase, fila in por_clase.iterrows():
        miembros = ", ".join(corto(x) for x in perfil.index[clases == clase])
        st.html(
            f'<div style="margin:.45rem 0 .1rem"><span class="ot-tag" style="background:{color(COLORES_CLASE[clase])};color:#fff">'
            f'{clase}</span> <span style="font-size:.8rem;color:#525252">{miembros}</span></div>'
            f'<div style="font-size:.8rem;color:#393939;line-height:1.5">{formato_numero(fila["visitantes_mes"])} visitantes/mes · '
            f'{fila["estadia_media"]:.1f} días · {fila["pct_extranjeros"]:.0%} extranjeros · '
            f'{fila["pct_excursionistas"]:.0%} excursionistas · finde ×{fila["presion_finde"]:.2f}</div>'
        )

# --- Matriz de perfiles y huella semanal -----------------------------------------------------------
c3, c4 = st.columns([1.25, 1], gap="small")
with c3, mosaico(
    "m4-matriz", "Matriz de perfiles", "Municipios por volumen · color: posición relativa en cada indicador", "observado",
    "**¿En qué se diferencia cada pueblo?**\n\nCada columna es un indicador con su valor real escrito; el color indica "
    "si el municipio está entre los menores (claro) o los mayores (oscuro) del lago **en esa columna**. Así se comparan "
    "variables de unidades distintas sin mezclarlas. La presión de fin de semana y el Lift vienen de la base diaria.",
    filtro=corto(sel) if sel else None,
):
    st.plotly_chart(fig_matriz_perfiles(perfil, sel), key="m4_matriz", width="stretch")
with c4, mosaico(
    "m4-huella", "Huella semanal de cada pueblo", "Índice por día (días regulares, promedio semanal = 100) · líneas: separación entre clases",
    "observado",
    "**¿Quién se llena el fin de semana?**\n\nBase diaria: rojo = por debajo del promedio de la semana, azul = por "
    "encima. Los pueblos de visita corta dependen más del sábado y domingo (excursiones de nacionales); los de larga "
    "estancia tienen una semana más pareja.",
):
    st.plotly_chart(fig_huella_semanal(te.huella_semanal(d), clases), key="m4_huella", width="stretch")

# --- Comparacion entre clases ------------------------------------------------------------------------
c5, c6 = st.columns(2, gap="small")
with c5, mosaico(
    "m4-mercados", "Mercados emisores por clase", "Composición de los visitantes extranjeros de cada clase", "observado",
    "**¿Atraen las clases a mercados distintos?**\n\nPorcentaje de los extranjeros de cada clase que viene de cada uno "
    "de los 8 principales países del lago. Diferencias aquí orientan la promoción por mercado de cada tipo de pueblo.",
):
    st.plotly_chart(fig_mercados_clase(te.mercados_por_clase(m, clases)), key="m4_mercados", width="stretch")
with c6, mosaico(
    "m4-estac", "Estacionalidad por clase", "Índice mensual de visitantes (promedio de los meses observados = 100)", "observado",
    "**¿Tienen la misma temporada?**\n\nEs un índice de forma: aunque sumar municipios de una clase duplique visitantes, "
    "el patrón entre meses se conserva. Los meses sin cobertura de telefonía aparecen vacíos.",
):
    st.plotly_chart(fig_estacionalidad_clase(te.estacionalidad_por_clase(m, clases)), key="m4_estac", width="stretch")

# --- Perfil del municipio elegido -------------------------------------------------------------------
mun = sel or perfil["visitantes_mes"].idxmax()
g = m[m["municipio"] == mun]
gd = d[d["municipio"] == mun]
k = ind.kpis_demanda(g)
fila = perfil.loc[mun]
st.html(f'<div class="ot-tt" style="margin-top:.5rem">Perfil de {mun}'
        + ("" if sel else " <span class='ot-ts'>(el de mayor volumen; elija otro en el cuadrante)</span>") + "</div>")
indicadores([
    {"etiqueta": "Clase", "valor": fila["clase"],
     "contexto": "ambos métodos coinciden" if fila["coinciden"] else f"k-medias: {fila['clase_kmedias']}" if col_clase == "clase_regla" else f"regla: {fila['clase_regla']}"},
    {"etiqueta": "Visitantes promedio por mes", "valor": formato_numero(k["visitantes_mes"]), "serie": k["serie_visitantes"]},
    {"etiqueta": "Estadía media ponderada", "valor": f"{k['estadia_media']:.2f} días", "serie": k["serie_estadia"]},
    {"etiqueta": "Presión de fin de semana", "valor": f"{fila['presion_finde']:.2f}×",
     "contexto": f"{k['pct_extranjeros']:.0%} extranjeros"},
])
c7, c8, c9 = st.columns(3, gap="small")
with c7, mosaico("m4-serie", "Visitantes por mes y origen", "Meses sin dato vacíos", "observado",
                 "Serie mensual del municipio, separando nacionales (con factor de expansión) y extranjeros.", filtro=corto(mun)):
    st.plotly_chart(fig_mensual_origen(g), key="m4_serie", width="stretch")
with c8, mosaico("m4-semana", "Patrón semanal", "Días regulares · promedio = 100", "observado",
                 "Índice de visitantes por día de la semana del municipio elegido (base diaria).", filtro=corto(mun)):
    st.plotly_chart(fig_patron_semanal(ind.patron_semanal(ind.serie_diaria(gd))), key="m4_semana", width="stretch")
with c9, mosaico("m4-paises", "Principales mercados extranjeros", "Top 8 del municipio", "observado",
                 "Mercados emisores extranjeros del municipio elegido.", filtro=corto(mun)):
    top = ind.top_paises(g, 8)
    if not top.empty:
        st.plotly_chart(fig_top_paises(top), key="m4_paises", width="stretch")
