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


def _huella(ruta: Path) -> str:
    h = hashlib.sha256()
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
    for fuente, (tabla, limpiar) in TABLAS.items():
        ruta, origen = localizar(fuente, forzar_sinteticos)
        cfg = CONFIG["fuentes"][fuente]
        crudo = _leer_excel(ruta, cfg["hoja"]) if ruta.suffix.lower() in {".xlsx", ".xls"} else pd.read_csv(ruta)
        limpio = limpiar(crudo, rep)
        limpio.to_parquet(destino / f"{tabla}.parquet", index=False)
        rep.fuentes[fuente] = {
            "archivo": ruta.name, "origen": origen, "sha256": _huella(ruta), "filas_leidas": len(crudo),
            "filas_limpias": len(limpio), "tabla": f"{tabla}.parquet",
        }
    salida = {"generado": datetime.now().isoformat(timespec="seconds"), "fuentes": rep.fuentes,
              "controles": [asdict(c) for c in rep.controles]}
    (destino / "calidad.json").write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")
    return rep


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
