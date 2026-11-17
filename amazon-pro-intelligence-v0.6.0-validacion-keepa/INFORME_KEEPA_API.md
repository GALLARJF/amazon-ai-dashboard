# Informe del conector Keepa (V0.5.0)
## Qué hace
- HTTPS a `api.keepa.com` con lista blanca de rutas: `/token` (gratis), `/product`, `/search`.
- Clave en `%USERPROFILE%\AmazonPro\keepa.env`; nunca se imprime, guarda en BD, exporta, empaqueta ni envía a IA (tests con clave centinela lo comprueban).
- Interruptor `AMAZON_PRO_KEEPA_ENABLE` (por defecto 0). Sin él, cero llamadas.
- Control de tokens: saldo (`/token`), estimación previa, presupuesto por lote (30) y tope (120), aprobación explícita si se supera, registro de consumo (`keepa_ledger`), caché 24 h, deduplicación, cola con separación mínima, 429 → pendiente con ETA, respuestas incompletas → pendientes (no se inventa), 401 detiene todo.
- Datos: precio actual/Buy Box/lista, BSR, valoración, reseñas, ofertas nuevas, histórico, fecha de captura. Lo que Keepa no devuelve se muestra **NO DISPONIBLE** (p. ej. vendedor, ventas, CPC, conversión: Keepa no los da).
- Exportación CSV/JSON de la caché; registro de fuente en cada registro.
## Cobertura
DE, FR, IT, ES (y UK, separado). **NL, PL, SE, BE, IE: sin soporte en el conector** → esos países quedan NO EVALUABLE salvo datos aportados por otra vía.
## Supuestos NO verificados (se confirman en la primera consulta real)
Códigos de dominio (DE=3, FR=4, IT=8, ES=9, UK=2), coste ≈1 token/ASIN, `/search` ≈10 tokens (se corrige con `tokensConsumed`), nombres de campos y posiciones del array `csv`. Documentación: keepa.com/#!discuss/t/request-products. Con tu plan (1 token/min, 60 de saldo) un lote de 15 ASIN tarda ≈15 min en reponerse.
## Cómo verificar
`CONFIGURAR_KEEPA.bat` → ENABLE=1 → Probar conexión → 1 ASIN conocido → comparar precio/BSR con la ficha de Amazon.

## V0.5.0: descubrimiento
`/search` (≈10 tokens/página de hasta 10 resultados) y `/product` en lotes de hasta 100. Alternativas documentadas, NO implementadas: Product Finder (≈10 + 1 por 100 ASIN), bestsellers (≈50/lista), categorías (≈1). Documentación oficial de Keepa no accesible desde aquí: costes de fuentes de terceros; verificar con `tokensConsumed`.
