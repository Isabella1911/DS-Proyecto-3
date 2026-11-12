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
        "pct_extranjeros": k["pct_extranjeros"],
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


def oferta(oferta_t: pd.DataFrame, ocup: pd.DataFrame, m: pd.DataFrame, departamento: str,
           ventana: list[str]) -> dict:
    anual = of.capacidad_anual(of.capacidad(oferta_t, departamento))
    o_dep = ocup[ocup["departamento"] == departamento].set_index("periodo")["ocupacion"]
    if anual.empty or o_dep.empty:
        return {}
    v0, v1 = (pd.Timestamp(p + "-01") for p in ventana)
    cruce = of.cruce_ventana(m, anual, o_dep, (v0, v1))
    a0, a1 = int(anual.index.min()), int(anual.index.max())
    ult = int(o_dep.index.year.max())
    o_ult = o_dep[o_dep.index.year == ult]
    return {
        "anio0": a0, "anio1": a1,
        "plazas0": float(anual.loc[a0, "plazas_cama"]), "plazas1": float(anual.loc[a1, "plazas_cama"]),
        "anio_ocupacion": ult, "ocupacion_prom": float(o_ult.mean()),
        "mes_pico": int(o_ult.idxmax().month), "ocupacion_pico": float(o_ult.max()),
        "meses_cruce": len(cruce),
        "tasa_implicita": float(cruce["tasa_implicita"].mean()) if len(cruce) else float("nan"),
        "ocupacion_oficial": float(cruce["ocupacion_oficial"].mean()) if len(cruce) else float("nan"),
        "noches_mes": float(cruce["noches_demandadas"].mean()) if len(cruce) else float("nan"),
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
    }


def resumen(m: pd.DataFrame, d: pd.DataFrame, mig: pd.DataFrame, ocup: pd.DataFrame, oferta_t: pd.DataFrame,
            config: dict) -> dict:
    """Los cuatro bloques con la configuracion del observatorio (todo el lago, todos los origenes)."""
    est = config["estimacion"]
    return {
        "demanda": demanda(m),
        "temporal": temporal(d, m, mig, est["meses_sin_cobertura"], est["anios_perfil"]),
        "oferta": oferta(oferta_t, ocup, m, normalizar_departamento(config["destino"]["departamento"]),
                         config["ventana_coincidente"]),
        "territorio": territorio(m, d),
    }
