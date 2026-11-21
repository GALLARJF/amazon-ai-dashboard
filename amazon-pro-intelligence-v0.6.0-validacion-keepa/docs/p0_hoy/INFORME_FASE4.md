# Informe · Fase 4 (final) — Amazon Pro Intelligence

**Rama local:** `aht-finalizacion-fase4` · **Base:** `925dcb7` (contiene completas las Fases 2, 2.1, 3 y 3.1; árbol limpio al empezar).
**Producción intacta:** ningún `git push` en el reflog, ninguna rama `aht-p0*` ni `aht-finalizacion*` en `origin`; no se ha desplegado nada ni se ha gastado nada (0 €; sin Keepa ni IA de pago).
**Detenido antes de push y de deploy.**

## 1. Qué se ha hecho
| Bloque | Resultado |
|---|---|
| **A · Ventas** (`js/ventas.js`) | Resumen ejecutivo: ventas, margen, publicidad (gasto/ACoS/TACoS), stock y alertas, cada cifra con REAL / DEMO / SIN DATOS. Conclusión y Decisión en primer nivel; Evidencia y Metodología plegadas. Sin rutas ni términos técnicos arriba. Móvil sin tablas horizontales. Un dato ausente es **SIN DATOS**, nunca 0. |
| **B · Productos** (`js/prod.js`) | Una ficha ejecutiva por producto: precio, coste, margen, inventario, ventas, publicidad, documentación y estado. ACTIVCORE (cosmética) y PHIVITAL (suplementos) en grupos, cabeceras y colores distintos. Margen **NO DETERMINABLE** mientras falten costes de Amazon; existencias históricas rotuladas como tales. «Ir al producto» desde el Director, Hoy y Decisiones abre y resalta la ficha. |
| **C · Administración** (`js/admin.js`) | Una sola pantalla con Aprobaciones, Conexiones, Historial y Auditoría. Arriba: operación diaria (por hacer hoy, decisiones, integridad de la auditoría, conexiones). Plegado: configuración técnica. Las pantallas originales (con toda su trazabilidad y seguridad) quedan dentro, intactas. Aviso de solo lectura para el viewer; no se añade ninguna escritura. |
| **D · Director IA** (`js/hoy.js`) | Máximo 3 decisiones; cada una con producto, impacto, evidencia, responsable, próxima acción y prioridad. Rotuladas «Regla determinista» o «Cálculo»; la leyenda define los tres tipos y declara que **no hay IA generativa** en el panel (nunca se presenta una regla como IA). Sin consultas de pago. |
| **E · Amazon** (`backend/amazon_arch.py`, `docs/p0_hoy/AMAZON_INTEGRACION_FASE4.md`) | Arquitectura declarativa SP-API (catálogo, pedidos, inventario, informes, tarifas, finanzas) y Ads API (campañas, palabras clave, gasto, ventas atribuidas, ACoS, ROAS). Desactivada por defecto, solo lectura, sin credenciales, sin llamadas reales. Variables de Render y proceso OAuth documentados. |
| **F · Legacy** | 10 suites migradas a la navegación nueva; paridad de 109 títulos de componentes (0 perdidos). **`?legacy=1` NO se retira**: ver §5. |

## 2. Criterios finales (verificados por prueba)
| Criterio | Resultado | Prueba |
|---|---|---|
| Pantallas a 1440, 390 y 360 px | ✔ | `ui_fase4_test` (174/174) en las 4 pantallas nuevas × 3 anchos |
| Sin desplazamiento horizontal | ✔ | idem (`scrollX=0`, `scrollWidth ≤ innerWidth`) |
| Controles táctiles ≥ 44 px | ✔ | idem (botones, cabeceras de acordeón y barra inferior) |
| REAL/DEMO/SIN DATOS inequívoco | ✔ | idem + `ui_hoy*`, `ui_nav_modo`, `ui_lanz_modo` |
| Viewer no puede escribir | ✔ | UI sin controles de escritura activos + POST → **403** (`/api/v06/decide`, `/api/approvals/decide`, `/api/catalog/update`, `/api/v06/order`) + `ui_viewer_ro_test` 3/3 |
| Cero llamadas externas en pruebas | ✔ | `ui_fase4_test` aborta y cuenta toda petición fuera de localhost: 0; `amazon_arch_test` bloquea `socket.connect` |
| Sin fallos nuevos de regresión | ✔ | §3 |
| Fallos heredados comparados con la base | ✔ | §3 |
| Sin cambiar contratos sin justificar | ✔ | §4 |
| No avanzar al despliegue | ✔ | sin push/deploy |

## 3. Regresión completa (`tests/run_all.sh`) — nueva vs. base `925dcb7`
Se ejecutó la batería completa en ambas rutas.
- **Fallos heredados (idénticos en base y en rama):** `seguridad (heredada V0.2)` 49/53 y `V0.4.0 API europea` 43/45. No se tocan.
- **En la base fallaban además** `V1.0 entrega candidata` (14/16) y `V0.7.0 entrega candidata` (KeyError) por el estado del árbol de trabajo; en la rama pasan (16/16 y 15/15).
- **Cambios de recuento esperados:** `ui_nav_test` 118 → 108 (Administración pasa de 3 sub-secciones a 1: desaparecen 10 comprobaciones de sub-pestañas); `ui_viewer_ro` 103 → 106 controles.
- **Nuevas:** `ui_fase4_test` 174/174 · `amazon_arch_test` 17/17 · `ui_legacy_paridad_test` 2/2.
- **Suites heredadas sin `?legacy=1`:** ui_test 40 · ui_v06 27 · ui_v07 31 · ui_k4 52 · ui_k3 37 · ui_eu 18 · ui_synth 15 · ui_v100 44 · ui_viewer 25 · ui_v100_cloud 37, todas OK.
- **Dos ejecuciones consecutivas** (criterio 2 del plan de retirada): `ui_nav_test` 108/108, `ui_nav_modo_test` 17/17, `viewer_test` 32/32, `ui_viewer_test` 25/25, ambas veces.

## 4. Contratos o pruebas existentes modificados (y por qué)
- `js/nav.js`: Administración pasa de 3 sub-secciones a 1 (unificación pedida). `ui_nav_test` y `ui_viewer_ro_test` se actualizan a ello.
- `js/hoy.js`: las decisiones del Director añaden campos (impacto, responsable, evidencia, próxima acción); `goProduct` abre la ficha nueva. Se conserva la frase «la IA generativa no participa… ni conectores externos» exigida por `ui_hoy_test`; ese test pasa a buscar la ficha en `#prod2`.
- `tests/ui_hoy_test.py`: el filtro de rutas que «gastan» ya no confunde `GET /api/v06/imports` (solo lectura, usado por las fichas) con `POST /api/v06/import`.
- `tests/ui_viewer_ro_test.py`: `Ver lanzamiento` / `Ir a Decisiones` se reconocen como navegación.
- `js/lanz.js`: se expone `LANZ2.select` (sin cambio de comportamiento) para que las pruebas heredadas elijan producto.
- `backend/conectores100.py`: la lista blanca de solo lectura incorpora `finances/*` y `v2/sp/{campaigns,adGroups,keywords}` (todo GET). Sin rutas de escritura (probado).
- `js/ro.js`: `[data-x4go]`/`[data-x4open]` en la lista de controles de navegación.
- Las 10 suites heredadas: se quita `?legacy=1` y se importa `tests/_nav_shim.py` (clic programático en `#tabs`, despliegue de `<details>`, reveal CSS de controles heredados). **No se elimina ninguna aserción.**

## 5. Retirada de `?legacy=1`: NO se retira
Cumplidos: criterio 1 (10 suites sin legacy), 2 (dos ejecuciones) y 3 (paridad de 109/109 títulos). **Pendientes exactamente:** criterio 4 (revisión de José de las Fases 2–4) y criterio 5 (regla de la Fase de retirada). Detalle y pasos en `PLAN_RETIRADA_LEGACY.md`.

## 6. Lista exacta de archivos modificados
**Nuevos:** `backend/amazon_arch.py` · `js/ex.js` · `js/ventas.js` · `js/prod.js` · `js/admin.js` · `tests/ui_fase4_test.py` · `tests/amazon_arch_test.py` · `tests/ui_legacy_paridad_test.py` · `tests/_nav_shim.py` · `docs/p0_hoy/INFORME_FASE4.md` · `docs/p0_hoy/AMAZON_INTEGRACION_FASE4.md` · `docs/p0_hoy/fase4/{desktop,android,android360}/*.png` (24 capturas).
**Modificados:** `.github/workflows/k4-ci.yml` · `backend/conectores100.py` · `index.html` · `js/hoy.js` · `js/lanz.js` · `js/nav.js` · `js/ro.js` · `styles.css` · `tools/coordinador.py` · `tests/run_all.sh` · `docs/p0_hoy/PLAN_RETIRADA_LEGACY.md` · `tests/ui_{test,v06,v07,k4,k3,eu,synth,v100,v100_cloud,viewer,hoy,nav,viewer_ro}_test.py` (según el caso).

## 7. Variables necesarias para conectar Amazon
Ver `AMAZON_INTEGRACION_FASE4.md` §3–4. En Render (secretos): `AMAZON_PRO_SPAPI_CLIENT_ID/SECRET/REFRESH_TOKEN`, `AMAZON_PRO_ADS_CLIENT_ID/SECRET/REFRESH_TOKEN`, `AMAZON_PRO_CONNECTORS`, y los interruptores `AMAZON_PRO_LIVE_SPAPI=1` / `AMAZON_PRO_LIVE_ADS=1` solo tras una verificación humana. (Aviso de nombres resuelto en la Corrección 4.1: convención única `AMAZON_PRO_*`.)

## 8. Checklist de despliegue en STAGING (no ejecutar sin orden)
1. Aprobación de José de esta fase y del commit; **solo entonces** push de la rama y despliegue en el servicio de staging.
2. `render.staging.yaml`: `AMAZON_PRO_STAGING=1`, `AMAZON_PRO_SEED_VIEWERS=auditor`, `AMAZON_PRO_PASSWORD_AUDITOR` (secreto), contraseña de admin (secreto). Ninguna clave de Keepa/OpenAI/Amazon.
3. Comprobar: banner STAGING visible; selector fijado en DEMO; login del auditor; las 4 pantallas nuevas en móvil real (390/360); viewer: 403 en cualquier escritura.
4. `/api/status`: 4 conectores DESHABILITADOS. `AMAZON_PRO_CONNECTORS` vacío.
5. Repetir `tests/ui_fase4_test.py` apuntando al staging (sin credenciales reales) y revisar los logs: 0 salidas a Amazon/Keepa/OpenAI.
6. Producción: no tocar hasta cerrar los pendientes de §9 y la retirada de legacy.

## 9. Datos reales pendientes
Ventas y publicidad reales (informes de Seller Central y Ads importados, o SP-API/Ads API conectadas) · costes completos de Amazon (transporte, preparación, tarifa FBA/FBM, almacenaje, devoluciones) · stock real de hoy (hoy solo hay existencias históricas) · PVP y costes puestos en Amazon revalidados · documentación regulatoria (PIF, CPSR, persona responsable UE, CPNP, claims) · comparabilidad confirmada de competidores · titular legal de la cuenta Seller Central («POR CONFIRMAR») · credenciales y verificación humana de SP-API y Ads.

## 10. Definición verificable de «proyecto terminado»
El proyecto está terminado **como producto de software** cuando se cumple todo esto (✔ = verificado en esta fase):
1. ✔ 6 secciones ejecutivas + Administración unificada, a 1440/390/360, sin scroll horizontal, con controles ≥ 44 px.
2. ✔ REAL/DEMO/SIN DATOS en cada bloque; ausencia nunca convertida en 0.
3. ✔ Viewer solo lectura (UI y 403 del servidor); trazabilidad y auditoría intactas.
4. ✔ Director IA: ≤ 3 decisiones con los 6 campos; reglas nunca presentadas como IA.
5. ✔ Arquitectura Amazon preparada, desactivada, solo lectura, sin secretos en el repo.
6. ✔ Cero llamadas externas en pruebas; regresión sin fallos nuevos frente a la base.
7. ☐ Revisión de José de la Fase 4 sin incidencias bloqueantes.
8. ☐ Retirada de `?legacy=1` (criterios 4 y 5).
9. ☐ Despliegue en staging según §8 y verificación en dispositivo real.
Y como **negocio operativo** además exige (no es código): importar o conectar datos reales de ventas, publicidad, costes y stock (§9) y obtener una verificación humana registrada de SP-API/Ads. Hasta entonces el sistema muestra SIN DATOS, que es lo correcto.
