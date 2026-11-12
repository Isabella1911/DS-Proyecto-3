<<aviso_datos>>

# Resumen ejecutivo

**El reto.** El Lago de Atitlán no es un destino único: es una red de diez municipios ribereños que reciben visitantes muy distintos. Algunos son puerta de entrada, otros retienen estancias largas de extranjeros y otros viven de excursiones de fin de semana. El reto del grupo fue caracterizar esa red con las bases del observatorio y traducirla en decisiones para el INGUAT: dónde reforzar la gestión de flujo, dónde promover estancias y qué datos faltan para medir mejor.

**Hallazgos principales** (<<periodo>>, <<meses>> meses con telefonía):

1. **<<titulo_h1>>** <<hub_lista>> recibe <<hub_vis>> visitantes por mes en promedio y sus turistas se quedan <<hub_est>> días. En <<larga_lista>> la estancia media sube a <<larga_est>> días con <<larga_ext>> de extranjeros.
2. **Los picos los marcan las festividades y los fines de semana.** <<evento_top>> eleva la afluencia <<lift_top>> frente a un día regular (<<lift_aj_top>> si se compara con el mismo día de la semana) y los sábados y domingos reciben <<presion>> veces los visitantes de un día hábil.
3. **<<titulo_h3>>** En la ventana <<ventana>>, las noches que pasan los turistas del lago equivalen al <<tasa_impl>> de las plazas-noche formales de Sololá, con una ocupación oficial de <<ocup_ofi>>. <<cierre_h3>>
4. **<<titulo_h4>>** Un mercado pequeño de estancia larga puede generar tantas noches como uno masivo de visita corta.

**Estimación de enero y febrero de 2026.** La telefonía no cubre esos meses. Con el factor de reparto sobre la base de migración se estiman **<<est_m1>>** y **<<est_m2>>** visitantes (suma de municipios). El método elegido es el <<metodo>> (<<metodo_nombre>>), que tuvo el menor error al validar dejando un mes fuera: MAPE de <<mape_sel>> (el otro método: <<mape_otro>>). Las estimaciones se rotulan siempre como *Estimación* y no se mezclan con lo observado.

![Visitantes por mes (suma de municipios): observado en negro y Estimación en violeta.](<<fig_estimacion>>){width=95%}

# 1. Arquitectura y modelo de datos

## 1.1 Las cinco fuentes

| Fuente | Archivo y hoja | Granularidad | Columnas que se usan | Uso |
|:-------|:---------------|:-------------|:---------------------|:----|
| Migración | `Base_Migracion_2009-2026jun.xlsx`, hoja *Datos* | Mes x país x vía x tipo de viajero (nacional) | `Año`, `Mes cod`, `Tipo de Viajero`, `Viajero` | Llegadas internacionales para estimar ene-feb 2026 (módulo 2) |
| Movilidad mensual | `BD_movilidad_mensual.xlsx`, hoja *Atitlan* | Municipio x mes x país x segmento | `destino`, `anio`, `mes`, `pais`, `es_consecutivo`, `visitantes`, `dias_persona`, `permanencia_prom` | Demanda, estadía, mercados (módulos 1, 3 y 4) |
| Movilidad diaria | `BD_movilidad_diaria.xlsx`, hoja *Atitlan* | Municipio x día x país | `destino`, `idfecha`, `pais`, `evento`, `cantidad_visitantes`, `dia_semana` | Festividades, patrón semanal (módulos 2 y 4) |
| Ocupación | `indice_ocupacion_mensual_2023_2025_1.csv` | Departamento x mes | `anio`, `mes`, `departamento`, `indice_ocupacion` | Ocupación hotelera (módulo 3) |
| Oferta | `oferta_hotelera_2022_2026.csv` | Departamento x corte (año y trimestre) x tipo | `anio`, `trimestre`, `departamento`, `tipo_alojamiento`, `establecimientos`, `habitaciones`, `plazas_cama` | Capacidad instalada (módulo 3) |

## 1.2 Cómo se relacionan

Las bases no comparten un identificador único; se unen por llaves de tiempo y territorio, siempre después de normalizarlas:

- **Periodo (año y mes)** une la movilidad mensual con la migración (factor de reparto) y con la ocupación (ventana coincidente).
- **Municipio** une la movilidad mensual con la diaria: el perfil de cada pueblo combina volumen y estadía (mensual) con presión de fin de semana y festividades (diaria).
- **Departamento y año** unen la ocupación con la oferta: las plazas cama del corte del año dan las plazas-noche del mes.
- La movilidad diaria **nunca se suma** para obtener el mes: mide presencia por día y la misma persona aparece en cada día que pasa en el destino.

![Flujo de datos y relaciones entre las cinco bases](<<fig_arquitectura>>){width=100%}

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

¿Qué papel juega cada pueblo del lago? Se construye un perfil por municipio con seis variables: visitantes promedio por mes, estadía media ponderada, porcentaje de extranjeros y de excursionistas (base mensual), y presión de fin de semana y Lift máximo de festividad (base diaria). Las variables se eligieron porque cada una responde a una decisión distinta: el volumen a la gestión de flujo, la estadía y el origen a la promoción, y la presión de fin de semana a la planificación de servicios.

## 3.2 Regla del cuadrante

Es la clasificación principal porque se puede explicar en una frase y repetir cada mes:

- **Hub comercial:** volumen de al menos el 60 % del municipio con más visitantes (hoy, <<umbral_hub>> visitantes por mes).
- **Larga estancia:** estadía igual o mayor que la mediana del lago (<<mediana_estadia>> días) y mayoría extranjera (50 % o más).
- **Visita corta:** el resto.

El cuadrante del módulo 4 dibuja el volumen (escala logarítmica) contra la estadía, con el tamaño según el porcentaje de extranjeros y las medianas del lago como líneas de referencia.

## 3.3 k-medias como contraste

k-medias agrupa a los municipios por parecido, sin reglas fijas. Se usa como contraste de la regla y no como clasificación independiente, por tres razones: con diez municipios cada uno pesa mucho, el algoritmo siempre devuelve los grupos que se le piden aunque no existan, y sus grupos no tienen nombre propio.

- **Variables:** $\log_{10}$ del volumen (la distribución es muy asimétrica: sin el logaritmo el hub dominaría la distancia), estadía media, porcentaje de extranjeros y presión de fin de semana.
- **Escala:** cada variable se estandariza (media 0, desviación 1) para que ninguna pese más por su unidad. Es una decisión de negocio: las cuatro dimensiones importan lo mismo para el INGUAT.
- **Ajuste:** $k = 3$, 50 inicios aleatorios con semilla 42 y se conserva la partición de menor inercia. Implementado con numpy, sin dependencias nuevas.
- **Nombres:** el grupo con mayor volumen es el hub; de los otros dos, el de mayor estadía es larga estancia y el restante visita corta.
- **Estabilidad:** se quita un municipio a la vez, se vuelve a agrupar y se cuenta cuántos de los demás conservan su clase. Hoy la estabilidad es <<estabilidad>>.

## 3.4 Resultados

<<tabla_municipios>>

Regla y k-medias coinciden en **<<coinciden>> de <<n>>** municipios<<difieren_texto>>.

<<tabla_clases>>

![Cuadrante de los municipios (regla del cuadrante). Color y forma: clase; tamaño: porcentaje de extranjeros.](<<fig_cuadrante>>){width=95%}

## 3.5 Validación con la dinámica diaria

Si la clasificación es correcta, los pueblos de visita corta deberían depender más del fin de semana que los de larga estancia. Con los datos actuales la presión de fin de semana es <<presion_corta>> en visita corta y <<presion_larga>> en larga estancia: <<validacion_texto>>

## 3.6 Qué se puede afirmar y qué no

- La tipología **describe** cómo se comporta cada pueblo; no explica por qué. Decir que un pueblo es de visita corta "porque" está cerca de Panajachel sería una hipótesis, no un resultado.
- Los volúmenes de una clase son **suma de municipios**: un visitante que recorre varios pueblos cuenta en cada uno. Por eso se comparan promedios simples por municipio e índices, nunca totales.
- La clasificación se recalcula sola con datos nuevos; conviene revisarla cada trimestre para ver si algún pueblo cambia de papel.

# 4. Supuestos y limitaciones

1. **Solo datos de Sololá.** Se usan los registros de los diez municipios del lago. Otros destinos que aparezcan en las bases se reportan en *Calidad de los datos* y se excluyen. La ocupación y la oferta son departamentales: no hay capacidad por municipio.
2. **Sin comparación 2025 contra 2026.** La telefonía no cubre enero ni febrero de ningún año. Esos meses se estiman y no hay un mismo mes observado en dos años, así que no se puede medir el crecimiento interanual.
3. **Hotelería formal y plataformas digitales son universos distintos.** La oferta y la ocupación cubren establecimientos registrados; las noches en Airbnb o casas de familia no están ahí. La tasa implícita no suma ambos universos: solo compara la demanda medida por telefonía con la capacidad formal.
4. **Encuestas sin factor de expansión.** Las encuestas disponibles no traen factor de expansión, así que no representan al total de visitantes. No se usaron en el tablero; incorporarlas exigiría ese factor.
5. **Nacionales con factor de expansión.** El conteo de nacionales de la telefonía ya viene expandido y no es comparable en la misma escala que el de extranjeros: se reportan por separado.
6. **Estimación.** El factor de reparto supone que la fracción de llegadas internacionales que llega al lago es estable entre meses. Para los nacionales el supuesto es más débil porque no pasan por migración.
7. **Corte de oferta 2026 parcial.** Es del primer trimestre y repite valores del año previo en buena parte de las combinaciones; no entra al cálculo de crecimiento.
8. **Fuentes opcionales no integradas.** La BD complementaria y los boletines de ocupación en PDF no se incorporaron porque no estaban disponibles para el equipo en el formato de trabajo.
9. **Datos sintéticos en el repositorio.** Por la cláusula de confidencialidad, el repositorio y la imagen de Docker solo contienen datos sintéticos con la misma estructura. Las cifras de esta memoria corresponden a los datos indicados en la primera página.

# 5. Recomendaciones para el INGUAT

1. **Gestión de flujo en picos.** Reforzar transporte lacustre, seguridad y servicios en <<evento_top>> y los fines de semana, con prioridad en los pueblos de visita corta (<<corta_lista>>), donde la presión de fin de semana es <<presion_corta>>.
2. **Promoción de estancias largas.** Dirigir la promoción internacional a <<mercado_estadia>> y mercados parecidos, con producto en <<larga_lista>>, donde cada turista se queda <<larga_est>> días.
3. **Medir el alojamiento no formal.** Acordar con las plataformas digitales un registro de noches por municipio para cerrar la brecha entre la demanda medida y la capacidad formal.
4. **Cerrar el hueco de telefonía.** Pedir al proveedor la cobertura de enero y febrero: sin ella la temporada de esos meses solo se estima y no se puede comparar 2025 contra 2026.
5. **Monitoreo continuo.** Actualizar el tablero cada mes con el mismo ETL, revisar la página de Calidad antes de publicar y reportar los indicadores con la periodicidad que exige INSTO.

**Datos nuevos que convendría incorporar:** la BD complementaria y los boletines de ocupación (fuentes opcionales de la asignación); la oferta y la ocupación por municipio; un registro de plataformas digitales; encuestas con factor de expansión (gasto y motivo de viaje) para pasar de visitantes a impacto económico; conteos del transporte lacustre entre pueblos; e indicadores ambientales (agua, residuos) que INSTO considera obligatorios.

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

- **Cuatro gráficas enlazadas** (la guía pide tres): municipios en el módulo 1, Lift en el 2, capacidad anual en el 3 y cuadrante en el 4. Todas llevan la misma pista "Clic para filtrar" y las gráficas que reciben el filtro muestran el chip "Filtrado por".
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
# copiar las 5 bases con su nombre original, por ejemplo con scp desde un equipo autorizado
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
