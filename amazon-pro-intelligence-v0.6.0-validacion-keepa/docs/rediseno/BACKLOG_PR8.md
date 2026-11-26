# Backlog ejecutable PR #8 (rama `aht-rediseno-dashboard-global`)
Ruta: `amazon-pro-intelligence-v0.6.0-validacion-keepa/docs/rediseno/BACKLOG_PR8.md`. Fuentes: comentarios 7188957830 y 7192596626. Sin merge/deploy/gasto/tokens Keepa/escrituras Amazon. Estados: PENDIENTE · EN_CURSO · HECHO · BLOQUEADO.

## Prioridad 0 — Tarea periódica (HECHO: diagnóstico; cambio de configuración POR CONFIRMAR por José)
- Tarea: `trig_014XfTf2Q9xFiEzS79SCKLdd` «AHT autonomía V1.0», cron `3 */4 * * *`, sin tocar.
- Lee: rama de código `aht-v100-desarrollo` (HEAD fc51ee4, 18/11, anterior a PR5/7/8); estado en rama `aht-autonomia-estado` (`AUTONOMIA/estado.json`, `limites.json`); backlog = listas fijas `BACKLOG` y `BACKLOG_V1` en `tools/desarrollo.py` (todas HECHO) → «backlog vacío» (parte 0f39cc5, 20261126T120500; último 20:05 UTC).
- Causa: un comentario de GitHub no activa ni alimenta la tarea; no lee PR #8 ni ramas de PR5/7/8; el prompt solo clona `aht-v100-desarrollo`.
- Cambio necesario (José): (a) decidir si la tarea debe leer `docs/rediseno/BACKLOG_PR8.md` de esta rama o bien (b) mantener la tarea separada y dejar PR #8 solo para sesiones manuales. Para (a) hay que editar su prompt: clonar `aht-rediseno-dashboard-global`, leer este fichero, deduplicar comentarios PR8/PR7 por ID/SHA y respetar PARAR/bloqueo. No lo he modificado (no pedido explícitamente; evita ramas incompatibles simultáneas).

## Prioridad 1 — PR #8 (comentario 7188957830)
| ID | Objetivo | Aceptación | Estado |
|---|---|---|---|
| R1-01 | Gráficos individuales diferenciados en los 6 KPI (series demo explícitas; real = Sin datos) | test: 6 sparklines/gráficos distintos en demo; ninguno en real | HECHO |
| R1-02 | Chat vacío sin textos de ejemplo | test DOM | HECHO |
| R1-03 | Filtros: etiqueta AHT; Región Global/Europa/América; países ES FR DE IT US; CA/MX futuros configurables | test filtros | HECHO |
| R1-04 | Contexto de filtros al Director IA con contrato validado (servidor) | test API + UI | HECHO |
| R1-05 | Conservar borrador/chat y fullscreen al cambiar filtros; evitar carrera de respuestas asíncronas | test | HECHO |
| R1-06 | Notificaciones: fallo HTTP = «Sin datos»; alertas con evidencia, estado y contexto | test | HECHO |
| R1-07 | Selección vacía: contrato y rotulado «sin datos» coherente en todas las métricas | test | HECHO |
| R1-08 | Donut: contribución negativa no es segmento positivo; alternativa para pérdidas | test | HECHO |
| R1-09 | Pruebas con usuario autorizado y chat real con proveedor simulado; fullscreen por interacción real | tests | HECHO |

Notas: R1-01 modelo de dirección 26/11 (infográfico en ahtcorporativo@gmail.com) aplicado: iconos, variación DEMO, gráficos por KPI, donut con tabla, periodo como desplegable, pie «Datos simulados». R1-09 «chat real» = proveedor SIMULADO (mock), nunca IA real. Pendiente de confirmar con José: Benchmarking en cabecera (la orden lo pide; el modelo no lo muestra).

## Prioridad 2 — Benchmarking página completa
R2-01 prompt libre, adjuntos pendientes, ejecutar, resultados conversacionales, tablas/gráficos/informe, historial persistente + exportar, contexto producto/ASIN/país/periodo, fuentes con fecha y evidencia, estimado vs real, escenarios; reutilizar K3/K4 y Keepa sin llamadas reales; persistencia en SQLite actual (verificar backups). PENDIENTE.

## Prioridad 3
R3-01 pruebas dirigidas y capturas escritorio/móvil; R3-02 auditar cambios K1–K3 posteriores a 17/11; R3-03 plan de integración PR7/PR8 sin fusionar. PENDIENTE. Regresión amplia solo al final.
