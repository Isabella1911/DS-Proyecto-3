<<aviso_datos>>

# Resumen ejecutivo

**El reto.** El Lago de Atitlán no es un destino único: es una red de diez municipios ribereños que reciben visitantes muy distintos. Algunos son puerta de entrada, otros retienen estancias largas de extranjeros y otros viven de excursiones de fin de semana. El reto del grupo fue caracterizar esa red con las bases del observatorio y traducirla en decisiones para el INGUAT: dónde reforzar la gestión de flujo, dónde promover estancias y qué datos faltan para medir mejor.

**Hallazgos principales** (<<periodo>>, <<meses>> meses con telefonía):

1. **<<titulo_h1>>** <<hub_lista>> concentran el flujo (<<hub_vis>> visitantes por mes en promedio por pueblo) y sus turistas se quedan <<hub_est>> días. En <<larga_lista>> la estancia media sube a <<larga_est>> días y atraen proporcionalmente más extranjeros que el lago (índice de especialización <<larga_iee>>). San Marcos, con la mayor especialización extranjera (<<iee_max>>), tiene en cambio una estadía de <<estadia_mun_iee>> días: la telefonía no respalda su imagen de destino de retiro.
2. **Los picos los marcan las festividades y los fines de semana, sobre todo en las puertas de entrada.** <<evento_top>> eleva la afluencia <<lift_top>> frente a un día regular (<<lift_aj_top>> si se compara con el mismo día de la semana); los sábados y domingos reciben <<presion>> veces los visitantes de un día hábil, y <<presion_hub>> en los hubs.
3. **La ocupación oficial describe al turismo extranjero, no al nacional.** En <<ventana>>, los hoteles formales de Sololá registran el <<capt_ext>> de las noches que la telefonía mide para los turistas extranjeros y solo el <<capt_nac>> de las de los nacionales; ambas fuentes, independientes, se mueven juntas (r = <<r_ext>> y <<r_nac>>). Entre quienes entran al país rumbo al lago, el <<fr_airbnb>> declara Airbnb o similar.
4. **<<titulo_h4>>** Un mercado pequeño de estancia larga puede generar tantas noches como uno masivo de visita corta.

**Estimación de enero y febrero de 2026.** La telefonía no cubre esos meses. Con el factor de reparto sobre la base de migración se estiman **<<est_m1>>** y **<<est_m2>>** visitantes (suma de municipios). El método elegido es el <<metodo>> (<<metodo_nombre>>), que tuvo el menor error al validar dejando un mes fuera: MAPE de <<mape_sel>> (el otro método: <<mape_otro>>). La base diaria confirma la forma: la rotación mensual (visitantes únicos por presente diario) es estable (<<rot_media>>, variación <<rot_cv>>) y la presencia diaria que implica la estimación cae dentro del rango observado. Las estimaciones se rotulan siempre como *Estimación* y no se mezclan con lo observado.

![Visitantes por mes (suma de municipios): observado en negro y Estimación en violeta.](<<fig_estimacion>>){width=95%}

# 1. Arquitectura y modelo de datos

## 1.1 Las siete fuentes

| Fuente | Archivo y hoja | Granularidad | Columnas que se usan | Uso |
|:-------|:---------------|:-------------|:---------------------|:----|
| Migración | `Base_Migracion_2009-2026jun.xlsx`, hoja *Datos* | Mes x país x vía x tipo de viajero (nacional) | `Año`, `Mes cod`, `Tipo de Viajero`, `Viajero` | Llegadas internacionales para estimar ene-feb 2026 (módulo 2) |
| Movilidad mensual | `BD_moviidad_mensual.xlsx`, hoja *Atitlan* | Municipio x mes x país x segmento | `destino`, `anio`, `mes`, `pais`, `es_consecutivo`, `visitantes`, `dias_persona`, `permanencia_prom` | Demanda, estadía, mercados (módulos 1, 3 y 4) |
| Movilidad diaria | `BD_moviidad_diario.xlsx`, hoja *Atitlan* | Municipio x día x país | `destino`, `idfecha`, `pais`, `evento`, `cantidad_visitantes`, `dia_semana` | Festividades, patrón semanal, verificación de la estimación (módulos 2 y 4) |
| Ocupación | `indice_ocupacion_mensual_2023_2025_1.csv` | Departamento x mes | `anio`, `mes`, `departamento`, `indice_ocupacion` | Ocupación hotelera (módulo 3) |
| Oferta | `oferta_hotelera_2022_2026.csv` | Departamento x corte (año y trimestre) x tipo | `anio`, `trimestre`, `departamento`, `tipo_alojamiento`, `establecimientos`, `habitaciones`, `plazas_cama` | Capacidad instalada (módulo 3) |
| Boletines de ocupación (opcional) | `BOLETIN OCUPACION HOTELERA ... 2023/2024/2025.pdf`, tabla mensual *Movimiento hotelero de turistas residentes y no residentes* | Departamento x mes x residencia | Habitaciones ocupadas, huéspedes registrados, noches realizadas, índice | Noches en hotel formal por residencia para la ventana coincidente; verificación del CSV (módulo 3) |
| BD complementaria (opcional) | `BD_COMPLEMENTARIA` (parquet), encuesta de perfil en puestos fronterizos | Encuesta individual (solo se conservan agregados) | `nuevo_destino`, `BD` (ola), `hospedaje`, `nombre_frontera`, `agrupacion_nombre`, `fecha` | Alojamiento declarado y puerta de ingreso de quienes van al lago (módulo 3) |

Del paquete se descartaron, por no corresponder a Atitlán según la guía de uso, las encuestas de satisfacción y de residentes (solo Antigua y Petén) y los archivos del aeropuerto y de Tikal (solo Petén).

## 1.2 Cómo se relacionan

Las bases no comparten un identificador único; se unen por llaves de tiempo y territorio, siempre después de normalizarlas:

- **Periodo (año y mes)** une la movilidad mensual con la migración (factor de reparto) y con la ocupación (ventana coincidente).
- **Municipio** une la movilidad mensual con la diaria: el perfil de cada pueblo combina volumen y estadía (mensual) con presión de fin de semana y festividades (diaria).
- **Departamento y año** unen la ocupación con la oferta (inventario de cada corte).
- **Departamento, mes y residencia** unen el boletín con la telefonía en la ventana sep–dic 2025: extranjeros con no residentes y nacionales con residentes. Su índice de ocupación se cruza con el CSV como control (coinciden en todos los meses).
- **Destino declarado** filtra la encuesta en fronteras (`nuevo_destino = Lago Atitlán`); no se une fila a fila con otra base.
- Una **tabla de meses común** (indicador de cobertura en Inicio y Calidad) muestra qué fuentes respaldan cada mes; un mes sin cobertura se declara *sin dato*.
- La movilidad diaria **nunca se suma** para obtener el mes: mide presencia por día y la misma persona aparece en cada día que pasa en el destino.

![Flujo de datos y relaciones entre las bases](<<fig_arquitectura>>){width=100%}

## 1.3 Del archivo original al tablero

1. `src/normalizar.py` lleva textos, números y fechas a una forma comparable: mayúsculas y tildes (`PANAJACHEL` = `Panajachel `), abreviaturas (`Sta.`, `Sn.`), nombres cortos de municipios (`SAN MARCOS` = San Marcos La Laguna), coma decimal (`2,55`) y fechas de Excel o texto. Lo que no reconoce no se descarta en silencio: queda en el reporte de calidad.
2. `src/etl.py` lee cada fuente, aplica los controles y guarda una tabla limpia por fuente en **parquet** (`data/procesados/`), más `calidad.json` con el origen de cada archivo (real o sintético), su huella SHA-256 y el resultado de cada control.
3. El tablero solo lee los parquet. Al iniciar, compara la huella de los archivos de entrada con la registrada; si cambiaron (por ejemplo, se colocaron las bases reales en `data/raw/`), vuelve a correr el ETL y muestra "Preparando datos..." mientras tanto.

| Tabla parquet | Una fila es | Columnas principales |
|:--------------|:------------|:---------------------|
| `mensual.parquet` | municipio x mes x país x segmento | `municipio`, `periodo`, `pais`, `origen`, `segmento`, `visitantes`, `dias_persona` |
| `diaria.parquet` | municipio x día x país | `municipio`, `fecha`, `pais`, `origen`, `evento`, `dia_semana`, `visitantes` |
| `migracion_mensual.parquet` | mes | `periodo`, `anio`, `mes`, `llegadas` (turistas + excursionistas) |
| `ocupacion.parquet` | departamento x mes | `departamento`, `periodo`, `ocupacion` (0 a 1) |
| `oferta.parquet` | departamento x corte x tipo | `departamento`, `anio`, `trimestre`, `tipo_alojamiento`, medidas, `corte_parcial`, `repite_previo` |
| `boletin_hotelero.parquet` | mes (Sololá) | `periodo`, habitaciones, huéspedes y noches de residentes y no residentes, `ocupacion`, `archivo` |
| `frontera_destino.parquet` | combinación ola x residencia x alojamiento x puesto x transporte x rango de noches | `encuestas`, `personas`, `desde`, `hasta` (solo agregados) |

## 1.4 Calidad de los datos

<<tabla_fuentes>>

Controles con aviso o error en la última ejecución:

<<tabla_controles>>

La página *Calidad de los datos* del tablero muestra lo mismo y `scripts/revisar_datos.py` lo imprime junto con las cifras que usan los textos de lectura, para revisarlas con las bases reales antes de presentar.

## 1.5 Estructura de carpetas

```text
app.py              navegación del tablero
paginas/            una página por módulo, conclusiones, calidad y acerca
src/                normalización, ETL, indicadores, oferta, territorio, pronóstico, hallazgos, figuras y estilo
scripts/            datos sintéticos, revisión de las bases reales y esta memoria
config/config.yaml  rutas, patrones de archivo, meses a estimar y ventana coincidente
data/               no se versiona: raw/ (reales), sinteticos/, procesados/ (parquet)
tests/              reglas metodológicas y pruebas de humo de todas las páginas
```

El árbol completo está en el Anexo A.

# 2. Catálogo de indicadores

Cada indicador del tablero tiene una ficha de ocho campos: nombre, definición, fórmula, código pandas, granularidad, unidad, archivo/hoja/columnas y reglas. En las fórmulas, $V$ son visitantes, $DP$ días-persona, $s$ el segmento (turista "mayor a 1" o excursionista "menor a 1"), $t$ el mes y $d$ el día. El código usa las tablas limpias del ETL: `m` (mensual), `d` (diaria), `mig` (migración), `ocup` (ocupación) y `oferta`.

<<fichas>>

# 3. Desarrollo del reto: la red de municipios

## 3.1 Pregunta y variables

¿Qué papel juega cada pueblo del lago? Se construye un perfil por municipio con seis variables: visitantes promedio por mes, estadía media ponderada, índice de especialización extranjera (IEE) y porcentaje de excursionistas (base mensual), y presión de fin de semana y Lift máximo de festividad (base diaria). El IEE reemplaza al "porcentaje de extranjeros" que sugiere la asignación: la guía de uso prohíbe dividir extranjeros entre el total porque los nacionales traen factor de expansión. El IEE compara la cuota del pueblo entre los extranjeros del lago con su cuota entre los nacionales, de modo que un factor de expansión constante se cancela, y ordena a los municipios igual que la proporción de la fuente. Las variables se eligieron porque cada una responde a una decisión distinta: el volumen a la gestión de flujo, la estadía y el origen a la promoción, y la presión de fin de semana a la planificación de servicios.

## 3.2 Regla del cuadrante

Es la clasificación principal porque se puede explicar en una frase y repetir cada mes:

1. **Larga estancia:** estadía en el cuartil superior del lago (hoy, <<p75_estadia>> días o más) e IEE de al menos 1.
2. **Hub comercial (puerta de entrada):** volumen de al menos el 60 % del municipio con más visitantes (hoy, <<umbral_hub>> visitantes por mes).
3. **Visita corta:** el resto.

La permanencia se evalúa primero: un pueblo con mucho volumen y estadía excepcional es un destino de permanencia, no de paso. Una primera versión de la regla exigía "mayoría extranjera" para larga estancia; con los datos reales ningún pueblo pasa del 15 % en la fuente, así que esa condición dejaba la clase vacía y se reemplazó por IEE ≥ 1. El cuadrante del módulo 4 dibuja el volumen (escala logarítmica) contra la estadía, con el tamaño según el IEE y los umbrales de la regla como líneas punteadas. Un mapa del lago animado mes a mes muestra el peso de cada pueblo (visitantes únicos del mes) con el color de su clase; la base no trae pares origen-destino, así que no se dibujan desplazamientos.

## 3.3 k-medias como contraste

k-medias agrupa a los municipios por parecido, sin reglas fijas. Se usa como contraste de la regla y no como clasificación independiente, por tres razones: con diez municipios cada uno pesa mucho, el algoritmo siempre devuelve los grupos que se le piden aunque no existan, y sus grupos no tienen nombre propio.

- **Variables:** $\log_{10}$ del volumen (la distribución es muy asimétrica: sin el logaritmo el hub dominaría la distancia), estadía media, IEE y presión de fin de semana.
- **Escala:** cada variable se estandariza (media 0, desviación 1) para que ninguna pese más por su unidad. Es una decisión de negocio: las cuatro dimensiones importan lo mismo para el INGUAT.
- **Ajuste:** $k = 3$, 50 inicios aleatorios con semilla 42 y se conserva la partición de menor inercia. Implementado con numpy, sin dependencias nuevas.
- **Nombres:** el grupo con mayor volumen es el hub; de los otros dos, el de mayor estadía es larga estancia y el restante visita corta.
- **Estabilidad:** se quita un municipio a la vez, se vuelve a agrupar y se cuenta cuántos de los demás conservan su clase. Hoy la estabilidad es <<estabilidad>>.

## 3.4 Resultados

<<tabla_municipios>>

Regla y k-medias coinciden en **<<coinciden>> de <<n>>** municipios<<difieren_texto>>.

<<tabla_clases>>

![Cuadrante de los municipios (regla del cuadrante). Color y forma: clase; tamaño: especialización extranjera.](<<fig_cuadrante>>){width=95%}

**Lectura.** <<hub_lista>> son las puertas de entrada: concentran el volumen y la presión de fin de semana (nacionales que llegan por carretera). <<larga_lista>> retienen las estancias más largas y más peso extranjero. San Marcos es el caso que contradice la expectativa de la asignación ("larga estancia/retiro"): tiene la mayor especialización extranjera del lago (IEE <<iee_max>>) pero una estadía de <<estadia_mun_iee>> días, por debajo de la mediana. Una explicación posible es que muchos extranjeros duermen en un pueblo vecino (San Pedro está a minutos en lancha) y lo visitan de día; confirmarlo exige pares origen-destino entre polígonos o una encuesta en sitio. k-medias separa sobre todo por niveles de volumen, por eso difiere de la regla en los pueblos intermedios.

## 3.5 Validación con la dinámica diaria

Si la clasificación es correcta, los pueblos de visita corta deberían depender más del fin de semana que los de larga estancia. Con los datos actuales la presión de fin de semana es <<presion_corta>> en visita corta y <<presion_larga>> en larga estancia: <<validacion_texto>>

## 3.6 Qué se puede afirmar y qué no

- La tipología **describe** cómo se comporta cada pueblo; no explica por qué. Decir que un pueblo es de visita corta "porque" está cerca de Panajachel sería una hipótesis, no un resultado.
- Los volúmenes de una clase son **suma de municipios**: un visitante que recorre varios pueblos cuenta en cada uno. Por eso se comparan promedios simples por municipio e índices, nunca totales.
- La clasificación se recalcula sola con datos nuevos; conviene revisarla cada trimestre para ver si algún pueblo cambia de papel.

## 3.7 Triangulación con la hotelería formal y la encuesta en fronteras

El reto pide aprovechar todas las fuentes. Para Atitlán se integraron las dos fuentes opcionales de la asignación:

- **Boletines de ocupación 2023–2025.** Se extrajo con código (pypdf) el renglón de Sololá de las 36 tablas mensuales de movimiento hotelero por residencia; cada renglón debe tener ocho cifras y cumplir que las habitaciones de residentes más las de no residentes igualen el total. El índice de ocupación extraído coincide con el CSV oficial en los 36 meses, lo que valida la extracción. La guía advierte contra extraer a mano cifras que ya están en los archivos: por eso del boletín solo se usa lo que el CSV no trae (huéspedes y noches por residencia).
- **Captación formal.** En <<ventana>> los turistas extranjeros suman <<noches_tel_ext>> noches por mes según la telefonía y los hoteles formales registran <<noches_hotel_ext>> noches de no residentes: captación de <<capt_ext>>. Para nacionales es de <<capt_nac>>. Como la telefonía es suma de municipios, la captación es una cota inferior.
- **Encuesta en fronteras (BD complementaria).** De <<fr_total>> encuestas, las que declaran ir al lago muestran en la ola <<fr_ola>> (<<fr_n>> encuestas) que el <<fr_hotel>> se aloja en hotel o similar y el <<fr_airbnb>> en Airbnb o similar, y que el <<fr_puesto_pct>> entra por <<fr_puesto>>. La proporción de Airbnb varía entre <<fr_airbnb_min>> y <<fr_airbnb_max>> según la ola (cambian cuotas y puestos), así que no se lee como tendencia.

La conclusión es robusta a esas limitaciones: el registro hotelero formal describe bien al turismo extranjero y casi nada de la presencia nacional con pernocta.

# 4. Supuestos y limitaciones

1. **Solo datos de Sololá.** Se usan los registros de los diez municipios del lago. Otros destinos que aparezcan en las bases se reportan en *Calidad de los datos* y se excluyen. La ocupación y la oferta son departamentales: no hay capacidad por municipio.
2. **Sin comparación 2025 contra 2026.** La telefonía no cubre enero ni febrero de ningún año. Esos meses se estiman y no hay un mismo mes observado en dos años, así que no se puede medir el crecimiento interanual.
3. **Hotelería formal y plataformas digitales son universos distintos.** La oferta, la ocupación y los boletines cubren establecimientos registrados; las noches en Airbnb o casas de familia no están ahí. La captación formal no suma ambos universos: mide qué parte de las noches de la telefonía registra el hotel formal.
4. **Encuestas sin factor de expansión.** La encuesta en fronteras es una muestra por cuotas sin factor de expansión, levantada sobre todo en puestos terrestres (el aeropuerto está subrepresentado). Solo se reportan porcentajes dentro del segmento que declara ir al lago y de la ola vigente, nunca totales de visitantes ni series de tiempo. Las encuestas de satisfacción y de residentes no existen para Atitlán.
5. **Nacionales con factor de expansión.** El conteo de nacionales de la telefonía ya viene expandido y no es comparable en la misma escala que el de extranjeros: se reportan por separado.
6. **Estimación.** El factor de reparto supone que la fracción de llegadas internacionales que llega al lago es estable entre meses. Para los nacionales el supuesto es más débil porque no pasan por migración.
7. **Corte de oferta 2026 parcial.** Es del primer trimestre y repite valores del año previo en buena parte de las combinaciones; no entra al cálculo de crecimiento.
8. **Telefonía como suma de municipios.** El total del lago debe solicitarse al proveedor; sumar los diez municipios duplica a quien visita varios pueblos. Todo volumen agregado se rotula como suma de municipios (cota superior) y los cocientes (estadía, captación) se interpretan en consecuencia.
9. **Ruptura en la migración.** La base de migración tiene una ruptura metodológica entre 2022 y 2023; el perfil estacional usa solo 2023–2025.
10. **Datos sintéticos en el repositorio.** Por la cláusula de confidencialidad, el repositorio y la imagen de Docker solo contienen datos sintéticos con la misma estructura. Las cifras de esta memoria corresponden a los datos indicados en la primera página.

# 5. Recomendaciones para el INGUAT

Cada recomendación se apoya en un hallazgo cuantitativo del tablero y tiene una prioridad según la solidez de la evidencia y el costo de no actuar.

| # | Recomendación | Evidencia | Decisión que apoya | Prioridad |
|:--|:--------------|:----------|:-------------------|:----------|
| 1 | **Gestionar los picos en las puertas de entrada** | <<evento_top>> <<lift_top>> sobre un día regular; fin de semana <<presion>> veces un día hábil y <<presion_hub>> en <<hub_lista>> | Reforzar transporte lacustre, seguridad y servicios municipales sábados, domingos y fin de año en los hubs; planificar con el patrón semanal de cada pueblo | Alta |
| 2 | **Medir el alojamiento que hoy no se ve** | Captación formal de <<capt_ext>> en extranjeros y <<capt_nac>> en nacionales; <<fr_airbnb>> de los encuestados rumbo al lago declara Airbnb | Crear con las municipalidades un registro de casas de huéspedes y plataformas digitales; hasta entonces, leer la ocupación oficial como indicador del turismo extranjero | Alta |
| 3 | **Promover estancias largas donde ya ocurren** | <<larga_lista>>: <<larga_est>> días frente a <<hub_est>> en los hubs e IEE <<larga_iee>>; <<mercado_estadia>> es el mercado de mayor estadía; el <<fr_puesto_pct>> de los encuestados entra por <<fr_puesto>> | Orientar la promoción internacional de estadías largas a esos pueblos y mercados, con información turística en la ruta terrestre de ingreso | Media |
| 4 | **Atacar la temporada baja** | La ocupación de Sololá cae a <<valle_ocup>> en <<valle_mes>> (promedio 2023–2025) frente a picos sobre 90 % | Campañas para el mercado nacional y paquetes de fin de semana en los meses valle, cuando sobra capacidad formal | Media |
| 5 | **Cerrar el hueco de telefonía** | Enero y febrero solo se estiman (MAPE <<mape_sel>>) y no hay comparación 2025 vs 2026 | Pedir al proveedor cobertura continua y el total del destino; actualizar el tablero cada mes con el mismo ETL | Base |

**Datos nuevos que convendría incorporar:** telefonía continua de 12 meses y el total del destino entregado por el proveedor; pares origen-destino entre polígonos (para confirmar el caso de San Marcos y medir el flujo entre pueblos); oferta y ocupación por municipio; un registro de plataformas digitales; una encuesta en sitio con factor de expansión (gasto, motivo, alojamiento); conteos del transporte lacustre por muelle; e indicadores ambientales (agua, residuos) que INSTO considera obligatorios.

# 5.1 Qué se incluyó en el tablero y qué se descartó

| Elemento | Decisión | Razón |
|:---------|:---------|:------|
| Cuadrante volumen x estadía x especialización, regla y k-medias | Incluido | Es el entregable del reto en la asignación; k-medias da un contraste independiente de la regla |
| Mapa animado del peso de cada pueblo | Incluido | La guía de uso lo pide para Atitlán ("mapa con el peso de cada pueblo y su evolución mensual") |
| Mapa de desplazamientos entre pueblos | Descartado | La base no trae pares origen-destino; dibujarlo sería inventar flujos |
| Porcentaje de extranjeros = extranjeros / total | Sustituido por el IEE | Error explícito en la guía de uso (nacionales con factor de expansión) |
| Tasa implícita de ocupación (noches de telefonía / plazas-noche) | Descartada en la versión final | Con datos reales daba 578 %: mezcla presencia nacional no turística con un universo hotelero formal. Se reemplazó por la captación formal por origen con los boletines |
| Tendencia de la oferta 2022–2026 | Descartada | Son cinco cortes de inventario; se muestran como barras por corte, sin línea de tendencia, y el corte 2026-T1 como parcial |
| Comparación interanual 2025 vs 2026 | Descartada | Ningún mes de telefonía se repite entre años |
| Proyección de la base diaria | Descartada | La guía la prohíbe; la base diaria solo verifica la estimación mensual |
| Encuestas de satisfacción, residentes, aeropuerto y Tikal | Descartadas | No corresponden a Atitlán según la guía de uso |
| Encuesta en fronteras y boletines | Incluidos | Fuentes opcionales que sí aportan evidencia sobre el lago (alojamiento declarado, noches por residencia) |

# 6. Observatorios de referencia: INSTO y SEGITTUR

## 6.1 INSTO (ONU Turismo)

La Red Internacional de Observatorios de Turismo Sostenible (INSTO) de ONU Turismo se creó en 2004 para apoyar la mejora continua de la sostenibilidad y la resiliencia del sector, conectando destinos que se comprometen a monitorear con regularidad los impactos económicos, ambientales y sociales del turismo. INSTO no impone indicadores: define áreas temáticas que cada observatorio debe medir, al menos en parte, durante sus primeros tres años. Su marco lista once áreas obligatorias: estacionalidad, empleo, beneficios económicos para el destino, gobernanza, satisfacción local, accesibilidad, gestión de la energía, del agua, de las aguas residuales y de los residuos sólidos, y acción climática (en el mismo documento todavía se menciona una versión anterior de nueve áreas). Los miembros entregan un informe anual con el perfil del destino, sus indicadores y un análisis diagnóstico; quien no reporta dos años seguidos pierde la membresía.

## 6.2 SEGITTUR y los Destinos Turísticos Inteligentes

SEGITTUR es la sociedad estatal española que gestiona la innovación y la tecnología turística, como medio propio de la Secretaría de Estado de Turismo. Lidera el modelo de Destinos Turísticos Inteligentes (DTI), que se apoya en cinco ejes: gobernanza, innovación, tecnología, sostenibilidad y accesibilidad. El modelo se formalizó en la norma UNE 178501 (sistema de gestión de los destinos turísticos inteligentes), publicada en 2016 y revisada en 2018. La Red DTI reúne a los destinos que aplican la metodología: en octubre de 2024 sumaba 681 miembros, entre destinos, instituciones, empresas y observadores. SEGITTUR impulsa además una Plataforma Inteligente de Destino para integrar los datos de cada destino.

## 6.3 Qué toma este observatorio de cada uno

| Práctica | Origen | Cómo se aplica aquí |
|:---------|:-------|:--------------------|
| Monitoreo continuo con un mismo método | INSTO | ETL reproducible y tablero que se actualiza al cambiar los archivos |
| Áreas temáticas antes que indicadores fijos | INSTO | Cuatro módulos (demanda, temporalidad, oferta, territorio); la estacionalidad es un área INSTO |
| Informe periódico con diagnóstico | INSTO | Página de Conclusiones y esta memoria, generadas con las cifras vigentes |
| Gobernanza del dato | SEGITTUR | Cláusula de confidencialidad, datos montados en solo lectura, controles de calidad y huella de cada archivo |
| Tecnología abierta e integrable | SEGITTUR | Python, Streamlit, Plotly y Docker, todos de código abierto |
| Accesibilidad | SEGITTUR e INSTO | Paleta con contraste 3:1, segunda señal para daltonismo y diseño responsivo |

**Brechas frente a ambos modelos:** el observatorio todavía no mide satisfacción local, empleo ni las áreas ambientales que INSTO exige, y no integra datos en tiempo real como propone la Plataforma Inteligente de Destino. Son los siguientes pasos naturales si el INGUAT quisiera postular el lago a la red INSTO.

# 7. Decisiones de tecnología y diseño

## 7.1 Por qué Streamlit, Plotly y Docker

| Necesidad | Decisión | Por qué | Alternativa descartada |
|:----------|:---------|:--------|:-----------------------|
| Un solo lenguaje del dato al tablero | **Streamlit** (Python) | El análisis ya estaba en pandas; la interfaz reutiliza las mismas funciones sin traducirlas. Las gráficas enlazadas salen de `on_select` sin escribir JavaScript. Trae su propio probador (`AppTest`), con el que se prueba que cada página y cada interacción corren sin errores. | Dash (más código de callbacks); Power BI o Tableau (licencias, no son de código abierto) |
| Gráficas interactivas | **Plotly** | Información al pasar el cursor, selección de puntos para filtrar otras gráficas y exportación a PNG. Las mismas figuras se usan en esta memoria. | matplotlib (estático, sin selección) |
| Despliegue repetible | **Docker** | Mismas versiones en cualquier equipo (Python 3.13 y dependencias fijas). Los datos reales se montan en solo lectura y nunca entran a la imagen; el puerto solo se publica en 127.0.0.1. | Instalación manual (cada equipo con versiones distintas) |

## 7.2 Paleta y teoría del color

La paleta sigue tres reglas. **Tono para categorías y luminosidad para magnitudes:** orígenes, segmentos y clases usan tonos distintos; los mapas de calor usan un solo azul de claro a oscuro, porque el ojo ordena la luminosidad sin leyenda. **Contraste suficiente:** todo color de dato llega al menos a 3:1 contra el fondo blanco (WCAG 2.2, criterio 1.4.11); turista, excursionista y festividad se oscurecieron en el espacio OKLab lo justo para lograrlo sin cambiar su tono. **Nunca solo el color** (criterio 1.4.1): al simular daltonismo (modelo de Machado et al., 2009) el par turista y excursionista casi se confunde con deuteranopia (distancia OKLab de 5 sobre 100) y el par hub y visita corta con protanopia (7); por eso el excursionista lleva trama de puntos y cada clase tiene forma y trazo propios.

<<tabla_paleta>>

El tema es claro y fijo: los contrastes se midieron sobre superficies claras y el tablero no ofrece modo oscuro, para que ninguna gráfica pierda legibilidad.

## 7.3 Interacción y pantallas pequeñas

- **Cuatro gráficas enlazadas** (la guía pide tres): municipios en el módulo 1 (filtra KPIs, segmentación, top 10 y estadía por nacionalidad), Lift en el 2 (resalta la festividad en la serie diaria), capacidad anual en el 3 (enfoca la ocupación en el año) y cuadrante en el 4 (abre el perfil del municipio y lo marca en la matriz).
- **Indicador de cobertura** en Inicio y Calidad: qué fuentes respaldan cada mes, con los meses estimados recuadrados en violeta. Todas llevan la misma pista "Clic para filtrar" y las gráficas que reciben el filtro muestran el chip "Filtrado por".
- **Barra de Plotly uniforme:** solo "descargar PNG"; sin zoom, paneo ni lazo. La única gráfica con acercamiento es la serie diaria, con su barra inferior.
- **Sin descarga de tablas:** se desactivó la exportación CSV de Streamlit (`client.disableDataExport`), aunque las tablas solo muestran agregados.
- **Responsivo:** se probó a 375 px (celular) y 768 px (tableta) sin desplazamiento horizontal; los encabezados y mosaicos se reorganizan y la barra de Plotly se oculta en pantallas táctiles.
- **Historia:** cada módulo termina con una frase que lleva al siguiente y la página de Conclusiones une los cuatro.

# Anexo A. Estructura del repositorio

```text
<<arbol>>
```

# Anexo B. requirements.txt

```text
<<requirements>>
```

# Anexo C. Fragmentos de código clave

**Estadía media ponderada** (`src/indicadores.py`): nunca se promedia `permanencia_prom`.

```python
<<codigo_estadia>>
```

**Lift de festividades** (`src/indicadores.py`), simple y ajustado por día de la semana.

```python
<<codigo_lift>>
```

**Índice de especialización extranjera** (`src/indicadores.py`): sustituye a extranjeros / total.

```python
<<codigo_iee>>
```

**Captación formal en la ventana coincidente** (`src/oferta.py`).

```python
<<codigo_cruce>>
```

**Estimación de los meses sin telefonía** (`src/pronostico.py`).

```python
<<codigo_predecir>>
```

**Regla del cuadrante y nombres de k-medias** (`src/territorio.py`).

```python
<<codigo_regla>>

<<codigo_nombrar>>
```

**Reproceso automático al cambiar los datos** (`src/etl.py`).

```python
<<codigo_vigente>>
```

# Anexo D. Instalación en un servidor desde cero

Probado como guía para Ubuntu Server 24.04 LTS. El servidor necesita acceso al repositorio privado (llave SSH de despliegue).

1. Instalar Git y Docker Engine con el plugin de Compose (guía oficial de Docker, repositorio apt):

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER    # cerrar sesión y volver a entrar
```

2. Clonar el repositorio y crear la carpeta de datos fuera de él, con permisos restringidos:

```bash
sudo git clone git@github.com:Isabella1911/DS-Proyecto-3.git /opt/observatorio
sudo mkdir -p /srv/observatorio/datos && sudo chmod 750 /srv/observatorio/datos
# copiar las bases con su nombre original (incluidos los boletines PDF y BD_COMPLEMENTARIA), por ejemplo con scp desde un equipo autorizado
```

3. Construir y levantar el tablero con los datos montados en solo lectura:

```bash
cd /opt/observatorio
DATOS_DIR=/srv/observatorio/datos docker compose up -d --build
docker compose ps
curl -s http://127.0.0.1:8501/_stcore/health    # responde "ok"
```

4. Acceso. El puerto solo escucha en 127.0.0.1. Para consultarlo desde otro equipo se usa un túnel SSH (`ssh -L 8501:localhost:8501 usuario@servidor` y abrir `http://localhost:8501`) o un proxy inverso con TLS y autenticación (por ejemplo nginx).

5. Actualizar el código o los datos:

```bash
cd /opt/observatorio && git pull && DATOS_DIR=/srv/observatorio/datos docker compose up -d --build
```

Sin Docker: `python3.13 -m venv .venv`, `.venv/bin/pip install -r requirements.txt` y `OBS_DATOS=/srv/observatorio/datos .venv/bin/streamlit run app.py`.

# Anexo E. Revisión con las bases reales y regeneración de esta memoria

Quien tenga las bases reales las coloca en `data/raw/` (o indica la carpeta con `OBS_DATOS`) y corre:

```bash
python scripts/revisar_datos.py            # controles, cobertura y cifras de las lecturas; marca [REVISAR]
python scripts/revisar_datos.py --esquema  # solo columnas, tipos y filas de cada archivo
python scripts/generar_memoria.py          # vuelve a generar esta memoria con las cifras reales (requiere pandoc)
```

La salida de ambos scripts es solo agregada; nunca imprime filas de las bases.

# Referencias

- INGUAT (2026). *Guía de uso de los datos. Tableros por destino* (documento del curso) y boletines anuales de ocupación hotelera 2023, 2024 y 2025.

- ONU Turismo. *About the International Network of Sustainable Tourism Observatories (INSTO)*. <https://www.untourism.int/sustainable-development/about-insto>
- ONU Turismo. *INSTO Framework*. <https://www.untourism.int/sustainable-development/into-framework>
- ONU Turismo. *FAQs about INSTO*. <https://www.untourism.int/sustainable-development/insto-faq>
- SEGITTUR. *Destinos Turísticos Inteligentes*. <https://www.segittur.es/destinos-turisticos-inteligentes/proyectos-destinos/destinos-turisticos-inteligentes/>
- SEGITTUR (2024). *Manual de gestión de la metodología DTI*. <https://www.destinosinteligentes.es/wp-content/uploads/2024/05/Manual-Gestion-Metodologia-DTI_Junio-2024.pdf>
- UNE (2022). *Nota de prensa: normas UNE para destinos turísticos inteligentes*. <https://www.une.org/salainformaciondocumentos/220928_UNE-SEGITTUR_NP_Destinos-Turisticos_Inteligentes.pdf>
- esmartcity (2024, 15 de octubre). *La Red de Destinos Turísticos Inteligentes aprueba la adhesión de 62 miembros titulares*. <https://www.esmartcity.es/2024/10/15/red-destinos-turisticos-inteligentes-aprueba-adhesion-62-miembros-titulares>
- W3C (2023). *Web Content Accessibility Guidelines (WCAG) 2.2*. <https://www.w3.org/TR/WCAG22/>
- Machado, G. M., Oliveira, M. M. y Fernandes, L. A. F. (2009). A physiologically-based model for simulation of color vision deficiency. *IEEE Transactions on Visualization and Computer Graphics*, 15(6), 1291-1298.
- Ottosson, B. (2020). *A perceptual color space for image processing (OKLab)*. <https://bottosson.github.io/posts/oklab/>
- Streamlit. *Documentación*. <https://docs.streamlit.io>
- Plotly. *Plotly Python Graphing Library*. <https://plotly.com/python/>
- Docker. *Install Docker Engine on Ubuntu*. <https://docs.docker.com/engine/install/ubuntu/>
