"""Red territorial de los 10 municipios (modulo 4, reto del grupo 3).

Perfil de cada municipio con la base mensual (volumen, estadia, mezcla de origen y segmento) y la
diaria (presion de fin de semana, Lift de festividades). La clasificacion se hace de dos formas:

- Regla del cuadrante (interpretable), en este orden de prioridad:
    larga estancia = estadia media en el cuartil superior del lago (>= P75) y especializacion
                     extranjera >= 1 (atrae proporcionalmente mas extranjeros que el lago)
    hub comercial  = volumen >= 60 % del municipio con mas visitantes (puerta de entrada)
    visita corta   = el resto
  La permanencia va primero: un pueblo con mucho volumen y estadia excepcional es un destino de
  permanencia, no de paso.
- k-medias (k = 3) sobre log10(volumen), estadia, especializacion extranjera (IEE) y presion de fin
  de semana, estandarizadas (media 0, desviacion 1) para que ninguna pese mas por su unidad. Los
  grupos se nombran por su centro: el de mayor volumen es el hub, de los otros dos el de mayor
  estadia es larga estancia y el restante visita corta.

La participacion de extranjeros nunca se calcula como extranjeros / total (los nacionales traen
factor de expansion): se usa el IEE de src/indicadores.py.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src import indicadores as ind
from src.normalizar import DIAS_SEMANA, MUNICIPIOS

CLASES = ["Hub comercial", "Larga estancia", "Visita corta"]
VARIABLES_KMEDIAS = ["log_volumen", "estadia_media", "iee", "presion_finde"]
UMBRAL_HUB = 0.6
CUANTIL_ESTADIA = 0.75
UMBRAL_IEE = 1.0
SEMILLA = 42

# Cabecera de cada municipio (WGS84, aproximada) para el mapa del lago. Dato geografico publico.
COORDENADAS = {
    "Panajachel": (14.7400, -91.1580),
    "San Pedro La Laguna": (14.6930, -91.2720),
    "San Lucas Tolimán": (14.6330, -91.1410),
    "Santiago Atitlán": (14.6380, -91.2300),
    "San Juan La Laguna": (14.6950, -91.2860),
    "Santa Catarina Palopó": (14.7210, -91.1350),
    "San Antonio Palopó": (14.6930, -91.1170),
    "San Pablo La Laguna": (14.7230, -91.2700),
    "San Marcos La Laguna": (14.7240, -91.2590),
    "Santa Cruz La Laguna": (14.7460, -91.2070),
}


# ---------------------------------------------------------------------------------------------
# Perfil


def _dinamica_diaria(d_mun: pd.DataFrame) -> tuple[float, float]:
    """Presion de fin de semana y Lift maximo de festividad de un municipio."""
    if d_mun.empty:
        return float("nan"), float("nan")
    diaria = ind.serie_diaria(d_mun)
    presion = ind.presion_fin_de_semana(ind.patron_semanal(diaria))
    lift = ind.lift_eventos(diaria)
    return presion, (float(lift["lift"].max()) if len(lift) else float("nan"))


def perfil_completo(m: pd.DataFrame, d: pd.DataFrame) -> pd.DataFrame:
    """Un renglon por municipio con los indicadores del cuadrante y de la matriz de perfiles."""
    p = ind.por_municipio(m)
    p["pct_excursionistas"] = 1 - p["pct_turistas"]
    dinamica = {mun: _dinamica_diaria(d[d["municipio"] == mun]) for mun in p.index}
    p["presion_finde"] = [dinamica[mun][0] for mun in p.index]
    p["lift_max"] = [dinamica[mun][1] for mun in p.index]
    p["log_volumen"] = np.log10(p["visitantes_mes"].clip(lower=1))
    return p


# ---------------------------------------------------------------------------------------------
# Clasificacion


def cortes_regla(p: pd.DataFrame) -> dict:
    """Umbrales de la regla calculados con los municipios cargados (se muestran en el tablero)."""
    return {
        "volumen_hub": float(p["visitantes_mes"].max() * UMBRAL_HUB),
        "estadia_larga": float(p["estadia_media"].quantile(CUANTIL_ESTADIA)),
        "iee": UMBRAL_IEE,
        "mediana_volumen": float(p["visitantes_mes"].median()),
        "mediana_estadia": float(p["estadia_media"].median()),
    }


def clasificar_regla(p: pd.DataFrame) -> pd.Series:
    c = cortes_regla(p)
    larga = (p["estadia_media"] >= c["estadia_larga"]) & (p["iee"] >= c["iee"])
    hub = p["visitantes_mes"] >= c["volumen_hub"]
    clase = np.select([larga, hub], [CLASES[1], CLASES[0]], default=CLASES[2])
    return pd.Series(clase, index=p.index, name="clase_regla")


def _kmedias(x: np.ndarray, k: int, semilla: int = SEMILLA, n_inicios: int = 50, iteraciones: int = 100) -> np.ndarray:
    """k-medias con varios inicios aleatorios; devuelve la particion de menor inercia."""
    rng = np.random.default_rng(semilla)
    mejor, mejor_inercia = None, np.inf
    for _ in range(n_inicios):
        centros = x[rng.choice(len(x), size=k, replace=False)]
        for _ in range(iteraciones):
            etiquetas = ((x[:, None, :] - centros[None, :, :]) ** 2).sum(axis=2).argmin(axis=1)
            nuevos = np.array([x[etiquetas == j].mean(axis=0) if (etiquetas == j).any() else centros[j] for j in range(k)])
            if np.allclose(nuevos, centros):
                break
            centros = nuevos
        inercia = ((x - centros[etiquetas]) ** 2).sum()
        if inercia < mejor_inercia - 1e-12:
            mejor, mejor_inercia = etiquetas, inercia
    return mejor


def _nombrar(p: pd.DataFrame, etiquetas: np.ndarray) -> pd.Series:
    """Nombra cada grupo por su centro: mayor volumen = hub; de los demas, mayor estadia = larga estancia."""
    centros = p[VARIABLES_KMEDIAS].groupby(etiquetas).mean()
    nombres = {}
    hub = centros["log_volumen"].idxmax()
    nombres[hub] = CLASES[0]
    resto = centros.drop(index=hub).sort_values("estadia_media", ascending=False)
    for grupo, nombre in zip(resto.index, CLASES[1:]):
        nombres[grupo] = nombre
    return pd.Series([nombres[e] for e in etiquetas], index=p.index, name="clase_kmedias")


def clasificar_kmedias(p: pd.DataFrame, k: int = 3) -> pd.Series:
    x = p[VARIABLES_KMEDIAS].astype(float)
    x = x.fillna(x.mean())
    z = ((x - x.mean()) / x.std(ddof=0).replace(0, 1)).to_numpy()
    etiquetas = _kmedias(z, min(k, len(p)))
    return _nombrar(p, etiquetas)


def estabilidad_kmedias(p: pd.DataFrame) -> float:
    """Proporcion de municipios que conservan su clase al quitar, uno a la vez, a otro municipio.

    k-medias siempre devuelve k grupos aunque no existan; si la clase cambia al quitar un solo pueblo,
    el grupo no es solido. 1.0 = todas las asignaciones se mantienen en todas las corridas.
    """
    base = clasificar_kmedias(p)
    iguales, total = 0, 0
    for fuera in p.index:
        resto = p.drop(index=fuera)
        if len(resto) < 3:
            continue
        nueva = clasificar_kmedias(resto)
        iguales += int((nueva == base.drop(index=fuera)).sum())
        total += len(resto)
    return iguales / total if total else float("nan")


def clasificar(p: pd.DataFrame) -> pd.DataFrame:
    """Agrega la clase por regla, la de k-medias y si coinciden."""
    p = p.copy()
    p["clase_regla"] = clasificar_regla(p)
    p["clase_kmedias"] = clasificar_kmedias(p)
    p["coinciden"] = p["clase_regla"] == p["clase_kmedias"]
    p.attrs["estabilidad_kmedias"] = estabilidad_kmedias(p)
    return p


# ---------------------------------------------------------------------------------------------
# Comparaciones entre clases


def perfil_por_clase(p: pd.DataFrame, columna: str = "clase") -> pd.DataFrame:
    """Promedio simple de los municipios de cada clase (cada pueblo pesa igual)."""
    cols = ["visitantes_mes", "estadia_media", "iee", "pct_excursionistas", "presion_finde"]
    t = p.groupby(columna)[cols].mean()
    return t.reindex([c for c in CLASES if c in t.index])


def huella_semanal(d: pd.DataFrame) -> pd.DataFrame:
    """Indice de visitantes por dia de la semana de cada municipio (dias regulares, promedio = 100)."""
    filas = {}
    for mun in MUNICIPIOS:
        g = d[d["municipio"] == mun]
        if not g.empty:
            filas[mun] = ind.patron_semanal(ind.serie_diaria(g))["indice"]
    return pd.DataFrame(filas).T.reindex(columns=DIAS_SEMANA)


def mercados_por_clase(m: pd.DataFrame, clases: pd.Series, n: int = 8) -> pd.DataFrame:
    """Participacion de los n principales paises extranjeros del lago dentro de cada clase (resto en 'Otros')."""
    ext = m[m["origen"] == "Extranjero"].assign(clase=lambda x: x["municipio"].map(clases))
    top = ext.groupby("pais")["visitantes"].sum().nlargest(n).index
    t = ext.pivot_table(index="clase", columns="pais", values="visitantes", aggfunc="sum", fill_value=0)
    t = t.div(t.sum(axis=1), axis=0)
    out = t.reindex(columns=top, fill_value=0)
    out["Otros"] = 1 - out.sum(axis=1)
    return out.reindex([c for c in CLASES if c in out.index])


def estacionalidad_por_clase(m: pd.DataFrame, clases: pd.Series) -> pd.DataFrame:
    """Indice mensual de visitantes de cada clase (promedio de los meses observados = 100).

    Es un indice de forma: sumar municipios de una clase duplica visitantes, pero la relacion entre
    meses se conserva. Los meses sin cobertura quedan vacios.
    """
    series = {}
    for clase in CLASES:
        miembros = clases.index[clases == clase]
        if len(miembros):
            s = ind.serie_mensual(m[m["municipio"].isin(miembros)])
            series[clase] = s / s.mean() * 100
    return pd.DataFrame(series)
