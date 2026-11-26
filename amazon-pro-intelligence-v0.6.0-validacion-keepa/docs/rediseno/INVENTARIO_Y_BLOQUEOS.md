# Rediseño "Amazon Pro Intelligence Global" — Inventario mínimo y bloqueos (entrega 1)

Rama: `aht-rediseno-dashboard-global` (base `aht-regresion-y-auditoria-4-2-1`, PR #5 intacto). Sin merge, deploy, gasto, cuota API ni escritura en Amazon.

## Inventario (HECHO)
- **Servidor**: `server.py` (stdlib) + SQLite; estáticos por lista blanca (añadido `/styles7.css`).
- **UI**: shell `js/nav.js` (NAV6); nuevas piezas `js/dash7calc.js`, `js/dash7.js`, `styles7.css`. Interfaz anterior intacta con `?shell=6`.
- **Rutas internas conservadas**: lanz, ventas, prod, hoyold (accesibles por `NAV6.go`), Director IA (`#tab-dir`).
- **Auth/roles**: viewer solo lectura (POST bloqueado en servidor; `js/ro.js` bloquea controles salvo filtros `data-view-filter`). Staging fuerza viewer + datos sintéticos + conectores off.
- **Contratos reutilizados**: `V03.ask` (`/api/director/ask`), `/api/v06/decisions`, `/api/keepa/status` (solo lectura, sin exponer clave).
- **Tests**: `tests/dash7_test.py` (79 checks, 1920x1080/1440x900/390x844) + suites heredadas con `?shell=6`.

## Entrega 1: Dashboard (HECHO)
Cabecera (AHT, Benchmarking, Director IA, sesión), 4 filtros (+ subdivisión PHIVITAL), 6 KPI, donut de ventas netas, notificaciones y chat Director IA. Ejemplo coherente: 49900 / 41239,67 / 1000 uds / 4990 / 8990 / 7485 / 5410 / 14364,67 / 34,83 %. Ratios ponderados sobre ventas netas. Capturas en `docs/rediseno/capturas/`.

## Bloqueos / pendientes
- NO DISPONIBLE: fuente real de ventas AHT → modo real muestra «Sin datos».
- El chat usa `V03.ask`: requiere dossier y rol con escritura; viewer ve el compositor deshabilitado.
- Adjuntos y micrófono: rotulados PENDIENTE/limitados; no se simula conexión.
- Keepa: no se ha llamado; suscripción activa ≠ acceso API (por confirmar).
- POR CONFIRMAR: regresión amplia `run_all.sh` completa en esta rama (solo suites focalizadas ejecutadas).
- Entrega 2 (Benchmarking a pantalla completa): pendiente.
