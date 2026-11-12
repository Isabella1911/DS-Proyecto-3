## Módulo 1. Demanda y mercados emisores

### I-01 Visitantes promedio por mes

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Visitantes promedio por mes |
| Definición | Promedio, entre los meses con dato, de los visitantes únicos del mes en el ámbito elegido. |
| Fórmula | $\frac{1}{T}\sum_{t}\sum_{p,s} V_{t,p,s}$, con $T$ = meses observados |
| Código pandas | `m.groupby("periodo")["visitantes"].sum().mean()` |
| Granularidad | Mes; municipio o suma de municipios; origen opcional |
| Unidad | Visitantes por mes |
| Archivo / hoja / columnas | `BD_moviidad_mensual.xlsx` / *Atitlan* / `destino`, `anio`, `mes`, `visitantes` |
| Reglas | Un mes sin dato es "Sin dato", nunca 0. Con varios municipios se rotula "suma de municipios" (cota superior: un visitante cuenta en cada pueblo que visita). La base diaria no se usa para este indicador. |

### I-02 Días-persona promedio por mes

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Días-persona promedio por mes |
| Definición | Promedio mensual de los días que pasan los visitantes en el destino (todos los segmentos). |
| Fórmula | $\frac{1}{T}\sum_{t}\sum_{p,s} DP_{t,p,s}$ |
| Código pandas | `m.groupby("periodo")["dias_persona"].sum().mean()` |
| Granularidad | Mes; municipio o suma de municipios |
| Unidad | Días-persona por mes |
| Archivo / hoja / columnas | `BD_moviidad_mensual.xlsx` / *Atitlan* / `dias_persona` |
| Reglas | Los excursionistas aportan 1 día por visitante. El ETL marca como error las filas con días-persona menores que visitantes. |

### I-03 Estadía media ponderada

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Estadía media ponderada |
| Definición | Días promedio que se queda un turista con pernocta. |
| Fórmula | $\dfrac{\sum DP_{s=\text{mayor a 1}}}{\sum V_{s=\text{mayor a 1}}}$ |
| Código pandas | `t = m[m["segmento"] == SEG_TURISTA]; t["dias_persona"].sum() / t["visitantes"].sum()` |
| Granularidad | Ámbito y periodo elegidos; también por mes, municipio y nacionalidad |
| Unidad | Días |
| Archivo / hoja / columnas | `BD_moviidad_mensual.xlsx` / *Atitlan* / `es_consecutivo`, `visitantes`, `dias_persona` |
| Reglas | Nunca se promedia `permanencia_prom` (daría el mismo peso a un mercado de 2 personas que a uno de 2 000); esa columna solo se usa para verificar. Excluye excursionistas. |

### I-04 Porcentaje de turistas con pernocta

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Porcentaje de turistas con pernocta (segmentación turista / excursionista) |
| Definición | Proporción de los visitantes que pasa más de un día en el destino. |
| Fórmula | $\dfrac{\sum V_{s=\text{mayor a 1}}}{\sum V}$; excursionistas $= 1 -$ turistas |
| Código pandas | `m.loc[m["segmento"] == SEG_TURISTA, "visitantes"].sum() / m["visitantes"].sum()` |
| Granularidad | Mes (gráfica) y periodo (indicador) |
| Unidad | Porcentaje |
| Archivo / hoja / columnas | `BD_moviidad_mensual.xlsx` / *Atitlan* / `es_consecutivo`, `visitantes` |
| Reglas | `es_consecutivo` "mayor a 1" = turista, "menor a 1" = excursionista (menos de 24 h). Valores no reconocidos van al reporte de calidad. Barras de personas y línea de porcentaje en ejes separados. |

### I-05 Visitantes extranjeros por mes e índice de especialización extranjera (IEE)

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Visitantes extranjeros por mes; índice de especialización extranjera (IEE) |
| Definición | Cuántos extranjeros recibe el ámbito por mes (reportado aparte de los nacionales) y, por municipio, si atrae proporcionalmente más extranjeros que el lago en conjunto. Sirve para orientar la promoción internacional por pueblo. |
| Fórmula | $\overline{E} = \frac{1}{T}\sum_t E_t$; $\ \text{IEE}_i = \dfrac{E_i / \sum_j E_j}{N_i / \sum_j N_j}$ ($E$ extranjeros, $N$ nacionales, $j$ municipios) |
| Código pandas | `ind.kpis_demanda(m)["extranjeros_mes"]`; `ind.especializacion_extranjera(m)` (pivot municipio x origen, `cuota = t / t.sum()`, `cuota["Extranjero"] / cuota["Nacional"]`) |
| Granularidad | Dato: municipio-mes-país. Cálculo: ámbito-periodo (volumen) y municipio (IEE) |
| Unidad | Personas por mes; índice (lago = 1) |
| Archivo / hoja / columnas | `BD_moviidad_mensual.xlsx` / *Atitlan* / `destino`, `pais`, `visitantes` |
| Reglas | **Nunca** se calcula extranjeros / total (error listado en la guía de uso): los nacionales traen factor de expansión. El IEE compara cuotas dentro de cada origen, por lo que un factor de expansión constante se cancela; ordena a los municipios igual que la proporción de la fuente, sin afirmar una participación real. |

### I-06 Participación de los mercados emisores extranjeros

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Top 10 de mercados emisores extranjeros |
| Definición | Los diez países extranjeros con más visitantes y su participación sobre el total de extranjeros. |
| Fórmula | $\dfrac{\sum V_{p}}{\sum_{p'\in \text{ext}} V_{p'}}$ |
| Código pandas | `ext = m[m["origen"] == "Extranjero"]; v = ext.groupby("pais")["visitantes"].sum(); v.nlargest(10) / v.sum()` |
| Granularidad | País; ámbito y periodo elegidos |
| Unidad | Visitantes y porcentaje |
| Archivo / hoja / columnas | `BD_moviidad_mensual.xlsx` / *Atitlan* / `pais`, `visitantes` |
| Reglas | Los nacionales se reportan aparte (factor de expansión). Los países se normalizan (mayúsculas, tildes, alias como EEUU o USA). |

### I-07 Estadía media por nacionalidad

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Estadía media por nacionalidad |
| Definición | Estadía media ponderada (I-03) de cada uno de los diez principales mercados extranjeros, frente a la de los nacionales y al promedio. |
| Fórmula | $\dfrac{\sum DP_{p,s=\text{mayor a 1}}}{\sum V_{p,s=\text{mayor a 1}}}$ |
| Código pandas | `ind.top_paises(m, 10)["estadia_media"]` |
| Granularidad | País |
| Unidad | Días |
| Archivo / hoja / columnas | `BD_moviidad_mensual.xlsx` / *Atitlan* / `pais`, `es_consecutivo`, `visitantes`, `dias_persona` |
| Reglas | Las mismas que I-03. Visualización adicional del grupo. |

## Módulo 2. Dinámica temporal y pronóstico

### I-08 Lift de festividad

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Lift de festividad (simple) |
| Definición | Cuánto sube la presencia diaria en los días de una festividad frente a un día regular. |
| Fórmula | $\dfrac{\overline{V}_{d\,\in\,\text{evento}}}{\overline{V}_{d\,\in\,\text{regular}}} - 1$ |
| Código pandas | `s = ind.serie_diaria(d); s[s["evento"] == e]["visitantes"].mean() / s[s["evento"] == "Regular"]["visitantes"].mean() - 1` |
| Granularidad | Festividad; ámbito y origen elegidos |
| Unidad | Porcentaje |
| Archivo / hoja / columnas | `BD_moviidad_diario.xlsx` / *Atitlan* / `idfecha`, `evento`, `cantidad_visitantes` |
| Reglas | Promedios por día, nunca sumas. Los días sin cobertura no cuentan como 0. "Regular", "Normal" o vacío se normalizan como día regular. |

### I-09 Lift ajustado por día de la semana

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Lift ajustado por día de la semana |
| Definición | Lift en el que cada día de festividad se compara con el día regular promedio del mismo día de la semana. |
| Fórmula | $\frac{1}{n}\sum_{d\,\in\,\text{evento}} \dfrac{V_d}{\overline{V}_{\text{regular},\,\text{dds}(d)}} - 1$ |
| Código pandas | `(ev["visitantes"] / ev["dia_semana"].map(base_dia)).mean() - 1`, con `base_dia = reg.groupby("dia_semana")["visitantes"].mean()` |
| Granularidad | Festividad |
| Unidad | Porcentaje |
| Archivo / hoja / columnas | `BD_moviidad_diario.xlsx` / *Atitlan* / `idfecha`, `evento`, `cantidad_visitantes` |
| Reglas | Evita atribuir al feriado el efecto de caer en sábado o domingo. El día de la semana se recalcula desde la fecha; si difiere de `dia_semana` se reporta en calidad. |

### I-10 Índice del patrón semanal

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Índice del patrón semanal |
| Definición | Visitantes promedio de cada día de la semana frente al promedio de los siete días. |
| Fórmula | $100 \cdot \overline{V}_{\text{dds}} \,/\, \frac{1}{7}\sum_{\text{dds}} \overline{V}_{\text{dds}}$ |
| Código pandas | `p = reg.groupby("dia_semana")["visitantes"].mean(); p / p.mean() * 100` |
| Granularidad | Día de la semana; ámbito o municipio |
| Unidad | Índice (promedio = 100) |
| Archivo / hoja / columnas | `BD_moviidad_diario.xlsx` / *Atitlan* / `idfecha`, `evento`, `cantidad_visitantes` |
| Reglas | Por defecto solo días regulares, para que un feriado no infle el día en que cayó. |

### I-11 Presión de fin de semana

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Presión de fin de semana |
| Definición | Cuántas veces recibe un sábado o domingo los visitantes de un día hábil. |
| Fórmula | $\overline{V}_{\text{sáb, dom}} \,/\, \overline{V}_{\text{lun a vie}}$ |
| Código pandas | `ind.presion_fin_de_semana(ind.patron_semanal(ind.serie_diaria(d)))` |
| Granularidad | Ámbito; por municipio y por clase en el módulo 4 |
| Unidad | Veces (razón) |
| Archivo / hoja / columnas | `BD_moviidad_diario.xlsx` / *Atitlan* / `idfecha`, `evento`, `cantidad_visitantes` |
| Reglas | Solo días regulares. Variable de k-medias en el módulo 4. |

### I-12 Estimación de visitantes de enero y febrero de 2026

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Estimación de los meses sin cobertura de telefonía |
| Definición | Visitantes únicos estimados para los meses que la telefonía no cubre, con la base de migración. |
| Fórmula | A: $F = \dfrac{\sum_{\text{obs}} D_t}{\sum_{\text{obs}} M_t}$, $\hat D_t = F\,M_t$. B: $S_m = \overline{M_{a,m}/\overline{M}_a}$, $L = \dfrac{\sum_{\text{obs}} D_t}{\sum_{\text{obs}} S_{m(t)}}$, $\hat D_t = L\,S_{m(t)}$ |
| Código pandas | `pr.estimar(obs, mig, ["2026-01", "2026-02"], [2023, 2024, 2025], metodo)` |
| Granularidad | Mes; ámbito y origen elegidos |
| Unidad | Visitantes por mes |
| Archivo / hoja / columnas | Destino: `BD_moviidad_mensual.xlsx` (`visitantes`). Migración: `Base_Migracion_2009-2026jun.xlsx` / *Datos* / `Año`, `Mes cod`, `Tipo de Viajero`, `Viajero` |
| Reglas | $M_t$ = turistas + excursionistas internacionales del mes. Se muestra siempre en violeta, con línea discontinua y rotulada "Estimación"; nunca entra en los indicadores observados. Por defecto se elige el método con menor MAPE. |

### I-13 Error de validación de la estimación

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | MAPE, MAE y RMSE |
| Definición | Error de estimar cada mes observado sin usarlo para calcular el factor (validación dejando uno fuera). |
| Fórmula | $\text{MAPE} = \frac{100}{n}\sum \frac{\lvert \hat D_t - D_t\rvert}{D_t}$; $\text{MAE} = \frac{1}{n}\sum \lvert \hat D_t - D_t\rvert$; $\text{RMSE} = \sqrt{\frac{1}{n}\sum (\hat D_t - D_t)^2}$ |
| Código pandas | `err = val["estimado"] - val["observado"]; (err.abs() / val["observado"]).mean() * 100` |
| Granularidad | Método y ámbito |
| Unidad | Porcentaje (MAPE); visitantes (MAE, RMSE) |
| Archivo / hoja / columnas | Las mismas que I-12 |
| Reglas | Si el MAPE supera 20 %, el tablero pide presentar la estimación como orden de magnitud. |

### I-14 Perfil estacional de las llegadas internacionales

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Perfil estacional de migración |
| Definición | Llegadas de cada mes frente al promedio de su año, promediado entre los años del perfil. |
| Fórmula | $S_m = \frac{1}{A}\sum_{a} M_{a,m} \,/\, \overline{M}_a$ |
| Código pandas | `b = mig[mig["anio"].isin(anios)]; (b["llegadas"] / b.groupby("anio")["llegadas"].transform("mean")).groupby(b["mes"]).mean()` |
| Granularidad | Mes del año |
| Unidad | Índice (1 = mes promedio) |
| Archivo / hoja / columnas | `Base_Migracion_2009-2026jun.xlsx` / *Datos* / `Año`, `Mes cod`, `Tipo de Viajero`, `Viajero` |
| Reglas | Años del perfil en `config.yaml` (2023 a 2025). Visualización adicional del grupo. |

### I-14b Rotación mensual (verificación con la base diaria)

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Rotación mensual y presencia diaria implícita en la estimación |
| Definición | Visitantes únicos del mes por cada persona presente en un día promedio. Si es estable, permite verificar que la estimación de ene–feb 2026 tenga una forma diaria plausible. |
| Fórmula | $R_t = V^{\text{mensual}}_t / \overline{P}^{\text{diaria}}_t$; presencia implícita $= \hat D_t / \overline R$ |
| Código pandas | `pr.consistencia_diaria(obs, ind.serie_diaria(d), r.estimados)` |
| Granularidad | Ámbito-mes (solo meses con base diaria completa, ≥ 28 días) |
| Unidad | Ratio; personas presentes por día |
| Archivo / hoja / columnas | Movilidad mensual (`visitantes`) y diaria (`idfecha`, `cantidad_visitantes`) |
| Reglas | La base diaria se promedia, nunca se suma ni se proyecta. Los feriados de meses sin cobertura se declaran ausentes. |

## Módulo 3. Oferta hotelera

### I-15 Capacidad instalada

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Capacidad instalada (establecimientos, habitaciones, plazas cama) y su crecimiento |
| Definición | Inventario de alojamiento formal de Sololá al cierre de cada año. |
| Fórmula | $C_a = \sum_{\text{tipo}} C_{a,\text{T4},\text{tipo}}$; crecimiento $= C_{a_1}/C_{a_0} - 1$ |
| Código pandas | `anual = of.capacidad_anual(of.capacidad(oferta, "Sololá")); anual["plazas_cama"].iloc[-1] / anual["plazas_cama"].iloc[0] - 1` |
| Granularidad | Año (corte del cuarto trimestre) y tipo de alojamiento |
| Unidad | Establecimientos, habitaciones o plazas cama |
| Archivo / hoja / columnas | `oferta_hotelera_2022_2026.csv` / `anio`, `trimestre`, `departamento`, `tipo_alojamiento`, `establecimientos`, `habitaciones`, `plazas_cama` |
| Reglas | El corte 2026-T1 es parcial (repite valores del año previo): se dibuja con trama y no entra al crecimiento. |

### I-16 Tasa de ocupación hotelera

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Tasa de ocupación mensual |
| Definición | Índice oficial de ocupación de los establecimientos del departamento. |
| Fórmula | Valor de la fuente; si viene en porcentaje se divide entre 100 |
| Código pandas | `ocup[ocup["departamento"] == "Sololá"].set_index("periodo")["ocupacion"]` |
| Granularidad | Departamento x mes (2023 a 2025) |
| Unidad | Porcentaje |
| Archivo / hoja / columnas | `indice_ocupacion_mensual_2023_2025_1.csv` / `anio`, `mes`, `departamento`, `indice_ocupacion` |
| Reglas | Un mes sin dato nunca se toma como 0 %. Valores fuera de 0 a 1 son error de calidad. Nunca comparte eje con personas. |

### I-17 Captación formal de noches (ventana coincidente)

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Captación formal de noches por origen |
| Definición | Qué parte de las noches que la telefonía registra en el lago queda registrada en la hotelería formal de Sololá. Le dice al INGUAT cuánto del turismo describe la ocupación oficial. |
| Fórmula | $C_o = \dfrac{\sum_t NH_{t,o}}{\sum_t \sum_{p,i} (DP - V)_{t,i,p,o,s=\text{mayor a 1}}}$, con $o \in$ {extranjeros ↔ no residentes, nacionales ↔ residentes} |
| Código pandas | `c = of.cruce_ventana(m, boletin, ocup_solola, (pd.Timestamp("2025-09-01"), pd.Timestamp("2025-12-01")))`; `of.resumen_cruce(c)["captacion"]` |
| Granularidad | Dato: municipio-mes-país (telefonía) y departamento-mes-residencia (boletín). Cálculo: origen en la ventana de 4 meses |
| Unidad | Porcentaje |
| Archivo / hoja / columnas | Movilidad mensual (`visitantes`, `dias_persona`, `es_consecutivo`, `pais`); boletines `BOLETIN OCUPACION HOTELERA ... 2025.pdf`, tabla *Movimiento hotelero de turistas residentes y no residentes por departamento*, columnas *Noches realizadas (pernoctaciones)* y *Huéspedes registrados* |
| Reglas | Solo sep–dic 2025. Noches por telefonía = días-persona − visitantes de los turistas (quien está $d$ días pasa $d-1$ noches). La suma de municipios es cota superior, así que la captación es cota **inferior**. Orígenes nunca mezclados. Del boletín solo se extrae, con código, lo que no está en los CSV; su ocupación debe coincidir con el CSV (control de calidad). |

### I-17b Perfil declarado en la encuesta en fronteras

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Tipo de alojamiento y puesto de ingreso declarados |
| Definición | Porcentaje de los encuestados que, al entrar al país, declaran ir al Lago de Atitlán, según tipo de alojamiento (hotel, Airbnb, familia) y puesto de ingreso. Aporta evidencia sobre el alojamiento que la oferta formal no registra. |
| Fórmula | $\%_k = n_k / \sum_k n_k$ dentro de la ola vigente (sin la categoría N/A en alojamiento) |
| Código pandas | `g = f[f["ola"] == ola]; g.groupby("hospedaje")["encuestas"].sum() / g["encuestas"].sum()` |
| Granularidad | Dato: encuesta individual (no se conserva). Cálculo: ola x categoría |
| Unidad | Porcentaje muestral |
| Archivo / hoja / columnas | `BD_COMPLEMENTARIA` (parquet) / `nuevo_destino`, `BD`, `hospedaje`, `nombre_frontera`, `agrupacion_nombre`, `fecha` |
| Reglas | Sin factor de expansión: nunca se reporta como total de visitantes. El ETL guarda solo agregados. Las olas cambian de cuotas y puestos: no se presenta como serie de tiempo. |

### I-18 Afluencia relativa entre municipios

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Afluencia relativa (Panajachel = 100) |
| Definición | Visitantes (o días-persona) de cada municipio frente a los de Panajachel. |
| Fórmula | $100 \cdot \overline{V}_{\text{municipio}} \,/\, \overline{V}_{\text{Panajachel}}$ |
| Código pandas | `p = ind.por_municipio(m); p["visitantes_mes"] / p.loc["Panajachel", "visitantes_mes"] * 100` |
| Granularidad | Municipio; origen y medida elegidos |
| Unidad | Índice |
| Archivo / hoja / columnas | `BD_moviidad_mensual.xlsx` / *Atitlan* / `destino`, `visitantes`, `dias_persona` |
| Reglas | Se usa un índice y no una participación sobre el total porque los municipios no se suman. |

## Módulo 4. Red de municipios

### I-19 Clase del municipio

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Clase del municipio (regla del cuadrante y k-medias) |
| Definición | Papel de cada pueblo en la red: hub comercial, larga estancia o visita corta. |
| Fórmula | Regla (en orden): larga estancia si estadía $\ge P_{75}$ del lago e $\text{IEE} \ge 1$; hub si $\overline{V} \ge 0.6\max \overline{V}$; visita corta el resto. k-medias: $k=3$ sobre $z(\log_{10}\overline{V})$, $z(\text{estadía})$, $z(\text{IEE})$, $z(\text{presión})$ |
| Código pandas | `te.clasificar(te.perfil_completo(m, d))[["clase_regla", "clase_kmedias", "coinciden"]]` |
| Granularidad | Municipio |
| Unidad | Categoría |
| Archivo / hoja / columnas | Movilidad mensual (volumen, estadía, IEE) y diaria (presión de fin de semana) |
| Reglas | La regla es la clasificación principal; k-medias es contraste. Los municipios donde difieren se reportan como pueblos de transición. |

### I-20 Estabilidad de k-medias

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Estabilidad de k-medias |
| Definición | Proporción de municipios que conservan su clase al quitar a otro municipio y volver a agrupar. |
| Fórmula | $\dfrac{\sum_{j}\#\{i \ne j : c_i^{(-j)} = c_i\}}{\sum_j (n-1)}$ |
| Código pandas | `te.estabilidad_kmedias(perfil)` |
| Granularidad | Clasificación completa |
| Unidad | Porcentaje |
| Archivo / hoja / columnas | Las mismas que I-19 |
| Reglas | Por debajo de 80 % los grupos se consideran frágiles y el tablero lo advierte. |

### I-21 Índice de estacionalidad por clase

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| Nombre | Índice de estacionalidad por clase |
| Definición | Visitantes de cada mes de una clase frente a su promedio mensual. |
| Fórmula | $100 \cdot V_{c,t} \,/\, \overline{V}_{c}$ |
| Código pandas | `s = ind.serie_mensual(m[m["municipio"].isin(miembros)]); s / s.mean() * 100` |
| Granularidad | Clase x mes |
| Unidad | Índice (promedio = 100) |
| Archivo / hoja / columnas | `BD_moviidad_mensual.xlsx` / *Atitlan* / `destino`, `anio`, `mes`, `visitantes` |
| Reglas | Es un índice de forma: la suma de municipios duplica visitantes pero conserva la relación entre meses. Meses sin cobertura vacíos. |
