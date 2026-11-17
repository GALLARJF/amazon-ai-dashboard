# Decisiones de diseño V0.5.0
1. Copia de V0.4.0, no sobrescritura; datos de ACTIVCORE conservados (prefijo vacío en cuenta activcore-eu).
2. Productos nuevos en cuenta `catalogo-aht` con claves prefijadas: aislamiento por producto sobre caché Keepa compartida.
3. Datos `DOCUMENTADO/VERIFICADO` exigen fuente (≥8 car.) y fecha; lo ausente es NO_DISPONIBLE, nunca 0.
4. Comparabilidad automática = heurística determinista, usable y revisable; la confirmación humana prevalece.
5. Descubrimiento: coste previo siempre; `approved_tokens` es tope duro; ejecuciones parciales reanudables con caché de 24 h; solo admin ejecuta.
6. Costes Keepa (10/búsqueda, 1/ASIN) son supuestos configurables hasta verificar con `tokensConsumed`.
7. Términos de búsqueda: biblioteca lingüística (serum capilar, magnesio, omega-3 en ES/DE/FR/IT); sin términos → FALTAN_TERMINOS.
8. Sin GO operativo: ranking exige cobertura mínima; sin costes logísticos queda NO EVALUABLE.
9. Windows: lanzador Python con control de puerto e instancia única; acceso directo vía PowerShell (.lnk con icono propio).
