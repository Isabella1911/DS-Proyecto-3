# Resumen ejecutivo

El Instituto Guatemalteco de Turismo (INGUAT) requiere un observatorio que permita seguir de forma continua la demanda turística, la oferta de alojamiento y la presión sobre el territorio en sus destinos prioritarios. Este documento presenta la memoria técnica del observatorio del Lago de Atitlán, un destino integrado por diez municipios ribereños con funciones turísticas distintas. El análisis especializado asignado al equipo consiste en caracterizar esa red de municipios y distinguir los que operan como puerta de entrada de los que retienen estadías largas.

El observatorio integra siete fuentes institucionales: la movilidad por telefonía móvil (bases mensual y diaria), el flujo migratorio, el índice de ocupación hotelera, la oferta de alojamiento, los boletines anuales de ocupación y la encuesta de perfil del visitante en puestos fronterizos. El periodo de referencia de la telefonía va de <<periodo>> (<<meses>> meses con cobertura).

**Principales resultados**

1. La red tiene dos puertas de entrada y tres destinos de permanencia. <<hub_lista>> concentran el flujo, con <<hub_vis>> visitantes por mes en promedio por municipio y una estadía de <<hub_est>> días. <<larga_lista>> registran <<larga_est>> días por turista y una especialización extranjera de <<larga_iee>>, superior a la del lago en conjunto. San Marcos La Laguna, con la mayor especialización extranjera (<<iee_max>>), tiene una estadía de <<estadia_mun_iee>> días, inferior a la mediana; los datos no respaldan su posicionamiento como destino de retiro.
2. La presión sobre el destino se concentra en fechas y días específicos. <<evento_top>> eleva la afluencia diaria en <<lift_top>> frente a un día regular (<<lift_aj_top>> al controlar por día de la semana). Los fines de semana reciben <<presion>> veces la presencia de un día hábil, y <<presion_hub>> veces en los hubs.
3. La ocupación hotelera oficial describe al turismo extranjero, no al nacional. En el periodo de <<ventana>>, la hotelería formal de Sololá registró el <<capt_ext>> de las noches que la telefonía mide para los turistas extranjeros y el <<capt_nac>> de las de los nacionales. Ambas fuentes, independientes entre sí, evolucionan en la misma dirección (r = <<r_ext>> y <<r_nac>>).
4. <<mercado_lider>> es el primer mercado extranjero (<<pct_lider>> de los visitantes extranjeros) y <<mercado_estadia>> el de estadía más larga (<<estadia_mercado>> días).

**Estimación de enero y febrero de 2026.** Estos meses no tienen cobertura de telefonía. Con el perfil estacional del flujo migratorio escalado al nivel observado del destino (método <<metodo>>), se estiman <<est_m1>> visitantes en enero y <<est_m2>> en febrero (suma de municipios). La validación cruzada sobre los meses observados arroja un error porcentual absoluto medio (MAPE) de <<mape_sel>>, frente a <<mape_otro>>. La base diaria confirma la consistencia de la estimación: la rotación mensual es estable (<<rot_media>> visitantes únicos por persona presente en un día promedio, con una variación de <<rot_cv>>) y la presencia diaria implícita se ubica dentro del rango observado.

**Recomendaciones prioritarias.** (1) Reforzar transporte lacustre, seguridad y servicios municipales en los hubs durante fines de semana y fin de año. (2) Establecer con las municipalidades un registro del alojamiento no formal. (3) Orientar la promoción internacional de estadías largas hacia <<larga_lista>>. La sección 6 desarrolla estas y otras dos recomendaciones con su evidencia y su horizonte de implementación.

# 1. Introducción y alcance

## 1.1 Objetivo

Construir un observatorio de inteligencia turística para el Lago de Atitlán que permita al INGUAT monitorear la demanda, la temporalidad, la oferta de alojamiento y el comportamiento diferenciado de los diez municipios del destino, con métodos reproducibles y documentados.

## 1.2 Preguntas de gestión

::: {custom-style="Leyenda"}
Tabla 1. Preguntas de gestión por módulo
:::

| Módulo | Pregunta que responde |
|:-------|:----------------------|
| 1. Demanda y mercados emisores | ¿Cuántos visitantes recibe el lago, cuánto permanecen y de dónde provienen? |
| 2. Dinámica temporal y estimación | ¿Qué días y festividades concentran la afluencia y cuántos visitantes hubo en los meses sin cobertura? |
| 3. Oferta de alojamiento | ¿Qué capacidad tiene Sololá, qué tan ocupada está y qué parte de las noches registra la hotelería formal? |
| 4. Red de municipios | ¿Qué función cumple cada municipio en el destino y qué implica para su gestión? |

::: {custom-style="Fuente"}
Fuente: guía del proyecto CC3084 y guía de uso de los datos del INGUAT. Elaboración propia.
:::

## 1.3 Alcance y periodo de referencia

El ámbito territorial son los diez municipios ribereños: Panajachel, San Pedro La Laguna, San Lucas Tolimán, Santiago Atitlán, San Juan La Laguna, Santa Catarina Palopó, San Antonio Palopó, San Pablo La Laguna, San Marcos La Laguna y Santa Cruz La Laguna. La oferta y la ocupación hotelera se publican a nivel departamental, por lo que corresponden a todo Sololá. Las cifras de esta memoria son agregadas; ningún microdato forma parte del documento.

# 2. Arquitectura y modelo de datos

## 2.1 Fuentes utilizadas

::: {custom-style="Leyenda"}
Tabla 2. Fuentes de datos del observatorio
:::

| Fuente | Archivo y hoja | Granularidad | Uso en el observatorio |
|:-------|:---------------|:-------------|:-----------------------|
| Flujo migratorio | `Base_Migracion_2009-2026jun.xlsx`, hoja Datos | Mes, país, vía y tipo de viajero | Perfil estacional para estimar enero y febrero de 2026 |
| Telefonía, base mensual | `BD_moviidad_mensual.xlsx`, hoja Atitlan | Municipio, mes, país y segmento de estadía | Demanda, estadía y mercados emisores |
| Telefonía, base diaria | `BD_moviidad_diario.xlsx`, hoja Atitlan | Municipio, día y país, con marca de evento | Festividades, patrón semanal y verificación de la estimación |
| Índice de ocupación hotelera | `indice_ocupacion_mensual_2023_2025_1.csv` | Departamento y mes | Ocupación mensual 2023 a 2025 |
| Oferta hotelera | `oferta_hotelera_2022_2026.csv` | Departamento, corte anual y tipo de alojamiento | Capacidad instalada |
| Boletines de ocupación | Boletines de ocupación hotelera 2023, 2024 y 2025 (PDF) | Departamento, mes y residencia | Huéspedes y noches por residencia; verificación del índice |
| Encuesta en puestos fronterizos | `BD_COMPLEMENTARIA` (parquet) | Encuesta individual; se conservan solo agregados | Alojamiento declarado y puesto de ingreso de los viajeros con destino al lago |

::: {custom-style="Fuente"}
Fuente: INGUAT. Elaboración propia.
:::

Las encuestas de satisfacción y de residentes, así como los registros del aeropuerto Mundo Maya y del Parque Nacional Tikal, corresponden a otros destinos según la guía de uso de los datos y no se utilizan.

## 2.2 Relación entre las fuentes

Las bases no comparten un identificador común. Se relacionan por llaves de tiempo y territorio, siempre después de normalizar textos, números y fechas:

- El periodo (año y mes) une la telefonía mensual con el flujo migratorio, para el factor de reparto, y con la ocupación, en la ventana coincidente de septiembre a diciembre de 2025.
- El municipio une la telefonía mensual con la diaria: el perfil de cada municipio combina volumen y estadía con presión de fin de semana y efecto de las festividades.
- El departamento y el año unen la ocupación con la oferta, que es un inventario por corte.
- El departamento, el mes y la residencia unen los boletines con la telefonía: extranjeros con no residentes y nacionales con residentes.
- El destino declarado filtra la encuesta en puestos fronterizos; no se une registro a registro con otra fuente.
- Una matriz común de meses, visible en el tablero como indicador de cobertura, documenta qué fuentes respaldan cada periodo. Un mes sin cobertura se declara sin dato y nunca se trata como cero.

::: {custom-style="Leyenda"}
Figura 1. Flujo de datos y relaciones entre las fuentes
:::

![](<<fig_arquitectura>>){width=100%}

::: {custom-style="Fuente"}
Fuente: elaboración propia.
:::

## 2.3 Proceso de datos

1. `src/normalizar.py` lleva textos, números y fechas a una forma comparable: mayúsculas y tildes, abreviaturas de municipios, separadores decimales y fechas en formato de Excel o texto. Los valores no reconocidos se registran en el reporte de calidad.
2. `src/etl.py` lee cada fuente, aplica los controles de calidad y guarda una tabla depurada por fuente en formato parquet, junto con un reporte (`calidad.json`) que incluye el origen de cada archivo, su huella SHA-256 y el resultado de cada control.
3. Los boletines en PDF se procesan con código: se extrae el renglón de Sololá de las tablas mensuales de movimiento hotelero, se verifica que tenga las ocho cifras esperadas y que las habitaciones de residentes y no residentes sumen el total. El índice de ocupación extraído coincide con el archivo oficial en los 36 meses.
4. El tablero lee únicamente las tablas depuradas. Al iniciar compara la huella de los archivos de entrada con la registrada y, si cambiaron, vuelve a ejecutar el proceso.

::: {custom-style="Leyenda"}
Tabla 3. Tablas depuradas que consume el tablero
:::

| Tabla | Unidad de registro | Columnas principales |
|:------|:-------------------|:---------------------|
| `mensual.parquet` | Municipio, mes, país y segmento | municipio, periodo, país, origen, segmento, visitantes, días-persona |
| `diaria.parquet` | Municipio, día y país | municipio, fecha, país, origen, evento, día de la semana, visitantes |
| `migracion_mensual.parquet` | Mes | periodo, llegadas de turistas y excursionistas |
| `ocupacion.parquet` | Departamento y mes | departamento, periodo, índice de ocupación (0 a 1) |
| `oferta.parquet` | Departamento, corte y tipo | establecimientos, habitaciones, plazas cama, corte parcial, valor repetido |
| `boletin_hotelero.parquet` | Mes (Sololá) | habitaciones, huéspedes y noches de residentes y no residentes |
| `frontera_destino.parquet` | Combinación de categorías | encuestas y personas por ola, residencia, alojamiento, puesto y transporte |

::: {custom-style="Fuente"}
Fuente: elaboración propia.
:::

## 2.4 Calidad de los datos

::: {custom-style="Leyenda"}
Tabla 4. Registros leídos y depurados por fuente
:::

<<tabla_fuentes>>

::: {custom-style="Fuente"}
Fuente: reporte de calidad del proceso de datos. Elaboración propia.
:::

Controles con aviso o error en la última ejecución:

<<tabla_controles>>

## 2.5 Estructura del repositorio

```text
app.py              navegación del tablero
paginas/            una página por módulo, conclusiones, calidad y acerca
src/                normalización, proceso de datos, indicadores, oferta, territorio, estimación, figuras y estilo
scripts/            datos sintéticos, revisión de las bases y generación de esta memoria
config/config.yaml  rutas, patrones de archivo, meses a estimar y ventana coincidente
data/               no versionada: raw/ (institucionales), sinteticos/, procesados/
tests/              reglas metodológicas y pruebas de todas las páginas
```

El detalle de archivos se presenta en el anexo A.

# 3. Catálogo de indicadores

Cada indicador del tablero se documenta con una ficha de ocho campos: nombre, definición, fórmula, implementación en código, granularidad, unidad, fuente y reglas. En las fórmulas, $V$ representa visitantes, $DP$ días-persona, $s$ el segmento de estadía (turista con pernocta o excursionista), $t$ el mes y $d$ el día. El código opera sobre las tablas depuradas: `m` (mensual), `d` (diaria), `mig` (flujo migratorio), `ocup` (ocupación) y `oferta`.

<<fichas>>

# 4. Análisis especializado: la red de municipios

## 4.1 Planteamiento

El análisis responde a una pregunta de gestión: qué función cumple cada municipio dentro del destino. Para cada municipio se construye un perfil con seis variables. La base mensual aporta el volumen de visitantes, la estadía media ponderada, la especialización extranjera y la proporción de excursionistas; la base diaria aporta la presión de fin de semana y el efecto máximo de las festividades. Cada variable se vincula con una decisión: el volumen con la gestión de flujos, la estadía y el origen con la promoción, y la presión de fin de semana con la planificación de servicios.

La asignación sugiere usar el porcentaje de extranjeros. La guía de uso de los datos señala que calcularlo como extranjeros entre el total es un error, porque las cifras nacionales incorporan un factor de expansión que las extranjeras no tienen. Por ello se utiliza el índice de especialización extranjera (IEE), que compara la participación del municipio entre los extranjeros del lago con su participación entre los nacionales. Un factor de expansión constante se cancela en el cociente y el índice ordena a los municipios igual que la proporción de la fuente.

## 4.2 Regla de clasificación

La regla se aplica en este orden:

1. Larga estancia: estadía media en el cuartil superior del lago (<<p75_estadia>> días o más) y especialización extranjera igual o mayor que 1.
2. Hub o puerta de entrada: volumen igual o mayor que el 60% del municipio con más visitantes (<<umbral_hub>> visitantes por mes).
3. Visita corta: los municipios restantes.

La permanencia se evalúa primero porque un municipio con volumen alto y estadía excepcional funciona como destino de permanencia. Una versión preliminar de la regla exigía mayoría extranjera para la larga estancia; con los datos institucionales ningún municipio supera el 15% de extranjeros en la fuente, de modo que esa condición dejaba vacía la clase y fue sustituida por el IEE.

## 4.3 Contraste con k-medias

El agrupamiento por k-medias se utiliza como contraste de la regla y no como clasificación independiente. Con diez municipios cada observación pesa mucho, el algoritmo siempre produce el número de grupos solicitado y los grupos resultantes no tienen nombre propio.

- Variables: logaritmo del volumen, estadía media, IEE y presión de fin de semana, estandarizadas con media 0 y desviación 1.
- Ajuste: tres grupos, 50 inicios aleatorios con semilla fija; se conserva la partición de menor inercia.
- Asignación de nombres: el grupo de mayor volumen corresponde al hub; de los otros dos, el de mayor estadía corresponde a larga estancia.
- Estabilidad: al excluir un municipio a la vez y repetir el agrupamiento, el <<estabilidad>> de los restantes conserva su clase.

## 4.4 Resultados

::: {custom-style="Leyenda"}
Tabla 5. Perfil y clasificación de los municipios
:::

<<tabla_municipios>>

::: {custom-style="Fuente"}
Fuente: INGUAT, movilidad por telefonía móvil, bases mensual y diaria. Elaboración propia.
:::

La regla y k-medias coinciden en <<coinciden>> de <<n>> municipios<<difieren_texto>>.

::: {custom-style="Leyenda"}
Tabla 6. Promedio de los indicadores por tipo de municipio
:::

<<tabla_clases>>

::: {custom-style="Fuente"}
Fuente: INGUAT, movilidad por telefonía móvil. Elaboración propia.
:::

::: {custom-style="Leyenda"}
Figura 2. Tipología de los municipios por volumen, estadía y especialización extranjera
:::

![](<<fig_cuadrante>>){width=95%}

::: {custom-style="Fuente"}
Fuente: INGUAT, movilidad por telefonía móvil. Elaboración propia. El tamaño del punto representa el IEE.
:::

<<hub_lista>> funcionan como puertas de entrada: concentran el volumen y la mayor presión de fin de semana, asociada al visitante nacional que llega por carretera. <<larga_lista>> retienen las estadías más largas y una especialización extranjera superior a la del lago. San Marcos La Laguna contradice la expectativa planteada en la asignación: presenta la mayor especialización extranjera (<<iee_max>>), pero su estadía media es de <<estadia_mun_iee>> días, por debajo de la mediana. Una explicación posible es que parte de sus visitantes extranjeros pernocte en un municipio vecino; confirmarlo requiere pares origen-destino entre polígonos o una encuesta en sitio.

## 4.5 Validación con la dinámica diaria

Si la tipología fuera solo un efecto del volumen, la presión de fin de semana sería similar entre clases. Con los datos actuales es de <<presion_hub>> en los hubs, <<presion_larga>> en los municipios de larga estancia y <<presion_corta>> en los de visita corta. La diferencia indica que los hubs cumplen una función distinta como receptores de visitas de fin de semana.

## 4.6 Triangulación con la hotelería formal y la encuesta en fronteras

En la ventana de <<ventana>>, los turistas extranjeros suman <<noches_tel_ext>> noches por mes según la telefonía, y la hotelería formal registra <<noches_hotel_ext>> noches de no residentes: una captación de <<capt_ext>>. Para los nacionales la captación es de <<capt_nac>>. Como la telefonía se agrega como suma de municipios, la captación es una cota inferior.

::: {custom-style="Leyenda"}
Figura 3. Noches de turistas extranjeros por fuente, septiembre a diciembre de 2025
:::

![](<<fig_captacion>>){width=95%}

::: {custom-style="Fuente"}
Fuente: INGUAT, movilidad por telefonía móvil y boletín de ocupación hotelera 2025. Elaboración propia.
:::

La encuesta en puestos fronterizos complementa esta lectura. De <<fr_total>> encuestas, las que declaran como destino el lago muestran en la ola <<fr_ola>> (<<fr_n>> encuestas) que el <<fr_hotel>> se aloja en hotel o similar y el <<fr_airbnb>> en Airbnb o similar, y que el <<fr_puesto_pct>> ingresa por <<fr_puesto>>. La proporción de Airbnb oscila entre <<fr_airbnb_min>> y <<fr_airbnb_max>> según la ola, porque cambian las cuotas y los puestos encuestados; no se interpreta como tendencia.

## 4.7 Alcance de las conclusiones

- La tipología describe el comportamiento de cada municipio; no establece causas.
- Los volúmenes de una clase son sumas de municipios y pueden contar más de una vez a un mismo visitante. Por ello se comparan promedios por municipio e índices.
- La clasificación se recalcula automáticamente con datos nuevos y conviene revisarla cada trimestre.

# 5. Supuestos, limitaciones y calidad de las fuentes

1. Consolidación territorial. Se utilizan los registros de los diez municipios del lago. La oferta y la ocupación son departamentales: incluyen establecimientos de Sololá fuera de la ribera y no permiten un análisis de capacidad por municipio.
2. Discontinuidad de la telefonía. La cobertura va de septiembre a diciembre de 2025 y de marzo a agosto de 2026. Ningún mes se repite entre años, por lo que no existe comparación interanual directa entre 2025 y 2026. Enero y febrero de 2026 se estiman.
3. Universos distintos. La oferta, la ocupación y los boletines cubren la hotelería formal registrada. Las noches en plataformas digitales y en viviendas de familiares no forman parte de ese universo, y la captación formal no suma ambos.
4. Encuestas sin factor de expansión. La encuesta en puestos fronterizos es una muestra por cuotas, levantada sobre todo en puestos terrestres. Se reportan solo porcentajes dentro del segmento que declara ir al lago y de la ola vigente, nunca totales de visitantes.
5. Factor de expansión de los nacionales. Las cifras de visitantes nacionales vienen expandidas y no son comparables en escala con las extranjeras; ambas se reportan por separado.
6. Supuesto de la estimación. El método supone que el nivel del destino frente al perfil estacional del flujo migratorio es estable entre meses. Para los nacionales el supuesto es más débil, porque no se registran en migración.
7. Suma de municipios. El total del destino debe ser provisto por el operador de telefonía. Sumar municipios duplica a quien visita varios; todo volumen agregado se rotula como cota superior.
8. Ruptura en el flujo migratorio. La serie presenta una ruptura metodológica entre 2022 y 2023; el perfil estacional usa solo 2023 a 2025.
9. Corte parcial de la oferta. El corte de 2026 corresponde al primer trimestre y se excluye del análisis de la evolución de la capacidad.

# 6. Recomendaciones estratégicas para el INGUAT

Cada recomendación se apoya en un resultado cuantitativo del observatorio. La prioridad combina la solidez de la evidencia con el costo de no actuar.

::: {custom-style="Leyenda"}
Tabla 7. Recomendaciones, evidencia y prioridad
:::

| N.º | Recomendación | Evidencia | Decisión que apoya | Prioridad |
|:----|:--------------|:----------|:-------------------|:----------|
| 1 | Gestión de picos en las puertas de entrada | <<evento_top>> eleva la afluencia <<lift_top>>; el fin de semana recibe <<presion>> veces un día hábil y <<presion_hub>> veces en los hubs | Refuerzo de transporte lacustre, seguridad y servicios municipales en fines de semana y fin de año en <<hub_lista>> | Alta |
| 2 | Registro del alojamiento no formal | Captación formal de <<capt_ext>> en extranjeros y <<capt_nac>> en nacionales; <<fr_airbnb>> de los encuestados declara Airbnb | Registro municipal de casas de huéspedes y plataformas; lectura de la ocupación oficial como indicador del turismo extranjero | Alta |
| 3 | Promoción de estadías largas donde ya ocurren | <<larga_lista>>: <<larga_est>> días frente a <<hub_est>> en los hubs; IEE de <<larga_iee>>; <<fr_puesto_pct>> de los encuestados ingresa por <<fr_puesto>> | Promoción internacional dirigida a esos municipios y a mercados de mayor estadía, con información en la ruta terrestre de ingreso | Media |
| 4 | Atención a la temporada baja | La ocupación de Sololá desciende a <<valle_ocup>> en <<valle_mes>> (promedio 2023 a 2025) | Campañas para el mercado nacional y paquetes de fin de semana en los meses de menor ocupación | Media |
| 5 | Cobertura continua de telefonía | Enero y febrero solo se estiman (MAPE de <<mape_sel>>) | Acuerdo con el operador para cobertura de doce meses y entrega del total del destino | Base |

::: {custom-style="Fuente"}
Fuente: resultados del observatorio. Elaboración propia.
:::

::: {custom-style="Leyenda"}
Tabla 8. Hoja de ruta propuesta
:::

| Horizonte | Acciones |
|:----------|:---------|
| Corto plazo (0 a 3 meses) | Plan operativo de fines de semana y fin de año en los hubs; publicación mensual del tablero con el proceso de datos actual |
| Mediano plazo (3 a 12 meses) | Registro municipal de alojamiento no formal; acuerdo de cobertura continua con el operador de telefonía; campaña de temporada baja |
| Largo plazo (más de 12 meses) | Oferta y ocupación por municipio; encuesta en sitio con factor de expansión; indicadores ambientales para una eventual postulación a la red INSTO |

::: {custom-style="Fuente"}
Fuente: elaboración propia.
:::

Datos que convendría incorporar: telefonía continua de doce meses y el total del destino entregado por el operador; pares origen-destino entre polígonos; oferta y ocupación hotelera por municipio; un registro de plataformas digitales; una encuesta en sitio con factor de expansión que incluya gasto, motivo de viaje y alojamiento; conteos de pasajeros del transporte lacustre por muelle; e indicadores ambientales de agua y residuos.

# 7. Criterios de selección del contenido del tablero

::: {custom-style="Leyenda"}
Tabla 9. Elementos incluidos y descartados
:::

| Elemento | Decisión | Justificación |
|:---------|:---------|:--------------|
| Tipología por volumen, estadía y especialización extranjera | Incluido | Entregable del análisis especializado; k-medias aporta un contraste independiente |
| Mapa del peso de cada municipio por mes | Incluido | Solicitado para Atitlán en la guía de uso de los datos |
| Mapa de desplazamientos entre municipios | Descartado | La base no contiene pares origen-destino |
| Porcentaje de extranjeros sobre el total | Sustituido por el IEE | Error explícito en la guía de uso (factor de expansión de los nacionales) |
| Tasa implícita de ocupación (noches de telefonía entre plazas-noche) | Sustituida por la captación formal | Con datos institucionales resultaba en 578%, porque mezcla presencia nacional no turística con un universo hotelero formal |
| Tendencia de la oferta 2022 a 2026 | Descartada | Cinco cortes de inventario no constituyen una serie; se presentan como barras por corte |
| Comparación interanual 2025 frente a 2026 | Descartada | Ningún mes de telefonía se repite entre años |
| Proyección de la base diaria | Descartada | La guía la prohíbe; la base diaria solo verifica la estimación mensual |
| Encuestas de satisfacción y de residentes, aeropuerto y Tikal | Descartadas | Corresponden a otros destinos |
| Boletines de ocupación y encuesta en puestos fronterizos | Incluidos | Aportan información sobre el lago que no está en los archivos de datos |

::: {custom-style="Fuente"}
Fuente: elaboración propia.
:::

# 8. Marco de referencia: observatorios de turismo sostenible

## 8.1 Red INSTO de ONU Turismo

La Red Internacional de Observatorios de Turismo Sostenible (INSTO) de ONU Turismo se creó en 2004 para apoyar la mejora continua de la sostenibilidad y la resiliencia del sector. Reúne destinos que se comprometen a monitorear con regularidad los impactos económicos, ambientales y sociales del turismo. INSTO no impone indicadores; define áreas temáticas que cada observatorio debe medir, al menos en parte, durante sus primeros tres años: estacionalidad, empleo, beneficios económicos para el destino, gobernanza, satisfacción local, accesibilidad, energía, agua, aguas residuales, residuos sólidos y acción climática. Los miembros entregan un informe anual con el perfil del destino, sus indicadores y un diagnóstico; la falta de reporte durante dos años consecutivos implica la pérdida de la membresía.

## 8.2 SEGITTUR y los Destinos Turísticos Inteligentes

SEGITTUR es la sociedad estatal española responsable de la innovación y la tecnología turística, como medio propio de la Secretaría de Estado de Turismo. Lidera el modelo de Destinos Turísticos Inteligentes (DTI), estructurado en cinco ejes: gobernanza, innovación, tecnología, sostenibilidad y accesibilidad. El modelo se formalizó en la norma UNE 178501, sistema de gestión de los destinos turísticos inteligentes, publicada en 2016 y revisada en 2018. En octubre de 2024 la Red DTI reunía 681 miembros entre destinos, instituciones, empresas y observadores.

## 8.3 Aplicación en este observatorio

::: {custom-style="Leyenda"}
Tabla 10. Prácticas de referencia adoptadas
:::

| Práctica | Origen | Aplicación |
|:---------|:-------|:-----------|
| Monitoreo continuo con un método constante | INSTO | Proceso de datos reproducible y tablero que se actualiza al cambiar los archivos |
| Áreas temáticas antes que indicadores fijos | INSTO | Cuatro módulos; la estacionalidad es un área obligatoria de INSTO |
| Informe periódico con diagnóstico | INSTO | Página de conclusiones y esta memoria, generadas con las cifras vigentes |
| Gobernanza del dato | SEGITTUR | Confidencialidad, datos montados en solo lectura, controles de calidad y huella de cada archivo |
| Tecnología abierta e integrable | SEGITTUR | Python, Streamlit, Plotly y Docker, de código abierto |
| Accesibilidad | SEGITTUR e INSTO | Contraste mínimo de 3:1, segunda señal para daltonismo y diseño adaptable |

::: {custom-style="Fuente"}
Fuente: ONU Turismo (INSTO) y SEGITTUR. Elaboración propia.
:::

Frente a ambos modelos, el observatorio aún no mide satisfacción local, empleo ni las áreas ambientales que INSTO exige, y no integra datos en tiempo real. Son los pasos necesarios si el INGUAT decidiera postular el destino a la red INSTO.

# 9. Decisiones de tecnología y diseño

## 9.1 Selección tecnológica

::: {custom-style="Leyenda"}
Tabla 11. Justificación de la plataforma tecnológica
:::

| Necesidad | Decisión | Justificación | Alternativa descartada |
|:----------|:---------|:--------------|:-----------------------|
| Un solo lenguaje del dato al tablero | Streamlit (Python) | Reutiliza las funciones de análisis en pandas; las gráficas enlazadas se implementan sin JavaScript; incluye un marco de pruebas para cada página | Dash, por mayor código de control; Power BI y Tableau, por licencias propietarias |
| Gráficas interactivas | Plotly | Información emergente, selección de elementos para filtrar otras gráficas y exportación a imagen | matplotlib, estático |
| Despliegue reproducible | Docker | Versiones fijas en cualquier equipo; los datos institucionales se montan en solo lectura y nunca forman parte de la imagen | Instalación manual |

::: {custom-style="Fuente"}
Fuente: elaboración propia.
:::

## 9.2 Paleta y teoría del color

La paleta responde a tres criterios. El tono distingue categorías y la luminosidad expresa magnitudes: orígenes, segmentos y clases usan tonos distintos, mientras que los mapas de calor usan una sola gama de azul. Todo color de dato alcanza un contraste de al menos 3:1 sobre fondo blanco, conforme al criterio 1.4.11 de las WCAG 2.2. Ninguna categoría depende solo del color, conforme al criterio 1.4.1: la simulación de daltonismo (modelo de Machado et al., 2009) mostró que los pares turista y excursionista, y hub y visita corta, se aproximan con deuteranopia y protanopia, por lo que el excursionista lleva trama de puntos y cada clase de municipio tiene forma y trazo propios.

::: {custom-style="Leyenda"}
Tabla 12. Paleta del observatorio
:::

<<tabla_paleta>>

::: {custom-style="Fuente"}
Fuente: elaboración propia. Contraste calculado según WCAG 2.2.
:::

## 9.3 Interacción y presentación

- Cuatro gráficas enlazadas, una por módulo: municipios (módulo 1), efecto de las festividades (módulo 2), capacidad anual (módulo 3) y tipología (módulo 4). Todas llevan la indicación "Clic para filtrar" y las gráficas que reciben el filtro muestran el filtro activo.
- Cada gráfica tiene título descriptivo, subtítulo con unidades y periodo, nota metodológica y fuente.
- Barra de herramientas reducida a la exportación de imagen, sin zoom ni selección libre. La serie diaria conserva una barra de desplazamiento temporal.
- Exportación de tablas deshabilitada, aunque solo contienen agregados.
- Diseño adaptable verificado a 390 px (teléfono) y 768 px (tableta).
- Indicador de cobertura de las fuentes en la portada y en la página de calidad.

# Anexo A. Estructura del repositorio

```text
<<arbol>>
```

# Anexo B. Dependencias

```text
<<requirements>>
```

# Anexo C. Fragmentos de código

Estadía media ponderada (`src/indicadores.py`). No se promedia la columna de permanencia.

```python
<<codigo_estadia>>
```

Índice de especialización extranjera (`src/indicadores.py`).

```python
<<codigo_iee>>
```

Estimación de los meses sin cobertura (`src/pronostico.py`).

```python
<<codigo_predecir>>
```

Regla de clasificación de los municipios (`src/territorio.py`).

```python
<<codigo_regla>>
```

# Anexo D. Instalación en un servidor

Procedimiento para Ubuntu Server 24.04 LTS. El servidor requiere acceso al repositorio privado mediante una llave de despliegue.

1. Instalar Git y Docker Engine con el complemento Compose, según la guía oficial de Docker:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
```

2. Clonar el repositorio y crear la carpeta de datos fuera de él, con permisos restringidos:

```bash
sudo git clone git@github.com:Isabella1911/DS-Proyecto-3.git /opt/observatorio
sudo mkdir -p /srv/observatorio/datos && sudo chmod 750 /srv/observatorio/datos
```

Los archivos institucionales se copian a esa carpeta con su nombre original, incluidos los boletines en PDF y la base complementaria.

3. Construir e iniciar el tablero con los datos montados en solo lectura:

```bash
cd /opt/observatorio
DATOS_DIR=/srv/observatorio/datos docker compose up -d --build
curl -s http://127.0.0.1:8501/_stcore/health
```

4. El puerto escucha solo en 127.0.0.1. El acceso desde otro equipo se realiza mediante un túnel SSH o un proxy inverso con TLS y autenticación.

5. Para actualizar código o datos se ejecuta `git pull` y `DATOS_DIR=/srv/observatorio/datos docker compose up -d --build`.

# Anexo E. Revisión de las bases y regeneración de esta memoria

```bash
python scripts/revisar_datos.py            # controles, cobertura y cifras de los textos del tablero
python scripts/revisar_datos.py --esquema  # columnas, tipos y filas de cada archivo
python scripts/generar_memoria.py          # regenera este documento con las cifras vigentes
```

Ambos scripts producen solo información agregada.

# Referencias

- Docker Inc. (2026). *Install Docker Engine on Ubuntu*. <https://docs.docker.com/engine/install/ubuntu/>
- esmartcity (15 de octubre de 2024). *La Red de Destinos Turísticos Inteligentes aprueba la adhesión de 62 miembros titulares*. <https://www.esmartcity.es/2024/10/15/red-destinos-turisticos-inteligentes-aprueba-adhesion-62-miembros-titulares>
- INGUAT (2023, 2024 y 2025). *Boletín de ocupación hotelera, enero a diciembre*. Departamento de Investigación y Análisis de Mercados.
- INGUAT (2026). *Guía de uso de los datos. Tableros por destino*. Documento para los equipos del curso CC3084.
- Machado, G. M., Oliveira, M. M. y Fernandes, L. A. F. (2009). A physiologically-based model for simulation of color vision deficiency. *IEEE Transactions on Visualization and Computer Graphics*, 15(6), 1291-1298.
- ONU Turismo. *About the International Network of Sustainable Tourism Observatories (INSTO)*. <https://www.untourism.int/sustainable-development/about-insto>
- ONU Turismo. *INSTO Framework*. <https://www.untourism.int/sustainable-development/into-framework>
- Ottosson, B. (2020). *A perceptual color space for image processing*. <https://bottosson.github.io/posts/oklab/>
- Plotly Technologies. *Plotly Python Graphing Library*. <https://plotly.com/python/>
- SEGITTUR (2024). *Manual de gestión de la metodología DTI*. <https://www.destinosinteligentes.es/wp-content/uploads/2024/05/Manual-Gestion-Metodologia-DTI_Junio-2024.pdf>
- SEGITTUR. *Destinos Turísticos Inteligentes*. <https://www.segittur.es/destinos-turisticos-inteligentes/proyectos-destinos/destinos-turisticos-inteligentes/>
- Streamlit Inc. *Streamlit documentation*. <https://docs.streamlit.io>
- UNE (2022). *Normas UNE para destinos turísticos inteligentes* (nota de prensa). <https://www.une.org/salainformaciondocumentos/220928_UNE-SEGITTUR_NP_Destinos-Turisticos_Inteligentes.pdf>
- W3C (2023). *Web Content Accessibility Guidelines (WCAG) 2.2*. <https://www.w3.org/TR/WCAG22/>
