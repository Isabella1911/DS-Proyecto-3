"""Genera la memoria tecnica (DOCX) con las cifras de los datos cargados.

    python scripts/generar_memoria.py

Todas las cifras salen de las tablas depuradas por el proceso de datos (las mismas del tablero). El
documento se construye directamente en Word (scripts/informe_docx.py) para controlar el ancho de cada
columna, el justificado y la numeracion de tablas y figuras. Solo contiene agregados, nunca microdatos.
Las figuras de Plotly requieren Chrome o Chromium (variable BROWSER_PATH si no esta en el PATH).
"""

from __future__ import annotations

import inspect
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from docx.shared import Cm  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from scripts.fichas_indicadores import fichas_informe  # noqa: E402
from scripts.informe_docx import Informe  # noqa: E402
from src import etl, hallazgos  # noqa: E402
from src import indicadores as ind  # noqa: E402
from src import oferta as of  # noqa: E402
from src import pronostico as pr  # noqa: E402
from src import territorio as te  # noqa: E402
from src.estilo import (  # noqa: E402
    COLOR_DESTACADO, COLOR_ESTIMADO, COLOR_EVENTO, COLOR_HISTORIA, COLOR_OCUPACION, COLOR_REAL, COLORES_CLASE,
    COLORES_ORIGEN, COLORES_SEGMENTO, contraste,
)
from src.graficas import fig_cruce_ventana, fig_cuadrante, fig_mensual_estimada  # noqa: E402
from src.normalizar import MUNICIPIO_CORTO, SEG_TURISTA, departamento  # noqa: E402

MEMORIA = RAIZ / "docs" / "memoria"
BUILD = MEMORIA / "_build"
SALIDA = MEMORIA / "Memoria_tecnica_Grupo3.docx"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]
MES_CORTO = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
EQUIPO = [
    "Anthony Lou Schwank (23410)",
    "Christa Isabella Obando Guzmán (23074)",
    "Fabian Prado Dluzniewski (23427)",
    "Luis Fernando Mendoza Alvarez (19644)",
]
F_TEL_M = "INGUAT, movilidad por telefonía móvil, base mensual (hoja Atitlan), septiembre de 2025 a agosto de 2026"
F_TEL_D = "INGUAT, movilidad por telefonía móvil, base diaria (hoja Atitlan)"
F_BOL = "INGUAT, boletines de ocupación hotelera 2023, 2024 y 2025"
F_OFE = "INGUAT, oferta hotelera 2022-2026 (cortes anuales)"
F_OCU = "INGUAT, índice de ocupación hotelera mensual 2023-2025"
F_FRO = "INGUAT, encuesta de perfil del visitante en puestos fronterizos (BD complementaria)"
F_MIG = "INGUAT, base de flujo migratorio 2009-2026"
EP = "Elaboración propia."

REGIONES = {"Estados Unidos": "Norteamérica", "Canadá": "Norteamérica", "México": "Norteamérica",
            "Costa Rica": "Centroamérica", "El Salvador": "Centroamérica", "Honduras": "Centroamérica",
            "Nicaragua": "Centroamérica", "Panamá": "Centroamérica", "Belice": "Centroamérica"}
EUROPA = {"Alemania", "Francia", "Italia", "España", "Países Bajos", "Austria", "Reino Unido", "Suiza", "Bélgica",
          "Suecia", "Dinamarca", "Noruega", "Portugal", "Irlanda", "Finlandia", "Polonia", "República Checa"}


# ---------------------------------------------------------------------------------------------
# Formato de cifras


def n0(x) -> str:
    return "Sin dato" if x is None or pd.isna(x) else f"{x:,.0f}"


def n1(x) -> str:
    return f"{x:,.1f}"


def n2(x) -> str:
    return f"{x:,.2f}"


def p0(x) -> str:
    return f"{x * 100:.0f}%"


def p1(x) -> str:
    return f"{x * 100:.1f}%"


def corto(m: str) -> str:
    return MUNICIPIO_CORTO.get(m, m)


def lista(items) -> str:
    items = list(items)
    if not items:
        return "ninguno"
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " y " + items[-1]


def categoria(texto: str) -> str:
    """'Hotel o Similares' -> 'Hotel o similares'; conserva marcas como Airbnb."""
    palabras = str(texto).split()
    return " ".join([palabras[0]] + [w if w in ("Airbnb",) else w.lower() for w in palabras[1:]]) if palabras else texto


def nombre_propio(texto: str) -> str:
    menores = {"de", "del", "la", "las", "los", "el", "y"}
    palabras = str(texto).lower().split()
    return " ".join(w if (i and w in menores) else w.capitalize() for i, w in enumerate(palabras))


# ---------------------------------------------------------------------------------------------
# Datos


def datos() -> dict:
    if not etl.vigente():
        etl.ejecutar()
    t = dict(zip(["mensual", "diaria", "migracion", "ocupacion", "oferta"], hallazgos.cargar(etl.PROCESADOS)))
    opc = hallazgos.cargar_opcionales(etl.PROCESADOS)
    r = hallazgos.resumen(t["mensual"], t["diaria"], t["migracion"], t["ocupacion"], t["oferta"], etl.CONFIG, **opc)
    cal = json.loads((etl.PROCESADOS / "calidad.json").read_text(encoding="utf-8"))
    m, d = t["mensual"], t["diaria"]
    depto = departamento(etl.CONFIG["destino"]["departamento"])
    v: dict = {"r": r, "t": t, "cal": cal, "depto": depto, "bol": opc["boletin"], "fro": opc["frontera_t"]}

    ext = m[m["origen"] == "Extranjero"].copy()
    ext["region"] = ext["pais"].map(lambda x: REGIONES.get(x, "Europa" if x in EUROPA else "Resto del mundo"))
    filas = {}
    for region, x in ext.groupby("region"):
        filas[region] = {"vis": x["visitantes"].sum(), "est": ind.estadia_media(x),
                         "pct_tur": x.loc[x["segmento"] == SEG_TURISTA, "visitantes"].sum() / x["visitantes"].sum()}
    reg = pd.DataFrame.from_dict(filas, orient="index")
    reg["share"] = reg["vis"] / reg["vis"].sum()
    v["regiones"] = reg.sort_values("share", ascending=False)
    v["est_ext"] = ind.estadia_media(m[m["origen"] == "Extranjero"])
    v["est_nac"] = ind.estadia_media(m[m["origen"] == "Nacional"])
    v["top"] = ind.top_paises(m, 10)
    v["n_paises"] = ext["pais"].nunique()
    serie = ind.serie_mensual(m)
    v["serie"] = serie
    obs = serie.dropna()
    v["mes_max"], v["mes_min"] = obs.idxmax(), obs.idxmin()

    diaria = ind.serie_diaria(d)
    v["lift"] = ind.lift_eventos(diaria)
    v["patron"] = ind.patron_semanal(diaria)
    faltantes = etl.CONFIG["estimacion"]["meses_sin_cobertura"]
    obs_c = serie.reindex(ind.calendario(serie.index, faltantes))
    res = {k: pr.estimar(obs_c, t["migracion"], faltantes, etl.CONFIG["estimacion"]["anios_perfil"], k) for k in pr.METODOS}
    v["est"], v["metodo"], v["obs_c"] = res, min(res, key=lambda k: res[k].mape), obs_c
    v["cons"] = pr.consistencia_diaria(obs_c, diaria, res[v["metodo"]].estimados)

    anual = of.capacidad_anual(of.capacidad(t["oferta"], depto))
    v["anual"] = anual
    oc = t["ocupacion"][t["ocupacion"]["departamento"] == depto]
    v["ocup_anual"] = oc.groupby("anio")["ocupacion"].mean()
    v["matriz"] = of.matriz_ocupacion(t["ocupacion"], depto)
    rank = t["ocupacion"][t["ocupacion"]["anio"] == oc["anio"].max()].groupby("departamento")["ocupacion"].mean()
    v["rank"] = (list(rank.sort_values(ascending=False).index).index(depto) + 1, len(rank))
    b = v["bol"]
    if b is not None:
        b = b.copy()
        b["hab_muestra"] = b["hab_total"] / b["ocupacion"] / b["periodo"].dt.days_in_month
        anio = b.groupby("anio").agg(hab_ocupadas=("hab_total", "sum"), hab_nores=("hab_no_residentes", "sum"),
                                     hues_res=("huespedes_residentes", "sum"), hues_nores=("huespedes_no_residentes", "sum"),
                                     noch_res=("noches_residentes", "sum"), noch_nores=("noches_no_residentes", "sum"),
                                     hab_muestra=("hab_muestra", "mean"))
        anio["inventario"] = anio.index.map(anual["habitaciones"])
        anio["cobertura"] = anio["hab_muestra"] / anio["inventario"]
        anio["ocup_inventario"] = anio["hab_ocupadas"] / (anio["inventario"] * 365)
        anio["ocup_publicada"] = anio.index.map(v["ocup_anual"])
        anio["pct_nores"] = anio["hab_nores"] / anio["hab_ocupadas"]
        v["bol_anual"] = anio
    ventana = tuple(pd.Timestamp(x + "-01") for x in etl.CONFIG["ventana_coincidente"])
    v["cruce"] = of.cruce_ventana(m, b, oc.set_index("periodo")["ocupacion"], ventana)
    v["rc"] = of.resumen_cruce(v["cruce"])

    f = v["fro"]
    if f is not None and not f.empty:
        ola = f.groupby("ola")["hasta"].max().idxmax()
        g = f[f["ola"] == ola]
        tot = g["encuestas"].sum()
        hosp = g.groupby("hospedaje")["encuestas"].sum().drop(index=["N/A"], errors="ignore")
        v["fro_ola"], v["fro_n"] = ola, int(tot)
        v["fro_periodo"] = (g["desde"].min(), g["hasta"].max())
        v["fro_hosp"] = (hosp / hosp.sum()).sort_values(ascending=False)
        v["fro_puesto"] = (g.groupby("puesto")["encuestas"].sum() / tot).sort_values(ascending=False)
        v["fro_transp"] = (g.groupby("transporte")["encuestas"].sum() / tot).sort_values(ascending=False)
        lm = g[g["puesto"] == v["fro_puesto"].index[0]]
        v["fro_bus_puesto"] = lm.loc[lm["transporte"].str.contains("Turístico", na=False), "encuestas"].sum() / lm["encuestas"].sum()
        olas = f.groupby("ola")["encuestas"].sum()
        air = f[f["hospedaje"].str.contains("Airbnb", na=False)].groupby("ola")["encuestas"].sum() / olas
        v["fro_air_rango"] = (air.min(), air.max())
        v["fro_total"] = int(cal["fuentes"].get("frontera", {}).get("filas_leidas", 0))
        v["fro_lago"] = int(f["encuestas"].sum())

    v["perfil"] = r["territorio"]["perfil"]
    v["huella"] = te.huella_semanal(d)
    mm = m.groupby(["municipio", "periodo"])["visitantes"].sum().unstack()
    v["amplitud"] = (mm.max(axis=1) / mm.min(axis=1)).sort_values()
    return v


# ---------------------------------------------------------------------------------------------
# Figuras


def _fuente_plex() -> str:
    for ttf in (RAIZ / "static" / "tipografia").glob("IBMPlexSans*.ttf"):
        font_manager.fontManager.addfont(str(ttf))
    return "IBM Plex Sans"


def _ejes(ax):
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color("#c6c6c6")
    ax.tick_params(colors="#525252", labelsize=9)
    ax.yaxis.grid(True, color="#e0e0e0", linewidth=0.8)
    ax.set_axisbelow(True)


def fig_arquitectura(ruta: Path) -> None:
    """Flujo en cuatro columnas: fuentes, proceso, tablas depuradas y tablero, sin cruces de flechas."""
    fig, ax = plt.subplots(figsize=(11, 6.4))
    ax.set_xlim(0, 113)
    ax.set_ylim(0, 67)
    ax.axis("off")

    def caja(x, y, w, h, texto, borde="#8d8d8d", fondo="#ffffff", negrita=False, tam=8.2):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.6", linewidth=1.1,
                                    edgecolor=borde, facecolor=fondo))
        ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=tam, color="#161616",
                fontweight="bold" if negrita else "normal", linespacing=1.25)

    def flecha(x0, y0, x1, y1):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", color="#6f6f6f", lw=0.9, shrinkA=0, shrinkB=0))

    for x, titulo in ((0, "Fuentes institucionales"), (33, "Proceso de datos"), (61, "Tablas depuradas"),
                      (91, "Tablero")):
        ax.text(x, 65, titulo, fontsize=10, fontweight="bold", color="#0d366b")
    fuentes = ["Telefonía, base mensual", "Telefonía, base diaria", "Flujo migratorio", "Índice de ocupación (CSV)",
               "Oferta hotelera (CSV)", "Boletines de ocupación (PDF)", "Encuesta en fronteras"]
    tablas = ["mensual", "diaria", "migracion_mensual", "ocupacion", "oferta", "boletin_hotelero", "frontera_destino"]
    for i, (fu, ta) in enumerate(zip(fuentes, tablas)):
        y = 55 - i * 8.2
        caja(0, y, 26, 6, fu, fondo="#f4f4f4")
        caja(61, y, 23, 6, ta + ".parquet", tam=7.6)
        flecha(26, y + 3, 33, 41)
        flecha(56, 24, 61, y + 3)
    caja(33, 35, 23, 12, "Normalización\nmunicipios, países,\ndecimales y fechas")
    caja(33, 17, 23, 12, "Controles de calidad\ny huella SHA-256\nde cada archivo", borde=COLOR_OCUPACION)
    flecha(44.5, 35, 44.5, 29)
    caja(33, 3, 23, 8, "Reporte de calidad\n(calidad.json)", tam=7.8, fondo="#f4f4f4")
    flecha(44.5, 17, 44.5, 11)
    modulos = ["1. Demanda y mercados", "2. Dinámica temporal\ny estimación", "3. Oferta de alojamiento",
               "4. Red de municipios", "Conclusiones,\ncalidad y método"]
    for i, mod in enumerate(modulos):
        y = 53 - i * 11.5
        caja(91, y, 22, 8, mod, borde=COLOR_DESTACADO, negrita=i < 4, tam=7.8)
        flecha(84, 31, 91, y + 4)
    fig.savefig(ruta, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig_ocupacion_inventario(v: dict, ruta: Path) -> None:
    a = v["bol_anual"]
    x = np.arange(len(a))
    fig, ax = plt.subplots(figsize=(9, 4.4))
    b1 = ax.bar(x - 0.19, a["ocup_publicada"], 0.36, color=COLOR_OCUPACION,
                label="Índice publicado (establecimientos que reportan)")
    b2 = ax.bar(x + 0.19, a["ocup_inventario"], 0.36, color="#9ec5f4", edgecolor="#256abf",
                label="Ocupación sobre el inventario registrado")
    for barras in (b1, b2):
        for rect in barras:
            ax.text(rect.get_x() + rect.get_width() / 2, rect.get_height() + 0.015, f"{rect.get_height() * 100:.0f}%",
                    ha="center", fontsize=9.5, color="#161616")
    ax.set_xticks(x, [f"{anio}\ncobertura del índice: {c * 100:.0f}%\ninventario: {inv:,.0f} habitaciones"
                      for anio, c, inv in zip(a.index, a["cobertura"], a["inventario"])])
    ax.tick_params(axis="x", labelsize=8.5)
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0, decimals=0))
    ax.set_ylabel("Habitaciones ocupadas", color="#525252", fontsize=9)
    _ejes(ax)
    ax.legend(frameon=False, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, 1.12), ncol=2)
    fig.savefig(ruta, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig_estacionalidad(v: dict, ruta: Path) -> None:
    mat = v["matriz"]
    med = mat.median()
    fig, ax = plt.subplots(figsize=(9, 3.6))
    colores = ["#9f1853" if mes in (10, 11) else ("#0d366b" if med[mes] >= 0.8 else "#898781") for mes in med.index]
    barras = ax.bar(range(12), med.values, color=colores, width=0.68, zorder=2)
    for rect, val in zip(barras, med.values):
        ax.text(rect.get_x() + rect.get_width() / 2, val + 0.02, f"{val * 100:.0f}%", ha="center", fontsize=8.5)
    for _, fila in mat.iterrows():
        ax.plot(range(12), fila.values, marker="o", ms=2.5, lw=0.8, color="#a8a8a8", zorder=3)
    ax.set_xticks(range(12), MES_CORTO)
    ax.set_ylim(0, 1.08)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0, decimals=0))
    _ejes(ax)
    fig.savefig(ruta, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def figuras(v: dict) -> dict[str, Path]:
    BUILD.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.family"] = _fuente_plex()
    out = {k: BUILD / f"{k}.png" for k in ("arquitectura", "inventario", "estacionalidad", "captacion", "cuadrante",
                                           "estimacion")}
    fig_arquitectura(out["arquitectura"])
    if "bol_anual" in v:
        fig_ocupacion_inventario(v, out["inventario"])
    fig_estacionalidad(v, out["estacionalidad"])
    perfil = v["perfil"].assign(clase=lambda x: x["clase_regla"])
    fig_cuadrante(perfil, None, v["r"]["territorio"]["cortes"]).update_layout(
        width=1000, height=520, paper_bgcolor="white").write_image(out["cuadrante"], scale=2)
    fig_mensual_estimada(v["obs_c"], v["est"][v["metodo"]].estimados).update_layout(
        width=1000, height=400, paper_bgcolor="white").write_image(out["estimacion"], scale=2)
    ext = v["cruce"][v["cruce"]["origen"] == "Extranjero"]
    if v["bol"] is not None and len(ext):
        fig_cruce_ventana(ext, "Noches por telefonía (turistas extranjeros)", "Noches en hotelería formal (no residentes)") \
            .update_layout(width=1000, height=400, paper_bgcolor="white").write_image(out["captacion"], scale=2)
    return out


# ---------------------------------------------------------------------------------------------
# Anexos


def arbol() -> str:
    archivos = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True).stdout.splitlines()
    archivos = sorted(a for a in set(archivos) | {"scripts/informe_docx.py", "scripts/fichas_indicadores.py"}
                      if not a.startswith("static/tipografia/"))
    grupos: dict[str, list[str]] = {}
    for a in archivos:
        carpeta, _, nombre = a.rpartition("/")
        grupos.setdefault(carpeta, []).append(nombre)
    lineas = []
    for carpeta in sorted(grupos, key=lambda c: (c != "", c)):
        if carpeta:
            lineas.append(carpeta + "/")
        lineas += [("    " if carpeta else "") + n for n in grupos[carpeta]]
    return "\n".join(lineas)


# ---------------------------------------------------------------------------------------------
# Documento


def redactar(v: dict, figs: dict[str, Path]) -> Informe:  # noqa: C901 - documento lineal
    r, inf = v["r"], Informe()
    dm, tp, tr = r["demanda"], r["temporal"], r["territorio"]
    p, cortes = v["perfil"], tr["cortes"]
    hub, larga = tr["miembros"].get("Hub comercial", []), tr["miembros"].get("Larga estancia", [])
    pc = tr["por_clase"]
    est = v["est"][v["metodo"]]
    otro = [k for k in v["est"] if k != v["metodo"]][0]
    lift, reg, ba, rc = v["lift"], v["regiones"], v.get("bol_anual"), v["rc"]
    cap_ext, cap_nac = rc.loc["Extranjero", "captacion"], rc.loc["Nacional", "captacion"]
    sl = "San Lucas Tolimán"
    sm = tr["mun_iee"]
    dom_sl = v["huella"].loc[sl, "Domingo"]
    puesto = nombre_propio(v["fro_puesto"].index[0])
    pct_air = v["fro_hosp"][[k for k in v["fro_hosp"].index if "Airbnb" in k]].sum()
    hab23, hab25 = v["anual"].loc[2023, "habitaciones"], v["anual"].loc[2025, "habitaciones"]
    eu, ca = reg.loc["Europa"], reg.loc["Centroamérica"]
    top_ev = lift["lift"].idxmax()
    med = v["matriz"].median()
    alta, baja = med[[1, 2, 3, 4, 5]].mean(), med[[10, 11]].mean()

    inf.ancla_indice()

    # ------------------------------------------------------------------------------ resumen
    inf.h1("Resumen ejecutivo")
    inf.p("El Instituto Guatemalteco de Turismo (INGUAT) requiere un observatorio de inteligencia turística para el Lago "
          "de Atitlán, un destino formado por diez municipios ribereños con funciones distintas dentro del sistema "
          "turístico de Sololá. Este informe documenta el observatorio construido, sus fuentes y sus métodos, y presenta "
          "los resultados de mayor utilidad para la gestión del destino.")
    inf.p(f"El análisis integra siete fuentes del INGUAT. La principal es la movilidad registrada por telefonía móvil, "
          f"disponible para {dm['meses']} meses entre septiembre de 2025 y agosto de 2026, que se cruzó con el flujo "
          "migratorio, el índice de ocupación hotelera, la oferta de alojamiento, los boletines anuales de ocupación y la "
          "encuesta de perfil del visitante en puestos fronterizos. Los tres primeros resultados solo son visibles al "
          "cruzar fuentes; los dos restantes caracterizan la demanda y su calendario.")
    if ba is not None:
        inf.recuadro(
            "1. El índice de ocupación publicado sobrestima el uso de la capacidad hotelera de Sololá",
            f"En 2025 el índice oficial promedió {p0(ba.loc[2025, 'ocup_publicada'])}. Los boletines del INGUAT registran "
            f"{n0(ba.loc[2025, 'hab_ocupadas'])} habitaciones-noche ocupadas en el año, que sobre las "
            f"{n0(ba.loc[2025, 'inventario'])} habitaciones del inventario equivalen a {p0(ba.loc[2025, 'ocup_inventario'])}. "
            f"La relación entre habitaciones ocupadas e índice implica que este se calcula sobre unas "
            f"{n0(ba.loc[2025, 'hab_muestra'])} habitaciones, el {p0(ba.loc[2025, 'cobertura'])} del inventario (frente al "
            f"{p0(ba.loc[2023, 'cobertura'])} en 2023). Entre 2023 y 2025 el inventario creció {p0(hab25 / hab23 - 1)} y las habitaciones ocupadas "
            f"{p0(ba.loc[2025, 'hab_ocupadas'] / ba.loc[2023, 'hab_ocupadas'] - 1)}.")
    inf.recuadro(
        "2. La hotelería formal registra la mayor parte del turismo extranjero y una fracción mínima del nacional",
        f"Entre septiembre y diciembre de 2025, los hoteles formales de Sololá registraron el {p0(cap_ext)} de las noches "
        f"que la telefonía mide para los turistas extranjeros en el lago y el {p1(cap_nac)} de las de los nacionales, aunque "
        f"los residentes ocupan el {p0(1 - ba.loc[2025, 'pct_nores'])} de las habitaciones formales. Las dos fuentes son "
        f"independientes y evolucionan en la misma dirección (r = {n2(rc.loc['Extranjero', 'correlacion'])} y "
        f"{n2(rc.loc['Nacional', 'correlacion'])}), lo que respalda la medición por telefonía.")
    inf.recuadro(
        "3. El lago funciona con dos puertas de entrada distintas y tres destinos de permanencia",
        f"Panajachel recibe el mayor número de visitantes extranjeros y San Lucas Tolimán es la puerta del visitante nacional: su "
        f"especialización extranjera es de {n2(p.loc[sl, 'iee'])} (lago = 1) y su domingo alcanza un índice de "
        f"{dom_sl:.0f}, la mayor presión puntual del destino. {lista([corto(x) for x in larga])} retienen "
        f"{n1(pc.loc['Larga estancia', 'estadia_media'])} días por turista frente a {n1(pc.loc['Hub comercial', 'estadia_media'])} "
        f"en los hubs. San Marcos La Laguna, con la mayor especialización extranjera ({n2(p.loc[sm, 'iee'])}), registra "
        f"{n1(p.loc[sm, 'estadia_media'])} días, por debajo de la mediana del lago.")
    inf.recuadro(
        "4. El valor del visitante extranjero depende del mercado y de la ruta de ingreso",
        f"Centroamérica aporta el {p0(ca['share'])} de los visitantes extranjeros, con {n1(ca['est'])} días de estadía y "
        f"{p0(ca['pct_tur'])} de pernocta; Europa, el {p0(eu['share'])}, con {n1(eu['est'])} días y {p0(eu['pct_tur'])} de "
        f"pernocta. De los viajeros encuestados en puestos fronterizos con destino al lago, el {p0(v['fro_puesto'].iloc[0])} "
        f"ingresa por {puesto} y, de ellos, el {p0(v['fro_bus_puesto'])} en bus turístico.")
    inf.recuadro(
        "5. La presión se concentra en pocos días y el año tiene dos temporadas marcadas",
        f"{top_ev} eleva la presencia diaria {lift.loc[top_ev, 'lift'] * 100:+.0f}% frente a un día regular; Semana Santa, "
        f"con veinte días observados, {lift.loc['Semana Santa', 'lift'] * 100:+.0f}%, y dos festividades la reducen. La "
        f"ocupación hotelera mediana es de {p0(alta)} entre enero y mayo y de {p0(baja)} en octubre y noviembre.")
    inf.h2("Estimación de enero y febrero de 2026")
    inf.p(f"Para los dos meses sin cobertura de telefonía, el perfil estacional del flujo migratorio escalado al nivel del "
          f"destino estima **{n0(est.estimados.iloc[0])}** visitantes en enero y **{n0(est.estimados.iloc[-1])}** en febrero "
          f"(suma de municipios), con un error porcentual absoluto medio (MAPE) de {est.mape:.1f}% en la validación cruzada "
          f"sobre {len(est.validacion)} meses. La presencia diaria implícita en la estimación coincide con el rango observado "
          "en la base diaria.")
    inf.h2("Recomendaciones prioritarias")
    inf.vinetas([
        "Publicar junto al índice de ocupación su cobertura y la ocupación sobre el inventario registrado, antes de usarlo "
        "para orientar inversiones o autorizar nueva capacidad.",
        "Establecer con las municipalidades un registro del alojamiento no formal, donde ocurre la mayor parte de las noches "
        "nacionales.",
        "Reforzar transporte lacustre, seguridad y servicios municipales en Panajachel y San Lucas Tolimán durante fines de "
        "semana y fin de año.",
        f"Orientar la promoción de estadías largas hacia {lista([corto(x) for x in larga])}, mercados europeos y "
        f"norteamericanos y el corredor terrestre de {puesto}.",
    ], numeradas=True)

    # ------------------------------------------------------------------------------ 1
    inf.h1("1. Introducción")
    inf.h2("1.1 Objetivo y alcance")
    inf.p("El observatorio permite al INGUAT seguir de forma continua la demanda, la temporalidad, la oferta de alojamiento "
          "y el comportamiento de cada municipio del Lago de Atitlán, con métodos reproducibles y cifras verificables. El "
          "ámbito comprende Panajachel, San Pedro La Laguna, San Lucas Tolimán, Santiago Atitlán, San Juan La Laguna, Santa "
          "Catarina Palopó, San Antonio Palopó, San Pablo La Laguna, San Marcos La Laguna y Santa Cruz La Laguna. La oferta "
          "y la ocupación hotelera se publican por departamento y corresponden a todo Sololá. Este documento contiene "
          "únicamente cifras agregadas.")
    inf.tabla("Preguntas de gestión y decisiones que apoya cada módulo del tablero",
              ["Módulo", "Pregunta de gestión", "Decisión que apoya"],
              [["1. Demanda y mercados", "¿Cuántos visitantes recibe el lago, cuánto permanecen y de dónde vienen?",
                "Priorización de mercados emisores"],
               ["2. Dinámica temporal", "¿Qué días concentran la afluencia y cuántos visitantes hubo en los meses sin dato?",
                "Planificación de servicios en picos"],
               ["3. Oferta de alojamiento", "¿Qué capacidad tiene Sololá, cuánto se usa y qué parte de las noches registra?",
                "Política de capacidad y de registro"],
               ["4. Red de municipios", "¿Qué función cumple cada municipio y qué implica para su gestión?",
                "Asignación territorial de recursos"]],
              [3.6, 7.6, 5.4], f"Guía del proyecto CC3084 y guía de uso de los datos del INGUAT. {EP}", resaltar_primera=True)

    # ------------------------------------------------------------------------------ 2
    inf.h1("2. Arquitectura y modelo de datos")
    inf.h2("2.1 Fuentes")
    inf.tabla("Fuentes de datos del observatorio", ["Fuente", "Archivo", "Granularidad", "Uso"], [
        ["Telefonía, base mensual", "BD_moviidad_mensual.xlsx, hoja Atitlan", "Municipio, mes, país y segmento", "Demanda, estadía y mercados"],
        ["Telefonía, base diaria", "BD_moviidad_diario.xlsx, hoja Atitlan", "Municipio, día y país, con evento", "Festividades, patrón semanal y verificación"],
        ["Flujo migratorio", "Base_Migracion_2009-2026jun.xlsx, hoja Datos", "Mes, país, vía y tipo de viajero", "Perfil estacional para la estimación"],
        ["Índice de ocupación", "indice_ocupacion_mensual_2023_2025_1.csv", "Departamento y mes", "Ocupación 2023 a 2025"],
        ["Oferta hotelera", "oferta_hotelera_2022_2026.csv", "Departamento, año y tipo", "Capacidad instalada"],
        ["Boletines de ocupación", "Boletines 2023, 2024 y 2025 (PDF)", "Departamento, mes y residencia", "Noches por residencia y cobertura del índice"],
        ["Encuesta en fronteras", "BD_COMPLEMENTARIA (parquet)", "Encuesta; se conservan solo agregados", "Alojamiento y puerta de ingreso declarados"]],
        [3.3, 5.0, 3.8, 4.5], f"INGUAT. {EP}", resaltar_primera=True)
    inf.p("Las encuestas de satisfacción y de residentes, y los registros del aeropuerto Mundo Maya y del Parque Nacional "
          "Tikal, corresponden a otros destinos según la guía de uso de los datos y no se utilizaron.")
    inf.h2("2.2 Relación entre las fuentes y proceso de datos")
    inf.p("Las fuentes no comparten un identificador y se relacionan por llaves de tiempo y territorio, después de "
          "normalizar textos, números y fechas. El mes une la telefonía con el flujo migratorio y con la ocupación; el "
          "municipio une las bases mensual y diaria; el departamento y el año unen la ocupación con la oferta; y el "
          "departamento, el mes y la residencia unen los boletines con la telefonía, de modo que los extranjeros se "
          "comparan con los huéspedes no residentes y los nacionales con los residentes. La encuesta en fronteras se filtra "
          "por el destino declarado.")
    inf.figura(figs["arquitectura"], "Flujo de datos del observatorio", EP)
    inf.p("Cada ejecución registra la huella SHA-256 de los archivos de entrada y el resultado de cada control de calidad; "
          "si un archivo cambia, el tablero lo vuelve a procesar. Los boletines en PDF se leen con código: se extrae el "
          "renglón de Sololá de las 36 tablas mensuales de movimiento hotelero, se verifica que contenga las ocho cifras "
          "esperadas y que las habitaciones de residentes y no residentes sumen el total. El índice de ocupación extraído "
          "coincide con el archivo oficial en los 36 meses.")
    nombres = {"migracion": "Flujo migratorio", "movilidad_mensual": "Telefonía, base mensual",
               "movilidad_diaria": "Telefonía, base diaria", "ocupacion": "Índice de ocupación",
               "oferta": "Oferta hotelera", "boletines": "Boletines (3 archivos PDF)", "frontera": "Encuesta en fronteras"}
    inf.tabla("Registros leídos y depurados por fuente", ["Fuente", "Registros leídos", "Registros depurados", "Tabla depurada"],
              [[nombres.get(k, k), n0(i["filas_leidas"]), n0(i["filas_limpias"]), i["tabla"]]
               for k, i in v["cal"]["fuentes"].items()],
              [4.6, 3.0, 3.2, 5.8], f"Reporte de calidad del proceso de datos. {EP}", numericas=(1, 2), resaltar_primera=True)
    avisos = [c for c in v["cal"]["controles"] if c["estado"] != "ok"]
    inf.p("Los controles no detectaron errores. " + ("El único aviso corresponde a la oferta hotelera: el corte de 2026 es "
          "parcial y " + avisos[0]["detalle"].split(" de las combinaciones")[0].lower() + " de las combinaciones del país "
          "repite el valor del año anterior." if avisos else ""))

    # ------------------------------------------------------------------------------ 3
    inf.h1("3. Catálogo formal de indicadores")
    inf.p("Cada indicador del tablero se documenta con una ficha de ocho campos: nombre, definición de negocio, fórmula, "
          "implementación en código, granularidad, unidad de medida, fuente y reglas de negocio. La tabla resume los 23 "
          "indicadores; las fichas completas están en el anexo A.")
    fichas = fichas_informe(MEMORIA / "fichas.md")
    inf.tabla("Catálogo de indicadores", ["Código", "Indicador", "Unidad", "Granularidad"],
              [[f["codigo"], f["nombre"], dict(f["campos"]).get("6. Unidad de medida", ""),
                dict(f["campos"]).get("5. Nivel de agregación y granularidad", "")] for f in fichas],
              [1.4, 6.2, 3.6, 5.4], EP)

    # ------------------------------------------------------------------------------ 4
    inf.h1("4. Diagnóstico del destino")
    inf.h2("4.1 Demanda y mercados emisores")
    inf.p(f"El lago recibe en promedio {n0(dm['visitantes_mes'])} visitantes por mes, medidos como suma de los diez "
          "municipios; la cifra es una cota superior, porque un visitante que recorre dos municipios se cuenta en ambos. De "
          f"ellos, {n0(dm['nacionales_mes'])} son nacionales y {n0(dm['extranjeros_mes'])} extranjeros, cifras que se reportan "
          f"por separado porque las nacionales incorporan un factor de expansión. El {p0(dm['pct_turistas'])} de los "
          f"visitantes pernocta. Los turistas nacionales permanecen {n1(v['est_nac'])} días y los extranjeros "
          f"{n1(v['est_ext'])}. La estadía corta de los extranjeros es consistente con un circuito que incluye otros destinos "
          "del país; buena parte de la presencia nacional con pernocta corresponde a estadías en viviendas de familiares o a presencia no "
          "turística que la telefonía no distingue.")
    inf.tabla("Visitantes extranjeros por región de procedencia", ["Región", "Participación", "Estadía media (días)", "Pernoctan"],
              [[k, p0(f["share"]), n2(f["est"]), p0(f["pct_tur"])] for k, f in reg.iterrows()],
              [5.2, 3.4, 4.2, 3.4], f"{F_TEL_M}. {EP}", numericas=(1, 2, 3), resaltar_primera=True)
    inf.p(f"La telefonía registra visitantes de {v['n_paises']} países. Estados Unidos es el primer mercado, con el "
          f"{p0(v['top']['pct'].iloc[0])} de los visitantes extranjeros. Centroamérica es el segundo bloque por volumen y el de "
          f"menor permanencia: un turista europeo permanece {eu['est'] / ca['est']:.1f} veces lo que uno centroamericano y la "
          f"proporción que pernocta es {eu['pct_tur'] / ca['pct_tur']:.1f} veces mayor. Para la promoción internacional, las "
          "noches generadas por mercado son un criterio de asignación más útil que el número de llegadas.")

    inf.h2("4.2 Temporalidad y efecto de las festividades")
    inf.p(f"La serie de telefonía alcanza su máximo en {MESES[v['mes_max'].month - 1]} de {v['mes_max'].year} "
          f"({n0(v['serie'].max())} visitantes) y su mínimo en {MESES[v['mes_min'].month - 1]} de {v['mes_min'].year} "
          f"({n0(v['serie'].min())}), una diferencia de {p0(v['serie'].max() / v['serie'].min() - 1)}. La ocupación hotelera, "
          "con tres años de historia, confirma una temporada alta de enero a mayo y una temporada baja en octubre y "
          "noviembre.")
    inf.figura(figs["estacionalidad"], "Ocupación hotelera mediana por mes en Sololá, 2023 a 2025",
               f"{F_OCU}. {EP} Barras: mediana de los tres años; líneas grises: cada año. El valor atípico de noviembre de "
               "2023 (20%) no altera la mediana.", ancho_cm=15.5)
    inf.tabla("Efecto de las festividades sobre la presencia diaria",
              ["Festividad", "Presencia media", "Lift simple", "Lift ajustado", "Días observados"],
              [[ev, n0(f["promedio_dia"]), f"{f['lift'] * 100:+.0f}%", f"{f['lift_ajustado'] * 100:+.0f}%", str(int(f["dias"]))]
               for ev, f in lift.iterrows()], [5.2, 3.0, 2.6, 2.8, 3.0],
              f"{F_TEL_D}. {EP} Día regular promedio: {n0(lift.attrs['base_regular'])} personas. El Lift ajustado compara cada "
              "día con el día regular del mismo día de la semana.", numericas=(1, 2, 3, 4), resaltar_primera=True)
    inf.p(f"Las festividades no actúan de forma uniforme. {top_ev} y los asuetos de octubre y junio concentran los mayores "
          f"incrementos; Semana Santa, pese a su duración, eleva la presencia {lift.loc['Semana Santa', 'lift'] * 100:.0f}%, y "
          f"el Festival de las Flores y el Día de los Santos la reducen. Los fines de semana reciben "
          f"{n2(tp['presion_finde'])} veces la presencia de un día hábil, con el sábado como día más concurrido.")

    inf.h2("4.3 Estimación de los meses sin cobertura")
    inf.p(f"Se compararon dos métodos basados en el flujo migratorio. El método A aplica a cada mes la proporción entre los "
          "visitantes del destino y las llegadas internacionales; el método B escala el perfil estacional de las llegadas de "
          f"2023 a 2025 al nivel observado del destino. Con validación dejando un mes fuera, el método {v['metodo']} obtuvo un "
          f"MAPE de {est.mape:.1f}% (MAE de {n0(est.mae)} y RMSE de {n0(est.rmse)} visitantes) y el método {otro}, de "
          f"{v['est'][otro].mape:.1f}%. La explicación más probable del error del método A es que las llegadas internacionales "
          "no describen al visitante nacional, que no se registra en migración y representa la mayor parte del flujo del "
          "lago.")
    inf.figura(figs["estimacion"], "Visitantes únicos por mes y estimación de enero y febrero de 2026",
               f"{F_TEL_M}; {F_MIG}. {EP} En violeta, la estimación.", ancho_cm=15.5)
    cons = v["cons"]
    inf.p(f"La estimación se verificó con la base diaria, que no se proyecta. La rotación mensual (visitantes únicos por "
          f"persona presente en un día promedio) es estable, {n1(cons.attrs['rotacion_media'])}, con una variación de "
          f"{p0(cons.attrs['rotacion_cv'])} entre meses, y la presencia diaria implícita en la estimación se ubica dentro "
          "del rango observado. Los feriados de enero y febrero se declaran ausentes.")

    inf.h2("4.4 Oferta de alojamiento y uso de la capacidad")
    if ba is not None:
        inf.tabla("Capacidad, habitaciones ocupadas y ocupación de Sololá, 2023 a 2025",
                  ["Año", "Estableci­mientos", "Habitaciones", "Habitaciones-noche ocupadas", "Índice publicado",
                   "Cobertura del índice", "Ocupación sobre inventario"],
                  [[str(a), n0(v["anual"].loc[a, "establecimientos"]), n0(ba.loc[a, "inventario"]), n0(ba.loc[a, "hab_ocupadas"]),
                    p0(ba.loc[a, "ocup_publicada"]), p0(ba.loc[a, "cobertura"]), p0(ba.loc[a, "ocup_inventario"])] for a in ba.index],
                  [1.3, 2.4, 2.3, 2.9, 2.4, 2.4, 2.9],
                  f"{F_OFE}; {F_BOL}; {F_OCU}. {EP} Cobertura del índice: habitaciones de los establecimientos que reportan "
                  "(habitaciones ocupadas ÷ índice ÷ días del mes, promedio del año) entre el inventario registrado.",
                  numericas=(1, 2, 3, 4, 5, 6))
        inf.figura(figs["inventario"], "Índice de ocupación publicado y ocupación sobre el inventario registrado",
                   f"{F_BOL}; {F_OFE}; {F_OCU}. {EP}", ancho_cm=15.0)
        inf.p(f"Los dos registros del INGUAT no son consistentes. El índice publicado se mantiene entre "
              f"{p0(ba['ocup_publicada'].min())} y {p0(ba['ocup_publicada'].max())}, mientras que la ocupación sobre el inventario "
              f"baja de {p0(ba.loc[2023, 'ocup_inventario'])} en 2023 a {p0(ba.loc[2025, 'ocup_inventario'])} en 2025. Las "
              "habitaciones implícitas en el índice pasaron de "
              f"{n0(ba.loc[2023, 'hab_muestra'])} a {n0(ba.loc[2025, 'hab_muestra'])}, mientras el inventario pasó de "
              f"{n0(ba.loc[2023, 'inventario'])} a {n0(ba.loc[2025, 'inventario'])}: la base del índice no creció al ritmo del "
              "inventario. Dos "
              "explicaciones posibles, que la muestra no incorpore los establecimientos nuevos o que el inventario incluya "
              "establecimientos inactivos, conducen a la misma conclusión: el índice publicado no debe usarse para "
              "dimensionar la capacidad del destino sin reportar su cobertura.")
        inf.p(f"Los residentes ocupan el {p0(1 - ba.loc[2025, 'pct_nores'])} de las habitaciones formales. Los huéspedes no "
              f"residentes permanecen {n2(ba.loc[2025, 'noch_nores'] / ba.loc[2025, 'hues_nores'])} noches y los residentes "
              f"{n2(ba.loc[2025, 'noch_res'] / ba.loc[2025, 'hues_res'])}. En 2025 Sololá ocupó el puesto {v['rank'][0]} de "
              f"{v['rank'][1]} departamentos por índice de ocupación.")
    inf.h3("Captación de noches por la hotelería formal")
    inf.tabla("Noches por telefonía y noches en hotelería formal, septiembre a diciembre de 2025",
              ["Mes", "Origen", "Noches por telefonía", "Noches en hotel formal", "Captación formal"],
              [[f"{MESES[f['periodo'].month - 1].capitalize()} {f['periodo'].year}",
                "Extranjeros" if f["origen"] == "Extranjero" else "Nacionales", n0(f["noches_telefonia"]),
                n0(f["noches_hotel"]), p1(f["captacion_formal"])] for _, f in v["cruce"].iterrows()],
              [3.4, 3.0, 3.6, 3.6, 3.0],
              f"{F_TEL_M}; {F_BOL}. {EP} Noches por telefonía: días-persona menos visitantes de los turistas con pernocta, "
              "suma de municipios. Extranjeros frente a no residentes; nacionales frente a residentes.", numericas=(2, 3, 4))
    inf.figura(figs["captacion"], "Noches de turistas extranjeros por fuente y captación formal, septiembre a diciembre de 2025",
               f"{F_TEL_M}; {F_BOL}. {EP}", ancho_cm=15.5)
    inf.p(f"La hotelería formal registró el {p0(cap_ext)} de las noches de los turistas extranjeros y el {p1(cap_nac)} de las "
          "de los nacionales. Como la telefonía se agrega por municipio, el denominador es una cota superior y la captación, "
          "una cota inferior. La ocupación oficial describe razonablemente al turismo extranjero; la presencia nacional con "
          "pernocta ocurre casi en su totalidad fuera del registro formal.")
    if "fro_hosp" in v:
        inf.h3("Alojamiento y puerta de ingreso declarados")
        filas = [["Alojamiento", categoria(k), p0(x)] for k, x in v["fro_hosp"].head(4).items()]
        filas += [["Puesto de ingreso", nombre_propio(k), p0(x)] for k, x in v["fro_puesto"].head(4).items()]
        filas += [["Medio de transporte", categoria(k), p0(x)] for k, x in v["fro_transp"].head(3).items()]
        a_ = v["fro_periodo"]
        inf.tabla(f"Perfil declarado de los viajeros con destino al lago, ola {v['fro_ola']}",
                  ["Variable", "Categoría", "Encuestados"], filas, [4.4, 8.2, 4.0],
                  f"{F_FRO}. {EP} Ola {v['fro_ola']}, {MESES[a_[0].month - 1]} de {a_[0].year} a {MESES[a_[1].month - 1]} de "
                  f"{a_[1].year}, {n0(v['fro_n'])} encuestas. Porcentajes muestrales, sin factor de expansión.",
                  numericas=(2,), resaltar_primera=True)
        inf.p(f"De las {n0(v['fro_total'])} encuestas de la base complementaria, {n0(v['fro_lago'])} declaran como destino el "
              f"lago. En la ola vigente, el {p0(pct_air)} declara alojarse en Airbnb o similar, una oferta que no figura en el "
              f"inventario hotelero. La proporción varía entre {p0(v['fro_air_rango'][0])} y {p0(v['fro_air_rango'][1])} según la "
              "ola, porque cambian las cuotas y los puestos encuestados, y no se interpreta como tendencia.")

    # ------------------------------------------------------------------------------ 5
    inf.h1("5. Análisis especializado: la red de municipios")
    inf.h2("5.1 Planteamiento")
    inf.p("El reto asignado consiste en distinguir los municipios que operan como puerta de entrada de los que retienen "
          "estadías largas. Para cada municipio se construyó un perfil con seis variables: visitantes por mes, estadía "
          "media ponderada, especialización extranjera y proporción de excursionistas, a partir de la base mensual, y "
          "presión de fin de semana y efecto máximo de las festividades, a partir de la base diaria.")
    inf.p("La asignación sugiere usar el porcentaje de extranjeros. La guía de uso de los datos señala que calcularlo como "
          "extranjeros entre el total es un error, porque las cifras nacionales incorporan un factor de expansión. En su "
          "lugar se usa el índice de especialización extranjera (IEE): la participación del municipio entre los extranjeros "
          "del lago dividida por su participación entre los nacionales. Un factor de expansión constante se cancela en el "
          "cociente, y el índice ordena a los municipios igual que la proporción de la fuente.")
    inf.h2("5.2 Método de clasificación")
    inf.p(f"La regla se aplica en orden. Un municipio es de larga estancia si su estadía está en el cuartil superior del "
          f"lago ({n2(cortes['estadia_larga'])} días o más) y su IEE es igual o mayor que 1; es hub si su volumen alcanza el "
          f"60% del municipio con más visitantes ({n0(cortes['volumen_hub'])} por mes); el resto es de visita corta. Una "
          "versión preliminar exigía mayoría extranjera para la larga estancia, pero ningún municipio supera el 15% de "
          "extranjeros en la fuente y la clase quedaba vacía.")
    inf.p(f"Como contraste se aplicó k-medias con tres grupos sobre el logaritmo del volumen, la estadía, el IEE y la "
          f"presión de fin de semana, estandarizados. Los métodos coinciden en {tr['coinciden']} de {tr['n']} municipios; al "
          f"excluir un municipio a la vez, el {p0(tr['estabilidad'])} de los restantes conserva su clase. k-medias separa "
          "sobre todo por niveles de volumen y difiere de la regla en los municipios intermedios. La regla es la "
          "clasificación de referencia porque se explica en una frase y se replica cada mes.")
    orden = p.sort_values("visitantes_mes", ascending=False)
    inf.tabla("Perfil y clasificación de los municipios",
              ["Municipio", "Visitantes por mes", "Estadía (días)", "IEE", "Excursio­nistas", "Fin de semana", "Regla",
               "k-medias"],
              [[corto(mun), n0(f["visitantes_mes"]), n2(f["estadia_media"]), n2(f["iee"]), p0(f["pct_excursionistas"]),
                n2(f["presion_finde"]), f["clase_regla"], f["clase_kmedias"]] for mun, f in orden.iterrows()],
              [2.5, 2.1, 1.7, 1.3, 2.0, 1.7, 2.6, 2.6],
              f"{F_TEL_M}; {F_TEL_D}. {EP} Fin de semana: presencia de sábado y domingo entre la de lunes a viernes.",
              numericas=(1, 2, 3, 4, 5), resaltar_primera=True, tam=8)
    inf.figura(figs["cuadrante"], "Tipología de los municipios por volumen, estadía y especialización extranjera",
               f"{F_TEL_M}. {EP} El tamaño del punto representa el IEE; las líneas punteadas, los umbrales de la regla.")
    inf.h2("5.3 Resultados")
    inf.tabla("Promedio de los indicadores por tipo de municipio",
              ["Clase", "Municipios", "Visitantes por mes", "Estadía", "IEE", "Fin de semana"],
              [[c, lista([corto(x) for x in tr["miembros"][c]]), n0(f["visitantes_mes"]), n1(f["estadia_media"]),
                n2(f["iee"]), n2(f["presion_finde"])] for c, f in pc.iterrows()],
              [2.8, 5.6, 2.4, 1.7, 1.5, 2.2], f"{F_TEL_M}; {F_TEL_D}. {EP}", numericas=(2, 3, 4, 5), resaltar_primera=True)
    inf.p(f"**Puertas de entrada.** {lista([corto(x) for x in hub])} concentran el volumen y la mayor presión de fin de "
          f"semana ({n2(pc.loc['Hub comercial', 'presion_finde'])} veces un día hábil), pero cumplen funciones distintas. "
          f"Panajachel combina visitantes nacionales y extranjeros (IEE {n2(p.loc['Panajachel', 'iee'])}) y recibe el mayor "
          f"número de extranjeros del lago. San Lucas Tolimán es la puerta del visitante nacional: su IEE es "
          f"{n2(p.loc[sl, 'iee'])}, el más bajo del lago, y su domingo alcanza un índice de {dom_sl:.0f}, la mayor presión "
          "puntual del destino.")
    inf.p(f"**Larga estancia.** {lista([corto(x) for x in larga])} retienen {n1(pc.loc['Larga estancia', 'estadia_media'])} "
          f"días por turista, frente a {n1(pc.loc['Hub comercial', 'estadia_media'])} en los hubs, y atraen proporcionalmente "
          f"más extranjeros que el lago (IEE {n2(pc.loc['Larga estancia', 'iee'])}). San Pedro La Laguna reúne volumen de hub "
          f"y la estadía más alta del lago ({n2(p.loc['San Pedro La Laguna', 'estadia_media'])} días).")
    inf.p(f"**Visita corta y el caso de San Marcos La Laguna.** San Marcos presenta la mayor especialización extranjera "
          f"({n2(p.loc[sm, 'iee'])}), pero su estadía de {n1(p.loc[sm, 'estadia_media'])} días está por debajo de la mediana "
          f"({n1(cortes['mediana_estadia'])}). El dato contradice la expectativa de la asignación, que lo ubicaba como destino "
          "de retiro. Una explicación consistente con la geografía es que parte de sus visitantes extranjeros pernocte en "
          "San Pedro La Laguna, a pocos minutos en lancha; confirmarlo requiere pares origen-destino entre polígonos. San "
          f"Antonio Palopó es el municipio más estacional: su mes de mayor afluencia supera {n1(v['amplitud'].max())} veces al "
          "de menor.")
    inf.h2("5.4 Implicaciones para la gestión")
    inf.vinetas([
        "Los hubs requieren gestión de flujo en fines de semana y feriados. San Lucas Tolimán, con el domingo más cargado, "
        "es el punto más expuesto y el menos visible en las estadísticas de turismo internacional.",
        "La promoción de estadías largas tiene su mejor base en los municipios de larga estancia, donde el visitante ya "
        "permanece más tiempo y la especialización extranjera es mayor.",
        "San Marcos La Laguna debe tratarse como destino de visita extranjera de corta duración mientras no se verifique "
        "dónde pernoctan sus visitantes.",
    ])

    # ------------------------------------------------------------------------------ 6
    inf.h1("6. Supuestos, limitaciones y calidad de las fuentes")
    inf.tabla("Supuestos y limitaciones", ["Tema", "Descripción", "Efecto en las conclusiones"], [
        ["Consolidación territorial", "Se usan los diez municipios del lago; oferta y ocupación son de todo Sololá.",
         "La capacidad no puede analizarse por municipio."],
        ["Discontinuidad de la telefonía", "Cobertura de septiembre a diciembre de 2025 y de marzo a agosto de 2026.",
         "No hay comparación interanual directa entre 2025 y 2026; enero y febrero se estiman."],
        ["Suma de municipios", "El operador no entrega el total del destino; sumar municipios duplica visitantes.",
         "Los volúmenes agregados son cotas superiores y la captación formal, una cota inferior."],
        ["Universos distintos", "Oferta, ocupación y boletines cubren solo la hotelería formal registrada.",
         "Airbnb y viviendas de familiares no forman parte de la capacidad medida."],
        ["Encuestas sin factor de expansión", "La encuesta en fronteras es una muestra por cuotas, sobre todo terrestre.",
         "Solo se reportan porcentajes de la ola vigente, nunca totales ni tendencias."],
        ["Factor de expansión nacional", "Las cifras nacionales vienen expandidas; las extranjeras no.",
         "Nacionales y extranjeros se reportan por separado y se usa el IEE."],
        ["Cobertura del índice de ocupación", "El índice se calcula sobre los establecimientos que reportan.",
         "No sirve para dimensionar la capacidad sin informar su cobertura."],
        ["Ruptura del flujo migratorio", "Cambio metodológico entre 2022 y 2023.", "El perfil estacional usa solo 2023 a 2025."],
        ["Corte parcial de la oferta", "El corte de 2026 cubre el primer trimestre.", "Se presenta aparte y no se compara."]],
        [3.9, 6.3, 6.4], EP, resaltar_primera=True)

    # ------------------------------------------------------------------------------ 7
    inf.h1("7. Recomendaciones estratégicas y hoja de ruta")
    inf.p("Cada recomendación se deriva de un resultado cuantitativo del observatorio. La prioridad combina la solidez de la "
          "evidencia con el costo de no actuar.")
    inf.tabla("Recomendaciones, evidencia y prioridad", ["Recomendación", "Evidencia", "Acción propuesta", "Prioridad"], [
        ["1. Medición de la ocupación", f"Índice publicado de {p0(ba.loc[2025, 'ocup_publicada'])} frente a "
         f"{p0(ba.loc[2025, 'ocup_inventario'])} sobre inventario; cobertura del índice de {p0(ba.loc[2025, 'cobertura'])}",
         "Publicar la cobertura del índice y la ocupación sobre inventario; actualizar la muestra de establecimientos", "Alta"],
        ["2. Registro del alojamiento no formal", f"Captación formal de {p0(cap_ext)} en extranjeros y {p1(cap_nac)} en "
         f"nacionales; {p0(pct_air)} de los encuestados declara Airbnb", "Registro municipal de casas de huéspedes y "
         "plataformas digitales", "Alta"],
        ["3. Gestión de picos en los hubs", f"{top_ev}: {lift.loc[top_ev, 'lift'] * 100:+.0f}%; domingo en San Lucas "
         f"Tolimán: índice {dom_sl:.0f}", "Refuerzo de transporte lacustre, seguridad y servicios en fines de semana y fin "
         "de año", "Alta"],
        ["4. Promoción de estadías largas", f"Larga estancia: {n1(pc.loc['Larga estancia', 'estadia_media'])} días; Europa: "
         f"{n1(eu['est'])} días frente a {n1(ca['est'])} de Centroamérica; {p0(v['fro_puesto'].iloc[0])} ingresa por {puesto}",
         f"Promoción en mercados europeos y norteamericanos; información en el corredor de {puesto}", "Media"],
        ["5. Temporada baja", f"Ocupación mediana de {p0(baja)} en octubre y noviembre",
         "Campañas para el mercado nacional y paquetes de fin de semana en esos meses", "Media"]],
        [3.4, 5.6, 5.8, 1.8], f"Resultados del observatorio. {EP}", resaltar_primera=True)
    inf.tabla("Hoja de ruta", ["Horizonte", "Acciones"], [
        ["0 a 3 meses", "Plan operativo de fines de semana y fin de año en los hubs; publicación de la cobertura del índice "
                        "de ocupación; actualización mensual del tablero."],
        ["3 a 12 meses", "Registro municipal de alojamiento no formal; acuerdo con el operador de telefonía para cobertura de "
                         "doce meses y entrega del total del destino; campaña de temporada baja."],
        ["Más de 12 meses", "Oferta y ocupación por municipio; encuesta en sitio con factor de expansión; pares origen-destino "
                            "entre polígonos; indicadores ambientales para una eventual postulación a la red INSTO."]],
        [3.2, 13.4], EP, resaltar_primera=True)

    # ------------------------------------------------------------------------------ 8
    inf.h1("8. Criterios de selección del contenido del tablero")
    inf.tabla("Elementos incluidos y descartados", ["Elemento", "Decisión", "Justificación"], [
        ["Tipología de municipios con regla y k-medias", "Incluido", "Entregable del reto; k-medias aporta un contraste independiente"],
        ["Mapa del peso de cada municipio por mes", "Incluido", "Solicitado para Atitlán en la guía de uso de los datos"],
        ["Mapa de desplazamientos entre municipios", "Descartado", "La base no contiene pares origen-destino"],
        ["Porcentaje de extranjeros sobre el total", "Sustituido por el IEE", "Error explícito en la guía de uso"],
        ["Tasa implícita (noches de telefonía ÷ plazas-noche)", "Sustituida", "Con datos reales daba 578% porque mezcla universos"],
        ["Tendencia de la oferta", "Descartada", "Cinco cortes de inventario no forman una serie"],
        ["Comparación de 2025 frente a 2026", "Descartada", "Ningún mes de telefonía se repite entre años"],
        ["Proyección de la base diaria", "Descartada", "La guía la prohíbe; la base diaria solo verifica la estimación"],
        ["Encuestas de satisfacción y residentes, aeropuerto y Tikal", "Descartadas", "Corresponden a otros destinos"],
        ["Boletines y encuesta en fronteras", "Incluidos", "Aportan información del lago que no está en los archivos de datos"]],
        [6.2, 3.2, 7.2], EP, resaltar_primera=True)

    # ------------------------------------------------------------------------------ 9
    inf.h1("9. Observatorios de referencia")
    inf.h2("9.1 Red INSTO de ONU Turismo")
    inf.p("La Red Internacional de Observatorios de Turismo Sostenible (INSTO) de ONU Turismo se creó en 2004 para apoyar el "
          "monitoreo regular de los impactos económicos, ambientales y sociales del turismo. No impone indicadores; define "
          "áreas que cada observatorio debe cubrir, al menos en parte, durante sus primeros tres años: estacionalidad, "
          "empleo, beneficios económicos para el destino, gobernanza, satisfacción local, accesibilidad, energía, agua, "
          "aguas residuales, residuos sólidos y acción climática. Los miembros entregan un informe anual y pierden la "
          "membresía si no reportan durante dos años consecutivos.")
    inf.h2("9.2 SEGITTUR y los Destinos Turísticos Inteligentes")
    inf.p("SEGITTUR es la sociedad estatal española responsable de la innovación y la tecnología turística. Lidera el modelo "
          "de Destinos Turísticos Inteligentes (DTI), estructurado en cinco ejes, gobernanza, innovación, tecnología, "
          "sostenibilidad y accesibilidad, y formalizado en la norma UNE 178501. En octubre de 2024 la Red DTI reunía 681 "
          "miembros entre destinos, instituciones, empresas y observadores.")
    inf.tabla("Prácticas de referencia y su aplicación", ["Práctica", "Origen", "Aplicación en el observatorio"], [
        ["Monitoreo continuo con un método constante", "INSTO", "Proceso de datos reproducible; el tablero se actualiza al cambiar los archivos"],
        ["Áreas temáticas antes que indicadores fijos", "INSTO", "Cuatro módulos; la estacionalidad es un área obligatoria"],
        ["Informe periódico con diagnóstico", "INSTO", "Página de conclusiones y esta memoria, generadas con las cifras vigentes"],
        ["Gobernanza del dato", "SEGITTUR", "Confidencialidad, datos en solo lectura, controles y huella de cada archivo"],
        ["Tecnología abierta", "SEGITTUR", "Python, Streamlit, Plotly y Docker"],
        ["Accesibilidad", "SEGITTUR e INSTO", "Contraste mínimo de 3:1, segunda señal para daltonismo, diseño adaptable"]],
        [5.2, 2.8, 8.6], f"ONU Turismo; SEGITTUR. {EP}", resaltar_primera=True)
    inf.p("Frente a ambos modelos, el observatorio todavía no mide satisfacción local, empleo ni las áreas ambientales que "
          "INSTO exige. Son los pasos necesarios si el INGUAT decidiera postular el destino a la red.")

    # ------------------------------------------------------------------------------ 10
    inf.h1("10. Tecnología y diseño")
    inf.h2("10.1 Selección tecnológica")
    inf.tabla("Justificación de la plataforma", ["Necesidad", "Decisión", "Justificación", "Alternativa descartada"], [
        ["Un solo lenguaje del dato al tablero", "Streamlit (Python)", "Reutiliza el análisis en pandas; gráficas enlazadas "
         "sin JavaScript; pruebas automáticas por página", "Dash; Power BI y Tableau por sus licencias propietarias"],
        ["Gráficas interactivas", "Plotly", "Información emergente, selección para filtrar y exportación a imagen", "matplotlib, estático"],
        ["Despliegue reproducible", "Docker", "Versiones fijas; datos montados en solo lectura, fuera de la imagen", "Instalación manual"]],
        [3.6, 2.8, 6.2, 4.0], EP, resaltar_primera=True)
    inf.h2("10.2 Paleta y teoría del color")
    inf.p("El tono distingue categorías y la luminosidad expresa magnitudes. Todo color de dato alcanza un contraste mínimo "
          "de 3:1 sobre fondo blanco (WCAG 2.2, criterio 1.4.11) y ninguna categoría depende solo del color (criterio "
          "1.4.1). La simulación de daltonismo de Machado et al. (2009) mostró que turista y excursionista, y hub y visita "
          "corta, se aproximan con deuteranopia y protanopia; por eso el excursionista lleva trama y cada clase de "
          "municipio, una forma propia.")
    paleta = [("Nacional", COLORES_ORIGEN["Nacional"]), ("Extranjero", COLORES_ORIGEN["Extranjero"]),
              *COLORES_SEGMENTO.items(), ("Dato observado", COLOR_REAL), ("Estimación", COLOR_ESTIMADO),
              ("Festividad", COLOR_EVENTO), ("Selección", COLOR_DESTACADO), ("Contexto", COLOR_HISTORIA),
              ("Ocupación hotelera", COLOR_OCUPACION),
              *((f"Clase: {k}", c) for k, c in COLORES_CLASE.items() if k != "Intermedio")]
    inf.tabla("Paleta del observatorio", ["Significado", "Color", "Contraste sobre blanco"],
              [[s, c.upper(), f"{contraste(c):.2f}:1"] for s, c in paleta], [7.0, 4.0, 5.6],
              f"{EP} Contraste calculado según WCAG 2.2.", numericas=(2,))
    inf.h2("10.3 Interacción")
    inf.vinetas([
        "Cuatro gráficas enlazadas, una por módulo, señalizadas con «Clic para filtrar»; las gráficas que reciben el filtro "
        "muestran el filtro activo.",
        "Cada gráfica tiene título descriptivo, subtítulo con unidades y periodo, nota metodológica y fuente.",
        "Exportación de tablas deshabilitada; la barra de herramientas solo exporta imágenes.",
        "Diseño adaptable verificado a 390 px (teléfono) y 768 px (tableta), con indicador de cobertura de las fuentes.",
    ])

    # ------------------------------------------------------------------------------ anexos
    inf.h1("Anexo A. Fichas de indicadores")
    seccion = None
    for f in fichas:
        if f["seccion"] != seccion:
            seccion = f["seccion"]
            inf.h2(seccion.replace("3.", "A.", 1))
        inf.ficha(f["codigo"], f["nombre"], f["campos"])

    inf.h1("Anexo B. Estructura del repositorio y dependencias")
    inf.codigo(arbol())
    inf.p("Dependencias del tablero (requirements.txt):")
    inf.codigo((RAIZ / "requirements.txt").read_text(encoding="utf-8"))

    inf.h1("Anexo C. Fragmentos de código")
    for titulo, fn in (("Estadía media ponderada (src/indicadores.py)", ind.estadia_media),
                       ("Índice de especialización extranjera (src/indicadores.py)", ind.especializacion_extranjera),
                       ("Estimación de los meses sin cobertura (src/pronostico.py)", pr._predecir),
                       ("Regla de clasificación de los municipios (src/territorio.py)", te.clasificar_regla)):
        inf.h3(titulo)
        inf.codigo(inspect.getsource(fn))

    inf.h1("Anexo D. Instalación en un servidor")
    inf.p("Procedimiento para Ubuntu Server 24.04 LTS con acceso al repositorio privado mediante una llave de despliegue. "
          "Primero se instalan Git y Docker Engine con el complemento Compose, según la guía oficial de Docker:")
    inf.codigo("sudo apt-get update && sudo apt-get install -y ca-certificates curl git\n"
               "sudo install -m 0755 -d /etc/apt/keyrings\n"
               "sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc\n"
               "echo \"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \\\n"
               "  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable\" \\\n"
               "  | sudo tee /etc/apt/sources.list.d/docker.list\n"
               "sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin")
    inf.p("Después se clona el repositorio y se copian los archivos institucionales, con su nombre original, a una carpeta "
          "con permisos restringidos fuera del repositorio:")
    inf.codigo("sudo git clone git@github.com:Isabella1911/DS-Proyecto-3.git /opt/observatorio\n"
               "sudo mkdir -p /srv/observatorio/datos && sudo chmod 750 /srv/observatorio/datos")
    inf.p("Por último se construye e inicia el tablero con los datos montados en solo lectura. El puerto escucha solo en "
          "127.0.0.1; el acceso externo se configura con un túnel SSH o un proxy inverso con TLS:")
    inf.codigo("cd /opt/observatorio\n"
               "DATOS_DIR=/srv/observatorio/datos docker compose up -d --build\n"
               "curl -s http://127.0.0.1:8501/_stcore/health")
    inf.p("La memoria se regenera con python scripts/generar_memoria.py y la revisión de las bases se realiza con python "
          "scripts/revisar_datos.py. Ambos procesos producen solo información agregada.")

    inf.h1("Referencias")
    for ref in [
        "Docker Inc. (2026). Install Docker Engine on Ubuntu. https://docs.docker.com/engine/install/ubuntu/",
        "esmartcity (15 de octubre de 2024). La Red de Destinos Turísticos Inteligentes aprueba la adhesión de 62 miembros "
        "titulares. https://www.esmartcity.es/2024/10/15/red-destinos-turisticos-inteligentes-aprueba-adhesion-62-miembros-titulares",
        "INGUAT (2023, 2024 y 2025). Boletín de ocupación hotelera, enero a diciembre. Departamento de Investigación y "
        "Análisis de Mercados.",
        "INGUAT (2026). Guía de uso de los datos. Tableros por destino. Documento para los equipos del curso CC3084.",
        "Machado, G. M., Oliveira, M. M. y Fernandes, L. A. F. (2009). A physiologically-based model for simulation of "
        "color vision deficiency. IEEE Transactions on Visualization and Computer Graphics, 15(6), 1291-1298.",
        "ONU Turismo. About the International Network of Sustainable Tourism Observatories (INSTO). "
        "https://www.untourism.int/sustainable-development/about-insto",
        "ONU Turismo. INSTO Framework. https://www.untourism.int/sustainable-development/into-framework",
        "SEGITTUR (2024). Manual de gestión de la metodología DTI. https://www.destinosinteligentes.es/wp-content/uploads/"
        "2024/05/Manual-Gestion-Metodologia-DTI_Junio-2024.pdf",
        "SEGITTUR. Destinos Turísticos Inteligentes. https://www.segittur.es/destinos-turisticos-inteligentes/",
        "UNE (2022). Normas UNE para destinos turísticos inteligentes. https://www.une.org/salainformaciondocumentos/"
        "220928_UNE-SEGITTUR_NP_Destinos-Turisticos_Inteligentes.pdf",
        "W3C (2023). Web Content Accessibility Guidelines (WCAG) 2.2. https://www.w3.org/TR/WCAG22/",
    ]:
        par = inf.p(ref, alin=0)
        par.paragraph_format.left_indent = Cm(0.75)
        par.paragraph_format.first_line_indent = Cm(-0.75)
    return inf


def main() -> None:
    v = datos()
    figs = figuras(v)
    inf = redactar(v, figs)
    inf.guardar(SALIDA, EQUIPO)
    print(f"Memoria generada: {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
