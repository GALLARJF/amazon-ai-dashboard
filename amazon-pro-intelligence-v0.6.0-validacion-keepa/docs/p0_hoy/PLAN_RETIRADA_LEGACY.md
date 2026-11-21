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

---
## Estado tras la Fase 4 (evaluación de los criterios)
| # | Criterio | Estado | Evidencia |
|---|---|---|---|
| 1 | Las 10 suites heredadas usan la navegación nueva y pasan | **CUMPLIDO** | `?legacy=1` eliminado de las 10 suites; adaptador `tests/_nav_shim.py` (solo pruebas) |
| 2 | `ui_nav_test`, `ui_nav_modo_test`, `viewer_test`, `ui_viewer_test` pasan en dos ejecuciones consecutivas | **CUMPLIDO** (ver INFORME_FASE4) | dos ejecuciones registradas |
| 3 | Matriz de componentes verificada por prueba | **CUMPLIDO** | `tests/ui_legacy_paridad_test.py`: los 109 títulos de la navegación antigua existen en la nueva (0 perdidos) |
| 4 | Revisión de José de las Fases 2–4 sin incidencias bloqueantes | **PENDIENTE** | requiere la revisión humana de la Fase 4; no la puede dar el sistema |
| 5 | Ninguna rama de producción recibe `?legacy=1` activo tras la Fase 5 | **PENDIENTE** | es una regla de la Fase de retirada, aún no ejecutada |

**Decisión: `?legacy=1` NO se retira en esta fase.** Quedan pendientes exactamente: (a) el criterio 4 (revisión de José de la Fase 4) y (b) el criterio 5 (se verifica al retirar). Cuando José apruebe la Fase 4, la retirada es mecánica y está acotada: borrar la rama `legacy` de `js/nav.js`, la barra «NAVEGACIÓN ANTIGUA», los 13 botones de `#tabs` (sustituyendo el clic programático por llamadas de montaje) y las reglas CSS `body.shell6 #tabs`; después, quitar `tests/_nav_shim.py` y el caso `?legacy=1` de `ui_nav_modo_test`. Mientras tanto la navegación antigua sigue oculta por defecto y solo se abre con la URL explícita.
