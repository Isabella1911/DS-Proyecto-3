"""Lectura de las fichas de indicadores (docs/memoria/fichas.md) para el informe en Word.

Las formulas estan escritas en LaTeX; se convierten a notacion legible (Σ, ÷, subindices entre
corchetes) porque el informe se dirige a directivos y debe leerse igual en cualquier procesador.
"""

from __future__ import annotations

import re
from pathlib import Path

_SIMBOLOS = {r"\cdot": "·", r"\geq": "≥", r"\ge": "≥", r"\le": "≤", r"\times": "×", r"\lvert": "|", r"\rvert": "|",
             r"\in": "∈", r"\neq": "≠", r"\#": "#", r"\,": " ", r"\ ": " ", r"\max": "máx", r"\log_{10}": "log₁₀",
             r"\sqrt": "√", r"\hat": "", r"\widehat": "", r"\overline": "", r"\left": "", r"\right": ""}


def _llaves(s: str, i: int) -> tuple[str, int]:
    """Contenido del grupo {...} que empieza en s[i] y posicion siguiente."""
    nivel, j = 0, i
    while j < len(s):
        if s[j] == "{":
            nivel += 1
        elif s[j] == "}":
            nivel -= 1
            if nivel == 0:
                return s[i + 1:j], j + 1
        j += 1
    return s[i + 1:], len(s)


def latex_a_texto(expr: str) -> str:
    s = expr
    # fracciones
    while True:
        m = re.search(r"\\d?frac", s)
        if not m:
            break
        num, k = _llaves(s, m.end())
        den, k2 = _llaves(s, k)
        s = s[:m.start()] + f"({latex_a_texto(num)}) ÷ ({latex_a_texto(den)})" + s[k2:]
    s = re.sub(r"\\text\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\mathrm\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\sum_\{([^}]*)\}\^\{\}", r"Σ[\1] ", s)
    s = re.sub(r"\\sum_\{([^}]*)\}", r"Σ[\1] ", s)
    s = re.sub(r"\\sum_(\w)", r"Σ[\1] ", s)
    s = s.replace(r"\sum", "Σ ")
    for k, v in sorted(_SIMBOLOS.items(), key=lambda kv: -len(kv[0])):
        s = s.replace(k, v)
    s = re.sub(r"_\{([^}]*)\}", r"[\1]", s)
    s = re.sub(r"_(\w)", r"[\1]", s)
    s = re.sub(r"\^\{([^}]*)\}", r"^\1", s)
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"\(\s*([^()÷]+?)\s*\)\s*÷", lambda m: (m.group(1) if " " not in m.group(1).strip() else f"({m.group(1).strip()})") + " ÷", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _limpiar(celda: str) -> str:
    celda = re.sub(r"\$([^$]+)\$", lambda m: latex_a_texto(m.group(1)), celda)
    return celda.replace("`", "").replace("*", "").strip()


def leer(ruta: Path) -> list[dict]:
    """Lista de fichas: {'seccion', 'codigo', 'nombre', 'campos': [(rotulo, contenido), ...]}."""
    fichas, seccion = [], ""
    actual = None
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.startswith("## "):
            seccion = linea[3:].strip()
        elif linea.startswith("### "):
            codigo, _, nombre = linea[4:].partition(" ")
            actual = {"seccion": seccion, "codigo": codigo, "nombre": nombre.strip(), "campos": []}
            fichas.append(actual)
        elif actual is not None and linea.startswith("| ") and not linea.startswith("| Campo") and not linea.startswith("|:"):
            partes = [x.strip() for x in linea.strip().strip("|").split(" | ")]
            if len(partes) >= 2:
                rotulo = partes[0]
                contenido = " | ".join(partes[1:])
                actual["campos"].append((rotulo, contenido if rotulo.startswith("4.") else _limpiar(contenido)))
    for f in fichas:
        f["campos"] = [(r, c.replace("`", "")) for r, c in f["campos"]]
    return fichas


# Formulas redactadas a mano para el informe (notacion legible, equivalente a la de fichas.md)
FORMULAS = {
    "I-01": "V̄ = (1/T) · Σₜ Vₜ,  donde Vₜ = Σ visitantes del mes t y T = número de meses con dato",
    "I-02": "DP̄ = (1/T) · Σₜ DPₜ,  donde DPₜ = Σ días-persona del mes t",
    "I-03": "EM = Σ DP(turistas) ÷ Σ V(turistas),  turistas = segmento «mayor a 1 día»",
    "I-04": "%T = Σ V(turistas) ÷ Σ V(todos los segmentos);  %E = 1 − %T",
    "I-05": "Ē = (1/T) · Σₜ Eₜ;   IEEᵢ = (Eᵢ ÷ Σⱼ Eⱼ) ÷ (Nᵢ ÷ Σⱼ Nⱼ),  E = extranjeros, N = nacionales, j = municipios",
    "I-06": "Pₚ = Σ Vₚ ÷ Σ V(todos los países extranjeros)",
    "I-07": "EMₚ = Σ DPₚ(turistas) ÷ Σ Vₚ(turistas)",
    "I-08": "Lift = V̄(días del evento) ÷ V̄(días regulares) − 1",
    "I-09": "Lift ajustado = (1/n) · Σ_d [ V_d ÷ V̄(días regulares del mismo día de la semana) ] − 1",
    "I-10": "Índice_dds = 100 · V̄_dds ÷ promedio de los siete V̄_dds   (dds = día de la semana, solo días regulares)",
    "I-11": "PFS = V̄(sábado y domingo) ÷ V̄(lunes a viernes)",
    "I-12": "A: D̂ₜ = F · Mₜ,  F = Σ Dₜ ÷ Σ Mₜ (meses observados).   B: D̂ₜ = L · S_m(t),  L = Σ Dₜ ÷ Σ S_m(t)",
    "I-13": "MAPE = (100/n) · Σ |D̂ₜ − Dₜ| ÷ Dₜ;   MAE = (1/n) · Σ |D̂ₜ − Dₜ|;   RMSE = √[(1/n) · Σ (D̂ₜ − Dₜ)²]",
    "I-14": "S_m = promedio de los años a de (M_a,m ÷ M̄_a),  M = llegadas internacionales, M̄_a = promedio mensual del año",
    "I-15": "Rₜ = V(mes t) ÷ P̄(presencia diaria media del mes t);   presencia implícita = D̂ₜ ÷ R̄",
    "I-16": "C_a = Σ_tipo C(a, cuarto trimestre, tipo),  C = establecimientos, habitaciones o plazas cama",
    "I-17": "Índice publicado (0 a 1); sobre inventario: habitaciones-noche ocupadas ÷ (habitaciones × días del año)",
    "I-18": "Cₒ = Σₜ noches en hotel formalₒ ÷ Σₜ Σ (DP − V)ₒ(turistas),  o = extranjeros/no residentes o nacionales/residentes",
    "I-19": "%ₖ = encuestas de la categoría k ÷ encuestas del segmento con destino al lago (ola vigente)",
    "I-20": "Índiceᵢ = 100 · V̄ᵢ ÷ V̄(Panajachel)",
    "I-21": "Larga estancia: EMᵢ ≥ P75(EM) e IEEᵢ ≥ 1;  hub: V̄ᵢ ≥ 0.6 · máx V̄;  visita corta: resto",
    "I-22": "Estabilidad = Σⱼ #{i ≠ j : clase sin j = clase con todos} ÷ Σⱼ (n − 1)",
    "I-23": "Índice_c,t = 100 · V_c,t ÷ V̄_c,  c = clase de municipio",
}


def fichas_informe(ruta: Path) -> list[dict]:
    fichas = leer(ruta)
    for f in fichas:
        f["campos"] = [(r, FORMULAS.get(f["codigo"], c) if r.startswith("3.") else c) for r, c in f["campos"]]
    return fichas
