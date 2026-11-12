"""Modulo 2 · Dinamica temporal, eventos y pronostico predictivo.

Vista enlazada: un clic en una festividad de la grafica de Lift resalta sus dias en la serie diaria.
"""

from __future__ import annotations

import streamlit as st

from src import indicadores as ind
from src import pronostico as pr
from src.datos import CONFIG, corto, origenes, selector_ambito, tabla
from src.estilo import formato_numero

MESES_LARGOS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
                "octubre", "noviembre", "diciembre"]
from src.graficas import (
    MES_ES, fig_consistencia_diaria, fig_lift, fig_mensual_estimada, fig_patron_semanal, fig_perfil_estacional, fig_serie_diaria, fig_validacion,
)
from src.ui import aviso_sinteticos, barra_filtros, encabezado_pagina, grafica, indicadores, mosaico, nota, siguiente, sin_datos

d_todo = tabla("diaria")
m_todo = tabla("mensual")
mig = tabla("migracion_mensual")
faltantes = CONFIG["estimacion"]["meses_sin_cobertura"]
anios_perfil = CONFIG["estimacion"]["anios_perfil"]

encabezado_pagina(
    "Módulo 2. Dinámica temporal",
    "Dinámica temporal, festividades y estimación",
    "Afluencia diaria, efecto de las festividades, patrón semanal y estimación de los meses sin cobertura de "
    "telefonía. Toda cifra estimada se presenta en violeta, con línea discontinua y rotulada como estimación.",
    "Fuente: telefonía móvil, bases diaria y mensual<br>Meses estimados: <b>enero y febrero de 2026</b>",
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
st.html('<div class="ot-sec">Serie diaria y efecto de las festividades</div>')
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
    {"etiqueta": f"Lift de {ev_sel}", "valor": f"{fila[col_lift]:+.0%}", "contexto": f"Cálculo {tipo_lift.lower()}; {int(fila['dias'])} días observados"},
    {"etiqueta": "Presencia media en un día de la festividad", "valor": formato_numero(fila["promedio_dia"]),
     "contexto": f"Día regular promedio: {formato_numero(lift.attrs['base_regular'])}"},
    {"etiqueta": "Presión de fin de semana", "valor": f"{presion:.2f}×", "contexto": "Sábado y domingo frente a lunes a viernes"},
    {"etiqueta": "Día más concurrido", "valor": patron_reg["promedio"].idxmax(), "contexto": f"Índice {patron_reg['indice'].max():.0f} (promedio semanal = 100)"},
])

c1, c2 = st.columns([1.7, 1], gap="small")
with c1, mosaico(
    "m2-diaria", f"Presencia diaria de visitantes, {nombre.lower() if es_suma else nombre}",
    "Personas presentes por día. Ámbar: días con festividad; azul: festividad seleccionada",
    "observado",
    "**¿Cómo se mueve la afluencia día a día?**\n\nLa base diaria mide **presencia por día**: la misma persona aparece "
    "en cada día que pasa en el destino, así que estos valores **no se suman** para obtener los visitantes del mes. "
    "La franja gris marca los días sin cobertura de telefonía (sin dato, no cero). Use la barra inferior para acercarse.",
    filtro=ev_sel,
):
    grafica(fig_serie_diaria(diaria, ev_sel), "m2_diaria")
with c2, mosaico(
    "m2-lift", "Efecto de las festividades sobre la afluencia", f"Lift {tipo_lift.lower()} frente al día regular promedio", "observado",
    "**¿Cuánto sube la afluencia en cada festividad?**\n\n"
    "Lift = (promedio de visitantes en los días del evento ÷ promedio de un día regular) − 1. "
    "Un +50 % significa que un día de esa festividad recibe la mitad más de visitantes que un día regular. "
    "El ajustado por día de semana evita atribuir al feriado el efecto de caer en sábado o domingo.",
    enlazada=True,
):
    grafica(fig_lift(lift, col_lift, ev_sel), "m2_lift_chart", enlazada=True)

# --- Patron semanal -------------------------------------------------------------------------------
c3, c4 = st.columns([1, 1], gap="small")
with c3, mosaico(
    "m2-semana", "Afluencia por día de la semana", "Índice de presencia diaria, promedio semanal = 100", "observado",
    "**¿Cuánta presión ponen los fines de semana?**\n\nPromedio de visitantes de cada día de la semana dividido entre "
    "el promedio de los siete días. Por defecto se excluyen los días con festividad para que un feriado no infle el "
    "día de la semana en que cayó.",
):
    solo_reg = st.toggle("Solo días regulares (sin festividades)", value=True, key="m2_solo_reg")
    patron = patron_reg if solo_reg else ind.patron_semanal(diaria, solo_regulares=False)
    grafica(fig_patron_semanal(patron), "m2_semana")
with c4, st.container(key="tile-m2-lectura"):
    st.html('<div class="ot-tt">Resultados</div><div class="ot-ts">Festividades y patrón semanal</div>')
    top_ev = lift[col_lift].idxmax()
    nota("observado", f"{top_ev} es la festividad de mayor impacto en {nombre.lower() if es_suma else nombre}, con "
         f"{lift.loc[top_ev, col_lift]:+.0%} frente a un día regular. Los sábados y domingos reciben "
         f"{presion:.2f} veces la presencia de un día hábil.")
    negativos = lift.index[lift[col_lift] < 0].tolist()
    if negativos:
        nota("interpretacion", f"{' y '.join(negativos)} no atraen más visitantes que un día regular. El feriado, por sí "
             "solo, no moviliza demanda hacia el lago; una explicación posible es que se trate de asuetos de un día que "
             "no forman fin de semana largo.")
    if es_suma:
        nota("interpretacion", "En la suma de municipios, un visitante presente en dos municipios el mismo día se cuenta "
             "dos veces. El Lift es un cociente y se ve poco afectado; los volúmenes son una cota superior.")

# --- Estimacion de ene-feb 2026 y validacion --------------------------------------------------------
st.html('<div class="ot-sec">Estimación de los meses sin cobertura de telefonía</div>')
m = ind.filtrar(m_todo, ambito, origen)
obs = ind.serie_mensual(m)
obs = obs.reindex(ind.calendario(obs.index, faltantes))
resultados = {k: pr.estimar(obs, mig, faltantes, anios_perfil, k) for k in pr.METODOS}
mejor = min(resultados, key=lambda k: resultados[k].mape)
metodo = st.segmented_control(
    "Método de estimación", list(pr.METODOS), default=mejor, format_func=lambda k: f"Método {k}: {pr.METODOS[k].lower()}", key="m2_metodo",
) or mejor
r = resultados[metodo]

indicadores([
    {"etiqueta": f"Estimación {MES_ES[r.estimados.index[0].month - 1]} {r.estimados.index[0].year}",
     "valor": formato_numero(r.estimados.iloc[0]), "contexto": "Visitantes únicos del mes"},
    {"etiqueta": f"Estimación {MES_ES[r.estimados.index[-1].month - 1]} {r.estimados.index[-1].year}",
     "valor": formato_numero(r.estimados.iloc[-1]), "contexto": "Visitantes únicos del mes"},
    {"etiqueta": "Error porcentual absoluto medio (MAPE)", "valor": f"{r.mape:.1f}%", "contexto": f"Validación con {len(r.validacion)} meses observados"},
    {"etiqueta": "MAE y RMSE", "valor": f"{formato_numero(r.mae)} y {formato_numero(r.rmse)}", "contexto": "Visitantes por mes"},
])

c5, c6 = st.columns([1.5, 1], gap="small")
with c5, mosaico(
    "m2-estimacion", f"Visitantes únicos por mes, {nombre.lower() if es_suma else nombre}",
    "Dato observado (negro) y estimación de enero y febrero de 2026 (violeta, línea discontinua)", "estimacion",
    "**¿Cuántos visitantes hubo en enero y febrero de 2026?**\n\nLa telefonía no cubre esos meses. Se estiman con la base "
    "de migración:\n\n"
    "- **A. Factor de reparto × migración del mes:** F = Σ visitantes del destino / Σ llegadas internacionales en los "
    "meses observados; estimación = F × llegadas del mes faltante.\n"
    "- **B. Perfil estacional × nivel:** índice estacional de las llegadas (promedio de "
    f"{anios_perfil[0]}–{anios_perfil[-1]}) escalado al nivel observado del destino.\n\n"
    "Por defecto se muestra el método con menor MAPE en la validación.",
):
    grafica(fig_mensual_estimada(obs, r.estimados), "m2_estimacion")
    st.caption("Las estimaciones no se incorporan a los indicadores observados del módulo 1.")
with c6, mosaico(
    "m2-validacion", "Validación cruzada de la estimación", "Cada mes observado se estima sin utilizar su propio dato",
    "estimacion",
    "**¿Qué tan confiable es la estimación?**\n\nPara cada mes observado se recalcula el factor **sin ese mes** y se "
    "estima su valor; la diferencia con lo observado da el error. MAPE = promedio de |error| / observado; "
    "MAE = promedio de |error|; RMSE = raíz del promedio del error al cuadrado.",
):
    grafica(fig_validacion(r.validacion), "m2_validacion")
    comp = {pr.METODOS[k].split(" ×")[0] + f" ({k})": f"{v.mape:.1f}%" for k, v in resultados.items()}
    st.caption("MAPE por método: " + "; ".join(f"{a}, {b}" for a, b in comp.items()) + ".")

perfil = pr.perfil_estacional(mig, anios_perfil)
meses_est = [int(p[-2:]) for p in faltantes]
i0, i1 = (float(perfil.get(x, float("nan"))) for x in (meses_est[0], meses_est[-1]))
lectura_perfil = (
    f"Explica la forma de la estimación: {MES_ES[meses_est[0] - 1]} tiene un índice de {i0:.2f} y "
    f"{MES_ES[meses_est[-1] - 1]} de {i1:.2f}, así que el método B estima "
    + ("más visitantes en el primero." if i0 > i1 else "más visitantes en el segundo." if i1 > i0 else "lo mismo en ambos.")
)
c7, c8 = st.columns([1, 1.5], gap="small")
with c7, mosaico(
    "m2-perfil", "Perfil estacional de las llegadas internacionales",
    f"Índice mensual, flujo migratorio {anios_perfil[0]}–{anios_perfil[-1]}. Violeta: meses estimados", "observado",
    "**Visualización complementaria.** Índice de cada mes frente al promedio de su año (1 = mes promedio). "
    + lectura_perfil,
):
    grafica(fig_perfil_estacional(perfil, meses_est), "m2_perfil")
with c8, st.container(key="tile-m2-lectura-est"):
    st.html('<div class="ot-tt">Supuestos y alcance de la estimación</div><div class="ot-ts">Método seleccionado por menor error de validación</div>')
    nota("estimacion", f"Con el método {metodo}, {nombre.lower() if es_suma else nombre} habría recibido "
         f"{formato_numero(r.estimados.iloc[0])} visitantes en enero y {formato_numero(r.estimados.iloc[-1])} en febrero "
         f"de 2026, con un error porcentual medio de validación de {r.mape:.1f}%.")
    nota("interpretacion", "Supuesto principal: la proporción de las llegadas internacionales que visita el lago se "
         "mantiene estable entre meses. Para los visitantes nacionales el supuesto es más débil, porque no se registran "
         "en migración; el filtro de origen permite comparar el error por segmento. Al no existir cobertura de enero y "
         "febrero en ningún año, no es posible una comparación interanual directa entre 2025 y 2026.")
    if r.mape > 20:
        nota("interpretacion", f"El error de validación ({r.mape:.0f}%) es elevado: la estimación debe leerse como orden "
             "de magnitud y no como cifra precisa.")

# --- Verificacion con la base diaria -------------------------------------------------------------
cons = pr.consistencia_diaria(obs, diaria, r.estimados)
c9, c10 = st.columns([1.5, 1], gap="small")
with c9, mosaico(
    "m2-consistencia", "Verificación de la estimación con la base diaria",
    "Presencia diaria media por mes. Franja gris: rango observado; violeta: valor implícito en la estimación", "estimacion",
    "**¿La estimación mensual es coherente con lo que se ve día a día?**\n\nLa guía pide usar la base diaria para "
    "verificar el comportamiento dentro del mes (no para proyectarla). Se calcula la **rotación** = visitantes únicos "
    "del mes / presencia diaria media en los meses con ambas bases completas. Si es estable, la estimación implica una "
    "presencia diaria = estimación / rotación media, que debe caer en el rango observado. Ninguna base se suma.",
):
    if cons.attrs.get("rotacion_media"):
        grafica(fig_consistencia_diaria(cons), "m2_consistencia")
    else:
        sin_datos("No hay meses completos con ambas bases para verificar la estimación.")
with c10, st.container(key="tile-m2-lectura-diaria"):
    st.html('<div class="ot-tt">Resultado de la verificación</div><div class="ot-ts">Base diaria y feriados sin cobertura</div>')
    if cons.attrs.get("rotacion_media"):
        lo, hi = cons.attrs["rango"]
        imp = cons[cons["tipo"] == "Estimación"]["presencia_media"]
        dentro = imp.between(lo * 0.95, hi * 1.05).all()
        nota("observado", f"La rotación mensual es estable: {cons.attrs['rotacion_media']:.1f} visitantes únicos por cada "
             f"persona presente en un día promedio, con una variación de {cons.attrs['rotacion_cv']:.0%} entre meses.")
        nota("estimacion", "Presencia diaria implícita en la estimación: " + " y ".join(
             f"{formato_numero(v)} en {MESES_LARGOS[t.month - 1]}" for t, v in imp.items())
             + f", frente a un rango observado de {formato_numero(lo)} a {formato_numero(hi)}. "
             + ("La estimación es consistente con el comportamiento diario de los meses observados." if dentro else
                "El valor queda fuera del rango observado; el método debe revisarse antes de utilizar la estimación."))
    nota("interpretacion", "La base diaria no cubre enero ni febrero de 2026. Los feriados de esos meses (1 de enero) "
         "se declaran ausentes y no se estiman; la serie diaria no se proyecta.")

# --- Hilo hacia el siguiente modulo --------------------------------------------------------------
siguiente(
    "paginas/m3_oferta.py", "Módulo 3. Oferta hotelera",
    "Oferta de alojamiento: capacidad y ocupación hotelera de Sololá, y su contraste con las noches registradas "
    "por la telefonía.",
    ":material/hotel:",
)
