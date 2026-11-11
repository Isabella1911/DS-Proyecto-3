"""Figuras del observatorio (Plotly). Cada funcion recibe tablas ya calculadas por src.indicadores."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.estilo import (
    COLOR_DESTACADO, COLOR_ESTIMADO, COLOR_EVENTO, COLOR_HISTORIA, COLOR_OCUPACION, COLOR_REAL, COLORES_CLASE,
    COLORES_ORIGEN, COLORES_SEGMENTO, CUADRICULA, SECUENCIAL_AZUL, aplicar_estilo,
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
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    x = [_mes(t) for t in seg.index]
    for s in [SEG_TURISTA, SEG_EXCURSIONISTA]:
        fig.add_bar(x=x, y=seg[s], name=s, marker_color=COLORES_SEGMENTO[s],
                    hovertemplate="%{x}<br>" + s + ": %{y:,.0f}<extra></extra>")
    fig.add_scatter(x=x, y=seg["pct_turistas"], name="% turistas", mode="lines+markers", line=dict(color=COLOR_REAL, width=1.5),
                    connectgaps=False, secondary_y=True, hovertemplate="%{x}<br>%{y:.0%} turistas<extra></extra>")
    sin = [_mes(t) for t in seg.index[seg[SEG_TURISTA].isna()]]
    for m in sin:
        fig.add_annotation(x=m, y=0, yref="paper", text="Sin dato", showarrow=False, textangle=-90, yanchor="bottom",
                           font=dict(size=10, color=COLOR_HISTORIA))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="Visitantes", tickformat=",.0f", secondary_y=False)
    fig.update_yaxes(title_text="% turistas", tickformat=".0%", range=[0, 1], showgrid=False, secondary_y=True)
    return aplicar_estilo(fig, alto=340)


def fig_top_paises(top: pd.DataFrame) -> go.Figure:
    t = top.sort_values("visitantes")
    fig = go.Figure(go.Bar(
        y=t.index, x=t["visitantes"], orientation="h", marker_color=COLORES_ORIGEN["Extranjero"],
        text=[f"{p:.0%}" for p in t["pct"]], textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} visitantes<br>%{text} de los extranjeros<extra></extra>",
    ))
    fig.update_xaxes(title_text="Visitantes en el periodo (suma de meses)", tickformat=",.0f")
    return aplicar_estilo(fig, alto=340)


def fig_estadia_paises(top: pd.DataFrame, estadia_nacional: float, estadia_total: float) -> go.Figure:
    """Puntos: estadia media ponderada por nacionalidad, con referencias nacional y global."""
    t = top.sort_values("estadia_media")
    fig = go.Figure(go.Scatter(
        y=t.index, x=t["estadia_media"], mode="markers", marker=dict(size=11, color=COLORES_ORIGEN["Extranjero"]),
        hovertemplate="<b>%{y}</b><br>%{x:.2f} días por turista<extra></extra>", name="Extranjeros",
    ))
    for valor, texto, color in [(estadia_nacional, "Nacionales", COLORES_ORIGEN["Nacional"]), (estadia_total, "Promedio ponderado", COLOR_REAL)]:
        if pd.notna(valor):
            fig.add_vline(x=valor, line=dict(color=color, dash="dot", width=1.5),
                          annotation=dict(text=f"{texto}: {valor:.2f}", font=dict(size=11, color=color), yanchor="bottom"),
                          annotation_position="top")
    fig.update_xaxes(title_text="Estadía media ponderada (días, solo turistas > 1 día)")
    fig.update_layout(showlegend=False)
    return aplicar_estilo(fig, alto=340)


# ---------------------------------------------------------------------------------------------
# Modulo 2


def fig_serie_diaria(diaria: pd.DataFrame, evento_sel: str | None) -> go.Figure:
    fig = go.Figure()
    fig.add_scatter(x=diaria.index, y=diaria["visitantes"], mode="lines", name="Presencia diaria",
                    line=dict(color=COLOR_HISTORIA, width=1), connectgaps=False,
                    hovertemplate="%{x|%a %d/%m/%Y}<br>%{y:,.0f} visitantes<extra></extra>")
    ev = diaria[(diaria["evento"].notna()) & (diaria["evento"] != EVENTO_REGULAR)]
    fig.add_scatter(x=ev.index, y=ev["visitantes"], mode="markers", name="Día con festividad",
                    marker=dict(color=COLOR_EVENTO, size=6), customdata=ev["evento"],
                    hovertemplate="%{x|%a %d/%m/%Y}<br><b>%{customdata}</b><br>%{y:,.0f} visitantes<extra></extra>")
    if evento_sel:
        dias = diaria.index[diaria["evento"] == evento_sel]
        for d in dias:
            fig.add_vrect(x0=d - pd.Timedelta(hours=12), x1=d + pd.Timedelta(hours=12), fillcolor=COLOR_DESTACADO,
                          opacity=0.18, line_width=0)
        sel = diaria.loc[dias]
        fig.add_scatter(x=sel.index, y=sel["visitantes"], mode="markers", name=evento_sel,
                        marker=dict(color=COLOR_DESTACADO, size=9, line=dict(color="white", width=1)),
                        hovertemplate="%{x|%a %d/%m/%Y}<br>%{y:,.0f} visitantes<extra></extra>")
    huecos = diaria["visitantes"].isna()
    if huecos.any():
        ini, fin = diaria.index[huecos].min(), diaria.index[huecos].max()
        fig.add_vrect(x0=ini, x1=fin, fillcolor=CUADRICULA, opacity=0.5, line_width=0,
                      annotation=dict(text="Sin dato (sin cobertura de telefonía)", font=dict(size=11, color=COLOR_HISTORIA)),
                      annotation_position="top left")
    fig.update_yaxes(title_text="Visitantes presentes en el día", tickformat=",.0f")
    fig.update_xaxes(rangeslider=dict(visible=True, thickness=0.06),
                     range=[diaria.index.min() - pd.Timedelta(days=3), diaria.index.max() + pd.Timedelta(days=3)])
    return aplicar_estilo(fig, alto=420)


def fig_lift(lift: pd.DataFrame, columna: str, seleccionado: str | None) -> go.Figure:
    t = lift.sort_values(columna)
    colores = [COLOR_DESTACADO if e == seleccionado else COLOR_EVENTO for e in t.index]
    fig = go.Figure(go.Bar(
        y=t.index, x=t[columna], orientation="h", marker_color=colores, customdata=t["dias"],
        text=[f"{v:+.0%}" for v in t[columna]], textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Lift %{x:+.1%}<br>%{customdata} días observados<extra></extra>",
    ))
    fig.add_vline(x=0, line=dict(color=COLOR_REAL, width=1))
    fig.update_xaxes(title_text="Impacto frente al día regular promedio", tickformat="+.0%")
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
    fig.update_yaxes(title_text="Índice (promedio semanal = 100)")
    return aplicar_estilo(fig, alto=340)


def fig_mensual_estimada(obs: pd.Series, estimados: pd.Series) -> go.Figure:
    """Serie mensual observada (tinta) y Estimación (violeta discontinua, rotulada)."""
    fig = go.Figure()
    fig.add_scatter(x=obs.index, y=obs.values, mode="lines+markers", name="Observado", connectgaps=False,
                    line=dict(color=COLOR_REAL, width=2), marker=dict(size=7),
                    hovertemplate="%{x|%b %Y}<br>%{y:,.0f} visitantes<extra>Observado</extra>")
    # Puente punteado entre el ultimo observado, la estimacion y el siguiente observado
    puente = pd.concat([obs.dropna()[obs.dropna().index < estimados.index.min()].tail(1), estimados,
                        obs.dropna()[obs.dropna().index > estimados.index.max()].head(1)])
    fig.add_scatter(x=puente.index, y=puente.values, mode="lines", line=dict(color=COLOR_ESTIMADO, dash="dash", width=2),
                    showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=estimados.index, y=estimados.values, mode="markers+text", name="Estimación",
                    marker=dict(size=10, color="white", line=dict(color=COLOR_ESTIMADO, width=2.5), symbol="diamond"),
                    text=["Estimación"] * len(estimados), textposition="top center", textfont=dict(color=COLOR_ESTIMADO, size=11),
                    hovertemplate="%{x|%b %Y}<br>%{y:,.0f} visitantes<extra>Estimación</extra>")
    fig.add_vrect(x0=estimados.index.min() - pd.Timedelta(days=15), x1=estimados.index.max() + pd.Timedelta(days=15),
                  fillcolor=COLOR_ESTIMADO, opacity=0.07, line_width=0)
    fig.update_yaxes(title_text="Visitantes únicos del mes", tickformat=",.0f", rangemode="tozero")
    fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
    return aplicar_estilo(fig, alto=380)


def fig_validacion(val: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(x=val.index, y=val["observado"], name="Observado", marker_color=COLOR_REAL,
                hovertemplate="%{x|%b %Y}<br>%{y:,.0f}<extra>Observado</extra>")
    fig.add_bar(x=val.index, y=val["estimado"], name="Estimación (sin ver ese mes)", marker=dict(color=COLOR_ESTIMADO, pattern_shape="/"),
                customdata=val["error_pct"], hovertemplate="%{x|%b %Y}<br>%{y:,.0f}<br>error %{customdata:+.1%}<extra>Estimación</extra>")
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Visitantes", tickformat=",.0f")
    fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
    return aplicar_estilo(fig, alto=320)


def fig_perfil_estacional(perfil: pd.Series, destacar: list[int]) -> go.Figure:
    colores = [COLOR_ESTIMADO if m in destacar else COLOR_HISTORIA for m in perfil.index]
    fig = go.Figure(go.Bar(x=[MES_ES[m - 1] for m in perfil.index], y=perfil.values, marker_color=colores,
                           hovertemplate="%{x}<br>índice %{y:.2f}<extra></extra>"))
    fig.add_hline(y=1, line=dict(color=COLOR_REAL, dash="dot", width=1))
    fig.update_yaxes(title_text="Llegadas / promedio del año")
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
                        hovertemplate=dep + "<br>%{x|%b %Y}: %{y:.0%}<extra></extra>")
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
    fig.update_xaxes(title_text="Afluencia relativa (Panajachel = 100)")
    return aplicar_estilo(fig, alto=340)


# ---------------------------------------------------------------------------------------------
# Modulo 4 (base)


def fig_cuadrante(perfil: pd.DataFrame, seleccionado: str | None) -> go.Figure:
    fig = go.Figure()
    for clase, g in perfil.groupby("clase"):
        fig.add_scatter(
            x=g["visitantes_mes"], y=g["estadia_media"], mode="markers+text", name=clase,
            text=[MUNICIPIO_CORTO.get(m, m) for m in g.index], textposition="top center",
            customdata=list(zip(g.index, g["pct_extranjeros"])),
            marker=dict(size=12 + 40 * g["pct_extranjeros"], color=COLORES_CLASE.get(clase, COLOR_HISTORIA), opacity=0.85,
                        line=dict(color=["#161616" if m == seleccionado else "white" for m in g.index],
                                  width=[3 if m == seleccionado else 1 for m in g.index])),
            hovertemplate="<b>%{customdata[0]}</b><br>%{x:,.0f} visitantes/mes<br>estadía %{y:.2f} días"
                          "<br>%{customdata[1]:.0%} extranjeros<extra>" + clase + "</extra>",
        )
    fig.add_vline(x=perfil["visitantes_mes"].median(), line=dict(color=COLOR_HISTORIA, dash="dot", width=1))
    fig.add_hline(y=perfil["estadia_media"].median(), line=dict(color=COLOR_HISTORIA, dash="dot", width=1))
    fig.update_xaxes(title_text="Volumen: visitantes promedio por mes (escala log)", type="log", tickformat=",.0f",
                     tickvals=[500, 1000, 2000, 5000, 10000, 20000, 50000])
    fig.update_yaxes(title_text="Estadía media ponderada (días)")
    fig.update_layout(clickmode="event+select", dragmode=False)
    return aplicar_estilo(fig, alto=460)


# Etiquetas de los pueblos del oeste a un lado para que no se encimen
POSICION_ETIQUETA = {
    "San Juan La Laguna": "middle left", "San Pablo La Laguna": "middle left", "San Pedro La Laguna": "middle right",
    "San Marcos La Laguna": "top right", "San Antonio Palopó": "middle right", "Santa Catarina Palopó": "middle right",
    "San Lucas Tolimán": "bottom center", "Santiago Atitlán": "bottom center",
}


def fig_mapa_lago(perfil: pd.DataFrame, coordenadas: dict[str, tuple[float, float]], contorno: list[tuple[float, float]],
                  volcanes: dict[str, tuple[float, float]], seleccionado: str | None) -> go.Figure:
    """Portada: los 10 municipios sobre un mapa esquematico del lago (sin teselas en linea).
    Tamano = visitantes/mes (area), color = clase. Cada pueblo es clicable y lleva su nombre en customdata."""
    p = perfil[perfil.index.isin(coordenadas)].copy()
    p["lat"] = [coordenadas[m][0] for m in p.index]
    p["lon"] = [coordenadas[m][1] for m in p.index]
    escala = 48 / p["visitantes_mes"].max() ** 0.5
    fig = go.Figure()
    lat, lon = zip(*(contorno + contorno[:1]))
    fig.add_scatter(x=lon, y=lat, mode="lines", fill="toself", fillcolor="#cfe9f6", line=dict(color="#4fb0dc", width=2),
                    hoverinfo="skip", showlegend=False)
    vlat, vlon = zip(*volcanes.values())
    fig.add_scatter(x=vlon, y=vlat, mode="markers+text", text=list(volcanes), textposition="bottom center",
                    textfont=dict(size=11, color="#4b6475"), hoverinfo="skip", showlegend=False,
                    marker=dict(symbol="triangle-up", size=22, color="#a9c3d1", line=dict(color="#7b93a3", width=1)))
    for clase in [c for c in COLORES_CLASE if c in set(p["clase"])]:
        g = p[p["clase"] == clase]
        fig.add_scatter(
            x=g["lon"], y=g["lat"], mode="markers+text", name=clase,
            text=[MUNICIPIO_CORTO.get(m, m) for m in g.index],
            textposition=[POSICION_ETIQUETA.get(m, "top center") for m in g.index],
            textfont=dict(size=12, color="#00314d"),
            customdata=list(zip(g.index, g["visitantes_mes"], g["estadia_media"], g["pct_extranjeros"])),
            marker=dict(size=(g["visitantes_mes"] ** 0.5 * escala).clip(lower=12), color=COLORES_CLASE[clase],
                        opacity=[1 if seleccionado in (None, m) else 0.4 for m in g.index],
                        line=dict(color=["#00314d" if m == seleccionado else "white" for m in g.index],
                                  width=[3 if m == seleccionado else 1.5 for m in g.index])),
            selected=dict(marker=dict(opacity=1)), unselected=dict(marker=dict(opacity=0.4)),
            hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]:,.0f} visitantes/mes"
                          "<br>estadía %{customdata[2]:.2f} días<br>%{customdata[3]:.0%} extranjeros<extra>" + clase + "</extra>",
        )
    # Sin fixedrange: con ambos ejes fijos Plotly no crea el area de clic y la seleccion no funciona.
    # El zoom se evita con dragmode=False y scrollZoom=False en la configuracion del grafico.
    fig.update_xaxes(visible=False, range=[-91.33, -91.07])
    fig.update_yaxes(visible=False, range=[14.565, 14.765], scaleanchor="x", scaleratio=1.034)
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0), height=500, clickmode="event+select", dragmode=False,
        plot_bgcolor="#f3f8f4", paper_bgcolor="#f3f8f4",
        legend=dict(orientation="h", x=0.01, y=0.01, xanchor="left", yanchor="bottom", bgcolor="rgba(255,255,255,.9)",
                    font=dict(size=12, color="#00314d"), title=dict(text="Clase del municipio  ")),
        font=dict(family='PlexSans, "IBM Plex Sans", Arial, sans-serif'),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    return fig


def fig_mensual_origen(m: pd.DataFrame) -> go.Figure:
    t = m.pivot_table(index="periodo", columns="origen", values="visitantes", aggfunc="sum")
    t = t.reindex(pd.date_range(t.index.min(), t.index.max(), freq="MS"))
    fig = go.Figure()
    for origen in ["Nacional", "Extranjero"]:
        if origen in t:
            fig.add_scatter(x=t.index, y=t[origen], name=origen, mode="lines+markers", connectgaps=False,
                            line=dict(color=COLORES_ORIGEN[origen], width=2),
                            hovertemplate="%{x|%b %Y}<br>%{y:,.0f}<extra>" + origen + "</extra>")
    fig.update_yaxes(title_text="Visitantes del mes", tickformat=",.0f", rangemode="tozero")
    fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
    return aplicar_estilo(fig, alto=300)


# ---------------------------------------------------------------------------------------------
# Modulo 3 (completo)


def fig_heatmap_ocupacion(matriz: pd.DataFrame) -> go.Figure:
    """Mapa de calor anio x mes de la ocupacion (secuencial azul: mas oscuro = mas lleno)."""
    from src.estilo import ESCALA_SECUENCIAL

    fig = go.Figure(go.Heatmap(
        z=matriz.values, x=MES_ES, y=[str(a) for a in matriz.index], colorscale=ESCALA_SECUENCIAL,
        text=[[f"{v:.0%}" if pd.notna(v) else "" for v in fila] for fila in matriz.values], texttemplate="%{text}",
        hovertemplate="%{x} %{y}: %{z:.0%}<extra></extra>", colorbar=dict(tickformat=".0%", thickness=10, len=0.9),
        xgap=2, ygap=2,
    ))
    fig.update_yaxes(autorange="reversed", showgrid=False, type="category")
    fig.update_xaxes(type="category")
    return aplicar_estilo(fig, alto=260)


def fig_cruce_ventana(cruce: pd.DataFrame) -> go.Figure:
    """Dos paneles: noches (demandadas vs capacidad formal) y tasas (implicita vs oficial)."""
    x = [_mes(t) for t in cruce.index]
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.14,
                        subplot_titles=("Noches", "Tasas"))
    fig.add_bar(x=x, y=cruce["plazas_noche"], name="Plazas-noche disponibles", marker_color="#d0d0d0", row=1, col=1,
                hovertemplate="%{x}<br>%{y:,.0f} plazas-noche<extra></extra>")
    fig.add_bar(x=x, y=cruce["noches_demandadas"], name="Noches demandadas (turistas)", marker_color=COLOR_REAL, row=1, col=1,
                hovertemplate="%{x}<br>%{y:,.0f} noches<extra></extra>")
    fig.add_scatter(x=x, y=cruce["ocupacion_oficial"], name="Ocupación oficial", mode="lines+markers",
                    line=dict(color=COLOR_OCUPACION, width=2.5), row=1, col=2, hovertemplate="%{x}<br>%{y:.0%}<extra>Oficial</extra>")
    fig.add_scatter(x=x, y=cruce["tasa_implicita"], name="Tasa implícita (noches / plazas-noche)", mode="lines+markers",
                    line=dict(color=COLOR_REAL, width=2, dash="dot"), row=1, col=2,
                    hovertemplate="%{x}<br>%{y:.0%}<extra>Implícita</extra>")
    fig.update_layout(barmode="overlay")
    fig.update_yaxes(tickformat=",.0f", row=1, col=1)
    fig.update_yaxes(tickformat=".0%", rangemode="tozero", row=1, col=2)
    fig.update_annotations(font=dict(size=12))
    aplicar_estilo(fig, alto=380)
    fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.18, x=0, xanchor="left"), margin=dict(b=8, t=28))
    return fig


def fig_capacidad_anual(anual: pd.DataFrame, medida: str, anio_sel: int | None) -> go.Figure:
    """Barras de un corte por anio (completos), para elegir el anio con un clic."""
    colores = [COLOR_DESTACADO if a == anio_sel else SECUENCIAL_AZUL[3] for a in anual.index]
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
    "visitantes_mes": ("Visitantes/mes", ",.0f"),
    "estadia_media": ("Estadía media", ".2f"),
    "pct_extranjeros": ("% extranjeros", ".0%"),
    "pct_excursionistas": ("% excursionistas", ".0%"),
    "presion_finde": ("Presión finde", ".2f"),
    "lift_max": ("Lift máx. festividad", "+.0%"),
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
    fig.update_xaxes(side="top", showgrid=False)
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
                        line=dict(color=COLORES_CLASE.get(clase, COLOR_HISTORIA), width=2),
                        hovertemplate="%{x|%b %Y}<br>índice %{y:.0f}<extra>" + clase + "</extra>")
    fig.add_hline(y=100, line=dict(color=COLOR_HISTORIA, dash="dot", width=1))
    fig.update_yaxes(title_text="Índice (promedio = 100)")
    fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
    return aplicar_estilo(fig, alto=300)
