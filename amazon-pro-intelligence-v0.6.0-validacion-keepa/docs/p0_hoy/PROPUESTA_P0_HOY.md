# Propuesta visual P0 — «HOY»: que un CEO entienda Amazon Pro Intelligence en < 30 s

Base: rama `aht-staging-viewer` @ e914144 → rama nueva `aht-p0-hoy` (local; sin push, sin despliegue, sin gasto, producción intacta).
Estado: **solo propuesta (wireframes). No se ha implementado nada de la nueva interfaz. Espera aprobación.**

> Nota: el informe `AUDITORIA_EJECUTIVA_AMAZON_PRO_INTELLIGENCE_STAGING_E914144.md` **no existe** en el repositorio ni en el entorno. La propuesta parte del recorrido real de las 13 pantallas con el viewer (capturas «ANTES») y de tus 10 requisitos. Si tienes el informe, pásalo y lo contrasto.

## 0. Defecto encontrado durante el análisis (ya corregido, commit 30ee37f)
En e914144, `lockUi()` desactivaba TODOS los botones sin atributo `type` (el DOM les da `type=submit` por defecto), incluidos los de **navegación interna** (p. ej. las 4 sub-vistas de K4). El backend nunca estuvo en riesgo (403), pero el viewer no podía consultar Benchmarking, Pricing ni Director·Datos. Corregido y con prueba nueva (`ui_viewer_test` 24/24). Ojo: la ZIP anterior (E914144) contiene este defecto.

## 1. Diagnóstico «ANTES» (datos medidos en el staging local)
| Pantalla | Alto de página desktop / Android | Problema para un CEO |
|---|---|---|
| Inicio | 1.130 / 2.750 px | 11 tarjetas, casi todas «SIN DATOS»; cuatro métricas de «estado del catálogo» que no son negocio |
| K4 Ejecutivo | 1.167 / 2.671 | 4 vistas; ocupa la 2.ª navegación; duplica Inicio |
| Director IA | 1.992 / 4.328 | Mezcla conclusión, hechos, métodos y modelos en una columna |
| Lanzamientos | 5.394 / 9.923 | 11 pasos + briefing + expediente en una página |
| Navegación | 13 pestañas en 3 niveles (5 + 8 «Avanzado») | En Android la cabecera ocupa más de media pantalla |
| Bandejas de decisión | 5 sitios (Inicio, Director IA, K4 «pendientes», K4 «seguimiento», Aprobaciones, + aprobaciones del servidor en Historial) | No se sabe dónde aprobar |

Capturas: `docs/p0_hoy/antes/` (desktop 1440×900 y Android 412×915; pantalla 1 y completa).

## 2. Navegación propuesta
**Principal (6):** Hoy · Ventas · Productos · Lanzamientos · Director IA · Administración.
**Siempre visibles en la cabecera:** chip **Decisiones · n** (abre DECISIONES), selector **Datos: REAL | DEMO** (sustituye a «Panel DEMO»), etiqueta STAGING y usuario.
**Android:** barra inferior con 5 (Hoy, Ventas, Productos, Lanzam., Director IA) + «Más» (Decisiones, Administración, cuenta, datos). Cabecera de 1 fila.
DECISIONES no es una 7.ª pestaña: es una pantalla a la que se llega desde el chip y desde HOY.

| Sección | Sub-pestañas internas |
|---|---|
| Hoy | — (una pantalla) |
| Ventas | Resumen · Indicadores · Rentabilidad por país · Publicidad · Inventario · Importar |
| Productos | Catálogo · Precio (Pricing Intelligence) · Competencia (Benchmarking) · Costes · Documentos/Imágenes · Expediente (incl. PhiVital) |
| Lanzamientos | Resumen · Expediente · Europa · Mercados · Pre-Launch · Tareas |
| Director IA | 4 niveles: Conclusión · Decisión · Evidencia · Metodología |
| Administración | Auditoría · Conexiones · Bloqueos · Integración · Seguridad |

## 3. Wireframes (`docs/p0_hoy/wireframes/*.png|html`, desktop y Android)
- **HOY**: banda de situación (semáforo + 1 frase) → 3 bloques (Ventas netas · Margen · Stock y riesgos) → Decisiones (máx. 3) | Prioridades del Director (máx. 3). Se alimenta SOLO de endpoints existentes (anotados en cada bloque).
- **DECISIONES**: una lista con 4 filtros (Pendientes de ti · En seguimiento · Resueltas · Todas las bandejas); cada fila: origen, qué se pide, por qué, impacto, coste, quién decide, evidencia. Botones Aprobar/Rechazar: el viewer los ve bloqueados (🔒) y el servidor responde 403.
- **LANZAMIENTOS**: selector de producto + sub-pestañas; los 11 pasos agrupados en 4 etapas con estado; «siguiente paso que más desbloquea».
- **DIRECTOR IA**: acordeón de 4 niveles; PARAR automatizaciones y chat en rail fijo.
- Comparativas lado a lado: `docs/p0_hoy/comparativas/ANTES_DESPUES_*_{desktop,android}.png`.
Honestidad: los wireframes muestran el estado REAL actual (casi todo «SIN DATO»); «SIN DATO» nunca se sustituye por 0. La pantalla DECISIONES usa un ejemplo ILUSTRATIVO (hoy hay 0 decisiones) y así lo dice.

## 4. Matriz exacta: componente actual → nueva ubicación
Estado: **M** = se mueve · **R** = se resume en HOY y el detalle se mueve · **P** = se pliega (nivel Metodología/Detalle) · **U** = se unifica con otro.
| # | Pantalla actual · componente | Nueva ubicación | Estado |
|---|---|---|---|
| 1 | Inicio · Fichas completas / Competidores identificados / Productos con regulatorio | Productos › Catálogo (cabecera de completitud) | M |
| 2 | Inicio · Decisiones por aprobar (KPI) | Chip «Decisiones · n» + HOY | U |
| 3 | Inicio · Ventas y rentabilidad | HOY › Ventas netas / Margen; detalle Ventas › Resumen | R |
| 4 | Inicio · Competencia y precios | Productos › Competencia | M |
| 5 | Inicio · Publicidad y retorno | Ventas › Publicidad | M |
| 6 | Inicio · Posicionamiento | Productos › Competencia | M |
| 7 | Inicio · Trabajo automático en curso | Director IA › Metodología (cola) | P |
| 8 | Inicio · Productos en riesgo | HOY › Stock y riesgos; detalle Productos › Catálogo | R |
| 9 | Inicio · Director Amazon IA (Preparar lanzamiento / Ejecutar tareas) | Lanzamientos › Resumen / Director IA › Decisión | M |
| 10 | Inicio · Bandeja de decisiones | DECISIONES | U |
| 11 | K4 · filtros globales (producto, país, periodo, canal) | Barra de filtros contextual en Ventas y Productos | M |
| 12 | K4 · Indicadores comerciales (8 KPIs) | HOY (3) / Ventas › Indicadores (8) | R |
| 13 | K4 · Decisión de precio (resumen) | HOY › banda de situación | R |
| 14 | K4 · Dictamen completo, Riesgos, Escenarios, Trazabilidad, Datos faltantes | Productos › Precio | M |
| 15 | K4 · Qué falta | HOY (situación) + Director IA › Decisión | R |
| 16 | K4 · Decisiones pendientes de una persona | DECISIONES › Pendientes | U |
| 17 | K4 · Qué hace hoy el Director (capacidades) | Director IA › Metodología | P |
| 18 | K4 · Benchmarking visual (Recomendación del Director) | Productos › Competencia | M |
| 19 | K4 · Pricing Intelligence › Ficha de costes | Productos › Costes | M |
| 20 | K4 · Pricing Intelligence › Importar datos comerciales | Ventas › Importar | M |
| 21 | K4 · Director·Datos › Dossiers del Director | Director IA › Evidencia | M |
| 22 | K4 · Seguimiento de decisiones | DECISIONES › En seguimiento | U |
| 23 | K4 · Registro de imágenes y derechos | Productos › Documentos/Imágenes | M |
| 24 | K4 · Nuevo producto (dossier) | Productos › + Nuevo | M |
| 25 | Mis ventas · Importar informes / Resumen real / Rentabilidad por país / Inventario | Ventas (mismas tarjetas, mismas sub-pestañas) | M |
| 26 | Mis ventas · Conexiones | Administración › Conexiones (enlace desde Ventas) | U |
| 27 | Productos · Cosmética / Suplementos (normalización) | Productos › Catálogo | M |
| 28 | Lanzamientos · pasos 1–11 | Lanzamientos › Expediente (4 etapas) | M |
| 29 | Lanzamientos · Siguientes pasos | Lanzamientos › Resumen («siguiente paso») | M |
| 30 | Lanzamientos · Tareas del producto | Lanzamientos › Tareas | M |
| 31 | Lanzamientos · Expediente comercial v0.7, Competidores reales (Keepa) | Lanzamientos › Expediente | M |
| 32 | Lanzamientos · Briefing del Director / Procedencia del dato | Director IA (Conclusión/Decisión/Evidencia); enlace desde Lanzamientos | U |
| 33 | Lanzamientos · Director card + Bandeja | DECISIONES / Director IA | U |
| 34 | Director IA · Briefing: veredicto | Director IA › Conclusión | M |
| 35 | Director IA · Briefing: prioridades, preguntas, desbloqueos | Director IA › Decisión | M |
| 36 | Director IA · Briefing: hechos citados, procedencia | Director IA › Evidencia | M |
| 37 | Director IA · Autonomía N1–N4, políticas N2 | Director IA › Metodología | P |
| 38 | Director IA · Modelos de IA, Últimas llamadas | Director IA › Metodología | P |
| 39 | Director IA · Cola de tareas | Director IA › Decisión (top) y Metodología (completa) | R |
| 40 | Director IA · Libro de decisiones | DECISIONES › Resueltas | U |
| 41 | Director IA · Eventos recientes | Director IA › Metodología | P |
| 42 | Director IA · PARAR automatizaciones / Conversar | Rail fijo de Director IA | M |
| 43 | Panel DEMO · filtros, KPIs, gráficos (Ventas, Competencia, Publicidad, Posicionamiento) | **Modo de datos DEMO**: las mismas vistas de HOY/Ventas/Productos con el dataset DEMO | U |
| 44 | Panel DEMO · Coworkers (7) | Director IA › Metodología | P |
| 45 | Panel DEMO · Alertas | HOY › riesgos (modo DEMO) | U |
| 46 | Panel DEMO · Noticias verificadas | Lanzamientos › Europa | M |
| 47 | Piloto PHIVITAL Magnesio | Productos › Expediente (PhiVital Magnesio) y selector de Lanzamientos | M |
| 48 | Pre-Launch · expediente, Claims, Decisión, Economía, Precio vs banda, Bloqueos | Lanzamientos › Pre-Launch | M |
| 49 | Europa · Mercados (ranking, benchmarking, cumplimiento, noticias, ficha, descubrimiento, consentimiento IA…) | Lanzamientos › Europa · Mercados | M |
| 50 | Historial · Historial de consultas, Ejecuciones de IA, Registro de auditoría | Administración › Auditoría | M |
| 51 | Historial · Aprobaciones (servidor) | DECISIONES › Resueltas (+ enlace a Auditoría) | U |
| 52 | Estado · Matriz de conexiones | Administración › Conexiones | M |
| 53 | Estado · Bloqueos antes de operar (13) | Administración › Bloqueos | M |
| 54 | Estado · Integración Executive Neon, Coworkers, Controles de seguridad | Administración › Integración / Seguridad | M |
| 55 | Aprobaciones · Cola local de propuestas | DECISIONES | U |
| 56 | Cabecera · selector de cuenta, sesión, DEMO badge | Cabecera (cuenta, usuario) + selector Datos REAL/DEMO | M |

Ningún cálculo, validación, control regulatorio, auditoría ni medida de seguridad se elimina: solo cambian de sitio o de nivel de detalle (requisito 7). 56/56 componentes con destino.

## 5. Archivos que se modificarían
- **Shell y navegación:** `index.html`, `styles.css`, `js/app.js` (router de pestañas), `js/v03.js` (cabecera, sesión, rol viewer/lockUi, aprobaciones).
- **Pantallas existentes (re-montaje, sin cambiar cálculos):** `js/v06.js` (inicio/ventas/prod/lanz/dir), `js/k4.js`, `js/eu.js`, `js/prelaunch.js`, `js/estado.js`, `js/v07.js`.
- **Nuevos:** `js/hoy.js`, `js/decisiones.js`, `js/director_niveles.js`, `js/admin.js`, `js/nav.js`.
- **Pruebas a adaptar** (referencian pestañas/ids): `ui_test.py`, `ui_v06_test.py`, `ui_v07_test.py`, `ui_k4_test.py`, `ui_k3_test.py`, `ui_eu_test.py`, `ui_v100_test.py`, `ui_v100_cloud_test.py`, `ui_synth_test.py`, `ui_viewer_test.py`; nuevas `ui_hoy_test.py`, `ui_android_test.py`.
- **No se tocan:** `server.py`, `backend/*`, contratos API, esquema de datos, `render*.yaml`, el rol viewer ni sus bloqueos.

## 6. Riesgos técnicos y mitigación
1. **Regresión de 10 suites de UI** que apuntan a `data-tab`/`#tab-*`. → Estrategia «estrangulador»: los `<main id="tab-*">` y sus renderizadores se conservan; la nueva navegación los monta como sub-pestañas. Modo `?legacy=1` mantiene la navegación antigua hasta migrar los tests.
2. **Modo DEMO vs REAL:** el Panel DEMO usa un dataset del cliente (`data.js`), la UI real usa la API. Riesgo de mezclar. → Selector global con etiqueta permanente, sin mezcla, DEMO nunca se guarda; en staging solo hay sintético.
3. **HOY compone varias llamadas** (`home`, `kpis`, `dictamen`, `briefing`, `decisions`). Latencia/errores parciales. → Carga en paralelo con tarjeta por bloque y «SIN DATO»/error explícito; nunca 0 inventado; sin endpoints nuevos.
4. **Unificar bandejas** sin perder la regla N3 (aprobador distinto del proponente, auditoría). → DECISIONES solo es vista; las acciones llaman a los mismos endpoints; pruebas de roles.
5. **Viewer:** nuevas pantallas = nuevos botones. → `lockUi` por lista de verbos + atributo explícito `data-write` en los nuevos botones; prueba que recorre todas las pantallas y verifica 0 POST y 403.
6. **Android:** tablas anchas (benchmark, ranking) y gráficos. → tablas con scroll horizontal y modo tarjeta; barra inferior; pruebas a 412×915.
7. **Accesibilidad/CSP:** sin `eval` ni inline; nuevos JS con `script-src 'self'` (la ruta estática admite `js/[a-z0-9_-]+.js`).
8. **Pérdida de detalle percibida** al plegar a Metodología. → todo sigue a un clic; matriz 56/56 verificada por prueba que busca cada componente por título.
9. **Presupuesto:** el rediseño es grande (~3–4 iteraciones). Se propone entregar por fases (abajo).

## 7. Plan de pruebas
- **Regresión completa** (CI + `run_all.sh`): sin fallos nuevos respecto a las 6 suites heredadas ya conocidas.
- **`viewer_test` 32/32** y `ui_viewer_test` ampliado: 6 secciones + sub-pestañas navegables, 0 POST, 403 en escrituras, sin «restringido».
- **`ui_hoy_test`:** HOY muestra solo los 5 bloques, ≤3 decisiones, ≤3 prioridades, semáforo coherente con el dictamen, «SIN DATO» ≠ 0; carga < X s en local.
- **`ui_decisiones_test`:** las 5 fuentes aparecen unificadas; filtros; contador del chip = nº de pendientes.
- **`ui_director_test`:** 4 niveles presentes; todos los hechos citados siguen con etiqueta de procedencia.
- **Matriz 56/56:** test que localiza cada componente por su título en su nueva ubicación.
- **Android (412×915) y desktop (1440×900):** sin desbordamiento horizontal, objetivos táctiles ≥44 px, primera pantalla de HOY legible sin scroll, capturas automáticas ANTES/DESPUÉS reales.
- **Seguridad:** CSP sin inline, contratos API inalterados (hash de respuestas de todos los GET antes/después), cero llamadas externas, DB sin cambios.
- **Prueba «30 segundos»:** guion de 5 preguntas (¿cómo estoy?, ¿cuánto vendo/gano?, ¿qué riesgo hay?, ¿qué decido?, ¿qué hace el Director?) respondidas solo con la primera pantalla.

## 8. Fases propuestas tras tu aprobación
F1 shell + navegación + modo de datos + viewer (legacy activo) · F2 HOY + DECISIONES · F3 Lanzamientos (Europa, Pre-Launch, PhiVital) · F4 Director IA 4 niveles + Administración · F5 retirar legado, adaptar tests, capturas reales. Cada fase: commit local, pruebas y capturas; sin push ni despliegue.
