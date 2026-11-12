"""El ETL se vuelve a correr cuando cambian los archivos de entrada (p. ej. al agregar los reales)."""

from __future__ import annotations

import shutil

from src import etl


def test_vigente_detecta_archivos_nuevos(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    procesados = tmp_path / "procesados"
    monkeypatch.setenv("OBS_DATOS", str(raw))

    etl.ejecutar(destino=procesados)
    assert etl.vigente(procesados)

    # Llega un archivo "real" a data/raw: lo procesado ya no corresponde a las entradas
    sint = etl.RAIZ / etl.CONFIG["rutas"]["sinteticos"]
    shutil.copy(next(sint.glob(etl.CONFIG["fuentes"]["oferta"]["patron"])), raw / "oferta_hotelera_2022_2026.csv")
    assert not etl.vigente(procesados)


def test_vigente_sin_procesados(tmp_path):
    assert not etl.vigente(tmp_path / "no_existe")
