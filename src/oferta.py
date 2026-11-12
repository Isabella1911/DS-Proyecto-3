"""Oferta hotelera (modulo 3): capacidad instalada, ocupacion y su cruce con la demanda de noches.

Reglas:
- La capacidad anual usa solo cortes completos (cuarto trimestre). El corte parcial de 2026 se
  muestra aparte y no entra al crecimiento.
- Personas, noches y porcentajes nunca comparten eje (las figuras usan paneles separados).
- El cruce entre afluencia y hoteleria solo se calcula en la ventana en que coinciden telefonia y
  ocupacion (sep-dic 2025), y siempre por origen: extranjeros (telefonia) frente a no residentes
  (boletin) y nacionales frente a residentes. Nunca se mezclan ni se divide extranjeros / total.
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


ORIGEN_BOLETIN = {"Extranjero": "no_residentes", "Nacional": "residentes"}


def cruce_ventana(m: pd.DataFrame, boletin: pd.DataFrame | None, ocupacion: pd.Series,
                  ventana: tuple[pd.Timestamp, pd.Timestamp]) -> pd.DataFrame:
    """Triangulacion telefonia x hoteleria formal en la ventana coincidente, por mes y origen.

    - noches_telefonia = Σ (dias_persona - visitantes) de los turistas con pernocta: una persona
      presente d dias pasa d - 1 noches (suma de municipios: cota superior).
    - noches_hotel = noches realizadas (pernoctaciones) en la hoteleria formal del departamento,
      segun el boletin de INGUAT (residentes o no residentes).
    - captacion_formal = noches_hotel / noches_telefonia: que parte de las noches que la telefonia
      registra en el lago pasa por un hotel formal registrado. Como el denominador es una cota
      superior, la captacion es una cota inferior.
    Solo quedan los meses de la ventana con ambas fuentes.
    """
    meses = pd.date_range(ventana[0], ventana[1], freq="MS")
    tur = m[(m["segmento"] == SEG_TURISTA) & m["periodo"].isin(meses)]
    t = tur.groupby(["periodo", "origen"]).agg(turistas_telefonia=("visitantes", "sum"), dias=("dias_persona", "sum"))
    t["noches_telefonia"] = t["dias"] - t["turistas_telefonia"]
    t = t.drop(columns="dias").reset_index()
    if boletin is not None and not boletin.empty:
        b = boletin.set_index("periodo")
        for origen, sufijo in ORIGEN_BOLETIN.items():
            fila = t["origen"] == origen
            t.loc[fila, "huespedes_hotel"] = t.loc[fila, "periodo"].map(b[f"huespedes_{sufijo}"]).to_numpy()
            t.loc[fila, "noches_hotel"] = t.loc[fila, "periodo"].map(b[f"noches_{sufijo}"]).to_numpy()
    else:
        t["huespedes_hotel"] = float("nan")
        t["noches_hotel"] = float("nan")
    t["captacion_formal"] = t["noches_hotel"] / t["noches_telefonia"]
    t["ocupacion_oficial"] = t["periodo"].map(ocupacion).to_numpy()
    return t.dropna(subset=["noches_telefonia", "ocupacion_oficial"]).sort_values(["origen", "periodo"]).reset_index(drop=True)


def resumen_cruce(cruce: pd.DataFrame) -> pd.DataFrame:
    """Por origen: captacion de la ventana completa (Σ noches hotel / Σ noches telefonia) y correlacion mensual."""
    filas = {}
    for origen, g in cruce.groupby("origen"):
        g = g.dropna(subset=["noches_hotel"])
        if g.empty:
            continue
        filas[origen] = {
            "meses": len(g),
            "noches_telefonia_mes": g["noches_telefonia"].mean(),
            "noches_hotel_mes": g["noches_hotel"].mean(),
            "captacion": g["noches_hotel"].sum() / g["noches_telefonia"].sum(),
            "correlacion": g["noches_hotel"].corr(g["noches_telefonia"]) if len(g) >= 3 else float("nan"),
        }
    return pd.DataFrame.from_dict(filas, orient="index")


def uso_capacidad(boletin: pd.DataFrame | None, anual: pd.DataFrame, ocupacion: pd.Series) -> pd.DataFrame:
    """Indice publicado frente a la ocupacion sobre el inventario registrado, por anio.

    - habitaciones_indice = habitaciones ocupadas / indice / dias del mes (promedio del anio): tamano implicito
      de la base sobre la que se calcula el indice (establecimientos que reportan).
    - cobertura = habitaciones_indice / habitaciones del inventario (corte de cierre de anio).
    - ocupacion_inventario = habitaciones-noche ocupadas / (habitaciones del inventario x 365).
    """
    if boletin is None or boletin.empty:
        return pd.DataFrame()
    b = boletin.assign(hab_indice=boletin["hab_total"] / boletin["ocupacion"] / boletin["periodo"].dt.days_in_month)
    t = b.groupby("anio").agg(habitaciones_ocupadas=("hab_total", "sum"), habitaciones_indice=("hab_indice", "mean"))
    t = t[t.index.isin(anual.index)]
    t["inventario"] = t.index.map(anual["habitaciones"])
    t["cobertura"] = t["habitaciones_indice"] / t["inventario"]
    t["ocupacion_inventario"] = t["habitaciones_ocupadas"] / (t["inventario"] * 365)
    t["ocupacion_publicada"] = t.index.map(ocupacion.groupby(ocupacion.index.year).mean())
    return t


def matriz_ocupacion(ocup: pd.DataFrame, departamento: str) -> pd.DataFrame:
    """Ocupacion del departamento como tabla anio x mes (1 a 12); los meses sin dato quedan vacios."""
    o = ocup[ocup["departamento"] == departamento]
    t = o.pivot_table(index="anio", columns="mes", values="ocupacion", aggfunc="mean")
    t = t.reindex(columns=range(1, 13))
    t.index = t.index.astype(int)
    return t
