# Corrección 3.1 · Fase 3 (sobre 0cdc2e8)

Sin push, deploy, gasto ni cambios de backend/API/cálculos/datos/seguridad.

## 1 · Aislamiento estricto por producto
- Causa: el legado (11 secciones + panel V0.7) se pinta aparte y de forma asíncrona. El panel V0.7 no sabía a qué producto pertenecía (una respuesta tardía de ACTIVCORE podía pintarse en PHIVITAL), su texto «SIN DATOS» nombraba a ACTIVCORE y el selector legacy listaba los demás productos. El backend sí filtra por producto (`keepa_real.PRODUCT_EVIDENCE`, `scoped_records`).
- Corrección (solo interfaz): el panel V0.7 queda sellado con `data-product` y descarta respuestas de otro producto; el texto sin datos es neutro; se retira el selector legacy; una **cuarentena** elimina del expediente cualquier bloque legacy que contenga nombres o identificadores de otro producto y lo sustituye por un aviso con enlace «Fuente general (no es de este producto)»; si el expediente original no corresponde al producto abierto se oculta. Metodología muestra el ámbito («solo datos de X») y separa los datos generales de la cuenta con un enlace rotulado.
## 2 · Prueba de contaminación cruzada (`ui_lanz_aislamiento_test`, 104/104)
Centinelas únicos por producto (stock, coste, PVP, documento, competidor, ASIN, marca): ACTIVCORE 71011/7,71/71,71/SENT-ACT-DOC-ALFA/B0SENTAC01; Magnesio 72022/…; Omega-3 73033/… (sin competidor: su benchmark debe seguir SIN DATOS). Se recorren los 4 niveles de cada expediente con todo abierto (pasos, legado, V0.7) a 1440, 390 y 360 px: los centinelas propios aparecen y ninguno ajeno aparece; tampoco nombres de otros productos; cambios rápidos A→B→A no dejan restos.
Antes (0cdc2e8) la misma prueba falla: el expediente de ACTIVCORE contiene nombres de Magnesio y Omega-3 y el selector legacy (el cruce de competidores por respuesta tardía no pude reproducirlo en este entorno, queda cerrado estructuralmente).
## 3 · Acordeones móviles
Evidencia y Metodología inician cerradas y son excluyentes en ≤760 px; las secciones originales van plegadas (una por acordeón). Páginas: Evidencia con los 10 pasos abiertos ≈ 7,5–8,2 mil px; Metodología con las secciones originales ≈ ≤ 10 mil px (medido en el test). Indicador «Producto activo» persistente (sticky, ≥44 px).
## 4 · Coherencia de estado
El benchmark de otro producto no cuenta: el progreso de Omega-3 no cambia al añadir competidores a los otros dos, mientras el de ACTIVCORE y Magnesio sube solo con el suyo. GO exige además comparabilidad CONFIRMADA de todos los competidores (sin competidores o AUTOMÁTICA/SUGERIDA → REVISAR). SIN DATOS nunca pasa a 0.
## Resultados
ui_lanz_aislamiento 104/104 · ui_lanz 110/110 · ui_lanz_modo 9/9 · ui_fase21 58/58 · ui_hoy 121/121 · ui_hoy_modo 23/23 · ui_viewer_ro 3/3 · viewer 32/32 · ui_viewer 24/24 · ui_nav 118/118 · ui_nav_modo 17/17 · ui_v07 31/31 · v070_registro 102/102 · `run_all.sh` (77 suites): solo fallan las 2 heredadas idénticas en 167584b (seguridad 49/53 y v040_api 43/45).
Capturas: `docs/p0_hoy/fase3_1/despues/` (ACTIVCORE, Magnesio y Omega-3 a 1440/390/360, estado inicial y expediente abierto) y comparativa en `comparativas/`.
