# INFORME V1.0.0-candidata — Amazon Pro Intelligence

Generado desde el estado del coordinador. **CANDIDATA: no es producción.** Hay integraciones críticas sin conectar y Windows sin verificar.

## Qué incluye

- Flujo PREPARAR Y LANZAR de extremo a extremo (orden → tareas → decisión humana → persistencia tras reinicio), probado con servidor real.
- VENDER Y OPTIMIZAR con informes CSV importados (marcados IMPORTADO; ACOS y TACoS exactos; duplicados y archivos hostiles rechazados).
- Motor financiero determinista: escenarios, sensibilidad y punto de equilibrio (`backend/finanzas100.py`); lo que falta es NO CALCULABLE.
- Exportaciones CSV/HTML/Markdown con trazabilidad y escapado seguro: `GET /api/v07/export`.
- Plan de coordinación de especialistas del Director IA, sin GO por defecto: `GET /api/v07/plan`.
- Persistencia: respaldo con hash, restauración verificada y arranque que se niega con BD corrupta sin tocarla.
- Interfaz NEON comprobada en Chromium real a 390, 820 y 1600 px (corregido un desborde a 820 px).
- Adaptadores de solo lectura SP-API y Ads API, **probados solo con simulación local**.
- Relevo autónomo con bloqueo de concurrencia y commit controlado; sesiones cada 4 horas (independientes, no continuas).

## Objetivos V1.0 (estado real)

| Clave | Estado | Intentos | Resultado |
|---|---|---|---|
| V1-01 | HECHO | 1 | aceptación OK: 14/14 OK |
| V1-02 | HECHO | 1 | aceptación OK: 6/6 OK |
| V1-03 | HECHO | 1 | aceptación OK: 12/12 OK |
| V1-04 | HECHO | 1 | aceptación OK: 16/16 OK |
| V1-05 | HECHO | 1 | aceptación OK: 20/20 OK |
| V1-06 | HECHO | 1 | aceptación OK: 14/14 OK |
| V1-07 | HECHO | 1 | aceptación OK: 14/14 OK |
| V1-08 | HECHO | 1 | aceptación OK: 16/16 OK |
| V1-09 | HECHO | 1 | aceptación OK: 44/44 OK |
| V1-10 | HECHO | 1 | aceptación OK: 6/6 OK |
| V1-11 | HECHO | 1 | aceptación OK: 10/10 OK |
| V1-12 | HECHO | 1 | aceptación OK: 16/16 OK |
| V1-13 | HECHO | 1 | aceptación OK: 16/16 OK |
| V1-14 | HECHO | 1 | aceptación OK: 37/37 OK |

## Matriz de aceptación (resumen)

- VERIFICADO REAL: 13
- VERIFICADO SIMULADO: 7
- IMPLEMENTADO NO VERIFICADO: 0
- BLOQUEADO: 7

Detalle en `MATRIZ_ACEPTACION_V100.md`.

## Pruebas (qué se probó)

| Suite | Clase | Estado | Resultado |
|---|---|---|---|
| keepa-cliente | MOCK | PASA | 27/27 OK |
| keepa-misión | MOCK | PASA | 18/18 OK |
| keepa-flujo-Director | MOCK | PASA | 16/16 OK |
| keepa-evidencias-reales | REAL-EVIDENCIA | PASA | 9/9 OK |
| v0.6-operación | MOCK | PASA | 74/74 OK |
| v0.5-catálogo | MOCK | PASA | 43/43 OK |
| API | MOCK | PASA | 51/51 OK |
| lanzador | LOCAL | PASA | 9/9 OK |
| UI-v0.6 | MOCK+NAVEGADOR | PASA | 27/27 OK |
| v0.7-keepa-real | REAL-EVIDENCIA | PASA | 21/21 OK |
| v0.7-expediente | MOCK | PASA | 41/41 OK |
| v0.7-director | MOCK | PASA | 29/29 OK |
| v0.7-seguridad | MOCK | PASA | 23/23 OK |
| UI-v0.7 | MOCK+NAVEGADOR | PASA | 31/31 OK |
| desarrollo | LOCAL | PASA | 9/9 OK |
| relevo | LOCAL | PASA | 14/14 OK |
| v1.0-matriz | LOCAL | PASA | 6/6 OK |
| v1.0-lanzar | MOCK | PASA | 12/12 OK |
| v1.0-vender | MOCK | PASA | 16/16 OK |
| v1.0-finanzas | MOCK | PASA | 20/20 OK |
| v1.0-export | MOCK | PASA | 14/14 OK |
| v1.0-persistencia | MOCK | PASA | 16/16 OK |
| v1.0-ficha | MOCK | PASA | 6/6 OK |
| v1.0-ui | MOCK+NAVEGADOR | PASA | 44/44 OK |
| v1.0-plan | MOCK | PASA | 14/14 OK |
| v1.0-conectores | MOCK | PASA | 16/16 OK |
| v1.0-docs | MOCK | PASA | 10/10 OK |
| v1.0-entrega | LOCAL | PASA | 16/16 OK |
| v1.0-cloud | MOCK | PASA | 29/29 OK |
| v1.0-ui-cloud | MOCK+NAVEGADOR | PASA | 37/37 OK |
| v0.7-registro | LOCAL | PASA | 79/79 OK |
| v0.7-entrega | LOCAL | PASA | 15/15 OK |

Resumen: 32 pasan · 0 intermitentes · 0 fallan · 32 total. **MOCK = proveedores simulados, no integraciones reales.**

## Auditoría

- Fecha: 2026-11-17T16:21:53Z · Resultado: **OK**
- **Auditoría independiente: NO hubo.** No se dispuso de un segundo modelo autorizado y sin coste; la revisión fue determinista (regresión, escaneo de secretos, integridad del registro, pruebas negativas).

## Qué NO está verificado

- **Windows**: solo se probó en Linux; no se declara verificado.
- **Conexiones externas**: solo Keepa `/token` y `/search` (ES) tienen llamada real. SP-API, Ads API y OpenAI **no** están conectados; sus pruebas son simuladas.
- Comparabilidad de competidores automática, no confirmada por una persona; precios con fecha. Costes, ventas y evidencia regulatoria reales: sin datos.
- Protección de la rama en GitHub: no se pudo activar desde la sesión.

## Bloqueos externos (decisión del propietario)

- **Keepa /product y DE/FR/IT/UK** — BLOQUEADA (sin clave; solo ES /search verificado) → Entregar la clave en keepa.env y autorizar un tope de tokens
- **OpenAI (IA generativa)** — BLOQUEADA (API de pago no autorizada) → Autorizar gasto máximo mensual y crear la clave
- **Amazon SP-API (pedidos, inventario, catálogo)** — ADAPTADOR SOLO LECTURA IMPLEMENTADO (probado solo con simulación local) · NO CONECTADO → Registrar la app en Seller Central y autorizarla en solo lectura
- **Amazon Ads API** — ADAPTADOR SOLO LECTURA IMPLEMENTADO (probado solo con simulación local) · NO CONECTADO → Solicitar acceso a la Ads API y autorizar el perfil
- **Windows (ejecución del servidor y la UI)** — NO VERIFICADO (la sesión es Linux) → Ejecutar python server.py en tu PC y lanzar tests/run_all.sh equivalente; enviar el resultado
- **Costes, precio objetivo y ventas reales** — SIN DATOS → Sergio/José: aportar costes y precio objetivo por producto (ficha del producto)
- **Evidencia regulatoria cosmética ACTIVCORE** — SIN EVIDENCIA → Laboratorios Klein / responsable: informe de seguridad, PIF, notificación CPNP
- **Imagen Docker construida y despliegue cloud persistente (Render Starter + disco 1 GB)** — PREPARADO, NO DESPLEGADO (7,25 USD/mes; no existe opción gratuita con disco persistente) → Autorizar el gasto de 7,25 USD/mes, crear la cuenta de Render con tarjeta y aplicar el Blueprint
- **Protección de la rama en GitHub** — NO PUDE CONFIGURARLA (el proxy no permite escribir en esa API) → Activar protección para aht-v100-desarrollo: sin force-push ni borrado

## Límites respetados

- Gasto 0 € · 0 tokens Keepa adicionales · 0 llamadas a OpenAI y APIs de pago · sin publicación en Amazon · sin despliegue · sin credenciales en el repositorio · sin `git push --force`.

## Conexiones

- Keepa /token y /search ES: REAL VERIFICADO (PARCIAL) (real)
- GitHub GALLARJF/amazon-ai-dashboard (lectura/clonado): VERIFICADO (real)
- GitHub (escritura/push): BLOQUEADO 403 (no real)
- Google Drive (lectura): VERIFICADO (real)
- Entorno cloud (Python, terminal, Playwright): VERIFICADO (real)
