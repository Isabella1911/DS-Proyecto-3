"""Modulo 2 · Dinamica temporal, eventos y pronostico predictivo.

Vista enlazada: un clic en una festividad de la grafica de Lift resalta sus dias en la serie diaria.
"""

from __future__ import annotations

import streamlit as st

from src import indicadores as ind
from src import pronostico as pr
from src.datos import CONFIG, corto, origenes, selector_ambito, tabla
from src.estilo import formato_numero
from src.graficas import (
    MES_ES, fig_lift, fig_mensual_estimada, fig_patron_semanal, fig_perfil_estacional, fig_serie_diaria, fig_validacion,
)
from src.ui import aviso_sinteticos, barra_filtros, encabezado_pagina, indicadores, mosaico, nota, sin_datos

d_todo = tabla("diaria")
m_todo = tabla("mensual")
mig = tabla("migracion_mensual")
faltantes = CONFIG["estimacion"]["meses_sin_cobertura"]
anios_perfil = CONFIG["estimacion"]["anios_perfil"]

encabezado_pagina(
    "Módulo 2 · Temporalidad",
    "Dinámica temporal, eventos y pronóstico",
    "¿Qué días se llena el lago, cuánto pesan los feriados y cuántos visitantes hubo en los meses sin dato de "
    "telefonía? Toda cifra estimada se muestra en violeta, con línea discontinua y rotulada 'Estimación'.",
    f"Telefonía diaria y mensual<br>Estimación: <b>{', '.join(faltantes)}</b>",
)
aviso_sinteticos(origenes())

with barra_filtros("m2"):
    c1, c2 = st.columns([1.4, 1], gap="medium")
    ambito = selector_ambito("m2_ambito", c1)
    origen = c2.segmented_control("Origen", ["Todos", "Nacional", "Extranjero"], default="Todos", key="m2_origen") or "Todos"

es_suma = len(ambito) > 1
nombre = "Suma de los 10 municipios" if es_suma else corto(ambito[0])
d = ind.filtrar(d_todo, ambito, origen)
if d.empty:
    sin_datos("No hay registros diarios para esta selección.")
    st.stop()

diaria = ind.serie_diaria(d)
lift = ind.lift_eventos(diaria)
patron_reg = ind.patron_semanal(diaria, solo_regulares=True)
presion = ind.presion_fin_de_semana(patron_reg)

# --- Serie diaria y efecto feriados (enlazadas) ---------------------------------------------------
st.html('<div class="ot-tt" style="margin-top:.25rem">Serie diaria y efecto de las festividades</div>')
estado_lift = st.session_state.get("m2_lift_chart")
puntos = estado_lift.selection.points if estado_lift and estado_lift.selection else []
desde_grafica = next((p.get("y") for p in puntos if p.get("y") in lift.index), None)

eventos = list(lift.index)
if not eventos:
    sin_datos("No hay festividades registradas en la cobertura diaria.")
    st.stop()
c_ev, c_tipo = st.columns([1.4, 1], gap="medium")
ev_sel = desde_grafica or c_ev.selectbox("Festividad", eventos, key="m2_evento",
                                         help="También puede elegirla con un clic en la gráfica de Lift.")
if desde_grafica:
    c_ev.selectbox("Festividad", [desde_grafica], disabled=True, key="m2_evento_bloq",
                   help="Elegida desde la gráfica de Lift; doble clic en la gráfica para liberar.")
tipo_lift = c_tipo.segmented_control(
    "Cálculo del Lift", ["Simple", "Ajustado por día de semana"], default="Simple", key="m2_tipo_lift",
    help="Simple: promedio de los días del evento / promedio del día regular − 1 (definición de la guía). "
    "Ajustado: compara cada día de evento con el día regular del mismo día de la semana.",
) or "Simple"
col_lift = "lift" if tipo_lift == "Simple" else "lift_ajustado"
fila = lift.loc[ev_sel]

indicadores([
    {"etiqueta": f"Lift de {ev_sel}", "valor": f"{fila[col_lift]:+.0%}", "contexto": f"{tipo_lift.lower()} · {int(fila['dias'])} días observados"},
    {"etiqueta": "Visitantes en un día de la festividad", "valor": formato_numero(fila["promedio_dia"]),
     "contexto": f"día regular promedio: {formato_numero(lift.attrs['base_regular'])}"},
    {"etiqueta": "Presión de fin de semana", "valor": f"{presion:.2f}×", "contexto": "sáb-dom frente a lun-vie (días regulares)"},
    {"etiqueta": "Día más concurrido", "valor": patron_reg["promedio"].idxmax(), "contexto": f"índice {patron_reg['indice'].max():.0f} (promedio = 100)"},
])

c1, c2 = st.columns([1.7, 1], gap="small")
with c1, mosaico(
    "m2-diaria", f"Presencia diaria · {nombre}", "Visitantes presentes cada día · puntos ámbar: festividades · azul: la elegida",
    "observado",
    "**¿Cómo se mueve la afluencia día a día?**\n\nLa base diaria mide **presencia por día**: la misma persona aparece "
    "en cada día que pasa en el destino, así que estos valores **no se suman** para obtener los visitantes del mes. "
    "La franja gris marca los días sin cobertura de telefonía (sin dato, no cero). Use la barra inferior para acercarse.",
    filtro=ev_sel,
):
    st.plotly_chart(fig_serie_diaria(diaria, ev_sel), key="m2_diaria", width="stretch")
with c2, mosaico(
    "m2-lift", "Lift por festividad", f"{tipo_lift} · clic en una barra para verla en la serie diaria", "observado",
    "**¿Cuánto sube la afluencia en cada festividad?**\n\n"
    "Lift = (promedio de visitantes en los días del evento ÷ promedio de un día regular) − 1. "
    "Un +50 % significa que un día de esa festividad recibe la mitad más de visitantes que un día regular. "
    "El ajustado por día de semana evita atribuir al feriado el efecto de caer en sábado o domingo.",
):
    st.plotly_chart(fig_lift(lift, col_lift, ev_sel), key="m2_lift_chart", on_select="rerun", selection_mode="points", width="stretch")

# --- Patron semanal -------------------------------------------------------------------------------
c3, c4 = st.columns([1, 1], gap="small")
with c3, mosaico(
    "m2-semana", "Patrón semanal", "Índice de visitantes por día de la semana (promedio = 100)", "observado",
    "**¿Cuánta presión ponen los fines de semana?**\n\nPromedio de visitantes de cada día de la semana dividido entre "
    "el promedio de los siete días. Por defecto se excluyen los días con festividad para que un feriado no infle el "
    "día de la semana en que cayó.",
):
    solo_reg = st.toggle("Solo días regulares (sin festividades)", value=True, key="m2_solo_reg")
    patron = patron_reg if solo_reg else ind.patron_semanal(diaria, solo_regulares=False)
    st.plotly_chart(fig_patron_semanal(patron), key="m2_semana", width="stretch")
with c4, st.container(key="tile-m2-lectura"):
    st.html('<div class="ot-tt">Lectura de la dinámica</div><div class="ot-ts">Eventos y semana</div>')
    top_ev = lift[col_lift].idxmax()
    nota("observado", f"**{top_ev}** es la festividad de mayor impacto en {nombre.lower() if es_suma else nombre}: "
         f"{lift.loc[top_ev, col_lift]:+.0%} frente a un día regular. Los sábados y domingos reciben "
         f"{presion:.2f} veces los visitantes de un día hábil.")
    negativos = lift.index[lift[col_lift] < 0].tolist()
    if negativos:
        nota("interpretacion", f"{', '.join(negativos)} no atraen más visitantes que un día regular: son feriados "
             "cortos que no alcanzan para un viaje al lago.")
    if es_suma:
        nota("interpretacion", "Con 'suma de municipios', un visitante que pasa el día en dos pueblos cuenta dos veces. "
             "El Lift no cambia mucho porque es un cociente, pero los volúmenes son una cota superior.")

# --- Estimacion de ene-feb 2026 y validacion --------------------------------------------------------
st.html('<div class="ot-tt" style="margin-top:.5rem">Estimación de los meses sin cobertura de telefonía</div>')
m = ind.filtrar(m_todo, ambito, origen)
obs = ind.serie_mensual(m)
obs = obs.reindex(ind.calendario(obs.index, faltantes))
resultados = {k: pr.estimar(obs, mig, faltantes, anios_perfil, k) for k in pr.METODOS}
mejor = min(resultados, key=lambda k: resultados[k].mape)
metodo = st.segmented_control(
    "Método de estimación", list(pr.METODOS), default=mejor, format_func=lambda k: f"{k} · {pr.METODOS[k]}", key="m2_metodo",
) or mejor
r = resultados[metodo]

indicadores([
    {"etiqueta": f"Estimación {MES_ES[r.estimados.index[0].month - 1]} {r.estimados.index[0].year}",
     "valor": formato_numero(r.estimados.iloc[0]), "contexto": "visitantes únicos del mes"},
    {"etiqueta": f"Estimación {MES_ES[r.estimados.index[-1].month - 1]} {r.estimados.index[-1].year}",
     "valor": formato_numero(r.estimados.iloc[-1]), "contexto": "visitantes únicos del mes"},
    {"etiqueta": "MAPE (validación)", "valor": f"{r.mape:.1f} %", "contexto": f"{len(r.validacion)} meses observados, dejando uno fuera"},
    {"etiqueta": "MAE / RMSE", "valor": f"{formato_numero(r.mae)} / {formato_numero(r.rmse)}", "contexto": "visitantes por mes"},
])

c5, c6 = st.columns([1.5, 1], gap="small")
with c5, mosaico(
    "m2-estimacion", f"Visitantes por mes · {nombre}", "Observado (negro) y Estimación (violeta, discontinua)", "estimacion",
    "**¿Cuántos visitantes hubo en enero y febrero de 2026?**\n\nLa telefonía no cubre esos meses. Se estiman con la base "
    "de migración:\n\n"
    "- **A · Factor de reparto × migración del mes:** F = Σ visitantes del destino / Σ llegadas internacionales en los "
    "meses observados; estimación = F × llegadas del mes faltante.\n"
    "- **B · Perfil estacional × nivel:** índice estacional de las llegadas (promedio de "
    f"{anios_perfil[0]}–{anios_perfil[-1]}) escalado al nivel observado del destino.\n\n"
    "Por defecto se muestra el método con menor MAPE en la validación.",
):
    st.plotly_chart(fig_mensual_estimada(obs, r.estimados), key="m2_estimacion", width="stretch")
    st.caption(f"Factor estimado: {r.factor:.4f} · método {metodo}. Las estimaciones no se mezclan con lo observado en los "
               "indicadores del módulo 1.")
with c6, mosaico(
    "m2-validacion", "Validación del modelo", "Cada mes observado estimado sin usarlo (validación dejando uno fuera)",
    "estimacion",
    "**¿Qué tan confiable es la estimación?**\n\nPara cada mes observado se recalcula el factor **sin ese mes** y se "
    "estima su valor; la diferencia con lo observado da el error. MAPE = promedio de |error| / observado; "
    "MAE = promedio de |error|; RMSE = raíz del promedio del error al cuadrado.",
):
    st.plotly_chart(fig_validacion(r.validacion), key="m2_validacion", width="stretch")
    comp = {pr.METODOS[k].split(" ×")[0] + f" ({k})": f"{v.mape:.1f} %" for k, v in resultados.items()}
    st.caption("MAPE por método: " + " · ".join(f"{a}: {b}" for a, b in comp.items()))

c7, c8 = st.columns([1, 1.5], gap="small")
with c7, mosaico(
    "m2-perfil", "Perfil estacional de las llegadas internacionales",
    f"Base de migración {anios_perfil[0]}–{anios_perfil[-1]} · violeta: meses que se estiman", "observado",
    "**Visualización adicional del grupo.** Índice de cada mes frente al promedio de su año. Explica por qué la "
    "estimación de enero queda por encima de la de febrero: enero es temporada alta de llegadas internacionales.",
):
    perfil = pr.perfil_estacional(mig, anios_perfil)
    st.plotly_chart(fig_perfil_estacional(perfil, [int(p[-2:]) for p in faltantes]), key="m2_perfil", width="stretch")
with c8, st.container(key="tile-m2-lectura-est"):
    st.html('<div class="ot-tt">Lectura de la estimación</div><div class="ot-ts">Supuestos y límites</div>')
    nota("estimacion", f"Con el método {metodo}, {nombre.lower() if es_suma else nombre} habría recibido "
         f"{formato_numero(r.estimados.iloc[0])} visitantes en enero y {formato_numero(r.estimados.iloc[-1])} en febrero "
         f"de 2026, con un error típico de validación de {r.mape:.1f} %.")
    nota("interpretacion", "Supuesto: la fracción de las llegadas internacionales que llega al lago es estable entre "
         "meses. Para los nacionales es un supuesto más débil (no pasan por migración), por eso su error es mayor. "
         "Como la telefonía no cubre ene-feb de ningún año, no hay comparación interanual directa 2025 vs 2026.")
