# V0.6.0 — Informe de cambios, matrices, pruebas y bloqueos (2026-11-17)

## F0 · Protección y auditoría
- Backup verificado de V0.5.0: `BACKUPS/amazon-pro-intelligence-v0.5.0_BACKUP_20261117.tar.gz` (SHA-256 en `BACKUPS/SHA256SUMS.txt`, comparado con `diff -r`). V0.4.0.zip y anteriores intactos. V0.6.0 es una copia evolutiva (no una app paralela).
- Pruebas rojas: `ui_synth_test` 14/15 = defecto real (selector de cuenta por defecto elegía la cuenta de sistema del catálogo) → corregido. `budget_test` 28/29 = **no reproducible** (≥8 ejecuciones 29/29); causa no identificada, queda vigilada.
- **Defecto grave hallado y corregido (V0.5.0):** los productos no-ACTIVCORE heredaban el coste 10,03 € de ACTIVCORE en la economía europea. Ahora cada producto parte de SUS costes (o NO DISPONIBLE). Test de regresión incluido.
- Matriz de conexiones: ver `docs_v06/F0_AUDITORIA_Y_CONEXIONES.md` y pestaña MIS VENTAS.

## Matriz de funciones
| Fase | Función | Estado | Evidencia |
|---|---|---|---|
| F1 | Diseño NEON, 4 gráficos con pregunta/fuente/periodo/actualización/estado, estados honestos, DEMO separado | HECHO | ui_v06_test 27/27 + capturas 20–28 |
| F2 | 5 espacios, INICIO adaptado a prelanzamiento, Director como centro operativo | HECHO (Director conversacional = chat EU existente por producto) | ui_v06_test |
| F3 | Catálogo dinámico + SKU, composición, claims, estado comercial, conexiones Amazon | HECHO | v060_test |
| F4 | Expediente de lanzamiento (11 secciones), arranque automático al alta, listing/A+/FAQ/imágenes/vídeo/PPC/calendario en BORRADOR, claim-lint, cumplimiento cosmética vs suplementos, export MD/HTML | HECHO con datos reales disponibles = ninguno de mercado (SIN DATOS) | v060_test |
| F4 | Investigación europea con datos reales de Keepa | **BLOQUEADO**: nunca se ha hecho una llamada real; NL/PL/SE/BE/IE sin conector | matriz |
| F5 | Operación: importación de informes reales (CSV) con hash/fecha/cobertura; SP-API/Ads API | Importación HECHA · APIs NO IMPLEMENTADAS (PENDIENTE DE CONEXIÓN) | v060_test |
| F6 | 7 especialidades como herramientas bajo un Director (política por tarea) | PARCIAL: tareas de compliance, economía, descubrimiento, listing, expediente; SEO/PPC/creatividad como borradores deterministas; sin 7 agentes | código |
| F7 | Motor económico trazable (clases OBSERVADO…SINTÉTICO, ACoS equilibrio, TACoS, escenarios país, inventario) | HECHO; resultados NO CALCULABLES hasta aportar costes logísticos | v060_test |
| F8 | Tareas persistentes: cola, estados, reintentos limitados, deduplicación, recuperación tras reinicio, errores, presupuesto, auditoría, prioridad explicable | HECHO | v060_test |
| F9 | N1–N4, políticas N2, bandeja única agrupada, interruptor de emergencia | HECHO (aprobar = registrar; sin ejecución externa) | v060_test |
| F10 | Puerta de modelos: política por tarea, caché, presupuestos, 1 escalado máx., validadores independientes, registro, clasificación de errores, modelo fijado con evidencia | HECHO con proveedor **simulado**; sin llamada real | v060_test |
| F11 | Libro de decisiones (sin atribución automática ni cambio de políticas) | HECHO | v060_test |
| F12 | Conectores: Keepa (código, sin verificar), OpenAI (código, sin verificar), importadores | ver matriz | |
| F13 | Windows: lanzador, acceso directo, instancia única | Lógica probada en Linux; **no probado en Windows real** | launcher_test |
| F14 | Independencia + contratos | `INTEGRACION_EXECUTIVE_NEON_CONTRATOS_V1.md` (sin cambios de contrato; nuevos endpoints /api/v06/*) | |

## Pruebas (run_all.sh: TODAS LAS SUITES OK)
- v060_test 74/74 (incluye negativas: sin costes, claim no respaldado, sin comparables, datos contradictorios→importación rechazada/advertida, presupuesto agotado, reinicio durante tarea, acción no autorizada, Keepa sin tokens = sin llamada, IA real sin aprobación, rol analista, CSRF).
- ui_v06_test 27/27 (navegador real, 1600×900 y móvil 390 px). ui_test 40/40, ui_synth 15/15, ui_eu 18/18, v050 43/43, launcher 8/8, resto heredado verde.
- **Naturaleza de las pruebas:** todas son ejecución local REAL del código con proveedores SIMULADOS (mock). Ninguna toca Keepa, OpenAI ni Amazon reales. Windows real: no probado. Prueba negativa «tokens de Keepa insuficientes» e «API caída» cubiertas por keepa_test (heredada, simulada).

## Pendientes y bloqueos reales
1. Primera llamada real a Keepa/OpenAI: requiere tu autorización de gasto y claves colocadas por ti en ai.env/keepa.env (nunca en chat). Hasta entonces costes en tokens y códigos de dominio son supuestos.
2. Costes logísticos (transporte, preparación, tarifa FBA/FBM, almacenaje, devoluciones) y evidencias regulatorias de ACTIVCORE: aportar → economía y cumplimiento dejan de ser NO CALCULABLE.
3. SP-API y Ads API: no implementadas; requieren credenciales de vendedor y verificación de permisos.
4. NL/PL/SE/BE/IE: sin fuente autorizada conectada.
5. Windows real sin probar. `budget_test` intermitente sin causa identificada.
6. Chat del Director con IA real: usa el flujo V0.5 (por producto, con confirmación); no verificado con IA real.
7. Atribución/aprendizaje: solo registro; la calibración estadística no está implementada (exige datos reales acumulados).
