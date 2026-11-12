"""Inicio: que es el observatorio, cifras clave y acceso a los cuatro modulos."""

import pandas as pd
import streamlit as st

from src import indicadores as ind
from src import oferta as of
from src.datos import CONFIG, cobertura, corto, origenes, tabla, tabla_opcional
from src.estilo import formato_numero
from src.graficas import MES_ES, fig_cobertura
from src.normalizar import departamento
from src.ui import aviso_sinteticos, encabezado_pagina, grafica, indicadores, mosaico, nota

m = tabla("mensual")
d = tabla("diaria")
k = ind.kpis_demanda(m)
perfil = ind.por_municipio(m)
lift = ind.lift_eventos(ind.serie_diaria(d))
p0, p1 = m["periodo"].min(), m["periodo"].max()
_ocup = tabla("ocupacion")
_depto = departamento(CONFIG["destino"]["departamento"])
_v0, _v1 = (pd.Timestamp(x + "-01") for x in CONFIG["ventana_coincidente"])
res_cruce = of.resumen_cruce(of.cruce_ventana(m, tabla_opcional("boletin_hotelero"),
                                              _ocup[_ocup["departamento"] == _depto].set_index("periodo")["ocupacion"], (_v0, _v1)))

encabezado_pagina(
    "Observatorio de Inteligencia Turística",
    "Lago de Atitlán, Sololá",
    "Seguimiento continuo de la demanda turística, la oferta de alojamiento y la presión sobre el territorio en los "
    "diez municipios ribereños del lago. El tablero se organiza en cuatro módulos y un análisis especializado de la "
    "red de municipios, con la metodología documentada en cada gráfica.",
    f"Telefonía: {MES_ES[p0.month - 1]} {p0.year} a {MES_ES[p1.month - 1]} {p1.year}<br><b>10 municipios</b>",
)
aviso_sinteticos(origenes())

indicadores([
    {"etiqueta": "Visitantes por mes, suma de municipios", "valor": formato_numero(k["visitantes_mes"]),
     "contexto": "Cota superior: un visitante puede contarse en varios municipios", "serie": k["serie_visitantes"]},
    {"etiqueta": "Estadía media ponderada", "valor": f"{k['estadia_media']:.2f} días", "contexto": "Turistas con pernocta",
     "serie": k["serie_estadia"]},
    {"etiqueta": "Visitantes extranjeros por mes", "valor": formato_numero(k["extranjeros_mes"]),
     "contexto": f"Nacionales: {formato_numero(k['nacionales_mes'])} por mes, con factor de expansión"},
    {"etiqueta": "Festividad de mayor impacto", "valor": lift["lift"].idxmax() if len(lift) else "Sin dato",
     "contexto": f"Lift de {lift['lift'].max():+.0%} frente a un día regular" if len(lift) else "Sin festividades en la base diaria"},
])

c1, c2 = st.columns([1, 1], gap="small")
with c1, st.container(key="tile-inicio-lectura"):
    st.html('<div class="ot-tt">Principales resultados</div><div class="ot-ts">Telefonía móvil, septiembre de 2025 a agosto de 2026</div>')
    nota("observado", f"{corto(perfil['visitantes_mes'].idxmax())} es el municipio con mayor afluencia y la principal "
         f"puerta de entrada del lago; {corto(perfil['estadia_media'].idxmax())} registra la estadía media más larga "
         f"({perfil['estadia_media'].max():.1f} días).")
    if not res_cruce.empty and {"Extranjero", "Nacional"} <= set(res_cruce.index):
        nota("observado", f"Entre septiembre y diciembre de 2025, la hotelería formal de Sololá registró el "
             f"{res_cruce.loc['Extranjero', 'captacion']:.0%} de las noches de los turistas extranjeros y el "
             f"{res_cruce.loc['Nacional', 'captacion']:.1%} de las de los nacionales (módulo 3).")
    nota("estimacion", "Enero y febrero de 2026 carecen de cobertura de telefonía. Sus valores se estiman a partir del "
         "flujo migratorio (módulo 2) y se identifican siempre como estimación.")
with c2, st.container(key="tile-inicio-reglas"):
    st.html('<div class="ot-tt">Criterios metodológicos</div><div class="ot-ts">Conforme a la guía de uso de los datos del INGUAT</div>')
    st.markdown(
        "- Un periodo sin cobertura se presenta como *sin dato*, nunca como cero.\n"
        "- La estadía media se pondera (Σ días-persona / Σ visitantes); no se promedia la permanencia.\n"
        "- La base diaria no se suma para obtener totales mensuales.\n"
        "- Los municipios no se suman como total del lago; toda agregación se rotula como suma de municipios.\n"
        "- Visitantes nacionales y extranjeros se reportan por separado (los nacionales incluyen factor de expansión).\n"
        "- Personas y porcentajes no comparten eje."
    )

with mosaico("inicio-cobertura", "Cobertura temporal de las fuentes de datos",
             "Meses con información por fuente, enero de 2023 a septiembre de 2026. Azul: con dato; gris: sin dato; "
             "recuadro violeta: meses estimados",
             "observado",
             "Las fuentes tienen coberturas distintas. Telefonía: sep–dic 2025 y mar–ago 2026 (ene–feb 2026 se estiman). "
             "Ocupación y boletines: 2023–2025. La única ventana donde telefonía y ocupación coinciden es sep–dic 2025, y "
             "todo cruce entre ellas se limita a esos cuatro meses. Oferta: un corte por año (inventario, no flujo)."):
    grafica(fig_cobertura(cobertura(), CONFIG["estimacion"]["meses_sin_cobertura"]), "inicio_cobertura")

ACCESOS = [
    ("paginas/m1_demanda.py", "1. Demanda y mercados", "Volumen de visitantes, estadía media, segmentación y principales mercados emisores.", ":material/groups:"),
    ("paginas/m2_temporal.py", "2. Dinámica temporal", "Afluencia diaria, efecto de las festividades, patrón semanal y estimación de enero y febrero de 2026.", ":material/calendar_month:"),
    ("paginas/m3_oferta.py", "3. Oferta hotelera", "Capacidad instalada, ocupación hotelera, captación formal de noches y alojamiento declarado.", ":material/hotel:"),
    ("paginas/m4_municipios.py", "4. Red de municipios", "Tipología de los diez municipios: hubs, larga estancia y visita corta.", ":material/hub:"),
    ("paginas/conclusiones.py", "Conclusiones y recomendaciones", "Síntesis de resultados y recomendaciones para el INGUAT.", ":material/flag:"),
]
cols = st.columns(len(ACCESOS), gap="small")
for i, (col, (pagina, titulo, desc, icono)) in enumerate(zip(cols, ACCESOS)):
    with col, st.container(key=f"acceso-{i}"):
        st.html(f'<div class="ot-acc-t">{titulo}</div><div class="ot-acc-d">{desc}</div>')
        st.page_link(pagina, label="Abrir", icon=icono)
