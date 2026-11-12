"""Hallazgos principales de los cuatro modulos en un solo lugar.

Los usa la pagina de Conclusiones y el script scripts/revisar_datos.py, asi las cifras que se
presentan y las que se revisan con las bases reales salen del mismo calculo. Todo es agregado
(nunca microdatos). Cada bloque devuelve None en lo que no se pueda calcular con los datos cargados.
"""

from __future__ import annotations

import pandas as pd

from src import indicadores as ind
from src import oferta as of
from src import pronostico as pr
from src import territorio as te
from src.normalizar import departamento as normalizar_departamento


def demanda(m: pd.DataFrame) -> dict:
    k = ind.kpis_demanda(m)
    perfil = ind.por_municipio(m)
    top = ind.top_paises(m, 10)
    return {
        "visitantes_mes": k["visitantes_mes"],
        "estadia_media": k["estadia_media"],
        "extranjeros_mes": k["extranjeros_mes"],
        "nacionales_mes": k["nacionales_mes"],
        "pct_turistas": k["pct_turistas"],
        "meses": k["meses"],
        "mun_volumen": perfil["visitantes_mes"].idxmax() if len(perfil) else None,
        "mun_estadia": perfil["estadia_media"].idxmax() if len(perfil) else None,
        "estadia_mun_max": float(perfil["estadia_media"].max()) if len(perfil) else float("nan"),
        "mercado_lider": top.index[0] if len(top) else None,
        "pct_mercado_lider": float(top["pct"].iloc[0]) if len(top) else float("nan"),
        "mercado_estadia": top["estadia_media"].idxmax() if len(top) else None,
        "estadia_mercado_max": float(top["estadia_media"].max()) if len(top) else float("nan"),
    }


def temporal(d: pd.DataFrame, m: pd.DataFrame, mig: pd.DataFrame, faltantes: list[str], anios_perfil: list[int]) -> dict:
    diaria = ind.serie_diaria(d)
    lift = ind.lift_eventos(diaria)
    patron = ind.patron_semanal(diaria)
    obs = ind.serie_mensual(m)
    obs = obs.reindex(ind.calendario(obs.index, faltantes))
    res = {k: pr.estimar(obs, mig, faltantes, anios_perfil, k) for k in pr.METODOS}
    mejor = min(res, key=lambda k: res[k].mape)
    perfil = pr.perfil_estacional(mig, anios_perfil)
    meses = [int(p[-2:]) for p in faltantes]
    return {
        "evento_top": lift["lift"].idxmax() if len(lift) else None,
        "lift_top": float(lift["lift"].max()) if len(lift) else float("nan"),
        "lift_ajustado_top": float(lift.loc[lift["lift"].idxmax(), "lift_ajustado"]) if len(lift) else float("nan"),
        "eventos_negativos": lift.index[lift["lift"] < 0].tolist(),
        "presion_finde": ind.presion_fin_de_semana(patron),
        "dia_top": patron["promedio"].idxmax(),
        "metodo": mejor,
        "estimados": res[mejor].estimados,
        "mape": {k: r.mape for k, r in res.items()},
        "perfil_meses": {mes: float(perfil.get(mes, float("nan"))) for mes in meses},
    }


def frontera(f: pd.DataFrame | None) -> dict:
    """Ola mas reciente de la encuesta en fronteras (porcentajes muestrales, sin factor de expansion)."""
    if f is None or f.empty:
        return {}
    ola = f.groupby("ola")["hasta"].max().idxmax()
    g = f[f["ola"] == ola]
    n = float(g["encuestas"].sum())
    hosp = g.groupby("hospedaje")["encuestas"].sum().drop(index=["N/A"], errors="ignore")
    hosp = hosp / hosp.sum()
    puesto = g.groupby("puesto")["encuestas"].sum() / n
    airbnb = (f[f["hospedaje"].str.contains("Airbnb", na=False)].groupby("ola")["encuestas"].sum()
              / f.groupby("ola")["encuestas"].sum()).dropna()
    return {
        "ola": ola, "encuestas": int(n), "desde": g["desde"].min(), "hasta": g["hasta"].max(),
        "pct_hotel": float(hosp[[h for h in hosp.index if "Hotel" in h]].sum()),
        "pct_airbnb": float(hosp[[h for h in hosp.index if "Airbnb" in h]].sum()),
        "puesto_top": puesto.idxmax().title(), "pct_puesto_top": float(puesto.max()),
        "airbnb_min": float(airbnb.min()) if len(airbnb) else float("nan"),
        "airbnb_max": float(airbnb.max()) if len(airbnb) else float("nan"),
    }


def oferta(oferta_t: pd.DataFrame, ocup: pd.DataFrame, m: pd.DataFrame, departamento: str,
           ventana: list[str], boletin: pd.DataFrame | None = None) -> dict:
    anual = of.capacidad_anual(of.capacidad(oferta_t, departamento))
    o_dep = ocup[ocup["departamento"] == departamento].set_index("periodo")["ocupacion"]
    if anual.empty or o_dep.empty:
        return {}
    v0, v1 = (pd.Timestamp(p + "-01") for p in ventana)
    cruce = of.cruce_ventana(m, boletin, o_dep, (v0, v1))
    rc = of.resumen_cruce(cruce)
    a0, a1 = int(anual.index.min()), int(anual.index.max())
    ult = int(o_dep.index.year.max())
    o_ult = o_dep[o_dep.index.year == ult]
    perfil_mes = o_dep.groupby(o_dep.index.month).mean()
    meses_ventana = cruce.drop_duplicates("periodo")

    def _rc(origen: str, col: str) -> float:
        return float(rc.loc[origen, col]) if origen in rc.index else float("nan")

    return {
        "anio0": a0, "anio1": a1,
        "plazas0": float(anual.loc[a0, "plazas_cama"]), "plazas1": float(anual.loc[a1, "plazas_cama"]),
        "anio_ocupacion": ult, "ocupacion_prom": float(o_ult.mean()),
        "mes_pico": int(o_ult.idxmax().month), "ocupacion_pico": float(o_ult.max()),
        "mes_valle_tipico": int(perfil_mes.idxmin()), "ocupacion_valle_tipico": float(perfil_mes.min()),
        "meses_cruce": len(meses_ventana),
        "ocupacion_oficial": float(meses_ventana["ocupacion_oficial"].mean()) if len(meses_ventana) else float("nan"),
        "captacion_ext": _rc("Extranjero", "captacion"), "captacion_nac": _rc("Nacional", "captacion"),
        "correlacion_ext": _rc("Extranjero", "correlacion"), "correlacion_nac": _rc("Nacional", "correlacion"),
        "noches_tel_ext": _rc("Extranjero", "noches_telefonia_mes"), "noches_hotel_ext": _rc("Extranjero", "noches_hotel_mes"),
        "noches_tel_nac": _rc("Nacional", "noches_telefonia_mes"), "noches_hotel_nac": _rc("Nacional", "noches_hotel_mes"),
    }


def territorio(m: pd.DataFrame, d: pd.DataFrame) -> dict:
    p = te.clasificar(te.perfil_completo(m, d))
    por_clase = te.perfil_por_clase(p, "clase_regla")
    miembros = {c: p.index[p["clase_regla"] == c].tolist() for c in te.CLASES}
    return {
        "perfil": p,
        "miembros": miembros,
        "por_clase": por_clase,
        "coinciden": int(p["coinciden"].sum()),
        "n": len(p),
        "estabilidad": p.attrs.get("estabilidad_kmedias", float("nan")),
        "difieren": p.index[~p["coinciden"]].tolist(),
        "cortes": te.cortes_regla(p),
        "mun_iee": p["iee"].idxmax(),
        "iee_max": float(p["iee"].max()),
        "estadia_mun_iee": float(p.loc[p["iee"].idxmax(), "estadia_media"]),
    }


def cargar(procesados) -> list[pd.DataFrame]:
    """Las 5 tablas base en el orden de resumen(): mensual, diaria, migracion, ocupacion y oferta."""
    return [pd.read_parquet(procesados / f"{n}.parquet") for n in ["mensual", "diaria", "migracion_mensual", "ocupacion", "oferta"]]


def cargar_opcionales(procesados) -> dict:
    """Boletines y encuesta en fronteras si se procesaron (None si la fuente no estaba)."""
    leer = lambda n: pd.read_parquet(procesados / f"{n}.parquet") if (procesados / f"{n}.parquet").exists() else None  # noqa: E731
    return {"boletin": leer("boletin_hotelero"), "frontera_t": leer("frontera_destino")}


def resumen(m: pd.DataFrame, d: pd.DataFrame, mig: pd.DataFrame, ocup: pd.DataFrame, oferta_t: pd.DataFrame,
            config: dict, boletin: pd.DataFrame | None = None, frontera_t: pd.DataFrame | None = None) -> dict:
    """Los cuatro bloques con la configuracion del observatorio (todo el lago, todos los origenes)."""
    est = config["estimacion"]
    return {
        "demanda": demanda(m),
        "temporal": temporal(d, m, mig, est["meses_sin_cobertura"], est["anios_perfil"]),
        "oferta": oferta(oferta_t, ocup, m, normalizar_departamento(config["destino"]["departamento"]),
                         config["ventana_coincidente"], boletin),
        "frontera": frontera(frontera_t),
        "territorio": territorio(m, d),
    }
