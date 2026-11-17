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

## Ficheros
`Dockerfile`, `.dockerignore`, `render.yaml` (en la raíz del repositorio con `rootDir`), `server.py` (modo cloud), `tests/v100_cloud_test.py` (28/28) y `tests/ui_v100_cloud_test.py` (37/37, Chromium a 390/820/1600 px).

## Límites
Producción no declarada: SP-API, Ads API y OpenAI siguen sin conectar y Windows sin verificar. Un único servicio con un disco no admite varias réplicas. Si cambias a un dominio propio, define `AMAZON_PRO_PUBLIC_HOST`.
