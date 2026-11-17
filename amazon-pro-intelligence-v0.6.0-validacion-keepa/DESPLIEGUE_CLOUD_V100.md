# Despliegue cloud privado — Amazon Pro Intelligence V1.0.0-candidata

**Estado: PREPARADO, NO DESPLEGADO.** Ningún proveedor ofrece hoy alojamiento persistente a 0 € para esta aplicación (ver «Qué se verificó»). No se ha contratado nada. Lo que sí está probado es el modo cloud de la aplicación con un proceso real y un proxy HTTPS local; **no** se ha desplegado en ningún proveedor ni construido la imagen Docker (no hay demonio Docker en la sesión).

## Opción concreta (sin contratar)
**Render — web service «Starter» + disco persistente de 1 GB: 7 USD/mes + 0,25 USD/mes = 7,25 USD/mes** (precios de la página de Render; sin IVA ni conversión). Sin tarjeta no se puede crear. Incluye HTTPS, URL estable `*.onrender.com`, sin dormirse y disco que sobrevive a reinicios.

## Qué se verificó sobre alternativas gratuitas
- Render gratuito: el sistema de ficheros es efímero (se pierde la base SQLite en cada reinicio o reposo); no admite disco persistente y se duerme a los 15 minutos.
- Fly.io y Koyeb: sin nivel gratuito de cómputo para cuentas nuevas (Koyeb exige tarjeta con retención). Railway: crédito de prueba, no gratis indefinido.
- Resultado: **gratis + persistente + sin tarjeta no existe** para esta aplicación. Una sesión de Claude no sirve de alojamiento: es temporal.

## Seguridad del modo cloud (probada)
- Solo responde al nombre público configurado y por HTTPS; otro `Host` u `Origin` → 403.
- Sin sesión, toda la API devuelve 401. Cookie `Secure`, `HttpOnly`, `SameSite=Strict` y HSTS.
- Las contraseñas **nunca** van por chat ni se imprimen en logs: se escriben como secretos en el panel del proveedor.
- Si falta `AMAZON_PRO_ADMIN_PASSWORD` (mínimo 12 caracteres), la aplicación no arranca.
- Keepa e IA desactivados por defecto: 0 tokens, 0 €.
- Respaldo automático diario con hash en el disco (conserva los 7 últimos).

## Cómo crear tu usuario administrador y el de Sergio (sin contraseñas en el chat)
1. En Render: **New → Blueprint**, conecta el repositorio `GALLARJF/amazon-ai-dashboard` (rama `aht-v100-desarrollo`).
2. Render pedirá los secretos marcados `sync: false`: escribe tú mismo `AMAZON_PRO_ADMIN_PASSWORD` (tu contraseña de `admin`) y `AMAZON_PRO_PASSWORD_SERGIO` (la de Sergio; puede escribirla él). Mínimo 12 caracteres.
3. Se crea el usuario `admin` en el primer arranque y `sergio` (rol `approver`) desde `AMAZON_PRO_SEED_USERS`. Para añadir otro usuario no administrador: añade `nombre:rol` a esa variable y su secreto `AMAZON_PRO_PASSWORD_NOMBRE`.
4. Entra en `https://<tu-servicio>.onrender.com`. Los administradores nunca se crean por la variable de siembra.

## Respaldo FUERA del disco de Render, restauración y recuperación (probado)
- `/data/backups` está en el **mismo disco** que la base: sirve contra errores de software, **no** contra pérdida del disco. La copia que cuenta es la que se guarda en tu PC.
- **Descargar** (cada semana o antes de cambios): `python tools/respaldo_remoto.py descargar https://TU-SERVICIO.onrender.com --usuario admin --carpeta respaldos`. Pide la contraseña en el terminal (no se imprime ni va por argumentos), verifica TLS, comprueba hash SHA-256, integridad SQLite y cadena de auditoría, y guarda el fichero en tu PC. Solo el administrador puede (403 al resto).
- **Restaurar**: `python tools/respaldo_remoto.py subir https://TU-SERVICIO.onrender.com --usuario admin --archivo respaldos/respaldo_XXXX.db`. El servidor valida el fichero (hash, integridad, auditoría) y lo deja **pendiente**; se aplica al **reiniciar** el servicio (Render → Manual Deploy → Restart). La base anterior se conserva como `amazon_pro.db.previo-<fecha>`; un fichero manipulado o dañado se rechaza (400).
- Los respaldos contienen hashes de contraseñas y datos comerciales: guárdalos en un sitio privado, nunca en GitHub ni Drive compartido.
- Prueba automática: `tests/v100_respaldo_cloud_test.py` (20/20): descarga fuera del disco, pérdida total del disco, restauración, rechazo de hash falso/no-SQLite/auditoría manipulada.

## Recuperación del administrador y rotación de contraseñas (sin chat)
1. En el panel de Render → Environment: escribe la contraseña nueva (≥12 caracteres) en `AMAZON_PRO_ADMIN_PASSWORD` (o `AMAZON_PRO_PASSWORD_<NOMBRE>` para otro usuario) y añade `AMAZON_PRO_ROTATE=admin,sergio` (los que toquen).
2. Reinicia. Se aplica la contraseña, se cierran todas las sesiones de esos usuarios y se audita (`user.rotate`) sin contraseñas en logs. Contraseña corta o usuario inexistente → se omite sin romper el arranque.
3. Quita `AMAZON_PRO_ROTATE` después (reaplicarlo es inofensivo). Rotación recomendada: al terminar la prueba y si alguien compartió una clave.
- Nunca se crean administradores por variables de entorno; solo se rota el existente.

## Verificación de la configuración Render (honesta)
- **Verificado en documentación/soporte de Render**: el proxy envía `X-Forwarded-Proto: https`; `RENDER_EXTERNAL_HOSTNAME` es el host `onrender.com` del servicio; el health check usa como Host el dominio personalizado verificado si existe, si no el `onrender.com`. `/healthz` va antes de la comprobación de Host/Origin, así que el health check pasa en ambos casos. Si añades dominio propio, define `AMAZON_PRO_PUBLIC_HOST` con ese dominio.
- **Probado localmente**: Host/Origin ajenos → 403, cookies Secure/HttpOnly/SameSite=Strict, HSTS, secretos obligatorios (tests v100_cloud 29/29, UI 37/37).
- **NO verificado (requiere cuenta Render)**: despliegue real del Blueprint desde la rama `aht-v100-desarrollo`, montaje del disco, comportamiento del plan Starter. No se pudo leer la página de la especificación de Blueprint desde este entorno; los campos usados (`runtime: docker`, `plan`, `branch`, `disk`, `healthCheckPath`, `sync: false`) son los habituales y debe confirmarlos el primer despliegue.
- **Imagen Docker**: no hay Docker local. Se añadió `.github/workflows/docker.yml` (construye la imagen, arranca el contenedor, comprueba `/healthz` y usuario no root). Estado del CI: ver el informe GO/NO-GO.

## Ficheros
`Dockerfile`, `.dockerignore`, `render.yaml` (en la raíz del repositorio con `rootDir`), `server.py` (modo cloud), `tests/v100_cloud_test.py` (28/28) y `tests/ui_v100_cloud_test.py` (37/37, Chromium a 390/820/1600 px).

## Límites
Producción no declarada: SP-API, Ads API y OpenAI siguen sin conectar y Windows sin verificar. Un único servicio con un disco no admite varias réplicas. Si cambias a un dominio propio, define `AMAZON_PRO_PUBLIC_HOST`.
