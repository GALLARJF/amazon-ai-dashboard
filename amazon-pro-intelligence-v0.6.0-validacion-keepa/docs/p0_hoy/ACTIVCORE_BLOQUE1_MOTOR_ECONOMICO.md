# ACTIVCORE Pro Intelligence — Bloque 1: motor económico por SKU/lote/canal

Respuesta al encargo de José (25/11/2026, comentario en `amazon-ai-dashboard` PR #5): "adaptar Amazon Pro Intelligence a la
auditoría comercial ACTIVCORE". Este PR cubre **solo el Bloque 1** (motor económico). Los Bloques 2–6 (simulador, Ads,
presupuesto incremental, checklist Seller, integración de UI/RBAC) **no están implementados todavía** — ver "Qué falta" al
final.

Sin despliegue, sin producción, sin conectores reales, sin secretos, sin gasto, sin merge. Solo código nuevo (`backend/activcore_pricing_engine.py`),
pruebas unitarias (`tests/activcore_pricing_engine_test.py`) y este informe. No se tocó `server.py`, el resto de `backend/` ni `js/`.

## Qué hace

Dado un SKU (`ACTIVCORE_V2`), un lote (`lote1` / `lote2`) y un canal (`FBA` / `FBM`), calcula:

- **Margen bruto** = precio neto de IVA − coste del lote.
- **Contribución antes de Ads** = margen bruto − coste de canal (comisión, FBA/FBM, entrada, prep, almacén, plan amortizado, promociones, incidencias).
- **IVA**, declarado aparte, informativo (nunca se resta como coste).
- **Operativo / Neto / Caja**: quedan como notas explícitas "PENDIENTE" — dependen de los Bloques 2 y 3 (costes fijos no amortizados, Ads, cobros/devoluciones reales), que aún no están construidos. No se inventa un número para rellenarlos.

Cada partida lleva **estado** (VERIFICADO · ESTIMADO · CONDICIONADO · PROVISIONAL · PENDIENTE), **fuente** y **fecha**,
siguiendo la misma convención que ya usa el repo en `eu.py`/`econ6.py`/`k4_costs.py`. Ningún dato de este bloque está
VERIFICADO salvo el tipo de IVA (21 %, tipo legal público) — todo lo demás son las cifras que José dio en el encargo,
calificadas tal cual él las calificó (condicionado/provisional/pendiente), no "promovidas" a verificado.

**Anti-doble-imputación** (como pide el punto 1 del encargo): el coste de `lote1` (12,55 €) está declarado como total que
**incluye regulación**, así que el motor nunca resta una partida de regulación aparte. Si en el futuro se añade un coste de
"muestras" o "costes fijos" propio, debe declararse con su propia marca de qué incluye, para que quien lo añada vea qué ya
está contado.

`lote2` (coste 8,99 €) está marcado explícitamente **pendiente de confirmar** por José: el motor sí calcula con ese valor
(no lo bloquea, porque hay un número, solo que sin confirmar — igual que el resto de costes de este bloque), pero el
resultado queda etiquetado "ESCENARIO HIPOTÉTICO/PENDIENTE DE CONFIRMAR" en vez de presentarse como un dato firme. Un coste
realmente ausente (`v=None`), en cambio, sí bloquea el cálculo — eso se prueba explícitamente en los tests.

## Conciliación con las cifras que dio José — RESUELTO

El encargo decía: *"Base FBA 15,40 y FBM 14,81 antes Ads"*. Al construir el motor línea a línea **no** coincidían con el
total de coste de canal solo (13,29 € FBA / 13,88 € FBM) — contrastar esto era parte explícita del encargo ("no declarar
tarifas verificadas sin evidencia oficial").

Resultado de la conciliación: **15,40 € y 14,81 € son la CONTRIBUCIÓN de `lote1`** (precio neto de IVA − coste del lote
12,55 € − coste de canal), no el coste de canal por sí solo. Con esa lectura, el motor reproduce las dos cifras de José
**exactamente**, céntimo a céntimo, con el redondeo por partida pedido. Esto queda fijado como prueba de regresión
(`activcore_pricing_engine_test.py`): si un cambio futuro del motor deja de reproducirlas, el test debe fallar, no pasar
desapercibido.

| | FBA | FBM |
|---|---:|---:|
| PVP bruto | 49,90 € | 49,90 € |
| Precio neto de IVA (21%) | 41,24 € | 41,24 € |
| − Coste lote1 (incluye regulación) | 12,55 € | 12,55 € |
| = Margen bruto | 28,69 € | 28,69 € |
| − Coste de canal (comisión 15% PVP bruto, tarifa, entrada/envío, prep, almacén, plan amortizado 300 uds/90d, promos, incidencias) | 13,29 € | 13,88 € |
| = **Contribución antes de Ads** | **15,40 €** ✓ | **14,81 €** ✓ |

## Qué falta (Bloques 2–6 del encargo, no implementados en este PR)

1. **Simulador** de precio/lotes/TACoS (0–25%)/FBA-FBM/farmacia-web/incentivos/packs/cupones/Vine/devoluciones/stock/tesorería.
2. **Ads**: ingestión solo lectura de informes (CPC, CVR, ACoS, TACoS con denominador explícito, atribución), propuestas de campaña automática→manual.
3. **Presupuesto incremental** no autorizado (150→1000 € en 90 días) con alertas de gasto/contribución negativa/stock/términos sin ventas.
4. **Checklist** Seller/Brand Registry/incentivos/regulación/listing/FBA/Vine, sincronizado con `activcore-launch-control`.
5. **Integración en la UI** existente (vista HOY/DECISIONES, RBAC viewer, datos reales vs. demo separados) y endpoint de solo lectura en `server.py` para exponer este motor — este PR deja el motor como módulo Python puro, sin wiring todavía, para no tocar `server.py`/producción sin que José vea primero el motor en sí.
6. **Auditoría visual** de este bloque (no aplica aún: no hay UI que auditar).

## Pruebas

`python3 tests/activcore_pricing_engine_test.py` → 19/19 OK. Sin red, sin gasto, sin tocar `server.py` ni el resto del backend.
`tests/security_test.py` se re-ejecutó sin regresión (mismo 49/53 preexistente, documentado en PR #5 — no relacionado con este cambio).
