"""Conclusiones: la historia de los cuatro modulos en una pagina y lo que el INGUAT puede hacer con ella.

Todas las frases se arman con src/hallazgos.py, asi que cambian solas al cargar las bases reales.
"""

import streamlit as st

from src import hallazgos
from src.datos import CONFIG, corto, origenes, tabla, tabla_opcional
from src.estilo import formato_numero
from src.graficas import MES_ES
from src.ui import aviso_sinteticos, encabezado_pagina, indicadores, nota


@st.cache_data(show_spinner=False)
def _resumen(m, d, mig, ocup, oferta, boletin, frontera):
    return hallazgos.resumen(m, d, mig, ocup, oferta, CONFIG, boletin=boletin, frontera_t=frontera)


r = _resumen(tabla("mensual"), tabla("diaria"), tabla("migracion_mensual"), tabla("ocupacion"), tabla("oferta"),
             tabla_opcional("boletin_hotelero"), tabla_opcional("frontera_destino"))
dm, tp, ofe, te, fr = r["demanda"], r["temporal"], r["oferta"], r["territorio"], r["frontera"]
hay_cruce = bool(ofe) and ofe.get("captacion_ext") == ofe.get("captacion_ext")  # no NaN
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
     "contexto": f"estadía {dm['estadia_media']:.2f} días · {formato_numero(dm['extranjeros_mes'])} extranjeros/mes"},
    {"etiqueta": "2 · Festividad de mayor impacto", "valor": tp["evento_top"] or "Sin dato",
     "contexto": f"Lift {tp['lift_top']:+.0%} · fin de semana ×{tp['presion_finde']:.2f}"},
    {"etiqueta": f"3 · Noches extranjeras en hotel formal ({ventana})",
     "valor": f"{ofe['captacion_ext']:.0%}" if hay_cruce else "Sin dato",
     "contexto": f"nacionales: {ofe['captacion_nac']:.1%} · ocupación {ofe['ocupacion_oficial']:.0%}" if hay_cruce else ""},
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
        nota("observado", f"Sololá tenía **{formato_numero(ofe['plazas1'])} plazas cama** en el corte de {ofe['anio1']} "
             f"(inventario, no tendencia) y una ocupación promedio de {ofe['ocupacion_prom']:.0%} en {ofe['anio_ocupacion']}, "
             f"con pico en {MES_ES[ofe['mes_pico'] - 1]} ({ofe['ocupacion_pico']:.0%}); el mes más flojo en promedio es "
             f"{MES_ES[ofe['mes_valle_tipico'] - 1]} ({ofe['ocupacion_valle_tipico']:.0%}).")
        if hay_cruce:
            nota("observado", f"En {ventana}, los hoteles formales registran el **{ofe['captacion_ext']:.0%}** de las noches "
                 f"que la telefonía mide para los turistas extranjeros, pero solo el **{ofe['captacion_nac']:.1%}** de las de "
                 f"los nacionales (las series se mueven juntas: r = {ofe['correlacion_ext']:.2f} y {ofe['correlacion_nac']:.2f}).")
        if fr:
            nota("observado", f"Entre quienes entran al país rumbo al lago (encuesta en fronteras, ola {fr['ola']}), el "
                 f"{fr['pct_airbnb']:.0%} declara Airbnb o similar y el {fr['pct_puesto_top']:.0%} entra por "
                 f"{fr['puesto_top']} (porcentajes muestrales).")
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
    partes = [f"El Lago de Atitlán funciona como una red: {_lista(hub)} " + ("reciben" if len(hub) > 1 else "recibe") + " el volumen"]
    if larga:
        partes.append(f"{_lista(larga)} retienen las estancias largas")
    if corta:
        partes.append(f"{len(corta)} pueblos de visita corta absorben las excursiones")
    frase = ", ".join(partes[:-1]) + (" y " if len(partes) > 1 else "") + partes[-1] + "."
    frase += (f" La demanda se concentra en {tp['evento_top']} y en los fines de semana, cuando la presión sobre "
              "transporte y servicios es mayor que la que muestran los promedios mensuales.")
    nota("interpretacion", frase)

# --- Hallazgos y recomendaciones vinculadas ------------------------------------------------------------
pc = te["por_clase"]
hub_finde = pc.loc["Hub comercial", "presion_finde"] if "Hub comercial" in pc.index else float("nan")
recs = [
    ("Alta", "Gestionar los picos en las puertas de entrada",
     f"Año Nuevo eleva la afluencia {tp['lift_top']:+.0%} sobre un día regular y el fin de semana {tp['presion_finde']:.2f}×; "
     f"en los hubs ({_lista(hub)}) llega a {hub_finde:.2f}×.",
     "Reforzar transporte lacustre, seguridad y servicios municipales sábados, domingos y fin de año en los hubs; "
     "planificar con el patrón semanal de cada pueblo (módulo 4) y no con promedios mensuales."),
]
if hay_cruce:
    recs.append(("Alta", "Medir el alojamiento que hoy no se ve",
                 f"La hotelería formal capta {ofe['captacion_ext']:.0%} de las noches extranjeras y {ofe['captacion_nac']:.1%} de "
                 "las nacionales" + (f"; {fr['pct_airbnb']:.0%} de los encuestados rumbo al lago declara Airbnb." if fr else "."),
                 "Crear con las municipalidades un registro de casas de huéspedes y plataformas digitales; sin él, la ocupación "
                 "oficial describe al turismo extranjero pero no a la mayoría de las noches del lago."))
if larga:
    recs.append(("Media", "Promover estancias largas donde ya ocurren",
                 f"{_lista(larga)} retienen {pc.loc['Larga estancia', 'estadia_media']:.1f} días por turista frente a "
                 f"{pc.loc['Hub comercial', 'estadia_media']:.1f} en los hubs y atraen más extranjeros que el lago (IEE "
                 f"{pc.loc['Larga estancia', 'iee']:.2f})." + (f" El {fr['pct_puesto_top']:.0%} de los encuestados entra por "
                 f"{fr['puesto_top']}." if fr else ""),
                 "Orientar la promoción internacional de estadías largas a esos pueblos y a mercados de mayor estadía, con "
                 "información turística en la ruta terrestre de ingreso" + (f" ({fr['puesto_top']})." if fr else ".")))
if ofe:
    recs.append(("Media", "Atacar la temporada baja",
                 f"La ocupación cae a {ofe['ocupacion_valle_tipico']:.0%} en {MES_ES[ofe['mes_valle_tipico'] - 1]} (promedio "
                 "2023–2025) frente a picos sobre 90 %.",
                 f"Concentrar campañas para el mercado nacional y paquetes de fin de semana en {MES_ES[ofe['mes_valle_tipico'] - 1]}, "
                 "cuando sobra capacidad formal."))
recs.append(("Base", "Cerrar el hueco de telefonía",
             f"Enero y febrero solo se estiman (MAPE {tp['mape'][tp['metodo']]:.1f} %) y no hay comparación 2025 vs 2026.",
             "Acordar con el proveedor cobertura continua de los 12 meses y actualizar este tablero cada mes con el mismo ETL."))

with st.container(key="tile-concl-recs"):
    st.html('<div class="ot-tt">Recomendaciones para el INGUAT</div><div class="ot-ts">Cada una con la evidencia que la sostiene, '
            'la decisión que apoya y su prioridad</div>')
    filas = "".join(
        f"<tr><td style='white-space:nowrap'><b>{i}. {titulo}</b><br><span class='ot-tag'>{prioridad}</span></td>"
        f"<td>{evidencia}</td><td>{accion}</td></tr>"
        for i, (prioridad, titulo, evidencia, accion) in enumerate(recs[:5], start=1)
    )
    st.html("<table class='ot-tabla-recs'><thead><tr><th>Recomendación</th><th>Evidencia</th><th>Decisión que apoya</th></tr>"
            f"</thead><tbody>{filas}</tbody></table>")

with st.container(key="tile-concl-datos"):
    st.html('<div class="ot-tt">Datos que convendría incorporar</div><div class="ot-ts">Para responder lo que hoy queda abierto</div>')
    st.markdown(
        "- **Telefonía continua** (12 meses) y el **total del destino** entregado por el proveedor: hoy el total del lago "
        "solo puede acotarse con la suma de municipios.\n"
        "- **Pares origen-destino entre polígonos** para medir el flujo entre pueblos y confirmar si los extranjeros de "
        "San Marcos duermen en otro pueblo.\n"
        "- **Oferta y ocupación por municipio**, no solo por departamento, para cruzar capacidad y demanda pueblo por pueblo.\n"
        "- **Registro de plataformas digitales** y casas de huéspedes.\n"
        "- **Encuesta en sitio con factor de expansión** (gasto, motivo, alojamiento) y **conteos de lanchas** por muelle."
    )
