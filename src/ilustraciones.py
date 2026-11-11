"""Ilustraciones de los encabezados (SVG en blanco translucido, como imagen de fondo).

La portada lleva la silueta de los tres volcanes del lago (San Pedro, Toliman y Atitlan) sobre el agua, y
cada modulo su propio motivo:
- Modulo 1 (demanda): multitud de visitantes y la ruta de un avion (mercados emisores).
- Modulo 2 (temporal): serie diaria con picos de festividades y un calendario.
- Modulo 3 (oferta): hileras de hoteles con ventanas.
- Modulo 4 (red): el contorno del lago con los 10 pueblos conectados.

Se devuelven como `data:` URL porque st.html elimina los <svg> sueltos de este tamano.
"""

from __future__ import annotations

from urllib.parse import quote

from src import territorio as te

ANCHO, ALTO = 600, 220


def _volcanes(agua: str, intensidad: float = 1.0) -> str:
    o = lambda v: f"{v * intensidad:.3f}"  # noqa: E731
    return (
        f'<path d="M120 220 L250 92 Q262 80 274 92 L410 220 Z" fill="#fff" fill-opacity="{o(.08)}"/>'
        f'<path d="M300 220 L420 70 Q432 56 446 70 L600 200 L600 220 Z" fill="#fff" fill-opacity="{o(.12)}"/>'
        f'<path d="M215 220 L330 118 Q340 109 350 118 L470 220 Z" fill="#fff" fill-opacity="{o(.10)}"/>'
        f'<path d="M0 176 Q75 166 150 176 T300 176 T450 176 T600 176 L600 220 L0 220 Z" fill="{agua}" fill-opacity=".35"/>'
        '<path d="M60 190 Q105 183 150 190 T240 190" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width="1.5"/>'
        '<path d="M300 200 Q350 193 400 200 T500 200 T600 200" fill="none" stroke="#fff" stroke-opacity=".28" stroke-width="1.5"/>'
    )


def _demanda() -> str:
    """Multitud (alturas distintas) y la ruta punteada de un avion."""
    partes = ['<path d="M70 120 Q300 6 540 58" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="2" stroke-dasharray="7 7"/>',
              '<path d="M540 58 l-20 -4 l6 8 l-6 8 z M528 54 l-8 -12 l6 0 l12 13 z M528 62 l-8 12 l6 0 l12 -13 z" '
              'fill="#fff" fill-opacity=".6"/>']
    gente = [(250, 34), (285, 42), (318, 30), (350, 46), (385, 36), (418, 50), (452, 38), (486, 44), (520, 32), (555, 40)]
    for i, (x, h) in enumerate(gente):
        op = .22 if i % 2 else .3
        base = 214
        top = base - h
        partes.append(f'<circle cx="{x}" cy="{top - 11}" r="{9 + h / 12:.1f}" fill="#fff" fill-opacity="{op}"/>')
        partes.append(f'<path d="M{x - 15} {base} Q{x - 15} {top} {x} {top} Q{x + 15} {top} {x + 15} {base} Z" '
                      f'fill="#fff" fill-opacity="{op}"/>')
    return "".join(partes)


def _temporal() -> str:
    """Serie diaria con picos de festividades (puntos) y un calendario."""
    ys = [150, 142, 148, 138, 146, 150, 70, 144, 136, 148, 140, 132, 146, 92, 138, 150, 140, 134, 60, 140, 146, 138, 148, 128, 142]
    xs = [140 + i * 18 for i in range(len(ys))]
    linea = " ".join(f"{x},{y}" for x, y in zip(xs, ys))
    area = f"M{xs[0]} 176 L" + " L".join(f"{x} {y}" for x, y in zip(xs, ys)) + f" L{xs[-1]} 176 Z"
    picos = "".join(f'<circle cx="{x}" cy="{y}" r="6" fill="#fff" fill-opacity=".75"/>' for x, y in zip(xs, ys) if y < 100)
    cal = ['<rect x="470" y="16" width="96" height="78" rx="8" fill="#fff" fill-opacity=".14" stroke="#fff" stroke-opacity=".35"/>',
           '<rect x="470" y="16" width="96" height="18" rx="8" fill="#fff" fill-opacity=".3"/>',
           '<rect x="490" y="9" width="5" height="14" rx="2" fill="#fff" fill-opacity=".6"/>',
           '<rect x="541" y="9" width="5" height="14" rx="2" fill="#fff" fill-opacity=".6"/>']
    for f in range(3):
        for c in range(5):
            op = .65 if (f, c) == (1, 3) else .25
            cal.append(f'<rect x="{479 + c * 17}" y="{42 + f * 16}" width="11" height="10" rx="2" fill="#fff" fill-opacity="{op}"/>')
    dibujo = (f'<path d="{area}" fill="#fff" fill-opacity=".12"/>'
              f'<polyline points="{linea}" fill="none" stroke="#fff" stroke-opacity=".7" stroke-width="2.2" stroke-linejoin="round"/>'
              + picos + "".join(cal))
    # Mas pequeno (75 %, anclado abajo a la derecha) y con el blanco atenuado: sobre el amarillo resaltaba demasiado
    return f'<g transform="translate(150 55) scale(.75)" opacity=".6">{dibujo}</g>'


def _oferta() -> str:
    """Casas de hospedaje en la ladera del lago (techo de dos aguas, puerta y ventanas) entre arboles;
    la mas grande lleva la H. En el lago el hospedaje es sobre todo de casas y posadas, no de edificios."""
    partes = ['<path d="M200 214 Q330 168 600 150 L600 220 L200 220 Z" fill="#fff" fill-opacity=".08"/>']
    # (x, base, ancho, alto del muro)
    casas = [(262, 210, 46, 30), (330, 200, 54, 36), (404, 190, 70, 46), (494, 182, 50, 34), (556, 176, 40, 28)]
    for i, (x, base, w, h) in enumerate(casas):
        op = .3 if i % 2 else .38
        y = base - h
        partes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff" fill-opacity="{op}"/>')
        partes.append(f'<path d="M{x - 6} {y + 1} L{x + w / 2} {y - h * .55} L{x + w + 6} {y + 1} Z" fill="#fff" '
                      f'fill-opacity="{op + .2:.2f}"/>')
        puerta_w = w * .2
        partes.append(f'<rect x="{x + w / 2 - puerta_w / 2:.1f}" y="{base - h * .55:.1f}" width="{puerta_w:.1f}" '
                      f'height="{h * .55:.1f}" rx="1.5" fill="#000" fill-opacity=".12"/>')
        for vx in (x + w * .14, x + w * .66):
            partes.append(f'<rect x="{vx:.1f}" y="{y + h * .25:.1f}" width="{w * .2:.1f}" height="{h * .24:.1f}" rx="1" '
                          f'fill="#000" fill-opacity=".1"/>')
    for tx, tb, r in [(238, 212, 13), (392, 196, 11), (478, 186, 12), (550, 180, 8)]:
        partes.append(f'<rect x="{tx - 2}" y="{tb - 14}" width="4" height="14" fill="#fff" fill-opacity=".3"/>'
                      f'<circle cx="{tx}" cy="{tb - 14 - r * .6:.1f}" r="{r}" fill="#fff" fill-opacity=".28"/>')
    x, base, w, h = casas[2]
    cx, cy = x + w / 2, base - h - h * .55 - 18
    partes.append(f'<circle cx="{cx}" cy="{cy:.1f}" r="13" fill="#fff" fill-opacity=".75"/>'
                  f'<text x="{cx}" y="{cy + 5.5:.1f}" text-anchor="middle" font-family="Arial" font-weight="700" '
                  f'font-size="15" fill="#000" fill-opacity=".35">H</text>')
    return "".join(partes)


def _oferta_edificios() -> str:
    """Version anterior del motivo del modulo 3 (edificios); se conserva por si se quiere volver a ella."""
    edificios = [(250, 62, 70), (318, 52, 104), (378, 74, 132), (460, 50, 92), (518, 64, 116)]
    partes = []
    for i, (x, w, h) in enumerate(edificios):
        y = 205 - h
        partes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="#fff" fill-opacity="{.2 if i % 2 else .26}"/>')
        for fila in range(int((h - 26) // 20)):
            for col in range(int((w - 12) // 14)):
                partes.append(f'<rect x="{x + 8 + col * 14}" y="{y + 12 + fila * 20}" width="7" height="9" rx="1" '
                              f'fill="#fff" fill-opacity="{.55 if (fila + col + i) % 3 == 0 else .3}"/>')
    x, w, h = edificios[2]
    partes.append(f'<circle cx="{x + w / 2}" cy="{205 - h - 18}" r="14" fill="#fff" fill-opacity=".7"/>'
                  f'<text x="{x + w / 2}" y="{205 - h - 12.5}" text-anchor="middle" font-family="Arial" font-weight="700" '
                  f'font-size="16" fill="#000" fill-opacity=".35">H</text>')
    return "".join(partes)


def _red() -> str:
    """Contorno del lago con los 10 pueblos conectados a Panajachel (el hub)."""
    lats = [p[0] for p in te.CONTORNO_LAGO] + [c[0] for c in te.COORDENADAS.values()]
    lons = [p[1] for p in te.CONTORNO_LAGO] + [c[1] for c in te.COORDENADAS.values()]
    x0, x1, y0, y1 = min(lons), max(lons), min(lats), max(lats)
    caja = (250, 20, 330, 160)  # x, y, ancho, alto

    def xy(lat: float, lon: float) -> tuple[float, float]:
        return (caja[0] + (lon - x0) / (x1 - x0) * caja[2], caja[1] + (y1 - lat) / (y1 - y0) * caja[3])

    contorno = " ".join(f"{x:.1f},{y:.1f}" for x, y in (xy(*p) for p in te.CONTORNO_LAGO))
    puntos = {m: xy(*c) for m, c in te.COORDENADAS.items()}
    hx, hy = puntos["Panajachel"]
    lineas = "".join(f'<line x1="{hx:.1f}" y1="{hy:.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="#fff" stroke-opacity=".4" '
                     f'stroke-width="1.4" stroke-dasharray="4 4"/>' for m, (x, y) in puntos.items() if m != "Panajachel")
    nodos = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{11 if m == "Panajachel" else 6}" fill="#fff" '
                    f'fill-opacity="{.85 if m == "Panajachel" else .6}"/>' for m, (x, y) in puntos.items())
    return (f'<polygon points="{contorno}" fill="#fff" fill-opacity=".14" stroke="#fff" stroke-opacity=".45" stroke-width="1.6"/>'
            + lineas + nodos)


_MOTIVOS = {"m1_demanda": _demanda, "m2_temporal": _temporal, "m3_oferta": _oferta, "m4_municipios": _red}


def svg(tema: str | None, agua: str) -> str:
    """Ilustracion del encabezado: el motivo del modulo solo; sin tema, los volcanes de la portada."""
    motivo = _MOTIVOS.get(tema)
    cuerpo = motivo() if motivo else _volcanes(agua)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ANCHO} {ALTO}">{cuerpo}</svg>'


def url(tema: str | None, agua: str) -> str:
    return "data:image/svg+xml," + quote(svg(tema, agua))
