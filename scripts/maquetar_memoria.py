"""Maquetacion profesional de la memoria tecnica (etapa posterior a pandoc).

pandoc convierte el contenido; este modulo aplica el formato de informe:

- Tamano carta, margenes de 2.5 cm y encabezado y pie en todas las paginas salvo la portada.
- Portada institucional con titulo, destinatario, equipo, fecha, version y aviso de uso.
- Estilos tipograficos: Arial 10.5 pt, titulos en azul institucional, leyendas de tablas y figuras,
  notas de fuente y codigo en fuente monoespaciada.
- Tablas con filete superior e inferior, fila de encabezado sombreada y repetida en cada pagina.
- Pie con "Pagina X de Y" y actualizacion automatica del indice al abrir el documento en Word.

    python scripts/maquetar_memoria.py docs/memoria/Memoria_tecnica_Grupo3.docx
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

AZUL = RGBColor(0x0D, 0x36, 0x6B)
TINTA = RGBColor(0x16, 0x16, 0x16)
GRIS = RGBColor(0x52, 0x52, 0x52)
GRIS_CLARO = RGBColor(0x8D, 0x8D, 0x8D)
FUENTE = "Arial"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]

TITULO = "Observatorio de Inteligencia Turística del Lago de Atitlán"
SUBTITULO = "Memoria técnica y recomendaciones para la gestión del destino"


# ---------------------------------------------------------------------------------------------
# Utilidades XML

# Orden de los hijos que exige el esquema OOXML (ECMA-376); un elemento fuera de orden invalida el archivo
_ORDEN_PPR = ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl", "numPr",
              "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap",
              "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd", "snapToGrid",
              "spacing", "ind", "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc", "textDirection",
              "textAlignment", "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr", "pPrChange"]
_ORDEN_TBLPR = ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize", "tblStyleColBandSize", "tblW",
                "jc", "tblCellSpacing", "tblInd", "tblBorders", "shd", "tblLayout", "tblCellMar", "tblLook",
                "tblCaption", "tblDescription", "tblPrChange"]
_DESPUES_UPDATEFIELDS = ["hdrShapeDefaults", "footnotePr", "endnotePr", "compat", "docVars", "rsids", "mathPr",
                         "attachedSchema", "themeFontLang", "clrSchemeMapping", "doNotIncludeSubdocsInStats",
                         "doNotAutoCompressPictures", "forceUpgrade", "captions", "readModeInkLockDown", "smartTagType",
                         "schemaLibrary", "shapeDefaults", "doNotEmbedSmartTags", "decimalSymbol", "listSeparator"]


def _local(elemento) -> str:
    return elemento.tag.split("}")[-1]


def _insertar_en_orden(padre, nuevo, orden: list[str]) -> None:
    """Inserta `nuevo` antes del primer hijo que el esquema ubica despues de el."""
    posicion = orden.index(_local(nuevo))
    posteriores = set(orden[posicion + 1:])
    for i, hijo in enumerate(list(padre)):
        if _local(hijo) in posteriores:
            padre.insert(i, nuevo)
            return
    padre.append(nuevo)


def _fuente(run, nombre: str = FUENTE) -> None:
    run.font.name = nombre
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), nombre)


def _campo(parrafo, instruccion: str, texto: str = "1", tam: float = 8, color: RGBColor = GRIS) -> None:
    """Inserta un campo de Word (PAGE, NUMPAGES) como runs con fldChar."""
    def run(elemento):
        r = parrafo.add_run()
        r.font.size = Pt(tam)
        r.font.color.rgb = color
        _fuente(r)
        r._element.append(elemento)
        return r

    inicio = OxmlElement("w:fldChar")
    inicio.set(qn("w:fldCharType"), "begin")
    run(inicio)
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f" {instruccion} "
    run(instr)
    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    run(sep)
    r = parrafo.add_run(texto)
    r.font.size = Pt(tam)
    r.font.color.rgb = color
    _fuente(r)
    fin = OxmlElement("w:fldChar")
    fin.set(qn("w:fldCharType"), "end")
    run(fin)


def _borde_parrafo(parrafo, lado: str, grosor: int = 6, color: str = "C6C6C6", espacio: int = 4) -> None:
    ppr = parrafo._p.get_or_add_pPr()
    bordes = ppr.find(qn("w:pBdr"))
    if bordes is None:
        bordes = OxmlElement("w:pBdr")
        _insertar_en_orden(ppr, bordes, _ORDEN_PPR)
    b = OxmlElement(f"w:{lado}")
    b.set(qn("w:val"), "single")
    b.set(qn("w:sz"), str(grosor))
    b.set(qn("w:space"), str(espacio))
    b.set(qn("w:color"), color)
    bordes.append(b)


# ---------------------------------------------------------------------------------------------
# Estilos


def _estilo(doc, nombre: str, tam: float, negrita: bool = False, color: RGBColor = TINTA, antes: float = 0,
            despues: float = 6, cursiva: bool = False, interlineado: float | None = None, siguiente: bool = False,
            salto: bool = False, fuente: str = FUENTE):
    try:
        st = doc.styles[nombre]
    except KeyError:
        return None
    st.font.name = fuente
    st.font.size = Pt(tam)
    st.font.bold = negrita
    st.font.italic = cursiva
    st.font.color.rgb = color
    rpr = st.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), fuente)
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        rfonts.attrib.pop(qn(attr), None)
    if not hasattr(st, "paragraph_format"):
        return st
    pf = st.paragraph_format
    pf.space_before = Pt(antes)
    pf.space_after = Pt(despues)
    if interlineado:
        pf.line_spacing = interlineado
    pf.keep_with_next = siguiente
    pf.page_break_before = salto
    return st


def estilos(doc) -> None:
    _estilo(doc, "Normal", 10.5, despues=6, interlineado=1.15)
    for nombre in ("Body Text", "First Paragraph", "Compact"):
        _estilo(doc, nombre, 10.5, despues=6, interlineado=1.15)
    _estilo(doc, "Compact", 10.5, despues=3, interlineado=1.1)
    _estilo(doc, "Heading 1", 16, negrita=True, color=AZUL, antes=0, despues=12, siguiente=True, salto=True)
    _estilo(doc, "Heading 2", 12.5, negrita=True, color=TINTA, antes=14, despues=6, siguiente=True)
    _estilo(doc, "Heading 3", 11, negrita=True, color=AZUL, antes=12, despues=4, siguiente=True)
    _estilo(doc, "Leyenda", 9.5, negrita=True, color=TINTA, antes=10, despues=4, siguiente=True)
    _estilo(doc, "Fuente", 8.5, cursiva=True, color=GRIS, antes=3, despues=12)
    _estilo(doc, "Source Code", 8, color=TINTA, despues=0, fuente="Consolas")
    _estilo(doc, "Verbatim Char", 8.5, color=TINTA, fuente="Consolas")
    _estilo(doc, "TOC Heading", 16, negrita=True, color=AZUL, antes=0, despues=12)
    for n in (1, 2):
        _estilo(doc, f"toc {n}", 10.5 if n == 1 else 10, negrita=(n == 1), despues=3 if n == 1 else 1)
    _estilo(doc, "Hyperlink", 10.5, color=RGBColor(0x0F, 0x62, 0xFE))


# ---------------------------------------------------------------------------------------------
# Tablas


def _borde_tabla(tbl, bordes: dict[str, tuple[int, str]]) -> None:
    tblpr = tbl._tbl.tblPr
    actual = tblpr.find(qn("w:tblBorders"))
    if actual is not None:
        tblpr.remove(actual)
    nodo = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b = OxmlElement(f"w:{lado}")
        if lado in bordes:
            sz, color = bordes[lado]
            b.set(qn("w:val"), "single")
            b.set(qn("w:sz"), str(sz))
            b.set(qn("w:color"), color)
        else:
            b.set(qn("w:val"), "nil")
        nodo.append(b)
    _insertar_en_orden(tblpr, nodo, _ORDEN_TBLPR)


def _sombra(celda, color: str) -> None:
    tcpr = celda._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    _insertar_en_orden(tcpr, shd, ["cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd", "noWrap",
                                   "tcMar", "textDirection", "tcFitText", "vAlign", "hideMark"])


def _margenes_celda(tbl) -> None:
    tblpr = tbl._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for lado, valor in (("top", 50), ("left", 80), ("bottom", 50), ("right", 80)):
        m = OxmlElement(f"w:{lado}")
        m.set(qn("w:w"), str(valor))
        m.set(qn("w:type"), "dxa")
        mar.append(m)
    actual = tblpr.find(qn("w:tblCellMar"))
    if actual is not None:
        tblpr.remove(actual)
    _insertar_en_orden(tblpr, mar, _ORDEN_TBLPR)


def tablas(doc) -> None:
    for tbl in doc.tables:
        es_ficha = len(tbl.columns) == 2 and tbl.rows and tbl.rows[0].cells[0].text.strip() == "Campo"
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        _borde_tabla(tbl, {"top": (12, "161616"), "bottom": (12, "161616"), "insideH": (4, "C6C6C6")})
        _margenes_celda(tbl)
        for i, fila in enumerate(tbl.rows):
            if i == 0:
                trpr = fila._tr.get_or_add_trPr()
                rep = OxmlElement("w:tblHeader")
                trpr.append(rep)
            no_partir = OxmlElement("w:cantSplit")
            fila._tr.get_or_add_trPr().append(no_partir)
            for j, celda in enumerate(fila.cells):
                if i == 0:
                    _sombra(celda, "E8E8E8")
                elif es_ficha and j == 0:
                    _sombra(celda, "F4F4F4")
                for p in celda.paragraphs:
                    p.paragraph_format.space_before = Pt(0)
                    p.paragraph_format.space_after = Pt(0)
                    p.paragraph_format.line_spacing = 1.05
                    for r in p.runs:
                        r.font.size = Pt(8.5)
                        if i == 0 or (es_ficha and j == 0):
                            r.font.bold = True
        # Las fichas no repiten el encabezado "Campo | Contenido": se oculta su texto y queda como filete
        if es_ficha:
            encabezado = tbl.rows[0]
            encabezado._tr.getparent().remove(encabezado._tr)


# ---------------------------------------------------------------------------------------------
# Pagina, encabezado, pie y portada


def pagina(doc) -> None:
    for s in doc.sections:
        s.page_width, s.page_height = Cm(21.59), Cm(27.94)
        s.top_margin = s.bottom_margin = Cm(2.5)
        s.left_margin = s.right_margin = Cm(2.5)
        s.header_distance = s.footer_distance = Cm(1.2)
        s.gutter = Cm(0)
        s.different_first_page_header_footer = True

        enc = s.header.paragraphs[0] if s.header.paragraphs else s.header.add_paragraph()
        enc.text = ""
        enc.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r = enc.add_run(f"{TITULO}  |  Memoria técnica")
        r.font.size = Pt(8)
        r.font.color.rgb = GRIS
        _fuente(r)
        _borde_parrafo(enc, "bottom", 4, "C6C6C6", 4)

        pie = s.footer.paragraphs[0] if s.footer.paragraphs else s.footer.add_paragraph()
        pie.text = ""
        ancho = s.page_width - s.left_margin - s.right_margin
        pie.paragraph_format.tab_stops.add_tab_stop(ancho, WD_TAB_ALIGNMENT.RIGHT)
        _borde_parrafo(pie, "top", 4, "C6C6C6", 4)
        r = pie.add_run("Grupo 3, CC3084 Data Science, Universidad del Valle de Guatemala. Uso académico.\t")
        r.font.size = Pt(8)
        r.font.color.rgb = GRIS
        _fuente(r)
        r = pie.add_run("Página ")
        r.font.size = Pt(8)
        r.font.color.rgb = GRIS
        _fuente(r)
        _campo(pie, "PAGE")
        r = pie.add_run(" de ")
        r.font.size = Pt(8)
        r.font.color.rgb = GRIS
        _fuente(r)
        _campo(pie, "NUMPAGES")


def _parrafo_antes(ancla, texto: str = "", tam: float = 10.5, negrita: bool = False, color: RGBColor = TINTA,
                   antes: float = 0, despues: float = 6, alin=WD_ALIGN_PARAGRAPH.LEFT, cursiva: bool = False):
    p = ancla.insert_paragraph_before()
    p.style = p.part.document.styles["Normal"]
    p.alignment = alin
    p.paragraph_format.space_before = Pt(antes)
    p.paragraph_format.space_after = Pt(despues)
    if texto:
        r = p.add_run(texto)
        r.font.size = Pt(tam)
        r.font.bold = negrita
        r.font.italic = cursiva
        r.font.color.rgb = color
        _fuente(r)
    return p


def portada(doc, equipo: list[str], version: str) -> None:
    # Ancla al inicio absoluto del cuerpo (antes del indice que inserta pandoc); al final recibe el salto de pagina
    from docx.text.paragraph import Paragraph
    nuevo = OxmlElement("w:p")
    doc.element.body.insert(0, nuevo)
    ancla = Paragraph(nuevo, doc._body)
    hoy = date.today()
    _parrafo_antes(ancla, "INFORME TÉCNICO", 9, negrita=True, color=GRIS, antes=60, despues=10)
    t = _parrafo_antes(ancla, TITULO, 26, negrita=True, color=AZUL, despues=10)
    t.paragraph_format.line_spacing = 1.0
    s = _parrafo_antes(ancla, SUBTITULO, 14, color=TINTA, despues=18)
    _borde_parrafo(s, "bottom", 12, "0D366B", 8)
    _parrafo_antes(ancla, "Preparado para", 9, negrita=True, color=GRIS, antes=24, despues=2)
    _parrafo_antes(ancla, "Instituto Guatemalteco de Turismo (INGUAT)", 11, despues=14)
    _parrafo_antes(ancla, "Elaborado por", 9, negrita=True, color=GRIS, despues=2)
    _parrafo_antes(ancla, "Grupo 3, curso CC3084 Data Science", 11, despues=0)
    _parrafo_antes(ancla, "Departamento de Ciencias de la Computación, Universidad del Valle de Guatemala", 11, despues=8)
    for nombre in equipo:
        _parrafo_antes(ancla, nombre, 10.5, color=GRIS, despues=0)
    _parrafo_antes(ancla, "Fecha y versión", 9, negrita=True, color=GRIS, antes=14, despues=2)
    _parrafo_antes(ancla, f"Guatemala, {hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}. Versión {version}.", 11, despues=0)
    aviso = _parrafo_antes(
        ancla,
        "Documento elaborado con datos institucionales del INGUAT compartidos exclusivamente para uso académico. "
        "Contiene solo cifras agregadas, sin microdatos. Las cifras no constituyen estadística oficial.",
        8.5, color=GRIS, antes=150, despues=0, cursiva=True)
    _borde_parrafo(aviso, "top", 4, "C6C6C6", 6)
    ancla.add_run().add_break(WD_BREAK.PAGE)


def imagenes_centradas(doc) -> None:
    for p in doc.paragraphs:
        if p._p.findall(".//" + qn("w:drawing")):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.keep_with_next = True
            p.paragraph_format.space_after = Pt(2)


def ordenar_matematicas(doc) -> None:
    """pandoc escribe m:sty despues de m:scr fuera del orden del esquema de Office Math; se reordena."""
    orden = ["lit", "nor", "scr", "sty", "brk", "aln"]
    m = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
    for rpr in doc.element.body.iter(m + "rPr"):
        hijos = sorted(list(rpr), key=lambda h: orden.index(_local(h)) if _local(h) in orden else len(orden))
        for h in list(rpr):
            rpr.remove(h)
        # m:nor (texto normal) y m:scr/m:sty son excluyentes en el esquema: con m:nor se descarta m:sty
        if any(_local(h) == "nor" for h in hijos):
            hijos = [h for h in hijos if _local(h) not in ("scr", "sty")]
        for h in hijos:
            rpr.append(h)


def indice_prellenado(doc) -> None:
    """El campo TOC de pandoc llega vacio: Word lo llena al abrir, pero otros visores no. Se insertan las
    entradas (titulos de nivel 1 y 2) como resultado del campo; Word agrega los numeros de pagina al actualizar."""
    from docx.text.paragraph import Paragraph

    body = doc.element.body
    sdt = body.find(qn("w:sdt"))
    if sdt is None:
        return
    contenido = sdt.find(qn("w:sdtContent"))
    campo = None
    for par in contenido.findall(qn("w:p")):
        if par.find(".//" + qn("w:instrText")) is not None:
            campo = par
    if campo is None:
        return
    fin = [fc for fc in campo.iter(qn("w:fldChar")) if fc.get(qn("w:fldCharType")) == "end"]
    if not fin:
        return
    fin_run = fin[0].getparent()
    fin_run.remove(fin[0])
    estilos_toc = {"Heading 1": "toc 1", "Heading 2": "toc 2"}
    anterior = campo
    for par in doc.paragraphs:
        nivel = estilos_toc.get(par.style.name)
        if not nivel or not par.text.strip():
            continue
        nuevo = OxmlElement("w:p")
        anterior.addnext(nuevo)
        entrada = Paragraph(nuevo, doc._body)
        try:
            entrada.style = doc.styles[nivel]
        except KeyError:
            pass
        r = entrada.add_run(par.text.strip())
        _fuente(r)
        anterior = nuevo
    cierre = OxmlElement("w:p")
    anterior.addnext(cierre)
    run = OxmlElement("w:r")
    run.append(fin[0])
    cierre.append(run)


def actualizar_campos(doc) -> None:
    """Word recalcula el indice y los numeros de pagina al abrir el archivo."""
    settings = doc.settings.element
    nodo = settings.find(qn("w:updateFields"))
    if nodo is None:
        nodo = OxmlElement("w:updateFields")
        _insertar_en_orden(settings, nodo, ["updateFields", *_DESPUES_UPDATEFIELDS])
    nodo.set(qn("w:val"), "true")


def maquetar(ruta: Path, equipo: list[str], version: str = "1.0") -> None:
    doc = Document(str(ruta))
    estilos(doc)
    tablas(doc)
    imagenes_centradas(doc)
    pagina(doc)
    portada(doc, equipo, version)
    ordenar_matematicas(doc)
    indice_prellenado(doc)
    actualizar_campos(doc)
    doc.core_properties.title = TITULO
    doc.core_properties.subject = SUBTITULO
    doc.core_properties.author = "Grupo 3, CC3084 Data Science, UVG"
    doc.core_properties.language = "es-GT"
    doc.save(str(ruta))


if __name__ == "__main__":
    maquetar(Path(sys.argv[1]), [])
