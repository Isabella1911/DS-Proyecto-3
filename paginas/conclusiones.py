"""Conclusiones: la historia de los cuatro modulos en una pagina y lo que el INGUAT puede hacer con ella.

Todas las frases se arman con src/hallazgos.py, asi que cambian solas al cargar las bases reales.
"""

import streamlit as st

from src import hallazgos
from src.datos import CONFIG, corto, origenes, tabla
from src.estilo import formato_numero
from src.graficas import MES_ES
from src.ui import aviso_sinteticos, encabezado_pagina, indicadores, nota


@st.cache_data(show_spinner=False)
def _resumen(m, d, mig, ocup, oferta):
    return hallazgos.resumen(m, d, mig, ocup, oferta, CONFIG)


r = _resumen(tabla("mensual"), tabla("diaria"), tabla("migracion_mensual"), tabla("ocupacion"), tabla("oferta"))
dm, tp, ofe, te = r["demanda"], r["temporal"], r["oferta"], r["territorio"]
v0, v1 = CONFIG["ventana_coincidente"]
ventana = f"{MES_ES[int(v0[-2:]) - 1]}–{MES_ES[int(v1[-2:]) - 1]} {v1[:4]}"


def _lista(municipios: list[str]) -> str:
    nombres = [corto(x) for x in municipios]
    return " y ".join([", ".join(nombres[:-1]), nombres[-1]]) if len(nombres) > 1 else (nombres[0] if nombres else "ninguno")


encabezado_pagina(
    "Cierre",
    "Conclusiones del observatorio",
    "La historia de los cuatro módulos en una página: cuántos visitantes llegan y de dónde, cuándo llegan, dónde "
    "duermen y qué papel juega cada pueblo. Cada cifra se recalcula con los datos cargados.",
    "Todo el lago · todos los orígenes",
)
aviso_sinteticos(origenes())

hub, larga, corta = (te["miembros"].get(c, []) for c in ["Hub comercial", "Larga estancia", "Visita corta"])
indicadores([
    {"etiqueta": "1 · Visitantes por mes (suma de municipios)", "valor": formato_numero(dm["visitantes_mes"]),
     "contexto": f"estadía {dm['estadia_media']:.2f} días · {dm['pct_extranjeros']:.0%} extranjeros"},
    {"etiqueta": "2 · Festividad de mayor impacto", "valor": tp["evento_top"] or "Sin dato",
     "contexto": f"Lift {tp['lift_top']:+.0%} · fin de semana ×{tp['presion_finde']:.2f}"},
    {"etiqueta": f"3 · Noches demandadas / plazas-noche ({ventana})",
     "valor": f"{ofe['tasa_implicita']:.0%}" if ofe.get("meses_cruce") else "Sin dato",
     "contexto": f"ocupación oficial: {ofe['ocupacion_oficial']:.0%}" if ofe.get("meses_cruce") else ""},
    {"etiqueta": "4 · Hub · larga estancia · visita corta", "valor": f"{len(hub)} · {len(larga)} · {len(corta)}",
     "contexto": f"regla y k-medias coinciden en {te['coinciden']} de {te['n']}"},
])

# --- La historia, modulo por modulo ---------------------------------------------------------------
c1, c2 = st.columns(2, gap="small")
with c1, st.container(key="tile-concl-m1"):
    st.html('<div class="ot-tt">1 · ¿Cuántos llegan y de dónde?</div><div class="ot-ts">Demanda y mercados emisores</div>')
    nota("observado", f"El lago recibe en promedio **{formato_numero(dm['visitantes_mes'])} visitantes por mes** (suma de "
         f"municipios, una cota superior). El {dm['pct_turistas']:.0%} pernocta y se queda {dm['estadia_media']:.1f} días. "
         f"**{dm['mercado_lider']}** es el primer mercado extranjero ({dm['pct_mercado_lider']:.0%}) y "
         f"**{dm['mercado_estadia']}** el de estadía más larga ({dm['estadia_mercado_max']:.1f} días).")
    st.page_link("paginas/m1_demanda.py", label="Ver módulo 1", icon=":material/groups:")
with c2, st.container(key="tile-concl-m2"):
    st.html('<div class="ot-tt">2 · ¿Cuándo llegan?</div><div class="ot-ts">Dinámica temporal y pronóstico</div>')
    est = tp["estimados"]
    nota("observado", f"**{tp['evento_top']}** eleva la afluencia {tp['lift_top']:+.0%} frente a un día regular y los fines "
         f"de semana reciben {tp['presion_finde']:.2f} veces los visitantes de un día hábil.")
    nota("estimacion", "Sin telefonía en " + " y ".join(f"{MES_ES[t.month - 1]} {t.year}" for t in est.index)
         + f", el método {tp['metodo']} estima " + " y ".join(formato_numero(v) for v in est.values)
         + f" visitantes (error de validación {tp['mape'][tp['metodo']]:.1f} %).")
    st.page_link("paginas/m2_temporal.py", label="Ver módulo 2", icon=":material/calendar_month:")

c3, c4 = st.columns(2, gap="small")
with c3, st.container(key="tile-concl-m3"):
    st.html('<div class="ot-tt">3 · ¿Dónde duermen?</div><div class="ot-ts">Oferta hotelera</div>')
    if ofe:
        crec = ofe["plazas1"] / ofe["plazas0"] - 1
        nota("observado", f"Sololá tenía **{formato_numero(ofe['plazas1'])} plazas cama** en {ofe['anio1']} ({crec:+.0%} desde "
             f"{ofe['anio0']}) y una ocupación promedio de {ofe['ocupacion_prom']:.0%} en {ofe['anio_ocupacion']}. En "
             f"{ventana}, los turistas del lago demandaron {formato_numero(ofe['noches_mes'])} noches al mes: el "
             f"{ofe['tasa_implicita']:.0%} de las plazas-noche formales (ocupación oficial: {ofe['ocupacion_oficial']:.0%}).")
        if ofe["ocupacion_prom"] < 0.7:
            nota("interpretacion", "En promedio la capacidad formal no está saturada: la presión aparece en fechas "
                 "puntuales (festividades y fines de semana del módulo 2), no todo el año.")
        else:
            nota("interpretacion", "La ocupación promedio supera el 70 %: la capacidad formal está cerca de su límite.")
    st.page_link("paginas/m3_oferta.py", label="Ver módulo 3", icon=":material/hotel:")
with c4, st.container(key="tile-concl-m4"):
    st.html('<div class="ot-tt">4 · ¿Qué papel juega cada pueblo?</div><div class="ot-ts">Red de municipios (reto del grupo)</div>')
    nota("observado", f"**Hub comercial:** {_lista(hub)}. **Larga estancia:** {_lista(larga)}. "
         f"**Visita corta:** {_lista(corta)}.")
    pc = te["por_clase"]
    if {"Hub comercial", "Larga estancia"} <= set(pc.index):
        nota("observado", f"Un turista de larga estancia se queda {pc.loc['Larga estancia', 'estadia_media']:.1f} días frente a "
             f"{pc.loc['Hub comercial', 'estadia_media']:.1f} en el hub. Regla y k-medias coinciden en {te['coinciden']} "
             f"de {te['n']} municipios y k-medias conserva la clase del {te['estabilidad']:.0%} al quitar un pueblo.")
    st.page_link("paginas/m4_municipios.py", label="Ver módulo 4", icon=":material/hub:")

# --- Sintesis y recomendaciones -------------------------------------------------------------------
with st.container(key="tile-concl-historia"):
    st.html('<div class="ot-tt">La historia en una frase</div>')
    partes = [f"El Lago de Atitlán funciona como una red: {_lista(hub)} recibe el volumen"]
    if larga:
        partes.append(f"{_lista(larga)} retienen las estancias largas")
    if corta:
        partes.append(f"{len(corta)} pueblos de visita corta absorben las excursiones")
    frase = ", ".join(partes[:-1]) + (" y " if len(partes) > 1 else "") + partes[-1] + "."
    frase += (f" La demanda se concentra en {tp['evento_top']} y en los fines de semana, cuando la presión sobre "
              "transporte y servicios es mayor que la que muestran los promedios mensuales.")
    nota("interpretacion", frase)

recs = []
if tp["presion_finde"] > 1.1 or tp["lift_top"] > 0.2:
    recs.append(f"**Gestión de flujo en picos.** Reforzar transporte lacustre, seguridad y servicios en {tp['evento_top']} y "
                "los fines de semana" + (f", con prioridad en los pueblos de visita corta ({_lista(corta)})." if corta else "."))
if larga:
    recs.append(f"**Promoción de estancias largas.** Dirigir la promoción internacional a {dm['mercado_estadia']} y mercados "
                f"parecidos, con producto en {_lista(larga)}: cada turista genera más noches que en el hub.")
recs.append("**Alojamiento no formal.** Incorporar un registro de plataformas digitales (Airbnb y similares) para medir las "
            "noches que la hotelería formal no capta; hoy son universos distintos y no se pueden sumar.")
alta = any(v > 1 for v in tp["perfil_meses"].values())
recs.append("**Cerrar el hueco de telefonía.** Acordar con el proveedor la cobertura de enero y febrero: "
            + ("son meses de llegadas internacionales sobre el promedio y " if alta else "")
            + "hoy solo se estiman, lo que impide comparar 2025 contra 2026.")
recs.append("**Monitoreo continuo.** Actualizar el tablero cada mes con el mismo ETL y revisar la página de Calidad antes de "
            "publicar cifras.")

c5, c6 = st.columns([1.3, 1], gap="small")
with c5, st.container(key="tile-concl-recs"):
    st.html('<div class="ot-tt">Recomendaciones para el INGUAT</div><div class="ot-ts">Derivadas de las cifras anteriores</div>')
    st.markdown("\n".join(f"{i}. {t}" for i, t in enumerate(recs[:5], start=1)))
with c6, st.container(key="tile-concl-datos"):
    st.html('<div class="ot-tt">Datos que convendría incorporar</div><div class="ot-ts">Para responder lo que hoy queda abierto</div>')
    st.markdown(
        "- **BD complementaria y boletines de ocupación (PDF)**: fuentes opcionales de la asignación, aún no integradas.\n"
        "- **Oferta por municipio**, no solo por departamento, para cruzar capacidad y demanda pueblo por pueblo.\n"
        "- **Registro de plataformas digitales** de alojamiento.\n"
        "- **Encuestas con factor de expansión** (gasto, motivo de viaje) para pasar de visitantes a impacto económico.\n"
        "- **Conteos de transporte lacustre** para medir el flujo entre pueblos."
    )
