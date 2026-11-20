# Fase 3 · Lanzamientos guiados (sobre 167584b)

Sin push, deploy, gasto ni cambios de backend/API/cálculos/datos/seguridad. No se ejecuta Keepa, IA de pago, publicación ni acción comercial. `?legacy=1` se mantiene.

## Qué cambia
- Nueva capa de presentación `js/lanz.js` (solo GET existentes: catalog, v06/launch, v06/decisions). Las 11 secciones originales y todos sus cálculos siguen intactas y accesibles en el nivel 4.
- **Primer nivel por lanzamiento (8 elementos):** Producto, Estado (GO/REVISAR/NO GO/SIN DATOS), Conclusión, Bloqueos críticos, Próxima acción, Responsable, Progreso (X de 10), Última actualización.
- **Cuatro niveles:** 1 Conclusión · 2 Decisión (qué bloquea, próxima acción, responsable, datos que faltan y quién los aporta, resumen del Director IA sin consumo de IA, enlaces a Decisiones/Director/Productos) · 3 Evidencia (plegada: expediente guiado en 10 pasos) · 4 Metodología (plegada: reglas del estado + secciones originales).
- **Expediente en 10 pasos:** Producto y mercado · Economía unitaria · Precio y margen · Benchmark y competidores · Demanda · Stock y logística · Cumplimiento regulatorio · Documentos y fuentes · Riesgos y bloqueos · Recomendación final. Cada paso: estado, rótulo REAL/DEMO/SIN DATOS, faltantes con rol responsable.
- **Regla del estado (determinista, probada):** GO solo con economía positiva en todos los países, cumplimiento sin requisitos abiertos y ranking; NO GO solo si la contribución es negativa en todos los países calculados; SIN DATOS si el servidor dice NO DECIDIBLE y no hay economía, benchmark ni cumplimiento; si no, REVISAR. El servidor actual nunca emite GO y la interfaz no lo inventa.
- Sin duplicación: aprobar/rechazar sigue únicamente en Decisiones; la ficha completa sigue en Productos (enlace); Director IA solo se enlaza.

## Casos
- ACTIVCORE V2: SIN DATOS · 72 requisitos sin evidencia · COGS histórico 10,03 € («a revalidar», no se trata como coste puesto en Amazon) · stock histórico 550 uds «NO es stock disponible hoy» · 0 de 5 países calculables.
- PHIVITAL Magnesio: SIN DATOS · 66 requisitos sin evidencia · PVP 17,99 € documentado · sin costes, stock ni documentos · 1 decisión pendiente enlazada.

## Matriz de aceptación
| Requisito | Resultado | Prueba |
|---|---|---|
| 8 elementos de primer nivel | OK | ui_lanz_test |
| 4 niveles; evidencia y metodología plegadas | OK | ui_lanz_test |
| Expediente de 10 pasos en el orden pedido | OK | ui_lanz_test |
| REAL/DEMO/SIN DATOS; ausencia ≠ 0 | OK | ui_lanz_test, ui_lanz_modo_test |
| Estado justificado con evidencia; GO nunca por defecto | OK | lógica GO/REVISAR/NO GO/SIN DATOS (7 casos) |
| Qué falta y quién lo aporta | OK | ui_lanz_test |
| ACTIVCORE y PHIVITAL comprensibles sin recorrer pantallas | OK | tarjetas + detalle en una pantalla |
| Cálculos y validaciones accesibles | OK | 11 secciones originales + exportación + Pre-Launch/Europa |
| Sin duplicar con Productos/Decisiones/Director | OK | enlaces, un solo detalle |
| Director explica bloqueo y siguiente acción | OK | resumen determinista |
| Móvil: 1 columna, sin tablas, ≥44 px, barra inferior | OK | 390 y 360 |
| Viewer: lectura completa, escrituras bloqueadas y rotuladas, 403 servidor | OK | ui_lanz_test (+ ui_viewer_ro, viewer_test) |
| Sin Keepa/IA/publicación; sin cambios de backend | OK | solo js/css/html/tests |

## Resultados
ui_lanz 110/110 · ui_lanz_modo 9/9 · ui_fase21 58/58 · ui_hoy 121/121 · ui_hoy_modo 23/23 · ui_viewer_ro 3/3 · viewer 32/32 · ui_viewer 24/24 · ui_nav 118/118 · ui_nav_modo 17/17 · v070_registro 102/102 · ui_v07 31/31 · ui_v100 44/44.
`run_all.sh` completo: solo fallan 2 suites heredadas, idénticas en 167584b: seguridad_test 49/53 y v040_api_test 43/45.

Cambio en un test heredado: el detector de contenido tapado por la barra inferior (`ui_nav_test`) ya no cuenta como visible el contenido que está dentro de acordeones cerrados anidados.

Altura de la pantalla (antes → después, plegado): escritorio 5.428 → 1.694 px (ACTIVCORE); Android 390 10.101 → 3.680 px; Android 360 8.866 → 3.906 px (PHIVITAL).

## Límites
Responsables = roles propuestos por regla (el sistema no asigna personas). La fecha «Última actualización» es la del producto en el catálogo. Demanda no tiene fuente en servidor: se muestra SIN DATOS. No hay lanzamientos con datos completos en staging: GO/NO GO se verifican con casos sintéticos de la lógica, no con un producto real.
