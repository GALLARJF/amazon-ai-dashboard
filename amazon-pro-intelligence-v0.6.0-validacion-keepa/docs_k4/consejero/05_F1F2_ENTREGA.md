# K4 · Consejero Estratégico — Entrega F1–F2

> *Documento regenerado en F2.1 con la corrección de formato (ACTIVCORE = 100 ml; ver `06_F21_CORRECCIONES.md`).*

> **Todo lo mostrado aquí se ha generado con proveedores SIMULADOS y datos SINTÉTICOS** (URLs `sintetico://`, textos marcados «[SINTÉTICO]»). Gasto adicional: **0 €**. Sin IA externa, sin búsqueda de pago, sin credenciales. **Superar estas pruebas valida el motor (trazabilidad, verificación, sensibilidad a la evidencia); no demuestra razonamiento autónomo real.** PR #4 sin fusionar.

## 1. Qué se ha construido

| Módulo | Función |
|---|---|
| `k4c_providers.py` | Interfaces independientes del proveedor (llm, búsqueda, lectura, herramienta, verificador), adaptadores externos NO operativos y `Router`: estados OPERATIVA/NO_OPERATIVA/REQUIERE_AUTORIZACION, bloqueo de proveedor REAL sin autorización, topes (0 € por defecto), log de cada consulta |
| `k4c_ledger.py` | Libro de evidencias persistente: fuente (procedencia, fecha, tipo primaria/secundaria, calidad, vigencia, entorno), extracto literal con hash, afirmaciones, hipótesis, predicciones |
| `k4c_verifier.py` | Verificador: cita inexistente, cita que no respalda, histórico como actual, error de cálculo, secundaria como primaria, comparación no equivalente, conclusión que excede la evidencia (+ ausencia como prueba, BSR→ventas, correlación→causa, ingrediente→fórmula) |
| `k4c_mock.py` | Corpus sintético, búsqueda/lectura/LLM simulados (el LLM simulado puede inyectar errores para probar el verificador), calculadora de diseño de experimento |
| `k4c_engine.py` | Plan, árbol de hipótesis (con búsqueda contraria), informe estructurado, decisión por reglas explícitas, evaluación adversarial, premisas, predicciones, integración con Director |
| `api_k4.py` | `GET consejero/estado|investigaciones|investigacion/<id>|libro/<id>` · `POST consejero/investigar|dossier|proponer|prediccion` (sin pantallas nuevas) |

Pruebas: `tests/k4c_test.py` (ver doc 06 para el recuento F2.1); registrada en `run_all.sh`, `coordinador.py` y CI.

## 2. Demostración del libro de evidencias (investigación INV-b269798b)

10 fuentes · 10 extractos · 26 consultas registradas · gasto 0.0 €

| Fuente | Tipo | Calidad | Dato | Fecha | Objeto |
|---|---|---|---|---|---|
| `sintetico://blog-norma` | SECUNDARIA | BAJA | ATEMPORAL | 2024-09-01 | NORMA |
| `sintetico://bsr-nota` | SECUNDARIA | MEDIA | ATEMPORAL | 2024-01-15 | METODO |
| `sintetico://cafeina-revision` | PRIMARIA | ALTA | ATEMPORAL | 2024-05-01 | INGREDIENTE |
| `sintetico://comp-alfa` | PRIMARIA | ALTA | ACTUAL | 2026-11-16 | PRODUCTO |
| `sintetico://comp-beta` | PRIMARIA | ALTA | HISTORICO | 2025-03-02 | PRODUCTO |
| `sintetico://comp-delta` | PRIMARIA | ALTA | ACTUAL | 2026-11-12 | PRODUCTO |
| `sintetico://comp-gamma` | PRIMARIA | ALTA | ACTUAL | 2026-11-12 | PRODUCTO |
| `sintetico://luteolina-raton` | PRIMARIA | MEDIA | ATEMPORAL | 2023-02-10 | INGREDIENTE |
| `sintetico://minoxidil` | PRIMARIA | ALTA | ACTUAL | 2026-10-20 | MEDICAMENTO |
| `sintetico://norma-oficial` | PRIMARIA | ALTA | ATEMPORAL | 2023-06-01 | NORMA |

Extractos (literales, con hash; cada uno ligado a una hipótesis y un efecto):

- `X-8b760705c7` · H0 · efecto +1 · «la cafeína tópica mejora el recuento de cabello en alopecia androgenética con certeza GRADE moderada»
- `X-19c788cc2e` · H0 · efecto +0 · «la luteolina tópica aumentó el crecimiento del pelo; no existen datos en humanos»
- `X-66ddec54e1` · H2 · efecto +1 · «serum capilar premium de 90 ml, precio observado 39,94 EUR»
- `X-2e5aed35be` · H2 · efecto +1 · «serum capilar premium de 30 ml, precio observado 35,00 EUR»
- `X-16d384c34a` · H2 · efecto +1 · «ampollas capilares premium de 50 ml, precio observado 52,00 EUR»
- `X-b59a4af507` · H2 · efecto +0 · «tratamiento capilar de 100 ml, precio 55,00 EUR en marzo de 2025»
- `X-d6abd99ae2` · H3 · efecto +1 · «Minoxidil 5 % solución de 60 ml, precio máximo oficial 12,49 EUR»
- `X-c31b5580ac` · H4 · efecto +1 · «se decide caso por caso valorando la presentación completa, la composición y las alegaciones»
- `X-23dda5283f` · H4 · efecto +0 · «alegaciones de crecimiento capilar suelen considerarse medicinales»
- `X-23d4a00988` · H5 · efecto +0 · «no equivale a unidades vendidas»

Primeras consultas del log (proveedor, método, estado, coste):

- 2026-11-19T01:38:54 · busqueda_sintetica.buscar · «cafeina topica evidencia ingrediente ensayo revision» · 2 resultados · OK · 0.0 €
- 2026-11-19T01:38:54 · lectura_sintetica.leer · «sintetico://cafeina-revision» · 1 resultados · OK · 0.0 €
- 2026-11-19T01:38:54 · lectura_sintetica.leer · «sintetico://luteolina-raton» · 1 resultados · OK · 0.0 €
- 2026-11-19T01:38:54 · busqueda_sintetica.buscar · «luteolina topica evidencia ingrediente ensayo revision» · 2 resultados · OK · 0.0 €
- 2026-11-19T01:38:54 · busqueda_sintetica.buscar · «cafeina topica evidencia ingrediente limites ensayo» · 2 resultados · OK · 0.0 €
- 2026-11-19T01:38:54 · busqueda_sintetica.buscar · «luteolina topica evidencia ingrediente limites ensayo» · 2 resultados · OK · 0.0 €

## 3. Ejemplo de investigación con proveedor simulado

Pregunta: «¿Se sostiene el precio premium de ACTIVCORE?» (49,90 € / 100 ml = 49,90 €/100 ml, ficha maestra) con datos internos sintéticos declarados (ventas 3/día, margen 20 €, tráfico 400/día, conversión 5 %, elasticidad medida −2,0 sobre 12 observaciones).

**Hipótesis (H0 = tesis de AHT; H1–H5 = alternativas):**

- **H0** (AHT) — El precio premium de ACTIVCORE se sostiene por la evidencia de sus ingredientes (cafeina, luteolina). → *PARCIALMENTE_SOPORTADA_SOLO_INGREDIENTE* (puntuación 4)
- **H1** (ALTERNATIVA) — La evidencia del ingrediente no se traslada a la fórmula final y no justifica por sí sola un sobreprecio. → *SOPORTADA* (puntuación 0)
- **H2** (ALTERNATIVA) — El mercado comparable vigente (cosméticos capilares premium equivalentes) fija un rango de precio por 100 ml del que ACTIVCORE puede quedar dentro o fuera; el rango no decide por sí solo. → *SOPORTADA* (puntuación 12)
- **H3** (ALTERNATIVA) — Minoxidil es un sustituto terapéutico indirecto que condiciona la disposición a pagar, no un competidor cosmético equivalente. → *SOPORTADA* (puntuación 4)
- **H4** (ALTERNATIVA) — La clasificación regulatoria depende de la presentación completa, la composición y las alegaciones (crecimiento capilar, anticaida); una alegación de crecimiento puede cambiarla. → *SOPORTADA* (puntuación 4)
- **H5** (ALTERNATIVA) — No se pueden inferir ventas reales a partir del BSR ni atribuir causalidad a correlaciones de BSR y precio. → *INDECISA* (puntuación 0)

**Hechos con cita y cálculo recalculado:**

- Precio por 100 ml calculado: Ficha Alfa serum capilar → `precio / volumen * 100` = 44.38 (vigente)
- Precio por 100 ml calculado: Ficha Beta tratamiento capilar → `precio / volumen * 100` = 55.0 (**histórico**, no se usa como actual)
- Precio por 100 ml calculado: Ficha Delta ampolla → `precio / volumen * 100` = 104.0 (vigente)
- Precio por 100 ml calculado: Ficha Gamma serum → `precio / volumen * 100` = 116.67 (vigente)
- Precio por 100 ml calculado: Precio máximo minoxidil (sustituto terapéutico indirecto, no competidor cosmético equivalente) → `precio / volumen * 100` = 20.82 (vigente)
- Precio propio por 100 ml (ficha maestra): 49.9 EUR → `precio / volumen * 100` = 49.9 (vigente)
- Precio óptimo de margen con elasticidad medida e=-2.0 (n=12, historial sintético de precio): 59.8 EUR → `coste * e / (1 + e)` = 59.8 (vigente)

**Datos faltantes declarados:**

- Ensayo clínico o prueba de eficacia/seguridad de la fórmula final de ACTIVCORE. No se localizó evidencia en las consultas del libro (no equivale a ausencia de efecto).
- Clasificación regulatoria del caso concreto con fuente oficial. Pendiente de análisis de la presentación completa y las alegaciones.

**Conclusión:** `SUBIR` · confianza MEDIA. Con elasticidad medida e=-2.00 y coste variable 29.90 €, el precio óptimo de margen es 59.80 € (+20 % vs actual).

Tesis de AHT: **PARCIALMENTE_SOPORTADA_SOLO_INGREDIENTE** — alcance: evidencia de INGREDIENTE; no equivale a eficacia de la fórmula final.

**Experimento** (según tráfico/conversión, no 3 días fijos): n = 14193 por variante, ≥ 71 días. al menos 2 semanas completas para cubrir ciclo semanal; potencia 80 %, alfa 0.05, efecto mínimo detectable 15 % relativo

**Qué cambiaría la conclusión:** Aparecen ≥3 comparables vigentes y equivalentes (cambia el rango de referencia). · Se obtienen ventas y margen reales y una medida de la respuesta de la demanda al precio. · Se localiza evidencia de la fórmula final, a favor o en contra. · Una corrección o retractación de la evidencia del ingrediente (debilita la tesis de AHT).

Verificación: **ACEPTADO_CON_RESERVAS** (0 bloqueantes, 1 avisos). Adversarial: **SUPERADA**. Publicación: **PUBLICABLE_INTERNO** (entorno SINTETICO).

### Cambia la conclusión cuando cambia la evidencia (T1)

| Escenario sintético | Decisión | Confianza | Tesis AHT (H0) |
|---|---|---|---|
| BASE (sin datos internos, 1 comparable vigente) | NO_CONCLUIBLE | BAJA | PARCIALMENTE_SOPORTADA_SOLO_INGREDIENTE |
| + 2 comparables vigentes + datos internos (sin elasticidad) | DISENAR_EXPERIMENTO | BAJA | PARCIALMENTE_SOPORTADA_SOLO_INGREDIENTE |
| + elasticidad medida | SUBIR | MEDIA | PARCIALMENTE_SOPORTADA_SOLO_INGREDIENTE |
| Revisión de cafeína corregida (certeza muy baja) | NO_CONCLUIBLE | BAJA | DEBILITADA |

## 4. Ejemplo de conclusión rechazada por el verificador

El redactor simulado inyecta una decisión «SUBIR» con confianza ALTA apoyada solo en hipótesis/inferencias (sin evidencia de respuesta al precio):

- **CONCLUSION_EXCEDE_EVIDENCIA** (conclusion): confianza ALTA pero el eslabón más débil de la base es de calidad 1/3
- **CONCLUSION_EXCEDE_EVIDENCIA** (conclusion): una decisión de precio exige datos internos observados (ventas/margen) entre sus bases
- **RECOMENDACION_SOLO_POR_RANGO** (conclusion): SUBIR/BAJAR/MANTENER exige evidencia de la respuesta de la demanda al precio; la posición frente al rango de competidores no basta
- **CONCLUSION_EXCEDE_EVIDENCIA** (conclusion): conclusión basada solo en hipótesis/inferencias con confianza superior a BAJA

Resultado: **RECHAZADO** → publicación **NO_PUBLICABLE**. El motor no la propone como decisión.

Caso de cita válida que no respalda la afirmación (el id existe, el contenido no): 
**CITA_NO_RESPALDA** — X-f64181dead: cifras no presentes en el extracto: 40. La afirmación se retira y el informe queda `ACEPTADO_CON_RESERVAS` con la retirada registrada.

## 5. Correcciones A–F al caso ACTIVCORE incorporadas

| | Corrección | Dónde se aplica |
|---|---|---|
| A | Minoxidil = sustituto terapéutico indirecto | `comparacion.relacion_declarada=SUSTITUTO_INDIRECTO`; sin ella el verificador bloquea (`COMPARACION_NO_EQUIVALENTE`); hipótesis H3 |
| B | Clasificación regulatoria por presentación completa, mecanismo y alegaciones | H4; fuente oficial exigida (`NORMATIVA_SIN_FUENTE_OFICIAL`); queda como dato faltante, no se dictamina |
| C | Sin pruebas de precio de 3 días por defecto | `CalculadoraExperimento`: n y duración por tráfico, conversión, MDE; sin datos → «no diseñable»; avisa de inviabilidad |
| D | Evidencia de ingrediente ≠ fórmula final | `objeto` de fuente; `INGREDIENTE_COMO_FORMULA`; la tesis H0 solo puede ser `PARCIALMENTE_SOPORTADA_SOLO_INGREDIENTE` |
| E | Ausencia localizada ≠ ausencia de efecto | `AUSENCIA_LOCALIZADA` (FALTANTE) vs `AUSENCIA_COMO_EVIDENCIA_DE_AUSENCIA` bloqueante |
| F | Correlación ≠ causa; BSR ≠ ventas | `CORRELACION_COMO_CAUSA`, `BSR_COMO_VENTAS` |

## 6. Estado de las diez pruebas anti-plantilla

Leyenda: **AUTO** = automatizada en `k4c_test.py` con mocks · **PARCIAL** = la parte de procedimiento está automatizada, el resto exige evaluación humana o modelo real · **HUMANA** · **TEMPORAL** = requiere seguimiento en el tiempo.

| Prueba | Estado | Qué se comprueba hoy | Qué NO se demuestra |
|---|---|---|---|
| T1 Contrafactual | AUTO | La conclusión y la tesis cambian de forma coherente al cambiar evidencia o dato interno (4 comprobaciones) | Que un modelo real haga lo mismo con evidencia ambigua |
| T2 Sin herramientas | AUTO | Sin búsqueda: «no pude investigar», sin fuentes ni hechos inventados, NO_CONCLUIBLE | Que un LLM real no rellene de memoria (el redactor simulado no lo intenta) |
| T3 Trazabilidad | AUTO | 0 hechos sin cita; hash de extractos; cálculos recalculados; 11 trampas detectadas | Verificación semántica profunda: el verificador léxico es heurístico |
| T4 Premisa falsa | AUTO (heurística) | «Luteolina demostrada en humanos» se marca CUESTIONADA con el extracto; la premisa cierta no se contradice | Premisas sutiles o expresadas de otro modo |
| T5 Producto control | AUTO | Sin datos: NO_CONCLUIBLE, sin hechos citados, ≥3 faltantes | — |
| T6 Solapamiento | PARCIAL | Herramienta de n-gramas operativa | Umbral sin calibrar; requiere ≥2 productos reales distintos |
| T7 Aprendizaje nuevo | HUMANA | — | Hallazgos nuevos para dirección AHT: solo con datos reales y revisión ciega |
| T8 Abogado del diablo | PARCIAL | Búsqueda contraria por hipótesis y exigencia de «cambia si»; un informe sesgado resulta DEFICIENTE | Objeciones sustantivas de un segundo modelo/experto |
| T9 Estabilidad | AUTO (determinista) | 3 ejecuciones idénticas en decisión, evidencias y texto | Estabilidad de un LLM real (no determinista) |
| T10 Predicción puntuada | PARCIAL + TEMPORAL | Se registra predicción medible y se calcula calibración | Calibración real: requiere ≥20 predicciones cerradas con resultados reales |

Regla de oro del diseño: si T1–T5 fallan, el informe no se presenta como análisis. Hoy pasan **con mocks**; con un modelo real deberán repetirse en F3.

## 7. Integración con Director, expedientes y seguimiento

- `POST consejero/dossier` guarda la investigación como expediente `consejero` en `k4_dossier` (misma tabla que el Director; entorno y veredictos incluidos).
- `proponer_decision` **rechaza** investigaciones SINTÉTICAS, con verificador RECHAZADO, adversarial DEFICIENTE o conclusión NO_CONCLUIBLE; las REAL quedan bloqueadas hasta F3 y autorización. No ejecuta nada externo.
- Cada investigación registra una predicción en `k4c_prediccion` (ventana en días) que alimenta la calibración (T10).
- Reutiliza el Director existente: no hay segunda aplicación ni segundo Director.

## 8. Riesgos y limitaciones

- El corpus es sintético y los extractos vienen etiquetados por el propio corpus: en F3 los hechos los extraerá un modelo y el verificador será más importante.
- El verificador es léxico/numérico: detecta errores evidentes, no sustituye la lectura humana.
- El redactor simulado no razona; las «trampas» prueban el verificador, no la honestidad de un modelo.
- Reglas de decisión simples (rango de comparables + datos internos); umbrales comerciales siguen sin aprobar.
- Con datos reales, el rango de comparables exige equivalencia de producto y formato: hoy solo 1 comparable de la comparativa K3 tiene precio vigente.
- Sin UI nueva por instrucción: el Consejero se consume por API y expedientes.

## 9. Plan F3 (proveedores reales, costes verificables, criterios de aceptación)

**Condición previa:** autorización expresa de José para gasto y activación; hoy 0 €.

| Pieza | Candidato | Coste público verificado | Nota |
|---|---|---|---|
| Búsqueda web | Brave Search API | 5 $ por 1.000 solicitudes; 5 $/mes de crédito incluido (brave.com/es/search/api, consultada hoy) | Requiere tarjeta; cobertura de derechos de almacenamiento aparte |
| Búsqueda + extracción | Tavily | 1.000 créditos/mes gratis sin tarjeta; PAYG 0,008 $/crédito; búsqueda básica 1 crédito (docs.tavily.com, hoy) | Alternativa/respaldo; extracción cuesta créditos adicionales |
| LLM | `ai.py` ya existente (OpenAI/Anthropic/compatible) | Precios en `ai.PRICES` (USD/1M tokens), **no reverificados hoy** → verificar en la página oficial antes de activar | Estimación previa en doc 02: ≈0,03 / 0,49 / 2,45 USD por investigación según modelo |
| Lectura de páginas | Lector con lista de hosts permitidos | 0 € (propio) | Respeta robots y límites; sin descargar archivos |

Presupuesto orientativo por investigación real (45 consultas del motor actual → se reducirá a ≈12–15 con deduplicación): búsqueda ≈0,06–0,23 $ con Brave más LLM 0,03–2,45 USD ⇒ **topes propuestos: 1 € por investigación, 20 € al mes, a fijar por José**.

**Pasos F3:** (1) adaptador Brave/Tavily detrás de `ProveedorBusqueda` con lista de hosts y caché; (2) lector real con extracción por modelo y reverificación literal del extracto; (3) activar `autorizacion_externa` solo por decisión humana, con topes en `k4c_cfg`; (4) repetir T1–T5 con modelo real y corpus real de ACTIVCORE; (5) T7/T8 con revisión ciega de AHT; (6) iniciar T10 con predicciones reales.

**Criterios de aceptación F3:** T1–T5 superadas con proveedores reales; 0 hechos sin cita verificable; ≥2 hallazgos nuevos verificables por informe según AHT; coste real ≤ tope en el 100 % de las investigaciones; ninguna llamada externa sin registro; el informe cambia de conclusión al cambiar la evidencia relevante; revisión humana de 3 informes sin errores de cita ni de cálculo.
