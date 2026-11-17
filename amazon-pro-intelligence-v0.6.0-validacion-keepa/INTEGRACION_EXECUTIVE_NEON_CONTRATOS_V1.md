# Contratos versionados para AHT Executive Neon (v1)
Ruta futura: Ventas → Canales de Venta → Amazon (con Marketing, Finanzas, Logística, Presidencia como consumidores). El módulo es aislado: no duplica módulos corporativos ni modifica el master. Solo lectura; todo exige sesión; los consumidores no pueden convertir REVISAR/NO EVALUABLE en GO.
| Contrato | Endpoint | Campos clave |
|---|---|---|
| catalog.v1 | `GET /api/catalog`, `/api/catalog/product?id=` | id, name, brand, category, version, format, pvp/costs/stock (valor+estado+fuente+fecha), regulatory, missing |
| discovery.v1 | `GET /api/discovery/plan?product=`, `/last` | países, términos+origen, consultas, tokens previstos, estado, pendientes |
| market.v1 | `GET /api/eu/overview|benchmark|economics?product=` | ranking (evaluable, cobertura, faltantes), benchmark (comparabilidad+score+BSR cat/fecha), economía por PVP |
| coworker.v1 | dentro de overview | estado, última ejecución, fuente, datos, hallazgos, bloqueos, próxima acción, enlace |
| export.v1 | `GET /api/eu/export?what=` | CSV ranking/benchmark/economía |
Cambios incompatibles → `v2` con rutas nuevas; V0.4.0 sigue funcionando (producto por defecto PRD-ACTIVCORE-V2). Roles, auditoría, evidencias y aprobaciones se heredan del módulo. Pendiente antes de integrar: SSO/MFA, cifrado en reposo, copias externas.

## Adenda V0.6.0 (F14)
- La app sigue siendo independiente; no modifica el sistema corporativo ni duplica maestros (el catálogo es local y exportable).
- Nuevos contratos de lectura (JSON, solo sesión local): `GET /api/v06/home`, `/launch?product=`, `/tasks`, `/decisions`, `/ledger`, `/imports`, `/connections`. Escritura bajo rol aprobador/admin con CSRF.
- Flujo futuro previsto: Presidencia → Ventas → Canales de Venta → Amazon; compartir resultados con Marketing, Finanzas, Logística y Dirección General mediante estos contratos (sin acceso directo a la BD). Nada de esto está integrado todavía.
