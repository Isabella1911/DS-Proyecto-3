"""Genera el icono del observatorio (el lago con sus tres volcanes) en tres variantes, con su logotipo.

    python scripts/generar_iconos.py

Salida en static/: icono_<variante>.svg (32x32, pestana del navegador y barra lateral plegada) y
logo_<variante>.svg (icono + nombre, barra lateral). Variantes:
- rainbow: un color por modulo (rojo, naranja, verde; lago celeste -> morado)
- teal: monocromatico en teal
- azul: degradado de los azules de la portada
"""

from pathlib import Path

STATIC = Path(__file__).resolve().parents[1] / "static"

# Volcanes: San Pedro (izq.), Atitlan (atras, el mas alto) y Toliman (der.)
V_IZQ = "M2 22 L8 13.2 Q9 11.8 10 13.2 L15.5 22 Z"
V_ATRAS = "M9 22 L16.9 8.2 Q18 6.6 19.1 8.2 L27 22 Z"
V_DER = "M15 22 L21 13.6 Q22 12.3 23 13.6 L30.5 22 Z"
LAGO = "M1 21 H31 V25.5 Q31 30 26.5 30 H5.5 Q1 30 1 25.5 Z"
OLAS = ('<path d="M5 24.8 Q8 23.3 11 24.8 T17 24.8" fill="none" stroke="#fff" stroke-opacity=".85" stroke-width="1.3" stroke-linecap="round"/>'
        '<path d="M15 27.4 Q18 25.9 21 27.4 T27 27.4" fill="none" stroke="#fff" stroke-opacity=".7" stroke-width="1.3" stroke-linecap="round"/>')

VARIANTES = {
    "rainbow": {
        "defs": ('<linearGradient id="lago" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#4cc9f0"/>'
                 '<stop offset="1" stop-color="#7b2cbf"/></linearGradient>'),
        "atras": "#f77f00", "izq": "#d62839", "der": "#2d9f5a", "lago": "url(#lago)",
        "titulo": "#161616", "sub": "#525252",
    },
    "teal": {
        "defs": "", "atras": "#14a3a5", "izq": "#0b6e70", "der": "#0f8b8d", "lago": "#0f8b8d",
        "titulo": "#0b4f50", "sub": "#0f8b8d",
    },
    "azul": {
        "defs": ('<linearGradient id="volcan" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#00314d"/>'
                 '<stop offset="1" stop-color="#0067a0"/></linearGradient>'
                 '<linearGradient id="volcan2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#004a73"/>'
                 '<stop offset="1" stop-color="#0084bb"/></linearGradient>'
                 '<linearGradient id="lago" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0084bb"/>'
                 '<stop offset="1" stop-color="#4fb0dc"/></linearGradient>'),
        "atras": "url(#volcan)", "izq": "url(#volcan2)", "der": "url(#volcan2)", "lago": "url(#lago)",
        "titulo": "#00314d", "sub": "#0067a0",
    },
}


def dibujo(v: dict) -> str:
    return (f'<path d="{V_ATRAS}" fill="{v["atras"]}"/><path d="{V_IZQ}" fill="{v["izq"]}"/>'
            f'<path d="{V_DER}" fill="{v["der"]}" fill-opacity=".92"/><path d="{LAGO}" fill="{v["lago"]}"/>{OLAS}')


def icono(v: dict) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">'
            f'<defs>{v["defs"]}</defs>{dibujo(v)}</svg>\n')


def logo(v: dict) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="260" height="40" viewBox="0 0 260 40">'
            f'<defs>{v["defs"]}</defs><g transform="translate(0 2) scale(1.12)">{dibujo(v)}</g>'
            f'<text x="44" y="19" font-family="IBM Plex Sans, Helvetica, Arial, sans-serif" font-size="14" font-weight="600" '
            f'fill="{v["titulo"]}">Observatorio de Turismo</text>'
            f'<text x="44" y="33" font-family="IBM Plex Sans, Helvetica, Arial, sans-serif" font-size="11" '
            f'fill="{v["sub"]}">Guatemala · Lago de Atitlán</text></svg>\n')


if __name__ == "__main__":
    for nombre, v in VARIANTES.items():
        (STATIC / f"icono_{nombre}.svg").write_text(icono(v), encoding="utf-8")
        (STATIC / f"logo_{nombre}.svg").write_text(logo(v), encoding="utf-8")
        print("static/icono_" + nombre + ".svg", "static/logo_" + nombre + ".svg")
