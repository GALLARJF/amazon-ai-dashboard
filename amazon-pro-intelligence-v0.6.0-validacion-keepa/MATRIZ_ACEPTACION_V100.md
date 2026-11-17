# Matriz de aceptación V1.0

Generada por tools/matriz_v100.py. Sin datos inventados; simulado ≠ real.

## VERIFICADO REAL (11)

| Requisito | Evidencia / causa | Propietario |
|---|---|---|
| Servidor HTTP + SQLite, auditoría encadenada, aislamiento de roles | suites v0.6/v0.7 locales (servidor y BD reales en Linux) | — |
| Interfaz NEON en Chromium real (Playwright), 5 secciones, capturas | ui_v07_test + capturas; solo Chromium/Linux | — |
| Keepa /token y /search dominio ES | docs_v06/evidencia_keepa_real (10 tokens consumidos) | — |
| GitHub: lectura, push, ramas, bloqueo de concurrencia por compare-and-swap | relevo_test 14/14 con remoto bare local; push real a GALLARJF/amazon-ai-dashboard | — |
| Google Drive: subida de partes de texto | partes publicados en AHT_AMAZON_PRO_AUTONOMIA | — |
| Tareas programadas: sesiones independientes (mínimo 1 h), no continuas | ejecución real de V7-02/03/04; cron */15 rechazado | — |
| Flujo PREPARAR Y LANZAR de extremo a extremo con persistencia tras reinicio | v100_lanzar_test 12/12: servidor y BD reales en Linux; el producto ACTIVCORE sigue NO DECIDIBLE por falta de datos | — |
| Exportaciones CSV/HTML/MD con trazabilidad y escapado | v100_export_test 14/14 con los 20 competidores reales de Keepa guardados | — |
| Copia de seguridad, restauración y arranque ante BD corrupta | v100_persistencia_test 16/16 sobre SQLite real en Linux | — |
| Interfaz sin desbordes a 390/820/1600 px y producto por defecto ACTIVCORE | ui_v100_test 44/44 en Chromium real (Linux); desborde a 820 px corregido | — |
| Documentación (manual, instalación) coherente con el producto | v100_docs_test 10/10 | — |

## VERIFICADO SIMULADO (7)

| Requisito | Evidencia / causa | Propietario |
|---|---|---|
| Director IA determinista, nunca GO por defecto | v070_director_test con datos Keepa reales guardados, sin IA generativa | — |
| Expediente comercial ACTIVCORE con huecos y desbloqueos | v070_expediente_test; economía NO CALCULABLE por falta de costes | — |
| Motor económico (econ6) y lanzamiento | suites v0.6 con datos de prueba | — |
| VENDER Y OPTIMIZAR con CSV importados (ACOS, TACoS, conversión, rechazos) | v100_vender_test 16/16 con CSV inventados solo para probar el cálculo; ningún informe real de Amazon importado todavía | — |
| Motor financiero: escenarios, sensibilidad y punto de equilibrio | v100_finanzas_test 20/20 con supuestos sintéticos; con datos reales de ACTIVCORE da NO CALCULABLE | — |
| Plan de especialistas del Director IA (/api/v07/plan) | v100_director_plan_test 14/14; hoy todo BLOQUEADO con datos reales; los escenarios desbloqueados son de prueba | — |
| Adaptadores SP-API y Ads API de solo lectura | v100_conectores_test 16/16 contra un servidor local; no se ha llamado a Amazon | — |

## IMPLEMENTADO NO VERIFICADO (0)

| Requisito | Evidencia / causa | Propietario |
|---|---|---|

## BLOQUEADO (6)

| Requisito | Evidencia / causa | Propietario |
|---|---|---|
| Keepa /product y dominios DE/FR/IT/UK | sin clave Keepa disponible y sin gasto autorizado | José: nueva clave en keepa.env local + autorizar tokens |
| OpenAI (IA generativa) | API de pago no autorizada | José: autorizar gasto y clave en ai.env local |
| Amazon SP-API y Ads API | sin credenciales ni permisos de vendedor | José/Sergio: autorizar app y permisos de solo lectura |
| Ejecución en Windows | no hay entorno Windows en la sesión; no se declara verificado | José: ejecutar la prueba en su PC |
| Evidencia regulatoria ACTIVCORE (cosmético UE) | requiere documentos del fabricante, no inventados | José/Laboratorios Klein |
| Costes, ventas y márgenes reales | sin datos reales aportados | Sergio/José: costes y precio objetivo |
