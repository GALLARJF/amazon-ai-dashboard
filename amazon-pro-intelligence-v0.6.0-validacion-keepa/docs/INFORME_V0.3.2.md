# Amazon Pro Intelligence V0.3.2 — Preparación final para la primera llamada real

**Estado: lista para la primera llamada, SIN haberla hecho.** No hay clave, no se ejecutó ninguna llamada de pago ni a `api.openai.com` (la suite lo impide y lo verifica; el camino «REAL» se probó con `_post` parcheado sin red). **No se declara IA real.** Todas las conexiones Amazon siguen desactivadas («Conectores habilitados: NINGUNO») y la interfaz horizontal NEON no cambia (solo etiqueta de versión y la línea de estado del Director).

## 1. Auditoría del presupuesto (hallazgos en V0.3.1)
| # | Hallazgo | Evidencia | Gravedad |
|---|---|---|---|
| 1 | **Carrera de presupuesto**: el gasto del mes se leía antes de llamar y se escribía después | Reproducido con 5 análisis simultáneos y presupuesto para 1 peor caso (0,002 USD vs 0,00138 por llamada): **llegaron 5 peticiones al proveedor** | Alta |
| 2 | El consumo se deducía de los registros `ai_run`: un timeout o un 5xx no dejaba rastro de coste | Revisión de código | Alta |
| 3 | Sin límite de llamadas simultáneas ni protección ante doble clic | Revisión | Media |
| 4 | Un reinicio en mitad de una llamada perdía la reserva | Revisión | Media |
| 5 | Reintentos: **no existen** reintentos automáticos (urllib, una sola petición) | Test: 1 petición por llamada en 4xx/5xx/timeout | Info (correcto; se blinda con test) |

## 2. Reserva atómica (corregido)
- **Libro `ai_budget` en SQLite.** `reserve()` comprueba y descuenta en **una sola operación** (`BEGIN IMMEDIATE` + cerrojo): comprometido = facturado real + peor caso de lo reservado o incierto. Peor caso = entrada estimada + `MAX_OUT` (incluye razonamiento) a tarifa de lista. Válido también con varios procesos sobre la misma BD.
- **Límite de simultaneidad** `AMAZON_PRO_AI_MAX_CONCURRENT` (defecto 1, máx. 4, por proceso): el resto queda «SIN IA · IA_OCUPADA», sin colas ni reintentos.
- **Pruebas:** 60 hilos reservando 0,01 con presupuesto 0,2 → exactamente 20; 6 análisis simultáneos con presupuesto para 2 → **2 peticiones** (antes 5); con concurrencia 1 → 1.
- Reservas REAL y locales/de prueba se contabilizan por separado: solo las REAL consumen el presupuesto real.

## 3. Timeouts, errores HTTP y consumo incierto
| Resultado | Estado del libro | Razón |
|---|---|---|
| 200 con `usage` válido | **liquidado** con tokens reales × tarifa | consumo conocido |
| 200 incompleto | liquidado (parcial) | el uso viene reportado |
| 200 sin `usage`, no-JSON o inesperado | **incierto** (se retiene el peor caso) | se cobró algo, cuánto no se sabe |
| 400/401/403/404/429 | **liberado** | petición rechazada, no se factura (supuesto estándar; ver §8) |
| 408/409/5xx | **incierto** | pudo procesarse |
| timeout / reset | **incierto** | idem |
| conexión rechazada / DNS | liberado | nunca llegó |
| reinicio con reserva en vuelo | **incierto** | proceso caído |
El incierto sigue descontando presupuesto hasta que el admin lo concilia con el panel de OpenAI (`POST /api/ai/reconcile {id, actual_cost}`, solo admin, auditado, solo reservas inciertas). La UI avisa «N consumo(s) INCIERTO(s)». Los cuerpos de error del proveedor no se guardan.

## 4. IDs y tarifas frente a la documentación oficial (re-verificado 2026-11-16)
Fuentes: <https://developers.openai.com/api/docs/pricing> y <https://developers.openai.com/api/docs/models>. Coinciden **exactamente** con el código (`tests/docs_match_test.py`, 15 comprobaciones contra `docs/oficial_snapshot_2026-11-16.json`):
| ID | Entrada | Salida | Razonamiento |
|---|---|---|---|
| gpt-6-luna | 0,10 | 0,50 | none…max |
| gpt-6.1-terra | 1,00 | 5,00 | none…max |
| gpt-6.1-sol | 2,00 | 10,00 | low…max (**sin none**) |
| gpt-6-astra | 10,00 | 50,00 | low…max (**sin none**) |
Novedades de V0.3.2: el código **rechaza** `REASONING=none` en Sol/Astra (no documentado) antes de llamar; el estado muestra la fecha de verificación de tarifas y avisa si superan 45 días. La documentación oficial solo cita la Responses API para estos modelos; no define instantáneas con fecha (el `model` de la respuesta se registra tal cual llegue). La página de precios **no tiene fecha de actualización** y sigue mencionando un precio promocional de «GPT-5.6 Sol» hasta el 30-nov que no concilia con `gpt-6.1-sol`: se usa la tabla. Recargos de endpoint regional/FedRAMP (+10 %) no aplicados (se usa el endpoint global).

## 5. Control de acceso a `/api/ai/usage` (probado por HTTP real en subproceso)
Sin sesión **401** · analista **403** · aprobador **403** · admin **200** · `POST` no permitido. `/api/ai/reconcile`: sin sesión 401, analista 403, id inválido 400. El estado público (`/api/ai/status`) devuelve solo `key_present`.

## 6. La clave nunca aparece (probado con una clave centinela)
Servidor lanzado en subproceso con la centinela; proveedor local «torpe» que **devuelve la cabecera `Authorization` en su cuerpo de error 401 y dentro de su texto de respuesta**. Buscada la centinela en: salida del servidor (stdout/stderr), **todas** las respuestas HTTP y cabeceras (todos los roles y endpoints), la base de datos y su WAL (registros, auditoría), y **todos los archivos del proyecto** (código, docs, demos, exportables): **0 apariciones**. Defensa añadida: si un proveedor devolviera la clave en su texto, se sustituye por `[CLAVE-OCULTA]` antes de guardar o mostrar. Los exportables de la app (paquete de integración, CSV) se construyen desde registros y resúmenes sin acceso a la configuración de IA.

## 7. Expediente sintético único y guardia de primera llamada
- `SINTÉTICO · Magnesio PRUEBA`, en la cuenta `sintetico-primera-llamada` (titular «SINTÉTICO — sin titularidad real», sin marketplaces), creado una sola vez al arrancar. 100 % ficticio; deja un dato pendiente a propósito (vídeo) para comprobar que la IA lo declara y no lo inventa. Su decisión determinista actual es **GO sobre datos ficticios: no es una recomendación comercial**.
- **Guardia:** mientras no exista una ejecución REAL **sin error y con tokens reportados por el proveedor**, a OpenAI solo puede viajar ese expediente y solo si su huella SHA-256 no cambió (PHIVITAL o cualquier otro queda en «SIN IA · PRIMERA_LLAMADA_SOLO_SINTETICO»). PRUEBA_LOCAL, SIMULADA, errores o tokens estimados **no** la levantan. Tras la primera verificación se levanta sola.
- `tools/preflight_primera_llamada.py`: sin red y sin gasto, muestra estado, guardias, peor caso de la llamada (≈ 0,0014 USD con Luna) y el **texto exacto** que se enviaría (`demos/preflight_*.txt`).

## 8. Límites y supuestos que no puedo verificar sin tu clave
1. Que 4xx no se facturan (práctica estándar; si no fuera así, el panel de OpenAI lo mostrará y se concilia). 2. Los nombres de campo de uso (`usage.input_tokens/output_tokens`): si difirieran, la llamada contaría como incierta (peor caso) y **no** verificaría la IA real. 3. Que tu cuenta tenga acceso a los IDs (`tools/check_openai_models.py --yes`). 4. El coste es estimación a tarifa de lista sin descuento de caché (conservador). 5. El mes se cuenta en UTC. 6. La simultaneidad se limita por proceso; el presupuesto es atómico aunque haya varios procesos.

## 9. Resultados de pruebas (todas sin consumo real) — `tests/resultado_ejecucion_final.txt`
JS 11+21+29+16 · paridad 657/657 · store 17 · backend 51 · OpenAI 50 · **presupuesto 29** · **docs 15** · **V0.3.2 32** · API 51 · seguridad 53 · esquema · UI 40. V0.1, V0.2 y V0.3.1 verificadas sin alteración (`docs/evidencia_integridad_V01_V02_V031.txt`).

## 10. Pendiente
Tu clave y tu autorización de gasto → primera llamada real con el sintético (`docs/ACTIVAR_API_OPENAI.md`). Datos documentados del piloto PHIVITAL y titular legal «POR CONFIRMAR» siguen pendientes.
