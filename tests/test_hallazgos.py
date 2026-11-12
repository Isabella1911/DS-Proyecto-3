"""Los hallazgos de los cuatro modulos se calculan con las tablas procesadas (datos sinteticos)."""

from __future__ import annotations

import pandas as pd

from src import etl, hallazgos


def test_resumen_completo():
    if not etl.vigente():
        etl.ejecutar()
    t = {n: pd.read_parquet(etl.PROCESADOS / f"{n}.parquet") for n in ["mensual", "diaria", "migracion_mensual", "ocupacion", "oferta"]}
    r = hallazgos.resumen(t["mensual"], t["diaria"], t["migracion_mensual"], t["ocupacion"], t["oferta"], etl.CONFIG)
    assert set(r) == {"demanda", "temporal", "oferta", "frontera", "territorio"}
    assert r["demanda"]["estadia_media"] > 1
    assert len(r["temporal"]["estimados"]) == len(etl.CONFIG["estimacion"]["meses_sin_cobertura"])
    assert r["oferta"]["meses_cruce"] >= 1
    assert r["territorio"]["n"] == 10
    assert sum(len(v) for v in r["territorio"]["miembros"].values()) == 10
