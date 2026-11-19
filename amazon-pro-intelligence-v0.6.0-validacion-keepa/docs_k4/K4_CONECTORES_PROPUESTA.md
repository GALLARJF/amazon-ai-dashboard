# K4 · Propuesta de activación de conectores (NADA ACTIVADO)
Estado: Keepa de pago **desactivado**, SP-API y Ads **NO_OPERATIVO**, IA externa **desactivada**. Esto es una propuesta para tu decisión; no se ha hecho ninguna llamada.

## 1. Keepa (solo lectura, refresco de precios vigentes)
**Hallazgo:** de los 5 competidores seleccionados, **solo Kérastase tiene ASIN**; los otros cuatro son referencias de maqueta sin ASIN. Sin ASIN no hay precio vigente ni foto autorizada posible.
| Marca (selección K3) | ASIN | País |
|---|---|---|
| KÉRASTASE | B083JKPCFB | ES |
| Nioxin | **sin ASIN** | ES |
| Redken | **sin ASIN** | ES |
| The Ordinary | **sin ASIN** | ES |
| Bio-Pilixin | **sin ASIN** | ES |

| Opción | ASIN a consultar | Tokens estimados (plan sin consumir) | Frecuencia |
|---|---|---|---|
| A · mínima | los 5 de la comparativa que tengan ASIN (1) | ≈ 1 | una vez |
| B · explorador | los 20 ASIN conocidos de las 24 referencias (ES) | ≈ 20 (1 token/ASIN, parámetro del sistema; presupuesto de lote configurado 30) | una vez, luego semanal |
- Cálculo hecho con `Keepa.plan()` offline (sin red). El consumo REAL lo marcará `tokensConsumed` de la respuesta y queda en el libro; el coste por token **no está verificado** en esta propuesta.
- Antes de pedir tokens: **identificar los ASIN de las 4 referencias sin ASIN** (búsqueda manual en Amazon.es por vuestro equipo; una búsqueda Keepa cuesta ≈10 tokens y no se hará sin tu OK).
- Datos necesarios: precio vigente (Nuevo/Buy Box), fecha, volumen del título. Imágenes: **no** se descargan (términos de Keepa no verificados).
- Para activarlo necesito: tu autorización expresa, opción A o B, tope de tokens y la variable de clave en Render (la configuras tú; no pasa por el chat).

## 2. SP-API (Seller Central) — datos propios
- Datos: pedidos/ventas, sesiones y conversión (Business Reports), inventario FBA, devoluciones, tarifas. Solo ACTIVCORE/PhiVital propios; sin ventas inventadas.
- Requiere: registrar la aplicación privada en Seller Central, autorización OAuth del vendedor (rol y alcance de solo lectura), credenciales en Render. Coste de API: **no verificado**; la documentación oficial debe confirmarse antes de activar.
- Frecuencia propuesta: diaria (informes) tras validar en un mes de datos con importación manual.
- Mientras tanto: importación CSV de informes reales (ya operativa, con duplicados, conflictos y conciliación).

## 3. Amazon Ads
- Datos: gasto, ventas atribuidas, clics, impresiones por campaña/ASIN. Requiere perfil de Ads y acceso a la API de Ads (alta aparte; **requisitos de acceso no verificados**). Frecuencia: diaria. Mientras tanto, importación CSV.

## 4. Reglas de seguridad previstas
Solo lectura; tope de gasto 0 € hasta aprobar otro; parada de emergencia del planificador; ningún cambio de precio/campaña desde K4; credenciales solo en secretos de Render; registro de cada llamada.
