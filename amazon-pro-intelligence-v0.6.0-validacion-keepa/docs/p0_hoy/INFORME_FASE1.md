# Fase 1 — Navegación, selector de datos y compatibilidad con viewer

Base: `30ee37f` (incluye la corrección del viewer). Rama local `aht-p0-fase1`. Sin push, sin deploy, 0 € de gasto.
No se tocan: `server.py`, `backend/*`, contratos de API, datos, producción ni seguridad.

## Condiciones
| # | Condición | Estado Fase 1 |
|---|-----------|---------------|
| 1 | Rutas `/api/...` fuera del primer nivel de HOY | Nueva capa `js/nav.js` no las muestra; wireframes v2. Contenido de HOY (Evidencia/Metodología) → Fase 2 |
| 2 | Barra Android no tapa contenido | Padding inferior `88px + safe-area`; prueba automática con control negativo (`ui_nav_test`) |
| 3 | "5 riesgos abiertos: 0 críticos · 5 medios" | Diseñado en wireframes v2; implementación en HOY (Fase 2) |
| 4 | HOY: solo Situación, Ventas, Margen, Stock/riesgos, Decisiones, Prioridades | Wireframes v2; implementación Fase 2 |
| 5 | DECISIONES con 6 campos | Wireframes v2; implementación Fase 2 |
| 6 | DIRECTOR IA: Conclusión/Decisión abiertas, máx. 3 decisiones, técnica en Metodología | Wireframes v2; implementación Fase 2 |
| 7 | Selector DATOS REALES vs DEMO/SINTÉTICOS sin mezcla | Implementado (`ui_nav_modo_test` 17/17); en staging forzado a DEMO |
| 8 | `?legacy=1` transitorio | `PLAN_RETIRADA_LEGACY.md`: retirada en Fase 5 con 5 criterios medibles |
| 9 | Sin cambios backend/contratos/seguridad | Cumplido (solo index.html, styles.css, js/nav.js, tests, docs) |

## Resultados
- `ui_nav_test` (navegación interna, viewer, 3 viewports, barra móvil): 118/118
- `ui_nav_modo_test`: 17/17
- `viewer_test`: 32/32 · `ui_viewer_test`: 24/24
- Regresión `tests/run_all.sh`: todo OK salvo 2 suites heredadas (seguridad V0.2 49/53; API europea V0.4 43/45), previas a esta fase.

## Avisos
- El informe de auditoría `AUDITORIA_EJECUTIVA_..._E914144.md` no está en el repo ni en el entorno ni en Drive: hace falta que lo aportes.
- En staging el modo es DEMO forzado, así que HOY muestra el dataset demo.
- El chip de decisiones abre Aprobaciones hasta que la Fase 2 unifique bandejas.
- HOY y DECISIONES conservan aún el contenido legacy: Fase 1 es solo el armazón.
