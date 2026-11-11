"""Calculos del modulo 3: capacidad instalada, ocupacion y cruce con la afluencia.

Reglas:
- La oferta es inventario fisico por corte: no se suma entre cortes. El crecimiento se calcula solo con
  cortes completos (cuarto trimestre); 2026-T1 es parcial y se muestra aparte.
- El cruce afluencia x ocupacion se limita a la ventana coincidente (sep-dic 2025).
- Personas, noches y porcentajes no comparten eje.
"""

from __future__ import annotations

import pandas as pd

from src.normalizar import SEG_TURISTA

MEDIDAS = ["establecimientos", "habitaciones", "plazas_cama"]


def capacidad(oferta: pd.DataFrame, depto: str) -> pd.DataFrame:
    cap = oferta[oferta["departamento"] == depto].copy()
    cap["corte"] = [f"{int(a)}" + (f" (T{int(t)}, parcial)" if p else "")
                    for a, t, p in zip(cap["anio"], cap["trimestre"], cap["corte_parcial"])]
    return cap


def capacidad_anual(cap: pd.DataFrame) -> pd.DataFrame:
    """Totales del departamento por corte completo (un renglon por anio)."""
    return cap[~cap["corte_parcial"]].groupby("anio")[MEDIDAS].sum()


def matriz_ocupacion(ocup: pd.DataFrame, depto: str) -> pd.DataFrame:
    """Ocupacion del departamento en forma anio x mes (para el mapa de calor)."""
    o = ocup[ocup["departamento"] == depto]
    return o.pivot_table(index="anio", columns="mes", values="ocupacion").reindex(columns=range(1, 13))


def ocupacion_relativa(ocup: pd.DataFrame, depto: str) -> pd.Series:
    """Ocupacion del departamento menos el promedio de los demas, mes a mes (puntos porcentuales)."""
    t = ocup.pivot_table(index="periodo", columns="departamento", values="ocupacion")
    otros = t.drop(columns=depto, errors="ignore").mean(axis=1)
    return (t[depto] - otros).rename("diferencia")


def cruce_ventana(m: pd.DataFrame, anual: pd.DataFrame, ocup_dep: pd.Series, ventana: tuple[pd.Timestamp, pd.Timestamp]) -> pd.DataFrame:
    """Noches demandadas por los turistas frente a la capacidad formal, mes a mes en la ventana.

    noches_demandadas = Σ dias_persona del segmento turista (suma de municipios)
    plazas_noche      = plazas_cama del corte del anio × dias del mes
    tasa_implicita    = noches_demandadas / plazas_noche
    La tasa implicita se compara con la ocupacion oficial: si la supera, parte de las noches ocurre fuera de
    la hoteleria formal registrada (plataformas digitales, casas de familia) o la suma de municipios duplica.
    """
    v0, v1 = ventana
    t = m[(m["segmento"] == SEG_TURISTA) & m["periodo"].between(v0, v1)]
    filas = []
    for periodo, g in t.groupby("periodo"):
        anios = [a for a in anual.index if a <= periodo.year]
        if not anios:
            continue
        plazas = float(anual.loc[max(anios), "plazas_cama"])
        plazas_noche = plazas * periodo.days_in_month
        noches = float(g["dias_persona"].sum())
        filas.append({
            "periodo": periodo,
            "turistas": float(g["visitantes"].sum()),
            "noches_demandadas": noches,
            "plazas_noche": plazas_noche,
            "tasa_implicita": noches / plazas_noche,
            "ocupacion_oficial": float(ocup_dep.get(periodo, float("nan"))),
        })
    out = pd.DataFrame(filas)
    if out.empty:
        return out
    out = out.set_index("periodo")
    out["brecha"] = out["tasa_implicita"] - out["ocupacion_oficial"]
    return out
