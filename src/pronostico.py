"""Estimacion de los meses sin cobertura de telefonia (ene-feb 2026).

La guia pide usar el perfil estacional de Base_Migracion combinado con el factor de reparto
observado del destino. Se comparan dos variantes y se valida cada una contra los meses
observados (dejando fuera un mes a la vez):

A. Factor de reparto x migracion del mes
       F = Σ_obs D(t) / Σ_obs M(t)          D^(t) = F · M(t)
   M(t) = llegadas internacionales de visitantes (turistas + excursionistas) del mes t.

B. Perfil estacional x nivel del destino
       S(m) = promedio, en los anios del perfil, de M(anio, m) / promedio anual de M(anio)
       L = Σ_obs D(t) / Σ_obs S(m(t))      D^(t) = L · S(m(t))

D(t) es la serie mensual del destino (visitantes unicos del mes) para el ambito elegido.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

METODOS = {
    "A": "Factor de reparto × migración del mes",
    "B": "Perfil estacional de migración × nivel del destino",
}


def perfil_estacional(mig: pd.DataFrame, anios: list[int]) -> pd.Series:
    base = mig[mig["anio"].isin(anios)].copy()
    base["rel"] = base["llegadas"] / base.groupby("anio")["llegadas"].transform("mean")
    return base.groupby("mes")["rel"].mean()


def _predecir(obs: pd.Series, destino: pd.DatetimeIndex, mig: pd.Series, perfil: pd.Series, metodo: str) -> pd.Series:
    if metodo == "A":
        x_obs, x_dest = mig.reindex(obs.index), mig.reindex(destino)
    else:
        x_obs, x_dest = perfil.reindex(obs.index.month).set_axis(obs.index), perfil.reindex(destino.month).set_axis(destino)
    factor = obs.sum() / x_obs.sum()
    return (x_dest * factor).rename("estimado")


@dataclass
class Resultado:
    metodo: str
    factor: float
    estimados: pd.Series       # meses sin cobertura
    validacion: pd.DataFrame   # observado vs. estimado en cada mes observado (dejando fuera ese mes)
    mae: float
    rmse: float
    mape: float


def estimar(obs: pd.Series, mig: pd.DataFrame, faltantes: list[str], anios_perfil: list[int], metodo: str = "A") -> Resultado:
    obs = obs.dropna()
    obs = obs[obs > 0]
    m = mig.set_index("periodo")["llegadas"]
    perfil = perfil_estacional(mig, anios_perfil)
    destino = pd.DatetimeIndex([pd.Timestamp(p + "-01") for p in faltantes])
    estimados = _predecir(obs, destino, m, perfil, metodo)
    factor = float(obs.sum() / (m.reindex(obs.index).sum() if metodo == "A" else perfil.reindex(obs.index.month).sum()))

    filas = []
    for t in obs.index:
        resto = obs.drop(t)
        if resto.empty:
            continue
        pred = _predecir(resto, pd.DatetimeIndex([t]), m, perfil, metodo).iloc[0]
        filas.append({"periodo": t, "observado": obs[t], "estimado": pred})
    val = pd.DataFrame(filas).set_index("periodo")
    err = val["estimado"] - val["observado"]
    val["error_pct"] = err / val["observado"]
    return Resultado(
        metodo=metodo,
        factor=factor,
        estimados=estimados,
        validacion=val,
        mae=float(err.abs().mean()),
        rmse=float(np.sqrt((err**2).mean())),
        mape=float((err.abs() / val["observado"]).mean() * 100),
    )
