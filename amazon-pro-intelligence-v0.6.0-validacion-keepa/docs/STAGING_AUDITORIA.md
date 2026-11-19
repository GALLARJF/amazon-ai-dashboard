# STAGING de auditoría — rol `viewer` (solo lectura)

Estado: implementado y probado **en local**. NO desplegado. Producción (`render.yaml`, rama `aht-v100-desarrollo`) sin cambios.

## Qué es el rol `viewer`
- Lee todas las pantallas, expedientes, gráficos, tablas, recomendaciones, historial/auditoría, aprobaciones, estado de conexiones, uso/límites del Director IA y K4 · Ejecutivo: para las consultas (GET) se comporta como administrador.
- No escribe nada. Cualquier POST/PUT/PATCH/DELETE → **403**, sea cual sea la ruta (existente o no).
- **Excepción deliberada de secretos:** no puede descargar el respaldo de la base de datos (`GET /api/v07/respaldo`), porque contiene hashes de contraseñas y sesiones → 403. Tampoco existe ningún endpoint que muestre claves (ni para el admin).

## Barreras (defensa en profundidad)
1. **Central** (`server.py`, `do_POST/do_PUT/...`): denegación por defecto antes de enrutar. Solo `login` y `logout` quedan permitidos.
2. **`_sess(write=True)`** rechaza al viewer; **`_v06`** rechaza cualquier método no GET; **`api6/api7/api_k4.handle`** lanzan `PermissionError`.
3. **Interfaz** (`js/v03.js`): `api()` no envía escrituras del viewer y `lockUi()` desactiva los controles de escritura. No es la protección real: lo es el servidor.
4. Cada intento bloqueado se audita (`viewer.write_blocked`).

## Modo STAGING (`AMAZON_PRO_STAGING=1`)
- Etiqueta fija **«STAGING — DATOS SINTÉTICOS — SOLO LECTURA»** incrustada en el HTML (visible antes de iniciar sesión) + cabecera `X-Env: staging`.
- El arranque se ABORTA si existe cualquier variable de KEEPA/OPENAI/ANTHROPIC/SPAPI/ADS/H10.
- Fuerza IA, Keepa y trabajador en segundo plano desactivados; `enabled_connectors()` siempre vacío; lista de salida a Internet vacía; `/api/connectors/test` → 403.
- Solo datos sintéticos/DEMO del propio código. Nada se copia de producción.
- Usuario viewer: `AMAZON_PRO_SEED_VIEWERS=auditor` + secreto `AMAZON_PRO_PASSWORD_AUDITOR` (≥12). Idempotente. Cambio de contraseña: `AMAZON_PRO_ROTATE=auditor`.

## Ejecutar en local
```bash
cd amazon-pro-intelligence-v0.6.0-validacion-keepa
python3 tests/viewer_test.py          # 403 en escrituras + lectura completa + sin servicios de pago
python3 tests/ui_viewer_test.py       # navegador real; capturas en CAPTURAS_UI/viewer/
# servidor de staging local con viewer:
AMAZON_PRO_STAGING=1 AMAZON_PRO_SEED_VIEWERS=auditor AMAZON_PRO_PASSWORD_AUDITOR='<>=12 caracteres, la eliges tú>' \
  AMAZON_PRO_ADMIN_PASSWORD='<otra>' python3 server.py     # http://localhost:8765  (usuario: auditor)
```
Introduce la contraseña solo en tu terminal/panel, nunca en el chat.

## Despliegue (NO realizado) y reversión
`render.staging.yaml` (raíz) define un servicio independiente. Si algún día se aprueba: crearlo en Render desde ese Blueprint, escribir los secretos en el panel, comprobar `/healthz` y el 403 del viewer. Reversión: suspender/eliminar el servicio y el disco de staging, o descartar la rama `aht-staging-viewer`; producción no se ve afectada.
