# Avance del proyecto · Grupo 3 · Lago de Atitlán

## 1. Qué se reutilizó de los Laboratorios 10 y 11

| Del laboratorio | En el proyecto |
|---|---|
| Sistema visual tipo IBM Carbon, tipografía Plex, mosaicos con ayuda (`src/ui.py`) | Igual, con etiquetas *Observado / Interpretación / Estimación* |
| Paleta validada para daltonismo (`src/estilo.py`) | Reasignada: origen, segmento, estimación, festividad, clase de municipio |
| Gráficas enlazadas con `on_select` de Streamlit | Los 4 módulos tienen al menos una gráfica que filtra a otras |
| Estimación con factor de reparto sobre la base de migración (Lab 11) | Método A del módulo 2, ahora calibrado con el factor **observado** del destino |
| Docker con datos montados, nunca copiados a la imagen | Igual, más datos sintéticos generados al construir |

Los datos reales **no** se copiaron (el repositorio del Lab 10 es público y contiene la base de migración; se
recomienda hacerlo privado o eliminar el archivo de su historial).

## 2. Pipeline de datos

```
data/raw (reales, no versionados) ─┐
                                   ├─> src/normalizar.py ─> src/etl.py ─> data/procesados/*.parquet ─> tablero
data/sinteticos (si falta el real) ┘                         └─> calidad.json (controles y origen de cada fuente)
```

Normalización: mayúsculas, tildes y espacios (`PANAJACHEL` = `Panajachel `), abreviaturas (`Sta.`, `Sn.`),
nombres cortos de municipios (`SAN MARCOS` → San Marcos La Laguna), países en mayúsculas, departamentos sin
tilde (`SOLOLA`), coma decimal (`2,55`), fechas de Excel o texto, valores de segmento y evento
(`Regular`). Lo no reconocido se reporta en la página **Calidad de los datos**. Detalle por tabla en
[normalizacion.md](normalizacion.md).

## 3. Módulo 1 · Demanda y mercados emisores

- **KPIs**: visitantes promedio por mes, días-persona promedio por mes, estadía media ponderada, % turistas.
- **Estadía media** = Σ días-persona / Σ visitantes, solo segmento "mayor a 1".
- **Turista vs. excursionista** por mes, con % de pernocta.
- **Top 10 extranjeros**; los nacionales (Guatemala, con factor de expansión) se reportan aparte.
- **Adicional**: estadía media por nacionalidad frente a nacionales y al promedio.
- **Enlace**: clic en la gráfica de municipios → se recalculan KPIs, segmentación, top 10 y estadía.

## 4. Módulo 2 · Dinámica temporal y pronóstico

- **Serie diaria** con festividades resaltadas; selector de festividad (o clic en la gráfica de Lift).
- **Lift** = promedio del día de evento / promedio del día regular − 1, más una versión ajustada por día de la
  semana.
- **Patrón semanal** (índice, promedio = 100) y presión de fin de semana (sáb-dom / lun-vie).
- **Estimación ene–feb 2026** (rotulada *Estimación*, violeta y discontinua):
  - A: F = Σ destino / Σ llegadas internacionales (meses observados); estimación = F × llegadas del mes.
  - B: perfil estacional de migración 2023–2025 × nivel del destino.
- **Validación**: dejando un mes fuera; MAPE, MAE y RMSE. Se elige por defecto el método con menor MAPE.
- **Adicional**: perfil estacional de las llegadas internacionales.

## 5. Módulo 3 · Oferta hotelera y desagregación territorial

- **Capacidad instalada** de Sololá: cortes anuales completos 2022–2025 y desglose por tipo de alojamiento;
  el corte 2026-T1 se dibuja con trama como parcial y no entra al crecimiento.
- **Ocupación mensual** 2023–2025 de Sololá frente a los demás departamentos.
- **Enlace**: clic en un año de capacidad → la ocupación se enfoca en ese año con su resumen.
- **Ventana coincidente sep–dic 2025**: noches demandadas por los turistas (Σ días-persona) frente a
  plazas-noche formales (plazas cama × días del mes), y tasa implícita frente a la ocupación oficial, en
  paneles separados (noches y porcentajes no comparten eje).
- **Desagregación por subdestinos**: índice de afluencia frente a Panajachel = 100 (nunca participación sobre
  una suma), por origen y en visitantes o días-persona.
- **Adicional**: calendario de ocupación (mapa de calor año × mes) para ver temporada alta y baja.

## 6. Módulo 4 · Red territorial de los 10 municipios (reto del grupo)

- **Cuadrante** volumen × estadía media × % extranjeros con medianas del lago.
- **Clasificación** en hub comercial, larga estancia y visita corta con una regla interpretable, contrastada
  con **k-medias** (k = 3) sobre volumen, estadía, % extranjeros y presión de fin de semana; se reportan los
  municipios donde los métodos difieren.
- **Matriz de perfiles**: 6 indicadores por municipio (color = posición relativa en cada columna).
- **Huella semanal** de cada pueblo con la base diaria: confirma que los de visita corta dependen del fin de
  semana.
- **Comparación por clase**: mercados emisores y estacionalidad.
- **Enlace**: clic en un municipio del cuadrante → perfil (serie por origen, patrón semanal, mercados).
- **Hallazgos** calculados con los datos cargados e implicaciones para el INGUAT.

## 7. Pendiente para la entrega final

1. Correr con las bases reales y revisar el reporte de calidad (nombres no reconocidos, coberturas) y los
   textos de lectura, que se calculan solos pero conviene validar con los números reales.
2. Memoria técnica: fichas de indicadores (8 campos), investigación sobre observatorios (INSTO/SEGITTUR),
   supuestos, recomendaciones para el INGUAT.
3. Opcional: integrar los boletines de ocupación (PDF) y la BD complementaria si aportan al reto.
4. Repositorio privado con catedráticos y auxiliares como colaboradores.
