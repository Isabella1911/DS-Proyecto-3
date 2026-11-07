"""Indicadores del observatorio (funciones puras sobre las tablas limpias del ETL).

Reglas de la guia que se respetan aqui:
- La estadia media es Σ dias_persona / Σ visitantes del segmento 'mayor a 1'; nunca se
  promedia la columna permanencia_prom.
- La base diaria mide presencia por dia: no se suma para obtener visitantes del mes.
- Los municipios no se suman para dar un total del lago sin advertirlo (duplican visitantes):
  toda cifra de varios municipios se rotula como "suma de municipios".
- Un mes sin dato es NaN ('Sin dato'), nunca cero.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.normalizar import DIAS_SEMANA, EVENTO_REGULAR, MUNICIPIOS, SEG_EXCURSIONISTA, SEG_TURISTA

ORIGENES = ["Nacional", "Extranjero"]


def filtrar(df: pd.DataFrame, municipios: list[str] | None = None, origen: str | None = None) -> pd.DataFrame:
    out = df
    if municipios:
        out = out[out["municipio"].isin(municipios)]
    if origen in ORIGENES:
        out = out[out["origen"] == origen]
    return out


def calendario(periodos: pd.Series, extra: list[str] | None = None) -> pd.DatetimeIndex:
    """Todos los meses entre el primero y el ultimo (incluye los que no tienen dato)."""
    fechas = list(pd.to_datetime(periodos))
    fechas += [pd.Timestamp(p + "-01") for p in (extra or [])]
    return pd.date_range(min(fechas), max(fechas), freq="MS")


# ---------------------------------------------------------------------------------------------
# Modulo 1


def serie_mensual(m: pd.DataFrame, columna: str = "visitantes") -> pd.Series:
    """Total mensual (meses sin dato quedan NaN, no 0)."""
    s = m.groupby("periodo")[columna].sum()
    return s.reindex(calendario(s.index)) if len(s) else s


def estadia_media(m: pd.DataFrame) -> float:
    """Σ dias_persona / Σ visitantes, solo turistas con pernocta (> 1 dia)."""
    t = m[m["segmento"] == SEG_TURISTA]
    vis = t["visitantes"].sum()
    return float(t["dias_persona"].sum() / vis) if vis else float("nan")


def kpis_demanda(m: pd.DataFrame) -> dict:
    mensual = m.groupby("periodo")[["visitantes", "dias_persona"]].sum()
    total = m["visitantes"].sum()
    turistas = m.loc[m["segmento"] == SEG_TURISTA, "visitantes"].sum()
    extranjeros = m.loc[m["origen"] == "Extranjero", "visitantes"].sum()
    return {
        "meses": len(mensual),
        "visitantes_mes": float(mensual["visitantes"].mean()) if len(mensual) else float("nan"),
        "dias_persona_mes": float(mensual["dias_persona"].mean()) if len(mensual) else float("nan"),
        "estadia_media": estadia_media(m),
        "pct_turistas": float(turistas / total) if total else float("nan"),
        "pct_extranjeros": float(extranjeros / total) if total else float("nan"),
        "serie_visitantes": mensual["visitantes"].tolist(),
        "serie_estadia": [estadia_media(g) for _, g in m.groupby("periodo")],
    }


def segmentacion(m: pd.DataFrame) -> pd.DataFrame:
    """Visitantes por mes y segmento (turista / excursionista) con su proporcion."""
    t = m.pivot_table(index="periodo", columns="segmento", values="visitantes", aggfunc="sum")
    t = t.reindex(columns=[SEG_TURISTA, SEG_EXCURSIONISTA]).reindex(calendario(t.index))
    t["pct_turistas"] = t[SEG_TURISTA] / t[[SEG_TURISTA, SEG_EXCURSIONISTA]].sum(axis=1, min_count=1)
    return t


def top_paises(m: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top n nacionalidades extranjeras con su estadia media (los nacionales van aparte)."""
    ext = m[m["origen"] == "Extranjero"]
    vis = ext.groupby("pais")["visitantes"].sum().sort_values(ascending=False)
    top = vis.head(n).to_frame("visitantes")
    top["pct"] = top["visitantes"] / vis.sum()
    top["estadia_media"] = [estadia_media(ext[ext["pais"] == p]) for p in top.index]
    return top


def por_municipio(m: pd.DataFrame) -> pd.DataFrame:
    """Perfil de cada municipio: volumen mensual, estadia, % extranjeros y % turistas."""
    filas = []
    for mun in MUNICIPIOS:
        g = m[m["municipio"] == mun]
        if g.empty:
            continue
        k = kpis_demanda(g)
        filas.append({"municipio": mun, "visitantes_mes": k["visitantes_mes"], "dias_persona_mes": k["dias_persona_mes"],
                      "estadia_media": k["estadia_media"], "pct_extranjeros": k["pct_extranjeros"],
                      "pct_turistas": k["pct_turistas"]})
    return pd.DataFrame(filas).set_index("municipio")


# ---------------------------------------------------------------------------------------------
# Modulo 2


def serie_diaria(d: pd.DataFrame) -> pd.DataFrame:
    """Presencia diaria (dias sin cobertura quedan NaN) con su evento y dia de la semana."""
    d = d.assign(visitantes=pd.to_numeric(d["visitantes"], errors="coerce"))
    s = d.groupby("fecha").agg(visitantes=("visitantes", "sum"), evento=("evento", "first"))
    s = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="D"))
    s.index.name = "fecha"
    s["dia_semana"] = s.index.day_of_week.map(dict(enumerate(DIAS_SEMANA)))
    return s


def lift_eventos(diaria: pd.DataFrame) -> pd.DataFrame:
    """Lift = promedio diario del evento / promedio del dia regular - 1."""
    obs = diaria.dropna(subset=["visitantes"])
    regulares = obs[obs["evento"] == EVENTO_REGULAR]
    base = regulares["visitantes"].mean()
    # Lift ajustado: compara cada dia de evento con el dia regular promedio del MISMO dia de la
    # semana, para no confundir el efecto del feriado con el efecto del fin de semana.
    base_dia = regulares.groupby("dia_semana")["visitantes"].mean()
    eventos = obs[obs["evento"] != EVENTO_REGULAR].copy()
    eventos["rel"] = eventos["visitantes"].astype(float) / eventos["dia_semana"].map(base_dia).astype(float)
    ev = eventos.groupby("evento").agg(promedio_dia=("visitantes", "mean"), dias=("visitantes", "size"), rel=("rel", "mean"))
    ev["lift"] = ev["promedio_dia"] / base - 1
    ev["lift_ajustado"] = ev["rel"] - 1
    ev = ev.drop(columns="rel").sort_values("lift", ascending=False)
    ev.attrs["base_regular"] = float(base)
    return ev


def patron_semanal(diaria: pd.DataFrame, solo_regulares: bool = True) -> pd.DataFrame:
    obs = diaria.dropna(subset=["visitantes"])
    if solo_regulares:
        obs = obs[obs["evento"] == EVENTO_REGULAR]
    t = obs.groupby("dia_semana")["visitantes"].agg(["mean", "count"]).reindex(DIAS_SEMANA)
    t["indice"] = t["mean"] / t["mean"].mean() * 100
    return t.rename(columns={"mean": "promedio", "count": "dias"})


def presion_fin_de_semana(patron: pd.DataFrame) -> float:
    """Promedio sabado-domingo / promedio lunes-viernes."""
    return float(patron.loc[["Sábado", "Domingo"], "promedio"].mean() / patron.loc[DIAS_SEMANA[:5], "promedio"].mean())


# ---------------------------------------------------------------------------------------------
# Modulo 4: cuadrante de los municipios


def clasificar_municipios(perfil: pd.DataFrame) -> pd.DataFrame:
    """Ubica cada municipio en el cuadrante volumen x estadia (cortes en la mediana).

    - Hub comercial: volumen alto (puerta de entrada).
    - Larga estancia: volumen bajo/medio y estadia alta, mayoria extranjera.
    - Visita corta: estadia baja (excursiones de un dia desde otro municipio).
    Es una primera regla de trabajo; el modulo 4 la afinara con mas variables.
    """
    p = perfil.copy()
    corte_vol = p["visitantes_mes"].median()
    corte_est = p["estadia_media"].median()
    p["clase"] = np.select(
        [p["visitantes_mes"] >= p["visitantes_mes"].max() * 0.6,
         (p["estadia_media"] >= corte_est) & (p["pct_extranjeros"] >= 0.5),
         p["estadia_media"] < corte_est],
        ["Hub comercial", "Larga estancia", "Visita corta"],
        default="Intermedio",
    )
    p.attrs.update(corte_volumen=float(corte_vol), corte_estadia=float(corte_est))
    return p
