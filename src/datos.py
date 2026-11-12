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
def tabla_opcional(nombre: str) -> pd.DataFrame | None:
    """Tabla de una fuente opcional (boletines, encuesta en fronteras) o None si no se cargo."""
    _asegurar_procesados()
    ruta = etl.PROCESADOS / f"{nombre}.parquet"
    return pd.read_parquet(ruta) if ruta.exists() else None


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


FUENTES_COBERTURA = [
    "Telefonía mensual", "Telefonía diaria", "Migración (llegadas)", "Ocupación hotelera (CSV)",
    "Boletines de ocupación (PDF)", "Encuesta en fronteras", "Oferta hotelera (corte)",
]


@st.cache_data(show_spinner=False)
def cobertura(desde: str = "2023-01", hasta: str = "2026-09") -> pd.DataFrame:
    """Matriz fuente x mes: 1 = mes con dato, 0.5 = cobertura parcial, NaN = sin dato (nunca cero)."""
    meses = pd.date_range(desde + "-01", hasta + "-01", freq="MS")
    t = pd.DataFrame(index=FUENTES_COBERTURA, columns=meses, dtype=float)
    t.loc["Telefonía mensual", t.columns.isin(tabla("mensual")["periodo"].unique())] = 1
    d = tabla("diaria")
    dias = d.groupby(d["fecha"].dt.to_period("M").dt.to_timestamp())["fecha"].nunique()
    for mes, n in dias.items():
        if mes in t.columns:
            t.loc["Telefonía diaria", mes] = 1 if n >= 28 else 0.5
    t.loc["Migración (llegadas)", t.columns.isin(tabla("migracion_mensual")["periodo"].unique())] = 1
    t.loc["Ocupación hotelera (CSV)", t.columns.isin(tabla("ocupacion")["periodo"].unique())] = 1
    b = tabla_opcional("boletin_hotelero")
    if b is not None:
        t.loc["Boletines de ocupación (PDF)", t.columns.isin(b["periodo"].unique())] = 1
    f = tabla_opcional("frontera_destino")
    if f is not None and not f.empty:
        ini, fin = pd.Timestamp(f["desde"].min()).to_period("M").to_timestamp(), pd.Timestamp(f["hasta"].max())
        t.loc["Encuesta en fronteras", (t.columns >= ini) & (t.columns <= fin)] = 1
    for anio, trim in tabla("oferta")[["anio", "trimestre"]].drop_duplicates().itertuples(index=False):
        mes = pd.Timestamp(int(anio), int(trim) * 3, 1)
        if mes in t.columns:
            t.loc["Oferta hotelera (corte)", mes] = 1
    return t
