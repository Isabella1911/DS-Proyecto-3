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
    "Cada base pasa por la capa de normalización (nombres de municipios, países y departamentos, coma decimal, fechas) "
    "y por controles de calidad antes de llegar al tablero. Lo que no se reconoce se reporta aquí, no se descarta en silencio.",
    f"ETL ejecutado<br><b>{cal['generado'].replace('T', ' ')}</b>",
)
aviso_sinteticos(origenes())

with mosaico("cal-cobertura", "Cobertura de las fuentes", "Azul oscuro: mes con dato · azul claro: parcial · gris: sin dato · "
             "recuadro violeta: meses que se estiman", "observado",
             "**¿Qué fuentes respaldan cada mes?** Un mes sin cobertura se lee como *sin dato*, nunca como cero. Telefonía "
             "y ocupación solo coinciden en sep–dic 2025: es la única ventana donde se cruzan."):
    grafica(fig_cobertura(cobertura(), CONFIG["estimacion"]["meses_sin_cobertura"]), "cal_cobertura")

fuentes = pd.DataFrame(cal["fuentes"]).T.rename(columns={
    "archivo": "Archivo", "origen": "Origen", "sha256": "Huella SHA-256", "filas_leidas": "Filas leídas",
    "filas_limpias": "Filas limpias", "tabla": "Tabla limpia"})
with mosaico("cal-fuentes", "Fuentes", "Archivo leído, origen (real o sintético) y filas", "observado",
             "La huella SHA-256 identifica exactamente qué versión del archivo se procesó."):
    st.dataframe(fuentes, width="stretch")

ctrl = pd.DataFrame(cal["controles"])
ICONO = {"ok": "✅ ok", "aviso": "⚠️ aviso", "error": "⛔ error"}
ctrl["estado"] = ctrl["estado"].map(ICONO)
with mosaico("cal-controles", "Controles aplicados", "Un renglón por control y fuente", "observado",
             "**aviso**: se corrigió o se excluyó y se documenta. **error**: dato imposible (p. ej. días-persona menores "
             "que visitantes) que hay que revisar en la fuente."):
    st.dataframe(ctrl.rename(columns={"fuente": "Fuente", "control": "Control", "estado": "Estado", "detalle": "Detalle",
                                      "filas": "Filas"}), width="stretch", hide_index=True, height=min(36 * (len(ctrl) + 1), 900),
                 column_config={"Detalle": st.column_config.TextColumn(width="large")})
    with st.expander("Detalle completo de avisos y fuentes complementarias", icon=":material/warning:"):
        for c in cal["controles"]:
            if c["estado"] != "ok" or c["fuente"] in ("boletines", "frontera"):
                st.markdown(f"- **{c['fuente']} · {c['control']}** ({ICONO[c['estado']]}): {c['detalle']}")
