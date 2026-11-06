"""Normalizacion de textos, numeros y fechas de las bases del observatorio.

Las bases llegan con escrituras distintas para lo mismo ("PANAJACHEL", "Panajachel ",
"Sta. Catarina", "SOLOLA", "2,55", fechas como texto o como numero de Excel). Todo pasa por
aqui antes de calcular cualquier indicador. Lo que no se reconoce no se descarta en silencio:
queda con su texto original (en formato titulo) y se anota en el reporte de calidad.
"""

from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------------------------
# Texto


def clave(texto: object) -> str:
    """Forma comparable de un texto: sin tildes, minusculas, sin puntuacion ni espacios extra.

    'Sta. Catarina  Palopó ' -> 'sta catarina palopo'
    """
    if texto is None or (isinstance(texto, float) and np.isnan(texto)):
        return ""
    s = unicodedata.normalize("NFKD", str(texto))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("_", " ")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _titulo(texto: object) -> str:
    s = re.sub(r"\s+", " ", str(texto)).strip()
    menores = {"de", "del", "la", "las", "los", "y", "a"}
    palabras = s.lower().split(" ")
    return " ".join(p if (i and p in menores) else p.capitalize() for i, p in enumerate(palabras))


# Abreviaturas frecuentes en las bases
_ABREV = [(r"\bsta\b", "santa"), (r"\bsto\b", "santo"), (r"\bsn\b", "san"), (r"\bstgo\b", "santiago")]


def _expandir(c: str) -> str:
    for patron, reemplazo in _ABREV:
        c = re.sub(patron, reemplazo, c)
    return c


# ---------------------------------------------------------------------------------------------
# Municipios del Lago de Atitlan (los 10 subdestinos del grupo 3)

MUNICIPIOS = [
    "Panajachel",
    "San Pedro La Laguna",
    "San Marcos La Laguna",
    "Santiago Atitlán",
    "San Juan La Laguna",
    "San Lucas Tolimán",
    "Santa Cruz La Laguna",
    "Santa Catarina Palopó",
    "San Antonio Palopó",
    "San Pablo La Laguna",
]
# Nombre corto para ejes y etiquetas
MUNICIPIO_CORTO = {
    "Panajachel": "Panajachel",
    "San Pedro La Laguna": "San Pedro",
    "San Marcos La Laguna": "San Marcos",
    "Santiago Atitlán": "Santiago",
    "San Juan La Laguna": "San Juan",
    "San Lucas Tolimán": "San Lucas",
    "Santa Cruz La Laguna": "Santa Cruz",
    "Santa Catarina Palopó": "Sta. Catarina",
    "San Antonio Palopó": "San Antonio",
    "San Pablo La Laguna": "San Pablo",
}
# Nucleo del nombre (sin el apellido "La Laguna", "Palopo", "Atitlan", "Toliman")
_NUCLEO_MUNICIPIO = {
    "panajachel": "Panajachel",
    "pana": "Panajachel",
    "san pedro": "San Pedro La Laguna",
    "san marcos": "San Marcos La Laguna",
    "santiago": "Santiago Atitlán",
    "san juan": "San Juan La Laguna",
    "san lucas": "San Lucas Tolimán",
    "santa cruz": "Santa Cruz La Laguna",
    "santa catarina": "Santa Catarina Palopó",
    "san antonio": "San Antonio Palopó",
    "san pablo": "San Pablo La Laguna",
}
_APELLIDOS = r"\b(la laguna|palopo|atitlan|toliman)\b"


def municipio(texto: object) -> str | None:
    """Nombre oficial del municipio o None si no se reconoce."""
    c = _expandir(clave(texto))
    c = re.sub(_APELLIDOS, "", c).strip()
    c = re.sub(r"\s+", " ", c)
    return _NUCLEO_MUNICIPIO.get(c)


# ---------------------------------------------------------------------------------------------
# Paises

_PAISES = {
    "guatemala": "Guatemala",
    "estados unidos": "Estados Unidos",
    "estados unidos de america": "Estados Unidos",
    "eeuu": "Estados Unidos",
    "usa": "Estados Unidos",
    "mexico": "México",
    "canada": "Canadá",
    "el salvador": "El Salvador",
    "honduras": "Honduras",
    "nicaragua": "Nicaragua",
    "costa rica": "Costa Rica",
    "panama": "Panamá",
    "belice": "Belice",
    "alemania": "Alemania",
    "francia": "Francia",
    "espana": "España",
    "italia": "Italia",
    "reino unido": "Reino Unido",
    "inglaterra": "Reino Unido",
    "paises bajos": "Países Bajos",
    "holanda": "Países Bajos",
    "belgica": "Bélgica",
    "suiza": "Suiza",
    "austria": "Austria",
    "suecia": "Suecia",
    "israel": "Israel",
    "japon": "Japón",
    "corea del sur": "Corea del Sur",
    "china": "China",
    "australia": "Australia",
    "argentina": "Argentina",
    "brasil": "Brasil",
    "chile": "Chile",
    "colombia": "Colombia",
    "peru": "Perú",
    "republica dominicana": "República Dominicana",
    "haiti": "Haití",
}


def pais(texto: object) -> str:
    c = clave(texto)
    if not c:
        return "Sin dato"
    return _PAISES.get(c, _titulo(texto))


# ---------------------------------------------------------------------------------------------
# Departamentos

_DEPARTAMENTOS = {
    "solola": "Sololá",
    "sacatepequez": "Sacatepéquez",
    "peten": "Petén",
    "alta verapaz": "Alta Verapaz",
    "baja verapaz": "Baja Verapaz",
    "izabal": "Izabal",
    "escuintla": "Escuintla",
    "santa rosa": "Santa Rosa",
    "guatemala": "Guatemala",
    "quetzaltenango": "Quetzaltenango",
    "huehuetenango": "Huehuetenango",
    "chimaltenango": "Chimaltenango",
    "quiche": "Quiché",
    "el quiche": "Quiché",
    "retalhuleu": "Retalhuleu",
    "suchitepequez": "Suchitepéquez",
    "san marcos": "San Marcos",
    "totonicapan": "Totonicapán",
    "zacapa": "Zacapa",
    "chiquimula": "Chiquimula",
    "jalapa": "Jalapa",
    "jutiapa": "Jutiapa",
    "el progreso": "El Progreso",
}


def departamento(texto: object) -> str:
    c = clave(texto)
    return _DEPARTAMENTOS.get(c, _titulo(texto) if c else "Sin dato")


# ---------------------------------------------------------------------------------------------
# Categorias de las bases de movilidad

SEG_TURISTA = "Turista (> 1 día)"
SEG_EXCURSIONISTA = "Excursionista (< 1 día)"


def segmento(texto: object) -> str | None:
    """'mayor a 1' -> turista con pernocta; 'menor a 1' -> excursionista."""
    c = clave(texto)
    if "mayor" in c or c.startswith(">"):
        return SEG_TURISTA
    if "menor" in c or c.startswith("<"):
        return SEG_EXCURSIONISTA
    return None


EVENTO_REGULAR = "Regular"


def evento(texto: object) -> str:
    c = clave(texto)
    if c in {"", "regular", "normal", "ninguno", "sin evento", "na", "nan", "none", "dia regular"}:
        return EVENTO_REGULAR
    return _titulo(texto)


DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def tipo_alojamiento(texto: object) -> str:
    c = clave(texto)
    return _titulo(texto) if c else "Sin dato"


# ---------------------------------------------------------------------------------------------
# Numeros y fechas


def numero(serie: pd.Series) -> pd.Series:
    """Convierte a numero aceptando coma decimal ('2,55'), espacios y celdas vacias.

    Si un texto trae punto y coma a la vez ('1.234,5') el punto se toma como separador de miles.
    """
    if pd.api.types.is_numeric_dtype(serie):
        return serie.astype(float)
    s = serie.astype("string").str.strip()
    ambos = s.str.contains(r"\.", regex=True) & s.str.contains(",", regex=False)
    s = s.where(~ambos, s.str.replace(".", "", regex=False))
    s = s.str.replace(",", ".", regex=False).str.replace(r"[^0-9.\-eE]", "", regex=True)
    return pd.to_numeric(s, errors="coerce").astype(float)


def fecha(serie: pd.Series) -> pd.Series:
    """Fechas como datetime, numero de serie de Excel o texto dia/mes/anio."""
    if pd.api.types.is_datetime64_any_dtype(serie):
        return serie.dt.normalize()
    num = pd.to_numeric(serie, errors="coerce")
    desde_excel = pd.to_datetime(num, unit="D", origin="1899-12-30", errors="coerce")
    texto = pd.to_datetime(serie.where(num.isna()).astype("string"), errors="coerce", dayfirst=True)
    return desde_excel.fillna(texto).dt.normalize()


def columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Nombres de columna en minusculas, sin tildes y con guion bajo ('Tipo de Viajero' -> 'tipo_de_viajero')."""
    return df.rename(columns=lambda c: clave(c).replace(" ", "_"))
