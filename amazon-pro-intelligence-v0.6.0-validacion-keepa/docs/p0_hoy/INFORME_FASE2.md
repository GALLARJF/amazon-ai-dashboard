# Fase 2 — HOY ejecutivo · DECISIONES unificada · DIRECTOR IA simplificado

Base: `b49ce8b` (Fase 1 aprobada) · rama local `aht-p0-fase2` · sin push, sin deploy, 0 € de gasto, producción intacta.
No se tocan `server.py`, `backend/*`, contratos de API, cálculos, datos ni seguridad. Todo es capa de presentación sobre endpoints GET existentes
(`js/hoy.js`, `js/ro.js`, `index.html`, `styles.css`, `js/nav.js`). `?legacy=1` se mantiene (retirada en Fase 5, ver `PLAN_RETIRADA_LEGACY.md`).
La trazabilidad, la metodología y todos los controles heredados se conservan, movidos a segundo nivel (bloques plegados «Evidencia y metodología» / «Evidencia» / «Metodología»).

## Matriz de criterios de aceptación
Pruebas: **H** = `tests/ui_hoy_test.py` (121; viewer en staging; escritorio 1440, Android 390 y 360) · **M** = `tests/ui_hoy_modo_test.py` (23; admin, selector REAL/DEMO) · **V** = `tests/ui_viewer_ro_test.py` (3) · `viewer_test` (32) · `ui_viewer_test` (24) · `ui_nav_test` (118) · `ui_nav_modo_test` (17).

| # | Criterio | Estado | Evidencia |
|---|----------|--------|-----------|
| **HOY** | | | |
| 1 | Solo 6 bloques: situación, ventas, margen, stock y riesgos, decisiones, tres prioridades | CUMPLE | H: «exactamente los 6 bloques» (×3 viewports) |
| 2 | Sin rutas `/api/`, metodología ni detalles técnicos en primer nivel | CUMPLE | H: regex técnica sobre el primer nivel = 0 coincidencias; «Evidencia y metodología» plegada; abierta sí contiene `/api/` |
| 3 | Ausencia de datos ≠ 0 | CUMPLE | H: «ningún bloque SIN DATOS muestra un 0»; M: ventas/margen SIN DATOS sin importar informe; margen NO DETERMINABLE con ventas importadas |
| 4 | Identificar siempre REAL / DEMO / SIN DATOS | CUMPLE | H: 6 etiquetas válidas; en staging todo DEMO, nunca REAL; M: REAL / DEMO / SIN DATOS por bloque |
| 5 | «5 riesgos abiertos» por criticidad | CUMPLE | H y M: «5 riesgos abiertos: 0 críticos · 0 altos · 5 medios · 0 bajos» y la suma cuadra |
| 6 | Comprensión en < 30 s | CUMPLE (diseño; no se ha medido con personas) | Situación en una frase con semáforo arriba; en Android 390 cabe en la primera pantalla (H) |
| **DECISIONES** | | | |
| 7 | 8 campos por decisión: producto, prioridad, fecha límite, impacto estimado, responsable, evidencia, estado, acción recomendada | CUMPLE (con límite: ver «Límites») | H: 8 etiquetas, ningún campo vacío, ×(1 pendiente + 5 sugeridas) |
| 8 | Una sola bandeja | CUMPLE | Fuentes unificadas: aprobaciones del servidor, K4, cola local y riesgos por reglas; chip = botón de HOY = pestaña (H, M) |
| **DIRECTOR IA** | | | |
| 9 | Primero Conclusión y Decisión recomendada | CUMPLE | H: orden Conclusión → Decisión; Evidencia/Metodología después y plegadas |
| 10 | Máx. 3 decisiones prioritarias | CUMPLE | H: 1 ≤ n ≤ 3 |
| 11 | Sin detalles técnicos en primer nivel (modelos, tokens, llamadas, endpoints) | CUMPLE | H: regex técnica = 0; Centro operativo, modelos, tokens y llamadas solo dentro de Metodología (H abre y comprueba) |
| 12 | Diferencia regla determinista / cálculo / IA generativa | CUMPLE | H: leyenda con los 3 tipos; cada recomendación lleva su tipo; declara que la IA generativa no participa |
| 13 | Navegar de la recomendación al producto afectado | CUMPLE | H: «Ir al producto afectado» → Productos con el producto resaltado |
| 14 | Dice expresamente cuándo faltan datos | CUMPLE | H y M: «Datos insuficientes» + aviso explícito |
| 15 | Sin consultas de pago ni conectores externos | CUMPLE | H: 0 peticiones externas, 0 a order/run/import/Keepa; solo GET existentes |
| **VIEWER** | | | |
| 16 | Controles de escritura visualmente desactivados o rotulados | CUMPLE | V: 143 controles en 7 pantallas/16 sub-vistas, 0 activos o sin rótulo; control negativo con admin (20 activos). Hueco real encontrado y cerrado: chat y chips del Director (Panel DEMO), subida de archivos y etiquetas «Importar» |
| 17 | Bloqueos íntegros | CUMPLE | `viewer_test` 32/32; H: POST forzado → 403; servidor sin cambios |
| **MÓVIL** | | | |
| 18 | Sin tablas horizontales en HOY ni DECISIONES | CUMPLE | H: 0 `<table>` y `scrollWidth ≤ innerWidth` |
| 19 | Tarjetas de una columna | CUMPLE | H: misma columna y ancho completo (390 y 360) |
| 20 | Botones táctiles ≥ 44 px | CUMPLE | H: 0 botones/resúmenes < 44 px en HOY y DECISIONES |
| 21 | Barra inferior sin cubrir contenido | CUMPLE | H: HOY, DECISIONES y DIRECTOR; `ui_nav_test` con control negativo |
| 22 | Prioriza conclusión, decisión y alerta | CUMPLE | Situación (conclusión + alerta) en primera pantalla; decisión debajo |
| **RESTRICCIONES** | | | |
| 23 | No tocar producción / deploy / push / API / cálculos / datos / seguridad | CUMPLE | `git diff b49ce8b --stat`: solo `js/`, `index.html`, `styles.css`, tests, docs, CI |
| 24 | Mantener `?legacy=1` | CUMPLE | 10 suites heredadas siguen en modo legacy (verdes salvo 2 ya conocidas) |
| 25 | No avanzar a Fase 3 | CUMPLE | — |

## Regresión
`tests/run_all.sh`: todo OK salvo las 2 suites heredadas que ya fallaban antes de la Fase 1 (seguridad V0.2 49/53; API europea V0.4 43/45). Ningún fallo nuevo.
`ui_nav_test` 118/118 (el chip ahora abre DECISIONES), `ui_nav_modo_test` 17/17, `viewer_test` 32/32, `ui_viewer_test` 24/24 (legacy), `v070_registro_test` 99/99.

## Defectos encontrados y corregidos durante la fase
- El botón Aprobar/Rechazar de DECISIONES no enviaba el cuerpo JSON (`se requiere application/json`): detectado por `ui_hoy_modo_test`, corregido.
- HOY mostraba datos en caché al cambiar de modo REAL/DEMO o tras importar: ahora se relee en cada visita y por modo.
- Viewer: el chat del Director y sus chips seguían activos en el Panel DEMO; la subida de archivos y las etiquetas «Importar» no se veían bloqueadas. Corregido en `js/ro.js`.

## Límites y avisos (decisiones para la revisión)
1. **Fecha límite e impacto estimado**: la API no tiene esos campos. Se muestran «SIN FECHA LÍMITE DEFINIDA» y «NO DETERMINABLE» (con el motivo). No se inventan. Para mostrar valores reales haría falta un cambio de backend, fuera de esta fase.
2. **Prioridad**: derivada por regla (nivel N3 → ALTA; N4 → CRÍTICA; riesgos: ALTO → ALTA, MEDIO → MEDIA, BAJO → BAJA). Documentada en Metodología.
3. **Responsable**: la API no asigna responsables; se muestra el rol que puede decidir o «Sin asignar».
4. **Aprobar** una decisión de gasto Keepa hace lo mismo que antes: registra la decisión y lanza `run` (comportamiento heredado, solo con rol aprobador/admin). El viewer no puede (403 + botón desactivado).
5. **Staging**: el modo está forzado a DEMO, así que todo se rotula DEMO; el dataset de ventas/margen es el demo. Las capturas usan una decisión sintética sembrada en la BD temporal de la prueba.
6. **Cola local de propuestas**: se lee del panel local (solo registro; no ejecuta nada).
7. **Cabecera móvil**: ocupa unos 270 px antes del contenido; candidata a compactar en Fase 3/4.
8. El informe `AUDITORIA_EJECUTIVA_AMAZON_PRO_INTELLIGENCE_STAGING_E914144.md` mencionado como adjunto no ha llegado a mi entorno (tampoco en la Fase 1). No lo he podido consultar.
