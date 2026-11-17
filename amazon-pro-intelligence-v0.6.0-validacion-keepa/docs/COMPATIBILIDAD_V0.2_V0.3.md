# Informe de compatibilidad V0.2 → V0.3
V0.1 y V0.2 se conservan **intactas** (carpetas y ZIP originales; hashes sha256 comprobados al cierre, ver `evidencia_integridad_V01_V02.txt`). V0.3 es una copia de V0.2 con cambios aditivos.

| Área | V0.2 | V0.3 | Compatibilidad |
|---|---|---|---|
| Motor económico | `js/economics.js` | Se conserva sin cambios; **port Python** `backend/engine.py` | 657/657 casos idénticos JS↔Python (`tests/parity_test.py`) |
| Expediente Pre-Launch | `js/dossier.js` + localStorage | Sin cambios; se añade copia servidor y `backend/pilot.py` (costes documentados) | Misma lógica GO/REVISAR/NO-GO; el piloto añade exigencia de evidencia de costes |
| Contrato Executive Neon `amazon-channel@1` | paquete sin ámbito | `source.scope` **opcional** (cuenta, titular legal, Seller Central, marketplaces); claves con prefijo `acct:<id>\|` | Paquetes V0.2 siguen válidos (`version 0.2`); con ámbito `version 0.3`; IDs distintos por cuenta (`tests/scope_test.js`) |
| API HTTP | `/api/status`, `/api/connectors/test` | Se mantienen idénticos (53/53 pruebas de seguridad heredadas) + API autenticada | Aditivo |
| Seguridad | token admin de conectores | + sesiones HttpOnly, CSRF, roles, aislamiento por cuenta, auditoría encadenada | Conectores siguen deshabilitados por defecto |
| Coworkers | 7 reglas locales sobre datos DEMO (`js/coworkers.js`) | 7 coworkers servidor (`backend/coworkers.py`), estado real | `js/coworkers.js` y `js/director.js` **se conservan pero ya no se cargan** (V0.2 respondía con reglas locales; V0.3 no mezcla ambos) |
| Director | reglas locales en navegador | Servidor: orquestación + IA opcional | Rompe a propósito: el Director V0.2 ya no existe en la UI |
| UI | neón horizontal 1600×840 | Se conserva; pestañas nuevas Piloto e Historial; Pre-Launch V0.2 queda como «Pre-Launch (local)» | Diseño aprobado intacto |
| Pruebas | 186 comprobaciones | Las suites JS/seguridad heredadas pasan; UI reescrita para V0.3 | `ui_test.py` de V0.2 sustituido (referenciaba controles retirados) |

## Rupturas conocidas (declaradas)
1. La cola local de aprobaciones del navegador (V0.2) sigue existiendo pero **no es** la aprobación del servidor; las aprobaciones V0.3 viven en el servidor (rol approver).
2. Ya no hay modo sin servidor para el Director/coworkers: requieren `server.py` y sesión.
3. `tests/ui_test.py` de V0.2 se reemplazó; los resultados V0.2 se conservan en la carpeta V0.2.

## Multi-marca / multi-cuenta / multi-titular
Cada registro (`records`) pertenece a una `account` (titular legal + referencia Seller Central + marketplaces). Todas las lecturas/escrituras filtran por cuenta; un id de otra cuenta devuelve 404/403 y no puede sobrescribirse (`tests/store_test.py`, `tests/api_test.py`). El paquete de integración lleva el ámbito y no comparte IDs entre cuentas. **Limitación:** una marca por cuenta aún no tiene entidad propia en UI (campo `brand` en expediente), y `marketplaces` es informativo hasta que existan conectores.
