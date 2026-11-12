"""Conclusiones: la historia de los cuatro modulos en una pagina y lo que el INGUAT puede hacer con ella.

Todas las frases se arman con src/hallazgos.py, asi que cambian solas al cargar las bases reales.
"""

import streamlit as st

from src import hallazgos
from src.datos import CONFIG, corto, origenes, tabla, tabla_opcional
from src.estilo import formato_numero
from src.graficas import MES_ES

MESES_LARGOS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
                "noviembre", "diciembre"]
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
    "Conclusiones",
    "Conclusiones y recomendaciones",
    "Síntesis de los resultados de los cuatro módulos y recomendaciones para la gestión del destino. Las cifras se "
    "recalculan con los datos cargados.",
    "Ámbito: lago completo, todos los orígenes<br>Telefonía: septiembre de 2025 a agosto de 2026",
)
aviso_sinteticos(origenes())

hub, larga, corta = (te["miembros"].get(c, []) for c in ["Hub comercial", "Larga estancia", "Visita corta"])
indicadores([
    {"etiqueta": "Visitantes por mes, suma de municipios", "valor": formato_numero(dm["visitantes_mes"]),
     "contexto": f"Estadía media de {dm['estadia_media']:.2f} días"},
    {"etiqueta": "Festividad de mayor impacto", "valor": tp["evento_top"] or "Sin dato",
     "contexto": f"Lift de {tp['lift_top']:+.0%}; fin de semana {tp['presion_finde']:.2f} veces un día hábil"},
    {"etiqueta": f"Noches extranjeras en hotelería formal, {ventana}",
     "valor": f"{ofe['captacion_ext']:.0%}" if hay_cruce else "Sin dato",
     "contexto": f"Nacionales: {ofe['captacion_nac']:.1%}" if hay_cruce else ""},
    {"etiqueta": "Hubs, larga estancia y visita corta", "valor": f"{len(hub)}, {len(larga)} y {len(corta)}",
     "contexto": f"Municipios por clase; métodos coinciden en {te['coinciden']} de {te['n']}"},
])

c1, c2 = st.columns(2, gap="small")
with c1, st.container(key="tile-concl-m1"):
    st.html('<div class="ot-tt">1. Demanda y mercados emisores</div><div class="ot-ts">Módulo 1</div>')
    nota("observado", f"El lago recibe en promedio {formato_numero(dm['visitantes_mes'])} visitantes por mes (suma de "
         f"municipios, cota superior). El {dm['pct_turistas']:.0%} pernocta, con una estadía media de "
         f"{dm['estadia_media']:.1f} días. {dm['mercado_lider']} es el primer mercado extranjero "
         f"({dm['pct_mercado_lider']:.0%}) y {dm['mercado_estadia']} el de estadía más larga ({dm['estadia_mercado_max']:.1f} días).")
    st.page_link("paginas/m1_demanda.py", label="Ir al módulo 1", icon=":material/groups:")
with c2, st.container(key="tile-concl-m2"):
    st.html('<div class="ot-tt">2. Dinámica temporal y estimación</div><div class="ot-ts">Módulo 2</div>')
    est = tp["estimados"]
    nota("observado", f"{tp['evento_top']} eleva la afluencia {tp['lift_top']:+.0%} frente a un día regular; los fines de "
         f"semana reciben {tp['presion_finde']:.2f} veces la presencia de un día hábil.")
    nota("estimacion", "Para " + " y ".join(f"{MESES_LARGOS[t.month - 1]} de {t.year}" for t in est.index)
         + f", meses sin cobertura de telefonía, el método {tp['metodo']} estima "
         + " y ".join(formato_numero(v) for v in est.values)
         + f" visitantes, con un error de validación de {tp['mape'][tp['metodo']]:.1f}%.")
    st.page_link("paginas/m2_temporal.py", label="Ir al módulo 2", icon=":material/calendar_month:")

c3, c4 = st.columns(2, gap="small")
with c3, st.container(key="tile-concl-m3"):
    st.html('<div class="ot-tt">3. Oferta de alojamiento</div><div class="ot-ts">Módulo 3</div>')
    if ofe:
        nota("observado", f"Sololá contaba con {formato_numero(ofe['plazas1'])} plazas cama en el corte de {ofe['anio1']}. "
             f"La ocupación promedio de {ofe['anio_ocupacion']} fue de {ofe['ocupacion_prom']:.0%}, con un máximo en "
             f"{MESES_LARGOS[ofe['mes_pico'] - 1]} ({ofe['ocupacion_pico']:.0%}); el mes de menor ocupación en promedio "
             f"es {MESES_LARGOS[ofe['mes_valle_tipico'] - 1]} ({ofe['ocupacion_valle_tipico']:.0%}).")
        if hay_cruce:
            nota("observado", f"Entre septiembre y diciembre de 2025, la hotelería formal registró el {ofe['captacion_ext']:.0%} "
                 f"de las noches que la telefonía mide para los turistas extranjeros y el {ofe['captacion_nac']:.1%} de las "
                 f"de los nacionales. Ambas fuentes evolucionan en la misma dirección (r = {ofe['correlacion_ext']:.2f} y "
                 f"{ofe['correlacion_nac']:.2f}).")
        if fr:
            nota("observado", f"Entre los viajeros que ingresan al país con destino al lago (ola {fr['ola']}), el "
                 f"{fr['pct_airbnb']:.0%} declara alojarse en Airbnb o similar y el {fr['pct_puesto_top']:.0%} ingresa por "
                 f"{fr['puesto_top']}. Porcentajes muestrales.")
    st.page_link("paginas/m3_oferta.py", label="Ir al módulo 3", icon=":material/hotel:")
with c4, st.container(key="tile-concl-m4"):
    st.html('<div class="ot-tt">4. Red de municipios</div><div class="ot-ts">Módulo 4, análisis especializado</div>')
    nota("observado", f"Hubs: {_lista(hub)}. Larga estancia: {_lista(larga)}. Visita corta: {_lista(corta)}.")
    pc = te["por_clase"]
    if {"Hub comercial", "Larga estancia"} <= set(pc.index):
        nota("observado", f"Un turista de larga estancia permanece {pc.loc['Larga estancia', 'estadia_media']:.1f} días, "
             f"frente a {pc.loc['Hub comercial', 'estadia_media']:.1f} en los hubs. La regla y k-medias coinciden en "
             f"{te['coinciden']} de {te['n']} municipios; k-medias conserva la clase del {te['estabilidad']:.0%} al excluir "
             "un municipio.")
    st.page_link("paginas/m4_municipios.py", label="Ir al módulo 4", icon=":material/hub:")

with st.container(key="tile-concl-historia"):
    st.html('<div class="ot-tt">Síntesis</div>')
    partes = [f"El Lago de Atitlán funciona como una red: {_lista(hub)} " + ("concentran" if len(hub) > 1 else "concentra")
              + " el flujo de visitantes"]
    if larga:
        partes.append(f"{_lista(larga)} retienen las estadías más largas")
    if corta:
        partes.append(f"otros {len(corta)} municipios reciben sobre todo visitas cortas")
    frase = ", ".join(partes[:-1]) + (" y " if len(partes) > 1 else "") + partes[-1] + "."
    frase += (f" La demanda se concentra en {tp['evento_top']} y en los fines de semana, cuando la presión sobre "
              "transporte y servicios supera la que reflejan los promedios mensuales.")
    nota("interpretacion", frase)

# --- Hallazgos y recomendaciones vinculadas ------------------------------------------------------------
pc = te["por_clase"]
hub_finde = pc.loc["Hub comercial", "presion_finde"] if "Hub comercial" in pc.index else float("nan")
recs = [
    ("Alta", "Gestión de picos en las puertas de entrada",
     f"{tp['evento_top']} eleva la afluencia {tp['lift_top']:+.0%} sobre un día regular. El fin de semana recibe "
     f"{tp['presion_finde']:.2f} veces la presencia de un día hábil, y {hub_finde:.2f} veces en los hubs ({_lista(hub)}).",
     "Reforzar transporte lacustre, seguridad y servicios municipales en sábados, domingos y fin de año en los hubs, "
     "con base en el patrón semanal de cada municipio y no en promedios mensuales."),
]
if hay_cruce:
    recs.append(("Alta", "Registro del alojamiento no formal",
                 f"La hotelería formal registra el {ofe['captacion_ext']:.0%} de las noches de turistas extranjeros y el "
                 f"{ofe['captacion_nac']:.1%} de las de nacionales."
                 + (f" El {fr['pct_airbnb']:.0%} de los encuestados con destino al lago declara alojarse en Airbnb." if fr else ""),
                 "Establecer con las municipalidades un registro de casas de huéspedes y plataformas digitales. Mientras no "
                 "exista, la ocupación oficial debe leerse como indicador del turismo extranjero."))
if larga:
    recs.append(("Media", "Promoción de estadías largas donde ya ocurren",
                 f"{_lista(larga)} registran {pc.loc['Larga estancia', 'estadia_media']:.1f} días por turista frente a "
                 f"{pc.loc['Hub comercial', 'estadia_media']:.1f} en los hubs, con especialización extranjera de "
                 f"{pc.loc['Larga estancia', 'iee']:.2f}."
                 + (f" El {fr['pct_puesto_top']:.0%} de los encuestados ingresa por {fr['puesto_top']}." if fr else ""),
                 "Dirigir la promoción internacional de estadías largas a esos municipios y a los mercados de mayor estadía, "
                 "con información turística en la ruta terrestre de ingreso"
                 + (f" ({fr['puesto_top']})." if fr else ".")))
if ofe:
    recs.append(("Media", "Temporada baja",
                 f"La ocupación hotelera desciende a {ofe['ocupacion_valle_tipico']:.0%} en "
                 f"{MESES_LARGOS[ofe['mes_valle_tipico'] - 1]} (promedio 2023 a 2025), frente a máximos superiores al 90%.",
                 f"Concentrar campañas para el mercado nacional y paquetes de fin de semana en "
                 f"{MESES_LARGOS[ofe['mes_valle_tipico'] - 1]}, cuando existe capacidad formal disponible."))
recs.append(("Base", "Cobertura continua de telefonía",
             f"Enero y febrero solo pueden estimarse (MAPE de {tp['mape'][tp['metodo']]:.1f}%) y no existe comparación "
             "interanual entre 2025 y 2026.",
             "Acordar con el proveedor la cobertura de los doce meses y la entrega del total del destino; actualizar el "
             "tablero cada mes con el mismo proceso de datos."))

with st.container(key="tile-concl-recs"):
    st.html('<div class="ot-tt">Recomendaciones para el INGUAT</div><div class="ot-ts">Evidencia, decisión que apoya y '
            'prioridad de cada recomendación</div>')
    filas = "".join(
        f"<tr><td><b>{i}. {titulo}</b><br><span class='ot-tag'>Prioridad {prioridad.lower()}</span></td>"
        f"<td>{evidencia}</td><td>{accion}</td></tr>"
        for i, (prioridad, titulo, evidencia, accion) in enumerate(recs[:5], start=1)
    )
    st.html("<table class='ot-tabla-recs'><thead><tr><th>Recomendación</th><th>Evidencia</th><th>Decisión que apoya</th></tr>"
            f"</thead><tbody>{filas}</tbody></table>")

with st.container(key="tile-concl-datos"):
    st.html('<div class="ot-tt">Información adicional requerida</div><div class="ot-ts">Para resolver las preguntas que quedan abiertas</div>')
    st.markdown(
        "- Telefonía continua de doce meses y total del destino entregado por el proveedor; hoy el total del lago solo "
        "puede acotarse con la suma de municipios.\n"
        "- Pares origen-destino entre polígonos, para medir el flujo entre municipios y verificar dónde pernoctan los "
        "visitantes extranjeros de San Marcos La Laguna.\n"
        "- Oferta y ocupación hotelera por municipio, para contrastar capacidad y demanda en cada localidad.\n"
        "- Registro de plataformas digitales y casas de huéspedes.\n"
        "- Encuesta en sitio con factor de expansión (gasto, motivo de viaje, alojamiento) y conteos de pasajeros de "
        "transporte lacustre por muelle."
    )
