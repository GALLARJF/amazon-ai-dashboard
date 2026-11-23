# Regresión completa post-4.2.1, fallos heredados y auditoría visual de staging

**Rama:** `aht-regresion-y-auditoria-4-2-1` (base `b58c97c367ae540094d9b31a39db85e8b8ad827b`, rama `aht-finalizacion-fase4`) · **Fecha:** 24-nov-2026 · **Alcance:** solo pruebas y documentación. Sin producción, sin despliegue, sin conectores reales, sin credenciales, sin gasto. Código de producto (`server.py`, `backend/`, `js/`) **sin modificar**.

## 1. Conclusión (HECHO)
- Regresión completa de la batería (`tests/run_all.sh`, 80 suites) ejecutada sobre `b58c97c`: **78 suites en verde y 2 en rojo** (`security_test` 49/53, `v040_api_test` 43/45), idénticas a las heredadas.
- Las 6 comprobaciones fallidas tienen causa demostrada y **todas son expectativas obsoletas de las pruebas, no defectos del producto ni de la seguridad**. Se actualizaron las pruebas sin retirar ninguna comprobación de seguridad: tras el cambio `security_test` 53/53 y `v040_api_test` 46/46.
- Auditoría visual autenticada: ver §4 (**sobre una instancia local en modo staging, no sobre el Render real**).
- Nota de ejecución: la sesión de trabajo se reinició durante la regresión (suite 78 de 80). Las suites restantes (11, desde `ui_viewer_ro_test`) se ejecutaron en una segunda tanda con el mismo script; entre ambas tandas constan todas las suites. Logs: no se versionan (efímeros); los comandos están en §5.

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

## 3. Resultados de la regresión (post-corrección de pruebas)
- Batería: 80 suites originales + 1 nueva = 81. Suites relevantes: `ui_viewer_ro_total_test` 54/54, `ui_staging_final_test`, `ui_k4_test` 52/52, `amazon_lectura_test` 63/63, `v070_registro_test` 110/110, `v070_entrega_test` 15/15, `k4_api_test` 43/43, `security_test` 53/53, `v040_api_test` 46/46.
- Las intermitencias citadas en el informe anterior (`ui_v100_cloud_test`, `budget_test`, `ui_v100_test`) **no se reprodujeron** en esta ejecución.

## 4. Auditoría visual autenticada de staging
**Qué se hizo (HECHO):** `tests/auditoria_visual_staging_test.py` arranca el servidor en proceso con `AMAZON_PRO_STAGING=1` (misma configuración que `render.staging.yaml`: datos sintéticos, conectores apagados, viewer forzado), inicia sesión **por la interfaz real** como `auditor` (viewer) con la contraseña de prueba local ya presente en la batería, y recorre las 6 secciones / 15 pantallas a **1440, 390, 360 y Pixel 7**. Verifica: sesión viewer, banner de datos sintéticos, ausencia de «PRODUCCIÓN»/«datos reales», sin texto roto (undefined/NaN/[object), sin imágenes rotas, sin desbordamiento horizontal de página, 0 errores JS, 0 errores de consola y 0 peticiones externas. **Resultado: 26/26, 0 hallazgos automáticos.** Capturas: `docs/p0_hoy/auditoria_visual_staging/{1440,390,360,pixel7}/` (1440 y 390 a página completa; 360 y Pixel 7 solo viewport); resumen `resultado.json`.
**Qué NO se hizo (POR CONFIRMAR):** auditoría sobre el **servicio staging real de Render**: la URL de staging no consta en el repositorio (solo aparece la de producción, que no se toca), no hay credenciales del auditor y no se autorizó despliegue. Debe repetirla una persona con acceso (o autorizar a Claude con la URL y una sesión de lectura) una vez desplegado.
**Revisión visual manual de capturas (1440 admin, 390 hoy):** diseño coherente, banner ámbar de staging y rótulo «DATOS FICTICIOS» visibles, controles de escritura atenuados con «SOLO LECTURA · VIEWER». Observaciones **menores y no bloqueantes**, no corregidas por no ser errores demostrados: (a) el selector de cuenta de la cabecera a 1440 trunca «POR CONFIRMAR (titular legal c…)»; (b) en capturas de página completa a 390 la barra inferior fija aparece superpuesta a mitad de página (artefacto de la captura a página completa, no de uso real).

## 5. Reproducción
```
git checkout aht-regresion-y-auditoria-4-2-1
bash tests/run_all.sh                         # batería completa (81 suites)
python3 tests/security_test.py                # 53/53
python3 tests/v040_api_test.py                # 46/46
python3 tests/auditoria_visual_staging_test.py  # 26/26 + capturas
```
Las suites regeneran capturas versionadas en `docs/p0_hoy/**`; tras ejecutarlas conviene `git checkout -- docs tests/security_results.json` para no ensuciar el árbol (así se hizo en esta rama).

## 6. Bloqueos y siguiente paso
- Auditoría visual en Render real: pendiente de URL/acceso (§4).
- SP-API/Ads: siguen desactivados; activación solo tras Seller verificado y aprobación expresa.
- Rama de producción `aht-v100-desarrollo` y `amazon-ai-dashboard` en producción: sin tocar.

**Sin despliegue, sin producción, sin conectores reales, sin credenciales y sin gasto.**
