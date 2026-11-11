"""Calculos del modulo 4: red territorial y caracterizacion de los 10 municipios del lago.

Reto del grupo 3: distinguir puertas de entrada (hubs comerciales) de destinos de larga estancia y de
visita corta. Se combinan las dos bases de movilidad:
- mensual: volumen, estadia media ponderada, % extranjeros, % turistas con pernocta;
- diaria: presion de fin de semana y reaccion a festividades de cada pueblo.

La clasificacion se hace de dos formas independientes y se comparan:
1. Regla del cuadrante (interpretable, la que pide la guia).
2. k-medias (k = 3) sobre las variables estandarizadas, como contraste sin reglas fijas.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src import indicadores as ind
from src.normalizar import DIAS_SEMANA, MUNICIPIOS

CLASES = ["Hub comercial", "Larga estancia", "Visita corta"]

# Ubicacion aproximada de la cabecera de cada municipio (lat, lon), para el mapa de la portada
COORDENADAS = {
    "Panajachel": (14.7417, -91.1569),
    "Santa Catarina Palopó": (14.7206, -91.1347),
    "San Antonio Palopó": (14.6930, -91.1150),
    "San Lucas Tolimán": (14.6333, -91.1406),
    "Santiago Atitlán": (14.6378, -91.2297),
    "San Pedro La Laguna": (14.6928, -91.2717),
    "San Juan La Laguna": (14.6967, -91.2856),
    "San Pablo La Laguna": (14.7208, -91.2700),
    "San Marcos La Laguna": (14.7247, -91.2594),
    "Santa Cruz La Laguna": (14.7447, -91.2047),
}

# Contorno esquematico del lago (lat, lon), en sentido horario desde San Pablo. Es aproximado: sirve para
# ubicar los pueblos sin depender de mapas en linea (el tablero funciona sin internet).
CONTORNO_LAGO = [
    (14.724, -91.272), (14.728, -91.262), (14.735, -91.245), (14.742, -91.225), (14.746, -91.205),
    (14.746, -91.185), (14.743, -91.168), (14.740, -91.156), (14.731, -91.146), (14.720, -91.137),
    (14.706, -91.126), (14.692, -91.118), (14.678, -91.120), (14.664, -91.128), (14.650, -91.134),
    (14.636, -91.141), (14.640, -91.152), (14.655, -91.163), (14.666, -91.176), (14.669, -91.196),
    (14.661, -91.212), (14.647, -91.221), (14.636, -91.229), (14.643, -91.240), (14.659, -91.249),
    (14.675, -91.259), (14.690, -91.270), (14.696, -91.284), (14.708, -91.283), (14.717, -91.279),
]
VOLCANES = {"Volcán San Pedro": (14.656, -91.266), "Volcán Tolimán": (14.612, -91.189), "Volcán Atitlán": (14.583, -91.186)}
VARIABLES_KMEDIAS = {
    "log_volumen": "Volumen (log de visitantes/mes)",
    "estadia_media": "Estadía media ponderada",
    "pct_extranjeros": "% extranjeros",
    "presion_finde": "Presión de fin de semana",
}


def dinamica_diaria(d: pd.DataFrame) -> pd.DataFrame:
    """Por municipio: presion de fin de semana (dias regulares) y Lift de la festividad principal."""
    filas = []
    for mun in MUNICIPIOS:
        g = d[d["municipio"] == mun]
        if g.empty:
            continue
        serie = ind.serie_diaria(g)
        patron = ind.patron_semanal(serie, solo_regulares=True)
        lift = ind.lift_eventos(serie)
        filas.append({
            "municipio": mun,
            "presion_finde": ind.presion_fin_de_semana(patron),
            "lift_max": float(lift["lift"].max()) if len(lift) else float("nan"),
            "evento_max": lift["lift"].idxmax() if len(lift) else None,
            "lift_semana_santa": float(lift.loc["Semana Santa", "lift"]) if "Semana Santa" in lift.index else float("nan"),
            "presencia_dia": float(serie["visitantes"].mean()),
        })
    return pd.DataFrame(filas).set_index("municipio")


def perfil_completo(m: pd.DataFrame, d: pd.DataFrame) -> pd.DataFrame:
    p = ind.por_municipio(m).join(dinamica_diaria(d), how="left")
    p["pct_excursionistas"] = 1 - p["pct_turistas"]
    p["log_volumen"] = np.log10(p["visitantes_mes"])
    return p


def clasificar_regla(p: pd.DataFrame) -> pd.Series:
    """Regla del cuadrante (cortes en la mediana del lago):
    - Hub comercial: volumen >= 60 % del municipio mas visitado.
    - Larga estancia: estadia sobre la mediana y mayoria extranjera.
    - Visita corta: el resto (estadia baja o mayoria nacional de paso).
    """
    corte_est = p["estadia_media"].median()
    hub = p["visitantes_mes"] >= p["visitantes_mes"].max() * 0.6
    larga = (p["estadia_media"] >= corte_est) & (p["pct_extranjeros"] >= 0.5)
    return pd.Series(np.select([hub, larga], CLASES[:2], default=CLASES[2]), index=p.index, name="clase_regla")


def _kmedias(x: np.ndarray, k: int, semilla: int = 2026, intentos: int = 50, iteraciones: int = 100) -> np.ndarray:
    """k-medias de Lloyd con varios arranques; devuelve la etiqueta de cada fila (inercia minima)."""
    rng = np.random.default_rng(semilla)
    mejor, mejor_inercia = None, np.inf
    for _ in range(intentos):
        centros = x[rng.choice(len(x), size=k, replace=False)]
        for _ in range(iteraciones):
            dist = ((x[:, None, :] - centros[None, :, :]) ** 2).sum(axis=2)
            etiquetas = dist.argmin(axis=1)
            nuevos = np.array([x[etiquetas == j].mean(axis=0) if (etiquetas == j).any() else centros[j] for j in range(k)])
            if np.allclose(nuevos, centros):
                break
            centros = nuevos
        inercia = ((x - centros[etiquetas]) ** 2).sum()
        if inercia < mejor_inercia:
            mejor, mejor_inercia = etiquetas, inercia
    return mejor


def clasificar_kmedias(p: pd.DataFrame) -> pd.Series:
    """k-medias (k = 3) sobre variables estandarizadas. Cada grupo se nombra por su centroide:
    el de mayor volumen es el hub; de los otros dos, el de mayor estadia es larga estancia."""
    cols = list(VARIABLES_KMEDIAS)
    datos = p[cols].astype(float)
    datos = datos.fillna(datos.mean())
    z = ((datos - datos.mean()) / datos.std(ddof=0).replace(0, 1)).to_numpy()
    etiquetas = _kmedias(z, 3)
    centros = datos.groupby(etiquetas).mean()
    hub = centros["log_volumen"].idxmax()
    resto = centros.drop(index=hub)
    larga = resto["estadia_media"].idxmax()
    nombres = {hub: "Hub comercial", larga: "Larga estancia"}
    return pd.Series([nombres.get(e, "Visita corta") for e in etiquetas], index=p.index, name="clase_kmedias")


def clasificar(p: pd.DataFrame) -> pd.DataFrame:
    p = p.join(clasificar_regla(p)).join(clasificar_kmedias(p))
    p["coinciden"] = p["clase_regla"] == p["clase_kmedias"]
    p.attrs.update(corte_volumen=float(p["visitantes_mes"].median()), corte_estadia=float(p["estadia_media"].median()))
    return p


def perfil_por_clase(p: pd.DataFrame, columna: str = "clase_regla") -> pd.DataFrame:
    """Promedio simple de los indicadores de los municipios de cada clase (cada pueblo pesa igual)."""
    cols = ["visitantes_mes", "estadia_media", "pct_extranjeros", "pct_excursionistas", "presion_finde", "lift_max"]
    return p.groupby(columna)[cols].mean().reindex([c for c in CLASES if c in set(p[columna])])


def mercados_por_clase(m: pd.DataFrame, clases: pd.Series, n: int = 8) -> pd.DataFrame:
    """% de los visitantes extranjeros de cada clase que viene de cada pais (top n del lago)."""
    ext = m[m["origen"] == "Extranjero"].assign(clase=lambda x: x["municipio"].map(clases))
    top = ext.groupby("pais")["visitantes"].sum().nlargest(n).index
    t = ext.pivot_table(index="clase", columns="pais", values="visitantes", aggfunc="sum", fill_value=0)
    t = t.div(t.sum(axis=1), axis=0)
    t = t[list(top)].assign(**{"Otros": 1 - t[list(top)].sum(axis=1)})
    return t.reindex([c for c in CLASES if c in t.index])


def estacionalidad_por_clase(m: pd.DataFrame, clases: pd.Series) -> pd.DataFrame:
    """Indice mensual de visitantes de cada clase (promedio de los meses observados = 100).

    Es un indice de forma: aunque la suma de municipios de una clase duplique visitantes, el patron
    relativo entre meses se conserva."""
    t = (m.assign(clase=m["municipio"].map(clases))
         .pivot_table(index="periodo", columns="clase", values="visitantes", aggfunc="sum"))
    t = t.reindex(pd.date_range(t.index.min(), t.index.max(), freq="MS"))
    return (t / t.mean() * 100).reindex(columns=[c for c in CLASES if c in t.columns])


def huella_semanal(d: pd.DataFrame) -> pd.DataFrame:
    """Indice por dia de la semana de cada municipio (dias regulares, promedio semanal = 100)."""
    filas = {}
    for mun in MUNICIPIOS:
        g = d[d["municipio"] == mun]
        if g.empty:
            continue
        filas[mun] = ind.patron_semanal(ind.serie_diaria(g), solo_regulares=True)["indice"]
    return pd.DataFrame(filas).T.reindex(columns=DIAS_SEMANA)
