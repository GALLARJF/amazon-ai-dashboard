# Plan de integración PR #7 (motor comercial) ↔ PR #8 (rediseño) y auditoría K1–K3 (26/11/2026)
Sin fusionar nada. Ramas hermanas sobre PR #5 (`aht-regresion-y-auditoria-4-2-1`, 460e385). PR #7 = `aht-motor-comercial-activcore` (a3ebd4f). PR #8 = `aht-rediseno-dashboard-global`.

## 1. Solapes (HECHO: calculado con `git diff` y fusión de prueba en un worktree desechado, sin commit ni push)
Ficheros tocados por ambas: `index.html`, `js/nav.js`, `server.py`, `tests/run_all.sh`, `tests/ui_lanz_test.py`.
- Auto-fusionan: `index.html`, `js/nav.js`, `tests/run_all.sh`, `tests/ui_lanz_test.py`.
- **Conflicto real único: `server.py`** (PR8 añade `validate_dash_context`, import `bench7`, ruta `/api/bench7/`, `/styles7.css`; PR7 añade rutas/imports comerciales). Resolución: conservar ambos bloques (aditivos).
- Sin solape lógico: PR7 = `backend/comercial.py`, `ads_lectura.py`, `api_comercial.py`, `js/comercial.js`; PR8 = `js/dash7*.js`, `js/bench7.js`, `backend/bench7.py`, `styles7.css`.

## 2. Orden recomendado (POR CONFIRMAR por José/ChatGPT; no ejecutado)
1. Aplicar correcciones de auditoría de PR #7 (comentario 7168593874, pendientes) y cerrar PR #7 primero (motor económico es dependencia de datos del dashboard).
2. Rebasar/fusionar PR #8 sobre ello resolviendo `server.py`.
3. Conectar: el Dashboard (KPI y donut) pasa de DEMO a «Sin datos»/real leyendo el motor de PR #7 (contribución EUR/unidad, objetivos 10/15/18/20 €); el Benchmarking reutiliza sus escenarios en vez de la fórmula local de `bench7.py`.
4. Regresión amplia completa (`run_all.sh`) una sola vez en la rama integrada.

## 3. Sin perder funcionalidades
- PR8 conserva la interfaz anterior con `?shell=6` y todas las rutas internas (`NAV6.go('lanz'|'ventas'|'prod'|'hoyold'|'dir')`); el panel comercial de PR7 cuelga de Lanzamientos/Productos y sigue accesible.
- Las suites heredadas apuntan a `?shell=6`; las suites de PR7 (`comercial_test` 67, `comercial_visual_test` 21) deben ejecutarse tras la integración.

## 4. Auditoría K1–K3 posterior a 17/11 (HECHO: ejecución de suites existentes, sin red)
Cambios posteriores: K3 (18/11): 72ea182, 7abe65d, a2bc076 (motor de segmentación competitiva, config, Director, UI).
| Suite | Resultado |
|---|---|
| k1_http_test | 12/12 OK |
| k1_keepa_test | 29/29 OK |
| k3_segmentacion_test | 90/90 OK |
| ui_k3_test | 37/37 OK |
Hallazgos: ninguno bloqueante en las suites. HIPÓTESIS/POR CONFIRMAR: el 91 % de K3 no es validación independiente (ya documentado en a2bc076); revisión de contenido de los umbrales por un humano pendiente. No se realizaron llamadas a Keepa.
