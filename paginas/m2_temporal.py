"""Modulo 2 · Dinamica temporal y eventos.

Vista enlazada: un clic en una festividad de la grafica de Lift resalta sus dias en la serie diaria.
La seccion de estimacion de ene-feb 2026 se retiro de esta pagina; el calculo sigue en src/pronostico.py.
"""

from __future__ import annotations

import streamlit as st

from src import indicadores as ind
from src.datos import corto, origenes, selector_ambito, tabla
from src.estilo import formato_numero
from src.graficas import fig_lift, fig_patron_semanal, fig_serie_diaria
from src.ui import aviso_sinteticos, barra_filtros, encabezado_pagina, indicadores, mosaico, sin_datos

d_todo = tabla("diaria")

encabezado_pagina(
    "Módulo 2 · Temporalidad",
    "Dinámica temporal y eventos",
    tema="m2_temporal",
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
with mosaico(
    "m2-semana", "Patrón semanal", "Índice de visitantes por día de la semana (promedio = 100)", "observado",
    "**¿Cuánta presión ponen los fines de semana?**\n\nPromedio de visitantes de cada día de la semana dividido entre "
    "el promedio de los siete días. Por defecto se excluyen los días con festividad para que un feriado no infle el "
    "día de la semana en que cayó.",
):
    solo_reg = st.toggle("Solo días regulares (sin festividades)", value=True, key="m2_solo_reg")
    patron = patron_reg if solo_reg else ind.patron_semanal(diaria, solo_regulares=False)
    st.plotly_chart(fig_patron_semanal(patron), key="m2_semana", width="stretch")
