"""Revision de las bases antes de presentar: calidad, cobertura y las cifras de las lecturas.

Lo corre quien tenga las bases reales en data/raw (o en la carpeta de OBS_DATOS):

    python scripts/revisar_datos.py            # ETL + controles + cifras que usan los textos de lectura
    python scripts/revisar_datos.py --esquema  # solo columnas, tipos y filas de cada archivo de data/raw

La salida es solo agregada (conteos, promedios, nombres de categorias): se puede compartir con el
grupo sin romper la confidencialidad. Nunca imprime filas de las bases.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import pandas as pd  # noqa: E402

from src import etl, hallazgos  # noqa: E402
from src.normalizar import MUNICIPIO_CORTO  # noqa: E402

MES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def _titulo(texto: str) -> None:
    print(f"\n== {texto} " + "=" * max(0, 70 - len(texto)))


def _aviso(texto: str) -> None:
    print(f"  [REVISAR] {texto}")


def esquema() -> None:
    """Columnas, tipos y filas de cada archivo de la carpeta de datos (incluye fuentes opcionales)."""
    carpeta = etl._carpeta_datos()
    archivos = sorted(p for p in carpeta.iterdir() if p.suffix.lower() in {".xlsx", ".xls", ".csv", ".parquet"}
                      and not p.name.startswith("~$")) if carpeta.exists() else []
    if not archivos:
        print(f"No hay archivos en {carpeta}.")
        return
    for ruta in archivos:
        if ruta.suffix.lower() in {".xlsx", ".xls"}:
            hojas = pd.read_excel(ruta, sheet_name=None)
        elif ruta.suffix.lower() == ".csv":
            hojas = {"(csv)": pd.read_csv(ruta)}
        else:
            hojas = {"(parquet)": pd.read_parquet(ruta)}
        for hoja, df in hojas.items():
            _titulo(f"{ruta.name} / {hoja}: {len(df):,} filas")
            for c in df.columns:
                print(f"  {str(c):35} {str(df[c].dtype):12} {df[c].nunique():>8,} distintos  {df[c].isna().sum():>7,} vacios")


def calidad(rep: etl.Reporte) -> None:
    _titulo("Fuentes")
    for nombre, info in rep.fuentes.items():
        print(f"  {nombre:18} {info['origen']:9} {info['archivo']:45} {info['filas_leidas']:>8,} -> {info['filas_limpias']:>8,}")
    sint = [f for f, i in rep.fuentes.items() if i["origen"] == "sintetico"]
    if sint:
        _aviso(f"Estas fuentes siguen siendo sinteticas: {', '.join(sint)}. Coloque los reales en {etl._carpeta_datos()}.")
    _titulo("Controles con aviso o error (pagina Calidad de los datos)")
    malos = [c for c in rep.controles if c.estado != "ok"]
    for c in malos:
        print(f"  [{c.estado}] {c.fuente}: {c.control} ({c.filas} filas)\n          {c.detalle}")
    if not malos:
        print("  Ninguno.")
    _titulo("Cobertura")
    for c in rep.controles:
        if c.control.startswith("Cobertura"):
            print(f"  {c.fuente}: {c.detalle}")


def lecturas(r: dict) -> None:
    """Cifras que usan los textos de lectura, con avisos donde una frase podria no cuadrar."""
    corto = lambda x: MUNICIPIO_CORTO.get(x, x)  # noqa: E731
    dm, tp, ofe, te = r["demanda"], r["temporal"], r["oferta"], r["territorio"]

    _titulo("Modulo 1 - Demanda")
    print(f"  Visitantes por mes (suma de municipios): {dm['visitantes_mes']:,.0f} en {dm['meses']} meses")
    print(f"  Estadia media ponderada: {dm['estadia_media']:.2f} dias | extranjeros/mes {dm['extranjeros_mes']:,.0f} | "
          f"nacionales/mes {dm['nacionales_mes']:,.0f} | turistas con pernocta {dm['pct_turistas']:.0%}")
    print(f"  Mayor volumen: {corto(dm['mun_volumen'])} | estadia mas larga: {corto(dm['mun_estadia'])} "
          f"({dm['estadia_mun_max']:.1f} dias)")
    print(f"  Primer mercado extranjero: {dm['mercado_lider']} ({dm['pct_mercado_lider']:.0%}) | "
          f"estadia mas larga: {dm['mercado_estadia']} ({dm['estadia_mercado_max']:.1f} dias)")
    if dm["mun_volumen"] != "Panajachel":
        _aviso("Panajachel no es el municipio con mas visitantes: revise las frases que lo llaman 'puerta de entrada'.")

    _titulo("Modulo 2 - Dinamica temporal")
    print(f"  Festividad de mayor impacto: {tp['evento_top']} (Lift {tp['lift_top']:+.0%}, ajustado {tp['lift_ajustado_top']:+.0%})")
    print(f"  Festividades con Lift negativo: {', '.join(tp['eventos_negativos']) or 'ninguna'}")
    print(f"  Presion de fin de semana: {tp['presion_finde']:.2f}x | dia mas concurrido: {tp['dia_top']}")
    est = tp["estimados"]
    print(f"  Estimacion (metodo {tp['metodo']}): " + ", ".join(f"{MES[t.month - 1]} {t.year} = {v:,.0f}" for t, v in est.items()))
    print("  MAPE por metodo: " + ", ".join(f"{k} = {v:.1f} %" for k, v in tp["mape"].items()))
    if min(tp["mape"].values()) > 20:
        _aviso("El MAPE supera 20 %: presente la estimacion como orden de magnitud, no como cifra precisa.")
    pm = tp["perfil_meses"]
    if len(pm) == 2 and list(pm.values())[0] < list(pm.values())[1]:
        _aviso("En la migracion el primer mes estimado tiene MENOS llegadas que el segundo: revise la frase del perfil estacional.")

    _titulo("Modulo 3 - Oferta")
    if not ofe:
        _aviso("No hay oferta u ocupacion del departamento del destino.")
    else:
        crec = ofe["plazas1"] / ofe["plazas0"] - 1
        print(f"  Plazas cama {ofe['anio0']}: {ofe['plazas0']:,.0f} -> {ofe['anio1']}: {ofe['plazas1']:,.0f} ({crec:+.0%})")
        print(f"  Ocupacion promedio {ofe['anio_ocupacion']}: {ofe['ocupacion_prom']:.0%} (pico {MES[ofe['mes_pico'] - 1]}, "
              f"{ofe['ocupacion_pico']:.0%})")
        print(f"  Ventana coincidente: {ofe['meses_cruce']} meses | ocupacion oficial {ofe['ocupacion_oficial']:.0%}")
        print(f"  Captacion formal: extranjeros {ofe['captacion_ext']:.1%} (r = {ofe['correlacion_ext']:.2f}) | "
              f"nacionales {ofe['captacion_nac']:.1%} (r = {ofe['correlacion_nac']:.2f})")
        if ofe["captacion_ext"] != ofe["captacion_ext"]:
            _aviso("Sin boletines de ocupacion: el cruce de la ventana no tiene noches de hotel por residencia.")
    fr = r.get("frontera") or {}
    if fr:
        print(f"  Encuesta en fronteras (ola {fr['ola']}, {fr['encuestas']:,}): hotel {fr['pct_hotel']:.0%} | "
              f"Airbnb {fr['pct_airbnb']:.0%} (entre olas {fr['airbnb_min']:.0%}-{fr['airbnb_max']:.0%}) | "
              f"{fr['puesto_top']} {fr['pct_puesto_top']:.0%}")
        if ofe["meses_cruce"] < 4:
            _aviso("La ventana coincidente tiene menos de 4 meses: revise ventana_coincidente en config/config.yaml.")

    _titulo("Modulo 4 - Red de municipios")
    for clase, mun in te["miembros"].items():
        print(f"  {clase:15} {', '.join(corto(x) for x in mun) or '-'}")
    print(f"  Regla y k-medias coinciden en {te['coinciden']} de {te['n']} | estabilidad de k-medias {te['estabilidad']:.0%}")
    if te["difieren"]:
        print(f"  Difieren: {', '.join(corto(x) for x in te['difieren'])}")
    pc = te["por_clase"]
    for clase, fila in pc.iterrows():
        print(f"  {clase:15} {fila['visitantes_mes']:>9,.0f} vis/mes  {fila['estadia_media']:.1f} dias  "
              f"IEE {fila['iee']:.2f}  {fila['pct_excursionistas']:.0%} exc  finde x{fila['presion_finde']:.2f}")
    print(f"  Mayor especializacion extranjera: {corto(te['mun_iee'])} (IEE {te['iee_max']:.2f}, estadia "
          f"{te['estadia_mun_iee']:.1f} dias)")
    if {"Visita corta", "Larga estancia"} <= set(pc.index) and \
            pc.loc["Visita corta", "presion_finde"] <= pc.loc["Larga estancia", "presion_finde"]:
        print("  (info) Visita corta no depende mas del fin de semana que larga estancia; el texto del modulo 4 lo atribuye a los hubs.")
    if te["estabilidad"] < 0.8:
        _aviso("k-medias cambia de clase al quitar un municipio en mas del 20 % de los casos: presentelo solo como contraste.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Revision de las bases del observatorio")
    ap.add_argument("--esquema", action="store_true", help="solo columnas, tipos y filas de los archivos de data/raw")
    args = ap.parse_args()
    if args.esquema:
        esquema()
        return
    rep = etl.ejecutar()
    calidad(rep)
    r = hallazgos.resumen(*hallazgos.cargar(etl.PROCESADOS), etl.CONFIG, **hallazgos.cargar_opcionales(etl.PROCESADOS))
    lecturas(r)
    print("\nSi aparece [REVISAR], ajuste el texto de la pagina indicada o la configuracion antes de presentar.")


if __name__ == "__main__":
    main()
