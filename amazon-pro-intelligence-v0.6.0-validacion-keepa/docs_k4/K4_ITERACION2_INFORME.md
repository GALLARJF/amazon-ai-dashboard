# K4 · Iteración 2 — informe de cambios
Rama `aht-k4-ejecutivo` · PR #4 (sin fusionar, sin desplegar). Gasto adicional 0 €, Keepa de pago desactivado, IA externa desactivada, ningún dato comercial real modificado.

## Qué cambia
1. **Benchmarking en 3 niveles** (pestaña K4 → Benchmarking visual): *1 Comparativa ejecutiva* (ACTIVCORE destacado + 5 columnas de referencia, filas: precio, volumen, €/100 mL, activos, dosis, duración, coste/día, posicionamiento, evidencia, equivalencia, ventajas; estado de cada celda; dictamen debajo), *2 Explorador* (24 referencias en tabla con búsqueda, filtros, orden y alta/baja de la comparativa con motivo auditado), *3 Expediente 360°*. Las 24 tarjetas con foto desaparecen.
2. **Selección de los 5** por K3 (premium y funcional especializado, por equivalencia estimada) con justificación; ajustes manuales auditados (motivo ≥ 8 caracteres, aprobador) y persistentes.
3. **Director**: 8 secciones por dictamen + diagnóstico (PVP, subir/bajar, causa de falta de ventas, ventaja competitiva, prioridades) + plan de investigación. Sin datos → sin cifra inventada.
4. **Umbrales** configurables por producto/categoría/país/etapa, **ninguno aprobado**; sin aprobación en producción el dictamen es «evidencia insuficiente». Los valores 15 % / ±15 % / 5 % / 14 d son solo ilustrativos en demo sintética.
5. **Costes**: 10,03 €/ud sigue como histórico con alcance pendiente; no se suman componentes.
6. **Importación**: duplicados por fila omitidos, conflictos sin sobrescribir, reemplazo explícito, conciliación (huecos, pedidos>sesiones, devoluciones>unidades, importes, Ads sin ventas).
7. **Planificador robusto** (solo trabajos internos): ejecución única, persistencia, recuperación tras reinicio, reintentos con espera, registro de errores, tope de gasto 0 €, parada de emergencia y kill switch, medición posterior. No arranca solo.
8. **CI**: el workflow estaba dentro del subdirectorio y GitHub solo lee `.github/workflows` de la raíz → nunca se ejecutaba. Movido a `.github/workflows/k4-ci.yml`.
9. **Accesibilidad/móvil**: caption y `scope`, regiones desplazables con teclado, foco visible, `aria-selected`, comparación por pares en móvil, objetivos táctiles ≥ 38 px, `prefers-reduced-motion`.

## Hallazgos que debes conocer
- De los 5 competidores seleccionados **solo Kérastase tiene ASIN**; los otros 4 son referencias de maqueta → sin precio vigente ni foto posible hasta identificar ASIN.
- Solo hay 1 precio vigente premium (mínimo 3): la posición de precio es NO EVALUABLE.
- Las cifras de la infografía (PVP, dosis, duración, concentración) se muestran como «MAQUETA · no verificado» y no entran en estadísticos.
- Los cinco espacios principales de V0.6 no se han tocado (ui_v06 27/27).

## Decisiones pendientes tuyas
Alcance de los 10,03 €; permisos de imagen / ASIN de las 4 referencias; export de Seller Central; aprobación de umbrales (por una segunda persona); autorización de Keepa (ver `K4_CONECTORES_PROPUESTA.md`).
