## 3.1 Indicadores del módulo 1: demanda y mercados emisores

### I-01 Visitantes promedio por mes

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Visitantes promedio por mes |
| 2. Definición de negocio | Promedio, entre los meses con dato, de los visitantes únicos del mes en el ámbito elegido. |
| 3. Fórmula matemática | $\frac{1}{T}\sum_{t}\sum_{p,s} V_{t,p,s}$, con $T$ = meses observados |
| 4. Implementación en código | `m.groupby("periodo")["visitantes"].sum().mean()` |
| 5. Nivel de agregación y granularidad | Mes; municipio o suma de municipios; origen opcional |
| 6. Unidad de medida | Visitantes por mes |
| 7. Fuente de datos de origen | `BD_moviidad_mensual.xlsx` / *Atitlan* / `destino`, `anio`, `mes`, `visitantes` |
| 8. Reglas de negocio y exclusiones | Un mes sin dato es "Sin dato", nunca 0. Con varios municipios se rotula "suma de municipios" (cota superior: un visitante cuenta en cada pueblo que visita). La base diaria no se usa para este indicador. |

### I-02 Días-persona promedio por mes

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Días-persona promedio por mes |
| 2. Definición de negocio | Promedio mensual de los días que pasan los visitantes en el destino (todos los segmentos). |
| 3. Fórmula matemática | $\frac{1}{T}\sum_{t}\sum_{p,s} DP_{t,p,s}$ |
| 4. Implementación en código | `m.groupby("periodo")["dias_persona"].sum().mean()` |
| 5. Nivel de agregación y granularidad | Mes; municipio o suma de municipios |
| 6. Unidad de medida | Días-persona por mes |
| 7. Fuente de datos de origen | `BD_moviidad_mensual.xlsx` / *Atitlan* / `dias_persona` |
| 8. Reglas de negocio y exclusiones | Los excursionistas aportan 1 día por visitante. El ETL marca como error las filas con días-persona menores que visitantes. |

### I-03 Estadía media ponderada

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Estadía media ponderada |
| 2. Definición de negocio | Días promedio que se queda un turista con pernocta. |
| 3. Fórmula matemática | $\dfrac{\sum DP_{s=\text{mayor a 1}}}{\sum V_{s=\text{mayor a 1}}}$ |
| 4. Implementación en código | `t = m[m["segmento"] == SEG_TURISTA]; t["dias_persona"].sum() / t["visitantes"].sum()` |
| 5. Nivel de agregación y granularidad | Ámbito y periodo elegidos; también por mes, municipio y nacionalidad |
| 6. Unidad de medida | Días |
| 7. Fuente de datos de origen | `BD_moviidad_mensual.xlsx` / *Atitlan* / `es_consecutivo`, `visitantes`, `dias_persona` |
| 8. Reglas de negocio y exclusiones | Nunca se promedia `permanencia_prom` (daría el mismo peso a un mercado de 2 personas que a uno de 2 000); esa columna solo se usa para verificar. Excluye excursionistas. |

### I-04 Porcentaje de turistas con pernocta

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Porcentaje de turistas con pernocta (segmentación turista / excursionista) |
| 2. Definición de negocio | Proporción de los visitantes que pasa más de un día en el destino. |
| 3. Fórmula matemática | $\dfrac{\sum V_{s=\text{mayor a 1}}}{\sum V}$; excursionistas $= 1 -$ turistas |
| 4. Implementación en código | `m.loc[m["segmento"] == SEG_TURISTA, "visitantes"].sum() / m["visitantes"].sum()` |
| 5. Nivel de agregación y granularidad | Mes (gráfica) y periodo (indicador) |
| 6. Unidad de medida | Porcentaje |
| 7. Fuente de datos de origen | `BD_moviidad_mensual.xlsx` / *Atitlan* / `es_consecutivo`, `visitantes` |
| 8. Reglas de negocio y exclusiones | `es_consecutivo` "mayor a 1" = turista, "menor a 1" = excursionista (menos de 24 h). Valores no reconocidos van al reporte de calidad. El porcentaje se rotula sobre cada barra; no se usa un eje secundario. |

### I-05 Visitantes extranjeros por mes e índice de especialización extranjera (IEE)

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Visitantes extranjeros por mes; índice de especialización extranjera (IEE) |
| 2. Definición de negocio | Cuántos extranjeros recibe el ámbito por mes (reportado aparte de los nacionales) y, por municipio, si atrae proporcionalmente más extranjeros que el lago en conjunto. Sirve para orientar la promoción internacional por pueblo. |
| 3. Fórmula matemática | $\overline{E} = \frac{1}{T}\sum_t E_t$; $\ \text{IEE}_i = \dfrac{E_i / \sum_j E_j}{N_i / \sum_j N_j}$ ($E$ extranjeros, $N$ nacionales, $j$ municipios) |
| 4. Implementación en código | `ind.kpis_demanda(m)["extranjeros_mes"]`; `ind.especializacion_extranjera(m)` (pivot municipio x origen, `cuota = t / t.sum()`, `cuota["Extranjero"] / cuota["Nacional"]`) |
| 5. Nivel de agregación y granularidad | Dato: municipio-mes-país. Cálculo: ámbito-periodo (volumen) y municipio (IEE) |
| 6. Unidad de medida | Personas por mes; índice (lago = 1) |
| 7. Fuente de datos de origen | `BD_moviidad_mensual.xlsx` / *Atitlan* / `destino`, `pais`, `visitantes` |
| 8. Reglas de negocio y exclusiones | **Nunca** se calcula extranjeros / total (error listado en la guía de uso): los nacionales traen factor de expansión. El IEE compara cuotas dentro de cada origen, por lo que un factor de expansión constante se cancela; ordena a los municipios igual que la proporción de la fuente, sin afirmar una participación real. |

### I-06 Participación de los mercados emisores extranjeros

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Top 10 de mercados emisores extranjeros |
| 2. Definición de negocio | Los diez países extranjeros con más visitantes y su participación sobre el total de extranjeros. |
| 3. Fórmula matemática | $\dfrac{\sum V_{p}}{\sum_{p'\in \text{ext}} V_{p'}}$ |
| 4. Implementación en código | `ext = m[m["origen"] == "Extranjero"]; v = ext.groupby("pais")["visitantes"].sum(); v.nlargest(10) / v.sum()` |
| 5. Nivel de agregación y granularidad | País; ámbito y periodo elegidos |
| 6. Unidad de medida | Visitantes y porcentaje |
| 7. Fuente de datos de origen | `BD_moviidad_mensual.xlsx` / *Atitlan* / `pais`, `visitantes` |
| 8. Reglas de negocio y exclusiones | Los nacionales se reportan aparte (factor de expansión). Los países se normalizan (mayúsculas, tildes, alias como EEUU o USA). |

### I-07 Estadía media por nacionalidad

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Estadía media por nacionalidad |
| 2. Definición de negocio | Estadía media ponderada (I-03) de cada uno de los diez principales mercados extranjeros, frente a la de los nacionales y al promedio. |
| 3. Fórmula matemática | $\dfrac{\sum DP_{p,s=\text{mayor a 1}}}{\sum V_{p,s=\text{mayor a 1}}}$ |
| 4. Implementación en código | `ind.top_paises(m, 10)["estadia_media"]` |
| 5. Nivel de agregación y granularidad | País |
| 6. Unidad de medida | Días |
| 7. Fuente de datos de origen | `BD_moviidad_mensual.xlsx` / *Atitlan* / `pais`, `es_consecutivo`, `visitantes`, `dias_persona` |
| 8. Reglas de negocio y exclusiones | Las mismas que I-03. Visualización adicional del grupo. |

## 3.2 Indicadores del módulo 2: dinámica temporal y estimación

### I-08 Lift de festividad

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Lift de festividad (simple) |
| 2. Definición de negocio | Cuánto sube la presencia diaria en los días de una festividad frente a un día regular. |
| 3. Fórmula matemática | $\dfrac{\overline{V}_{d\,\in\,\text{evento}}}{\overline{V}_{d\,\in\,\text{regular}}} - 1$ |
| 4. Implementación en código | `s = ind.serie_diaria(d); s[s["evento"] == e]["visitantes"].mean() / s[s["evento"] == "Regular"]["visitantes"].mean() - 1` |
| 5. Nivel de agregación y granularidad | Festividad; ámbito y origen elegidos |
| 6. Unidad de medida | Porcentaje |
| 7. Fuente de datos de origen | `BD_moviidad_diario.xlsx` / *Atitlan* / `idfecha`, `evento`, `cantidad_visitantes` |
| 8. Reglas de negocio y exclusiones | Promedios por día, nunca sumas. Los días sin cobertura no cuentan como 0. "Regular", "Normal" o vacío se normalizan como día regular. |

### I-09 Lift ajustado por día de la semana

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Lift ajustado por día de la semana |
| 2. Definición de negocio | Lift en el que cada día de festividad se compara con el día regular promedio del mismo día de la semana. |
| 3. Fórmula matemática | $\frac{1}{n}\sum_{d\,\in\,\text{evento}} \dfrac{V_d}{\overline{V}_{\text{regular},\,\text{dds}(d)}} - 1$ |
| 4. Implementación en código | `(ev["visitantes"] / ev["dia_semana"].map(base_dia)).mean() - 1`, con `base_dia = reg.groupby("dia_semana")["visitantes"].mean()` |
| 5. Nivel de agregación y granularidad | Festividad |
| 6. Unidad de medida | Porcentaje |
| 7. Fuente de datos de origen | `BD_moviidad_diario.xlsx` / *Atitlan* / `idfecha`, `evento`, `cantidad_visitantes` |
| 8. Reglas de negocio y exclusiones | Evita atribuir al feriado el efecto de caer en sábado o domingo. El día de la semana se recalcula desde la fecha; si difiere de `dia_semana` se reporta en calidad. |

### I-10 Índice del patrón semanal

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Índice del patrón semanal |
| 2. Definición de negocio | Visitantes promedio de cada día de la semana frente al promedio de los siete días. |
| 3. Fórmula matemática | $100 \cdot \overline{V}_{\text{dds}} \,/\, \frac{1}{7}\sum_{\text{dds}} \overline{V}_{\text{dds}}$ |
| 4. Implementación en código | `p = reg.groupby("dia_semana")["visitantes"].mean(); p / p.mean() * 100` |
| 5. Nivel de agregación y granularidad | Día de la semana; ámbito o municipio |
| 6. Unidad de medida | Índice (promedio = 100) |
| 7. Fuente de datos de origen | `BD_moviidad_diario.xlsx` / *Atitlan* / `idfecha`, `evento`, `cantidad_visitantes` |
| 8. Reglas de negocio y exclusiones | Por defecto solo días regulares, para que un feriado no infle el día en que cayó. |

### I-11 Presión de fin de semana

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Presión de fin de semana |
| 2. Definición de negocio | Cuántas veces recibe un sábado o domingo los visitantes de un día hábil. |
| 3. Fórmula matemática | $\overline{V}_{\text{sáb, dom}} \,/\, \overline{V}_{\text{lun a vie}}$ |
| 4. Implementación en código | `ind.presion_fin_de_semana(ind.patron_semanal(ind.serie_diaria(d)))` |
| 5. Nivel de agregación y granularidad | Ámbito; por municipio y por clase en el módulo 4 |
| 6. Unidad de medida | Veces (razón) |
| 7. Fuente de datos de origen | `BD_moviidad_diario.xlsx` / *Atitlan* / `idfecha`, `evento`, `cantidad_visitantes` |
| 8. Reglas de negocio y exclusiones | Solo días regulares. Variable de k-medias en el módulo 4. |

### I-12 Estimación de visitantes de enero y febrero de 2026

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Estimación de los meses sin cobertura de telefonía |
| 2. Definición de negocio | Visitantes únicos estimados para los meses que la telefonía no cubre, con la base de migración. |
| 3. Fórmula matemática | A: $F = \dfrac{\sum_{\text{obs}} D_t}{\sum_{\text{obs}} M_t}$, $\hat D_t = F\,M_t$. B: $S_m = \overline{M_{a,m}/\overline{M}_a}$, $L = \dfrac{\sum_{\text{obs}} D_t}{\sum_{\text{obs}} S_{m(t)}}$, $\hat D_t = L\,S_{m(t)}$ |
| 4. Implementación en código | `pr.estimar(obs, mig, ["2026-01", "2026-02"], [2023, 2024, 2025], metodo)` |
| 5. Nivel de agregación y granularidad | Mes; ámbito y origen elegidos |
| 6. Unidad de medida | Visitantes por mes |
| 7. Fuente de datos de origen | Destino: `BD_moviidad_mensual.xlsx` (`visitantes`). Migración: `Base_Migracion_2009-2026jun.xlsx` / *Datos* / `Año`, `Mes cod`, `Tipo de Viajero`, `Viajero` |
| 8. Reglas de negocio y exclusiones | $M_t$ = turistas + excursionistas internacionales del mes. Se muestra siempre en violeta, con línea discontinua y rotulada "Estimación"; nunca entra en los indicadores observados. Por defecto se elige el método con menor MAPE. |

### I-13 Error de validación de la estimación

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | MAPE, MAE y RMSE |
| 2. Definición de negocio | Error de estimar cada mes observado sin usarlo para calcular el factor (validación dejando uno fuera). |
| 3. Fórmula matemática | $\text{MAPE} = \frac{100}{n}\sum \frac{\lvert \hat D_t - D_t\rvert}{D_t}$; $\text{MAE} = \frac{1}{n}\sum \lvert \hat D_t - D_t\rvert$; $\text{RMSE} = \sqrt{\frac{1}{n}\sum (\hat D_t - D_t)^2}$ |
| 4. Implementación en código | `err = val["estimado"] - val["observado"]; (err.abs() / val["observado"]).mean() * 100` |
| 5. Nivel de agregación y granularidad | Método y ámbito |
| 6. Unidad de medida | Porcentaje (MAPE); visitantes (MAE, RMSE) |
| 7. Fuente de datos de origen | Las mismas que I-12 |
| 8. Reglas de negocio y exclusiones | Si el MAPE supera 20 %, el tablero pide presentar la estimación como orden de magnitud. |

### I-14 Perfil estacional de las llegadas internacionales

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Perfil estacional de migración |
| 2. Definición de negocio | Llegadas de cada mes frente al promedio de su año, promediado entre los años del perfil. |
| 3. Fórmula matemática | $S_m = \frac{1}{A}\sum_{a} M_{a,m} \,/\, \overline{M}_a$ |
| 4. Implementación en código | `b = mig[mig["anio"].isin(anios)]; (b["llegadas"] / b.groupby("anio")["llegadas"].transform("mean")).groupby(b["mes"]).mean()` |
| 5. Nivel de agregación y granularidad | Mes del año |
| 6. Unidad de medida | Índice (1 = mes promedio) |
| 7. Fuente de datos de origen | `Base_Migracion_2009-2026jun.xlsx` / *Datos* / `Año`, `Mes cod`, `Tipo de Viajero`, `Viajero` |
| 8. Reglas de negocio y exclusiones | Años del perfil en `config.yaml` (2023 a 2025). Visualización adicional del grupo. |

### I-15 Rotación mensual (verificación con la base diaria)

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Rotación mensual y presencia diaria implícita en la estimación |
| 2. Definición de negocio | Visitantes únicos del mes por cada persona presente en un día promedio. Si es estable, permite verificar que la estimación de ene–feb 2026 tenga una forma diaria plausible. |
| 3. Fórmula matemática | $R_t = V^{\text{mensual}}_t / \overline{P}^{\text{diaria}}_t$; presencia implícita $= \hat D_t / \overline R$ |
| 4. Implementación en código | `pr.consistencia_diaria(obs, ind.serie_diaria(d), r.estimados)` |
| 5. Nivel de agregación y granularidad | Ámbito-mes (solo meses con base diaria completa, ≥ 28 días) |
| 6. Unidad de medida | Ratio; personas presentes por día |
| 7. Fuente de datos de origen | Movilidad mensual (`visitantes`) y diaria (`idfecha`, `cantidad_visitantes`) |
| 8. Reglas de negocio y exclusiones | La base diaria se promedia, nunca se suma ni se proyecta. Los feriados de meses sin cobertura se declaran ausentes. |

## 3.3 Indicadores del módulo 3: oferta de alojamiento

### I-16 Capacidad instalada

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Capacidad instalada (establecimientos, habitaciones y plazas cama) |
| 2. Definición de negocio | Inventario de alojamiento formal de Sololá al cierre de cada año. |
| 3. Fórmula matemática | $C_a = \sum_{\text{tipo}} C_{a,\text{T4},\text{tipo}}$; crecimiento $= C_{a_1}/C_{a_0} - 1$ |
| 4. Implementación en código | `anual = of.capacidad_anual(of.capacidad(oferta, "Sololá")); anual["plazas_cama"].iloc[-1] / anual["plazas_cama"].iloc[0] - 1` |
| 5. Nivel de agregación y granularidad | Año (corte del cuarto trimestre) y tipo de alojamiento |
| 6. Unidad de medida | Establecimientos, habitaciones o plazas cama |
| 7. Fuente de datos de origen | `oferta_hotelera_2022_2026.csv` / `anio`, `trimestre`, `departamento`, `tipo_alojamiento`, `establecimientos`, `habitaciones`, `plazas_cama` |
| 8. Reglas de negocio y exclusiones | Inventario, no flujo: los cortes se presentan como barras por año y no como tendencia. El corte 2026-T1 es parcial y se identifica con trama. |

### I-17 Tasa de ocupación hotelera

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Tasa de ocupación hotelera (publicada y sobre inventario) |
| 2. Definición de negocio | Proporción de habitaciones ocupadas. El índice publicado se calcula sobre los establecimientos que reportan; la ocupación sobre inventario usa todas las habitaciones registradas y mide la utilización real de la capacidad. |
| 3. Fórmula matemática | Valor de la fuente; si viene en porcentaje se divide entre 100 |
| 4. Implementación en código | `ocup.query("departamento == 'Sololá'")["ocupacion"]`; `bol.groupby("anio")["hab_total"].sum() / (anual["habitaciones"] * 365)` |
| 5. Nivel de agregación y granularidad | Departamento x mes (2023 a 2025) |
| 6. Unidad de medida | Porcentaje |
| 7. Fuente de datos de origen | `indice_ocupacion_mensual_2023_2025_1.csv` (`indice_ocupacion`); boletines de ocupación (habitaciones ocupadas); `oferta_hotelera_2022_2026.csv` (habitaciones) |
| 8. Reglas de negocio y exclusiones | Un mes sin dato nunca se toma como 0%. La cobertura implícita del índice (habitaciones de la muestra ÷ inventario) debe reportarse junto con él. No comparte eje con personas. |

### I-18 Captación formal de noches (ventana coincidente)

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Captación formal de noches por origen |
| 2. Definición de negocio | Qué parte de las noches que la telefonía registra en el lago queda registrada en la hotelería formal de Sololá. Le dice al INGUAT cuánto del turismo describe la ocupación oficial. |
| 3. Fórmula matemática | $C_o = \dfrac{\sum_t NH_{t,o}}{\sum_t \sum_{p,i} (DP - V)_{t,i,p,o,s=\text{mayor a 1}}}$, con $o \in$ {extranjeros ↔ no residentes, nacionales ↔ residentes} |
| 4. Implementación en código | `c = of.cruce_ventana(m, boletin, ocup_solola, (pd.Timestamp("2025-09-01"), pd.Timestamp("2025-12-01")))`; `of.resumen_cruce(c)["captacion"]` |
| 5. Nivel de agregación y granularidad | Dato: municipio-mes-país (telefonía) y departamento-mes-residencia (boletín). Cálculo: origen en la ventana de 4 meses |
| 6. Unidad de medida | Porcentaje |
| 7. Fuente de datos de origen | Movilidad mensual (`visitantes`, `dias_persona`, `es_consecutivo`, `pais`); boletines `BOLETIN OCUPACION HOTELERA ... 2025.pdf`, tabla *Movimiento hotelero de turistas residentes y no residentes por departamento*, columnas *Noches realizadas (pernoctaciones)* y *Huéspedes registrados* |
| 8. Reglas de negocio y exclusiones | Solo sep–dic 2025. Noches por telefonía = días-persona − visitantes de los turistas (quien está $d$ días pasa $d-1$ noches). La suma de municipios es cota superior, así que la captación es cota **inferior**. Orígenes nunca mezclados. Del boletín solo se extrae, con código, lo que no está en los CSV; su ocupación debe coincidir con el CSV (control de calidad). |

### I-19 Perfil declarado en la encuesta en fronteras

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Tipo de alojamiento y puesto de ingreso declarados |
| 2. Definición de negocio | Porcentaje de los encuestados que, al entrar al país, declaran ir al Lago de Atitlán, según tipo de alojamiento (hotel, Airbnb, familia) y puesto de ingreso. Aporta evidencia sobre el alojamiento que la oferta formal no registra. |
| 3. Fórmula matemática | $\%_k = n_k / \sum_k n_k$ dentro de la ola vigente (sin la categoría N/A en alojamiento) |
| 4. Implementación en código | `g = f[f["ola"] == ola]; g.groupby("hospedaje")["encuestas"].sum() / g["encuestas"].sum()` |
| 5. Nivel de agregación y granularidad | Dato: encuesta individual (no se conserva). Cálculo: ola x categoría |
| 6. Unidad de medida | Porcentaje muestral |
| 7. Fuente de datos de origen | `BD_COMPLEMENTARIA` (parquet) / `nuevo_destino`, `BD`, `hospedaje`, `nombre_frontera`, `agrupacion_nombre`, `fecha` |
| 8. Reglas de negocio y exclusiones | Sin factor de expansión: nunca se reporta como total de visitantes. El ETL guarda solo agregados. Las olas cambian de cuotas y puestos: no se presenta como serie de tiempo. |

### I-20 Afluencia relativa entre municipios

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Afluencia relativa (Panajachel = 100) |
| 2. Definición de negocio | Visitantes (o días-persona) de cada municipio frente a los de Panajachel. |
| 3. Fórmula matemática | $100 \cdot \overline{V}_{\text{municipio}} \,/\, \overline{V}_{\text{Panajachel}}$ |
| 4. Implementación en código | `p = ind.por_municipio(m); p["visitantes_mes"] / p.loc["Panajachel", "visitantes_mes"] * 100` |
| 5. Nivel de agregación y granularidad | Municipio; origen y medida elegidos |
| 6. Unidad de medida | Índice |
| 7. Fuente de datos de origen | `BD_moviidad_mensual.xlsx` / *Atitlan* / `destino`, `visitantes`, `dias_persona` |
| 8. Reglas de negocio y exclusiones | Se usa un índice y no una participación sobre el total porque los municipios no se suman. |

## 3.4 Indicadores del módulo 4: red de municipios

### I-21 Clase del municipio

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Clase del municipio (regla del cuadrante y k-medias) |
| 2. Definición de negocio | Papel de cada pueblo en la red: hub comercial, larga estancia o visita corta. |
| 3. Fórmula matemática | Regla (en orden): larga estancia si estadía $\ge P_{75}$ del lago e $\text{IEE} \ge 1$; hub si $\overline{V} \ge 0.6\max \overline{V}$; visita corta el resto. k-medias: $k=3$ sobre $z(\log_{10}\overline{V})$, $z(\text{estadía})$, $z(\text{IEE})$, $z(\text{presión})$ |
| 4. Implementación en código | `te.clasificar(te.perfil_completo(m, d))[["clase_regla", "clase_kmedias", "coinciden"]]` |
| 5. Nivel de agregación y granularidad | Municipio |
| 6. Unidad de medida | Categoría |
| 7. Fuente de datos de origen | Movilidad mensual (volumen, estadía, IEE) y diaria (presión de fin de semana) |
| 8. Reglas de negocio y exclusiones | La regla es la clasificación principal; k-medias es contraste. Los municipios donde difieren se reportan como pueblos de transición. |

### I-22 Estabilidad de k-medias

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Estabilidad de k-medias |
| 2. Definición de negocio | Proporción de municipios que conservan su clase al quitar a otro municipio y volver a agrupar. |
| 3. Fórmula matemática | $\dfrac{\sum_{j}\#\{i \ne j : c_i^{(-j)} = c_i\}}{\sum_j (n-1)}$ |
| 4. Implementación en código | `te.estabilidad_kmedias(perfil)` |
| 5. Nivel de agregación y granularidad | Clasificación completa |
| 6. Unidad de medida | Porcentaje |
| 7. Fuente de datos de origen | Las mismas que I-19 |
| 8. Reglas de negocio y exclusiones | Por debajo de 80 % los grupos se consideran frágiles y el tablero lo advierte. |

### I-23 Índice de estacionalidad por clase

| Campo | Contenido |
|:------|:-----------------------------------------------------------|
| 1. Nombre del indicador | Índice de estacionalidad por clase |
| 2. Definición de negocio | Visitantes de cada mes de una clase frente a su promedio mensual. |
| 3. Fórmula matemática | $100 \cdot V_{c,t} \,/\, \overline{V}_{c}$ |
| 4. Implementación en código | `s = ind.serie_mensual(m[m["municipio"].isin(miembros)]); s / s.mean() * 100` |
| 5. Nivel de agregación y granularidad | Clase x mes |
| 6. Unidad de medida | Índice (promedio = 100) |
| 7. Fuente de datos de origen | `BD_moviidad_mensual.xlsx` / *Atitlan* / `destino`, `anio`, `mes`, `visitantes` |
| 8. Reglas de negocio y exclusiones | Es un índice de forma: la suma de municipios duplica visitantes pero conserva la relación entre meses. Meses sin cobertura vacíos. |
