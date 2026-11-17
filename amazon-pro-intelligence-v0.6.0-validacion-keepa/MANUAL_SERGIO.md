# Manual de Sergio · Amazon Pro Intelligence V0.6 (Director Comercial Autónomo)

## Arrancar (Windows)
1. Doble clic en **CREAR_ACCESO_DIRECTO.bat** (una vez): crea un icono en el escritorio.
2. Doble clic en el icono (o en **INICIAR.bat**). Se abre el navegador solo. Si ya estaba abierto, abre el mismo (no duplica).
3. Primer arranque: usuario `admin` y la contraseña que muestra la ventana negra (solo una vez). Para cerrar: cierra la ventana negra; tus datos se conservan.

## Los cinco espacios
- **INICIO**: lo esencial en 30 segundos. Si aún no hay ventas reales verás la *preparación* (fichas, competidores, regulatorio). Cuando importes informes de Amazon verás ventas, ACoS y los cuatro gráficos. A la derecha, el **Director IA** y tu **bandeja de decisiones**.
- **LANZAMIENTOS**: elige el producto y pulsa **🚀 Preparar lanzamiento europeo**. El Director prepara solo lo permitido y te deja pendiente lo crítico. Aquí está el **expediente comercial** (11 secciones) y los botones para descargarlo (Markdown / HTML para imprimir o guardar en PDF).
- **MIS VENTAS**: importa informes CSV reales de Amazon (ventas y publicidad), mira la rentabilidad por país y el inventario.
- **PRODUCTOS**: catálogo central. Añade, edita o archiva productos sin programar (ACTIVCORE, PHIVITAL Magnesio y Omega-3 ya están).
- **DIRECTOR IA**: centro operativo: cola de tareas, niveles de autonomía, modelos de IA, libro de decisiones y el botón de **parada de emergencia**.
- «Avanzado» conserva las pantallas anteriores (el Panel DEMO usa datos ficticios y lo dice).

## Cómo leer los estados
`SIN DATOS` = no hay dato. `NO DETERMINABLE/NO CALCULABLE` = faltan datos (se dice cuáles). `PENDIENTE DE CONEXIÓN` = requiere una conexión con Amazon que aún no existe. `BORRADOR` = nada publicado. Nunca verás un 0 que signifique «no sé». `DEMO · SINTÉTICO` = datos de ejemplo, separados.

## Qué te pedirá el Director (solo lo crítico)
Aprobar: gasto de tokens Keepa, llamadas de IA de pago, publicar, cambiar precios, activar campañas, claims. Todo llega **agrupado** a la bandeja. Aprobar queda **registrado**; esta versión no ejecuta acciones externas en Amazon.

## Importar un informe de Amazon
MIS VENTAS → elige el producto → archivo CSV (Informe de ventas por ASIN/fecha, o de campañas de publicidad) → Importar. Se guarda sin modificar, con su huella, fechas y cobertura. Si el ASIN no coincide con el del producto te avisa.

## Flujo ACTIVCORE (prueba de aceptación)
PRODUCTOS → ACTIVCORE V2 → LANZAMIENTOS → 🚀 Preparar lanzamiento. Resultado hoy: expediente **NO DECIDIBLE todavía** porque faltan costes logísticos, evidencias regulatorias y comparables reales; el Director te lista exactamente qué aportar y deja pendiente tu aprobación de la consulta Keepa.

## Seguridad
Nunca pegues claves en el chat ni en los informes. Las claves viven en archivos locales fuera del proyecto (ai.env / keepa.env). El servidor solo escucha en 127.0.0.1.
