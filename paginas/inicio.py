"""Inicio: que es el observatorio, cifras clave y acceso a los cuatro modulos."""

import streamlit as st

from src import indicadores as ind
from src.datos import corto, origenes, tabla
from src.estilo import formato_numero
from src.graficas import MES_ES
from src.ui import aviso_sinteticos, encabezado_pagina, indicadores, nota

m = tabla("mensual")
d = tabla("diaria")
k = ind.kpis_demanda(m)
perfil = ind.por_municipio(m)
lift = ind.lift_eventos(ind.serie_diaria(d))
p0, p1 = m["periodo"].min(), m["periodo"].max()

encabezado_pagina(
    "Observatorio de Inteligencia Turística · Grupo 3",
    "Lago de Atitlán, Sololá",
    "Un observatorio no es un reporte estático: monitorea de forma continua la demanda, la oferta y la presión sobre "
    "el territorio para que el INGUAT y los gestores locales decidan con evidencia. Este tablero sigue la estructura "
    "de cuatro módulos y el reto propio del destino: la red de 10 municipios ribereños.",
    f"Telefonía {MES_ES[p0.month - 1]} {p0.year} – {MES_ES[p1.month - 1]} {p1.year}<br><b>10 municipios</b>",
)
aviso_sinteticos(origenes())

indicadores([
    {"etiqueta": "Visitantes por mes (suma de municipios)", "valor": formato_numero(k["visitantes_mes"]),
     "contexto": "cota superior: un visitante puede contar en varios pueblos", "serie": k["serie_visitantes"]},
    {"etiqueta": "Estadía media ponderada", "valor": f"{k['estadia_media']:.2f} días", "contexto": "turistas con pernocta",
     "serie": k["serie_estadia"]},
    {"etiqueta": "Visitantes extranjeros", "valor": f"{k['pct_extranjeros']:.0%}", "contexto": "del total de visitantes"},
    {"etiqueta": "Festividad de mayor impacto", "valor": lift["lift"].idxmax() if len(lift) else "Sin dato",
     "contexto": f"Lift {lift['lift'].max():+.0%} frente a un día regular" if len(lift) else "sin festividades en la base diaria"},
])

c1, c2 = st.columns([1, 1], gap="small")
with c1, st.container(key="tile-inicio-lectura"):
    st.html('<div class="ot-tt">Lo más importante</div><div class="ot-ts">Lectura rápida de los datos actuales</div>')
    nota("observado", f"**{corto(perfil['visitantes_mes'].idxmax())}** es la principal puerta de entrada del lago y "
         f"**{corto(perfil['estadia_media'].idxmax())}** el municipio con estadías más largas "
         f"({perfil['estadia_media'].max():.1f} días).")
    nota("estimacion", "Enero y febrero de 2026 no tienen cobertura de telefonía: se estiman con la base de migración "
         "(módulo 2) y se muestran siempre como 'Estimación'.")
with c2, st.container(key="tile-inicio-reglas"):
    st.html('<div class="ot-tt">Reglas que respeta el tablero</div><div class="ot-ts">Según la guía metodológica</div>')
    st.markdown(
        "- Un mes sin dato es **'Sin dato'**, nunca cero.\n"
        "- La estadía media **se pondera** (Σ días-persona / Σ visitantes); nunca se promedia la permanencia.\n"
        "- La base diaria **no se suma** para obtener el mes.\n"
        "- Los municipios **no se suman** como total del lago sin advertirlo.\n"
        "- Personas y porcentajes nunca comparten eje."
    )

ACCESOS = [
    ("paginas/m1_demanda.py", "1 · Demanda y mercados", "KPIs, turista vs. excursionista y top 10 de nacionalidades.", ":material/groups:"),
    ("paginas/m2_temporal.py", "2 · Dinámica temporal", "Serie diaria, Lift de festividades, patrón semanal y estimación ene-feb 2026.", ":material/calendar_month:"),
    ("paginas/m3_oferta.py", "3 · Oferta hotelera", "Capacidad, ocupación, noches demandadas vs. plazas y reparto entre municipios.", ":material/hotel:"),
    ("paginas/m4_municipios.py", "4 · Red de municipios", "Hubs, larga estancia y visita corta: cuadrante, k-medias y dinámica de cada pueblo.", ":material/hub:"),
    ("paginas/conclusiones.py", "Conclusiones", "La historia de los cuatro módulos y recomendaciones para el INGUAT.", ":material/flag:"),
]
cols = st.columns(len(ACCESOS), gap="small")
for i, (col, (pagina, titulo, desc, icono)) in enumerate(zip(cols, ACCESOS)):
    with col, st.container(key=f"acceso-{i}"):
        st.html(f'<div class="ot-acc-t">{titulo}</div><div class="ot-acc-d">{desc}</div>')
        st.page_link(pagina, label="Abrir", icon=icono)
