# Informe GO / NO-GO — despliegue privado de pruebas (Render) · 2026-11-17

**Veredicto: GO CONDICIONAL para un despliegue PRIVADO DE PRUEBAS. NO-GO para producción.**
No se ha contratado nada ni tocado configuración de producción. Coste si decides contratar: 7,25 USD/mes (Starter 7 + disco 1 GB 0,25).

## Revisión punto a punto
| # | Punto | Estado | Evidencia |
|---|---|---|---|
| 1 | Respaldo fuera del disco + restauración | CUMPLIDO (probado) | `tools/respaldo_remoto.py`; API admin `/api/v07/respaldo` y `/subir`; restauración pendiente aplicada al reiniciar con copia previa; test 20/20 (pérdida total del disco, hash falso, no-SQLite y auditoría manipulada rechazados) |
| 2 | Imagen Docker construible | CUMPLIDO (CI real) | GitHub Actions éxito en f48d192: build, arranque no root, /healthz 200. Dos bugs reales corregidos gracias al CI |
| 3 | HTTPS proxy, Host, Origin, cookies, secretos | PROBADO LOCAL + DOC RENDER | 29/29 cloud, 37/37 Chromium con proxy TLS; Render envía X-Forwarded-Proto https y su health check usa host onrender.com/dominio propio (soporte/doc de Render); /healthz pasa antes del control de Host |
| 4 | Blueprint desde la rama correcta | NO VERIFICABLE sin cuenta | `render.yaml` apunta a `aht-v100-desarrollo` (rootDir en el del raíz); no pude leer la spec oficial desde este entorno; el primer despliegue lo confirma |
| 5 | Recuperación admin y rotación | CUMPLIDO (probado) | `AMAZON_PRO_ROTATE` + secreto nuevo; sesiones cerradas; auditado sin contraseñas; clave corta/usuario inexistente se omiten |
| 6 | APIs de pago / operaciones reales off | CUMPLIDO | Keepa e IA desactivados en Blueprint y en tests; 0 tokens, 0 llamadas de pago, nada publicado en Amazon |
| 7 | QA | 33/33 suites, auditoría OK | `coordinador.py qa` |

## Lo que sigue pendiente (honesto)
- Despliegue real en Render nunca ejecutado: disco persistente, plan Starter y Blueprint sin comprobar en vivo.
- SP-API, Ads API y OpenAI sin conectar → no es producción. Windows no verificado. Sin auditoría independiente de un segundo modelo.
- Los respaldos solo protegen si los descargas tú a tu PC con regularidad (no hay programación automática fuera del disco).

## Condiciones para pasar a GO (acciones tuyas)
1. Autorizar el gasto de 7,25 USD/mes en Render y conectar el repositorio GitHub (rama `aht-v100-desarrollo`).
2. Escribir tú `AMAZON_PRO_ADMIN_PASSWORD` y `AMAZON_PRO_PASSWORD_SERGIO` (≥12 caracteres) en el panel; nunca por chat.
3. Tras el primer despliegue: abrir `/healthz`, entrar, ejecutar `respaldo_remoto.py descargar` y una restauración de prueba.
