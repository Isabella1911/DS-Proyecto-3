# Normalización por tabla

Todas las bases pasan por `src/normalizar.py` antes de calcular cualquier indicador. La regla general: lo que
no se reconoce **no se descarta en silencio**, queda en el reporte de calidad (`data/procesados/calidad.json`,
página *Calidad de los datos* y `python scripts/revisar_datos.py`).

## Reglas comunes

| Problema en la fuente | Ejemplo | Qué hace la normalización |
|---|---|---|
| Nombres de columna distintos | `Tipo de Viajero`, `Año` | minúsculas, sin tildes y con guion bajo: `tipo_de_viajero`, `ano` |
| Mayúsculas, tildes y espacios | `PANAJACHEL`, `Panajachel ` | se comparan por su forma sin tildes ni espacios extra |
| Abreviaturas | `Sta. Catarina`, `Sn. Antonio`, `Stgo` | `Sta` = santa, `Sn` = san, `Sto` = santo, `Stgo` = santiago |
| Coma decimal | `2,55`, `1.234,5` | `2.55`; si hay punto y coma, el punto es separador de miles |
| Fechas | número de serie de Excel o texto `15/09/2025` | fecha (se asume día/mes/año en el texto) |
| Hojas con otro nombre | `Atitlán`, `ATITLAN` | se busca la hoja por su forma sin tildes ni mayúsculas |
| Archivos con otro nombre | `BD_movilidad_mensual (2).xlsx` | patrones con comodines en `config/config.yaml` |

## Base de migración (`Base_Migracion_*.xlsx`, hoja *Datos*)

- Columnas usadas: `Año`, `Mes cod`, `Tipo de Viajero`, `Viajero`.
- Se suman turistas y excursionistas (lista en `config.yaml`, `tipos_migracion`); se excluyen cruceristas y otros tipos.
- Controles: filas sin año, mes o viajeros (se excluyen); viajeros negativos (error).
- Salida: `migracion_mensual.parquet`, una fila por mes con `llegadas`.

## Movilidad mensual (`*movilidad*mensual*.xlsx`, hoja *Atitlan*)

- Municipios: se reconocen los 10 del lago por el núcleo del nombre (`SAN MARCOS` = San Marcos La Laguna, `PANA` = Panajachel). Otros destinos se reportan como "Municipio no reconocido" y se excluyen.
- Países: alias y tildes (`EEUU`, `USA`, `ESTADOS UNIDOS DE AMERICA` = Estados Unidos). El país nacional (`pais_nacional`) define el origen Nacional / Extranjero.
- Segmento: `mayor a 1` = turista con pernocta, `menor a 1` = excursionista; otros valores se reportan.
- Controles: días-persona menores que visitantes (error); excursionistas con permanencia distinta de 1 (aviso); `permanencia_prom` que no cuadra con días-persona / visitantes (aviso, la columna solo se usa para verificar); filas repetidas para la misma combinación (se suman).
- Salida: `mensual.parquet`.

## Movilidad diaria (`*movilidad*diari*.xlsx`, hoja *Atitlan*)

- Municipios y países: igual que la mensual.
- Evento: `Regular`, `Normal`, `Ninguno`, vacío = día regular; el resto se escribe en formato título.
- Día de la semana: se recalcula desde la fecha; si no coincide con `dia_semana` de la fuente se reporta.
- Controles: fecha o visitantes sin dato (se excluyen); días con más de un evento en el mismo municipio (se conserva el primero).
- Salida: `diaria.parquet`. Nunca se suma para obtener el mes.

## Ocupación (`indice_ocupacion_mensual*.csv`)

- Departamentos sin tilde o en mayúsculas (`SOLOLA` = Sololá).
- Índice en porcentaje (valores mayores que 1) se divide entre 100; fuera de 0 a 1 es error.
- Un mes sin dato se excluye; nunca se toma como 0 %.
- Salida: `ocupacion.parquet`.

## Oferta hotelera (`oferta_hotelera*.csv`)

- Departamentos y tipos de alojamiento normalizados.
- `corte_parcial`: el último trimestre del año es menor que 4 (corte 2026-T1).
- `repite_previo`: la combinación departamento y tipo repite exactamente el valor del corte anterior; se reporta qué porcentaje del corte parcial lo hace.
- Salida: `oferta.parquet`.

## Agregar un alias nuevo

Si la página de Calidad muestra un nombre no reconocido que sí es uno de los 10 municipios (o un país mal escrito),
se agrega su forma sin tildes a `_NUCLEO_MUNICIPIO` o `_PAISES` en `src/normalizar.py`, se agrega un caso a
`tests/test_indicadores.py::test_normalizar_municipios` y se vuelve a correr el tablero (el ETL se reprocesa solo).
