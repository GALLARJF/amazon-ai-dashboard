# Matriz de aceptación V1.0

Generada por tools/matriz_v100.py. Sin datos inventados; simulado ≠ real.

## VERIFICADO REAL (6)

| Requisito | Evidencia / causa | Propietario |
|---|---|---|
| Servidor HTTP + SQLite, auditoría encadenada, aislamiento de roles | suites v0.6/v0.7 locales (servidor y BD reales en Linux) | — |
| Interfaz NEON en Chromium real (Playwright), 5 secciones, capturas | ui_v07_test + capturas; solo Chromium/Linux | — |
| Keepa /token y /search dominio ES | docs_v06/evidencia_keepa_real (10 tokens consumidos) | — |
| GitHub: lectura, push, ramas, bloqueo de concurrencia por compare-and-swap | relevo_test 14/14 con remoto bare local; push real a GALLARJF/amazon-ai-dashboard | — |
| Google Drive: subida de partes de texto | partes publicados en AHT_AMAZON_PRO_AUTONOMIA | — |
| Tareas programadas: sesiones independientes (mínimo 1 h), no continuas | ejecución real de V7-02/03/04; cron */15 rechazado | — |

## VERIFICADO SIMULADO (3)

| Requisito | Evidencia / causa | Propietario |
|---|---|---|
| Director IA determinista, nunca GO por defecto | v070_director_test con datos Keepa reales guardados, sin IA generativa | — |
| Expediente comercial ACTIVCORE con huecos y desbloqueos | v070_expediente_test; economía NO CALCULABLE por falta de costes | — |
| Motor económico (econ6) y lanzamiento | suites v0.6 con datos de prueba | — |

## IMPLEMENTADO NO VERIFICADO (6)

| Requisito | Evidencia / causa | Propietario |
|---|---|---|
| Flujo PREPARAR Y LANZAR de extremo a extremo con persistencia | faltan prueba E2E y reinicio de servidor (V1-03) | — |
| VENDER Y OPTIMIZAR con CSV importados | importador existe; falta prueba de flujo completo (V1-04) | — |
| Exportaciones CSV/HTML/MD | md/json del expediente probados; CSV/HTML pendientes (V1-06) | — |
| Copia de seguridad/restauración y BD corrupta | pendiente V1-08 | — |
| Móvil: sin desbordes horizontales a 820 px (.hr/.sess) | defecto conocido preexistente (V1-09) | — |
| Producto por defecto ACTIVCORE (la captura mostró PHIVITAL Magnesio) | defecto conocido (V1-09) | — |

## BLOQUEADO (6)

| Requisito | Evidencia / causa | Propietario |
|---|---|---|
| Keepa /product y dominios DE/FR/IT/UK | sin clave Keepa disponible y sin gasto autorizado | José: nueva clave en keepa.env local + autorizar tokens |
| OpenAI (IA generativa) | API de pago no autorizada | José: autorizar gasto y clave en ai.env local |
| Amazon SP-API y Ads API | sin credenciales ni permisos de vendedor | José/Sergio: autorizar app y permisos de solo lectura |
| Ejecución en Windows | no hay entorno Windows en la sesión; no se declara verificado | José: ejecutar la prueba en su PC |
| Evidencia regulatoria ACTIVCORE (cosmético UE) | requiere documentos del fabricante, no inventados | José/Laboratorios Klein |
| Costes, ventas y márgenes reales | sin datos reales aportados | Sergio/José: costes y precio objetivo |
