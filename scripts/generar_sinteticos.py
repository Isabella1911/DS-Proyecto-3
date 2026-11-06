"""Genera DATOS SINTETICOS con la misma estructura que las bases institucionales del grupo 3.

Las bases reales son confidenciales (clausula de la guia del proyecto). Para desarrollar y
presentar avances se usan tablas inventadas que respetan nombres de archivo, hojas, columnas,
tipos y hasta las inconsistencias de escritura observadas (mayusculas, abreviaturas, coma
decimal), para que la capa de normalizacion se pruebe con los mismos problemas.

NINGUNA CIFRA DE ESTOS ARCHIVOS ES REAL.

Uso:
    python scripts/generar_sinteticos.py              # escribe en data/sinteticos/
    python scripts/generar_sinteticos.py --salida X   # otra carpeta
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
SEMILLA = 2026
rng = np.random.default_rng(SEMILLA)

MESES_ABR = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# ---------------------------------------------------------------------------------------------
# Catalogos (inventados, con nombres plausibles)

# pais, region, region dos, region OMT, MCEO, agrupacion, peso en llegadas, vias posibles
PAISES_MIG = [
    ("El Salvador", "CENTROAMERICA", "Centroamérica", "AMERICA CENTRAL", "01 EL SALVADOR", "Centroamérica", 30, "T"),
    ("Honduras", "CENTROAMERICA", "Centroamérica", "AMERICA CENTRAL", "02 HONDURAS", "Centroamérica", 14, "T"),
    ("Estados Unidos", "NORTEAMERICA", "Norteamérica", "AMERICA DEL NORTE", "03 ESTADOS UNIDOS", "Estados Unidos", 26, "A"),
    ("México", "NORTEAMERICA", "Norteamérica", "AMERICA DEL NORTE", "04 MEXICO", "México", 9, "AT"),
    ("Canadá", "NORTEAMERICA", "Norteamérica", "AMERICA DEL NORTE", "05 CANADA", "Canadá", 2.5, "A"),
    ("Nicaragua", "CENTROAMERICA", "Centroamérica", "AMERICA CENTRAL", "06 NICARAGUA", "Centroamérica", 3, "T"),
    ("Costa Rica", "CENTROAMERICA", "Centroamérica", "AMERICA CENTRAL", "06 COSTA RICA", "Centroamérica", 1.6, "A"),
    ("Alemania", "EUROPA", "Europa", "EUROPA OCCIDENTAL", "07 EUROPA", "Europa", 1.4, "A"),
    ("España", "EUROPA", "Europa", "EUROPA MERIDIONAL", "07 EUROPA", "Europa", 1.6, "A"),
    ("Francia", "EUROPA", "Europa", "EUROPA OCCIDENTAL", "07 EUROPA", "Europa", 1.2, "A"),
    ("Italia", "EUROPA", "Europa", "EUROPA MERIDIONAL", "07 EUROPA", "Europa", 0.7, "A"),
    ("Reino Unido", "EUROPA", "Europa", "EUROPA SEPTENTRIONAL", "07 EUROPA", "Europa", 0.7, "A"),
    ("Países Bajos", "EUROPA", "Europa", "EUROPA OCCIDENTAL", "07 EUROPA", "Europa", 0.6, "A"),
    ("Colombia", "SUDAMERICA", "Sudamérica", "AMERICA DEL SUR", "08 OTROS", "Sudamérica", 1.3, "A"),
    ("Israel", "OTROS", "Asia", "ORIENTE MEDIO", "08 OTROS", "Resto del mundo", 0.5, "A"),
    ("Japón", "OTROS", "Asia", "ASIA NORDESTE", "08 OTROS", "Resto del mundo", 0.3, "A"),
    ("Australia", "OTROS", "Oceanía", "AUSTRALASIA", "08 OTROS", "Resto del mundo", 0.3, "A"),
    ("Albania", "OTROS EUROPEOS", "Europa", "EUROPA MERIDIONAL", "08 OTROS", "Europa", 0.02, "A"),
]
FRONTERAS = {
    "A": [("Aérea", "01 La Aurora", 0.93), ("Aérea", "09 Mundo Maya", 0.07)],
    "T": [("Terrestre", "02 Pedro de Alvarado", 0.35), ("Terrestre", "03 Tecún Umán", 0.25),
          ("Terrestre", "04 San Cristóbal", 0.25), ("Terrestre", "05 Agua Caliente", 0.15)],
}
# Perfil estacional de llegadas internacionales (indice, promedio 1)
ESTACIONAL_MIG = np.array([1.12, 1.02, 1.08, 1.04, 0.86, 0.92, 1.18, 1.02, 0.78, 0.86, 0.94, 1.18])

# (pais tal como aparece en telefonia, peso entre extranjeros del lago)
PAISES_TEL = [
    ("Estados Unidos", 34), ("Alemania", 8), ("Francia", 7), ("España", 6), ("Canadá", 6),
    ("México", 6), ("El Salvador", 5), ("Reino Unido", 4), ("Países Bajos", 4), ("Italia", 3),
    ("Israel", 3.5), ("Suiza", 2), ("Australia", 2), ("Bélgica", 1.5), ("Argentina", 1.5),
    ("Colombia", 1.5), ("Costa Rica", 1), ("Japón", 1), ("Corea del Sur", 0.8), ("Honduras", 1.2),
]

# Perfil de cada municipio: escritura en la base mensual y en la diaria, peso de volumen,
# fraccion extranjera, fraccion de turistas (> 1 dia), estadia media de los turistas.
MUNICIPIOS = [
    # mensual,              diaria,                  vol,  ext,  tur,  estadia
    ("Panajachel",          "PANAJACHEL",            1.00, 0.42, 0.62, 2.6),
    ("San Pedro La Laguna", "SAN PEDRO LA LAGUNA",   0.55, 0.66, 0.74, 4.6),
    ("San Marcos La Laguna", "SAN MARCOS",           0.22, 0.78, 0.80, 5.4),
    ("Santiago Atitlán",    "SANTIAGO ATITLAN",      0.48, 0.30, 0.38, 1.8),
    ("San Juan La Laguna",  "SAN JUAN LA LAGUNA",    0.30, 0.45, 0.40, 2.0),
    ("San Lucas Tolimán",   "SAN LUCAS TOLIMAN",     0.20, 0.12, 0.35, 2.1),
    ("Santa Cruz La Laguna", "SANTA CRUZ LA LAGUNA", 0.12, 0.60, 0.70, 3.9),
    ("Sta. Catarina Palopó", "SANTA CATARINA PALOPO", 0.14, 0.25, 0.22, 1.6),
    ("San Antonio Palopó",  "SN. ANTONIO PALOPO",    0.10, 0.20, 0.20, 1.5),
    ("San Pablo La Laguna", "SAN PABLO LA LAGUNA",   0.09, 0.15, 0.30, 2.2),
]


def pesos_municipio(ext: float, estadia: float) -> np.ndarray:
    """Mezcla de paises de cada pueblo: los de larga estancia atraen mas europeos e israelies; los de
    mayoria nacional, mas visitantes regionales (El Salvador, Mexico, Honduras)."""
    w = np.array([w for _, w in PAISES_TEL], dtype=float)
    nombres = [p for p, _ in PAISES_TEL]
    if estadia >= 3.5:
        for p, f in {"Israel": 3.0, "Alemania": 1.6, "Francia": 1.5, "Países Bajos": 1.6, "Suiza": 1.5}.items():
            w[nombres.index(p)] *= f
    if ext < 0.3:
        for p, f in {"El Salvador": 2.8, "México": 2.0, "Honduras": 2.5, "Costa Rica": 1.6}.items():
            w[nombres.index(p)] *= f
    return w / w.sum()

# Eventos (festividades) en la cobertura de la base diaria
EVENTOS: dict[date, tuple[str, float]] = {}


def _rango(inicio: date, fin: date, nombre: str, lift: float) -> None:
    d = inicio
    while d <= fin:
        EVENTOS[d] = (nombre, lift)
        d += timedelta(days=1)


_rango(date(2025, 4, 13), date(2025, 4, 20), "Semana Santa", 1.95)
_rango(date(2026, 3, 29), date(2026, 4, 5), "Semana Santa", 1.95)
_rango(date(2025, 5, 1), date(2025, 5, 1), "Día del Trabajo", 1.30)
_rango(date(2026, 5, 1), date(2026, 5, 1), "Día del Trabajo", 1.30)
_rango(date(2025, 6, 30), date(2025, 6, 30), "Día del Ejército", 1.15)
_rango(date(2026, 6, 30), date(2026, 6, 30), "Día del Ejército", 1.15)
_rango(date(2025, 9, 14), date(2025, 9, 15), "Independencia", 1.45)
_rango(date(2025, 10, 20), date(2025, 10, 20), "Día de la Revolución", 1.25)
_rango(date(2025, 11, 1), date(2025, 11, 2), "Todos los Santos", 1.35)
_rango(date(2025, 12, 24), date(2025, 12, 25), "Navidad", 1.30)
_rango(date(2025, 12, 31), date(2025, 12, 31), "Fin de Año", 1.60)
_rango(date(2026, 1, 1), date(2026, 1, 1), "Fin de Año", 1.60)

FACTOR_SEMANA = np.array([0.82, 0.80, 0.83, 0.88, 1.08, 1.45, 1.30])

# Coberturas de telefonia (ene-feb 2026 sin dato, regla del proyecto)
MESES_TEL = [(2025, m) for m in range(9, 13)] + [(2026, m) for m in range(3, 7)]
DIARIA_INICIO, DIARIA_FIN = date(2025, 3, 1), date(2026, 6, 30)
SIN_COBERTURA = {(2026, 1), (2026, 2)}


# ---------------------------------------------------------------------------------------------
# 1. Base de migracion


def migracion() -> pd.DataFrame:
    filas = []
    for anio in range(2019, 2027):
        nivel = {2019: 1.0, 2020: 0.30, 2021: 0.45, 2022: 0.78, 2023: 0.95, 2024: 1.03, 2025: 1.08, 2026: 1.12}[anio]
        for mes in range(1, 13):
            if anio == 2026 and mes > 6:
                break
            if anio == 2020 and mes >= 4:
                nivel_mes = 0.05 if mes <= 9 else 0.25
            else:
                nivel_mes = nivel
            base = 210_000 * nivel_mes * ESTACIONAL_MIG[mes - 1]
            for p, reg, reg2, omt, mceo, agr, peso, vias in PAISES_MIG:
                for clave_via in vias:
                    for via, frontera, f_peso in FRONTERAS[clave_via]:
                        total = base * peso / 100 * f_peso / len(vias) * rng.lognormal(0, 0.06)
                        frac_tur = 0.55 if via == "Terrestre" else 0.95
                        for tipo, frac in (("Turista", frac_tur), ("Excursionista", 1 - frac_tur)):
                            n = int(rng.poisson(max(total * frac, 0)))
                            if n == 0:
                                continue
                            filas.append((anio, mes, MESES_ABR[mes - 1], via, frontera, p, reg, reg2, omt, mceo, agr, tipo, n))
    return pd.DataFrame(filas, columns=[
        "Año", "Mes cod", "Mes", "Vía", "Frontera", "País", "Región", "Región dos", "Regiones OMT", "MCEO",
        "Agrupación Residencia", "Tipo de Viajero", "Viajero",
    ])


def llegadas_mensuales(mig: pd.DataFrame) -> pd.Series:
    vis = mig[mig["Tipo de Viajero"].isin(["Turista", "Excursionista"])]
    return vis.groupby(["Año", "Mes cod"])["Viajero"].sum()


# ---------------------------------------------------------------------------------------------
# 2. Movilidad mensual (telefonia, visitantes unicos del mes por municipio)


def movilidad_mensual(llegadas: pd.Series) -> pd.DataFrame:
    filas = []
    # Factor de reparto: fraccion de las llegadas internacionales que se detecta en el lago
    for (anio, mes) in MESES_TEL:
        m_nac = llegadas[(anio, mes)]
        fecha = pd.Timestamp(anio, mes, 1)
        estac_nac = {4: 1.35, 12: 1.30, 11: 1.05, 9: 1.10, 6: 0.95, 3: 1.15}.get(mes, 1.0)
        for nombre, _, vol, ext, tur, estadia in MUNICIPIOS:
            extranjeros = m_nac * 0.052 * vol * ext * rng.lognormal(0, 0.05)
            nacionales = 9_000 * vol * (1 - ext) * 1.6 * estac_nac * rng.lognormal(0, 0.06)
            pesos = pesos_municipio(ext, estadia)
            grupos = [(p, extranjeros * w) for (p, _), w in zip(PAISES_TEL, pesos)] + [("Guatemala", nacionales)]
            for p, total in grupos:
                for seg, frac in (("mayor a 1", tur), ("menor a 1", 1 - tur)):
                    v = int(rng.poisson(max(total * frac, 0)))
                    if v == 0:
                        continue
                    if seg == "mayor a 1":
                        dp = int(round(v * max(1.1, estadia * rng.lognormal(0, 0.12) * (1.15 if p != "Guatemala" else 0.75))))
                    else:
                        dp = v
                    perm = f"{dp / v:.2f}".replace(".", ",")
                    filas.append((nombre, "Lago Atitlán", anio, mes, p, seg, fecha, v, dp, perm))
    df = pd.DataFrame(filas, columns=[
        "destino", "sub_grupo", "anio", "mes", "pais", "es_consecutivo", "fecha", "visitantes", "dias_persona",
        "permanencia_prom",
    ])
    # Inconsistencias tipicas: espacios al final y mayusculas sueltas
    idx = rng.choice(len(df), size=len(df) // 25, replace=False)
    df.loc[idx, "destino"] = df.loc[idx, "destino"].str.upper() + " "
    idx = rng.choice(len(df), size=len(df) // 30, replace=False)
    df.loc[idx, "es_consecutivo"] = df.loc[idx, "es_consecutivo"].str.capitalize()
    return df


# ---------------------------------------------------------------------------------------------
# 3. Movilidad diaria (presencia por dia, municipio y pais)


def movilidad_diaria() -> pd.DataFrame:
    filas = []
    d = DIARIA_INICIO
    while d <= DIARIA_FIN:
        if (d.year, d.month) in SIN_COBERTURA:
            d += timedelta(days=1)
            continue
        ev, lift = EVENTOS.get(d, ("Regular", 1.0))
        dow = d.weekday()
        estac = ESTACIONAL_MIG[d.month - 1]
        for _, nombre, vol, ext, tur, estadia in MUNICIPIOS:
            pesos = pesos_municipio(ext, estadia)
            base = 2_600 * vol * rng.lognormal(0, 0.07)
            # El fin de semana pesa mas en los pueblos de visita corta (excursiones de nacionales)
            amp_nac = 0.6 + (1 - tur)
            semana_nac = 1 + (FACTOR_SEMANA[dow] - 1) * amp_nac
            semana_ext = 1 + (FACTOR_SEMANA[dow] - 1) * 0.3
            lift_ext = 1 + (lift - 1) * 0.35  # los extranjeros reaccionan menos a los feriados nacionales
            lift_nac = 1 + (lift - 1) * (0.6 + (1 - tur))
            ext_total = base * ext * estac * lift_ext * semana_ext
            nac_total = base * (1 - ext) * lift_nac * semana_nac
            grupos = [(p.upper(), ext_total * w) for (p, _), w in zip(PAISES_TEL, pesos)] + [("GUATEMALA", nac_total)]
            for p, total in grupos:
                n = int(rng.poisson(max(total, 0)))
                if n == 0:
                    continue
                filas.append((nombre, "LAGO ATITLAN", d.year, d.month, pd.Timestamp(d), DIAS[dow], p,
                              d.isocalendar()[1], ev, n))
        d += timedelta(days=1)
    return pd.DataFrame(filas, columns=[
        "destino", "sub_grupo", "anio", "mes", "idfecha", "dia_semana", "pais", "Week", "evento", "cantidad_visitantes",
    ])


# ---------------------------------------------------------------------------------------------
# 4. Indice de ocupacion mensual por departamento (2023-2025)

DEPTOS = {
    # nombre como viene escrito, ocupacion media, amplitud estacional
    "Sacatepéquez": (0.52, 0.12),
    "Petén": (0.44, 0.15),
    "Sololá": (0.41, 0.13),
    "Alta Verapaz": (0.30, 0.10),
    "Izabal": (0.36, 0.12),
    "Escuintla": (0.33, 0.14),
    "Santa Rosa": (0.25, 0.09),
}
ESTAC_OCUP = np.array([0.15, 0.05, 0.40, 0.75, -0.30, -0.15, 0.55, 0.30, -0.85, -0.55, -0.05, 0.70])


def ocupacion() -> pd.DataFrame:
    filas = []
    for anio in (2023, 2024, 2025):
        tendencia = {2023: -0.02, 2024: 0.0, 2025: 0.02}[anio]
        for mes in range(1, 13):
            for dep, (media, amp) in DEPTOS.items():
                v = media + tendencia + amp * ESTAC_OCUP[mes - 1] + rng.normal(0, 0.015)
                nombre = dep if rng.random() > 0.08 else dep.upper().replace("Á", "A").replace("É", "E")
                filas.append((anio, mes, nombre, round(float(np.clip(v, 0.05, 0.95)), 2)))
    return pd.DataFrame(filas, columns=["anio", "mes", "departamento", "indice_ocupacion"])


# ---------------------------------------------------------------------------------------------
# 5. Oferta hotelera (cortes anuales 2022-2025 en el cuarto trimestre; 2026 solo trimestre 1)

TIPOS_ALOJ = {"Hotel": (0.30, 18, 2.9), "Hospedaje": (0.45, 9, 2.6), "Hostal": (0.15, 8, 4.2), "Apartamento": (0.10, 3, 3.4)}
ESTABLECIMIENTOS_BASE = {"Sacatepéquez": 360, "Petén": 290, "Sololá": 330, "Alta Verapaz": 160, "Izabal": 190,
                         "Escuintla": 210, "Santa Rosa": 90}


def oferta() -> pd.DataFrame:
    filas = []
    previos: dict[tuple[str, str], tuple[int, int, int]] = {}
    cortes = [(2022, 4), (2023, 4), (2024, 4), (2025, 4), (2026, 1)]
    for i, (anio, trim) in enumerate(cortes):
        for dep, base in ESTABLECIMIENTOS_BASE.items():
            for tipo, (frac, hab_por, camas_por) in TIPOS_ALOJ.items():
                if anio == 2026 and rng.random() < 0.5 and (dep, tipo) in previos:
                    est, hab, camas = previos[(dep, tipo)]  # levantamiento parcial: repite el anio previo
                else:
                    crec = (1 + 0.035) ** i * rng.lognormal(0, 0.03)
                    est = int(round(base * frac * crec))
                    hab = int(round(est * hab_por * rng.lognormal(0, 0.04)))
                    camas = int(round(hab * camas_por / 1.0 * rng.lognormal(0, 0.03) / 1.2))
                previos[(dep, tipo)] = (est, hab, camas)
                filas.append((anio, trim, dep, tipo, est, hab, camas))
    return pd.DataFrame(filas, columns=["anio", "trimestre", "departamento", "tipo_alojamiento", "establecimientos",
                                        "habitaciones", "plazas_cama"])


# ---------------------------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--salida", type=Path, default=RAIZ / "data" / "sinteticos")
    args = ap.parse_args()
    out: Path = args.salida
    out.mkdir(parents=True, exist_ok=True)

    mig = migracion()
    llegadas = llegadas_mensuales(mig)
    mensual = movilidad_mensual(llegadas)
    diaria = movilidad_diaria()

    with pd.ExcelWriter(out / "Base_Migracion_2009-2026jun.xlsx") as xw:
        mig.to_excel(xw, sheet_name="Datos", index=False)
    with pd.ExcelWriter(out / "BD_movilidad_mensual.xlsx") as xw:
        mensual.to_excel(xw, sheet_name="Atitlan", index=False)
    with pd.ExcelWriter(out / "BD_movilidad_diaria.xlsx") as xw:
        diaria.to_excel(xw, sheet_name="Atitlan", index=False)
    ocupacion().to_csv(out / "indice_ocupacion_mensual_2023_2025_1.csv", index=False)
    oferta().to_csv(out / "oferta_hotelera_2022_2026.csv", index=False)
    (out / "LEEME.txt").write_text(
        "DATOS SINTETICOS generados por scripts/generar_sinteticos.py (semilla 2026).\n"
        "Tienen la estructura de las bases institucionales, pero NINGUNA cifra es real.\n",
        encoding="utf-8",
    )
    print(f"migracion {len(mig):,} filas | mensual {len(mensual):,} | diaria {len(diaria):,} -> {out}")


if __name__ == "__main__":
    main()
