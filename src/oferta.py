"""Oferta hotelera (modulo 3): capacidad instalada, ocupacion y su cruce con la demanda de noches.

Reglas:
- La capacidad anual usa solo cortes completos (cuarto trimestre). El corte parcial de 2026 se
  muestra aparte y no entra al crecimiento.
- Personas, noches y porcentajes nunca comparten eje (las figuras usan paneles separados).
- La tasa implicita solo se calcula en la ventana en que coinciden telefonia y ocupacion.
"""

from __future__ import annotations

import pandas as pd

from src.normalizar import SEG_TURISTA

MEDIDAS = ["establecimientos", "habitaciones", "plazas_cama"]


def capacidad(oferta: pd.DataFrame, departamento: str) -> pd.DataFrame:
    """Oferta del departamento por corte y tipo de alojamiento.

    `corte` es el anio ('2025') o, si el corte es parcial, anio y trimestre ('2026-T1').
    """
    o = oferta[oferta["departamento"] == departamento].copy()
    if o.empty:
        return o.assign(corte=pd.Series(dtype="string"))
    o["corte"] = [f"{a}-T{t}" if p else str(a) for a, t, p in zip(o["anio"], o["trimestre"], o["corte_parcial"])]
    return (
        o.groupby(["corte", "anio", "trimestre", "tipo_alojamiento", "corte_parcial"], as_index=False)
        .agg(**{m: (m, "sum") for m in MEDIDAS}, repite_previo=("repite_previo", "all"))
        .sort_values(["corte", "tipo_alojamiento"])
        .reset_index(drop=True)
    )


def capacidad_anual(cap: pd.DataFrame) -> pd.DataFrame:
    """Total del departamento por anio, solo con cortes completos (ultimo trimestre de cada anio)."""
    completos = cap[~cap["corte_parcial"]]
    if completos.empty:
        return pd.DataFrame(columns=MEDIDAS, index=pd.Index([], name="anio"))
    ultimo = completos.groupby("anio")["trimestre"].transform("max")
    anual = completos[completos["trimestre"] == ultimo].groupby("anio")[MEDIDAS].sum()
    anual.index = anual.index.astype(int)
    return anual


def _plazas_del_anio(anual: pd.DataFrame, anio: int) -> float:
    """Plazas cama del corte del anio o, si no existe, del ultimo corte anterior."""
    previos = anual.loc[anual.index <= anio, "plazas_cama"]
    return float(previos.iloc[-1]) if len(previos) else float("nan")


def cruce_ventana(m: pd.DataFrame, anual: pd.DataFrame, ocupacion: pd.Series,
                  ventana: tuple[pd.Timestamp, pd.Timestamp]) -> pd.DataFrame:
    """Noches demandadas por los turistas frente a la capacidad formal, mes a mes.

    - noches_demandadas = suma de dias_persona de los turistas con pernocta (suma de municipios).
    - plazas_noche = plazas cama del corte del anio x dias del mes.
    - tasa_implicita = noches_demandadas / plazas_noche (comparable con la ocupacion oficial).
    - brecha = tasa_implicita - ocupacion_oficial, en puntos de proporcion.
    Solo quedan los meses con ambas series.
    """
    meses = pd.date_range(ventana[0], ventana[1], freq="MS")
    tur = m[(m["segmento"] == SEG_TURISTA) & m["periodo"].isin(meses)]
    t = tur.groupby("periodo").agg(turistas=("visitantes", "sum"), noches_demandadas=("dias_persona", "sum"))
    t = t.reindex(meses)
    t.index.name = "periodo"
    t["plazas_noche"] = [_plazas_del_anio(anual, p.year) * p.days_in_month for p in t.index]
    t["tasa_implicita"] = t["noches_demandadas"] / t["plazas_noche"]
    t["ocupacion_oficial"] = ocupacion.reindex(t.index).to_numpy()
    t["brecha"] = t["tasa_implicita"] - t["ocupacion_oficial"]
    return t.dropna(subset=["noches_demandadas", "plazas_noche", "ocupacion_oficial"])


def matriz_ocupacion(ocup: pd.DataFrame, departamento: str) -> pd.DataFrame:
    """Ocupacion del departamento como tabla anio x mes (1 a 12); los meses sin dato quedan vacios."""
    o = ocup[ocup["departamento"] == departamento]
    t = o.pivot_table(index="anio", columns="mes", values="ocupacion", aggfunc="mean")
    t = t.reindex(columns=range(1, 13))
    t.index = t.index.astype(int)
    return t
