"""Genera la memoria tecnica en DOCX con las cifras de los datos cargados (reales o sinteticos).

    python scripts/generar_memoria.py      # requiere pandoc (https://pandoc.org/installing.html)

Llena docs/memoria/plantilla.md con las cifras de src/hallazgos.py (las mismas del tablero), inserta las
fichas de indicadores (docs/memoria/fichas.md), exporta las figuras y construye
docs/memoria/Memoria_tecnica_Grupo3.docx. Los intermedios quedan en docs/memoria/_build (no se versiona).
La memoria solo contiene agregados; nunca filas de las bases.
"""

from __future__ import annotations

import inspect
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from src import etl, hallazgos  # noqa: E402
from src import indicadores as ind  # noqa: E402
from src import oferta as of  # noqa: E402
from src import pronostico as pr  # noqa: E402
from src import territorio as te  # noqa: E402
from src.estilo import (  # noqa: E402
    COLOR_DESTACADO, COLOR_ESTIMADO, COLOR_EVENTO, COLOR_HISTORIA, COLOR_OCUPACION, COLOR_REAL, COLORES_CLASE,
    COLORES_ORIGEN, COLORES_SEGMENTO, contraste, formato_numero,
)
from src.graficas import fig_cuadrante, fig_mensual_estimada  # noqa: E402
from src.normalizar import MUNICIPIO_CORTO, departamento  # noqa: E402

MEMORIA = RAIZ / "docs" / "memoria"
BUILD = MEMORIA / "_build"
SALIDA = MEMORIA / "Memoria_tecnica_Grupo3.docx"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]
EQUIPO = [
    "Anthony Lou Schwank (23410)",
    "Christa Isabella Obando Guzmán (23074)",
    "Fabian Prado Dluzniewski (23427)",
    "Luis Fernando Mendoza Alvarez (19644)",
]


def pct(x: float) -> str:
    return "Sin dato" if pd.isna(x) else f"{x:.0%}"


def num(x: float) -> str:
    return "Sin dato" if pd.isna(x) else formato_numero(x)


def lista(municipios: list[str]) -> str:
    nombres = [MUNICIPIO_CORTO.get(x, x) for x in municipios]
    if not nombres:
        return "ningún municipio"
    return nombres[0] if len(nombres) == 1 else ", ".join(nombres[:-1]) + " y " + nombres[-1]


def tabla_md(df: pd.DataFrame) -> str:
    cab = "| " + " | ".join(df.columns) + " |"
    sep = "|" + "|".join(":---" for _ in df.columns) + "|"
    filas = ["| " + " | ".join(str(v) for v in fila) + " |" for fila in df.itertuples(index=False)]
    return "\n".join([cab, sep, *filas])


# ---------------------------------------------------------------------------------------------
# Figuras


def fig_arquitectura(ruta: Path) -> None:
    """Flujo de datos (arriba) y llaves que unen las cinco bases (abajo)."""
    fig, ax = plt.subplots(figsize=(11, 6.2))
    ax.set_xlim(0, 110)
    ax.set_ylim(0, 62)
    ax.axis("off")

    def caja(x, y, w, h, texto, borde="#8d8d8d", fondo="#ffffff", negrita=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0", linewidth=1.2, edgecolor=borde, facecolor=fondo))
        ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=8.5, color="#161616",
                fontweight="bold" if negrita else "normal", wrap=True)

    def flecha(x0, y0, x1, y1, texto="", color="#525252"):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="->", color=color, lw=1.2))
        if texto:
            ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 1.2, texto, ha="center", fontsize=7.5, color=color)

    ax.text(0, 60, "Flujo de datos", fontsize=10, fontweight="bold", color="#161616")
    caja(0, 44, 18, 12, "data/raw\n(reales, solo lectura)\no data/sinteticos")
    caja(23, 44, 18, 12, "src/normalizar.py\ntextos, números\ny fechas")
    caja(46, 44, 18, 12, "src/etl.py\ncontroles +\ncalidad.json")
    caja(69, 44, 18, 12, "data/procesados\n5 tablas parquet")
    caja(92, 44, 18, 12, "Tablero Streamlit\n+ Plotly", borde=COLOR_DESTACADO, negrita=True)
    for x in (18, 41, 64, 87):
        flecha(x, 50, x + 5, 50)

    ax.text(0, 37, "Cómo se relacionan las cinco bases", fontsize=10, fontweight="bold", color="#161616")
    caja(36, 16, 26, 12, "Movilidad mensual\nmunicipio x mes x país x segmento", borde=COLOR_REAL, negrita=True)
    caja(0, 26, 24, 9, "Migración\nmes (llegadas internacionales)")
    caja(0, 2, 24, 9, "Movilidad diaria\nmunicipio x día x país")
    caja(76, 26, 24, 9, "Ocupación\ndepartamento x mes")
    caja(76, 2, 24, 9, "Oferta hotelera\ndepartamento x año x tipo")
    flecha(36, 25, 24, 30, "periodo: factor de reparto")
    flecha(36, 19, 24, 7, "municipio: fin de semana, festividades")
    flecha(62, 25, 76, 30, "periodo: ventana sep-dic 2025")
    flecha(62, 19, 76, 7, "año: plazas-noche")
    flecha(88, 26, 88, 11, "departamento", color=COLOR_OCUPACION)
    fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def figuras(t: dict, r: dict) -> dict[str, str]:
    BUILD.mkdir(parents=True, exist_ok=True)
    fig_arquitectura(BUILD / "arquitectura.png")
    perfil = r["territorio"]["perfil"].assign(clase=lambda p: p["clase_regla"])
    fig_cuadrante(perfil, None).update_layout(width=1000, height=520, paper_bgcolor="white") \
        .write_image(BUILD / "cuadrante.png", scale=2)
    est = r["temporal"]
    faltantes = etl.CONFIG["estimacion"]["meses_sin_cobertura"]
    obs = ind.serie_mensual(t["mensual"])
    obs = obs.reindex(ind.calendario(obs.index, faltantes))
    fig_mensual_estimada(obs, est["estimados"]).update_layout(width=1000, height=420, paper_bgcolor="white") \
        .write_image(BUILD / "estimacion.png", scale=2)
    return {"fig_arquitectura": "arquitectura.png", "fig_cuadrante": "cuadrante.png", "fig_estimacion": "estimacion.png"}


# ---------------------------------------------------------------------------------------------
# Bloques de texto


def aviso(fuentes: dict) -> str:
    sint = [f for f, i in fuentes.items() if i["origen"] == "sintetico"]
    hoy = date.today()
    fecha = f"{hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}"
    if sint:
        return (f"> **Aviso: versión con datos sintéticos.** Generada el {fecha} con datos sintéticos en "
                f"{len(sint)} de {len(fuentes)} fuentes ({', '.join(sint)}). Las cifras ilustran el método y no deben "
                "citarse. Para la versión final, quien tenga las bases reales corre `python scripts/generar_memoria.py` "
                "(Anexo E) y esta memoria se regenera con las cifras reales.")
    return f"> Generada el {fecha} con las bases institucionales. Contiene solo cifras agregadas, ningún microdato."


def tabla_fuentes(fuentes: dict) -> str:
    filas = [{"Fuente": f, "Archivo": f"`{i['archivo']}`", "Origen": i["origen"].replace("sintetico", "sintético"),
              "Filas leídas": f"{i['filas_leidas']:,}", "Filas limpias": f"{i['filas_limpias']:,}"} for f, i in fuentes.items()]
    return tabla_md(pd.DataFrame(filas))


def tabla_controles(controles: list[dict]) -> str:
    malos = [c for c in controles if c["estado"] != "ok"]
    if not malos:
        return "Ninguno: todos los controles pasaron."
    return "\n".join(f"- **{c['estado']}** en {c['fuente']}: {c['control']} ({c['filas']} filas). {c['detalle']}" for c in malos)


def tabla_municipios(p: pd.DataFrame) -> str:
    t = p.sort_values("visitantes_mes", ascending=False)
    df = pd.DataFrame({
        "Municipio": [MUNICIPIO_CORTO.get(x, x) for x in t.index],
        "Visitantes/mes": t["visitantes_mes"].map(num),
        "Estadía (días)": t["estadia_media"].map(lambda v: f"{v:.2f}"),
        "Extranjeros": t["pct_extranjeros"].map(pct),
        "Excursionistas": t["pct_excursionistas"].map(pct),
        "Presión finde": t["presion_finde"].map(lambda v: f"{v:.2f}"),
        "Regla": t["clase_regla"],
        "k-medias": t["clase_kmedias"],
    })
    return tabla_md(df)


def tabla_clases(r: dict) -> str:
    pc = r["por_clase"]
    df = pd.DataFrame({
        "Clase": pc.index,
        "Municipios": [lista(r["miembros"][c]) for c in pc.index],
        "Visitantes/mes": pc["visitantes_mes"].map(num),
        "Estadía": pc["estadia_media"].map(lambda v: f"{v:.1f} días"),
        "Extranjeros": pc["pct_extranjeros"].map(pct),
        "Excursionistas": pc["pct_excursionistas"].map(pct),
        "Presión finde": pc["presion_finde"].map(lambda v: f"{v:.2f}"),
    })
    return "Promedio simple de los municipios de cada clase (regla del cuadrante):\n\n" + tabla_md(df)


def tabla_paleta() -> str:
    filas = [
        ("Nacional", COLORES_ORIGEN["Nacional"]), ("Extranjero", COLORES_ORIGEN["Extranjero"]),
        *COLORES_SEGMENTO.items(), ("Dato observado", COLOR_REAL), ("Estimación", COLOR_ESTIMADO),
        ("Festividad", COLOR_EVENTO), ("Selección / filtro", COLOR_DESTACADO), ("Contexto", COLOR_HISTORIA),
        ("Ocupación hotelera", COLOR_OCUPACION),
        *((f"Clase: {k}", v) for k, v in COLORES_CLASE.items() if k != "Intermedio"),
    ]
    df = pd.DataFrame({"Significado": [f for f, _ in filas], "Color": [f"`{c}`" for _, c in filas],
                       "Contraste sobre blanco": [f"{contraste(c):.2f}:1" for _, c in filas]})
    return tabla_md(df)


def arbol() -> str:
    """Archivos versionados agrupados por carpeta (las fuentes tipograficas se resumen en una linea)."""
    archivos = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True).stdout.splitlines()
    archivos = [a for a in archivos if not a.startswith("static/tipografia/")]
    archivos = sorted(set(archivos) | {"docs/memoria/Memoria_tecnica_Grupo3.docx", "scripts/generar_memoria.py",
                                       "docs/memoria/plantilla.md", "docs/memoria/fichas.md"})
    grupos: dict[str, list[str]] = {}
    for a in archivos:
        carpeta, _, nombre = a.rpartition("/")
        grupos.setdefault(carpeta, []).append(nombre)
    grupos.setdefault("static/tipografia", []).append("IBM Plex Sans y Mono (licencia OFL)")
    lineas = []
    for carpeta in sorted(grupos, key=lambda c: (c != "", c)):
        if carpeta:
            lineas.append(carpeta + "/")
        lineas += [("  " if carpeta else "") + n for n in grupos[carpeta]]
    return "\n".join(lineas)


def codigo(funcion) -> str:
    return inspect.getsource(funcion).rstrip()


def valores(t: dict, r: dict, cal: dict, figs: dict) -> dict[str, str]:
    dm, tp, ofe, tr = r["demanda"], r["temporal"], r["oferta"], r["territorio"]
    pc, p = tr["por_clase"], tr["perfil"]
    clase = lambda c, col: pc.loc[c, col] if c in pc.index else float("nan")  # noqa: E731
    est = tp["estimados"]
    otro = [k for k in tp["mape"] if k != tp["metodo"]]
    v0, v1 = etl.CONFIG["ventana_coincidente"]
    p0, p1 = t["mensual"]["periodo"].min(), t["mensual"]["periodo"].max()
    corta_p, larga_p = clase("Visita corta", "presion_finde"), clase("Larga estancia", "presion_finde")
    # Titulares de los hallazgos: dependen de las cifras para no afirmar algo que los datos contradigan
    hub_l = lista(tr["miembros"]["Hub comercial"])
    titulo_h1 = (f"La demanda se concentra en {hub_l}, pero las estancias largas están en otros pueblos."
                 if clase("Larga estancia", "estadia_media") > clase("Hub comercial", "estadia_media")
                 else f"La demanda y las estancias se concentran en {hub_l}.")
    saturada = ofe.get("ocupacion_oficial", 0) >= 0.7
    titulo_h3 = ("La capacidad formal está cerca de su límite." if saturada
                 else "La capacidad formal no está saturada en promedio.")
    cierre_h3 = ("La presión sobre la capacidad es sostenida." if saturada
                 else "La presión es puntual (festividades y fines de semana), no permanente.")
    titulo_h4 = (f"{dm['mercado_lider']} es el primer mercado extranjero ({pct(dm['pct_mercado_lider'])}), pero "
                 f"{dm['mercado_estadia']} es el que más se queda ({dm['estadia_mercado_max']:.1f} días)."
                 if dm["mercado_estadia"] != dm["mercado_lider"] else
                 f"{dm['mercado_lider']} es a la vez el primer mercado extranjero ({pct(dm['pct_mercado_lider'])}) y el "
                 f"de estadía más larga ({dm['estadia_mercado_max']:.1f} días).")
    return {
        "titulo_h1": titulo_h1, "titulo_h3": titulo_h3, "cierre_h3": cierre_h3, "titulo_h4": titulo_h4,
        "aviso_datos": aviso(cal["fuentes"]),
        "periodo": f"{MESES[p0.month - 1]} de {p0.year} a {MESES[p1.month - 1]} de {p1.year}",
        "meses": str(dm["meses"]),
        "hub_lista": lista(tr["miembros"]["Hub comercial"]), "larga_lista": lista(tr["miembros"]["Larga estancia"]),
        "corta_lista": lista(tr["miembros"]["Visita corta"]),
        "hub_vis": num(clase("Hub comercial", "visitantes_mes")),
        "hub_est": f"{clase('Hub comercial', 'estadia_media'):.1f}",
        "larga_est": f"{clase('Larga estancia', 'estadia_media'):.1f}", "larga_ext": pct(clase("Larga estancia", "pct_extranjeros")),
        "evento_top": tp["evento_top"] or "Sin dato", "lift_top": f"{tp['lift_top']:+.0%}",
        "lift_aj_top": f"{tp['lift_ajustado_top']:+.0%}", "presion": f"{tp['presion_finde']:.2f}",
        "ventana": f"{MESES[int(v0[-2:]) - 1]} a {MESES[int(v1[-2:]) - 1]} de {v1[:4]}",
        "tasa_impl": pct(ofe.get("tasa_implicita", float("nan"))), "ocup_ofi": pct(ofe.get("ocupacion_oficial", float("nan"))),
        "mercado_lider": dm["mercado_lider"] or "Sin dato", "pct_lider": pct(dm["pct_mercado_lider"]),
        "mercado_estadia": dm["mercado_estadia"] or "Sin dato", "estadia_mercado": f"{dm['estadia_mercado_max']:.1f}",
        "est_m1": num(est.iloc[0]), "est_m2": num(est.iloc[-1]),
        "metodo": tp["metodo"], "metodo_nombre": pr.METODOS[tp["metodo"]].lower().replace("×", "x"),
        "mape_sel": f"{tp['mape'][tp['metodo']]:.1f} %",
        "mape_otro": ", ".join(f"{k}: {tp['mape'][k]:.1f} %" for k in otro),
        "tabla_fuentes": tabla_fuentes(cal["fuentes"]), "tabla_controles": tabla_controles(cal["controles"]),
        "fichas": (MEMORIA / "fichas.md").read_text(encoding="utf-8"),
        "umbral_hub": num(p["visitantes_mes"].max() * te.UMBRAL_HUB),
        "mediana_estadia": f"{p['estadia_media'].median():.2f}",
        "estabilidad": pct(tr["estabilidad"]),
        "tabla_municipios": tabla_municipios(p), "tabla_clases": tabla_clases(tr),
        "coinciden": str(tr["coinciden"]), "n": str(tr["n"]),
        "difieren_texto": (f"; difieren en {lista(tr['difieren'])}, pueblos de transición entre dos clases"
                           if tr["difieren"] else ""),
        "presion_corta": f"{corta_p:.2f}", "presion_larga": f"{larga_p:.2f}",
        "validacion_texto": ("confirma la clasificación, porque los pueblos de visita corta se llenan más el fin de semana."
                             if corta_p > larga_p else
                             "no la confirma: la diferencia entre clases está en el volumen y la estadía, no en el patrón "
                             "semanal, así que conviene revisar la regla con los datos reales."),
        "tabla_paleta": tabla_paleta(),
        "arbol": arbol(),
        "requirements": (RAIZ / "requirements.txt").read_text(encoding="utf-8").rstrip(),
        "codigo_estadia": codigo(ind.estadia_media), "codigo_lift": codigo(ind.lift_eventos),
        "codigo_predecir": codigo(pr._predecir), "codigo_regla": codigo(te.clasificar_regla),
        "codigo_nombrar": codigo(te._nombrar), "codigo_vigente": codigo(etl.vigente),
        **figs,
    }


# ---------------------------------------------------------------------------------------------
# Documento


def referencia(ruta: Path) -> None:
    """Estilos de Word del documento: Arial (disponible en Word y Google Docs), titulos en la tinta del
    tablero (#161616) y enlaces en el azul de seleccion (#0F62FE)."""
    base = BUILD / "base.docx"
    subprocess.run(["pandoc", "-o", str(base), "--print-default-data-file", "reference.docx"], check=True)
    fuente = '<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="Arial" w:cs="Arial" />'
    with zipfile.ZipFile(base) as zin, zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            datos = zin.read(item.filename)
            if item.filename == "word/styles.xml":
                s = datos.decode("utf-8")
                s = re.sub(r'<w:rFonts w:asciiTheme="(major|minor)HAnsi"[^>]*/>', fuente, s)
                s = re.sub(r'<w:color w:val="[0-9A-Fa-f]{6}"[^>]*/>', '<w:color w:val="161616" />', s)
                s = re.sub(r'(w:styleId="Hyperlink".*?)<w:color w:val="161616" />', r'\1<w:color w:val="0F62FE" />', s,
                           count=1, flags=re.S)
                # Fuente y tamano tambien en el estilo Normal (algunos visores ignoran los valores por defecto)
                s = re.sub(r'(<w:style w:type="paragraph" w:default="1" w:styleId="Normal">\s*<w:name w:val="Normal" />\s*'
                           r'<w:qFormat />\s*)</w:style>',
                           rf'\1<w:rPr>{fuente}<w:sz w:val="22" /><w:szCs w:val="22" /></w:rPr></w:style>', s)
                s = s.replace('<w:lang w:val="en-US"', '<w:lang w:val="es-GT"')
                datos = s.encode("utf-8")
            zout.writestr(item, datos)


def main() -> None:
    if shutil.which("pandoc") is None:
        sys.exit("Falta pandoc: https://pandoc.org/installing.html (macOS: brew install pandoc; Ubuntu: apt install pandoc)")
    if not etl.vigente():
        etl.ejecutar()
    t = {n: pd.read_parquet(etl.PROCESADOS / f"{n}.parquet") for n in ["mensual", "diaria", "migracion_mensual", "ocupacion", "oferta"]}
    cal = __import__("json").loads((etl.PROCESADOS / "calidad.json").read_text(encoding="utf-8"))
    r = hallazgos.resumen(t["mensual"], t["diaria"], t["migracion_mensual"], t["ocupacion"], t["oferta"], etl.CONFIG)
    BUILD.mkdir(parents=True, exist_ok=True)
    vals = valores(t, r, cal, figuras(t, r))

    texto = (MEMORIA / "plantilla.md").read_text(encoding="utf-8")
    texto = re.sub(r"<<(\w+)>>", lambda mt: vals[mt.group(1)], texto)
    faltan = re.findall(r"<<\w+>>", texto)
    if faltan:
        sys.exit(f"Marcadores sin valor: {sorted(set(faltan))}")
    autores = "\n".join(f"  - {a}" for a in EQUIPO)
    encabezado = (
        "---\n"
        "title: \"Memoria técnica\"\n"
        "subtitle: \"Observatorio de Inteligencia Turística: Lago de Atitlán. Grupo 3, CC3084 Data Science, "
        "Universidad del Valle de Guatemala\"\n"
        f"author:\n{autores}\n"
        f"date: \"{date.today().day} de {MESES[date.today().month - 1]} de {date.today().year}\"\n"
        "lang: es-GT\n"
        "toc-title: \"Contenido\"\n"
        "---\n\n"
    )
    md = BUILD / "memoria.md"
    md.write_text(encabezado + texto, encoding="utf-8")
    ref = BUILD / "referencia.docx"
    referencia(ref)
    subprocess.run(["pandoc", str(md), "-o", str(SALIDA), "--reference-doc", str(ref), "--toc", "--toc-depth=2",
                    "--resource-path", str(BUILD), "-f", "markdown-smart"], check=True)
    print(f"Memoria generada: {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
