"""Reglas metodologicas de la guia, verificadas con tablas pequenas hechas a mano."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import indicadores as ind
from src import normalizar as nz
from src import pronostico as pr

T, E = nz.SEG_TURISTA, nz.SEG_EXCURSIONISTA


def _mensual(filas):
    df = pd.DataFrame(filas, columns=["municipio", "periodo", "pais", "origen", "segmento", "visitantes", "dias_persona"])
    df["periodo"] = pd.to_datetime(df["periodo"])
    return df


def test_estadia_ponderada_no_promedia_permanencia():
    # Permanencias 2 y 10: el promedio simple daria 6; la ponderada (2*10 + 10*1)/(10+1) = 2.73
    m = _mensual([
        ("Panajachel", "2025-09-01", "Alemania", "Extranjero", T, 10, 20),
        ("Panajachel", "2025-09-01", "Francia", "Extranjero", T, 1, 10),
        ("Panajachel", "2025-09-01", "Guatemala", "Nacional", E, 100, 100),  # excursionistas: fuera de la estadia
    ])
    assert ind.estadia_media(m) == pytest.approx(30 / 11)


def test_mes_sin_dato_es_nan_no_cero():
    m = _mensual([
        ("Panajachel", "2025-12-01", "Alemania", "Extranjero", T, 10, 20),
        ("Panajachel", "2026-03-01", "Alemania", "Extranjero", T, 12, 24),
    ])
    s = ind.serie_mensual(m)
    assert s.loc["2026-01-01"] != s.loc["2026-01-01"]  # NaN
    assert len(s) == 4


@pytest.mark.parametrize("texto,esperado", [
    ("PANAJACHEL", "Panajachel"), ("Panajachel ", "Panajachel"), ("SAN MARCOS", "San Marcos La Laguna"),
    ("Sta. Catarina Palopó", "Santa Catarina Palopó"), ("SN. ANTONIO PALOPO", "San Antonio Palopó"),
    ("santiago atitlan", "Santiago Atitlán"), ("Otro lugar", None),
])
def test_normalizar_municipios(texto, esperado):
    assert nz.municipio(texto) == esperado


def test_normalizar_varios():
    assert nz.pais("ALEMANIA") == "Alemania"
    assert nz.pais("ESTADOS UNIDOS") == "Estados Unidos"
    assert nz.segmento("Mayor a 1") == T and nz.segmento("menor a 1 ") == E
    assert nz.evento("REGULAR") == nz.EVENTO_REGULAR
    assert nz.departamento("SOLOLA") == "Sololá"
    assert nz.numero(pd.Series(["2,55", "1.234,5", "3"])).tolist() == [2.55, 1234.5, 3.0]


def test_lift():
    fechas = pd.date_range("2025-09-01", periods=21, freq="D")
    d = pd.DataFrame({"fecha": fechas, "visitantes": 100.0, "evento": nz.EVENTO_REGULAR})
    d.loc[d["fecha"] == "2025-09-15", ["visitantes", "evento"]] = [150.0, "Independencia"]
    lift = ind.lift_eventos(ind.serie_diaria(d))
    assert lift.loc["Independencia", "lift"] == pytest.approx(0.5)


def test_estimacion_factor_exacto():
    # Si el destino es siempre 10 % de las llegadas, la estimacion debe ser exacta y el MAPE 0
    per = pd.date_range("2025-09-01", "2026-06-01", freq="MS")
    mig = pd.DataFrame({"periodo": per, "anio": per.year, "mes": per.month, "llegadas": range(1000, 1000 + 100 * len(per), 100)})
    obs = (mig.set_index("periodo")["llegadas"] * 0.1).drop(pd.to_datetime(["2026-01-01", "2026-02-01"]))
    r = pr.estimar(obs, mig, ["2026-01", "2026-02"], [2025, 2026], "A")
    assert r.mape == pytest.approx(0, abs=1e-9)
    assert r.estimados.iloc[0] == pytest.approx(mig.set_index("periodo").loc["2026-01-01", "llegadas"] * 0.1)


def test_kmedias_separa_grupos_evidentes():
    from src import territorio as te

    p = pd.DataFrame({
        "visitantes_mes": [10000, 9000, 1000, 1100, 1200, 900],
        "estadia_media": [2.0, 2.1, 5.0, 5.2, 1.2, 1.3],
        "pct_extranjeros": [0.4, 0.4, 0.8, 0.8, 0.1, 0.1],
        "presion_finde": [1.3, 1.3, 1.1, 1.1, 1.8, 1.8],
    }, index=list("abcdef"))
    p["log_volumen"] = np.log10(p["visitantes_mes"])
    clases = te.clasificar_kmedias(p)
    assert clases[["a", "b"]].eq("Hub comercial").all()
    assert clases[["c", "d"]].eq("Larga estancia").all()
    assert clases[["e", "f"]].eq("Visita corta").all()


def test_cruce_ventana_tasa_implicita():
    from src import oferta as of

    m = _mensual([("Panajachel", "2025-09-01", "Alemania", "Extranjero", T, 100, 300)])
    anual = pd.DataFrame({"plazas_cama": [1000.0]}, index=pd.Index([2025], name="anio"))
    ocup = pd.Series([0.4], index=pd.to_datetime(["2025-09-01"]))
    c = of.cruce_ventana(m, anual, ocup, (pd.Timestamp("2025-09-01"), pd.Timestamp("2025-12-01")))
    assert c.loc["2025-09-01", "tasa_implicita"] == pytest.approx(300 / (1000 * 30))
