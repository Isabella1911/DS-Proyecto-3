"""ETL del observatorio: bases originales -> tablas limpias en parquet + reporte de calidad.

    python -m src.etl                 # usa data/raw y, si falta un archivo, data/sinteticos
    python -m src.etl --sinteticos    # fuerza los datos sinteticos

Cada fuente pasa por la capa de normalizacion (src/normalizar.py). El resultado queda en
data/procesados/: un parquet por tabla y `calidad.json` con los controles aplicados y el
origen de cada fuente (real o sintetico). El tablero solo lee esos parquet.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

from src import normalizar as nz

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = yaml.safe_load((RAIZ / "config" / "config.yaml").read_text(encoding="utf-8"))
PROCESADOS = RAIZ / CONFIG["rutas"]["procesados"]

ORIGEN_NACIONAL = "Nacional"
ORIGEN_EXTRANJERO = "Extranjero"


@dataclass
class Control:
    fuente: str
    control: str
    estado: str  # ok | aviso | error
    detalle: str
    filas: int = 0


@dataclass
class Reporte:
    controles: list[Control] = field(default_factory=list)
    fuentes: dict[str, dict] = field(default_factory=dict)

    def agregar(self, fuente: str, control: str, n_malas: int, detalle: str, grave: bool = False) -> None:
        estado = "ok" if n_malas == 0 else ("error" if grave else "aviso")
        self.controles.append(Control(fuente, control, estado, detalle, int(n_malas)))


# ---------------------------------------------------------------------------------------------
# Localizacion de archivos


def _carpeta_datos() -> Path:
    return Path(os.environ.get("OBS_DATOS", RAIZ / CONFIG["rutas"]["datos"]))


def localizar_todos(nombre: str) -> list[Path]:
    """Todos los archivos reales de una fuente opcional (p. ej. un boletin por anio); [] si no hay."""
    patron = CONFIG["fuentes"][nombre]["patron"]
    return sorted(p for p in _carpeta_datos().glob(patron) if p.is_file() and not p.name.startswith("~$"))


def localizar(nombre: str, forzar_sinteticos: bool = False) -> tuple[Path, str]:
    """Ruta del archivo de la fuente y si es 'real' o 'sintetico'."""
    patron = CONFIG["fuentes"][nombre]["patron"]
    candidatos: list[tuple[Path, str]] = []
    if not forzar_sinteticos:
        candidatos.append((_carpeta_datos(), "real"))
    candidatos.append((RAIZ / CONFIG["rutas"]["sinteticos"], "sintetico"))
    for carpeta, origen in candidatos:
        encontrados = sorted(p for p in carpeta.glob(patron) if not p.name.startswith("~$"))
        if encontrados:
            return encontrados[-1], origen
    raise FileNotFoundError(
        f"No se encontró '{patron}' en {_carpeta_datos()} ni en los datos sintéticos. "
        "Genere los sintéticos con: python scripts/generar_sinteticos.py"
    )


def _huella(*rutas: Path) -> str:
    h = hashlib.sha256()
    for ruta in rutas:
        with ruta.open("rb") as f:
            for bloque in iter(lambda: f.read(1 << 20), b""):
                h.update(bloque)
    return h.hexdigest()[:16]


def _leer_excel(ruta: Path, hoja: str) -> pd.DataFrame:
    """Lee la hoja aunque su nombre cambie en tildes o mayusculas ('Atitlán', 'ATITLAN')."""
    hojas = pd.ExcelFile(ruta).sheet_names
    elegida = next((h for h in hojas if nz.clave(h) == nz.clave(hoja)), None)
    if elegida is None:
        raise ValueError(f"{ruta.name}: no existe la hoja '{hoja}'. Hojas disponibles: {hojas}")
    return pd.read_excel(ruta, sheet_name=elegida)


def _exigir(df: pd.DataFrame, columnas: list[str], fuente: str) -> None:
    faltan = [c for c in columnas if c not in df.columns]
    if faltan:
        raise ValueError(f"{fuente}: faltan columnas {faltan}. Columnas leídas: {list(df.columns)}")


def _origen_pais(paises: pd.Series) -> pd.Series:
    nacional = nz.pais(CONFIG["pais_nacional"])
    return paises.eq(nacional).map({True: ORIGEN_NACIONAL, False: ORIGEN_EXTRANJERO})


# ---------------------------------------------------------------------------------------------
# Fuentes


def limpiar_migracion(crudo: pd.DataFrame, rep: Reporte) -> pd.DataFrame:
    f = "migracion"
    df = nz.columnas(crudo)
    _exigir(df, ["ano", "mes_cod", "tipo_de_viajero", "viajero"], f)
    out = pd.DataFrame({
        "anio": nz.numero(df["ano"]).astype("Int64"),
        "mes": nz.numero(df["mes_cod"]).astype("Int64"),
        "tipo": df["tipo_de_viajero"].map(lambda t: nz.clave(t).capitalize()),
        "viajeros": nz.numero(df["viajero"]),
    })
    nulos = out[["anio", "mes", "viajeros"]].isna().any(axis=1)
    rep.agregar(f, "Campos indispensables sin dato", nulos.sum(), "Filas sin año, mes o viajeros; se excluyen.")
    out = out[~nulos]
    rep.agregar(f, "Viajeros negativos", (out["viajeros"] < 0).sum(), "Un conteo no puede ser negativo.", grave=True)
    tipos = {nz.clave(t).capitalize() for t in CONFIG["estimacion"]["tipos_migracion"]}
    mensual = (
        out[out["tipo"].isin(tipos)]
        .groupby(["anio", "mes"], as_index=False)["viajeros"].sum()
        .rename(columns={"viajeros": "llegadas"})
    )
    mensual["periodo"] = pd.to_datetime(dict(year=mensual["anio"], month=mensual["mes"], day=1))
    return mensual.sort_values("periodo").reset_index(drop=True)


def limpiar_mensual(crudo: pd.DataFrame, rep: Reporte) -> pd.DataFrame:
    f = "movilidad_mensual"
    df = nz.columnas(crudo)
    _exigir(df, ["destino", "anio", "mes", "pais", "es_consecutivo", "visitantes", "dias_persona"], f)
    out = pd.DataFrame({
        "destino_original": df["destino"].astype("string").str.strip(),
        "municipio": df["destino"].map(nz.municipio),
        "anio": nz.numero(df["anio"]).astype("Int64"),
        "mes": nz.numero(df["mes"]).astype("Int64"),
        "pais": df["pais"].map(nz.pais),
        "segmento": df["es_consecutivo"].map(nz.segmento),
        "visitantes": nz.numero(df["visitantes"]),
        "dias_persona": nz.numero(df["dias_persona"]),
        "permanencia_fuente": nz.numero(df["permanencia_prom"]) if "permanencia_prom" in df else float("nan"),
    })
    desconocidos = out["municipio"].isna()
    rep.agregar(f, "Municipio no reconocido", desconocidos.sum(),
                "Nombres fuera de los 10 municipios: " + ", ".join(sorted(out.loc[desconocidos, "destino_original"].dropna().unique())[:8]))
    sin_seg = out["segmento"].isna()
    rep.agregar(f, "Segmento de estadía no reconocido", sin_seg.sum(), "Valores de es_consecutivo distintos de 'mayor a 1' / 'menor a 1'.")
    nulos = out[["anio", "mes", "visitantes", "dias_persona"]].isna().any(axis=1)
    rep.agregar(f, "Campos indispensables sin dato", nulos.sum(), "Filas sin año, mes, visitantes o días-persona; se excluyen.")
    out = out[~(desconocidos | sin_seg | nulos)].copy()

    rep.agregar(f, "Días-persona menores que visitantes", (out["dias_persona"] < out["visitantes"]).sum(),
                "Cada visitante aporta al menos un día.", grave=True)
    exc = out["segmento"] == nz.SEG_EXCURSIONISTA
    rep.agregar(f, "Excursionistas con permanencia distinta de 1", (exc & (out["dias_persona"] != out["visitantes"])).sum(),
                "Por definición, a los visitantes de < 24 h se les asigna permanencia 1.")
    calc = out["dias_persona"] / out["visitantes"]
    incons = (out["permanencia_fuente"] - calc).abs() > 0.05
    rep.agregar(f, "permanencia_prom no cuadra con días-persona / visitantes", incons.sum(),
                "Solo se usa como verificación; la estadía media se recalcula ponderada (nunca se promedia esta columna).")

    out["origen"] = _origen_pais(out["pais"])
    out["periodo"] = pd.to_datetime(dict(year=out["anio"], month=out["mes"], day=1))
    claves = ["municipio", "periodo", "pais", "segmento"]
    dup = out.duplicated(claves, keep=False)
    rep.agregar(f, "Filas repetidas para la misma combinación", dup.sum(),
                "Misma combinación municipio-mes-país-segmento en varias filas; se consolidan sumando.")
    out = out.groupby(claves + ["anio", "mes", "origen"], as_index=False)[["visitantes", "dias_persona"]].sum()
    meses = sorted(out["periodo"].dt.strftime("%Y-%m").unique())
    rep.agregar(f, "Cobertura mensual", 0, f"{len(meses)} meses con dato: {meses[0]} a {meses[-1]}. "
                f"Sin cobertura configurada: {', '.join(CONFIG['estimacion']['meses_sin_cobertura'])}.")
    return out.sort_values(claves).reset_index(drop=True)


def limpiar_diaria(crudo: pd.DataFrame, rep: Reporte) -> pd.DataFrame:
    f = "movilidad_diaria"
    df = nz.columnas(crudo)
    _exigir(df, ["destino", "idfecha", "pais", "evento", "cantidad_visitantes"], f)
    out = pd.DataFrame({
        "destino_original": df["destino"].astype("string").str.strip(),
        "municipio": df["destino"].map(nz.municipio),
        "fecha": nz.fecha(df["idfecha"]),
        "pais": df["pais"].map(nz.pais),
        "evento": df["evento"].map(nz.evento),
        "visitantes": nz.numero(df["cantidad_visitantes"]),
        "dia_fuente": df["dia_semana"].map(nz.clave) if "dia_semana" in df else "",
    })
    desconocidos = out["municipio"].isna()
    rep.agregar(f, "Municipio no reconocido", desconocidos.sum(),
                "Nombres fuera de los 10 municipios: " + ", ".join(sorted(out.loc[desconocidos, "destino_original"].dropna().unique())[:8]))
    nulos = out[["fecha", "visitantes"]].isna().any(axis=1)
    rep.agregar(f, "Fecha o visitantes sin dato", nulos.sum(), "Se excluyen.")
    out = out[~(desconocidos | nulos)].copy()
    out["dia_semana"] = out["fecha"].dt.day_of_week.map(dict(enumerate(nz.DIAS_SEMANA)))
    if "dia_semana" in df:
        distinto = out["dia_fuente"] != out["dia_semana"].map(nz.clave)
        rep.agregar(f, "dia_semana no coincide con la fecha", distinto.sum(), "Se usa el día calculado desde la fecha.")
    out["origen"] = _origen_pais(out["pais"])
    claves = ["municipio", "fecha", "pais"]
    # Un dia con dos eventos distintos para el mismo municipio seria una inconsistencia
    ev_dia = out.groupby(["municipio", "fecha"])["evento"].nunique()
    rep.agregar(f, "Días con más de un evento", (ev_dia > 1).sum(), "Se conserva el primer evento del día.")
    out = (
        out.groupby(claves + ["origen", "dia_semana"], as_index=False)
        .agg(visitantes=("visitantes", "sum"), evento=("evento", "first"))
    )
    out["anio"] = out["fecha"].dt.year
    out["mes"] = out["fecha"].dt.month
    eventos = sorted(e for e in out["evento"].unique() if e != nz.EVENTO_REGULAR)
    rep.agregar(f, "Cobertura diaria", 0, f"{out['fecha'].nunique()} días con dato, del {out['fecha'].min():%d/%m/%Y} "
                f"al {out['fecha'].max():%d/%m/%Y}. Eventos: {', '.join(eventos)}.")
    return out.sort_values(claves).reset_index(drop=True)


def limpiar_ocupacion(crudo: pd.DataFrame, rep: Reporte) -> pd.DataFrame:
    f = "ocupacion"
    df = nz.columnas(crudo)
    _exigir(df, ["anio", "mes", "departamento", "indice_ocupacion"], f)
    out = pd.DataFrame({
        "anio": nz.numero(df["anio"]).astype("Int64"),
        "mes": nz.numero(df["mes"]).astype("Int64"),
        "departamento": df["departamento"].map(nz.departamento),
        "ocupacion": nz.numero(df["indice_ocupacion"]),
    })
    nulos = out.isna().any(axis=1)
    rep.agregar(f, "Campos sin dato", nulos.sum(), "Se excluyen; un mes sin dato nunca se toma como 0 %.")
    out = out[~nulos].copy()
    en_porcentaje = out["ocupacion"] > 1
    rep.agregar(f, "Índice expresado en porcentaje", en_porcentaje.sum(), "Valores > 1 se dividen entre 100.")
    out.loc[en_porcentaje, "ocupacion"] /= 100
    rep.agregar(f, "Índice fuera de 0-1", (~out["ocupacion"].between(0, 1)).sum(), "Revisar en la fuente.", grave=True)
    out["periodo"] = pd.to_datetime(dict(year=out["anio"], month=out["mes"], day=1))
    return out.sort_values(["departamento", "periodo"]).reset_index(drop=True)


def limpiar_oferta(crudo: pd.DataFrame, rep: Reporte) -> pd.DataFrame:
    f = "oferta"
    df = nz.columnas(crudo)
    _exigir(df, ["anio", "trimestre", "departamento", "tipo_alojamiento", "establecimientos", "habitaciones", "plazas_cama"], f)
    out = pd.DataFrame({
        "anio": nz.numero(df["anio"]).astype("Int64"),
        "trimestre": nz.numero(df["trimestre"]).astype("Int64"),
        "departamento": df["departamento"].map(nz.departamento),
        "tipo_alojamiento": df["tipo_alojamiento"].map(nz.tipo_alojamiento),
        "establecimientos": nz.numero(df["establecimientos"]),
        "habitaciones": nz.numero(df["habitaciones"]),
        "plazas_cama": nz.numero(df["plazas_cama"]),
    })
    out = out.dropna(subset=["anio", "trimestre"])
    ultimo_trim = out.groupby("anio")["trimestre"].transform("max")
    out["corte_parcial"] = ultimo_trim < 4
    # Repite exactamente el valor del corte anterior (levantamiento parcial de 2026)
    out = out.sort_values(["departamento", "tipo_alojamiento", "anio"])
    medidas = ["establecimientos", "habitaciones", "plazas_cama"]
    previo = out.groupby(["departamento", "tipo_alojamiento"])[medidas].shift()
    out["repite_previo"] = (out[medidas] == previo).all(axis=1)
    rep_parcial = out[out["corte_parcial"]]
    if len(rep_parcial):
        rep.agregar(f, "Corte parcial con valores repetidos", int(rep_parcial["repite_previo"].sum()),
                    f"{rep_parcial['repite_previo'].mean():.0%} de las combinaciones del corte "
                    f"{int(rep_parcial['anio'].iloc[0])}-T{int(rep_parcial['trimestre'].iloc[0])} repiten el valor del año previo.")
    return out.reset_index(drop=True)


# ---------------------------------------------------------------------------------------------
# Fuentes opcionales

MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
            "noviembre", "diciembre"]
COLUMNAS_BOLETIN = ["hab_residentes", "huespedes_residentes", "noches_residentes", "hab_no_residentes",
                    "huespedes_no_residentes", "noches_no_residentes", "hab_total", "ocupacion"]
_MES_PAGINA = re.compile(r"\b(" + "|".join(MESES_ES) + r")\b[\s\-]*(?:de\s+|del\s+)?(\d{4})", re.IGNORECASE)
_NUMERO = re.compile(r"\d[\d,]*%?")


def leer_boletin(ruta: Path, departamento: str) -> list[dict]:
    """Movimiento hotelero mensual de un departamento en un boletin anual (PDF).

    Se leen solo las paginas 'Movimiento hotelero ... residentes y no residentes' de un mes (se
    descartan los acumulados) y el renglon del departamento, que debe traer exactamente 8 cifras:
    habitaciones, huespedes y noches de residentes y de no residentes, habitaciones totales e indice.
    """
    import logging

    from pypdf import PdfReader  # import local: solo se necesita si existen los boletines

    logging.getLogger("pypdf").setLevel(logging.ERROR)  # avisos de texto rotado en graficas, irrelevantes aqui

    filas = []
    for pagina in PdfReader(str(ruta)).pages:
        texto = pagina.extract_text(extraction_mode="layout") or ""
        plano = re.sub(r"\s+", " ", texto).lower()
        encabezado = re.sub(r"\s+", " ", " ".join(texto.splitlines()[:12])).lower()
        if "movimiento hotelero" not in plano or "acumulado" in encabezado:
            continue
        mes = _MES_PAGINA.search(texto)
        if not mes:
            continue
        for linea in texto.splitlines():
            nombre = re.split(r"\d", linea, maxsplit=1)[0].split(",")[0].strip()
            if not nombre or nz.departamento(nombre) != departamento:
                continue
            cifras = _NUMERO.findall(linea[len(re.split(r"\d", linea, maxsplit=1)[0]):])
            if len(cifras) != 8 or not cifras[-1].endswith("%"):
                continue
            valores = [float(c.replace(",", "").rstrip("%")) for c in cifras]
            valores[-1] /= 100
            filas.append({"anio": int(mes.group(2)), "mes": MESES_ES.index(mes.group(1).lower()) + 1,
                          "departamento": departamento, **dict(zip(COLUMNAS_BOLETIN, valores)), "archivo": ruta.name})
            break
    return filas


def limpiar_boletines(rutas: list[Path], ocupacion: pd.DataFrame, rep: Reporte) -> pd.DataFrame:
    f = "boletines"
    depto = nz.departamento(CONFIG["destino"]["departamento"])
    filas = [fila for ruta in rutas for fila in leer_boletin(ruta, depto)]
    out = pd.DataFrame(filas, columns=["anio", "mes", "departamento", *COLUMNAS_BOLETIN, "archivo"])
    out = out.drop_duplicates(["anio", "mes"]).sort_values(["anio", "mes"]).reset_index(drop=True)
    out["periodo"] = pd.to_datetime(dict(year=out["anio"], month=out["mes"], day=1))
    esperados = 12 * len(rutas)  # un boletin anual por archivo
    rep.agregar(f, "Meses extraídos de los boletines", max(esperados - len(out), 0),
                f"{len(out)} meses de {depto} leídos de {len(rutas)} boletines "
                f"({out['periodo'].min():%m/%Y} a {out['periodo'].max():%m/%Y}).")
    suma = out[["hab_residentes", "hab_no_residentes"]].sum(axis=1)
    rep.agregar(f, "Habitaciones de residentes + no residentes distinta del total", (suma - out["hab_total"]).abs().gt(1).sum(),
                "Control aritmético de cada renglón extraído.", grave=True)
    o = ocupacion[ocupacion["departamento"] == depto].set_index("periodo")["ocupacion"]
    comp = out.set_index("periodo")["ocupacion"].to_frame("boletin").join(o.rename("csv"), how="inner")
    distintos = (comp["boletin"] - comp["csv"]).abs() > 0.011
    rep.agregar(f, "Ocupación del boletín distinta del CSV oficial", distintos.sum(),
                f"Se compararon {len(comp)} meses; {len(comp) - int(distintos.sum())} coinciden con el CSV (±1 punto). "
                "La ocupación del tablero sale siempre del CSV; el boletín aporta huéspedes y noches por residencia.")
    return out


def limpiar_frontera(crudo: pd.DataFrame, rep: Reporte) -> pd.DataFrame:
    """Agregados de la encuesta en fronteras para quienes declaran ir al lago (nunca microdatos)."""
    f = "frontera"
    _exigir(crudo, ["nuevo_destino", "BD", "hospedaje", "agrupacion_nombre", "nombre_frontera", "tipo_transporte", "noches"], f)
    destino = CONFIG["fuentes"]["frontera"]["destino_declarado"]
    s = crudo[crudo["nuevo_destino"].map(nz.clave) == nz.clave(destino)].copy()
    rep.agregar(f, "Encuestas con destino declarado al lago", 0,
                f"{len(s):,} de {len(crudo):,} encuestas declaran '{destino}'. Muestra por cuotas sin factor de "
                "expansión: solo se reportan porcentajes dentro del segmento.")
    nacional = nz.clave(CONFIG["pais_nacional"])
    s["origen"] = s["agrupacion_nombre"].map(lambda x: ORIGEN_NACIONAL if nz.clave(x) == nacional else ORIGEN_EXTRANJERO)
    s["noches_rango"] = pd.cut(pd.to_numeric(s["noches"], errors="coerce"), [-0.1, 1, 3, 7, 14, 30, 1000],
                               labels=["0-1", "2-3", "4-7", "8-14", "15-30", "31+"]).astype("string").fillna("Sin dato")
    claves = {"BD": "ola", "agrupacion_nombre": "residencia", "origen": "origen", "hospedaje": "hospedaje",
              "nombre_frontera": "puesto", "frontera_tipo": "tipo_puesto", "tipo_transporte": "transporte",
              "noches_rango": "noches_rango"}
    s["fecha"] = pd.to_datetime(s["fecha"], errors="coerce")
    out = (s[[*claves, "id_unico", "total_visitantes", "fecha"]].rename(columns=claves).groupby(list(claves.values()), dropna=False, as_index=False)
           .agg(encuestas=("id_unico", "size"), personas=("total_visitantes", "sum"),
                desde=("fecha", "min"), hasta=("fecha", "max")))
    olas = s.groupby("BD")["fecha"].agg(["min", "max", "size"])
    rep.agregar(f, "Olas de la encuesta", 0, "; ".join(f"{o}: {r['size']:,} encuestas ({r['min']:%m/%Y}–{r['max']:%m/%Y})"
                                                       for o, r in olas.iterrows()))
    return out


OPCIONALES = {"boletines": "boletin_hotelero", "frontera": "frontera_destino"}


def _ejecutar_opcionales(destino: Path, rep: Reporte, ocupacion: pd.DataFrame, forzar_sinteticos: bool) -> None:
    for fuente, tabla in OPCIONALES.items():
        salida = destino / f"{tabla}.parquet"
        rutas = [] if forzar_sinteticos else localizar_todos(fuente)
        if not rutas:
            salida.unlink(missing_ok=True)
            rep.fuentes[fuente] = {"archivo": "", "origen": "ausente", "sha256": "", "filas_leidas": 0,
                                   "filas_limpias": 0, "tabla": ""}
            continue
        if fuente == "boletines":
            limpio, leidas = limpiar_boletines(rutas, ocupacion, rep), len(rutas)
        else:
            crudo = pd.read_parquet(rutas[-1])
            limpio, leidas = limpiar_frontera(crudo, rep), len(crudo)
        limpio.to_parquet(salida, index=False)
        rep.fuentes[fuente] = {"archivo": ", ".join(r.name for r in rutas), "origen": "real", "sha256": _huella(*rutas),
                               "filas_leidas": leidas, "filas_limpias": len(limpio), "tabla": salida.name}


# ---------------------------------------------------------------------------------------------


TABLAS = {
    "migracion": ("migracion_mensual", limpiar_migracion),
    "movilidad_mensual": ("mensual", limpiar_mensual),
    "movilidad_diaria": ("diaria", limpiar_diaria),
    "ocupacion": ("ocupacion", limpiar_ocupacion),
    "oferta": ("oferta", limpiar_oferta),
}


def ejecutar(forzar_sinteticos: bool = False, destino: Path = PROCESADOS) -> Reporte:
    destino.mkdir(parents=True, exist_ok=True)
    rep = Reporte()
    limpias: dict[str, pd.DataFrame] = {}
    for fuente, (tabla, limpiar) in TABLAS.items():
        ruta, origen = localizar(fuente, forzar_sinteticos)
        cfg = CONFIG["fuentes"][fuente]
        crudo = _leer_excel(ruta, cfg["hoja"]) if ruta.suffix.lower() in {".xlsx", ".xls"} else pd.read_csv(ruta)
        limpio = limpiar(crudo, rep)
        limpias[fuente] = limpio
        limpio.to_parquet(destino / f"{tabla}.parquet", index=False)
        rep.fuentes[fuente] = {
            "archivo": ruta.name, "origen": origen, "sha256": _huella(ruta), "filas_leidas": len(crudo),
            "filas_limpias": len(limpio), "tabla": f"{tabla}.parquet",
        }
    _ejecutar_opcionales(destino, rep, limpias["ocupacion"], forzar_sinteticos)
    salida = {"generado": datetime.now().isoformat(timespec="seconds"), "fuentes": rep.fuentes,
              "controles": [asdict(c) for c in rep.controles]}
    (destino / "calidad.json").write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")
    return rep


def vigente(destino: Path = PROCESADOS) -> bool:
    """True si las tablas procesadas corresponden a los archivos de entrada actuales.

    Compara, fuente por fuente, el archivo que se usaria hoy (real o sintetico) y su huella con
    lo registrado en calidad.json. Asi, al colocar las bases reales en data/raw el tablero se
    reprocesa solo, en vez de seguir mostrando los sinteticos.
    """
    reporte = destino / "calidad.json"
    if not reporte.exists() or any(not (destino / f"{t}.parquet").exists() for t, _ in TABLAS.values()):
        return False
    previas = json.loads(reporte.read_text(encoding="utf-8")).get("fuentes", {})
    for fuente in TABLAS:
        try:
            ruta, origen = localizar(fuente)
        except FileNotFoundError:
            return False
        p = previas.get(fuente, {})
        if (p.get("archivo"), p.get("origen"), p.get("sha256")) != (ruta.name, origen, _huella(ruta)):
            return False
    for fuente in OPCIONALES:
        rutas = localizar_todos(fuente)
        actual = _huella(*rutas) if rutas else ""
        if previas.get(fuente, {}).get("sha256", "") != actual:
            return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="ETL del observatorio")
    ap.add_argument("--sinteticos", action="store_true", help="usar solo los datos sintéticos")
    args = ap.parse_args()
    rep = ejecutar(args.sinteticos)
    for nombre, info in rep.fuentes.items():
        print(f"{nombre:18} {info['origen']:9} {info['archivo']:45} {info['filas_leidas']:>7,} -> {info['filas_limpias']:>7,}")
    for c in rep.controles:
        if c.estado != "ok":
            print(f"  [{c.estado}] {c.fuente}: {c.control} ({c.filas})")


if __name__ == "__main__":
    main()
