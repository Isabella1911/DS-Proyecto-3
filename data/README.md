# Datos

Esta carpeta **no se versiona** (solo este archivo). Las bases institucionales son confidenciales.

| Carpeta | Contenido |
|---|---|
| `raw/` | Bases reales. Colóquelas aquí con su nombre original (`Base_Migracion_2009-2026jun.xlsx`, `BD_movilidad_mensual.xlsx` hoja *Atitlan*, `BD_movilidad_diaria.xlsx` hoja *Atitlan*, `indice_ocupacion_mensual_2023_2025_1.csv`, `oferta_hotelera_2022_2026.csv`). |
| `sinteticos/` | Datos inventados con la misma estructura: `python scripts/generar_sinteticos.py`. |
| `procesados/` | Salida del ETL (`python -m src.etl`): parquet limpios + `calidad.json`. |

Si un archivo no está en `raw/`, el ETL usa el sintético y el tablero muestra el aviso "Datos sintéticos".
Los nombres se buscan con comodines (ver `config/config.yaml`), así que variaciones menores del nombre funcionan.
