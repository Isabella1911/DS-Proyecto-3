"""Modulo 3 · Oferta hotelera y desagregacion territorial.

Vista enlazada: un clic en un anio de la capacidad instalada enfoca la serie de ocupacion en ese anio.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src import indicadores as ind
from src import oferta as of
from src.datos import CONFIG, corto, origenes, tabla
from src.estilo import formato_numero
from src.graficas import (
    MES_ES, fig_afluencia_relativa, fig_capacidad, fig_capacidad_anual, fig_cruce_ventana, fig_heatmap_ocupacion,
    fig_ocupacion,
)
from src.normalizar import departamento
from src.ui import aviso_sinteticos, barra_filtros, encabezado_pagina, grafica, indicadores, mosaico, nota, sin_datos

DEPTO = departamento(CONFIG["destino"]["departamento"])
oferta = tabla("oferta")
ocup = tabla("ocupacion")
m = tabla("mensual")

encabezado_pagina(
    "Módulo 3 · Oferta",
    "Oferta hotelera y desagregación territorial",
    f"¿Alcanza la capacidad de alojamiento de {DEPTO} para la demanda del lago? Capacidad instalada, ocupación "
    "mensual y su cruce con la afluencia en la única ventana en que ambas series coinciden.",
    f"Oferta 2022–2026 · Ocupación 2023–2025<br>Departamento: <b>{DEPTO}</b>",
)
aviso_sinteticos(origenes())

cap = of.capacidad(oferta, DEPTO)
anual = of.capacidad_anual(cap)
o_dep = ocup[ocup["departamento"] == DEPTO].set_index("periodo")["ocupacion"]
if anual.empty or o_dep.empty:
    sin_datos(f"Faltan la oferta o la ocupación de {DEPTO}.")
    st.stop()

with barra_filtros("m3"):
    medida = st.segmented_control("Medida de capacidad", of.MEDIDAS, default="plazas_cama",
                                  format_func=lambda x: x.replace("_", " ").capitalize(), key="m3_medida") or "plazas_cama"

# --- Indicadores ---------------------------------------------------------------------------------
a0, a1 = anual.index.min(), anual.index.max()
ult_anio_ocup = o_dep.index.year.max()
ocup_anio = o_dep[o_dep.index.year == ult_anio_ocup]
v0, v1 = (pd.Timestamp(p + "-01") for p in CONFIG["ventana_coincidente"])
cruce = of.cruce_ventana(m, anual, o_dep, (v0, v1))
indicadores([
    {"etiqueta": f"Plazas cama {a1}", "valor": formato_numero(anual.loc[a1, "plazas_cama"]),
     "delta": anual.loc[a1, "plazas_cama"] / anual.loc[a0, "plazas_cama"] - 1, "delta_texto": f"frente a {a0}",
     "serie": anual["plazas_cama"].tolist()},
    {"etiqueta": f"Establecimientos {a1}", "valor": formato_numero(anual.loc[a1, "establecimientos"]),
     "contexto": f"{anual.loc[a1, 'habitaciones'] / anual.loc[a1, 'establecimientos']:.1f} habitaciones por establecimiento",
     "serie": anual["establecimientos"].tolist()},
    {"etiqueta": f"Ocupación promedio {ult_anio_ocup}", "valor": f"{ocup_anio.mean():.0%}",
     "contexto": f"pico: {MES_ES[ocup_anio.idxmax().month - 1]} ({ocup_anio.max():.0%})", "serie": o_dep.tolist()},
    {"etiqueta": "Tasa implícita sep–dic 2025", "valor": f"{cruce['tasa_implicita'].mean():.0%}" if len(cruce) else "Sin dato",
     "contexto": f"ocupación oficial: {cruce['ocupacion_oficial'].mean():.0%}" if len(cruce) else ""},
])

# --- Capacidad (enlazada con ocupacion) -------------------------------------------------------------
estado = st.session_state.get("m3_cap_anual")
puntos = estado.selection.points if estado and estado.selection else []
anio_sel = next((int(p["customdata"]) for p in puntos if p.get("customdata") is not None), None)

c1, c2 = st.columns([1, 1.3], gap="small")
with c1, mosaico(
    "m3-cap-anual", f"Capacidad instalada de {DEPTO}", "Cortes anuales completos (T4) · clic en un año para ver su ocupación",
    "observado",
    "**¿Cuánta capacidad hay y cómo ha crecido?**\n\nCada barra es el inventario físico al cierre del año (cuarto "
    "trimestre). Al hacer clic en un año, la gráfica de ocupación se enfoca en ese año. El corte 2026 (solo T1, "
    "levantamiento parcial) se muestra en el desglose por tipo, no aquí.",
    filtro=str(anio_sel) if anio_sel else None,
    enlazada=True,
):
    grafica(fig_capacidad_anual(anual, medida, anio_sel), "m3_cap_anual", enlazada=True)

with c2, mosaico(
    "m3-ocup", "Tasa de ocupación mensual", f"{DEPTO} (verde azulado) frente a los demás departamentos (gris)", "observado",
    "**¿Qué tan llena está la capacidad mes a mes?**\n\nSerie mensual continua 2023–2025 del índice de ocupación "
    "departamental. Si eligió un año en la capacidad, la gráfica se enfoca en ese año.",
    filtro=str(anio_sel) if anio_sel else None,
):
    if anio_sel and anio_sel not in set(o_dep.index.year):
        sin_datos(f"No hay ocupación registrada para {anio_sel} (la serie cubre 2023–2025).")
    fig = fig_ocupacion(ocup, DEPTO)
    if anio_sel and anio_sel in set(o_dep.index.year):
        fig.update_xaxes(range=[pd.Timestamp(anio_sel, 1, 1) - pd.Timedelta(days=10), pd.Timestamp(anio_sel, 12, 1) + pd.Timedelta(days=10)])
        oa = o_dep[o_dep.index.year == anio_sel]
        st.caption(f"{anio_sel}: ocupación promedio {oa.mean():.0%} con {formato_numero(anual.loc[anio_sel, 'plazas_cama'])} "
                   f"plazas cama; mes más lleno {MES_ES[oa.idxmax().month - 1]} ({oa.max():.0%}), más vacío "
                   f"{MES_ES[oa.idxmin().month - 1]} ({oa.min():.0%}).")
    grafica(fig, "m3_ocup")

parcial = cap[cap["corte_parcial"]]
repite = f"el {parcial['repite_previo'].mean():.0%} de los tipos repite" if len(parcial) else "puede repetir"
c3, c4 = st.columns([1.3, 1], gap="small")
with c3, mosaico(
    "m3-cap-tipo", "Capacidad por tipo de alojamiento", "Todos los cortes · trama: corte parcial", "observado",
    "**¿Qué tipo de alojamiento domina?**\n\nEl corte de 2026 es solo del primer trimestre (tres meses después del "
    f"anterior, no doce) y se levantó de forma parcial: {repite} exactamente el valor del año previo. Por eso se "
    "dibuja con trama y no entra al cálculo de crecimiento.",
):
    grafica(fig_capacidad(cap, medida), "m3_cap")
    if len(parcial):
        st.caption(f"Corte parcial: {parcial['repite_previo'].mean():.0%} de los tipos de alojamiento repiten el valor anterior.")

matriz = of.matriz_ocupacion(ocup, DEPTO)
with c4, mosaico(
    "m3-heat", "Calendario de ocupación", f"{DEPTO} · año × mes", "observado",
    "**Visualización adicional del grupo.** El mapa de calor deja ver de un vistazo la temporada alta (más oscuro) y "
    "baja, y si se repite cada año. Ayuda a planificar promoción en los meses valle.",
):
    grafica(fig_heatmap_ocupacion(matriz), "m3_heat")
    perfil_mes = matriz.mean()
    st.caption(f"Meses más llenos en promedio: {', '.join(MES_ES[i - 1] for i in perfil_mes.nlargest(3).index)}. "
               f"Más vacíos: {', '.join(MES_ES[i - 1] for i in perfil_mes.nsmallest(3).index)}.")

# --- Ventana coincidente ---------------------------------------------------------------------------
c5, c6 = st.columns([1.5, 1], gap="small")
with c5, mosaico(
    "m3-ventana", "Ventana coincidente: demanda de noches vs. capacidad", f"{MES_ES[v0.month - 1]}–{MES_ES[v1.month - 1]} {v1.year}, "
    "únicos meses con telefonía y ocupación", "observado",
    "**¿La capacidad formal alcanza para las noches que pasan los turistas en el lago?**\n\n"
    "- **Noches demandadas** = Σ días-persona de los turistas con pernocta (suma de los 10 municipios).\n"
    "- **Plazas-noche** = plazas cama del corte del año × días del mes.\n"
    "- **Tasa implícita** = noches demandadas / plazas-noche, comparable con la ocupación oficial.\n\n"
    f"Noches y porcentajes van en paneles separados. Solo {len(cruce)} meses: la lectura es indicativa.",
):
    if cruce.empty:
        sin_datos("Falta alguna de las dos series en la ventana coincidente.")
    else:
        grafica(fig_cruce_ventana(cruce), "m3_ventana")
        with st.expander("Tabla de la ventana", icon=":material/table:"):
            tab = cruce.rename(index=lambda t: f"{MES_ES[t.month - 1]} {t.year}")
            st.dataframe(tab, width="stretch", column_config={
                "turistas": st.column_config.NumberColumn("Turistas", format="localized"),
                "noches_demandadas": st.column_config.NumberColumn("Noches demandadas", format="localized"),
                "plazas_noche": st.column_config.NumberColumn("Plazas-noche", format="localized"),
                "tasa_implicita": st.column_config.NumberColumn("Tasa implícita", format="percent"),
                "ocupacion_oficial": st.column_config.NumberColumn("Ocupación oficial", format="percent"),
                "brecha": st.column_config.NumberColumn("Brecha (pp)", format="percent"),
            })
with c6, st.container(key="tile-m3-lectura"):
    st.html('<div class="ot-tt">Lectura del cruce</div><div class="ot-ts">Ventana coincidente</div>')
    if len(cruce):
        brecha = cruce["brecha"].mean()
        r = cruce["noches_demandadas"].corr(cruce["ocupacion_oficial"]) if len(cruce) >= 3 else float("nan")
        if pd.isna(r):
            juntas = f"Con {len(cruce)} meses no se puede medir si se mueven juntas."
        elif r >= 0.5:
            juntas = f"Ambas se mueven juntas (correlación {r:.2f}, {len(cruce)} meses)."
        else:
            juntas = f"No se mueven juntas (correlación {r:.2f}, {len(cruce)} meses)."
        nota("observado", f"Los turistas del lago demandan en promedio {formato_numero(cruce['noches_demandadas'].mean())} "
             f"noches al mes, el {cruce['tasa_implicita'].mean():.0%} de las plazas-noche formales de {DEPTO}; la ocupación "
             f"oficial fue {cruce['ocupacion_oficial'].mean():.0%}. {juntas}")
        if brecha > 0:
            nota("interpretacion", "La tasa implícita **supera** a la oficial: parte de las noches ocurre fuera de la "
                 "hotelería formal registrada (plataformas digitales como Airbnb, casas de familia) o la suma de "
                 "municipios duplica turistas que se movieron entre pueblos.")
        else:
            nota("interpretacion", "La tasa implícita **queda por debajo** de la oficial: los hoteles de "
                 f"{DEPTO} también reciben huéspedes que la telefonía del lago no capta (otros municipios del "
                 "departamento, viajeros de negocios) o hay visitantes sin teléfono detectado.")
    nota("interpretacion", "Hotelería formal y plataformas digitales son universos distintos: este cruce no sustituye un "
         "registro de alojamiento no formal.")

# --- Subdestinos -----------------------------------------------------------------------------------
c7, c8 = st.columns([1.3, 1], gap="small")
with c7, mosaico(
    "m3-sub", "Afluencia relativa entre municipios", "Índice frente a Panajachel = 100 (no participación sobre un total)",
    "observado",
    "**¿Cómo se reparte la afluencia dentro del lago?**\n\nCada municipio se compara con Panajachel. Se usa un índice y "
    "no un porcentaje del total porque **los municipios no se suman** (un visitante puede recorrer varios). "
    "Con 'días-persona' se compara la carga de noches en vez de las personas.",
):
    s1, s2 = st.columns(2)
    origen = s1.segmented_control("Origen", ["Todos", "Nacional", "Extranjero"], default="Todos", key="m3_sub_origen") or "Todos"
    base = s2.segmented_control("Medida", ["Visitantes", "Días-persona"], default="Visitantes", key="m3_sub_medida") or "Visitantes"
    perfil = ind.por_municipio(ind.filtrar(m, origen=origen))
    col = "visitantes_mes" if base == "Visitantes" else "dias_persona_mes"
    if "Panajachel" in perfil.index and perfil.loc["Panajachel", col] > 0:
        rel = perfil[col] / perfil.loc["Panajachel", col] * 100
        grafica(fig_afluencia_relativa(rel), "m3_sub")
with c8, st.container(key="tile-m3-sub-lectura"):
    st.html('<div class="ot-tt">Lectura territorial</div><div class="ot-ts">Dónde se concentra la carga</div>')
    perfil_todo = ind.por_municipio(m)
    if "Panajachel" not in perfil_todo.index or len(perfil_todo) < 2:
        sin_datos("Panajachel no aparece en la base mensual: no se puede calcular el índice de afluencia relativa.")
    else:
        rel_v = perfil_todo["visitantes_mes"] / perfil_todo.loc["Panajachel", "visitantes_mes"] * 100
        rel_n = perfil_todo["dias_persona_mes"] / perfil_todo.loc["Panajachel", "dias_persona_mes"] * 100
        sube = (rel_n - rel_v).idxmax()
        nota("observado", f"Fuera de Panajachel, **{corto(rel_v.drop('Panajachel').idxmax())}** es el municipio con más "
             f"visitantes (índice {rel_v.drop('Panajachel').max():.0f}).")
        if rel_n[sube] > rel_v[sube]:
            nota("interpretacion", f"Al medir en días-persona, **{corto(sube)}** gana más peso relativo ({rel_v[sube]:.0f} → "
                 f"{rel_n[sube]:.0f}): recibe menos personas pero se quedan más noches, lo que presiona la oferta local de "
                 "alojamiento de forma distinta a las puertas de entrada (módulo 4).")
