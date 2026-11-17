# Integración futura con AHT Executive Neon (solo contratos)
No se ha modificado la plataforma principal. Amazon Pro Intelligence expone, bajo autenticación local, contratos JSON versionables:
- `GET /api/eu/overview` (producto, ranking, coworkers, cumplimiento, estado Keepa)
- `GET /api/eu/economics?country=&pvp=` · `GET /api/eu/benchmark?country=` · `GET /api/eu/export?what=benchmark|economics|ranking` (CSV)
- Cada coworker publica: estado, última ejecución, fuente, datos usados, hallazgos, bloqueos, próxima acción y enlace (cuenta/registro).
Reglas: datos DEMO/sintéticos y REALES nunca se mezclan (cuentas separadas: `activcore-eu`, `sintetico-primera-llamada`, `phivital-pendiente`); un integrador solo debe leer, y no puede convertir NO-GO/REVISAR/SIN DATOS en GO. Antes de integrar: SSO/MFA, cifrado en reposo, copias externas y anclaje de la auditoría (pendientes).
