"""Calidad de los datos: origen de cada fuente y controles del ETL (src/etl.py)."""

import pandas as pd
import streamlit as st

from src.datos import calidad, origenes
from src.ui import aviso_sinteticos, encabezado_pagina, mosaico

cal = calidad()
encabezado_pagina(
    "Metodología",
    "Calidad de los datos",
    "Cada base pasa por la capa de normalización (nombres de municipios, países y departamentos, coma decimal, fechas) "
    "y por controles de calidad antes de llegar al tablero. Lo que no se reconoce se reporta aquí, no se descarta en silencio.",
    f"ETL ejecutado<br><b>{cal['generado'].replace('T', ' ')}</b>",
)
aviso_sinteticos(origenes())

fuentes = pd.DataFrame(cal["fuentes"]).T.rename(columns={
    "archivo": "Archivo", "origen": "Origen", "sha256": "Huella SHA-256", "filas_leidas": "Filas leídas",
    "filas_limpias": "Filas limpias", "tabla": "Tabla limpia"})
with mosaico("cal-fuentes", "Fuentes", "Archivo leído, origen (real o sintético) y filas", "observado",
             "La huella SHA-256 identifica exactamente qué versión del archivo se procesó."):
    st.dataframe(fuentes, width="stretch")

ctrl = pd.DataFrame(cal["controles"])
ESTADO = {"ok": "OK", "aviso": "Aviso", "error": "Error"}
ctrl["estado"] = ctrl["estado"].map(ESTADO).fillna(ctrl["estado"])
with mosaico("cal-controles", "Controles aplicados", "Un renglón por control y fuente", "observado",
             "**aviso**: se corrigió o se excluyó y se documenta. **error**: dato imposible (p. ej. días-persona menores "
             "que visitantes) que hay que revisar en la fuente."):
    st.dataframe(ctrl.rename(columns={"fuente": "Fuente", "control": "Control", "estado": "Estado", "detalle": "Detalle",
                                      "filas": "Filas"}), width="stretch", hide_index=True)
