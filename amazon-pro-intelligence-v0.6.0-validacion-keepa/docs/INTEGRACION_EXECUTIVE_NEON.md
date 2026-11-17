# Integración futura con Executive Neon (V0.2)

Estado: **contrato y exportación listos; NO enlazado**. La app no lee ni escribe en la plataforma principal.

## Contrato
`schemas/amazon-channel.schema.json` (`executive-neon/amazon-channel@1`). Se genera con `AmazonPro.exportPackage()` o con el botón «Descargar paquete (JSON)» en Estado.

| Entidad | Clave de negocio (`key`) | Destino en Executive Neon |
|---|---|---|
| `sales_channel_snapshot` | `amazon|mercado|sku|fecha_fin|Nd` | Ventas › Canal Amazon (+ Marketing: gasto/ACoS; Finanzas: margen; Logística: stock) |
| `alert` | `alert|módulo|regla|ámbito|fecha_fin` | Alertas compartidas (módulo: ventas, marketing, finanzas, logística) |
| `launch_dossier` | `dossier|nombre` | Expedientes compartidos |
| `approval_request` | `approval|tipo|título|origen` | Cola de aprobaciones compartida |

## Reglas para no duplicar ni alterar la plataforma
1. **IDs deterministas**: el mismo hecho de negocio produce siempre el mismo `id` (`amz-<tipo>-<16 hex>`). Re-exportar no crea registros nuevos.
2. **Upsert por `key`** en el consumidor. El estado mutable (p. ej. `status` de una aprobación) se actualiza, no se duplica.
3. **Un solo escritor**: Executive Neon es propietario de sus tablas; este módulo solo **produce** paquetes.
4. **Vistas por referencia**: `module_views` contiene solo ids; los datos viven una vez.
5. **DEMO nunca se ingesta**: `ingest_allowed=false` si el origen es DEMO. Un CSV lleva `api_verified=false` hasta conciliar con fuentes reales.
6. **Solo lectura**: ninguna operación del paquete modifica Amazon.

## Pasos pendientes
1. Acordar con Executive Neon los nombres/tipos de sus entidades y mapear los campos.
2. Implementar el importador (upsert por `key`) en la plataforma, con validación contra el esquema.
3. Autenticación entre sistemas (ver `SEGURIDAD_AUTENTICACION.md`).
4. Sustituir DEMO/CSV por fuentes reales verificadas.
