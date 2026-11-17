# VALIDACIÓN REAL DE KEEPA · ACTIVCORE V2 · España — V0.6.0
Fecha de la misión: 2026-11-17 (Europe/Madrid) · Ejecutor: Claude · Presupuesto autorizado: **10 tokens Keepa**

## 0. Resumen
- **Conexión real con Keepa: VERIFICADA** (llamadas reales a `api.keepa.com`, clave leída de `keepa.env`, nunca mostrada ni exportada).
- **Consumo confirmado: 10 tokens** (la respuesta de Keepa informa `tokensConsumed = 10`). Tope de misión: 10. Restante: 0. No se superó.
- **Descubrimiento automático real:** 1 búsqueda en Amazon España devolvió **20 productos** (ASIN no introducidos a mano) con precio y BSR observados.
- Los resultados se incorporaron al expediente ACTIVCORE por el flujo normal del Director IA (orden → bandeja → aprobación de lectura Keepa → ejecución) y se ven en la interfaz NEON.
- **El expediente sigue «NO DECIDIBLE TODAVÍA»**: faltan costes logísticos, evidencias regulatorias y stock. No se publicó nada en Amazon ni se activó publicidad.

## 1. Estado real de la conexión
| Elemento | Estado | Evidencia |
|---|---|---|
| Clave Keepa en `keepa.env` | Presente y válida (Keepa la aceptó) | llamadas 200 OK |
| `GET /token` | REAL VERIFICADO, no consume tokens | saldo 60 antes y después de consultarlo |
| `GET /search` dominio ES (= 9) | REAL VERIFICADO, **coste real 10 tokens** | `keepa_ledger.json`, `mision_operaciones.json` |
| `GET /product` (coste por ASIN) | **NO VERIFICADO** (no se ejecutó: no cabía en el presupuesto) | — |
| Dominios DE/FR/IT/UK, ratings, vendedor | **NO VERIFICADOS** | — |
| NL/PL/SE/BE/IE | Keepa no los cubre (supuesto documentado, no probado) | — |

## 2. Saldo y consumo
| Momento (UTC) | Tokens disponibles | Nota |
|---|---|---|
| 01:05:52 | 60 | `/token` (gratuito), recarga 1 token/min |
| 01:07:51 | 60 | antes de buscar |
| 01:07:57 | 50 | tras `/search` (−10) |
| 01:08:59 | 51 | +1 por recarga natural; no es consumo |
**Tokens consumidos en la misión: 10 (confirmado).** Saldo final verificable: 51 (a las 01:08:59 UTC).

## 3. Endpoints y consultas
- `/token`: 3 consultas (gratuitas). `/search`: **1** consulta de pago (identificador de operación `KP-20261117010755-b7c971`). `/product`: 0.
- Término de búsqueda (generado automáticamente por la biblioteca de subcategoría, no escrito a mano): «sérum capilar cuero cabelludo». Dominio ES.
- Limitación: el cliente conserva como máximo 20 resultados por búsqueda; no sé si Keepa devolvió más. La respuesta cruda no se archivó (solo los registros normalizados): **defecto de evidencia reconocido**; repetirla costaría otros 10 tokens, así que no se repitió.

## 4. Resultados comerciales (observados, no extrapolables)
Fuente de todos los datos: Keepa API `/search` (api.keepa.com), consulta del 2026-11-17. **Muestra de 20 ASIN de UNA búsqueda; no es un estudio de Amazon España.**

| Marca | Producto | ASIN | Formato mL (inferido del título) | Precio € (observado) | €/100 mL (derivado) | Fecha del último punto de precio | Tipo / comparabilidad (heurística) | BSR |
|---|---|---|---|---|---|---|---|---|
| REDKEN | Redken Acidic Grow Sérum Pelo para Tratamiento Anticaíd | B0G59MCQT6 | 100.0 | 29.99 | 29.99 | 2026-05-22 | DIRECTO ALTA | 1731 |
| OGX | OGX ProGrowth + Peptide Champú Clarificante, Exfoliante | B0G6KTWQ8N | 385.0 | 5.41 | 1.41 | 2026-11-10 | INDIRECTO BAJA | 666 |
| FANOLA | Fanola, Cuidado del pelo y del cuero cabelludo - 1 unid | B00CGPLQY6 | ND | 14.0 | ND | 2026-11-13 | DIRECTO MEDIA | 5691 |
| SERQIA | Serum de crecimiento del cabello con cepillo integrado, | B0HG1D9G3D | ND | 11.99 | ND | 2026-10-28 | DIRECTO MEDIA | 9046 |
| KTouler | PDRN Hair Scalp Serum Built-In Brush,Masajeador Revital | B0HC63QWN9 | ND | 19.99 | ND | 2026-11-12 | DIRECTO MEDIA | 13023 |
| Sylk | Sylk Aceite de Romero para el Cabello - Crecimiento, An | B0HHFQGZ5V | ND | 12.97 | ND | 2026-11-02 | INDIRECTO BAJA | 28680 |
| LOBALABS | Lobalabs Raíz Viva Serum Capilar Aceite de Romero para  | B0H4X4RVNH | ND | 13.85 | ND | 2026-11-09 | INDIRECTO BAJA | 8825 |
| WoldoHealth | WoldoHealth Aceite de Romero Capilar para Cabello - Ser | B0C6NMCXQR | ND | 14.99 | ND | 2026-11-11 | INDIRECTO BAJA | 14974 |
| SANA- T ON CALM | SANA-T ON CALM SERUM 125ml. Reduce el picor del cuero c | B099ZTJKDL | 125.0 | 14.99 | 11.99 | 2025-06-12 | DIRECTO MEDIA | 25844 |
| KÉRASTASE | Kérastase Nutritive Sérum Profesional Pelo Para Cuero C | B0BZZK7GJB | 90.0 | 38.89 | 43.21 | 2026-11-03 | DIRECTO ALTA | 10915 |
| KÉRASTASE | Kérastase Genesis Sérum Anti-chute Tratamiento Anticaíd | B083JKPCFB | 90.0 | 39.94 | 44.38 | 2026-11-16 | DIRECTO ALTA | 57 |
| ZREVSB | Sérum Anticaída para Cabello, Suero Nutritivo Cuero Cab | B0HH6H6FHC | 60.0 | 6.99 | 11.65 | 2026-10-31 | DIRECTO MEDIA | 6412 |
| Australian Bodycare | Australian Bodycare Scalp Serum 150 ml / Hidratante par | B07DJK7R2B | 150.0 | 14.99 | 9.99 | 2026-10-25 | DIRECTO MEDIA | 7979 |
| AROMATICA | AROMATICA Potenciador de raíz de romero 3.38oz/100ml- S | B01MU9AUX7 | 100.0 | 17.06 | 17.06 | 2026-09-03 | DIRECTO ALTA | 3824 |
| KÉRASTASE | Kérastase Specifique Sérum de Pelo Profesional Para el  | B09GBBFYF7 | 90.0 | 38.18 | 42.42 | 2026-11-12 | DIRECTO ALTA | 13045 |
| Pantene | Pantene Grow Abundant Sérum Anticaída para Un Pelo más  | B0FPLQR5XW | 60.0 | 9.99 | 16.65 | 2026-11-10 | DIRECTO MEDIA | 81 |
| VT COSMETICS | VT COSMETICS PDRN Reedle Shot Sérum Capilar con Cepillo | B0GGQMYLXM | ND | 35.5 | ND | 2026-11-16 | DIRECTO MEDIA | 2434 |
| L'Oreal Paris | L'Oréal Paris Elvive Growth Booster Serúm Tratamiento A | B0DWFSJ9Y4 | 100.0 | 6.26 | 6.26 | 2026-11-09 | INDIRECTO BAJA | 31 |
| Transparent Lab | Transparent Lab Scalp Calming Treatment Sérum Cuero Cab | B0D5HTCRW6 | 50.0 | 13.27 | 26.54 | 2026-11-10 | DIRECTO ALTA | 7336 |
| Head & Shoulders | H&S DermaXPro Sérum Hidratante para Cuero Cabelludo Sec | B0BDZY6ZDN | 145.0 | 6.99 | 4.82 | 2026-10-27 | DIRECTO MEDIA | 2695 |

Notas de lectura:
- **Precio observado** = último valor de la serie «nuevo» de Keepa; **no es necesariamente el precio de hoy** (3 ASIN tienen su último punto antes del 2026-10-01: B0G59MCQT6 en mayo 2026, B099ZTJKDL en junio 2025, B01MU9AUX7 en septiembre 2026). Cada fila lleva su fecha.
- **Formato** inferido del título; 13 de 20 lo permiten. Sin formato, el precio por 100 mL queda en ND (no se inventa). Los precios de packs o multiformato no están ajustados.
- **Valoraciones y vendedor: NO DISPONIBLES** (la búsqueda no los devuelve; no se inventaron).
- **Precios de competidores ≠ ventas.** El BSR es una posición de ranking, no unidades vendidas; no se estimaron ventas.
- **Comparabilidad AUTOMÁTICA = heurística revisable**: hay casos dudosos (p. ej. un champú, un producto de uso oncológico, aceites de romero). Solo una persona puede marcar «CONFIRMADA».
- Estadística descriptiva (solo de esta muestra): precios observados de 5,41 € a 39,94 €; 13 referencias con precio/100 mL, de 1,41 a 44,38 €, mediana 16,65 €. El PVP objetivo de ACTIVCORE (49,90 € por 100 mL) queda por encima de las 13 referencias normalizables de esta muestra. **Esto describe la muestra; no es una recomendación de precio ni una conclusión de mercado.**

Clasificación de datos: **observado** (marca, título, ASIN, precio, BSR, fechas), **derivado** (€/100 mL), **inferido** (formato leído del título, comparabilidad automática).

## 5. Verificación del motor económico
- ACTIVCORE conserva únicamente su coste documentado (10,03 €): prueba pasa (también para ES).
- PHIVITAL Magnesio **no hereda** costes de ACTIVCORE: prueba pasa (coste = None).
- Sin tarifas FBA/FBM, transporte, preparación, almacenamiento y devoluciones, la rentabilidad es **NO CALCULABLE** y lista lo que falta; no se inventó ninguna tarifa.
- Los precios de competidores no entran en ningún cálculo de ventas.

## 6. Director IA y expediente (flujo real)
Orden «Preparar lanzamiento» → el Director creó 6 tareas y ejecutó solo las de nivel N1 (cumplimiento, economía, plan de descubrimiento, borrador de listing, expediente) → dejó `discovery.run` en la bandeja → **aprobación de lectura Keepa de esta misión** (registrada con el nombre del autorizador, tope 10, solo ES) → ejecución real → expediente reconstruido con 20 competidores. Persistente en SQLite; libro de decisiones y consumo registrados; no se publicó nada.

## 7. Errores encontrados y corregidos
1. **No existía tope acumulado de misión** (solo un tope por lote de 30/120). Añadido: contador de consumo confirmado, presupuesto restante, identificador de operación, anti-duplicados, parada **antes** de la red y peor caso para operaciones inciertas.
2. **`discovery.run` desde la bandeja nunca recibía presupuesto** (el manejador leía una clave inexistente `est_tokens` → 0 tokens → «REQUIERE_AUTORIZACION»). Corregido, y limitado a los países de la misión.
3. El manejador del plan devolvía `tokens_estimados: None` (clave equivocada). Corregido.
4. La búsqueda **descartaba los datos de producto** que Keepa ya devuelve (obligaba a gastar 1 token/ASIN extra). Ahora se aprovechan, sin llamadas extra.
5. El precio observado no llevaba fecha. Añadido `price_as_of` y columna en la tabla.
6. Regresión detectada por `v050_test` (candidatos sin precio contaminaban el benchmark): corregida; los candidatos sin precio no se guardan como dato.
7. La pantalla «Conexiones» decía que los costes eran supuestos «hasta la primera llamada real»; ahora distingue lo verificado de lo no verificado.

## 8. Pruebas
**REALES (datos o llamadas reales):**
- Conexión a Keepa, `/token`, `/search` ES y descubrimiento automático (la misión misma; evidencias en `docs_v06/evidencia_keepa_real/`).
- Prueba de coherencia de evidencias reales: 9/9 (lee los ficheros de la llamada real; no usa red).
- Comprobación visual en navegador automatizado real con los datos reales (capturas 30–33).
**SIMULADAS (mock; sin red):**
- Presupuesto de misión, presupuesto agotado, duplicados, error de API (401/429/500), datos incompletos, persistencia tras reabrir la base, separación DEMO/REAL, flujo completo del Director con tope 10: `keepa_mision_test` 18/18 y `keepa_mision_flow_test` 16/16.
- Suites anteriores: v060 74/74, keepa 27/27, v050 43/43, v040_api 45/45, api 51/51, ui_v06 27/27, launcher 8/8, y el resto de la batería `run_all.sh`.
**Fallo/Reserva honesta:** en la ejecución completa de `run_all.sh` la prueba del lanzador Windows se quedó colgada una vez (un servidor hijo huérfano retiene la tubería cuando se solapan ejecuciones) y se mató a mano; ejecutada sola pasa 8/8 y el resto de la batería salió OK. No es un fallo del código de Keepa, pero la batería completa limpia de una sola vez no la tengo.
**NO VERIFICADAS:** coste real de `/product`; dominios DE/FR/IT/UK; OpenAI/IA real; Amazon SP-API/Ads; Windows real; ratings y vendedor.

## 9. Capturas reales
`CAPTURAS_UI/30_REAL_inicio_activcore.png`, `31_REAL_lanzamientos_competidores.png`, `32_REAL_director_cola_libro.png`, `33_REAL_conexiones_keepa.png`.

## 10. Estado final del expediente ACTIVCORE
- Competidores ES: 20 (15 «DIRECTO», 5 «INDIRECTO»; comparabilidad AUTOMÁTICA, ninguna confirmada).
- España: «CON DATOS PARCIALES». DE/FR/IT: SIN DATOS. NL/PL: pendientes de conexión.
- Economía: NO CALCULABLE. Cumplimiento: 72 requisitos sin evidencia (publicación bloqueada). Recomendación: **NO DECIDIBLE TODAVÍA**.

## 11. Manejo de la clave y límites de la misión
- La clave se leyó de `keepa.env` en tu carpeta AmazonPro (con tu permiso) y se copió al espacio de trabajo en la nube **solo para esta misión**; no aparece en informes, logs, ledger, caché ni ZIP (comprobado por pruebas y búsqueda de texto). Las copias del espacio de trabajo se borraron al terminar.
- No se hicieron recargas ni compras; no se usó ninguna API de IA de pago; no se modificó Amazon; no se inició V0.7.0.

## 12. Recomendación para ampliar a otros países
1. **Antes de gastar más en países:** verificar `/product` con **1 ASIN** de los ya descubiertos (≈1 token) para conocer el coste real por ASIN y obtener rating/reseñas.
2. Cada búsqueda cuesta 10 tokens: DE, FR e IT serían ≈30 tokens más, y primero habría que confirmar sus códigos de dominio (hoy son supuestos). Con recarga de 1 token/min y un saldo de ~51, es viable en una misión posterior con un tope explícito (sugerido: 40).
3. Confirmar a mano la comparabilidad de los 6 competidores ALTA antes de usar la mediana como referencia.
4. NL/PL/SE/BE/IE requieren otra fuente (importación manual o proveedor alternativo).
5. Lo que más desbloquea el expediente no es Keepa: son los **costes logísticos de ACTIVCORE** y las **evidencias regulatorias**.

## 13. Archivos
`docs_v06/evidencia_keepa_real/` (competidores_ES.csv/json, keepa_ledger.json, mision_operaciones.json, saldo.json) · `tests/keepa_mision_test.py`, `keepa_mision_flow_test.py`, `keepa_real_evidence_test.py` · código: `backend/keepa.py`, `backend/discovery.py`, `backend/api6.py`.
