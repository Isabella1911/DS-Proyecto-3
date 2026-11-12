# Observatorio de Inteligencia Turística · Lago de Atitlán

Proyecto final de CC3084 Data Science (UVG, 2026) · **Grupo 3** · Destino: Lago de Atitlán (Sololá).
Reto analítico: caracterización territorial y cuadrante analítico de los 10 municipios ribereños.

Tablero en **Streamlit + Plotly** (100 % código abierto), contenerizado con **Docker**. Reutiliza el sistema
visual, la paleta validada y la estimación con la base de migración de los Laboratorios 10 y 11.

> **Datos.** Las bases institucionales son confidenciales y **no están en este repositorio** (ver
> [data/README.md](data/README.md)). Sin ellas, el tablero funciona con **datos sintéticos** de la misma
> estructura y lo indica con un aviso en cada página.

## Equipo

- Anthony Lou Schwank
- Christa Isabella Obando Guzmán
- Fabian Prado Dluzniewski
- Luis Fernando Mendoza Alvarez

## Estado

| Módulo | Estado | Contenido |
|---|---|---|
| Inicio | ✅ Completo | KPIs del lago e **indicador de cobertura** (qué fuente respalda cada mes; meses estimados recuadrados). |
| 1 · Demanda y mercados emisores | ✅ Completo | KPIs (visitantes/mes, días-persona, estadía media ponderada), extranjeros y nacionales por separado, turista vs. excursionista, top 10 extranjeros, estadía por nacionalidad. Gráfica de municipios enlazada a todo el módulo. |
| 2 · Dinámica temporal y pronóstico | ✅ Completo | Serie diaria con selector de festividad y Lift (simple y ajustado), patrón semanal, estimación ene–feb 2026 con dos métodos sobre migración, validación MAPE/MAE/RMSE y verificación con la base diaria (rotación mensual). Gráfica de Lift enlazada a la serie diaria. |
| 3 · Oferta hotelera | ✅ Completo | Capacidad instalada anual y por tipo (2026 parcial marcado), ocupación 2023–2025 y calendario, **captación formal de noches** por origen en sep–dic 2025 (telefonía × boletines PDF), alojamiento y puerta de ingreso declarados (BD complementaria), afluencia relativa entre municipios. Clic en un año de capacidad → ocupación de ese año. |
| 4 · Red de municipios | ✅ Completo | Cuadrante volumen × estadía × especialización extranjera (IEE), regla contrastada con k-medias, **mapa animado** del peso de cada pueblo mes a mes, matriz de perfiles, huella semanal, mercados y estacionalidad por clase, perfil del municipio y hallazgos. Clic en el cuadrante → perfil. |
| Conclusiones | ✅ Completo | La historia de los cuatro módulos con cifras recalculadas y 5 recomendaciones con su evidencia, la decisión que apoyan y su prioridad. Cada módulo termina con un enlace al siguiente. |
| Memoria técnica | ✅ Completa | [docs/memoria/Memoria_tecnica_Grupo3.docx](docs/memoria/Memoria_tecnica_Grupo3.docx), generada con `scripts/generar_memoria.py` **con las bases reales** (solo agregados). |
| Guion de la demo | ✅ | [docs/guion_presentacion.md](docs/guion_presentacion.md): recorrido por preguntas de gestión, reparto, hallazgos → recomendaciones y preguntas probables. |

**Fuentes usadas (7):** telefonía mensual y diaria, migración, ocupación, oferta, boletines de ocupación 2023–2025
(PDF, extraídos con código y verificados contra el CSV) y BD complementaria (encuesta en fronteras, solo agregados).

Interfaz: cuatro gráficas enlazadas con la misma pista "Clic para filtrar", barra de Plotly uniforme (solo
PNG), tablas sin descarga CSV, paleta con contraste 3:1 y segunda señal para daltonismo, diseño probado a
375 px y 768 px, y mensaje "Preparando datos..." en la primera carga.

## Cómo correrlo

### Con Docker (recomendado)

```bash
docker compose up --build        # http://localhost:8501
```

Para usar los datos reales, colóquelos en `data/raw/` (o `DATOS_DIR=/ruta docker compose up`). Se montan en
solo lectura; la imagen nunca los contiene.

### Local

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt      # Windows (Linux/Mac: .venv/bin/pip)
python scripts/generar_sinteticos.py                # datos de demostración
python -m src.etl                                   # limpieza -> data/procesados/
streamlit run app.py
python -m pytest tests                              # 41 pruebas
```

### Con las bases reales

Quien tenga las bases las coloca en `data/raw/` con su nombre original (los del paquete oficial, incluida la errata
`BD_moviidad_*.xlsx`, los tres boletines PDF y `BD_COMPLEMENTARIA`) (o indica la carpeta con `OBS_DATOS`). El
tablero detecta que cambiaron los archivos y vuelve a correr el ETL solo. Antes de presentar:

```bash
python scripts/revisar_datos.py            # controles, cobertura y cifras de los textos de lectura; marca [REVISAR]
python scripts/revisar_datos.py --esquema  # solo columnas, tipos y filas (sirve para fuentes nuevas)
python scripts/generar_memoria.py          # regenera la memoria con las cifras reales
```

Ambos scripts imprimen solo agregados, nunca filas de las bases. La memoria necesita además
`pip install -r requirements-memoria.txt` y Chrome/Chromium para exportar las figuras
(si no está en el PATH: `BROWSER_PATH=/ruta/a/chrome`). El documento se construye directamente en Word con python-docx.

## Estructura

```text
app.py                     Navegación (Inicio, 4 módulos, Conclusiones, Calidad, Acerca)
paginas/                   Una página por módulo, más conclusiones, calidad y acerca
src/
  normalizar.py            Limpieza de textos (municipios, países, departamentos), coma decimal y fechas
  etl.py                   Bases originales (y boletines PDF, BD complementaria) -> parquet + calidad.json
  indicadores.py           Estadía ponderada, segmentación, top 10, Lift, patrón semanal
  oferta.py                Capacidad, ocupación y captación formal de noches por origen (módulo 3)
  territorio.py            Perfiles de los 10 municipios, regla del cuadrante y k-medias (módulo 4)
  pronostico.py            Estimación ene–feb 2026 (factor de reparto / perfil estacional) y validación
  hallazgos.py             Cifras clave de los 4 módulos (conclusiones, revisión y memoria)
  graficas.py              Figuras Plotly
  estilo.py, ui.py         Paleta y componentes de interfaz (heredados del Lab 10)
  datos.py                 Carga con caché y reproceso al cambiar los archivos de entrada
scripts/generar_sinteticos.py   Datos sintéticos con la estructura exacta de las 5 bases
scripts/revisar_datos.py        Revisión de las bases reales antes de presentar
scripts/generar_memoria.py      Memoria técnica en DOCX con las cifras vigentes
scripts/informe_docx.py         Construcción del informe en Word: tablas con ancho fijo, leyendas, recuadros
scripts/maquetar_memoria.py     Portada, encabezado, pie y numeración de páginas de la memoria
scripts/fichas_indicadores.py   Lectura de las fichas de indicadores para el informe
config/config.yaml         Rutas, patrones de archivo, meses a estimar, ventana coincidente
tests/                     Reglas metodológicas y pruebas de humo de todas las páginas
data/                      (no versionada) raw/, sinteticos/, procesados/
docs/avances.md            Resumen del avance
docs/guion_presentacion.md Guion de la demo y preguntas probables
docs/normalizacion.md      Guía del proceso de normalización por tabla
docs/memoria/              Plantilla, fichas de indicadores y la memoria técnica (DOCX)
```

## Reglas metodológicas implementadas

1. La ausencia de dato no es cero: ene–feb 2026 aparecen como "Sin dato" o como "Estimación".
2. Estadía media = Σ días-persona / Σ visitantes del segmento "mayor a 1"; nunca se promedia `permanencia_prom`.
3. La base diaria no se suma para obtener el mes (los visitantes del mes salen de la base mensual).
4. Los municipios no se suman como total del lago: toda cifra agregada se rotula "suma de municipios".
5. Personas y porcentajes (ocupación) van en ejes separados.
6. Nunca se calcula extranjeros / total (los nacionales traen factor de expansión): se reportan por separado y, por
   municipio, se usa el índice de especialización extranjera (cociente de localización).
7. Todo cruce telefonía × hotelería se limita a sep–dic 2025 y va por origen (extranjeros ↔ no residentes).
8. Las encuestas se reportan como porcentajes muestrales, nunca como totales.
