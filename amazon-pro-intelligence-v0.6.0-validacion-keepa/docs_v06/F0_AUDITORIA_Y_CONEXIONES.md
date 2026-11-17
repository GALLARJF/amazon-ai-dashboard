# F0 — Protección y auditoría (V0.5.0 → V0.6)

## Copia de seguridad
- `BACKUPS/amazon-pro-intelligence-v0.5.0_BACKUP_20261117.tar.gz` (SHA-256 en `BACKUPS/SHA256SUMS.txt`), verificada: extraída y comparada con `diff -r` = idéntica.
- Contiene `data/amazon_pro.db` (datos locales del proyecto, sin claves: las claves viven en ai.env/keepa.env, que no existen en el árbol del proyecto).
- `amazon-pro-intelligence-v0.4.0.zip` intacto (SHA-256 98c15ca0…eb480; integridad ZIP OK). v0.3.4 y anteriores sin tocar.
- No hay repositorio Git. Punto de recuperación = backup + `MANIFIESTO_ARCHIVOS_V050.txt` (hash de cada archivo).

## Pruebas que fallaban
| Prueba | Causa | Resultado |
|---|---|---|
| `budget_test` 28/29 | No reproducible: 4 ejecuciones seguidas 29/29. Intermitente (sensible a tiempo/orden), sin cambio de código. **Queda vigilada**, no declarada resuelta con certeza. | 29/29 |
| `ui_synth_test` 14/15 | Defecto real de V0.5.0: el selector de cuenta por defecto elegía la cuenta de sistema `catalogo-aht` y no la de PhiVital, por lo que el desplegable no mostraba el expediente. Corregido en `js/v03.js`. | 15/15 |
`run_all.sh`: TODAS LAS SUITES OK.

## Matriz de conexiones (estado REAL verificado)
| Conexión | Código | Llamada real realizada | Estado |
|---|---|---|---|
| Keepa | cliente completo (tokens, caché, 429) | **NUNCA** (solo simulada en pruebas) | PENDIENTE DE VERIFICACIÓN: costes en tokens y códigos de dominio son supuestos de documentación de terceros |
| OpenAI | cliente con presupuesto, confirmación y procedencia | **NUNCA** (`AI._post` parcheado en pruebas) | "IA real verificada: NO" hasta una llamada autorizada |
| Amazon SP-API | no implementado | No | PENDIENTE DE CONEXIÓN |
| Amazon Ads API | no implementado | No | PENDIENTE DE CONEXIÓN |
| Importación informes Amazon | no implementado | No | F12 |
| Importación documentación interna | parcial (fichas) | No aplica | F12 |

Todas las pruebas son MOCK/SIMULACIÓN; ninguna es ejecución real contra un proveedor. Claves: nunca en chat, ZIP ni informes.
