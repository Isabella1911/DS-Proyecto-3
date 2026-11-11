"""Pruebas de humo: cada pagina corre sin excepciones (con los datos sinteticos)."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
# inicio.py usa st.page_link y solo corre dentro de app.py (lo cubre test_app_navegacion)
PAGINAS = sorted(str(p.relative_to(ROOT)) for p in (ROOT / "paginas").glob("*.py") if p.name != "inicio.py")


def correr(pagina: str) -> AppTest:
    at = AppTest.from_file(str(ROOT / pagina), default_timeout=120)
    at.run()
    return at


@pytest.mark.parametrize("pagina", PAGINAS)
def test_pagina_sin_errores(pagina):
    at = correr(pagina)
    assert not at.exception, at.exception


def test_app_navegacion():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120)
    at.run()
    assert not at.exception


@pytest.mark.parametrize("origen", ["Nacional", "Extranjero"])
def test_m1_origen(origen):
    at = correr("paginas/m1_demanda.py")
    at.button_group(key="m1_origen").set_value(origen).run()
    assert not at.exception


def test_m2_todos_los_ambitos():
    at = correr("paginas/m2_temporal.py")
    for amb in at.selectbox(key="m2_ambito").options:
        at.selectbox(key="m2_ambito").set_value(amb).run()
        assert not at.exception, amb


def test_m3_medidas():
    at = correr("paginas/m3_oferta.py")
    for medida in ["establecimientos", "habitaciones", "plazas_cama"]:
        at.button_group(key="m3_medida").set_value(medida).run()
        assert not at.exception, medida
    at.button_group(key="m3_sub_medida").set_value("Días-persona").run()
    at.button_group(key="m3_sub_origen").set_value("Extranjero").run()
    assert not at.exception


def test_m4_metodos():
    at = correr("paginas/m4_municipios.py")
    at.button_group(key="m4_metodo").set_value("k-medias").run()
    assert not at.exception
