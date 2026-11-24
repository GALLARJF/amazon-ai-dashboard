# Regresión completa post-4.2.1, fallos heredados y auditoría visual de staging

**Rama:** `aht-regresion-y-auditoria-4-2-1` (base `b58c97c367ae540094d9b31a39db85e8b8ad827b`, rama `aht-finalizacion-fase4`) · **Fecha:** 24-nov-2026 · **Alcance:** solo pruebas y documentación. Sin producción, sin despliegue, sin conectores reales, sin credenciales, sin gasto. Código de producto (`server.py`, `backend/`, `js/`) **sin modificar**.

## 1. Conclusión (HECHO)
- **Regresión final: una única ejecución ininterrumpida de `bash tests/run_all.sh` sobre el commit `9ee839817869b4a57d685aacf26f2829168dea3c`: 86 suites ejecutadas, 86 con rc=0, 0 con fallo, EXIT=0** (inicio 04:19:49Z, fin 04:39:48Z). Registro completo por suite (número, última línea, rc) en `docs/p0_hoy/regresion_final_run_all.log`. «86» es el número real de invocaciones de suite (el bucle `js/*` cuenta 4); los «80/81» del primer informe eran un recuento de líneas del script y se corrigen aquí.
- Los 6 fallos heredados eran expectativas obsoletas de las pruebas (§2). Además, la ejecución completa destapó **tres fuentes de intermitencia demostradas** en pruebas (no en el producto); están corregidas y descritas en §3b. **No se eliminó ni rebajó ninguna aserción.**
- El alias `KEEPA_KEY` queda caracterizado con pruebas; **no se ha tocado el servidor** (§2b).
- Auditoría visual autenticada endurecida y en verde (§4), **sobre instancia local en modo staging; el Render real sigue pendiente (§6)**.

## 2. Clasificación de los 6 fallos heredados (HECHO, con causa demostrada)
### `security_test` (4 fallos, 1 causa)
| Comprobación | Causa |
|---|---|
| «tras habilitar explícitamente, aparecen como probables» | La prueba fija la clave simulada con el nombre antiguo `KEEPA_KEY`; el servidor (desde K1) exige `KEEPA_API_KEY` en `CONNECTORS["keepa"]["env"]`. Con la clave «ausente», Keepa sale `testable=False` (depurado: `missing=['KEEPA_API_KEY']`). |
| «prueba keepa (simulada) OK», «segunda prueba inmediata → 429», «error de red: respuesta con código fijo…» | Consecuencia de la anterior: sin conector probable el servidor responde 403, no 200/429. |
**Corrección:** la prueba usa `KEEPA_API_KEY` (nombre canónico, el mismo que ya comprueba `FORBIDDEN_ENV` en staging). Resultado 53/53. No se debilita nada: el centinela sigue siendo un secreto falso y se sigue comprobando que no aparece en ninguna respuesta HTTP, que el transporte bloquea escrituras y hosts no permitidos y que no hay llamadas con conectores deshabilitados. *(Observación no corregida: `server.py` acepta `KEEPA_KEY` como alias en la llamada pero no en `status()`; es una incoherencia menor sin impacto de seguridad, propuesta como mejora separada.)*

### `v040_api_test` (2 fallos, causa común: el texto determinista del Director cambió en K2)
| Comprobación | Causa |
|---|---|
| «Director sin IA… lista de datos que faltan» | Desde K2 la respuesta se compone por intención; la lista `[DATOS QUE FALTAN]` solo se emite para la intención «faltan». Para la pregunta de país se emite `[SIN RECOMENDACIÓN]` y «Ningún país es evaluable…». |
| «pregunta de precio: cálculo por país…» | El formato de importes pasó de `39.90` a `39,90 €` y los marcadores a `[CÁLCULO · HIPÓTESIS]` / `[DATO NO DISPONIBLE] Francia`. |
**Corrección:** las aserciones se actualizan al comportamiento vigente y se **añade** una comprobación de la intención «faltan» (`[DATOS QUE FALTAN]`), de modo que la cobertura no disminuye (45 → 46). Se mantienen `status == SIN_DATOS_SUFICIENTES`, la ausencia de recomendación y `IA_NO_SOLICITADA` para el analista.

## 2b. Alias `KEEPA_KEY` frente a `KEEPA_API_KEY` (HECHO; propuesta NO aplicada)
Prueba nueva `tests/keepa_alias_consistency_test.py` (13/13; subprocesos con entorno mínimo y secretos falsos; sin red). Comportamiento actual demostrado:
| Caso | Resultado |
|---|---|
| Solo `KEEPA_KEY` | `status()`: falta `KEEPA_API_KEY`, no probable, «SIN CREDENCIALES». **`backend.keepa.config()` sí lee el alias** → incoherencia status/configuración |
| Solo `KEEPA_API_KEY` | reconocida por status y configuración |
| Ambas | gana `KEEPA_API_KEY` |
| Staging + `KEEPA_API_KEY` | no arranca; el mensaje nombra la variable, nunca el valor |
| Staging + solo `KEEPA_KEY` | **la guardia NO lo detecta** (`FORBIDDEN_ENV` solo lista `KEEPA_API_KEY`); queda mitigado porque la guardia fuerza `AMAZON_PRO_KEEPA_ENABLE=0` (modo 0, sin operaciones) |
En ningún caso se filtra el secreto (status JSON ni salida). **Propuesta (requiere código funcional, no aplicada):** o bien retirar el alias de `config()` y de la llamada de `/api/connectors/test`, o bien aceptarlo de forma consistente y añadir `KEEPA_KEY` a `FORBIDDEN_ENV`. Decisión pendiente de José/ChatGPT. Además `security_test` ahora aísla las variables heredadas (`AMAZON_PRO_*`, `KEEPA_*`, `OPENAI_*`, `ANTHROPIC_*`, `H10_*`) y se comprobó que pasa con `KEEPA_KEY` y `AMAZON_PRO_STAGING` hostiles en el entorno.

## 3. Resultados de la regresión
### 3a. Ejecuciones completas de `run_all.sh` (todas con 86 suites; solo la última es la de cierre)
| # | Commit | Resultado | Notas |
|---|---|---|---|
| 1 | `bab3c2c` | 85/86 | fallo: `ui_v100_test` 43/44 (veredicto/20 competidores) |
| 2 | `16171c1` | 84/86 | fallos: `ui_v100_test` y `ui_v100_cloud_test` (mismo patrón) |
| 3 | `e714427` | 84/86 | fallos: `budget_test` 28/29 y `ui_v100_cloud_test` |
| **4 (cierre)** | **`9ee8398`** | **86/86, EXIT=0** | registro por suite en `regresion_final_run_all.log` |
Las ejecuciones 1–3 se conservan solo como resumen (logs efímeros). Antes de ellas, la regresión del commit `b58c97c` se hizo en **dos tandas por un reinicio del entorno** (suites 1–77 y 79–89 del guion), de modo que **no cuenta como ejecución única**; la ejecución de cierre sí lo es.
### 3b. Intermitencias demostradas y corregidas (solo pruebas; el producto no cambia)
- **`budget_test`** (reproducido 3/40 en solitario): con 6 hilos y tope de concurrencia 4 (máximo de `ai.config`), el motivo del rechazo se reparte entre la puerta de concurrencia (`IA_OCUPADA`) y la de presupuesto según el orden de los hilos. **El gasto no varió nunca** (≤2 llamadas). Ahora: caso determinista con 4 hilos/tope 4 (2 llamadas, 2 rechazos por presupuesto, exacto) + caso de 6 hilos que exige lo invariante (≤2 llamadas, motivos solo `PRESUPUESTO_MENSUAL_EXCEDIDO`/`IA_OCUPADA`). 0/60 tras el cambio.
- **`ui_v100_test` / `ui_v100_cloud_test`**: la sección Lanzamientos se repinta de forma asíncrona y la tabla de competidores puede quedar vacía un instante (demostrado: `filas=0` justo después de una espera satisfecha). Ahora se exige un **instantáneo coherente completo** (producto ACTIVCORE, veredicto «NO DECIDIBLE», 20 filas) dentro de 15 s, con diagnóstico en el mensaje. 0/6 tras el cambio cada una. *(Observación de producto, no bloqueante: el vaciado momentáneo de la tabla durante el repintado podría evitarse en la interfaz; no se modifica código funcional.)*
- Instrumentación: `run_all.sh` imprime SHA, número y rc de cada suite, las líneas `FAIL` ante fallo y un resumen con totales.

## 4. Auditoría visual autenticada de staging
**Qué se hizo (HECHO):** `tests/auditoria_visual_staging_test.py` arranca el servidor en proceso con `AMAZON_PRO_STAGING=1` (misma configuración que `render.staging.yaml`: datos sintéticos, conectores apagados, viewer forzado), inicia sesión **por la interfaz real** como `auditor` (viewer) con la contraseña de prueba local ya presente en la batería, y recorre las 6 secciones / 15 pantallas a **1440, 390, 360 y Pixel 7**. Verifica: sesión viewer, banner de datos sintéticos, ausencia de «PRODUCCIÓN»/«datos reales», sin texto roto (undefined/NaN/[object), sin imágenes rotas, sin desbordamiento horizontal de página, 0 errores JS, 0 errores de consola y 0 peticiones externas. **Resultado: 35/35, 0 hallazgos automáticos (tras el endurecimiento descrito abajo).** Capturas: `docs/p0_hoy/auditoria_visual_staging/{1440,390,360,pixel7}/` (1440 y 390 a página completa; 360 y Pixel 7 solo viewport); resumen `resultado.json`.
**Endurecimiento (auditoría #7120503939):** la exclusión genérica de 401/403/404 y favicon se sustituyó por una lista **explícita** de respuestas ≥400 esperadas —una sola: `GET /api/v06/demo` → 401 antes del login (la API exige sesión; la interfaz muestra el acceso)— con recuento exacto por viewport; cualquier otra respuesta o error de consola falla. La identidad/rol se verifica con `/api/me` del servidor (auditor/viewer); cada una de las 15 navegaciones comprueba sección y subpantalla activas (`dec` es una sección oculta que se abre desde el botón Decisiones); el banner sintético no puede enmascarar indicios de datos reales (modo `demo`, opción «real» deshabilitada, ausencia de textos de producción/datos reales, marca DEMO en pantallas de datos); 0 peticiones externas y ningún secreto registrado. Resultado 35/35.
**Qué NO se hizo (POR CONFIRMAR):** auditoría sobre el **servicio staging real de Render**: la URL de staging no consta en el repositorio (solo aparece la de producción, que no se toca), no hay credenciales del auditor y no se autorizó despliegue. Debe repetirla una persona con acceso (o autorizar a Claude con la URL y una sesión de lectura) una vez desplegado.
**Revisión visual manual de capturas (1440 admin, 390 hoy):** diseño coherente, banner ámbar de staging y rótulo «DATOS FICTICIOS» visibles, controles de escritura atenuados con «SOLO LECTURA · VIEWER». Observaciones **menores y no bloqueantes**, no corregidas por no ser errores demostrados: (a) el selector de cuenta de la cabecera a 1440 trunca «POR CONFIRMAR (titular legal c…)»; (b) en capturas de página completa a 390 la barra inferior fija aparece superpuesta a mitad de página (artefacto de la captura a página completa, no de uso real).

## 5. Reproducción
```
git checkout aht-regresion-y-auditoria-4-2-1
bash tests/run_all.sh                         # batería completa (86 suites; imprime SHA, rc por suite y resumen)
python3 tests/security_test.py                # 53/53
python3 tests/v040_api_test.py                # 46/46
python3 tests/keepa_alias_consistency_test.py # 13/13
python3 tests/auditoria_visual_staging_test.py  # 35/35 + capturas
```
Las suites regeneran capturas versionadas en `docs/p0_hoy/**`; tras ejecutarlas conviene `git checkout -- docs tests/security_results.json` para no ensuciar el árbol (así se hizo en esta rama).

## 6. Bloqueos y siguiente paso
- **Auditoría visual en Render real: pendiente separada** (URL de staging y sesión de lectura; no se piden contraseñas por GitHub ni por chat).
- Decisión sobre el alias `KEEPA_KEY` (§2b) y mejora visual no bloqueante: cabecera con selector de cuenta truncado a 1440 (sin pérdida de funcionalidad).
- SP-API/Ads: siguen desactivados; activación solo tras Seller verificado y aprobación expresa.
- Rama de producción `aht-v100-desarrollo` y `amazon-ai-dashboard` en producción: sin tocar.

**Sin despliegue, sin producción, sin conectores reales, sin credenciales y sin gasto.**
