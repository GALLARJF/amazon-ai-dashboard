# Matriz de conexiones — reales vs pendientes (V0.2)

Fecha: 2026-11-16. **Ninguna conexión real está activa ni se ha probado**: no se han solicitado ni usado credenciales.

| Fuente | Alimenta | Código de prueba | Habilitada por defecto | Credenciales | Prueba real realizada | Estado real |
|---|---|---|:-:|---|:-:|---|
| Amazon SP-API | Ventas, costes/tarifas, inventario, reputación | Sí (solo lectura: token LWA + `marketplaceParticipations`) | No | No | **No** | PENDIENTE |
| Amazon Ads API | Publicidad (ACoS/TACoS), keywords | Sí (solo lectura: token LWA + `/v2/profiles`) | No | No | **No** | PENDIENTE |
| Keepa | Competencia y precios históricos | Sí (solo lectura: `/token`) | No | No | **No** | PENDIENTE |
| Helium 10 | Demanda y keywords | No (sin API pública verificada) | — | — | — | Solo por importación CSV (manual) |
| Brand Analytics | Términos de búsqueda, cuota | No | — | — | — | NO IMPLEMENTADO |
| Importación CSV | Ventas/costes manuales | Sí (validación + advertencias) | Disponible | — | Sí (pruebas automáticas) | DISPONIBLE; datos sin verificar vía API |
| Executive Neon | Ventas › Canal Amazon, Marketing, Finanzas, Logística | Sí (esquema + validación + exportación) | — | — | Sí (esquema) | CONTRATO LISTO · NO ENLAZADO |

**Qué significa «código de prueba»**: está implementado y probado con transporte simulado y secretos falsos; no demuestra que funcione contra el servicio real (endpoints, permisos y regiones reales deben validarse).

Para habilitar una conexión en un entorno controlado (más adelante): `AMAZON_PRO_CONNECTORS=keepa` + variables de credenciales + `AMAZON_PRO_ADMIN_TOKEN`; probar desde Estado con el token.
