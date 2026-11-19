# K4 · Consejero — Informe de correcciones F2.1

> Proveedores SIMULADOS y datos SINTÉTICOS. 0 € de gasto, sin IA externa, sin credenciales, sin pantallas nuevas, sin merge ni despliegue. PR #4 abierto.

## 1. Corrección crítica: ACTIVCORE = 100 ml

**Origen del error (mío):** la ficha maestra K3 declara formato de 100 ml y 2 ml/día, es decir **50 días de duración**. Al preparar el escenario del Consejero confundí «50 días» con «50 ml» y lo propagué a: el valor por defecto del motor y de la API, el fixture de pruebas (`PROPIO`), el informe `05_F1F2_ENTREGA.md` (99,80 €/100 ml) y una línea de `docs_k4/K4_IMAGENES_INFORME.md` (iteración 2). El motor recalculaba correctamente un dato erróneo: el fallo era de dato, no de aritmética.

**Corregido:** escenario de referencia 49,90 € / 100 ml = **49,90 €/100 ml**; la API toma el dato de la **ficha maestra K3** (`own()`), no de un valor por defecto; `05_F1F2_ENTREGA.md` regenerado; línea de imágenes corregida. Los informes `04_INFORME_PROFUNDO` ya usaban 50 días correctamente.

**Control nuevo (coherencia con ficha maestra):** antes de investigar se compara volumen, PVP y precio normalizado declarados con la ficha maestra. Si hay discrepancia, o no hay ficha maestra, la investigación se **bloquea** (sin consultas, sin gasto, sin conclusión) hasta que una persona confirme con motivo (≥10 caracteres) qué dato prevalece; queda auditado. Además, el verificador comprueba que los datos de origen «maestro» de cada cálculo coinciden con la ficha (`DATO_MAESTRO_INCOHERENTE`), por si el dato se altera después.

### Demostración del bloqueo por dato maestro incorrecto

Entrada: precio 49,90 €, **volumen 50 ml** (erróneo); ficha maestra: 49,90 € / 100 ml.

- Estado: **BLOQUEADA_DATO_MAESTRO** · decisión: **BLOQUEADO** · gasto: 0.0 € · consultas realizadas: 0
- Discrepancia (volumen_ml): volumen_ml declarado (50.0) ≠ ficha maestra (100.0)
- Discrepancia (precio_100ml): precio normalizado distinto del de la ficha maestra
- Motivo mostrado: Discrepancia con la ficha maestra: volumen_ml declarado (50.0) ≠ ficha maestra (100.0); precio normalizado distinto del de la ficha maestra. No se investiga ni se concluye hasta confirmar el dato (usar ficha maestra o confirmar el declarado con motivo).
- Si el dato erróneo se inyecta después del control inicial, el verificador lo rechaza: **RECHAZADO** → DATO_MAESTRO_INCOHERENTE: el valor 50.0 de «volumen» no coincide con la ficha maestra (100.0)

## 2. Razonamiento no prefijado: cinco fases separadas

| Fase | Qué hace | Dónde |
|---|---|---|
| 1 Generación de hipótesis | Hipótesis por producto, categoría y problema; cada una declara qué la refutaría, consultas favorables y contrarias; admite `extensiones` configuradas (F3: propuestas por investigación real) | `k4c_fases.generar_hipotesis` |
| 2 Investigación | Búsqueda/lectura vía router; libro de evidencias | `k4c_engine` + `k4c_providers` |
| 3 Evaluación de evidencias | Puntúa favorables/contrarias por calidad; no decide el precio | `k4c_fases.evaluar_evidencia` |
| 4 Análisis económico | Solo hechos: precio normalizado, comparables **vigentes y equivalentes**, excluidos con motivo, posición frente al rango | `k4c_fases.analisis_economico` |
| 5 Recomendación | Reglas deterministas como CONTROL; la posición frente al rango nunca basta | `k4c_fases.recomendar` |

**Reglas de recomendación:** `BLOQUEADO` (dato maestro) · `NO_CONCLUIBLE` (faltan ≥3 comparables equivalentes vigentes o datos internos) · `DISENAR_EXPERIMENTO` (hay comparables y datos internos pero no se ha medido cómo responde la demanda al precio) · `SUBIR/BAJAR/MANTENER` **solo** con elasticidad medida (≥8 observaciones, con fuente) y precio óptimo de margen calculado y verificado. El verificador rechaza `SUBIR/BAJAR/MANTENER` sin esa evidencia (`RECOMENDACION_SOLO_POR_RANGO`).

| Escenario sintético | Posición vs rango | Decisión | Motivo |
|---|---|---|---|
| Sin datos internos, 1 comparable | por encima del rango | **NO_CONCLUIBLE** | Faltan ≥3 comparables vigentes y equivalentes (hoy 1) y ventas y margen unitario internos. |
| +2 comparables y datos internos, sin elasticidad | dentro del rango | **DISENAR_EXPERIMENTO** | El precio propio está dentro del rango (44.38–116.67 €/100 ml), pero la posición frente a la competencia no indica en qué sentido mover el precio: fal |
| Precio 150 € (fuera del rango), sin elasticidad | por encima del rango | **DISENAR_EXPERIMENTO** | El precio propio está por encima del rango (44.38–116.67 €/100 ml), pero la posición frente a la competencia no indica en qué sentido mover el precio: |
| Competidores no equivalentes (masivo) | por encima del rango | **NO_CONCLUIBLE** | Faltan ≥3 comparables vigentes y equivalentes (hoy 1). |
| Con elasticidad −2,0 (n=12) | dentro del rango | **SUBIR** | Con elasticidad medida e=-2.00 y coste variable 29.90 €, el precio óptimo de margen es 59.80 € (+20 % vs actual). |

Excluidos del rango por no equivalentes o no vigentes (escenario de no equivalentes): Ficha Beta tratamiento capilar (histórico); Ficha Epsilon champú (categoría no equivalente: COSMETICO_CAPILAR_MASIVO); Ficha Zeta spray (categoría no equivalente: COSMETICO_CAPILAR_MASIVO)

### Hipótesis distintas: ACTIVCORE frente a PhiVital Magnesio

| ACTIVCORE (cosmético capilar, normaliza por 100 ml) | PhiVital Magnesio (suplemento oral, normaliza por dosis diaria) |
|---|---|
| **H0** El precio premium de ACTIVCORE se sostiene por la evidencia de sus ingredientes (cafeina, luteolina). | **S0** La forma química de magnesio bisglicinato de PhiVital Magnesio (biodisponibilidad, tolerancia) sostiene un precio superior al magnesio básico. |
| **H1** La evidencia del ingrediente no se traslada a la fórmula final y no justifica por sí sola un sobreprecio. | **S1** La dosis diaria aportada y los límites de ingesta determinan qué se puede alegar y cuántas unidades por día se recomiendan; el precio por envase no es comparable sin la dosis. |
| **H2** El mercado comparable vigente (cosméticos capilares premium equivalentes) fija un rango de precio por 100 ml del que ACTIVCORE puede quedar dentro o fuera; el rango no decide por sí solo. | **S2** El precio por dosis diaria y por mg de magnesio elemental de los comparables vigentes y equivalentes (capsulas, polvo, comprimidos) fija el rango relevante; precio por envase o por 100 ml no es la métrica. |
| **H3** Minoxidil es un sustituto terapéutico indirecto que condiciona la disposición a pagar, no un competidor cosmético equivalente. | **S3** La demanda se reparte con sustitutos (alimentos ricos en magnesio, magnesio de farmacia) que fijan una referencia de coste diario mucho menor. |
| **H4** La clasificación regulatoria depende de la presentación completa, la composición y las alegaciones (crecimiento capilar, anticaida); una alegación de crecimiento puede cambiarla. | **S4** Como complemento alimenticio solo pueden usarse alegaciones de salud autorizadas (fatiga, funcion muscular) y existen restricciones de marketplace para suplementos. |
| **H5** No se pueden inferir ventas reales a partir del BSR ni atribuir causalidad a correlaciones de BSR y precio. | **S5** La demanda de magnesio es estacional y está dominada por reseñas y recompra; el BSR no permite inferir ventas ni la recompra. |

Consultas de ejemplo — ACTIVCORE: «cafeina topica evidencia ingrediente ensayo revision», «bsr ranking ventas demanda unidades metodo» · PhiVital: «magnesio bisglicinato biodisponibilidad humana ensayo», «magnesio capsulas precio por dosis diaria». No comparten ids, textos ni consultas (prueba automática). Una categoría desconocida usa una plantilla genérica propia (G0–G2), no las de otro producto. PhiVital Magnesio no tiene ficha maestra cargada: su investigación quedaría BLOQUEADA hasta cargarla.

## 3. Presupuesto seguro (sin activar proveedores externos)

Reserva **atómica** (una sola sentencia `INSERT…SELECT` condicionada a los topes: segura entre hilos y procesos) · tope por operación, por investigación y por mes (todos 0 € por defecto) · coste máximo por operación · conciliación del coste real · reintentos con espera y liberación de reservas fallidas · timeout con retención conservadora del máximo (`INCIERTA`) · corte automático al alcanzar el límite o si el coste real supera el máximo · `reanudar` solo por admin con motivo · todo en `k4c_reserva` y `k4c_consulta` y en la auditoría encadenada.

### Demostración del control de presupuesto concurrente

40 hilos simultáneos, cada llamada con coste estimado 0,10 €, tope por investigación y mes 1,00 €, tope por operación 0,20 €:

- Ejecutadas: **10** · bloqueadas por presupuesto: **30**
- Gasto conciliado: **1.00 €** (nunca supera el tope) · reservas por estado: CONFIRMADA=10
- Corte automático activo: **True** (límite de gasto alcanzado)
- Coste real superior al estimado (estimado 0,10 €, real 0,35 €): reserva **EXCEDIDA**, real conciliado 0.35 €, corte automático **True**.

## 4. Predicciones y aprendizaje

Una predicción registra: hipótesis, predicción original, métrica, periodo, valor inicial y entorno. **No se puede cerrar con un booleano**: exige valor observado numérico, fuente del resultado, método de evaluación, incertidumbre y fecha posterior al fin de la ventana. Se evalúa el cambio relativo con su intervalo; si el intervalo cruza el umbral → `INCONCLUSA` → revisión humana (actor, decisión y nota ≥10 caracteres). Las predicciones **REAL** siempre pasan por revisión humana. La calibración se calcula **por entorno**: las SINTÉTICAS nunca entran en la calibración comercial REAL.

## 5. Pruebas

`tests/k4c_test.py`: **{'ok': 10, 'bloq': 30}** (incluye T1–T10 y las pruebas adicionales: volumen erróneo, precio/100 ml incorrecto, categorías no equivalentes, recomendación solo por rango, presupuesto concurrente, coste real > estimado, predicciones sin evidencia, separación sintético/real, hipótesis por categoría).
Las regresiones K2/K3/K4, QA completo y CI se indican en el cierre del PR.

## 6. Estado de T1–T10 tras F2.1

Sin cambios de fondo: T1–T5 y T9 automatizadas con mocks; T6/T8/T10 parciales; T7 humana. T10 es ahora más estricta (evidencia de resultado y revisión). **Siguen sin demostrar razonamiento autónomo real.**

## 7. Propuesta de piloto F3 limitado

**Alcance:** una sola investigación real de ACTIVCORE (precio 49,90 € / 100 ml, formato validado con la ficha maestra) con tope total **5 €** (a confirmar por José), sin tocar Amazon ni producción, 1 proveedor de búsqueda y 1 modelo, 10 días.

| Elemento | Propuesta | Coste verificable |
|---|---|---|
| Búsqueda | Brave Search API (alternativa: Tavily, 1.000 créditos/mes gratis sin tarjeta) | 5 $ por 1.000 solicitudes; ≈ 0,005 $ por búsqueda; 5 $/mes de crédito incluido (brave.com/es/search/api, consultada el 19-11-2026) |
| Modelo | uno solo, de gama baja/media, vía `ai.py` ya existente | `ai.PRICES` **no reverificado**: confirmar precio oficial antes de activar |
| Lectura | lector propio con lista de hosts | 0 € |
| Topes | por operación 0,05 €, por investigación 2 €, mes 5 € | los aplica el router (reserva atómica + corte) |

**Pasos:** (1) José autoriza por escrito proveedor, modelo y topes; (2) clave en el servidor (nunca en repo/chat); (3) activar `autorizacion_externa` solo para esa investigación; (4) ficha maestra validada; (5) ejecutar con registro completo; (6) revisión humana del informe y de cada cita; (7) desactivar y conciliar el gasto real.

**Criterios de aceptación:** gasto real ≤ tope y conciliado con el proveedor; 0 hechos sin cita verificable; 0 errores de cálculo; T1–T5 repetidas con el modelo real; el informe cambia de conclusión al añadir/quitar evidencia relevante; ≥2 hallazgos nuevos verificables para AHT (T7); ninguna llamada fuera del registro; hipótesis alternativas propuestas por la investigación (no solo las de la plantilla); predicciones registradas con valor inicial para seguimiento.

**No incluye:** más de una investigación, páginas con login, descargas, acciones comerciales, ni cambio de precios reales.
