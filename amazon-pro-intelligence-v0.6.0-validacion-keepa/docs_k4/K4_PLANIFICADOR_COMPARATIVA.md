# K4 · Planificador y autonomía fiable: comparativa A/B/C
Criterio central: **ejecutar informes a intervalos no es una dirección comercial autónoma.** La autonomía exige: detectar sobre datos reales → investigar → proponer → registrar decisión → medir resultado, con garantías de ejecución única y recuperación. Hoy esas garantías existen parcialmente en `ops.py` (cola con prioridad, dedupe, reintentos, `recover()`, políticas, kill-switch); falta quien las dispare dentro del servidor.

| Criterio | A. Hilo planificador en el proceso web | B. Servicio programado independiente (Render Cron Job / Background Worker) | C. Infraestructura ya disponible |
|---|---|---|---|
| Qué es | Un hilo daemon que, cada N s, reclama tareas vencidas en SQLite y las ejecuta con `Ops.run_next` | Proceso/contenedor aparte que arranca el mismo código contra la misma base | (C1) la tarea programada actual que abre una sesión cada 4 h; (C2) GitHub Actions programado llamando a la API |
| Persistencia | Tareas y latidos en SQLite (`tasks6`, nueva `k4_jobs`) en el disco persistente | Debe compartir la base: **un disco de Render solo se monta en un servicio** ⇒ B no puede leer la misma SQLite sin migrar a otra BD o exponer una API interna | Estado en repositorio/AUTONOMIA (C1) o ninguno (C2) |
| Reinicios/despliegues | El hilo muere con el proceso; al arrancar `recover()` repone tareas «en curso»; **durante un despliegue pueden coexistir dos instancias unos segundos** ⇒ necesita *lease* | Aislado del ciclo de despliegue web | C1 no corre entre sesiones; C2 depende de cron de GitHub (retrasos habituales) |
| Duplicaciones | Evitables con `dedup` por clave+ventana y *lease* con caducidad (`UPDATE … WHERE lease<now`) | Igual, más riesgo de dos escritores | C1/C2 no tienen exclusión mutua con el servidor |
| Concurrencia | SQLite WAL + `store.lock` ya serializan escrituras; *lease* por job | Dos procesos escribiendo en SQLite ⇒ solo si comparten fichero (no posible en Render) | No aplica |
| Recuperación | Reintentos con backoff y clasificación de error (existentes); watchdog propio | Reinicio automático de Render | Manual |
| Monitorización | Latido en `events6` + endpoint de salud; alerta si el latido > 2× intervalo | Logs de Render; sin latido compartido | C1 ya existe y podría verificar `/healthz` y la edad del latido |
| Coste | 0 € adicional (la instancia Starter ya está siempre activa) | Servicio adicional: **coste no verificado en esta auditoría** (los Cron/Worker de Render se facturan aparte) y exigiría cambiar de SQLite | 0 € (C1 ya en marcha; C2 dentro de cuota gratuita, no verificado) |
| Riesgos | Un fallo del job puede afectar al proceso web (mitigación: hilo con excepciones aisladas, límites de tiempo, no ejecuta acciones externas) | Complejidad y coste; sincronización de datos | Frecuencia baja y no determinista; depende de sesiones; necesita credenciales para llamar a la API |

## Decisión propuesta (con justificación)
**A como planificador principal + C1 como vigilante externo.**
1. **A** es la única opción que comparte la base de datos sin coste ni migración. Se blinda con: *lease* por job (`lease_until`, `owner`), claves de deduplicación por ventana, un solo hilo ejecutor, tiempo máximo por job, `recover()` al arrancar, kill-switch y límites de `policies6` consultados antes de cada ejecución, y **lista cerrada de jobs internos** (lectura, cálculo, informes, creación de tareas); ningún job puede llamar a acciones externas.
2. **C1** (la tarea de las 4 h) comprueba `/healthz` y la **edad del latido** del planificador y deja un incidente en `AUTONOMIA/` si está parado: es monitorización independiente, no el motor.
3. **B** queda como plan de escalado si el volumen o los jobs pesados lo exigen (requiere migrar SQLite a una BD gestionada; decisión de coste futura).
Estado: **comparativa y decisión documentadas; el planificador definitivo se implementa en la iteración 2** (P2, tras aprobación). Esta iteración sí incluye el ciclo **detectar → investigar → proponer → registrar → medir** ejecutable bajo demanda y con tareas internas (`k4_director`), sobre el que se montará el planificador.
