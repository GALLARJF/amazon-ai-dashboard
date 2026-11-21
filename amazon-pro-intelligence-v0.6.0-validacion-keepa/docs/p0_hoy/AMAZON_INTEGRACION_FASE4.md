# Integración con Amazon — arquitectura preparada (Fase 4 · E)

**Estado: ARQUITECTURA PREPARADA · DESACTIVADA · SIN LLAMADAS REALES.** Nada de lo descrito aquí se ha ejecutado contra Amazon. Todo es **solo lectura**: no existe ninguna ruta para publicar productos ni para modificar precios, inventario o campañas.

## 1. Qué hay en el repositorio
| Pieza | Archivo | Qué hace |
|---|---|---|
| Adaptadores de lectura | `backend/conectores100.py` | Solo GET (+ POST únicamente al token LWA), lista blanca de rutas, hosts EU fijos, modo REAL imposible sin credenciales **y** `AMAZON_PRO_LIVE_<SERVICIO>=1`. Simulado solo contra 127.0.0.1. |
| Arquitectura declarativa | `backend/amazon_arch.py` | Capacidades → rutas permitidas → de dónde sale el dato HOY. No abre sockets ni lee credenciales. |
| Estado de conectores | `server.py` (`/api/status`) | Los 4 conectores (SP-API, Ads, Keepa, Helium 10) salen DESHABILITADOS con las variables que faltan. |
| Pruebas | `tests/amazon_arch_test.py`, `tests/v100_conectores_test.py` | Lista blanca sin escritura, sin credenciales ⇒ NO CONECTADO, 0 conexiones de red, ningún secreto en el repo. |

Cambio de Fase 4 en `conectores100.py`: la lista blanca de solo lectura se amplía con `finances/*` (SP-API) y `v2/sp/campaigns|adGroups|keywords` (Ads). Son GET; no se añade ninguna ruta de escritura.

## 2. Capacidades
**SP-API:** catálogo (`/catalog/2022-04-01/items`), pedidos (`/orders/v0/orders`), inventario FBA (`/fba/inventory/v1/summaries`), informes (`/reports/2021-06-30/reports`), tarifas (vía informe: la estimación de tarifas de la API es POST y queda fuera), finanzas (`/finances/…`).
**Ads API:** campañas, grupos y palabras clave (`/v2/sp/*`, lectura) y gasto, ventas atribuidas, ACoS y ROAS (informes `reporting/reports/{id}`; **crear** un informe es POST y requiere una decisión aparte, por eso hoy se importa el CSV).

## 3. Variables para Render (todas son secretos: se crean en el panel de Render, nunca en el repositorio, el chat ni `render.yaml`)
Convención única (servidor, adaptador, `/api/status`, guardia STAGING, documentación y pruebas):
| Servicio | Credenciales (secretos) | Interruptor LIVE |
|---|---|---|
| SP-API | `AMAZON_PRO_SPAPI_CLIENT_ID`, `AMAZON_PRO_SPAPI_CLIENT_SECRET`, `AMAZON_PRO_SPAPI_REFRESH_TOKEN` | `AMAZON_PRO_LIVE_SPAPI=1` |
| Ads API | `AMAZON_PRO_ADS_CLIENT_ID`, `AMAZON_PRO_ADS_CLIENT_SECRET`, `AMAZON_PRO_ADS_REFRESH_TOKEN` | `AMAZON_PRO_LIVE_ADS=1` |
| Global | `AMAZON_PRO_CONNECTORS=sp-api,ads` (vacío = ninguna llamada de red) | |

Doble activación: hace falta `AMAZON_PRO_CONNECTORS` **y** el interruptor LIVE del servicio, con las tres credenciales. En STAGING ninguna de estas variables puede existir (el servidor no arranca). Corrección 4.1: el desajuste de nombres queda **resuelto**. Lectura real mediante `GET /api/amazon/read` (sesión, 20/min, auditada) y catálogo `GET /api/amazon/ops`; el access token LWA se obtiene por lectura y no se guarda ni se devuelve.

## 4. Proceso OAuth (lo ejecuta una persona de AHT, no el sistema)
1. **SP-API:** en Seller Central (cuenta titular, hoy «POR CONFIRMAR») → Aplicaciones y servicios → Desarrollar aplicaciones → registrar una aplicación **privada** con roles de solo lectura (Información del producto, Pedidos, Inventario y Fulfillment, Finanzas, Informes). Autorizar la aplicación para la propia cuenta: se obtiene el **refresh token**. Client ID/Secret salen de LWA.
2. **Ads API:** solicitar acceso a la Amazon Ads API en el portal de Ads; crear el perfil de seguridad LWA; autorizar con el alcance `advertising::campaign_management` en modo solo consulta (el ámbito de lectura/escritura lo concede Amazon por aplicación: **no usar nunca llamadas de modificación**; el adaptador no las implementa).
3. Cargar los tres valores de cada servicio como variables secretas en Render. **Nunca** pegarlos en el chat ni en un fichero del repositorio.
4. Activar primero `AMAZON_PRO_CONNECTORS=sp-api`, y solo después `AMAZON_PRO_LIVE_SPAPI=1`. Una persona registra una prueba real de solo lectura (token LWA + `marketplaceParticipations`); hasta entonces el estado es «CONFIGURADO · SIN VERIFICAR».
5. Un servicio nunca se declara operativo por defecto: lo decide una persona con la verificación registrada en la auditoría.

## 5. Qué NO se hace (y está comprobado por prueba)
Publicar o editar listings, cambiar precios, tocar inventario, crear/editar campañas o pujas, llamar a Amazon durante las pruebas, guardar credenciales en el repositorio.
