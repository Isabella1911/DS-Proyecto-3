# Guion de la presentación · Grupo 3 · Lago de Atitlán

Duración objetivo: **15 minutos de exposición + preguntas**. Ajustar los tiempos si la cátedra asigna otro bloque;
el reloj lo lleva quien no está hablando. Cifras con las bases reales (ETL del 12/11/2026). Si se vuelven a cargar
datos, verificar con `python scripts/revisar_datos.py`.

## Antes de entrar (checklist técnico)

- [ ] `docker compose up -d --build` con las bases en `data/raw/` → `curl localhost:8501/_stcore/health` responde `ok`.
- [ ] Abrir el tablero en el navegador y recorrer las 8 páginas una vez: precalienta la caché y descarga el mapa base.
- [ ] El mapa del módulo 4 necesita internet para el fondo (OpenStreetMap/CARTO). Sin red, las burbujas se ven igual sobre fondo vacío: decirlo si ocurre.
- [ ] Respaldo: tener abierta la memoria (`docs/memoria/Memoria_tecnica_Grupo3.docx`) y capturas de cada módulo por si falla el proyector o la red.
- [ ] Zoom del navegador al 90 % en el proyector; barra lateral abierta.
- [ ] Vestimenta formal. Teléfonos en silencio.

## Reparto (todos hablan, transiciones anunciadas)

| Bloque | Tiempo | Quién | Pantalla |
|:--|:--|:--|:--|
| Apertura, reto y cobertura de fuentes | 1:30 | Integrante 1 | Inicio |
| Módulo 1 · Demanda | 2:30 | Integrante 1 | 1 · Demanda y mercados |
| Módulo 2 · Temporalidad y estimación | 3:00 | Integrante 2 | 2 · Dinámica temporal |
| Módulo 3 · Oferta y triangulación | 3:00 | Integrante 3 | 3 · Oferta hotelera |
| Módulo 4 · Reto: red de municipios | 3:00 | Integrante 4 | 4 · Red de municipios |
| Conclusiones: 3 hallazgos y 3 recomendaciones | 2:00 | Integrante 4 → Integrante 1 cierra | Conclusiones |

Frase de transición sugerida al final de cada bloque (está escrita en el tablero, en el recuadro "Continúa en"):
"Ya sabemos *X*; la siguiente pregunta es *Y*, y la responde [nombre] con el módulo N".

## 1. Apertura (Inicio)

**Pregunta de gestión:** ¿qué necesita saber el INGUAT para gestionar el Lago de Atitlán como destino?

- Un observatorio monitorea de forma continua; no es un reporte estático. Seguimos INSTO (ONU Turismo) y SEGITTUR.
- Mostrar el **indicador de cobertura**: siete fuentes, cada una con su periodo. La telefonía cubre sep–dic 2025 y
  mar–ago 2026; enero y febrero de 2026 **no tienen dato** (recuadro violeta) y se estiman. La única ventana en que
  telefonía y ocupación coinciden es sep–dic 2025.
- Reglas que respetamos: sin dato no es cero, estadía ponderada, no sumar la base diaria ni los municipios, y
  **nunca dividir extranjeros entre el total** (los nacionales traen factor de expansión).

## 2. Módulo 1 · ¿Cuántos llegan, cuánto se quedan y de dónde?

- KPIs: **996.7 mil visitantes por mes** (suma de municipios, es una *cota superior* porque una persona cuenta en
  cada pueblo que visita), **5.67 días** de estadía media ponderada (Σ días-persona / Σ visitantes, solo > 1 día),
  **33 %** pernocta.
- Extranjeros y nacionales **por separado**: 87.4 mil extranjeros/mes y 909.3 mil nacionales/mes (con factor de expansión).
- **Demostrar el enlace:** clic en *San Pedro* en la gráfica de municipios → cambian KPIs, segmentación, top 10 y
  estadía por nacionalidad. Shift + clic para añadir Panajachel. Doble clic para limpiar.
- Mercados: **Estados Unidos 36 %** de los extranjeros; **Países Bajos** el de estadía más larga (2.6 días).

## 3. Módulo 2 · ¿Cuándo llegan y cuántos hubo en enero–febrero?

- **Demostrar el enlace:** clic en *Año Nuevo* en la gráfica de Lift → se resaltan sus días en la serie diaria.
  Lift **+142 %** frente a un día regular (+169 % ajustado por día de la semana). Día de los Santos y Festival de las
  Flores tienen Lift negativo: no todo feriado mueve la afluencia.
- Patrón semanal: el fin de semana recibe **1.26×** un día hábil; el sábado es el día más lleno.
- **Estimación ene–feb 2026** (violeta, rotulada *Estimación*): 1.05 M y 894 mil visitantes (suma de municipios).
  Método B (perfil estacional de migración 2023–2025 × nivel del destino). La migración aporta la *forma* estacional
  y el factor de reparto del destino aporta el *nivel*.
- **Validación:** dejando un mes fuera, **MAPE 8.9 %** (método A: 29.6 %). También MAE y RMSE en pantalla.
- **Verificación con la base diaria:** la rotación (únicos del mes / presencia diaria media) es estable (10.5, variación
  7 %); la presencia diaria que implica la estimación cae en el rango observado. La base diaria **no se proyecta**;
  el 1 de enero se declara ausente.
- Limitación: no hay comparación 2025 vs 2026 porque ningún mes se repite.

## 4. Módulo 3 · ¿Dónde duermen?

- Capacidad de Sololá: **9,639 plazas cama** en el corte 2025. Son cortes de inventario, no una tendencia; el corte
  2026-T1 es parcial y va con trama.
- **Demostrar el enlace:** clic en *2024* en la capacidad → la ocupación se enfoca en ese año.
- Ocupación 2025: **71 %** promedio, pico en diciembre (96 %).
- **Triangulación (sep–dic 2025):** con los boletines del INGUAT (extraídos con código; su ocupación coincide con el
  CSV en los 36 meses) comparamos noches en hotel formal con noches por telefonía, **por origen**:
  - Extranjeros: los hoteles formales registran el **58 %** de sus noches (r = 0.83).
  - Nacionales: solo el **3.7 %** (r = 0.94). Cambiar el selector de origen para mostrarlo.
- Encuesta en fronteras (ola V12): de quienes van al lago, **78 %** declara hotel, **12 %** Airbnb, y **64 %** entra
  por **La Mesilla** (ruta terrestre desde México). Son porcentajes muestrales sin factor de expansión.
- Lectura: la ocupación oficial describe al turismo extranjero; casi toda la presencia nacional con pernocta ocurre
  fuera del registro formal.

## 5. Módulo 4 · ¿Qué papel juega cada pueblo? (reto)

- Cuadrante: volumen (x, log) × estadía (y) × **especialización extranjera** (tamaño). Explicar en una frase el IEE:
  "cuánto más pesa el pueblo entre los extranjeros que entre los nacionales; 1 = igual que el lago". Reemplaza al
  % de extranjeros que la guía prohíbe calcular.
- Regla (líneas punteadas): larga estancia = estadía en el cuartil superior **e** IEE ≥ 1; hub = 60 % del volumen
  del mayor; visita corta = el resto.
  - **Hubs:** Panajachel y San Lucas. **Larga estancia:** San Pedro, San Juan y San Pablo (6.4 días vs 5.6).
    **Visita corta:** San Marcos, Santiago, Santa Cruz, Sta. Catarina y San Antonio.
- **Demostrar el enlace:** clic en *San Pedro* → abre su perfil (serie por origen, patrón semanal, mercados) y lo
  marca en la matriz.
- **Mapa:** botón ▶ Reproducir → peso de cada pueblo mes a mes. No hay flechas porque la base no trae pares origen-destino.
- k-medias como contraste: coincide en 5 de 10, estabilidad 88 %; agrupa sobre todo por volumen.
- **Hallazgo que contradice la expectativa:** San Marcos tiene la mayor especialización extranjera (1.84) pero una
  estadía de 4.2 días. La telefonía no respalda la imagen de "retiro"; hipótesis: duermen en San Pedro y lo visitan
  de día (hay que verificarlo con datos origen-destino).
- La presión de fin de semana es mayor en los **hubs (1.35×)** que en los de visita corta (1.18×): son nacionales
  que llegan por carretera.

## 6. Conclusiones · 3 hallazgos → 3 recomendaciones

| Hallazgo (con número) | Recomendación | Decisión que apoya | Prioridad |
|:--|:--|:--|:--|
| Año Nuevo +142 %; fin de semana 1.26× y 1.35× en los hubs | Gestionar picos en Panajachel y San Lucas | Transporte lacustre, seguridad y servicios en fines de semana y fin de año | Alta |
| Hotel formal capta 58 % de noches extranjeras y 3.7 % de nacionales; 12 % declara Airbnb | Registrar el alojamiento no formal con las municipalidades | Medir la capacidad real; leer la ocupación oficial como indicador del turismo extranjero | Alta |
| San Pedro, San Juan y San Pablo: 6.4 días e IEE 1.23; 64 % entra por La Mesilla | Promover estancias largas donde ya ocurren | Promoción internacional dirigida y información en la ruta terrestre | Media |

Mencionar las otras dos (temporada baja, que cae a 42 % en noviembre en promedio, y cerrar el hueco de telefonía) y los datos por
incorporar (telefonía continua, pares origen-destino, oferta por municipio, encuesta en sitio con factor de expansión).

**Cierre (Integrante 1, 20 s):** "El lago no es un destino, es una red: dos puertas de entrada, tres pueblos donde
se queda el turista y cinco de visita corta. Con estos datos el INGUAT puede decidir dónde reforzar servicios, dónde
promover y qué medir a partir de ahora."

## Preguntas probables y respuesta corta

- **¿Por qué no usan el % de extranjeros que pide la asignación?** La guía de uso lo lista como error: los
  nacionales traen factor de expansión y los extranjeros no. El IEE compara cuotas dentro de cada origen; un factor
  constante se cancela y ordena igual a los pueblos.
- **¿Por qué el total del lago es "suma de municipios"?** La guía prohíbe sumar subdestinos; el proveedor no entrega
  el total. Lo rotulamos como cota superior y usamos cocientes e índices para comparar.
- **¿Qué tan confiable es la estimación?** MAPE 8.9 % dejando un mes fuera, sobre 10 meses; además la verificación
  con la base diaria es consistente. Es una estimación rotulada, no un dato.
- **¿Por qué el método B y no el A?** Menor error. El A sigue mes a mes las llegadas internacionales, que no
  describen a los nacionales (no pasan por migración y son la mayor parte del flujo).
- **¿Extraer cifras de los PDF no está prohibido?** Lo prohibido es extraer *a mano* lo que ya está en los archivos.
  Extraemos con código solo lo que el CSV no tiene (huéspedes y noches por residencia) y verificamos que la
  ocupación del boletín coincida con el CSV (36 de 36 meses).
- **¿Captación de 3.7 % significa que el 96 % de nacionales duerme en Airbnb?** No. Significa que esas noches
  no pasan por el registro formal: casas de familia, alojamiento no registrado o presencia no turística que la
  telefonía no distingue. Por eso es una cota inferior y la recomendación es medir, no suponer.
- **¿Por qué San Lucas es hub?** Tiene el 60 % del volumen de Panajachel, IEE 0.33 (casi solo nacionales) y la mayor
  presión de fin de semana: es puerta de entrada nacional por la costa sur.
- **¿La encuesta de fronteras representa a todos los visitantes del lago?** No: no tiene factor de expansión y se
  levanta casi solo en puestos terrestres. Se usa como porcentaje del segmento y de la ola vigente.
- **¿Por qué la oferta no tiene línea de tendencia?** Son cinco cortes de inventario; la guía prohíbe tratarlos
  como tendencia.
- **¿Cómo se protege la confidencialidad?** Repositorio privado y `.gitignore` de los datos. En Docker, los datos se
  montan en solo lectura y nunca entran a la imagen. La exportación CSV está desactivada y el puerto solo escucha
  en 127.0.0.1.
