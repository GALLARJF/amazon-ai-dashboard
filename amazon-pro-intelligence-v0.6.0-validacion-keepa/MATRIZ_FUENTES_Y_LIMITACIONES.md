# Matriz de fuentes y limitaciones (V0.5.0)
| Fuente | Estado | Qué aporta | Límite / coste | Qué falta |
|---|---|---|---|---|
| Keepa `/product` | Implementado, NO probado con datos reales | Precio, BSR, reseñas, histórico | ~1 token/ASIN (supuesto) | Verificar con `tokensConsumed` en la 1ª consulta |
| Keepa `/search` | Implementado, NO probado | Candidatos por término | ~10 tokens/consulta (supuesto) | Ídem |
| Keepa Product Finder, bestsellers, categorías | NO implementado | Descubrimiento más amplio | Product Finder ≈10 tokens + 1/100 ASIN; bestsellers ≈50/lista (terceros) | Decisión y autorización de gasto |
| Keepa para NL, PL, SE, BE, IE | No cubierto por el conector | — | — | Otra fuente compatible |
| Amazon SP-API / Product Advertising API | NO conectado (credenciales Amazon prohibidas en esta fase) | Catálogo, comisiones, FBA exactas | Requiere cuenta/credenciales | Alta y aprobación |
| Demanda real (búsquedas, ventas) | SIN FUENTE VÁLIDA | — | BSR es señal indirecta, no ventas | Fuente documentada |
| Costes logísticos/FBA/VAT/ads | Aportados por el usuario | Margen y ACoS | Sin dato → NO CALCULABLE | Costes con fuente y fecha |
| Regulación | Checklist, sin dictamen | Pendientes por categoría | No es asesoría legal | Documentación (PIF/CPSR/CPNP, ensayos) |
| OpenAI | Desactivado por defecto; consentimiento por consulta | Redacción del Director | Presupuesto configurable | Primera llamada real verificada |
Descubrimiento: sin scraping. Todo desde API autorizadas; la entrada manual de ASIN es opción avanzada y no cuenta hasta confirmar.
