# Corrección final de staging — sin funcionalidades nuevas

Base: rama `aht-finalizacion-fase4` (a809569). Sin Amazon, sin Keepa, sin IA, sin tocar producción, sin push ni deploy.
Defectos observados en la auditoría autenticada de `amazon-pro-intelligence-staging-7cna.onrender.com`.

## P0
| # | Requisito | Resultado |
|---|---|---|
| 1 | El auditor entra como `auditor · viewer`, nunca como admin | Login real: respuesta del servidor `role=viewer` y etiqueta de sesión «auditor · viewer» en 1440, 390, 360 y Pixel 7. Además, en staging un usuario de auditoría **preexistente** con otro rol se fuerza a `viewer` al arrancar (`seed_viewers`). *No he podido reproducir el defecto observado (en esta compilación el auditor ya entraba como viewer); la causa en el despliegue (p. ej. un usuario `auditor` creado antes con otro rol, o haber entrado con otra cuenta) queda cubierta por esa norma.* |
| 2 | «PRODUCCIÓN» → «STAGING · DATOS SINTÉTICOS · NO USAR PARA DECISIONES REALES» | Banner permanente servido en el HTML con ese texto. Las etiquetas «PRODUCCIÓN» (Indicadores, Precio…) muestran el texto de staging. Prueba: 0 apariciones en 15 pantallas × 3 viewports × 2 usuarios, y en las 13 pestañas del modo `?legacy=1`. |
| 3 | Servidor: POST/PUT/PATCH/DELETE → 403 para todos los roles salvo login y logout | Bloqueo central previo a cualquier ruta (`_staging_denied`), auditado. Probado con **admin, approver y viewer** y CSRF válido: 14 escrituras (incl. rutas inexistentes) → 403; GET, login y logout siguen funcionando. |
| 4 | Controles de escritura desactivados visualmente | `ro.js` y `v03.js` aplican el bloqueo a **todos los roles** en staging (también «Crear dossier, Validar, Importar, Generar, Crear expediente, Analizar Europa, Probar conexión, Importar competidores, Vaciar, ejemplos DEMO, + competidor/categoría/producto, chat, coworker, aprobaciones»). Prueba: 0 controles de escritura activos en las 15 pantallas y en las 13 pestañas antiguas, con admin y con auditor. Excepción declarada: los campos del formulario de Pre-Launch son una calculadora local (no escriben en el servidor). |
| 5 | Frases contradictorias | Eliminado «datos reales parciales» (Europa), «datos reales» en estado, avisos, consentimiento IA, Panel, plan de lanzamiento, aria-labels y selector («DATOS DE AHT (no disponibles en staging)»). El stock histórico mantiene su rótulo «(histórico)» con la advertencia «no es stock disponible hoy». Cero «datos reales» en staging (prueba sobre texto, atributos y opciones). |

## P1
6. **Panel DEMO → Administración › Laboratorio DEMO** (ya no está en Ventas).
7. Marca **«DATOS FICTICIOS — NO REPRESENTAN RESULTADOS DE AHT»** en la barra de modo de todas las pantallas (también en móvil) y en el propio Laboratorio DEMO.
8. **Pre-Launch** agrupa bloqueos y avisos por Economía, Mercado, Regulatorio, Contenido y Logística (con la severidad en cada hallazgo).
9. **Europa**: primero Conclusión, País, Confianza, Motivo y Datos faltantes; después KPI y filtros.
10. **Competencia**: tarjetas (una por referencia, sin tablas) y la tabla completa solo dentro de «Evidencia» (plegada).

Defectos adicionales detectados por las nuevas pruebas y corregidos: desbordamiento horizontal a 390/360 px en Precio (tablas sin contenedor desplazable y selector largo) y banner de staging más compacto en móvil.

## Pruebas
- Nueva: `tests/ui_staging_final_test.py` (79 comprobaciones): login real, 403 universal, textos, controles, P1, cero llamadas externas (sockets del proceso + navegador), capturas de las 15 pantallas en **1440, 390 y 360 px** (auditor) y en **Chrome Android emulado (Pixel 7, UA Android/Chrome)**: `docs/p0_hoy/final_staging/` (60 capturas).
- Pruebas heredadas adaptadas al nuevo comportamiento (siembra de datos con el bloqueo levantado solo en la prueba; Panel DEMO → Laboratorio DEMO; Competencia en tarjetas).
- Regresión completa (`tests/run_all.sh`), antes (a809569) y después:

| Suite | Antes | Después |
|---|---|---|
| seguridad heredada V0.2 | 49/53 (4 comprobaciones de Keepa, ya fallaban en la base 925dcb7) | 49/53 (igual) |
| V0.4.0 API europea | 43/45 (heredado) | 43/45 (igual) |
| V1.0 Chromium modo cloud | intermitente: 35/37 y 37/37 en ejecuciones distintas | intermitente: 36/37 y 37/37 (la comprobación «20 competidores» depende de la carga asíncrona; no toca staging) |
| presupuesto / V1.0 UI | 28/29 y 43/44 en una ejecución intermedia | 29/29 y 44/44 (intermitentes, pasan al repetir) |
| resto (≈ 70 suites, incl. las 3 nuevas) | OK | OK |

Fallos **nuevos provocados por esta corrección y ya resueltos**: 6 pruebas que sembraban datos con el admin en staging (ahora el servidor lo prohíbe: la siembra levanta el bloqueo solo dentro de la prueba), Panel DEMO → Laboratorio DEMO, Competencia en tarjetas (la tabla ahora está en «Evidencia»), banner/barra de modo en móvil (el indicador sticky de Lanzamientos), y el control negativo del viewer (ahora el admin también queda bloqueado en staging).

## No incluido / límites
- Chrome Android **emulado** (no dispositivo físico).
- No se ha tocado el despliegue de Render ni producción; el servicio actual seguirá con el código anterior hasta que usted apruebe push y redeploy manual.
