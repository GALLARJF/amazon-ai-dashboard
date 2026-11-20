# Corrección 2.1 · Fase 2 (sobre 4ee069e)

Sin push, deploy ni cambios de backend/API/cálculo/datos/seguridad. Gasto extra: 0 €.

| # | Corrección | Cambio | Prueba |
|---|---|---|---|
| 1 | Prioridades | Título dinámico (`Una/Dos/Tres prioridades`); nunca se inventa una tercera | `ui_fase21_test` (título = nº de prioridades) |
| 2 | Franja amarilla vacía | Regla `:empty{display:none}` + `modebar` con texto corto; barrido de paneles/banners vacíos en 7 pantallas | `ui_fase21_test` a 360/390/1440/1280 |
| 3 | Scroll horizontal escritorio | `overflow-x:clip`, reinicio de scrollX al entrar en cada pantalla; barras clásicas | scrollX=0, scrollWidth ≤ innerWidth, sin elementos cortados (AHT, Hoy) |
| 4 | Cabecera móvil | Cabecera compacta (≤175 px hasta la franja de datos); «Salir» y selector de cuenta en el menú de cuenta; STAGING, cuenta, REAL/DEMO y decisiones visibles; objetivos ≥ 44 px | Situación + inicio de la siguiente tarjeta sin scroll en 390×844 y 360×740 |
| 5 | DECISIONES móvil | 5 campos visibles; Responsable, Evidencia y Estado en «Ver detalle» (los 8 campos siguen); escritorio muestra los 8 abiertos | tarjeta ≤ 520/560 px |

Nota honesta: el desplazamiento horizontal de escritorio y la franja vacía **no se pudieron reproducir** en el entorno de pruebas (scrollX=0 incluso con barras clásicas). Se añadieron salvaguardas y pruebas automáticas que los detectarían.

Resultados: ui_fase21 58/58 · ui_hoy 121/121 · ui_hoy_modo 23/23 · ui_viewer_ro 3/3 · viewer 32/32 · ui_viewer 24/24 · ui_nav 118/118 · ui_nav_modo 17/17 · v070_registro 100/100.
Capturas: `docs/p0_hoy/fase2_1/despues/` · comparativas: `docs/p0_hoy/fase2_1/comparativas/`.
