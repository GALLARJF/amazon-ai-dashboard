# MISIÓN K1 — Keepa en Render · Informe técnico (2026-11-17)

**Veredicto: GO CONDICIONAL.** GO para integrar la rama `aht-k1-keepa` (revisión del PR) y para la **comprobación de saldo, gratuita**. **NO-GO** para cualquier búsqueda real hasta que (1) la comprobación de saldo funcione en Render y (2) tú aprobes el presupuesto de la primera prueba (20 tokens, solo España). No se ha consumido ningún token ni tocado Render, secretos, SQLite, usuarios, sesiones, backups o disco. Rama de despliegue `aht-v100-desarrollo` **intacta**.

## 1. Diagnóstico técnico real (código, no interfaz)
| Pregunta | Hallazgo |
|---|---|
| Carga de configuración | `backend/keepa.py::config()` lee **variables de entorno** (`os.environ`). Además `server.py` carga `keepa.env` (`~/AmazonPro/keepa.env`) si existe; sin pisar variables ya definidas. En Render no hay `keepa.env`: **las variables de entorno de Render ya funcionaban sin cambios de código** |
| Nombres exactos | Clave: `KEEPA_API_KEY` (o `KEEPA_KEY`). Interruptor: `AMAZON_PRO_KEEPA_ENABLE`. Límites: `AMAZON_PRO_KEEPA_BATCH_BUDGET` (30), `_HARD_CAP` (120), `_MISSION_CAP` (0=sin tope), `_CACHE_HOURS`, `_SEARCH_COST` (10), `_COST_PER_ASIN` (1), `_MIN_GAP_S` (1.0), `_CHUNK` |
| Riesgo de exposición | La clave solo vive en memoria del proceso. `public_status` nunca la devuelve; el libro, la misión y los errores usan códigos fijos; los logs de acceso cloud no llevan cadenas de consulta ni cuerpos. Probado (K1: la clave no aparece en estado, libro, misión ni respuestas HTTP) |
| «Probar conexión» | `POST /api/keepa/test` → `GET https://api.keepa.com/token` (no consume tokens). **Defecto real:** con `ENABLE=0` devolvía «desactivado», así que para comprobar la clave había que activar Keepa del todo (incluidas búsquedas de pago). Corregido con el modo `balance` |
| Presupuestos | `batch_budget` y `hard_cap` por llamada; `mission_cap` acumulado (desactivado por defecto, con duplicados y peor caso persistidos en `keepa_mission`). **Defecto real:** el descubrimiento aceptaba una aprobación total (p. ej. 160) por encima del `hard_cap` (120): el tope solo se aplicaba por llamada suelta |
| Rutas implementadas | `/token`, `/product`, `/search` (lista blanca). Reales y verificadas con dinero: **solo `/token` y `/search` ES** (10 tokens observados, 2026-11-17). `/product` está probado **solo con simulación**; su coste real (1/ASIN supuesto) **no está verificado** |
| Persistencia y procedencia | SQLite: `keepa_cache` (registro normalizado con `source`, `fetched_at`, `evidence_quality`), `keepa_ledger` (estimado vs `tokensConsumed`), `keepa_mission` (peor caso, duplicados). Sobreviven a reinicios y despliegues (disco persistente) |
| Reinicios/despliegues/rotación | Las variables se releen en cada llamada; cambiar un secreto en Render reinicia el servicio y no toca el disco. Rotar la clave no requiere cambios de código |

## 2. Qué se ha cambiado (rama `aht-k1-keepa`, sin push a la rama de autodeploy)
- `backend/keepa.py`: modo `AMAZON_PRO_KEEPA_ENABLE` = `0` (apagado, por defecto) · **`balance` (solo saldo, gratis; /product y /search bloqueados por código)** · `1` (operaciones de pago). Aprobación explícita verificable a nivel de llamada (`grant`), una sola operación de pago a la vez (exclusión mutua), `approved > hard_cap` rechazado.
- `backend/discovery.py`: aprobación total ≤ tope; el plan indica `exceeds_hard_cap` y el coste por país; reglas K1 que **solo pueden bajar** la comparabilidad.
- `backend/keepa_k1.py` (nuevo): reglas de comparabilidad (categoría, función, formato, volumen, precio normalizado, marketplace, calidad de evidencia; DE/FR/IT/ES) e importación **sin red** de la evidencia real.
- `server.py`: endpoints con aprobación obligatoria; `POST /api/keepa/importar-evidencia` (solo admin, auditado); en modo cloud, valores por defecto prudentes (`REQUIRE_APPROVAL=1`, `MISSION_CAP=60`) que **nunca activan Keepa**.
- `render.yaml`: **se elimina `AMAZON_PRO_KEEPA_ENABLE: "0"`** (ver §4 efectos). `js/eu.js`: selector «Solo España / todos», tope en «Autorizar hasta», estado «SOLO SALDO», botón de importación.
- Tests: `k1_keepa_test` (29), `k1_http_test` (12); `v050_test` ajustado (su escenario de 160 tokens ahora declara tope 200).

## 3. 160 vs 120 tokens — resuelto
- 160 = 4 países × (2 búsquedas × 10 + 20 ASIN × 1) = **plan máximo «normal» de DE+FR+IT+ES**. 120 = `hard_cap` (tope absoluto).
- Antes el sistema permitía aprobar 160 por encima del tope (inconsistente). Ahora: aprobar > 120 se **rechaza** (`APROBACION_SUPERA_TOPE`) y el plan avisa y desglosa **40 tokens por país**. Se ejecuta país a país.

## 4. Benchmarking: 20 competidores históricos y 0 comparables
Causa distinguida: **no era un error del filtro ni ausencia real de datos**.
1. *Integración:* los 20 existen solo como fichero de evidencia del repositorio (`docs_v06/evidencia_keepa_real/`) leído por «MIS VENTAS»; el módulo EUROPA lee la **caché SQLite**, y la base de Render nació vacía. → Nuevo botón «Importar competidores ya obtenidos (sin gasto)».
2. *Filtro correcto:* aun importados, un candidato sin decisión humana no cuenta como «confirmado» (el sistema los muestra como automáticos/no confirmados).
3. *Calidad:* la puntuación antigua dejaba pasar sérums hidratantes/calmantes y nutritivos. Reglas K1 aplicadas a los 20: **6 ALTA, 3 MEDIA, 11 BAJA** (11 excluidos por categoría/función/formato). Limitación: los títulos de la evidencia están truncados, y la heurística por palabras clave es una inferencia revisable, no una verdad.
- BSR **no** se convierte en ventas: no hay metodología validada (regla documentada).

## 5. QA
| Prueba | Resultado | Tipo |
|---|---|---|
| K1 Keepa (clave ausente, deshabilitado, clave inválida, config válida, presupuesto excedido, duplicada, red caída, saldo insuficiente, respuesta malformada, reinicio, concurrencia, sin secretos) | 29/29 | **SIMULADA** (get falso + guardia de red) |
| K1 HTTP (modo balance, aprobación, tope 120, plan 160, importación, módulo europeo) | 12/12 | **SIMULADA** |
| Suite completa (coordinador) | 35/35 · auditoría OK | simulada/local; panel NEON y Director IA conservados (UI 44/44, EU 18/18) |
| Consultas reales a Keepa en K1 | **0** (0 tokens) | — |
| Reales previas | `/token` y `/search` ES (2026-11-17, 10 tokens); build Docker en GitHub Actions | reales |

## 6. Variables exactas para Render (las escribes tú; la clave nunca en chat/GitHub)
| Variable | Valor | Cuándo |
|---|---|---|
| `KEEPA_API_KEY` | tu clave (secreto) | ahora |
| `AMAZON_PRO_KEEPA_ENABLE` | `balance` | paso 1 (solo saldo, gratis) |
| `AMAZON_PRO_KEEPA_ENABLE` | `1` | solo tras aprobar la prueba de pago |
| `AMAZON_PRO_KEEPA_REQUIRE_APPROVAL` | `1` (ya por defecto en la nube) | opcional, explícito |
| `AMAZON_PRO_KEEPA_MISSION_CAP` | `60` (por defecto en la nube) | tope acumulado |
| `AMAZON_PRO_KEEPA_HARD_CAP` / `_BATCH_BUDGET` | `120` / `30` (por defecto) | no tocar |

**Pasos (sin revelar la clave):** 1) Fusiona el PR de `aht-k1-keepa` en `aht-v100-desarrollo` (provoca un redespliegue: ver §7). 2) Render → servicio `amazon-pro-intelligence` → *Environment* → *Add Environment Variable*: `KEEPA_API_KEY` y pega tú la clave; `AMAZON_PRO_KEEPA_ENABLE=balance`. 3) Guardar (Render reinicia; el disco persiste). 4) En la app: EUROPA · MERCADOS → *Probar conexión*.

## 7. Efectos sobre Blueprint, disco, secretos y costes (cambio en `render.yaml`)
- Quitar `AMAZON_PRO_KEEPA_ENABLE` del Blueprint evita que cada sincronización **restablezca** el valor que pongas en el panel. Si no estuviera definido, Keepa queda desactivado (valor por defecto del código). Al ser un cambio en el fichero, el Blueprint se vuelve a sincronizar; el valor `0` ya existente en el panel **se conserva** hasta que lo edites (comportamiento de Render al eliminar una clave del Blueprint: **no verificado** en tu cuenta; comprueba el valor tras el primer despliegue).
- Disco persistente, plan Starter y precio **sin cambios** (7,25 USD/mes). No se crean servicios. Las contraseñas y sesiones están en SQLite en el disco: se conservan.
- Autodeploy: fusionar en `aht-v100-desarrollo` provocará un redespliegue de ~1–3 min (comportamiento por defecto de Render ante un push a la rama enlazada; no verificado en tu panel). Por eso **no he fusionado nada**: queda en un PR para tu revisión.

## 8. Comprobar el saldo sin consumir tokens de búsqueda
Con `ENABLE=balance`: botón *Probar conexión (saldo de tokens, gratis)* → llama solo a `GET /token`. En este modo es **imposible** (por código y probado) llamar a `/search` o `/product`. Se muestra saldo, recarga/min y hora.

## 9. Presupuesto de la primera prueba real (solo España, ACTIVCORE V2)
Condición: saldo ≥ 20 verificado. Profundidad **ligera**, país **solo España**, **máx. 10 ASIN**: 1 búsqueda (10) + 10 consultas de producto (10) = **20 tokens** (aprobar exactamente 20; `MISSION_CAP` 60 como techo acumulado; sin segunda búsqueda; los duplicados se bloquean). Antes: *Importar competidores ya obtenidos* (0 tokens). Pasos: `ENABLE=1` → EUROPA → País España → ANALIZAR EUROPA → Profundidad ligera, Máx. 10, Autorizar 20 → confirmar. Después compara `tokensConsumed` real con el estimado (el coste de `/product` es el único supuesto no verificado). Cualquier operación fuera de eso (otros países, 160 tokens) requiere nueva aprobación.

## 10. Reversión
- Referencia de recuperación: etiqueta Git `k1-recuperacion` = estado desplegable anterior (`cabcf70`).
- Inmediata y sin código: pon `AMAZON_PRO_KEEPA_ENABLE=0` (o bórrala) → Keepa apagado.
- Si algo falla tras fusionar: Render → *Deploys* → desplegar el despliegue anterior, o revertir el PR. Datos, usuarios y backups no se tocan.

## 11. Límites honestos
Sin probar en Render real (ni el redespliegue ni la lectura de la clave en el contenedor); `/product` y la comparabilidad automática sin validación real; títulos de la evidencia truncados; sin auditoría independiente de un segundo modelo. SP-API, Ads y OpenAI no se han tocado.
