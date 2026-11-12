"""Carga de las tablas limpias para el tablero (con cache de Streamlit).

app.py llama a preparar() antes de cada pagina: si faltan los parquet o cambiaron los archivos de
entrada (por ejemplo, se colocaron las bases reales en data/raw), corre el ETL (src/etl.py).
"""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from src import etl
from src.normalizar import MUNICIPIO_CORTO, MUNICIPIOS

TABLAS = ["mensual", "diaria", "migracion_mensual", "ocupacion", "oferta"]


def preparar() -> None:
    """Corre el ETL si faltan las tablas o si cambiaron los archivos de entrada (una vez por sesion)."""
    if st.session_state.get("_datos_revisados"):
        return
    if not etl.vigente():
        with st.spinner("Preparando datos… Se leen y normalizan las 5 bases; solo ocurre la primera vez "
                        "o cuando cambian los archivos.", show_time=True):
            etl.ejecutar()
        st.cache_data.clear()
    st.session_state["_datos_revisados"] = True


def _asegurar_procesados() -> None:
    """Respaldo cuando una pagina corre sola (pruebas): solo verifica que existan las tablas."""
    faltan = [t for t in TABLAS if not (etl.PROCESADOS / f"{t}.parquet").exists()]
    if faltan or not (etl.PROCESADOS / "calidad.json").exists():
        etl.ejecutar()


@st.cache_data(show_spinner=False)
def tabla(nombre: str) -> pd.DataFrame:
    _asegurar_procesados()
    return pd.read_parquet(etl.PROCESADOS / f"{nombre}.parquet")


@st.cache_data(show_spinner=False)
def calidad() -> dict:
    _asegurar_procesados()
    return json.loads((etl.PROCESADOS / "calidad.json").read_text(encoding="utf-8"))


def origenes() -> dict[str, str]:
    return {k: v["origen"] for k, v in calidad()["fuentes"].items()}


CONFIG = etl.CONFIG
TODOS = "Todo el lago (suma de municipios)"


def corto(municipio: str) -> str:
    return MUNICIPIO_CORTO.get(municipio, municipio)


def selector_ambito(key: str, columna=None, por_defecto: str = TODOS) -> list[str]:
    """Selector comun de ambito: un municipio o la suma de los 10 (rotulada como tal)."""
    opciones = [TODOS] + MUNICIPIOS
    destino = columna if columna is not None else st
    elegido = destino.selectbox(
        "Ámbito", opciones, index=opciones.index(por_defecto), key=key,
        help="La guía prohíbe sumar subdestinos como si fueran el total del destino: un visitante que recorre "
        "varios pueblos se cuenta en cada uno. La opción 'suma de municipios' es una cota superior, no el total del lago.",
    )
    return MUNICIPIOS if elegido == TODOS else [elegido]


def es_suma(municipios: list[str]) -> bool:
    return len(municipios) > 1
