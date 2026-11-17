# Bloqueos antes de operar con Amazon (V0.2)

Estado: todos ABIERTOS salvo indicación. Se muestran también en la pestaña Estado de la aplicación.

| # | Bloqueo | Por qué bloquea | Cómo cerrarlo |
|---|---|---|---|
| 1 | Datos reales verificados | Todo el panel usa DEMO o CSV sin conciliar | Conectar SP-API (lectura) y conciliar con Seller Central |
| 2 | Conexiones reales con prueba | Ningún conector se ha probado con credenciales reales | Credenciales de solo lectura en entorno controlado + prueba desde Estado |
| 3 | Tarifas de comisión verificadas | Las tablas por categoría son orientativas (`verified:false`) | Contrastar con las tarifas vigentes de Amazon ES para cada categoría |
| 4 | Tarifas FBA, almacenaje y devoluciones | Se introducen a mano | Contrastar con calculadora de ingresos de Amazon e informes de tarifas |
| 5 | Base del ACoS (con/sin IVA) | Cambia el ACoS de equilibrio | Verificar en informes de Amazon Ads; ajustar «Base del ACoS» |
| 6 | Autenticación y permisos | Solo hay token de administrador local | Implementar SSO/roles según `SEGURIDAD_AUTENTICACION.md` |
| 7 | Persistencia y auditoría | Aprobaciones y expedientes viven en el navegador | Almacén servidor + registro inmutable |
| 8 | Revisión regulatoria | Plantillas de cosmético/complemento/otro son orientativas, no asesoramiento legal | Revisión del responsable regulatorio de AHT por producto |
| 9 | Conector de escritura | No existe por diseño | Diseño aparte con aprobación, límites, simulación y auditoría |
| 10 | Despliegue seguro | Solo local 127.0.0.1, sin TLS | Entorno de producción con TLS y gestor de secretos |
| 11 | Integración con Executive Neon | Contrato listo, importador no existe | Acordar esquema e implementar upsert por `key` |

Reglas que deben seguir vigentes: no cambiar precios, campañas ni publicaciones sin aprobación explícita; no usar DEMO como dato real; no declarar operativo ningún coworker ni conexión sin prueba real.
