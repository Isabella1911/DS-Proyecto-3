"""Modulo 4 · Red territorial y caracterizacion de los 10 municipios (reto del grupo 3).

Cuadrante analitico volumen x estadia media x especializacion extranjera (IEE) que clasifica a los pueblos en hubs
comerciales (puertas de entrada), larga estancia/retiro y visita corta; la clasificacion por regla se
contrasta con k-medias y se valida con la dinamica diaria (fin de semana y festividades) de cada pueblo.
Vista enlazada: un clic en un municipio del cuadrante abre su perfil y lo marca en la matriz.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src import indicadores as ind
from src import territorio as te
from src.datos import corto, origenes, tabla
from src.estilo import COLORES_CLASE, formato_numero
from src.graficas import (
    fig_cuadrante, fig_mapa_pueblos, fig_estacionalidad_clase, fig_huella_semanal, fig_matriz_perfiles, fig_mensual_origen,
    fig_mercados_clase, fig_patron_semanal, fig_top_paises,
)
from src.normalizar import MUNICIPIOS
from src.ui import aviso_sinteticos, barra_filtros, encabezado_pagina, grafica, indicadores, mosaico, nota, siguiente

m = tabla("mensual")
d = tabla("diaria")


@st.cache_data(show_spinner=False)
def _perfil(m, d):
    return te.clasificar(te.perfil_completo(m, d))


perfil = _perfil(m, d)
cortes = te.cortes_regla(perfil)

encabezado_pagina(
    "Módulo 4. Análisis especializado del destino",
    "Red territorial de los diez municipios ribereños",
    "Tipología de los municipios según su función en el destino: puertas de entrada o hubs, que concentran el flujo; "
    "destinos de larga estancia, con estadías en el cuartil superior y mayor especialización extranjera que el lago; "
    "y destinos de visita corta.",
    "Fuente: telefonía móvil, bases mensual y diaria<br><b>10 municipios</b>",
)
aviso_sinteticos(origenes())

with barra_filtros("m4"):
    metodo = st.segmented_control(
        "Método de clasificación", ["Regla del cuadrante", "k-medias"], default="Regla del cuadrante", key="m4_metodo",
        help="Regla: cortes interpretables sobre volumen, estadía y especialización extranjera. k-medias: agrupa a "
        "los pueblos por parecido en 4 variables estandarizadas, sin reglas fijas; sirve de contraste.",
    ) or "Regla del cuadrante"
col_clase = "clase_regla" if metodo == "Regla del cuadrante" else "clase_kmedias"
perfil["clase"] = perfil[col_clase]
clases = perfil["clase"]
por_clase = te.perfil_por_clase(perfil, "clase")

n_clase = clases.value_counts()
indicadores([
    {"etiqueta": "Hubs comerciales (puertas de entrada)", "valor": str(n_clase.get("Hub comercial", 0)),
     "contexto": ", ".join(corto(x) for x in perfil.index[clases == "Hub comercial"])},
    {"etiqueta": "Destinos de larga estancia", "valor": str(n_clase.get("Larga estancia", 0)),
     "contexto": ", ".join(corto(x) for x in perfil.index[clases == "Larga estancia"])},
    {"etiqueta": "Destinos de visita corta", "valor": str(n_clase.get("Visita corta", 0)), "contexto": ", ".join(corto(x) for x in perfil.index[clases == "Visita corta"])},
    {"etiqueta": "Coincidencia entre regla y k-medias", "valor": f"{perfil['coinciden'].sum()} de {len(perfil)}",
     "contexto": "Municipios con la misma clase en ambos métodos"},
])

# --- Cuadrante (origen del enlace) -------------------------------------------------------------------
estado = st.session_state.get("m4_cuadrante")
puntos = estado.selection.points if estado and estado.selection else []
sel = next((p["customdata"][0] for p in puntos if p.get("customdata") and p["customdata"][0] in MUNICIPIOS), None)

c1, c2 = st.columns([1.5, 1], gap="small")
with c1, mosaico(
    "m4-cuadrante", "Tipología de los municipios: volumen, estadía y especialización extranjera",
    f"Clasificación por {metodo.lower() if metodo != 'k-medias' else 'k-medias'}. El tamaño del punto representa la especialización extranjera",
    "interpretacion",
    "**¿Qué tipo de destino es cada pueblo?**\n\n- Eje X: visitantes promedio por mes (escala logarítmica).\n"
    "- Eje Y: estadía media ponderada de los turistas con pernocta (Σ días-persona / Σ visitantes, > 1 día).\n"
    "- Tamaño: **especialización extranjera (IEE)** = cuota del pueblo entre los extranjeros del lago / su cuota "
    "entre los nacionales. IEE > 1: atrae proporcionalmente más extranjeros que el lago. Se usa en lugar de "
    "'extranjeros / total' porque los nacionales traen factor de expansión y la guía prohíbe esa división.\n"
    "- Color y forma: clase (círculo = hub, rombo = larga estancia, cuadrado = visita corta).\n\n"
    f"**Regla** (líneas punteadas): larga estancia = estadía ≥ {cortes['estadia_larga']:.2f} días (P75 del lago) "
    f"e IEE ≥ 1; hub = volumen ≥ {formato_numero(cortes['volumen_hub'])} visitantes/mes (60 % del mayor); visita "
    "corta = el resto. La permanencia tiene prioridad sobre el volumen. **k-medias** agrupa por parecido en "
    "volumen, estadía, IEE y presión de fin de semana.",
    filtro=corto(sel) if sel else None,
    enlazada=True,
):
    grafica(fig_cuadrante(perfil, sel, cortes), "m4_cuadrante", enlazada=True)

with c2, st.container(key="tile-m4-clases"):
    st.html('<div class="ot-tt">Características de cada tipo de municipio</div><div class="ot-ts">Promedio simple de los municipios de cada clase</div>')
    for clase, fila in por_clase.iterrows():
        miembros = ", ".join(corto(x) for x in perfil.index[clases == clase])
        st.html(
            f'<div style="margin:.45rem 0 .1rem"><span class="ot-tag" style="background:{COLORES_CLASE[clase]};color:#fff">'
            f'{clase}</span> <span style="font-size:.8rem;color:#525252">{miembros}</span></div>'
            f'<div style="font-size:.8rem;color:#393939;line-height:1.5">{formato_numero(fila["visitantes_mes"])} visitantes por mes; '
            f'estadía de {fila["estadia_media"]:.1f} días; especialización extranjera {fila["iee"]:.2f}; '
            f'{fila["pct_excursionistas"]:.0%} excursionistas; fin de semana {fila["presion_finde"]:.2f} veces un día hábil.</div>'
        )
    distintos = perfil.index[~perfil["coinciden"]]
    if len(distintos):
        detalle = "; ".join(f"{corto(x)} ({perfil.loc[x, 'clase_regla'].lower()} por regla, "
                            f"{perfil.loc[x, 'clase_kmedias'].lower()} por k-medias)" for x in distintos)
        nota("interpretacion", f"Los métodos difieren en {len(distintos)} municipios: {detalle}. Son municipios de "
             "transición; k-medias separa sobre todo por niveles de volumen. La matriz de perfiles muestra en qué "
             "indicadores se aproximan a cada clase.")
    else:
        nota("interpretacion", f"La regla y k-medias coinciden en los {len(perfil)} municipios: la clasificación es robusta.")
    estab = perfil.attrs.get("estabilidad_kmedias", float("nan"))
    if pd.notna(estab):
        nota("observado", f"Estabilidad de k-medias: al excluir un municipio a la vez y repetir el agrupamiento, el "
             f"{estab:.0%} de los restantes conserva su clase. "
             + ("Los grupos son estables." if estab >= 0.8 else "Los grupos son inestables y solo sirven como contraste de la regla."))

# --- Mapa: peso de cada pueblo mes a mes ---------------------------------------------------------------
meses_obs = sorted(m["periodo"].unique())
with mosaico(
    "m4-mapa", "Visitantes por municipio y mes",
    f"Visitantes únicos del mes en cada municipio, {len(meses_obs)} meses con cobertura. El botón Reproducir recorre los meses",
    "observado",
    "**¿Cómo cambia el peso de cada pueblo a lo largo del año?**\n\nCada burbuja es un municipio en su cabecera; el "
    "tamaño es su número de visitantes únicos en el mes (misma escala en todos los meses) y el color su clase. "
    "Los municipios **no se suman**: cada burbuja es su propio conteo. Enero y febrero de 2026 no tienen cobertura "
    "de telefonía y no se dibujan (no son cero). La base no trae pares origen-destino entre pueblos, por eso no hay "
    "flechas de desplazamiento: solo el peso de cada uno.",
):
    grafica(fig_mapa_pueblos(m, clases, te.COORDENADAS), "m4_mapa")
    serie_mun = m.groupby(["periodo", "municipio"])["visitantes"].sum().unstack()
    cv = (serie_mun.std() / serie_mun.mean()).sort_values()
    st.caption(f"Pueblo más estable entre meses: **{corto(cv.index[0])}** (variación {cv.iloc[0]:.0%}); más estacional: "
               f"**{corto(cv.index[-1])}** (variación {cv.iloc[-1]:.0%}, coeficiente de variación de los visitantes mensuales).")

# --- Matriz de perfiles y huella semanal -----------------------------------------------------------
c3, c4 = st.columns([1.25, 1], gap="small")
with c3, mosaico(
    "m4-matriz", "Perfil comparado de los municipios", "Valor de cada indicador; el tono indica la posición relativa dentro del lago", "observado",
    "**¿En qué se diferencia cada pueblo?**\n\nCada columna es un indicador con su valor real escrito; el color indica "
    "si el municipio está entre los menores (claro) o los mayores (oscuro) del lago **en esa columna**. Así se comparan "
    "variables de unidades distintas sin mezclarlas. La presión de fin de semana y el Lift vienen de la base diaria.",
    filtro=corto(sel) if sel else None,
):
    grafica(fig_matriz_perfiles(perfil, sel), "m4_matriz")
with c4, mosaico(
    "m4-huella", "Afluencia por día de la semana y municipio", "Índice de días regulares, promedio semanal = 100. Las líneas separan las clases",
    "observado",
    "**¿Quién se llena el fin de semana?**\n\nBase diaria: rojo = por debajo del promedio de la semana, azul = por "
    "encima. Si la clasificación es correcta, los pueblos de visita corta dependen más del sábado y domingo "
    "(excursiones) y los de larga estancia tienen una semana más pareja; los hallazgos al final lo comprueban.",
):
    grafica(fig_huella_semanal(te.huella_semanal(d), clases), "m4_huella")

# --- Comparacion entre clases ------------------------------------------------------------------------
c5, c6 = st.columns(2, gap="small")
with c5, mosaico(
    "m4-mercados", "Mercados emisores extranjeros por tipo de municipio", "Composición porcentual de los visitantes extranjeros", "observado",
    "**¿Atraen las clases a mercados distintos?**\n\nPorcentaje de los extranjeros de cada clase que viene de cada uno "
    "de los 8 principales países del lago. Diferencias aquí orientan la promoción por mercado de cada tipo de pueblo.",
):
    grafica(fig_mercados_clase(te.mercados_por_clase(m, clases)), "m4_mercados")
with c6, mosaico(
    "m4-estac", "Estacionalidad por tipo de municipio", "Índice mensual de visitantes, promedio de los meses observados = 100", "observado",
    "**¿Tienen la misma temporada?**\n\nEs un índice de forma: aunque sumar municipios de una clase duplique visitantes, "
    "el patrón entre meses se conserva. Los meses sin cobertura de telefonía aparecen vacíos.",
):
    grafica(fig_estacionalidad_clase(te.estacionalidad_por_clase(m, clases)), "m4_estac")

# --- Perfil del municipio elegido -------------------------------------------------------------------
mun = sel or perfil["visitantes_mes"].idxmax()
g = m[m["municipio"] == mun]
gd = d[d["municipio"] == mun]
k = ind.kpis_demanda(g)
fila = perfil.loc[mun]
st.html(f'<div class="ot-sec">Perfil municipal: {mun}</div><div class="ot-ts">'
        + ("Municipio seleccionado en la tipología." if sel else
           "Se muestra el municipio de mayor afluencia; seleccione otro en la gráfica de tipología.") + "</div>")
indicadores([
    {"etiqueta": "Clase", "valor": fila["clase"],
     "contexto": "Coincide en ambos métodos" if fila["coinciden"] else f"k-medias: {fila['clase_kmedias'].lower()}" if col_clase == "clase_regla" else f"Regla: {fila['clase_regla'].lower()}"},
    {"etiqueta": "Visitantes promedio por mes", "valor": formato_numero(k["visitantes_mes"]), "serie": k["serie_visitantes"],
     "contexto": f"{k['meses']} meses con dato"},
    {"etiqueta": "Estadía media ponderada", "valor": f"{k['estadia_media']:.2f} días", "serie": k["serie_estadia"],
     "contexto": "Turistas con pernocta"},
    {"etiqueta": "Presión de fin de semana", "valor": f"{fila['presion_finde']:.2f}×",
     "contexto": f"Especialización extranjera: {fila['iee']:.2f} (lago = 1)"},
])
c7, c8, c9 = st.columns(3, gap="small")
with c7, mosaico("m4-serie", "Visitantes por mes y origen", "Nacionales y extranjeros; meses sin cobertura en blanco", "observado",
                 "Serie mensual del municipio, separando nacionales (con factor de expansión) y extranjeros.", filtro=corto(mun)):
    grafica(fig_mensual_origen(g), "m4_serie")
with c8, mosaico("m4-semana", "Afluencia por día de la semana", "Índice de días regulares, promedio semanal = 100", "observado",
                 "Índice de visitantes por día de la semana del municipio elegido (base diaria).", filtro=corto(mun)):
    grafica(fig_patron_semanal(ind.patron_semanal(ind.serie_diaria(gd))), "m4_semana")
with c9, mosaico("m4-paises", "Principales mercados extranjeros", "Ocho principales países de procedencia", "observado",
                 "Mercados emisores extranjeros del municipio elegido.", filtro=corto(mun)):
    top = ind.top_paises(g, 8)
    if not top.empty:
        grafica(fig_top_paises(top), "m4_paises")

# --- Hallazgos ----------------------------------------------------------------------------------------
with st.container(key="tile-m4-hallazgos"):
    st.html('<div class="ot-tt">Resultados del análisis territorial</div><div class="ot-ts">Telefonía móvil, septiembre de 2025 a agosto de 2026</div>')
    hub = por_clase.loc["Hub comercial"] if "Hub comercial" in por_clase.index else None
    larga = por_clase.loc["Larga estancia"] if "Larga estancia" in por_clase.index else None
    corta = por_clase.loc["Visita corta"] if "Visita corta" in por_clase.index else None
    if hub is not None and larga is not None:
        nota("observado", f"Los municipios de larga estancia reciben, en promedio, el "
             f"{larga['visitantes_mes'] / hub['visitantes_mes']:.0%} de los visitantes de un hub, pero sus turistas "
             f"permanecen {larga['estadia_media']:.1f} días frente a {hub['estadia_media']:.1f}"
             + (", por lo que generan más noches por visitante." if larga["estadia_media"] > hub["estadia_media"] else "."))
    if corta is not None and larga is not None:
        nota("observado", f"En los municipios de visita corta, el {corta['pct_excursionistas']:.0%} de los visitantes son "
             f"excursionistas. La presión de fin de semana es de {corta['presion_finde']:.2f} veces un día hábil, frente a "
             f"{larga['presion_finde']:.2f} en los de larga estancia"
             + (f" y {hub['presion_finde']:.2f} en los hubs." if hub is not None else "."))
    top_iee = perfil["iee"].idxmax()
    if perfil.loc[top_iee, "clase"] != "Larga estancia":
        nota("interpretacion", f"{corto(top_iee)} presenta la mayor especialización extranjera del lago "
             f"({perfil.loc[top_iee, 'iee']:.2f}), pero su estadía media es de {perfil.loc[top_iee, 'estadia_media']:.1f} días, "
             f"por debajo de la mediana ({cortes['mediana_estadia']:.1f}). Los datos de telefonía no respaldan su imagen "
             "de destino de retiro. Una explicación posible es que parte de sus visitantes extranjeros pernocte en un "
             "municipio vecino; conviene verificarlo antes de orientar hacia él la promoción de estadías largas.")
    if hub is not None and corta is not None:
        if hub["presion_finde"] > corta["presion_finde"]:
            nota("interpretacion", "Implicación para el INGUAT: la presión de fin de semana se concentra en los hubs, "
                 "donde predomina el visitante nacional que llega por carretera. El refuerzo de transporte lacustre, "
                 "seguridad y servicios debe priorizar sábados y domingos en las puertas de entrada; la promoción "
                 "internacional de estadías largas tiene mayor rendimiento en los municipios de larga estancia.")
        else:
            nota("interpretacion", "Implicación para el INGUAT: el refuerzo de transporte lacustre, seguridad y servicios "
                 "debe priorizar fines de semana y feriados en los municipios de visita corta; la promoción internacional "
                 "de estadías largas tiene mayor rendimiento en los municipios de larga estancia.")

# --- Hilo hacia el siguiente modulo --------------------------------------------------------------
siguiente(
    "paginas/conclusiones.py", "Conclusiones y recomendaciones",
    "Síntesis de los cuatro módulos y recomendaciones para el INGUAT, cada una con la evidencia que la respalda.",
    ":material/flag:",
)
