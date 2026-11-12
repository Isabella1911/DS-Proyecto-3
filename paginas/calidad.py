"""Calidad de los datos: origen de cada fuente y controles del ETL (src/etl.py)."""

import pandas as pd
import streamlit as st

from src.datos import CONFIG, calidad, cobertura, origenes
from src.graficas import fig_cobertura
from src.ui import aviso_sinteticos, encabezado_pagina, grafica, mosaico

cal = calidad()
encabezado_pagina(
    "Metodología",
    "Calidad de los datos",
    "Cada fuente pasa por una capa de normalización (municipios, países, departamentos, separadores decimales y fechas) "
    "y por controles de calidad antes de llegar al tablero. Los registros no reconocidos se documentan aquí; ninguno se "
    "descarta sin registro.",
    f"ETL ejecutado<br><b>{cal['generado'].replace('T', ' ')}</b>",
)
aviso_sinteticos(origenes())
NOMBRES = {"migracion": "Flujo migratorio", "movilidad_mensual": "Telefonía, base mensual",
           "movilidad_diaria": "Telefonía, base diaria", "ocupacion": "Índice de ocupación hotelera",
           "oferta": "Oferta hotelera", "boletines": "Boletines de ocupación (PDF)",
           "frontera": "Encuesta en puestos fronterizos"}
ORIGEN = {"real": "Institucional", "sintetico": "Sintético", "ausente": "No disponible"}

with mosaico("cal-cobertura", "Cobertura temporal de las fuentes de datos", "Azul oscuro: mes con dato; azul claro: cobertura "
             "parcial; gris: sin dato; recuadro violeta: meses estimados", "observado",
             "**¿Qué fuentes respaldan cada mes?** Un mes sin cobertura se lee como *sin dato*, nunca como cero. Telefonía "
             "y ocupación solo coinciden en sep–dic 2025: es la única ventana donde se cruzan."):
    grafica(fig_cobertura(cobertura(), CONFIG["estimacion"]["meses_sin_cobertura"]), "cal_cobertura")

fuentes = pd.DataFrame(cal["fuentes"]).T
fuentes.index = [NOMBRES.get(f, f) for f in fuentes.index]
fuentes["origen"] = fuentes["origen"].map(lambda o: ORIGEN.get(o, o))
fuentes = fuentes.rename(columns={
    "archivo": "Archivo", "origen": "Origen", "sha256": "Huella SHA-256", "filas_leidas": "Filas leídas",
    "filas_limpias": "Filas limpias", "tabla": "Tabla limpia"})
with mosaico("cal-fuentes", "Fuentes procesadas", "Archivo, origen, huella de integridad y registros leídos y depurados", "observado",
             "La huella SHA-256 identifica exactamente qué versión del archivo se procesó."):
    st.dataframe(fuentes, width="stretch")

ctrl = pd.DataFrame(cal["controles"])
ICONO = {"ok": "Correcto", "aviso": "Aviso", "error": "Error"}
ctrl["estado"] = ctrl["estado"].map(ICONO)
ctrl["fuente"] = ctrl["fuente"].map(lambda f: NOMBRES.get(f, f))
with mosaico("cal-controles", "Controles de calidad", "Resultado de cada control por fuente", "observado",
             "**aviso**: se corrigió o se excluyó y se documenta. **error**: dato imposible (p. ej. días-persona menores "
             "que visitantes) que hay que revisar en la fuente."):
    st.dataframe(ctrl.rename(columns={"fuente": "Fuente", "control": "Control", "estado": "Estado", "detalle": "Detalle",
                                      "filas": "Filas"}), width="stretch", hide_index=True, height=min(36 * (len(ctrl) + 1), 900),
                 column_config={"Detalle": st.column_config.TextColumn(width="large")})
    with st.expander("Detalle de avisos y de las fuentes complementarias", icon=":material/description:"):
        for c in cal["controles"]:
            if c["estado"] != "ok" or c["fuente"] in ("boletines", "frontera"):
                st.markdown(f"- {NOMBRES.get(c['fuente'], c['fuente'])}, {c['control'].lower()} ({ICONO[c['estado']].lower()}): {c['detalle']}")
