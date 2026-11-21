# Corrección 4.1 — conectores Amazon de solo lectura preparados técnicamente

Alcance: preparación técnica. **No hay conexión real, ni credenciales, ni push, ni deploy.** Todas las pruebas usan secretos falsos y transporte simulado (cero red; el socket externo está bloqueado en las pruebas).

## Resultado por bloqueo
| # | Bloqueo | Resultado |
|---|---|---|
| 1 | Variables unificadas `AMAZON_PRO_SPAPI_*` / `AMAZON_PRO_ADS_*` | Hecho en `server.py`, `backend/conectores100.py`, `/api/status`, guardia STAGING, `amazon_arch.py`, docs y pruebas. Prueba: ningún fichero conserva los nombres antiguos. |
| 2 | Token LWA temporal y cabeceras | SP-API: `x-amz-access-token`. Ads: `Authorization: Bearer` + `Amazon-Advertising-API-ClientId` + `Amazon-Advertising-API-Scope` (todo salvo `GET /v2/profiles`). El token se pide en cada lectura, vive en una variable local; `_cierra()` aborta si el token o un secreto aparece en la respuesta; URLs prefirmadas ocultas. |
| 3 | Capa de servicio real | `server.amazon_leer()` → `Conector.leer()`, expuesta en `GET /api/amazon/read` y `GET /api/amazon/ops` (sesión obligatoria, 20/min, auditoría `amazon.read`). `/api/connectors/test` usa la misma capa. |
| 4 | Doble activación | `AMAZON_PRO_CONNECTORS` + `AMAZON_PRO_LIVE_SPAPI` / `AMAZON_PRO_LIVE_ADS` = 1 + credenciales completas; si falta algo → 403 y 0 llamadas. |
| 5 | Solo lectura comercial | Operaciones en lista cerrada (pedidos, inventario, catálogo, finanzas, informes existentes, campañas/grupos/palabras en lectura). Sin listings, precios, inventario de escritura, campañas, pujas, presupuestos ni feeds. |
| 6 | Informes Ads | Se mantiene la importación CSV; no hay POST de creación de informes. |
| 7 | SP-API: parámetros, paginación, límites, 429, informes | Parámetros obligatorios validados; paginación (3 por defecto, tope 5; `NextToken`/`nextToken`/`startIndex`); tamaños de página acotados (100); 429 con espera `max(Retry-After, 2^n)` tope 30 s y 3 reintentos; informes existentes: listar, estado, documento y descarga (GET a `https://*.amazonaws.com`, gzip, 5 MB). Sin llamadas reales. |
| 8 | Pruebas | `tests/amazon_lectura_test.py`: **63/63** (ver abajo). |
| 9 | Captura Productos 1440 | **No se reproduce desplazamiento horizontal**: scrollX=0, ningún contenedor con scroll, `scrollWidth` 1425 ≤ 1425 (el ancho de ventana menos la barra vertical), borde izquierdo de las fichas a x=123 y cabecera a x=14, ninguna ficha recortada; igual si se llega desde el enlace del Director (con `scrollIntoView`). La impresión de «desplazada» procede de que el contenido tiene un ancho máximo de 1180 px centrado, mientras la cabecera ocupa todo el ancho (comportamiento común a todas las secciones). No se ha modificado el diseño. Prueba `tests/ui_prod_1440_test.py` 6/6 y captura `docs/p0_hoy/fase4_1/desktop/prod.png`. Si prefiere el contenido alineado a la izquierda con la cabecera, es un cambio de diseño que requiere su decisión. |

## Pruebas nuevas (`tests/amazon_lectura_test.py`)
Variables unificadas en código, estado, guardia STAGING y ficheros; cabeceras exactas SP y Ads (con y sin Scope); token LWA ausente en respuestas HTTP, stdout/stderr y auditoría; paginación limitada; 429 (Retry-After, tope, error final tras 3 reintentos); ningún POST salvo LWA (`_post` rechaza otras URLs, un único `method="POST"` en el código); ninguna ruta de escritura; parámetros obligatorios; descarga de informes; doble activación; staging con las variables definidas no arranca y sin ellas 403 y 0 conexiones externas; ruta interna `/api/amazon/read` que invoca realmente el adaptador.

## Ficheros modificados
`backend/conectores100.py` (reescrito), `server.py`, `backend/amazon_arch.py`, `tests/{amazon_lectura_test,ui_prod_1440_test}.py` (nuevos), `tests/{security,viewer,v100_conectores,amazon_arch,ui_fase4}_test.py`, `tests/run_all.sh`, `tools/coordinador.py`, `docs/p0_hoy/{AMAZON_INTEGRACION_FASE4,INFORME_FASE4,CORRECCION_FASE4_1}.md`.

## Pendiente / no autorizado
Conexión real, credenciales, despliegue y push. `?legacy=1` se conserva. Fallos heredados de la base (idénticos en 925dcb7): `security_test` 4 comprobaciones de Keepa y `v040` 43/45.
