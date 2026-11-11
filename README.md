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

## Estado (avance)

| Módulo | Estado | Contenido |
|---|---|---|
| 1 · Demanda y mercados emisores | ✅ Completo | KPIs (visitantes/mes, días-persona, estadía media ponderada), turista vs. excursionista, top 10 extranjeros + nacionales aparte, estadía por nacionalidad. Gráfica de municipios enlazada a todo el módulo. |
| 2 · Dinámica temporal y pronóstico | ✅ Completo | Serie diaria con selector de festividad y Lift (simple y ajustado), patrón semanal, estimación ene–feb 2026 con dos métodos sobre migración, validación MAPE/MAE/RMSE. Gráfica de Lift enlazada a la serie diaria. |
| 3 · Oferta hotelera | ✅ Completo | Capacidad instalada anual y por tipo (2026 parcial marcado), ocupación 2023–2025 y calendario de ocupación, ventana coincidente con noches demandadas vs. plazas-noche, afluencia relativa entre municipios. Clic en un año de capacidad → ocupación de ese año. |
| 4 · Red de municipios | ✅ Completo | Cuadrante volumen × estadía × % extranjeros, clasificación por regla contrastada con k-medias, matriz de perfiles, huella semanal por pueblo, mercados y estacionalidad por clase, perfil del municipio y hallazgos. Clic en el cuadrante → perfil. |

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
python -m pytest tests                              # 26 pruebas
```

## Estructura

```text
app.py                     Navegación (Inicio, 4 módulos, Calidad, Acerca)
paginas/                   Una página por módulo
src/
  normalizar.py            Limpieza de textos (municipios, países, departamentos), coma decimal y fechas
  etl.py                   Bases originales -> parquet limpios + reporte de calidad (calidad.json)
  indicadores.py           Estadía ponderada, segmentación, top 10, Lift, patrón semanal
  oferta.py                Capacidad, ocupación y cruce noches demandadas vs. plazas (módulo 3)
  territorio.py            Perfiles de los 10 municipios, regla del cuadrante y k-medias (módulo 4)
  pronostico.py            Estimación ene–feb 2026 (factor de reparto / perfil estacional) y validación
  graficas.py              Figuras Plotly
  estilo.py, ui.py         Paleta y componentes de interfaz (heredados del Lab 10)
  datos.py                 Carga con caché para el tablero
scripts/generar_sinteticos.py   Datos sintéticos con la estructura exacta de las 5 bases
config/config.yaml         Rutas, patrones de archivo, meses a estimar, ventana coincidente
tests/                     Reglas metodológicas y pruebas de humo de todas las páginas
data/                      (no versionada) raw/, sinteticos/, procesados/
docs/avances.md            Resumen del avance para la presentación
docs/normalizacion.md      Guía del proceso de normalización por tabla
```

## Reglas metodológicas implementadas

1. La ausencia de dato no es cero: ene–feb 2026 aparecen como "Sin dato" o como "Estimación".
2. Estadía media = Σ días-persona / Σ visitantes del segmento "mayor a 1"; nunca se promedia `permanencia_prom`.
3. La base diaria no se suma para obtener el mes (los visitantes del mes salen de la base mensual).
4. Los municipios no se suman como total del lago: toda cifra agregada se rotula "suma de municipios".
5. Personas y porcentajes (ocupación) van en ejes separados.
