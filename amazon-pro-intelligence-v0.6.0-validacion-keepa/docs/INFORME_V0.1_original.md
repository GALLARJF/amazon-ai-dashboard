# Informe — Amazon Pro Intelligence V0.1
Fecha: 2026-11-16 · Copia aislada: no toca la plataforma principal.

## 1. Funcionalidades implementadas (todas verificadas en navegador)
- Estructura horizontal NEON, fondo negro, tarjetas de color, tipografía legible; responsive hasta móvil. Cabe en 1600×840 sin scroll.
- Filtros funcionales: producto (4), periodo (7/30/90 d), marketplace (ES/DE/FR/IT). Recalculan KPIs y gráficos; variación vs periodo anterior.
- KPIs: ventas netas, margen (€ y %), TACoS, ACoS, stock.
- Gráficos SVG con tooltip: ventas y margen, competencia y precios, publicidad (gasto vs ventas ads), posicionamiento (BSR), tabla de keywords.
- Director Amazon IA: chat interactivo, motor LOCAL de reglas sobre los datos filtrados. No hay LLM conectado. Propone acciones → cola de aprobación.
- 7 coworkers (Mercado, Precios, SEO, PPC, Creatividad, Inventario, Reputación): análisis por reglas; Creatividad audita título/bullets pegados.
- Pre-Launch: PVP, costes, logística, comisión, IVA, devoluciones, ACoS objetivo → margen neto, ACoS de equilibrio, precio mínimo para el margen objetivo, benchmarking (mín/P25/mediana/P75/máx), payback, decisión GO / NO-GO / SIN DECISIÓN (<3 competidores). Los precios los introduce el usuario.
- Cola de aprobaciones: precios, campañas y publicaciones solo se registran; "Aprobada" NO ejecuta nada (no existe conector de escritura).
- Importación CSV (validada) para usar datos reales; plantilla descargable. Al importar desaparece la etiqueta DEMO.
- Interfaz de integración futura: `AmazonPro.exportSummary()` (Ventas → Canal Amazon). No enlazada hoy.

## 2. Estado de conexiones (honesto)
| Conector | Estado | Detalle |
|---|---|---|
| Amazon SP-API | NO CONFIGURADO | Código de prueba de solo lectura (token LWA + marketplaceParticipations). Sin credenciales no probado. |
| Amazon Ads | NO CONFIGURADO | Prueba de solo lectura (LWA + /v2/profiles). Sin probar. |
| Keepa | NO CONFIGURADO | Prueba GET /token. Sin probar. |
| Helium 10 | SIN API VERIFICADA | Vía importación CSV. |
Un conector solo muestra CONECTADO tras una prueba real exitosa. Ninguno lo está.

## 3. Estado de coworkers
Los 7: **PREPARADO** (lógica implementada y probada con datos sintéticos/DEMO). **Ninguno declarado operativo**: faltan datos reales. Reputación, SEO y Creatividad dependen de SP-API / Brand Analytics / Helium 10. Inventario usa un plazo de reposición supuesto de 30 días (editable en js/coworkers.js).

## 4. Pruebas realizadas
- Lógica (Node): 10 grupos OK — filtros, agregados, periodo anterior, economía unitaria, precio mínimo, GO/NO-GO/SIN DECISIÓN, estadística, CSV válido/inválido.
- UI (Playwright, Chromium): 33/33 OK — sin errores JS, filtros, tooltips, Director, 7 coworkers, cola de aprobación, Pre-Launch, estado de conectores, CSV válido (ventas netas 330 €) e inválido, exportSummary, móvil sin desbordamiento.
- Servidor: /api/connectors devuelve NO CONFIGURADO sin credenciales.
- NO probado: conexiones reales a Amazon/Keepa (sin credenciales), navegadores distintos de Chromium, Windows/Edge.

## 5. Limitaciones
- No pude acceder a la versión previa de AHT Executive Neon (ninguna carpeta conectada): se usó la imagen de referencia. Convendrá alinear estilos con el código real.
- Todas las cifras mostradas son DEMO (semilla fija), no ventas reales.
- Comisión 15 % y devoluciones son parámetros editables, no tarifas verificadas.

## 6. Pendientes y próximos pasos
1. Credenciales SP-API / Ads / Keepa como variables de entorno → ejecutar "Probar conexión".
2. Sincronización real de ventas, costes y campañas (solo lectura) reemplazando el DEMO.
3. Conector de escritura (precios/campañas) solo tras aprobación explícita y con auditoría.
4. LLM real para el Director (hoy reglas).
5. Reputación (reseñas) e imágenes/A+ en Creatividad con datos reales.
6. Alinear con AHT Executive Neon real e integrar en Ventas → Canal Amazon.
