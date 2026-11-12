"""Constructor del informe en Word con control total del formato (python-docx).

Se usa en lugar de una conversion automatica para fijar el ancho de cada columna, justificar el texto,
numerar tablas y figuras con su fuente y componer recuadros de mensaje clave, como en un informe de
consultoria. Los elementos de pagina (portada, encabezado, pie, indice) vienen de maquetar_memoria.py.
"""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.paragraph import Paragraph

from scripts.maquetar_memoria import (
    AZUL, FUENTE, GRIS, TINTA, _borde_parrafo, _fuente, _insertar_en_orden, _ORDEN_TBLPR, actualizar_campos, pagina,
    portada,
)

ANCHO_UTIL_CM = 16.59  # carta (21.59 cm) menos margenes de 2.5 cm
_NEGRITA = re.compile(r"\*\*(.+?)\*\*")


def _runs(parrafo, texto: str, tam: float | None = None, color: RGBColor | None = None, cursiva: bool = False) -> None:
    """Agrega texto con **negritas** en linea."""
    pos = 0
    for m in _NEGRITA.finditer(texto):
        if m.start() > pos:
            _run(parrafo, texto[pos:m.start()], tam, color, False, cursiva)
        _run(parrafo, m.group(1), tam, color, True, cursiva)
        pos = m.end()
    if pos < len(texto):
        _run(parrafo, texto[pos:], tam, color, False, cursiva)


def _run(parrafo, texto, tam, color, negrita, cursiva):
    r = parrafo.add_run(texto)
    if tam:
        r.font.size = Pt(tam)
    if color is not None:
        r.font.color.rgb = color
    r.font.bold = negrita or None
    r.font.italic = cursiva or None
    _fuente(r)
    return r


def _sombra(celda, color: str) -> None:
    tcpr = celda._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    _insertar_en_orden(tcpr, shd, ["cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd", "noWrap",
                                   "tcMar", "textDirection", "tcFitText", "vAlign", "hideMark"])


def _bordes_tabla(tabla, bordes: dict[str, tuple[int, str]]) -> None:
    tblpr = tabla._tbl.tblPr
    previo = tblpr.find(qn("w:tblBorders"))
    if previo is not None:
        tblpr.remove(previo)
    nodo = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b = OxmlElement(f"w:{lado}")
        if lado in bordes:
            b.set(qn("w:val"), "single")
            b.set(qn("w:sz"), str(bordes[lado][0]))
            b.set(qn("w:color"), bordes[lado][1])
        else:
            b.set(qn("w:val"), "nil")
        nodo.append(b)
    _insertar_en_orden(tblpr, nodo, _ORDEN_TBLPR)


def _margenes(tabla, arriba=60, lados=100) -> None:
    tblpr = tabla._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for lado, valor in (("top", arriba), ("left", lados), ("bottom", arriba), ("right", lados)):
        e = OxmlElement(f"w:{lado}")
        e.set(qn("w:w"), str(valor))
        e.set(qn("w:type"), "dxa")
        mar.append(e)
    _insertar_en_orden(tblpr, mar, _ORDEN_TBLPR)


def _ancho_fijo(tabla, anchos_cm: list[float]) -> None:
    """Ancho fijo por columna (grid y cada celda) y diseño 'fixed' para que Word no las comprima."""
    tabla.autofit = False  # python-docx escribe <w:tblLayout w:type="fixed"/>
    tblpr = tabla._tbl.tblPr
    tblw = tblpr.find(qn("w:tblW"))
    if tblw is None:
        tblw = OxmlElement("w:tblW")
        _insertar_en_orden(tblpr, tblw, _ORDEN_TBLPR)
    tblw.set(qn("w:w"), str(int(sum(anchos_cm) * 567)))
    tblw.set(qn("w:type"), "dxa")
    grid = tabla._tbl.tblGrid
    for gc, ancho in zip(grid.findall(qn("w:gridCol")), anchos_cm):
        gc.set(qn("w:w"), str(int(ancho * 567)))
    for fila in tabla.rows:
        for celda, ancho in zip(fila.cells, anchos_cm):
            celda.width = Cm(ancho)


class Informe:
    def __init__(self) -> None:
        self.doc = Document()
        self.n_tabla = 0
        self.n_figura = 0
        self._estilos()
        self._indice_ancla: Paragraph | None = None

    # ------------------------------------------------------------------ estilos
    def _estilo(self, nombre, tam, negrita=False, color=TINTA, antes=0, despues=6, cursiva=False, inter=1.15,
                siguiente=False, salto=False, alin=None, fuente=FUENTE, sangria=None):
        estilos = self.doc.styles
        try:
            st = estilos[nombre]
        except KeyError:
            st = estilos.add_style(nombre, WD_STYLE_TYPE.PARAGRAPH)
            st.base_style = estilos["Normal"]
        st.font.name = fuente
        st.font.size = Pt(tam)
        st.font.bold = negrita
        st.font.italic = cursiva
        st.font.color.rgb = color
        rpr = st.element.get_or_add_rPr()
        rf = rpr.find(qn("w:rFonts"))
        if rf is None:
            rf = OxmlElement("w:rFonts")
            rpr.insert(0, rf)
        for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rf.set(qn(a), fuente)
        for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
            rf.attrib.pop(qn(a), None)
        pf = st.paragraph_format
        pf.space_before, pf.space_after, pf.line_spacing = Pt(antes), Pt(despues), inter
        pf.keep_with_next, pf.page_break_before = siguiente, salto
        if alin is not None:
            pf.alignment = alin
        if sangria is not None:
            pf.left_indent = Cm(sangria)
        return st

    def _estilos(self) -> None:
        j = WD_ALIGN_PARAGRAPH.JUSTIFY
        self._estilo("Normal", 10.5, despues=6, alin=j)
        self._estilo("Heading 1", 17, negrita=True, color=AZUL, despues=14, siguiente=True, salto=True,
                     alin=WD_ALIGN_PARAGRAPH.LEFT, inter=1.0)
        self._estilo("Heading 2", 12.5, negrita=True, antes=16, despues=6, siguiente=True, alin=WD_ALIGN_PARAGRAPH.LEFT)
        self._estilo("Heading 3", 11, negrita=True, color=AZUL, antes=12, despues=4, siguiente=True,
                     alin=WD_ALIGN_PARAGRAPH.LEFT)
        self._estilo("List Bullet", 10.5, despues=3, alin=j)
        self._estilo("List Number", 10.5, despues=3, alin=j)
        self._estilo("Leyenda", 9.5, negrita=True, antes=12, despues=4, siguiente=True, alin=WD_ALIGN_PARAGRAPH.LEFT)
        self._estilo("Fuente", 8.5, cursiva=True, color=GRIS, antes=4, despues=12, alin=WD_ALIGN_PARAGRAPH.LEFT)
        self._estilo("Codigo", 8, despues=0, inter=1.0, alin=WD_ALIGN_PARAGRAPH.LEFT, fuente="Consolas")
        self._estilo("Celda", 8.5, despues=0, inter=1.05, alin=WD_ALIGN_PARAGRAPH.LEFT)
        self._estilo("Indice 1", 10.5, negrita=True, antes=5, despues=1, alin=WD_ALIGN_PARAGRAPH.LEFT)
        self._estilo("Indice 2", 10, despues=1, alin=WD_ALIGN_PARAGRAPH.LEFT, sangria=0.6)
        self._estilo("Titulo indice", 17, negrita=True, color=AZUL, despues=14, alin=WD_ALIGN_PARAGRAPH.LEFT)

    # ------------------------------------------------------------------ bloques
    def h1(self, texto):
        self.doc.add_heading(texto, level=1)

    def h2(self, texto):
        self.doc.add_heading(texto, level=2)

    def h3(self, texto):
        self.doc.add_heading(texto, level=3)

    def p(self, texto, alin=None, despues=None):
        par = self.doc.add_paragraph(style="Normal")
        _runs(par, texto)
        if alin is not None:
            par.alignment = alin
        if despues is not None:
            par.paragraph_format.space_after = Pt(despues)
        return par

    def vinetas(self, items, numeradas=False):
        for it in items:
            par = self.doc.add_paragraph(style="List Number" if numeradas else "List Bullet")
            _runs(par, it)

    def leyenda(self, texto):
        par = self.doc.add_paragraph(style="Leyenda")
        _runs(par, texto)

    def fuente(self, texto):
        par = self.doc.add_paragraph(style="Fuente")
        if not texto.startswith("Fuente"):
            texto = "Fuente: " + texto
        _runs(par, texto, cursiva=True)

    def salto(self):
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def tabla(self, titulo: str, encabezado: list[str], filas: list[list], anchos: list[float], fuente: str,
              numericas: tuple[int, ...] = (), resaltar_primera: bool = False, tam: float = 8.5):
        """Tabla numerada con anchos fijos (cm), filetes, encabezado sombreado y repetido, y nota de fuente."""
        self.n_tabla += 1
        self.leyenda(f"Tabla {self.n_tabla}. {titulo}")
        escala = ANCHO_UTIL_CM / sum(anchos) if sum(anchos) > ANCHO_UTIL_CM else 1.0
        anchos = [a * escala for a in anchos]
        t = self.doc.add_table(rows=1 + len(filas), cols=len(encabezado))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        _ancho_fijo(t, anchos)
        _bordes_tabla(t, {"top": (12, "161616"), "bottom": (12, "161616"), "insideH": (4, "D0D0D0")})
        _margenes(t)
        for i, fila in enumerate([encabezado] + filas):
            tr = t.rows[i]
            trpr = tr._tr.get_or_add_trPr()
            trpr.append(OxmlElement("w:cantSplit"))
            if i == 0:
                trpr.append(OxmlElement("w:tblHeader"))
            for j, valor in enumerate(fila):
                c = tr.cells[j]
                c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP if i else WD_CELL_VERTICAL_ALIGNMENT.BOTTOM
                par = c.paragraphs[0]
                par.style = self.doc.styles["Celda"]
                par.alignment = WD_ALIGN_PARAGRAPH.RIGHT if (j in numericas and i) else WD_ALIGN_PARAGRAPH.LEFT
                negrita = i == 0 or (resaltar_primera and j == 0)
                texto = str(valor)
                _runs(par, f"**{texto}**" if negrita and texto else texto, tam=tam)
                if i == 0:
                    _sombra(c, "E8E8E8")
                elif resaltar_primera and j == 0:
                    _sombra(c, "F4F4F4")
        self.fuente(fuente)
        return t

    def ficha(self, codigo: str, nombre: str, campos: list[tuple[str, str]]):
        """Ficha tecnica de indicador: dos columnas con ancho fijo (rotulo 4.6 cm, contenido 12 cm)."""
        self.h3(f"{codigo} {nombre}")
        t = self.doc.add_table(rows=len(campos), cols=2)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        _ancho_fijo(t, [4.6, ANCHO_UTIL_CM - 4.6])
        _bordes_tabla(t, {"top": (12, "0D366B"), "bottom": (8, "0D366B"), "insideH": (4, "D0D0D0")})
        _margenes(t)
        for i, (rotulo, contenido) in enumerate(campos):
            fila = t.rows[i]
            fila._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
            a, b = fila.cells
            _sombra(a, "F4F4F4")
            pa = a.paragraphs[0]
            pa.style = self.doc.styles["Celda"]
            _runs(pa, f"**{rotulo}**", tam=8.5)
            pb = b.paragraphs[0]
            pb.style = self.doc.styles["Celda"]
            if rotulo.startswith("4."):
                _run(pb, contenido, 8, None, False, False)
                for r in pb.runs:
                    _fuente(r, "Consolas")
            else:
                _runs(pb, contenido, tam=8.5)
        espacio = self.doc.add_paragraph()
        espacio.paragraph_format.space_after = Pt(4)

    def recuadro(self, titulo: str, texto: str):
        """Recuadro de mensaje clave (celda unica sombreada con filete izquierdo azul)."""
        t = self.doc.add_table(rows=1, cols=1)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        _ancho_fijo(t, [ANCHO_UTIL_CM])
        _bordes_tabla(t, {"left": (24, "0D366B")})
        _margenes(t, arriba=110, lados=180)
        c = t.rows[0].cells[0]
        _sombra(c, "EEF3FA")
        p1 = c.paragraphs[0]
        p1.style = self.doc.styles["Celda"]
        _runs(p1, f"**{titulo}**", tam=9.5, color=AZUL)
        p2 = c.add_paragraph(style="Celda")
        p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p2.paragraph_format.space_before = Pt(3)
        _runs(p2, texto, tam=9.5)
        sep = self.doc.add_paragraph()
        sep.paragraph_format.space_after = Pt(2)

    def figura(self, ruta: Path, titulo: str, fuente: str, ancho_cm: float = ANCHO_UTIL_CM):
        self.n_figura += 1
        self.leyenda(f"Figura {self.n_figura}. {titulo}")
        par = self.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.keep_with_next = True
        par.paragraph_format.space_after = Pt(2)
        par.add_run().add_picture(str(ruta), width=Cm(ancho_cm))
        self.fuente(fuente)

    def codigo(self, texto: str):
        t = self.doc.add_table(rows=1, cols=1)
        _ancho_fijo(t, [ANCHO_UTIL_CM])
        _bordes_tabla(t, {"left": (12, "8D8D8D")})
        _margenes(t, arriba=80, lados=140)
        c = t.rows[0].cells[0]
        _sombra(c, "F4F4F4")
        lineas = texto.rstrip().splitlines()
        primero = True
        for linea in lineas:
            par = c.paragraphs[0] if primero else c.add_paragraph()
            primero = False
            par.style = self.doc.styles["Codigo"]
            r = par.add_run(linea if linea else " ")
            r.font.size = Pt(7.5)
            _fuente(r, "Consolas")
        self.doc.add_paragraph().paragraph_format.space_after = Pt(2)

    # ------------------------------------------------------------------ indice
    def ancla_indice(self):
        titulo = self.doc.add_paragraph(style="Titulo indice")
        _runs(titulo, "Contenido")
        self._indice_ancla = self.doc.add_paragraph()

    def _campo_indice(self):
        """Campo TOC prellenado con los titulos (Word agrega los numeros de pagina al actualizar)."""
        ancla = self._indice_ancla
        def fld(tipo):
            e = OxmlElement("w:fldChar")
            e.set(qn("w:fldCharType"), tipo)
            r = OxmlElement("w:r")
            r.append(e)
            return r
        ancla._p.append(fld("begin"))
        r = OxmlElement("w:r")
        instr = OxmlElement("w:instrText")
        instr.set(qn("xml:space"), "preserve")
        instr.text = ' TOC \\o "1-2" \\h \\z \\u '
        r.append(instr)
        ancla._p.append(r)
        ancla._p.append(fld("separate"))
        previo = ancla._p
        for par in list(self.doc.paragraphs):
            nivel = {"Heading 1": "Indice 1", "Heading 2": "Indice 2"}.get(par.style.name)
            if not nivel or not par.text.strip():
                continue
            nuevo = OxmlElement("w:p")
            previo.addnext(nuevo)
            entrada = Paragraph(nuevo, self.doc._body)
            entrada.style = self.doc.styles[nivel]
            _run(entrada, par.text.strip(), None, None, False, False)
            previo = nuevo
        cierre = OxmlElement("w:p")
        previo.addnext(cierre)
        cierre.append(fld("end"))
        # Word asocia el campo TOC a los estilos 'TOC 1' y 'TOC 2'; se definen iguales a los del indice
        for nombre, base in (("toc 1", "Indice 1"), ("toc 2", "Indice 2")):
            try:
                self.doc.styles[nombre]
            except KeyError:
                st = self.doc.styles.add_style(nombre, WD_STYLE_TYPE.PARAGRAPH)
                st.base_style = self.doc.styles[base]

    # ------------------------------------------------------------------ cierre
    def guardar(self, ruta: Path, equipo: list[str], version: str = "2.0"):
        self._campo_indice()
        pagina(self.doc)
        portada(self.doc, equipo, version)
        actualizar_campos(self.doc)
        zoom = self.doc.settings.element.find(qn("w:zoom"))
        if zoom is not None and zoom.get(qn("w:percent")) is None:
            zoom.set(qn("w:percent"), "100")
        cp = self.doc.core_properties
        cp.title = "Observatorio de Inteligencia Turística del Lago de Atitlán"
        cp.subject = "Memoria técnica y recomendaciones para la gestión del destino"
        cp.author = "Grupo 3, CC3084 Data Science, UVG"
        cp.last_modified_by = "Grupo 3, CC3084 Data Science, UVG"
        cp.language = "es-GT"
        cp.comments = ""
        cp.keywords = "turismo; observatorio; Lago de Atitlán; INGUAT"
        self.doc.save(str(ruta))


def _borde_inferior(parrafo):
    _borde_parrafo(parrafo, "bottom", 6, "C6C6C6", 4)
