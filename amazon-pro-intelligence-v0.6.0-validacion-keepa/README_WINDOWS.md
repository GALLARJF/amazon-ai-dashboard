# Amazon Pro Intelligence V0.6.0 · Director Comercial Autónomo (AHT Executive Neon)

## Instalar y abrir (Windows, sin programar)
1. Descomprime `amazon-pro-intelligence-v0.6.0.zip` en una carpeta NUEVA (no encima de V0.3.4).
2. Doble clic en `INICIAR.bat`. Se abre http://localhost:8765 (solo accesible desde tu ordenador).
3. **Tus expedientes y usuarios**: cierra la app, copia `data\amazon_pro.db` de la carpeta antigua a `data\` de la nueva y vuelve a abrir. (Ver `GUIA_ACTUALIZACION_SEGURA.md`.)
4. Entra con tu usuario admin → pestaña **EUROPA · MERCADOS**: elige Categoría → Producto → **ANALIZAR EUROPA**. Si no recuerdas la contraseña: `RESTABLECER_ADMIN.bat`.

## Activar Keepa (cuando tú decidas gastar tokens)
1. Doble clic en `CONFIGURAR_KEEPA.bat` → pega tu clave en `%USERPROFILE%\AmazonPro\keepa.env` (fuera de la carpeta del proyecto).
2. Déjalo con `AMAZON_PRO_KEEPA_ENABLE=0`. Para consultar: ponlo a `1`, guarda y reinicia `INICIAR.bat`.
3. En la pestaña Europa (como admin): «Probar conexión» (gratis, muestra tokens) → pulsa **ANALIZAR EUROPA**: la app propone términos de búsqueda por idioma, calcula los tokens ANTES de gastar y te pide autorizar un máximo. No hace falta introducir ASIN (la entrada manual es opción avanzada).

## Qué ves ahora mismo (sin datos reales)
Ranking en **SIN DATOS SUFICIENTES**, países **NO EVALUABLE**, márgenes **NO CALCULABLE** hasta que existan costes logísticos y comparables confirmados. Es lo correcto: nada se inventa.

## IA
La IA (OpenAI) sigue desactivada por defecto. El Director Europeo responde con cálculo determinista; solo redacta con IA si marcas «usar IA» y confirmas un diálogo con proveedor, modelo, coste máximo, presupuesto, finalidad y texto exacto. Mientras la IA real no esté verificada con el expediente sintético, no se envía nada real.

## Acceso directo en el Escritorio
Doble clic en `CREAR_ACCESO_DIRECTO.bat`: crea «AHT Amazon Pro Intelligence» con icono propio. Al abrirlo arranca el servidor local, abre el navegador, evita duplicar instancias y avisa si el puerto 8765 está ocupado (usa el siguiente libre). Para salir, cierra la ventana negra. (Probado la lógica en Linux; el .lnk de Windows está sin verificar en un PC real.)

## Productos nuevos
En la pestaña, «+ Nuevo producto»: rellena ficha (solo datos reales; lo que falte queda NO DISPONIBLE). No requiere código.
