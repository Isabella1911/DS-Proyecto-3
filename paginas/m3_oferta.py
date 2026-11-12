"""Modulo 3 · Oferta hotelera y desagregacion territorial.

Vista enlazada: un clic en un anio de la capacidad instalada enfoca la serie de ocupacion en ese anio.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src import indicadores as ind
from src import oferta as of
from src.datos import CONFIG, corto, origenes, tabla, tabla_opcional
from src.estilo import formato_numero
from src.graficas import (
    MES_ES, fig_afluencia_relativa, fig_barras_pct, fig_capacidad, fig_capacidad_anual, fig_cruce_ventana, fig_heatmap_ocupacion,
    fig_ocupacion,
)
from src.normalizar import departamento
from src.ui import aviso_sinteticos, barra_filtros, encabezado_pagina, grafica, indicadores, mosaico, nota, siguiente, sin_datos

DEPTO = departamento(CONFIG["destino"]["departamento"])
oferta = tabla("oferta")
ocup = tabla("ocupacion")
m = tabla("mensual")
boletin = tabla_opcional("boletin_hotelero")
frontera = tabla_opcional("frontera_destino")

encabezado_pagina(
    "Módulo 3 · Oferta",
    "Oferta hotelera y desagregación territorial",
    f"¿Alcanza la capacidad de alojamiento de {DEPTO} y dónde duermen los visitantes del lago? Capacidad instalada, "
    "ocupación mensual, su cruce con la afluencia en la única ventana en que coinciden (sep–dic 2025) y el tipo de "
    "alojamiento que declaran quienes entran al país rumbo al lago.",
    f"Oferta 2022–2026 · Ocupación y boletines 2023–2025<br>Encuesta en fronteras · Departamento: <b>{DEPTO}</b>",
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
cruce = of.cruce_ventana(m, boletin, o_dep, (v0, v1))
res_cruce = of.resumen_cruce(cruce)
indicadores([
    {"etiqueta": f"Plazas cama {a1}", "valor": formato_numero(anual.loc[a1, "plazas_cama"]),
     "delta": anual.loc[a1, "plazas_cama"] / anual.loc[a0, "plazas_cama"] - 1, "delta_texto": f"frente a {a0}",
     "serie": anual["plazas_cama"].tolist()},
    {"etiqueta": f"Establecimientos {a1}", "valor": formato_numero(anual.loc[a1, "establecimientos"]),
     "contexto": f"{anual.loc[a1, 'habitaciones'] / anual.loc[a1, 'establecimientos']:.1f} habitaciones por establecimiento",
     "serie": anual["establecimientos"].tolist()},
    {"etiqueta": f"Ocupación promedio {ult_anio_ocup}", "valor": f"{ocup_anio.mean():.0%}",
     "contexto": f"pico: {MES_ES[ocup_anio.idxmax().month - 1]} ({ocup_anio.max():.0%})", "serie": o_dep.tolist()},
    {"etiqueta": "Captación formal de noches extranjeras", "valor":
        f"{res_cruce.loc['Extranjero', 'captacion']:.0%}" if "Extranjero" in res_cruce.index else "Sin dato",
     "contexto": (f"sep–dic 2025 · nacionales: {res_cruce.loc['Nacional', 'captacion']:.1%}"
                  if "Nacional" in res_cruce.index else "requiere los boletines de ocupación (PDF)")},
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
        rep_dep = parcial["repite_previo"].mean()
        st.caption(f"Corte parcial (2026-T1): {rep_dep:.0%} de los tipos de alojamiento de {DEPTO} repiten el valor anterior"
                   + (" (en el país, cerca de la mitad de las combinaciones lo hace). Aun así es un levantamiento de "
                      "tres meses y no entra al crecimiento." if rep_dep == 0 else "."))

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

# --- Ventana coincidente: triangulacion telefonia x hoteleria formal ------------------------------------
ORIGENES_CRUCE = {"Extranjeros · no residentes": "Extranjero", "Nacionales · residentes": "Nacional"}
c5, c6 = st.columns([1.5, 1], gap="small")
with c5, mosaico(
    "m3-ventana", "Ventana coincidente: ¿qué parte de las noches pasa por un hotel formal?",
    f"{MES_ES[v0.month - 1]}–{MES_ES[v1.month - 1]} {v1.year}, únicos meses con telefonía y ocupación · por origen",
    "observado",
    "**¿Cuántas de las noches que pasan los turistas en el lago quedan registradas en la hotelería formal?**\n\n"
    "- **Noches por telefonía** = Σ (días-persona − visitantes) de los turistas con pernocta: quien está *d* días "
    "pasa *d* − 1 noches. Suma de los 10 municipios (cota superior).\n"
    f"- **Noches en hotel formal** = pernoctaciones registradas en los hoteles de {DEPTO}, del boletín anual de "
    "ocupación del INGUAT (se extraen con código; el CSV solo trae el índice).\n"
    "- **Captación formal** = noches en hotel / noches por telefonía. Como el denominador es una cota superior, "
    "es una cota **inferior**.\n\n"
    "Extranjeros se comparan con *no residentes* y nacionales con *residentes*, nunca mezclados. Noches y "
    "porcentajes van en paneles separados. Solo 4 meses: la lectura es indicativa.",
):
    eleccion = st.segmented_control("Origen", list(ORIGENES_CRUCE), default=list(ORIGENES_CRUCE)[0], key="m3_cruce_origen") \
        or list(ORIGENES_CRUCE)[0]
    origen_c = ORIGENES_CRUCE[eleccion]
    g = cruce[cruce["origen"] == origen_c]
    if g.empty or g["noches_hotel"].isna().all():
        sin_datos("Faltan los boletines de ocupación hotelera (PDF) en la carpeta de datos: sin ellos no hay noches "
                  "de hotel por residencia para cruzar con la telefonía.")
    else:
        grafica(fig_cruce_ventana(g, "Noches por telefonía (turistas " + ("extranjeros)" if origen_c == "Extranjero" else "nacionales)"),
                                  "Noches en hotel formal (" + ("no residentes)" if origen_c == "Extranjero" else "residentes)")),
                "m3_ventana")
        with st.expander("Tabla de la ventana", icon=":material/table:"):
            tab = g.assign(mes=[f"{MES_ES[t.month - 1]} {t.year}" for t in g["periodo"]]).set_index("mes")
            st.dataframe(tab[["turistas_telefonia", "noches_telefonia", "huespedes_hotel", "noches_hotel", "captacion_formal",
                              "ocupacion_oficial"]], width="stretch", column_config={
                "turistas_telefonia": st.column_config.NumberColumn("Turistas (telefonía)", format="localized"),
                "noches_telefonia": st.column_config.NumberColumn("Noches (telefonía)", format="localized"),
                "huespedes_hotel": st.column_config.NumberColumn("Huéspedes en hotel", format="localized"),
                "noches_hotel": st.column_config.NumberColumn("Noches en hotel", format="localized"),
                "captacion_formal": st.column_config.NumberColumn("Captación formal", format="percent"),
                "ocupacion_oficial": st.column_config.NumberColumn("Ocupación oficial", format="percent"),
            })
with c6, st.container(key="tile-m3-lectura"):
    st.html('<div class="ot-tt">Lectura del cruce</div><div class="ot-ts">Ventana coincidente · tres fuentes</div>')
    if res_cruce.empty:
        nota("interpretacion", "Sin los boletines solo puede compararse la ocupación oficial; agregue los PDF para "
             "medir la captación formal por origen.")
    else:
        for origen_r, fila in res_cruce.iterrows():
            quien = "extranjeros" if origen_r == "Extranjero" else "nacionales"
            juntas = (f"ambas series se mueven juntas (r = {fila['correlacion']:.2f})" if fila["correlacion"] >= 0.5
                      else f"las series no se mueven juntas (r = {fila['correlacion']:.2f})") if pd.notna(fila["correlacion"]) else ""
            nota("observado", f"**{quien.capitalize()}:** la telefonía registra {formato_numero(fila['noches_telefonia_mes'])} "
                 f"noches al mes y los hoteles formales {formato_numero(fila['noches_hotel_mes'])}: captación de "
                 f"**{fila['captacion']:.1%}**" + (f"; {juntas}." if juntas else "."))
        if {"Extranjero", "Nacional"} <= set(res_cruce.index):
            ce, cn = res_cruce.loc["Extranjero", "captacion"], res_cruce.loc["Nacional", "captacion"]
            nota("interpretacion", f"La hotelería formal capta una parte importante del turismo extranjero ({ce:.0%}) pero "
                 f"casi nada de la presencia nacional con pernocta ({cn:.1%}): la mayoría de esas noches ocurre en casas de "
                 "familia, alojamiento no registrado o plataformas digitales, o corresponde a presencia no turística que la "
                 "telefonía no distingue. La ocupación oficial describe al turismo extranjero mucho mejor que al nacional.")
        nota("observado", f"Ocupación oficial de la ventana: {cruce.drop_duplicates('periodo')['ocupacion_oficial'].mean():.0%} "
             f"(el boletín coincide con el CSV en todos los meses comparados).")
    nota("interpretacion", "Hotelería formal y plataformas digitales son universos distintos: este cruce mide cuánto "
         "capta el registro formal, no la capacidad total de alojamiento del lago.")

# --- Encuesta en fronteras: donde se alojan quienes van al lago ------------------------------------------
if frontera is not None and not frontera.empty:
    olas = frontera.groupby("ola").agg(encuestas=("encuestas", "sum"), desde=("desde", "min"), hasta=("hasta", "max"))
    ola_actual = olas["hasta"].idxmax()
    f_act = frontera[frontera["ola"] == ola_actual]
    n_act = int(f_act["encuestas"].sum())
    o = olas.loc[ola_actual]
    periodo_ola = f"{MES_ES[o['desde'].month - 1]} {o['desde'].year} – {MES_ES[o['hasta'].month - 1]} {o['hasta'].year}"
    hosp = f_act.groupby("hospedaje")["encuestas"].sum().drop(index=["N/A"], errors="ignore")
    hosp = hosp / hosp.sum()
    puesto = f_act.groupby("puesto")["encuestas"].sum() / n_act
    puesto = puesto.nlargest(5)
    airbnb_olas = (frontera[frontera["hospedaje"].str.contains("Airbnb", na=False)].groupby("ola")["encuestas"].sum()
                   / frontera.groupby("ola")["encuestas"].sum()).dropna()
    c9, c10, c11 = st.columns([1, 1, 0.9], gap="small")
    with c9, mosaico(
        "m3-hosp", "¿Dónde dicen alojarse quienes van al lago?",
        f"Encuesta en fronteras, ola {ola_actual} ({periodo_ola}) · {n_act:,} encuestas · % muestral", "observado",
        "**Tipo de alojamiento declarado** por los viajeros que, al entrar al país, dicen ir al Lago de Atitlán "
        "(BD complementaria). Es una muestra por cuotas **sin factor de expansión**: se reporta solo como porcentaje "
        "de los encuestados y nunca como total de visitantes. Se usa la ola más reciente porque coincide con la "
        "telefonía.",
    ):
        grafica(fig_barras_pct(hosp, "% de los encuestados",
                               destacar=[h for h in hosp.index if "Airbnb" in h]), "m3_hosp")
    with c10, mosaico(
        "m3-puesto", "¿Por dónde entran al país?", f"Puesto fronterizo de ingreso · ola {ola_actual} · top 5", "observado",
        "**Puerta de ingreso al país** de quienes declaran ir al lago. La encuesta se levanta sobre todo en puestos "
        "terrestres: el aeropuerto está subrepresentado y el porcentaje no describe a todos los visitantes del lago.",
    ):
        grafica(fig_barras_pct(puesto.rename(index=lambda x: x.title()), "% de los encuestados"), "m3_puesto")
    with c11, st.container(key="tile-m3-frontera"):
        st.html('<div class="ot-tt">Lectura de la encuesta</div><div class="ot-ts">Fuente complementaria · porcentajes muestrales</div>')
        formal = hosp[[h for h in hosp.index if "Hotel" in h]].sum()
        plataformas = hosp[[h for h in hosp.index if "Airbnb" in h]].sum()
        nota("observado", f"En la ola {ola_actual}, el {formal:.0%} de los encuestados que van al lago declara hotel o "
             f"similar y el {plataformas:.0%} Airbnb o similar. **{puesto.index[0].title()}** concentra el "
             f"{puesto.iloc[0]:.0%} de los ingresos encuestados.")
        if len(airbnb_olas) > 1:
            nota("interpretacion", f"El peso de Airbnb varía entre {airbnb_olas.min():.0%} y {airbnb_olas.max():.0%} según la "
                 "ola: cambian las cuotas y los puestos encuestados, así que **no se lee como tendencia**. Lo robusto es "
                 "que en todas las olas existe un segmento de plataformas que la oferta hotelera formal no registra.")

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

# --- Hilo hacia el siguiente modulo --------------------------------------------------------------
siguiente(
    "paginas/m4_municipios.py", "Módulo 4 · Red de municipios",
    "La carga de visitantes y noches no se reparte igual entre pueblos. El módulo 4 clasifica a los 10 "
    "municipios según <b>el papel que juegan</b> en la red del lago.",
    ":material/hub:",
)
