"""Observatorio de Inteligencia Turística - Lago de Atitlán (Grupo 3, CC3084 Data Science, UVG).

Ejecutar:
    streamlit run app.py
"""

import streamlit as st

from src.ui import FUENTE_DATOS, estilo_global

st.set_page_config(
    page_title="Observatorio Turístico · Lago de Atitlán",
    page_icon="static/icono.svg",
    layout="wide",
)
st.logo("static/logo.svg", icon_image="static/icono.svg", size="large")
estilo_global()

paginas = st.navigation(
    {
        "Observatorio": [
            st.Page("paginas/inicio.py", title="Inicio", icon=":material/dashboard:", default=True),
        ],
        "Módulos": [
            st.Page("paginas/m1_demanda.py", title="1 · Demanda y mercados", icon=":material/groups:"),
            st.Page("paginas/m2_temporal.py", title="2 · Dinámica temporal y pronóstico", icon=":material/calendar_month:"),
            st.Page("paginas/m3_oferta.py", title="3 · Oferta hotelera", icon=":material/hotel:"),
            st.Page("paginas/m4_municipios.py", title="4 · Red de municipios", icon=":material/hub:"),
        ],
        "Metodología": [
            st.Page("paginas/calidad.py", title="Calidad de los datos", icon=":material/fact_check:"),
            st.Page("paginas/acerca.py", title="Acerca del observatorio", icon=":material/info:"),
        ],
    }
)
st.sidebar.caption(FUENTE_DATOS)
paginas.run()
