"""Figuras del observatorio (Plotly). Cada funcion recibe tablas ya calculadas por src.indicadores."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.estilo import (
    COLOR_DESTACADO, COLOR_ESTIMADO, COLOR_EVENTO, COLOR_HISTORIA, COLOR_OCUPACION, COLOR_REAL, COLORES_CLASE,
    COLORES_ORIGEN, COLORES_SEGMENTO, CUADRICULA, PATRON_EXCURSIONISTA, SECUENCIAL_AZUL, SIMBOLOS_CLASE, TRAZOS_CLASE,
    aplicar_estilo, fechas_en_espanol,
)
from src.normalizar import EVENTO_REGULAR, MUNICIPIO_CORTO, SEG_EXCURSIONISTA, SEG_TURISTA

MES_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def _mes(t: pd.Timestamp) -> str:
    return f"{MES_ES[t.month - 1]} {t.year}"


# ---------------------------------------------------------------------------------------------
# Modulo 1


def fig_municipios(tabla: pd.DataFrame) -> go.Figure:
    """Barras horizontales apiladas por origen: visitantes promedio por mes de cada municipio.

    tabla: index municipio, columnas Nacional / Extranjero (promedio mensual)."""
    t = tabla.assign(total=tabla.sum(axis=1)).sort_values("total")
    y = [MUNICIPIO_CORTO.get(m, m) for m in t.index]
    fig = go.Figure()
    for origen in ["Nacional", "Extranjero"]:
        fig.add_bar(
            y=y, x=t[origen], name=origen, orientation="h", customdata=list(t.index),
            marker=dict(color=COLORES_ORIGEN[origen]), unselected=dict(marker=dict(opacity=0.3)),
            hovertemplate="<b>%{customdata}</b><br>" + origen + ": %{x:,.0f} por mes<extra></extra>",
        )
    fig.update_layout(barmode="stack", clickmode="event+select", dragmode=False)
    fig.update_xaxes(title_text="Visitantes promedio por mes", tickformat=",.0f")
    return aplicar_estilo(fig, alto=380)


def fig_segmentacion(seg: pd.DataFrame) -> go.Figure:
    """Barras apiladas por segmento y, sobre cada barra, el porcentaje de turistas con pernocta.
    Un solo eje: el porcentaje va como rotulo, no en un eje secundario con otra escala."""
    fig = go.Figure()
    x = [_mes(t) for t in seg.index]
    for s in [SEG_TURISTA, SEG_EXCURSIONISTA]:
        fig.add_bar(x=x, y=seg[s], name=s,
                    marker=dict(color=COLORES_SEGMENTO[s], pattern_shape=PATRON_EXCURSIONISTA if s == SEG_EXCURSIONISTA else ""),
                    hovertemplate="%{x}<br>" + s + ": %{y:,.0f}<extra></extra>")
    total = seg[[SEG_TURISTA, SEG_EXCURSIONISTA]].sum(axis=1, min_count=1)
    for xi, tot, pct in zip(x, total, seg["pct_turistas"]):
        if pd.notna(tot):
            fig.add_annotation(x=xi, y=tot, text=f"{pct:.0%}", showarrow=False, yanchor="bottom", yshift=2,
                               font=dict(size=10, color=COLOR_REAL))
        else:
            fig.add_annotation(x=xi, y=0, text="Sin dato", showarrow=False, yanchor="bottom", textangle=-90,
                               font=dict(size=10, color=COLOR_HISTORIA))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="Visitantes únicos del mes", tickformat=",.0f", range=[0, float(total.max()) * 1.12])
    return aplicar_estilo(fig, alto=340)


def fig_top_paises(top: pd.DataFrame) -> go.Figure:
    t = top.sort_values("visitantes")
    fig = go.Figure(go.Bar(
        y=t.index, x=t["visitantes"], orientation="h", marker_color=COLORES_ORIGEN["Extranjero"],
        text=[f"{p:.0%}" for p in t["pct"]], textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} visitantes<br>%{text} de los extranjeros<extra></extra>",
    ))
    fig.update_xaxes(title_text="Visitantes en el periodo (suma de meses)", tickformat=",.0f", range=_rango_con_etiquetas(t["visitantes"]))
    return aplicar_estilo(fig, alto=340)


def _rango_con_etiquetas(valores: pd.Series, holgura: float = 0.22) -> list[float]:
    """Rango del eje con espacio para las etiquetas de texto fuera de las barras (en pantallas angostas
    no se recortan contra el borde ni se montan sobre los nombres del eje)."""
    lo, hi = min(0.0, float(valores.min())), max(0.0, float(valores.max()))
    ancho = (hi - lo) or 1.0
    return [lo - holgura * ancho if lo < 0 else 0, hi + holgura * ancho]


def fig_estadia_paises(top: pd.DataFrame, estadia_nacional: float, estadia_total: float) -> go.Figure:
    """Puntos: estadia media ponderada por nacionalidad, con referencias nacional y global."""
    t = top.sort_values("estadia_media")
    fig = go.Figure(go.Scatter(
        y=t.index, x=t["estadia_media"], mode="markers", marker=dict(size=11, color=COLORES_ORIGEN["Extranjero"]),
        hovertemplate="<b>%{y}</b><br>%{x:.2f} días por turista<extra></extra>", name="Extranjeros",
    ))
    # Referencias en lineas punteadas; sus rotulos van en la parte baja, a ambos lados, para no encimarse
    refs = [(estadia_total, "Promedio general", COLOR_REAL), (estadia_nacional, "Nacionales", COLORES_ORIGEN["Nacional"])]
    refs = sorted([r for r in refs if pd.notna(r[0])], key=lambda r: r[0])
    for i, (valor, texto, color) in enumerate(refs):
        fig.add_vline(x=valor, line=dict(color=color, dash="dot", width=1.5))
        fig.add_annotation(x=valor, y=0, yref="paper", text=f"{texto}: {valor:.2f}", showarrow=False,
                           xanchor="right" if i == 0 else "left", xshift=-4 if i == 0 else 4, yanchor="bottom",
                           font=dict(size=11, color=color), bgcolor="rgba(255,255,255,.85)")
    tope = max([float(t["estadia_media"].max())] + [r[0] for r in refs])
    fig.update_xaxes(title_text="Días por turista con pernocta", range=[0, tope * 1.35])
    fig.update_layout(showlegend=False)
    return aplicar_estilo(fig, alto=340)


# ---------------------------------------------------------------------------------------------
# Modulo 2


def fig_serie_diaria(diaria: pd.DataFrame, evento_sel: str | None) -> go.Figure:
    fig = go.Figure()
    fig.add_scatter(x=diaria.index, y=diaria["visitantes"], mode="lines", name="Presencia diaria",
                    line=dict(color=COLOR_HISTORIA, width=1), connectgaps=False,
                    hovertemplate="%{x|%d/%m/%Y}<br>%{y:,.0f} visitantes<extra></extra>")
    ev = diaria[(diaria["evento"].notna()) & (diaria["evento"] != EVENTO_REGULAR)]
    fig.add_scatter(x=ev.index, y=ev["visitantes"], mode="markers", name="Día con festividad",
                    marker=dict(color=COLOR_EVENTO, size=6), customdata=ev["evento"],
                    hovertemplate="%{x|%d/%m/%Y}<br><b>%{customdata}</b><br>%{y:,.0f} visitantes<extra></extra>")
    if evento_sel:
        dias = diaria.index[diaria["evento"] == evento_sel]
        for d in dias:
            fig.add_vrect(x0=d - pd.Timedelta(hours=12), x1=d + pd.Timedelta(hours=12), fillcolor=COLOR_DESTACADO,
                          opacity=0.18, line_width=0)
        sel = diaria.loc[dias]
        fig.add_scatter(x=sel.index, y=sel["visitantes"], mode="markers", name=evento_sel,
                        marker=dict(color=COLOR_DESTACADO, size=9, line=dict(color="white", width=1)),
                        hovertemplate="%{x|%d/%m/%Y}<br>%{y:,.0f} visitantes<extra></extra>")
    # Una franja por cada tramo continuo sin cobertura (mas de 3 dias): nunca se dibuja como cero
    huecos = diaria["visitantes"].isna()
    tramo = (huecos != huecos.shift()).cumsum()
    primera = True
    for _, g in diaria[huecos].groupby(tramo[huecos]):
        if len(g) <= 3:
            continue
        fig.add_vrect(x0=g.index.min() - pd.Timedelta(hours=12), x1=g.index.max() + pd.Timedelta(hours=12),
                      fillcolor=CUADRICULA, opacity=0.55, line_width=0,
                      annotation=dict(text="Sin cobertura" if primera else "", font=dict(size=10, color=COLOR_HISTORIA)),
                      annotation_position="top left")
        primera = False
    fig.update_yaxes(title_text="Visitantes presentes en el día", tickformat=",.0f")
    fig.update_xaxes(rangeslider=dict(visible=True, thickness=0.06),
                     range=[diaria.index.min() - pd.Timedelta(days=3), diaria.index.max() + pd.Timedelta(days=3)])
    aplicar_estilo(fig, alto=420)
    # Unica grafica con acercamiento: el eje de fechas se mueve con la barra inferior (rangeslider)
    fig.update_xaxes(fixedrange=False)
    return fig


def fig_lift(lift: pd.DataFrame, columna: str, seleccionado: str | None) -> go.Figure:
    t = lift.sort_values(columna)
    colores = [COLOR_DESTACADO if e == seleccionado else COLOR_EVENTO for e in t.index]
    fig = go.Figure(go.Bar(
        y=t.index, x=t[columna], orientation="h", marker_color=colores, customdata=t["dias"],
        text=[f"{v:+.0%}" for v in t[columna]], textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Lift %{x:+.1%}<br>%{customdata} días observados<extra></extra>",
    ))
    fig.add_vline(x=0, line=dict(color=COLOR_REAL, width=1))
    fig.update_xaxes(title_text="Impacto frente al día regular promedio", tickformat="+.0%", range=_rango_con_etiquetas(t[columna]))
    fig.update_layout(clickmode="event+select", dragmode=False)
    return aplicar_estilo(fig, alto=360)


def fig_patron_semanal(patron: pd.DataFrame) -> go.Figure:
    colores = [COLOR_REAL if d in ("Sábado", "Domingo") else COLOR_HISTORIA for d in patron.index]
    fig = go.Figure(go.Bar(
        x=patron.index, y=patron["indice"], marker_color=colores, customdata=patron["promedio"],
        text=[f"{v:.0f}" for v in patron["indice"]], textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Índice %{y:.0f}<br>%{customdata:,.0f} visitantes promedio<extra></extra>",
    ))
    fig.add_hline(y=100, line=dict(color=COLOR_HISTORIA, dash="dot", width=1))
    fig.update_yaxes(title_text="Índice", range=[0, float(patron["indice"].max()) * 1.15])
    fig.update_xaxes(tickangle=0, ticktext=[d[:3] for d in patron.index], tickvals=list(patron.index))
    return aplicar_estilo(fig, alto=340)


def fig_mensual_estimada(obs: pd.Series, estimados: pd.Series) -> go.Figure:
    """Serie mensual observada (tinta) y Estimación (violeta discontinua, rotulada)."""
    fig = go.Figure()
    fig.add_scatter(x=obs.index, y=obs.values, mode="lines+markers", name="Observado", connectgaps=False,
                    line=dict(color=COLOR_REAL, width=2), marker=dict(size=7),
                    hovertemplate="%{x|%m/%Y}<br>%{y:,.0f} visitantes<extra>Observado</extra>")
    # Puente punteado entre el ultimo observado, la estimacion y el siguiente observado
    puente = pd.concat([obs.dropna()[obs.dropna().index < estimados.index.min()].tail(1), estimados,
                        obs.dropna()[obs.dropna().index > estimados.index.max()].head(1)])
    fig.add_scatter(x=puente.index, y=puente.values, mode="lines", line=dict(color=COLOR_ESTIMADO, dash="dash", width=2),
                    showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=estimados.index, y=estimados.values, mode="markers+text", name="Estimación",
                    marker=dict(size=10, color="white", line=dict(color=COLOR_ESTIMADO, width=2.5), symbol="diamond"),
                    text=["Estimación"] * len(estimados), textposition="top center", textfont=dict(color=COLOR_ESTIMADO, size=11),
                    hovertemplate="%{x|%m/%Y}<br>%{y:,.0f} visitantes<extra>Estimación</extra>")
    fig.add_vrect(x0=estimados.index.min() - pd.Timedelta(days=15), x1=estimados.index.max() + pd.Timedelta(days=15),
                  fillcolor=COLOR_ESTIMADO, opacity=0.07, line_width=0)
    fig.update_yaxes(title_text="Visitantes únicos del mes", tickformat=",.0f", rangemode="tozero")
    fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
    return aplicar_estilo(fig, alto=380)


def fig_consistencia_diaria(t: pd.DataFrame) -> go.Figure:
    """Presencia diaria media por mes: observada (base diaria) e implicita en cada estimacion (violeta)."""
    obs, est = t[t["tipo"] == "Observado"], t[t["tipo"] == "Estimación"]
    fig = go.Figure()
    fig.add_bar(x=[_mes(i) for i in obs.index], y=obs["presencia_media"], name="Observada (base diaria)",
                marker_color=COLOR_HISTORIA, hovertemplate="%{x}<br>%{y:,.0f} presentes por día<extra>Observada</extra>")
    fig.add_bar(x=[_mes(i) for i in est.index], y=est["presencia_media"], name="Implícita en la Estimación",
                marker=dict(color="white", line=dict(color=COLOR_ESTIMADO, width=2), pattern=dict(shape="/", fgcolor=COLOR_ESTIMADO)),
                text=["Estimación"] * len(est), textposition="outside", textfont=dict(color=COLOR_ESTIMADO, size=11),
                hovertemplate="%{x}<br>%{y:,.0f} presentes por día<extra>Estimación</extra>")
    lo, hi = t.attrs.get("rango", (None, None))
    if lo is not None:
        fig.add_hrect(y0=lo, y1=hi, fillcolor=COLOR_HISTORIA, opacity=0.12, line_width=0)
    orden = [_mes(i) for i in t.sort_index().index]
    fig.update_xaxes(categoryorder="array", categoryarray=orden, type="category")
    fig.update_yaxes(title_text="Presencia diaria media", tickformat=",.0f", rangemode="tozero")
    return aplicar_estilo(fig, alto=320)


def fig_validacion(val: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(x=val.index, y=val["observado"], name="Observado", marker_color=COLOR_REAL,
                hovertemplate="%{x|%m/%Y}<br>%{y:,.0f}<extra>Observado</extra>")
    fig.add_bar(x=val.index, y=val["estimado"], name="Estimación (sin ver ese mes)", marker=dict(color=COLOR_ESTIMADO, pattern_shape="/"),
                customdata=val["error_pct"], hovertemplate="%{x|%m/%Y}<br>%{y:,.0f}<br>error %{customdata:+.1%}<extra>Estimación</extra>")
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Visitantes", tickformat=",.0f")
    fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
    return aplicar_estilo(fig, alto=320)


def fig_perfil_estacional(perfil: pd.Series, destacar: list[int]) -> go.Figure:
    colores = [COLOR_ESTIMADO if m in destacar else COLOR_HISTORIA for m in perfil.index]
    fig = go.Figure(go.Bar(x=[MES_ES[m - 1] for m in perfil.index], y=perfil.values, marker_color=colores,
                           hovertemplate="%{x}<br>índice %{y:.2f}<extra></extra>"))
    fig.add_hline(y=1, line=dict(color=COLOR_REAL, dash="dot", width=1))
    fig.update_yaxes(title_text="Índice estacional")
    return aplicar_estilo(fig, alto=320)


# ---------------------------------------------------------------------------------------------
# Modulo 3 (base)


def fig_capacidad(cap: pd.DataFrame, medida: str) -> go.Figure:
    """Barras apiladas por tipo de alojamiento; el corte parcial se dibuja con trama."""
    tipos = list(cap.groupby("tipo_alojamiento")[medida].sum().sort_values(ascending=False).index)
    paleta = SECUENCIAL_AZUL[::-1][: max(len(tipos), 1)] if len(tipos) <= len(SECUENCIAL_AZUL) else None
    fig = go.Figure()
    for i, tipo in enumerate(tipos):
        g = cap[cap["tipo_alojamiento"] == tipo].sort_values("corte")
        fig.add_bar(x=g["corte"], y=g[medida], name=tipo,
                    marker=dict(color=paleta[i * 2 % len(paleta)] if paleta else None,
                                pattern_shape=["/" if p else "" for p in g["corte_parcial"]]),
                    hovertemplate="%{x}<br>" + tipo + ": %{y:,.0f}<extra></extra>")
    fig.update_layout(barmode="stack")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text=medida.replace("_", " ").capitalize(), tickformat=",.0f")
    return aplicar_estilo(fig, alto=340)


def fig_ocupacion(ocup: pd.DataFrame, destacado: str) -> go.Figure:
    fig = go.Figure()
    for dep, g in ocup.groupby("departamento"):
        es = dep == destacado
        fig.add_scatter(x=g["periodo"], y=g["ocupacion"], mode="lines", name=dep, showlegend=es,
                        line=dict(color=COLOR_OCUPACION if es else "#d0d0d0", width=2.5 if es else 1),
                        hovertemplate=dep + "<br>%{x|%m/%Y}: %{y:.0%}<extra></extra>")
    fig.data = tuple(sorted(fig.data, key=lambda t: t.name == destacado))
    fig.update_yaxes(title_text="Tasa de ocupación", tickformat=".0%")
    return aplicar_estilo(fig, alto=340)


def fig_ventana(afluencia: pd.Series, ocupacion: pd.Series) -> go.Figure:
    """Dos paneles con ejes propios: personas y porcentaje no comparten eje."""
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Turistas con pernocta (suma de municipios)", "Ocupación hotelera de Sololá"),
                        horizontal_spacing=0.12)
    x1 = [_mes(t) for t in afluencia.index]
    fig.add_bar(x=x1, y=afluencia.values, marker_color=COLOR_REAL, name="Turistas", row=1, col=1,
                hovertemplate="%{x}: %{y:,.0f}<extra></extra>")
    x2 = [_mes(t) for t in ocupacion.index]
    fig.add_bar(x=x2, y=ocupacion.values, marker_color=COLOR_OCUPACION, name="Ocupación", row=1, col=2,
                hovertemplate="%{x}: %{y:.0%}<extra></extra>")
    fig.update_yaxes(tickformat=",.0f", row=1, col=1)
    fig.update_yaxes(tickformat=".0%", row=1, col=2)
    fig.update_layout(showlegend=False)
    fig.update_annotations(font=dict(size=12))
    return aplicar_estilo(fig, alto=320)


def fig_afluencia_relativa(rel: pd.Series) -> go.Figure:
    t = rel.sort_values()
    fig = go.Figure(go.Bar(y=[MUNICIPIO_CORTO.get(m, m) for m in t.index], x=t.values, orientation="h",
                           marker_color=COLOR_HISTORIA, text=[f"{v:.0f}" for v in t.values], textposition="outside",
                           cliponaxis=False, hovertemplate="%{y}: índice %{x:.0f}<extra></extra>"))
    fig.add_vline(x=100, line=dict(color=COLOR_REAL, dash="dot", width=1))
    fig.update_xaxes(title_text="Afluencia relativa (Panajachel = 100)", range=_rango_con_etiquetas(t))
    return aplicar_estilo(fig, alto=340)


# ---------------------------------------------------------------------------------------------
# Modulo 4 (base)


def fig_cuadrante(perfil: pd.DataFrame, seleccionado: str | None, cortes: dict | None = None) -> go.Figure:
    """Volumen (x, log) x estadia media (y); tamano = especializacion extranjera (IEE, lago = 1).

    Las lineas punteadas son los umbrales de la regla: volumen del hub y estadia de larga estancia."""
    fig = go.Figure()
    for clase, g in perfil.groupby("clase"):
        iee = g["iee"].fillna(1.0)
        fig.add_scatter(
            x=g["visitantes_mes"], y=g["estadia_media"], mode="markers+text", name=clase,
            text=[MUNICIPIO_CORTO.get(m, m) for m in g.index],
            textposition=["bottom center" if m in ("San Antonio Palopó", "San Lucas Tolimán") else "top center" for m in g.index],
            customdata=list(zip(g.index, iee)),
            marker=dict(size=(10 + 22 * iee.clip(upper=2.2)).tolist(), color=COLORES_CLASE.get(clase, COLOR_HISTORIA),
                        opacity=0.85, symbol=SIMBOLOS_CLASE.get(clase, "circle"),
                        line=dict(color=["#161616" if m == seleccionado else "white" for m in g.index],
                                  width=[3 if m == seleccionado else 1 for m in g.index])),
            hovertemplate="<b>%{customdata[0]}</b><br>%{x:,.0f} visitantes/mes<br>estadía %{y:.2f} días"
                          "<br>especialización extranjera %{customdata[1]:.2f} (lago = 1)<extra>" + clase + "</extra>",
        )
    c = cortes or {"volumen_hub": perfil["visitantes_mes"].median(), "estadia_larga": perfil["estadia_media"].median()}
    fig.add_vline(x=c["volumen_hub"], line=dict(color=COLOR_HISTORIA, dash="dot", width=1),
                  annotation_text="umbral hub", annotation_position="top left", annotation_font_size=10)
    fig.add_hline(y=c["estadia_larga"], line=dict(color=COLOR_HISTORIA, dash="dot", width=1),
                  annotation_text="umbral larga estancia (P75)", annotation_position="top left", annotation_font_size=10)
    fig.update_xaxes(title_text="Volumen: visitantes promedio por mes (escala log)", type="log", tickformat=",.0f",
                     tickvals=[500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000])
    fig.update_yaxes(title_text="Estadía media ponderada (días)")
    fig.update_layout(clickmode="event+select", dragmode=False)
    return aplicar_estilo(fig, alto=460)


def fig_mapa_pueblos(m: pd.DataFrame, clases: pd.Series, coordenadas: dict[str, tuple[float, float]]) -> go.Figure:
    """Mapa del lago con el peso de cada pueblo, animado mes a mes (boton Reproducir / deslizador).

    Tamano = visitantes unicos del mes en el municipio (escala fija en todos los cuadros para que el
    crecimiento se vea). No se suman pueblos: cada burbuja es su propio conteo. Ene-feb 2026 no tienen
    cobertura y no aparecen como cuadros (nunca como cero)."""
    t = m.groupby(["periodo", "municipio"], as_index=False)["visitantes"].sum()
    t = t[t["municipio"].isin(coordenadas)]
    t["lat"] = t["municipio"].map(lambda x: coordenadas[x][0])
    t["lon"] = t["municipio"].map(lambda x: coordenadas[x][1])
    t["clase"] = t["municipio"].map(clases).fillna("")
    t["corto"] = t["municipio"].map(lambda x: MUNICIPIO_CORTO.get(x, x))
    maximo = float(t["visitantes"].max()) or 1.0
    periodos = sorted(t["periodo"].unique())

    def trazas(periodo):
        g = t[t["periodo"] == periodo]
        out = []
        for clase in ["Hub comercial", "Larga estancia", "Visita corta"]:
            h = g[g["clase"] == clase]
            out.append(go.Scattermap(
                lat=h["lat"], lon=h["lon"], mode="markers+text", name=clase, text=h["corto"], textposition="top center",
                textfont=dict(size=11, color="#161616"),
                marker=dict(size=(8 + 52 * (h["visitantes"] / maximo) ** 0.5).tolist(), color=COLORES_CLASE.get(clase), opacity=0.8),
                customdata=list(zip(h["municipio"], h["visitantes"])),
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]:,.0f} visitantes en el mes<extra>" + clase + "</extra>",
            ))
        return out

    fig = go.Figure(data=trazas(periodos[0]),
                    frames=[go.Frame(data=trazas(p), name=_mes(pd.Timestamp(p))) for p in periodos])
    pasos = [dict(method="animate", label=_mes(pd.Timestamp(p)),
                  args=[[_mes(pd.Timestamp(p))], dict(mode="immediate", frame=dict(duration=0, redraw=True), transition=dict(duration=0))])
             for p in periodos]
    fig.update_layout(
        map=dict(style="carto-positron", center=dict(lat=14.69, lon=-91.20), zoom=10.3),
        updatemenus=[dict(type="buttons", showactive=False, direction="right", x=0, y=0, xanchor="left", yanchor="top",
                          pad=dict(t=8),
                          buttons=[dict(label="▶ Reproducir", method="animate",
                                        args=[None, dict(frame=dict(duration=900, redraw=True), fromcurrent=True, transition=dict(duration=0))]),
                                   dict(label="❚❚", method="animate",
                                        args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")])])],
        sliders=[dict(active=0, steps=pasos, x=0.035, len=0.93, y=0, yanchor="top", pad=dict(t=52, b=0), font=dict(size=10),
                      currentvalue=dict(prefix="Mes: ", font=dict(size=12)))],
    )
    aplicar_estilo(fig, alto=560)
    fig.update_layout(margin=dict(l=0, r=0, t=8, b=125), legend=dict(orientation="h", y=1.02, x=0, yanchor="bottom"))
    return fig


def fig_mensual_origen(m: pd.DataFrame) -> go.Figure:
    t = m.pivot_table(index="periodo", columns="origen", values="visitantes", aggfunc="sum")
    t = t.reindex(pd.date_range(t.index.min(), t.index.max(), freq="MS"))
    fig = go.Figure()
    for origen in ["Nacional", "Extranjero"]:
        if origen in t:
            fig.add_scatter(x=t.index, y=t[origen], name=origen, mode="lines+markers", connectgaps=False,
                            line=dict(color=COLORES_ORIGEN[origen], width=2),
                            hovertemplate="%{x|%m/%Y}<br>%{y:,.0f}<extra>" + origen + "</extra>")
    fig.update_yaxes(title_text="Visitantes del mes", tickformat=",.0f", rangemode="tozero")
    fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
    aplicar_estilo(fig, alto=300)
    return fechas_en_espanol(fig, paso_minimo=2)


# ---------------------------------------------------------------------------------------------
# Modulo 3 (completo)


def fig_heatmap_ocupacion(matriz: pd.DataFrame) -> go.Figure:
    """Mapa de calor anio x mes de la ocupacion (secuencial azul: mas oscuro = mas lleno)."""
    from src.estilo import ESCALA_SECUENCIAL

    fig = go.Figure(go.Heatmap(
        z=matriz.values, x=MES_ES, y=[str(a) for a in matriz.index], colorscale=ESCALA_SECUENCIAL, zmin=0, zmax=1,
        text=[[f"{v * 100:.0f}" if pd.notna(v) else "" for v in fila] for fila in matriz.values], texttemplate="%{text}",
        textfont=dict(size=10), hovertemplate="%{x} %{y}: %{z:.0%}<extra></extra>",
        colorbar=dict(tickformat=".0%", thickness=8, len=0.9, title=dict(text="%", side="top")),
        xgap=2, ygap=2,
    ))
    fig.update_yaxes(autorange="reversed", showgrid=False, type="category")
    fig.update_xaxes(type="category")
    return aplicar_estilo(fig, alto=260)


def fig_cruce_ventana(cruce: pd.DataFrame, etiqueta_tel: str, etiqueta_hotel: str) -> go.Figure:
    """Dos paneles para UN origen: noches (telefonia vs hoteleria formal) y captacion formal (%).

    Noches y porcentajes nunca comparten eje."""
    x = [_mes(t) for t in cruce["periodo"]]
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.14, column_widths=[0.6, 0.4],
                        subplot_titles=("Noches en el mes", "Captación formal"))
    fig.add_bar(x=x, y=cruce["noches_telefonia"], name=etiqueta_tel, marker_color="#d0d0d0", row=1, col=1,
                hovertemplate="%{x}<br>%{y:,.0f} noches<extra>Telefonía</extra>")
    fig.add_bar(x=x, y=cruce["noches_hotel"], name=etiqueta_hotel, marker_color=COLOR_REAL, row=1, col=1,
                hovertemplate="%{x}<br>%{y:,.0f} noches<extra>Hotelería formal</extra>")
    fig.add_scatter(x=x, y=cruce["captacion_formal"], name="Noches en hotel formal / noches por telefonía",
                    mode="lines+markers+text", text=[f"{v:.0%}" for v in cruce["captacion_formal"]], textposition="top center",
                    line=dict(color=COLOR_OCUPACION, width=2.5), row=1, col=2,
                    hovertemplate="%{x}<br>%{y:.1%}<extra>Captación</extra>")
    fig.update_layout(barmode="group")
    fig.update_yaxes(tickformat=",.0f", row=1, col=1)
    tope = float(cruce["captacion_formal"].max()) if cruce["captacion_formal"].notna().any() else 1.0
    fig.update_yaxes(tickformat=".0%", range=[0, max(tope * 1.3, 0.1)], row=1, col=2)
    fig.update_annotations(font=dict(size=12))
    aplicar_estilo(fig, alto=380)
    fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.18, x=0, xanchor="left"), margin=dict(b=8, t=28))
    return fig


def fig_barras_pct(serie: pd.Series, titulo_x: str, destacar: list[str] | None = None, alto: int = 300) -> go.Figure:
    """Barras horizontales de porcentajes muestrales (encuesta sin factor de expansion)."""
    serie = serie.sort_values()
    colores = [COLOR_DESTACADO if (destacar and k in destacar) else COLOR_HISTORIA for k in serie.index]
    fig = go.Figure(go.Bar(
        y=serie.index, x=serie.values, orientation="h", marker_color=colores,
        text=[f"{v:.0%}" for v in serie.values], textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: %{x:.1%} de los encuestados<extra></extra>",
    ))
    fig.update_xaxes(tickformat=".0%", range=[0, min(1, float(serie.max()) * 1.25)], title_text=titulo_x)
    return aplicar_estilo(fig, alto=alto)


def fig_capacidad_anual(anual: pd.DataFrame, medida: str, anio_sel: int | None) -> go.Figure:
    """Barras de un corte por anio (completos), para elegir el anio con un clic."""
    colores = [COLOR_DESTACADO if a == anio_sel else COLOR_HISTORIA for a in anual.index]
    fig = go.Figure(go.Bar(
        x=[str(a) for a in anual.index], y=anual[medida], marker_color=colores, customdata=list(anual.index),
        text=[f"{v:,.0f}" for v in anual[medida]], textposition="outside", cliponaxis=False,
        hovertemplate="%{x}: %{y:,.0f}<extra></extra>",
    ))
    fig.update_yaxes(title_text=medida.replace("_", " ").capitalize(), tickformat=",.0f", rangemode="tozero")
    fig.update_layout(clickmode="event+select", dragmode=False)
    fig.update_xaxes(type="category")
    return aplicar_estilo(fig, alto=300)


# ---------------------------------------------------------------------------------------------
# Modulo 4 (completo)

COLUMNAS_MATRIZ = {
    "visitantes_mes": ("Visitantes<br>por mes", ",.0f"),
    "estadia_media": ("Estadía<br>(días)", ".2f"),
    "iee": ("Especialización<br>extranjera", ".2f"),
    "pct_excursionistas": ("Excursionistas", ".0%"),
    "presion_finde": ("Presión de<br>fin de semana", ".2f"),
    "lift_max": ("Lift máximo<br>festividad", "+.0%"),
}


def fig_matriz_perfiles(p: pd.DataFrame, seleccionado: str | None) -> go.Figure:
    """Municipios x indicadores. Color = posicion relativa en cada columna (0 = menor del lago, 1 = mayor);
    el texto muestra el valor real. Permite comparar variables de unidades distintas sin mezclarlas."""
    cols = list(COLUMNAS_MATRIZ)
    orden = p.sort_values("visitantes_mes", ascending=False)
    datos = orden[cols]
    rel = (datos - datos.min()) / (datos.max() - datos.min()).replace(0, 1)
    texto = [[format(v, COLUMNAS_MATRIZ[c][1]) if pd.notna(v) else "" for c, v in zip(cols, fila)] for fila in datos.values]
    y = [("▶ " if m == seleccionado else "") + MUNICIPIO_CORTO.get(m, m) for m in orden.index]
    fig = go.Figure(go.Heatmap(
        z=rel.values, x=[COLUMNAS_MATRIZ[c][0] for c in cols], y=y, colorscale=[[0, "#f2f2f2"], [1, "#256abf"]],
        text=texto, texttemplate="%{text}", showscale=False, xgap=2, ygap=2,
        hovertemplate="%{y} · %{x}: %{text}<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(side="top", showgrid=False, tickangle=0, tickfont=dict(size=11))
    return aplicar_estilo(fig, alto=420)


def fig_huella_semanal(huella: pd.DataFrame, clases: pd.Series) -> go.Figure:
    from src.estilo import ESCALA_DIVERGENTE

    orden = huella.loc[[m for c in ["Hub comercial", "Larga estancia", "Visita corta"] for m in huella.index if clases.get(m) == c]]
    fig = go.Figure(go.Heatmap(
        z=orden.values, x=[d[:3] for d in orden.columns], y=[MUNICIPIO_CORTO.get(m, m) for m in orden.index],
        customdata=[[clases.get(m, "")] * len(orden.columns) for m in orden.index],
        colorscale=ESCALA_DIVERGENTE, zmid=100, text=[[f"{v:.0f}" for v in fila] for fila in orden.values], texttemplate="%{text}",
        hovertemplate="%{y} (%{customdata}) · %{x}: índice %{z:.0f}<extra></extra>", showscale=False,
        xgap=2, ygap=2,
    ))
    # Separadores entre clases
    limites = [c for c in ["Hub comercial", "Larga estancia", "Visita corta"] if (clases.reindex(orden.index) == c).any()]
    acumulado = 0
    for c in limites[:-1]:
        acumulado += int((clases.reindex(orden.index) == c).sum())
        fig.add_hline(y=acumulado - 0.5, line=dict(color=COLOR_REAL, width=2))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(tickangle=0, showgrid=False)
    return aplicar_estilo(fig, alto=420)


def fig_mercados_clase(t: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    paleta = ["#0d366b", "#184f95", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4", "#cde2fb", "#e5eefb", "#d0d0d0"]
    for i, pais in enumerate(t.columns):
        fig.add_bar(y=t.index, x=t[pais], name=pais, orientation="h", marker_color=paleta[i % len(paleta)],
                    hovertemplate="%{y}<br>" + pais + ": %{x:.0%}<extra></extra>")
    fig.update_layout(barmode="stack", legend=dict(font=dict(size=10)))
    fig.update_xaxes(tickformat=".0%", range=[0, 1], title_text="% de los visitantes extranjeros de la clase")
    fig.update_yaxes(autorange="reversed")
    return aplicar_estilo(fig, alto=300)


def fig_estacionalidad_clase(t: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for clase in t.columns:
        fig.add_scatter(x=t.index, y=t[clase], name=clase, mode="lines+markers", connectgaps=False,
                        line=dict(color=COLORES_CLASE.get(clase, COLOR_HISTORIA), width=2, dash=TRAZOS_CLASE.get(clase, "solid")),
                        marker=dict(symbol=SIMBOLOS_CLASE.get(clase, "circle"), size=7),
                        hovertemplate="%{x|%m/%Y}<br>índice %{y:.0f}<extra>" + clase + "</extra>")
    fig.add_hline(y=100, line=dict(color=COLOR_HISTORIA, dash="dot", width=1))
    fig.update_yaxes(title_text="Índice (promedio = 100)")
    fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
    return aplicar_estilo(fig, alto=300)


def fig_cobertura(t: pd.DataFrame, marcar: list[str] | None = None) -> go.Figure:
    """Indicador de cobertura: que fuentes respaldan cada mes (gris claro = sin dato, nunca cero)."""
    x = [_mes(c) for c in t.columns]
    texto = [["con dato" if v == 1 else "parcial (ventanas de evento)" if v == 0.5 else "sin dato" for v in fila]
             for fila in t.values]
    fig = go.Figure(go.Heatmap(
        z=t.fillna(0).values, x=x, y=list(t.index), zmin=0, zmax=1, showscale=False, xgap=1, ygap=3,
        colorscale=[[0, "#f2f2f2"], [0.5, "#9ec5f4"], [1, "#184f95"]], customdata=texto,
        hovertemplate="%{y} · %{x}: %{customdata}<extra></extra>",
    ))
    for per in marcar or []:
        ts = pd.Timestamp(per + "-01")
        if ts in t.columns:
            i = list(t.columns).index(ts)
            fig.add_vrect(x0=i - 0.5, x1=i + 0.5, line=dict(color=COLOR_ESTIMADO, width=2), fillcolor="rgba(0,0,0,0)")
    fig.update_yaxes(autorange="reversed", showgrid=False)
    trimestres = [x[i] for i, c in enumerate(t.columns) if c.month in (1, 4, 7, 10)]
    texto = [f"{_mes(c).split()[0]}<br>{c.year}" if c.month == 1 else _mes(c).split()[0]
             for c in t.columns if c.month in (1, 4, 7, 10)]
    fig.update_xaxes(showgrid=False, tickangle=0, tickfont=dict(size=10), type="category",
                     tickmode="array", tickvals=trimestres, ticktext=texto)
    return aplicar_estilo(fig, alto=300)


def fig_uso_capacidad(t: pd.DataFrame) -> go.Figure:
    """Barras por anio: indice publicado (verde) y ocupacion sobre el inventario registrado (azul claro)."""
    x = [str(a) for a in t.index]
    fig = go.Figure()
    fig.add_bar(x=x, y=t["ocupacion_publicada"], name="Índice publicado (establecimientos que reportan)",
                marker_color=COLOR_OCUPACION, text=[f"{v:.0%}" for v in t["ocupacion_publicada"]], textposition="outside",
                cliponaxis=False, hovertemplate="%{x}: %{y:.0%}<extra>Índice publicado</extra>")
    fig.add_bar(x=x, y=t["ocupacion_inventario"], name="Ocupación sobre el inventario registrado",
                marker=dict(color="#9ec5f4", line=dict(color="#256abf", width=1)),
                text=[f"{v:.0%}" for v in t["ocupacion_inventario"]], textposition="outside", cliponaxis=False,
                customdata=list(zip(t["cobertura"], t["inventario"])),
                hovertemplate="%{x}: %{y:.0%}<br>cobertura del índice %{customdata[0]:.0%} de %{customdata[1]:,.0f} "
                              "habitaciones<extra>Sobre inventario</extra>")
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Habitaciones ocupadas", tickformat=".0%", range=[0, 1])
    return aplicar_estilo(fig, alto=320)
