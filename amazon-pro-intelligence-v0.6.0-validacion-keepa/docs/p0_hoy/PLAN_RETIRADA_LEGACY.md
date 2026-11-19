# Retirada de `?legacy=1` (navegación antigua)

`?legacy=1` existe SOLO como transición: conserva las 13 pestañas antiguas (con el aviso «se retirará en la Fase 5») para que las 10 suites de interfaz heredadas sigan ejecutándose sin cambios mientras se migran.

**Fase de retirada: Fase 5** (después de HOY y DECISIONES — Fase 2 —, Lanzamientos — Fase 3 — y Director IA 4 niveles + Administración — Fase 4).

**Criterios (todos, medibles):**
1. Las 10 suites de interfaz (`ui_test`, `ui_v06`, `ui_v07`, `ui_k4`, `ui_k3`, `ui_eu`, `ui_synth`, `ui_v100`, `ui_v100_cloud`, `ui_viewer`) usan la navegación nueva (sin `?legacy=1`) y pasan.
2. `ui_nav_test`, `ui_nav_modo_test`, `viewer_test` y `ui_viewer_test` pasan en dos ejecuciones consecutivas.
3. Matriz de componentes 56/56 verificada por prueba (cada componente localizado en su nueva ubicación).
4. Revisión de José de las Fases 2–4 sin incidencias bloqueantes abiertas.
5. Ninguna rama de producción recibe una versión con `?legacy=1` activo después de la Fase 5.

**Qué se elimina en la Fase 5:** la rama `legacy` de `js/nav.js`, la barra «NAVEGACIÓN ANTIGUA», los 13 botones de `#tabs` en `index.html` (el clic programático pasa a llamar a las funciones de montaje de cada sección) y las reglas CSS `body.shell6 #tabs`.

**Si no se cumplen los criterios** la retirada se aplaza; mientras tanto la navegación antigua queda oculta por defecto (nunca visible para el auditor) y solo accesible con la URL explícita.
