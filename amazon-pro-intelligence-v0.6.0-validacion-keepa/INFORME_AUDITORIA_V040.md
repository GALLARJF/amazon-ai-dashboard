# Fase 0 · Auditoría de V0.4.0 (base de V0.5.0)
Alcance: repositorio y BD reales de V0.4.0 (carpeta `amazon-pro-intelligence-v0.4.0`, sin tocar). V0.5.0 es una COPIA; V0.3.4 y V0.4.0 permanecen intactas.

| Capacidad pedida | Estado en V0.4.0 | Acción en V0.5.0 |
|---|---|---|
| Autenticación, roles (analyst/approver/admin), CSRF, CSP, auditoría encadenada, solo 127.0.0.1 | HECHO | Reutilizado sin cambios |
| Conector Keepa (token, caché, presupuesto, cola, 429, ledger) | HECHO | Reutilizado; añadidos unidades, categoría y fecha del BSR |
| Motor europeo (economía, benchmark, ranking con pesos, sensibilidad) | HECHO (solo ACTIVCORE) | Generalizado por producto (`ctx`), normalización €/100 mL o €/100 uds |
| Director Amazon IA + 7 coworkers | HECHO (solo ACTIVCORE) | Conectados al expediente de cada producto |
| Catálogo central multiproducto/multicategoría | AUSENTE (producto fijo en código) | NUEVO `backend/catalog.py`: CRUD, versiones inmutables, archivado, categorías extensibles |
| Descubrimiento automático de competidores | AUSENTE (ASIN a mano) | NUEVO `backend/discovery.py`: términos→búsqueda→validación→dedup→score→Keepa |
| Comparabilidad | PARCIAL (solo manual) | Score 0–100 transparente: AUTOMATICA (usable, revisable) / CONFIRMADA (humana prevalece) |
| Cumplimiento por categoría | PARCIAL (solo cosmética) | Checklist cosmética (12) y suplementos (11, referencias «A VERIFICAR») |
| UI Categoría→Producto→Europa→Expediente→Director | AUSENTE | `js/eu.js` reescrito |
| Acceso directo Windows con icono | AUSENTE | `CREAR_ACCESO_DIRECTO.bat`, `tools/lanzador.py`, icono propio |
| Datos REALES de mercado | AUSENTE: 0 consultas Keepa reales | Sin cambios: se necesita tu clave y autorización |
Hallazgo: los datos de ACTIVCORE (coste 10,03 €, stock 550, PVP 49,90) están marcados HISTÓRICO/PROPUESTO y no se tratan como verificados.
