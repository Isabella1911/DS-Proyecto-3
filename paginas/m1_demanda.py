"""Modulo 1 · Monitor de demanda y mercados emisores (diagnostico macro).

Vista enlazada: un clic en la grafica de municipios filtra los indicadores, la segmentacion
turista/excursionista, el top 10 de nacionalidades y la estadia por nacionalidad.
"""

from __future__ import annotations

import streamlit as st

from src import indicadores as ind
from src.datos import corto, origenes, tabla
from src.estilo import formato_numero
from src.graficas import MES_ES, fig_estadia_paises, fig_municipios, fig_segmentacion, fig_top_paises
from src.normalizar import MUNICIPIOS
from src.ui import aviso_sinteticos, barra_filtros, encabezado_pagina, indicadores, mosaico, nota, sin_datos

m_todo = tabla("mensual")
periodos = sorted(m_todo["periodo"].unique())
etiq = {p: f"{MES_ES[p.month - 1]} {p.year}" for p in periodos}

encabezado_pagina(
    "Módulo 1 · Diagnóstico macro",
    "Demanda y mercados emisores",
    "¿Cuántos visitantes recibe el lago, cuánto se quedan y de dónde vienen? Haga clic en uno o varios municipios "
    "para que todo el módulo se recalcule para esa selección.",
    f"Telefonía mensual<br><b>{len(periodos)} meses</b> con dato",
)
aviso_sinteticos(origenes())

with barra_filtros("m1"):
    c1, c2 = st.columns([2, 1], gap="medium")
    rango = c1.select_slider("Periodo", options=periodos, value=(periodos[0], periodos[-1]), format_func=etiq.get, key="m1_periodo")
    origen = c2.segmented_control("Origen", ["Todos", "Nacional", "Extranjero"], default="Todos", key="m1_origen") or "Todos"

m = m_todo[m_todo["periodo"].between(*rango)]
m = ind.filtrar(m, origen=origen)
if m.empty:
    sin_datos("No hay visitantes para este periodo y origen.")
    st.stop()

# --- Grafica de origen del filtro: municipios ---------------------------------------------------
promedio = (
    m.groupby(["municipio", "origen", "periodo"])["visitantes"].sum()
    .groupby(["municipio", "origen"]).mean().unstack(fill_value=0)
    .reindex(columns=["Nacional", "Extranjero"], fill_value=0)
)


def _seleccion(estado) -> list[str]:
    puntos = estado.selection.points if estado and estado.selection else []
    return sorted({p["customdata"] for p in puntos if p.get("customdata") in MUNICIPIOS})


sel_previa = _seleccion(st.session_state.get("m1_mun_chart"))

col_a, col_b = st.columns([1, 1.25], gap="small")
with col_a, mosaico(
    "m1-mun", "Visitantes por municipio", "Promedio mensual, nacionales y extranjeros · clic para filtrar el módulo",
    "observado",
    "**¿Qué municipios concentran la demanda?**\n\nCada barra es el promedio de visitantes únicos por mes del municipio. "
    "Haga clic en una barra (Shift + clic para varias) y los indicadores y gráficas de la derecha y de abajo se "
    "recalculan para esa selección. Doble clic limpia la selección.\n\n"
    "Los municipios **no se suman** para obtener un total del lago: quien visita Panajachel y San Juan el mismo mes "
    "aparece en ambos.",
    filtro=", ".join(corto(x) for x in sel_previa) if sel_previa else None,
):
    evento = st.plotly_chart(fig_municipios(promedio), key="m1_mun_chart", on_select="rerun",
                             selection_mode="points", width="stretch")

seleccion = _seleccion(evento)

ambito = seleccion or MUNICIPIOS
ms = ind.filtrar(m, municipios=ambito)
es_suma = len(ambito) > 1
nombre_ambito = ", ".join(corto(x) for x in ambito) if seleccion else "Los 10 municipios"
k = ind.kpis_demanda(ms)

with col_b:
    st.html(f'<div class="ot-ts" style="margin:.2rem 0 .4rem">Indicadores de: <b>{nombre_ambito}</b>'
            + (" · <i>suma de municipios (puede duplicar visitantes)</i>" if es_suma else "") + "</div>")
    indicadores([
        {"etiqueta": "Visitantes promedio por mes", "valor": formato_numero(k["visitantes_mes"]),
         "contexto": f"{k['meses']} meses con dato", "serie": k["serie_visitantes"]},
        {"etiqueta": "Días-persona promedio por mes", "valor": formato_numero(k["dias_persona_mes"]),
         "contexto": "todos los segmentos"},
        {"etiqueta": "Estadía media ponderada", "valor": f"{k['estadia_media']:.2f} días",
         "contexto": "Σ días-persona / Σ visitantes, solo > 1 día", "serie": k["serie_estadia"]},
        {"etiqueta": "Turistas con pernocta", "valor": f"{k['pct_turistas']:.0%}",
         "contexto": f"excursionistas: {1 - k['pct_turistas']:.0%}"},
    ])
    nota("observado",
         f"{nombre_ambito}: {formato_numero(k['visitantes_mes'])} visitantes por mes en promedio; "
         f"el {k['pct_extranjeros']:.0%} son extranjeros. Los turistas que pernoctan se quedan "
         f"{k['estadia_media']:.1f} días en promedio.")
    if es_suma:
        nota("interpretacion", "Con varios municipios, los volúmenes son la **suma de municipios**: una cota superior "
             "del total del lago. La estadía media y los porcentajes sí son comparables porque son cocientes.")

# --- Segmentacion y mercados ---------------------------------------------------------------------
c1, c2 = st.columns(2, gap="small")
with c1, mosaico(
    "m1-seg", "Turistas vs. excursionistas", "Visitantes por mes y segmento · línea: % con pernocta", "observado",
    "**¿Qué parte de los visitantes pasa la noche?**\n\nTurista: más de un día en el destino (segmento 'mayor a 1'). "
    "Excursionista: menos de 24 horas ('menor a 1'); por definición su permanencia es 1 y no entra en la estadía media. "
    "Los meses sin cobertura aparecen vacíos y rotulados 'Sin dato', nunca como cero.",
    filtro=nombre_ambito if seleccion else None,
):
    st.plotly_chart(fig_segmentacion(ind.segmentacion(ms)), key="m1_seg", width="stretch")

top = ind.top_paises(ms, 10)
with c2, mosaico(
    "m1-top", "Top 10 mercados emisores extranjeros", "Visitantes en el periodo · % sobre el total de extranjeros",
    "observado",
    "**¿De qué países vienen los extranjeros?**\n\nSolo visitantes extranjeros. Los nacionales se reportan aparte "
    "porque su conteo incorpora un **factor de expansión** y no es comparable directamente con el de los extranjeros.",
    filtro=nombre_ambito if seleccion else None,
):
    if top.empty:
        sin_datos("La selección no tiene visitantes extranjeros.")
    else:
        st.plotly_chart(fig_top_paises(top), key="m1_top", width="stretch")
    nac = ms[ms["origen"] == "Nacional"]
    if not nac.empty:
        st.caption(f"**Nacionales (Guatemala):** {formato_numero(nac.groupby('periodo')['visitantes'].sum().mean())} "
                   f"visitantes por mes en promedio · estadía media {ind.estadia_media(nac):.2f} días. "
                   "Cifra con factor de expansión: no se compara en la misma escala que el ranking.")

# --- Visualizacion adicional: estadia por nacionalidad ------------------------------------------
c3, c4 = st.columns([1.25, 1], gap="small")
with c3, mosaico(
    "m1-estadia", "¿Quién se queda más tiempo?", "Estadía media ponderada por nacionalidad (top 10 por volumen)",
    "observado",
    "**Visualización adicional del grupo.** Compara la estadía media de cada mercado con la de los nacionales y con "
    "el promedio ponderado. Un mercado con pocas llegadas pero estadía larga puede generar tantas noches como uno "
    "masivo de visita corta, algo clave para la promoción del INGUAT.",
    filtro=nombre_ambito if seleccion else None,
):
    if not top.empty:
        st.plotly_chart(fig_estadia_paises(top, ind.estadia_media(ms[ms["origen"] == "Nacional"]), k["estadia_media"]),
                        key="m1_estadia", width="stretch")

with c4, st.container(key="tile-m1-lectura"):
    st.html('<div class="ot-tt">Lectura del módulo</div><div class="ot-ts">Qué muestran los datos de la selección</div>')
    if not top.empty:
        lider = top.index[0]
        larga = top["estadia_media"].idxmax()
        nota("observado", f"**{lider}** es el primer mercado extranjero ({top['pct'].iloc[0]:.0%} de los extranjeros). "
             f"**{larga}** es el de estadía más larga ({top['estadia_media'].max():.1f} días).")
    perfil = ind.por_municipio(m)
    if not perfil.empty:
        mas_largo = perfil["estadia_media"].idxmax()
        nota("interpretacion", f"**{corto(mas_largo)}** tiene la estadía más larga del lago "
             f"({perfil.loc[mas_largo, 'estadia_media']:.1f} días) y **{corto(perfil['visitantes_mes'].idxmax())}** el mayor "
             "volumen: el lago combina puertas de entrada con destinos de larga estancia (se desarrolla en el módulo 4).")
    with st.expander("Tabla por municipio", icon=":material/table:"):
        st.dataframe(
            perfil.rename(index=corto).rename(columns={
                "visitantes_mes": "Visitantes/mes", "dias_persona_mes": "Días-persona/mes", "estadia_media": "Estadía media",
                "pct_extranjeros": "% extranjeros", "pct_turistas": "% turistas"}),
            column_config={"% extranjeros": st.column_config.NumberColumn(format="percent"),
                           "% turistas": st.column_config.NumberColumn(format="percent"),
                           "Estadía media": st.column_config.NumberColumn(format="%.2f"),
                           "Visitantes/mes": st.column_config.NumberColumn(format="localized"),
                           "Días-persona/mes": st.column_config.NumberColumn(format="localized")},
            width="stretch",
        )
