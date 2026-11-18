# K3 · Motor inteligente de segmentación competitiva — informe técnico

Fecha de datos: 2026-11-18. Rama `aht-k3-segmentacion` (PR sin fusionar ni desplegar). Keepa de pago e IA externa desactivados; gasto adicional 0 €; nada publicado en Amazon.

## 1. Qué es K3
- **Etapa A · elegibilidad**: categoría real, necesidad, zona, leave-on/aclarado, cosmético vs medicamento/suplemento, formato → ELEGIBLE / EXCLUIDO / PENDIENTE.
- **Etapa B · equivalencia 0-100** (explicable, configurable): necesidad 25 % · tipo y aplicación 20 % · posicionamiento y público 20 % · activos 15 % · canal y categoría 10 % · formato/volumen/pauta 10 %. **El precio NO puntúa** (test de propiedad: mismo producto a 5 € y a 500 € → misma puntuación).
- **Cinco segmentos**: premium · funcional · económica/masiva · no comparable · pendiente de evidencia. Premium exige marca documentada como profesional/dermocosmética, sérum/loción leave-on, zona no contradictoria y la misma necesidad (caída/densidad); ni el precio ni la similitud de palabras bastan.
- **Sin datos esenciales (necesidad, tipo) o con cobertura de evidencia < 60 % → PENDIENTE DE EVIDENCIA**, no puntuación alta. Una marca sin clasificar nunca puede ser premium.
- **Revisable**: confirmar/rechazar/restablecer con justificación obligatoria, actor, fecha e historial (SQLite + auditoría); la clasificación automática se conserva.
- **Arquitectura por categoría**: criterios en `backend/k3_config/<categoria>.json` (léxicos multilingües, marcas, activos, pesos, umbrales, ficha de referencia). Hoy solo existe el perfil `capilar_cuero_cabelludo`; cosmética facial, magnesio y omega-3 requieren su propio JSON con criterios específicos (no se improvisan aquí).
- **Descubrimiento**: `plan_consultas` genera consultas multilingües (ES/DE/FR/IT) por necesidad, tipo, aplicación, posicionamiento, activos y productos similares, con expansión (candidatos → clasificar → descartar falsos positivos → semillas) y deduplicación por ASIN y marca+línea. **No se ejecuta**: requiere autorización explícita y estimación previa de tokens (flujo K1).

## 2. Clasificación explicada de los 20 ASIN + referencias de la infografía

| # | Segmento | Equiv. | Marca · producto | ASIN | Precio (fecha · clase) | €/100 mL | Motivo |
|--:|---|--:|---|---|---|--:|---|
| 1 | COMPETIDOR DIRECTO PREMIUM | 100 | KÉRASTASE · Kérastase Genesis Sérum Anti-chute Tratamiento Anticaída Pro | B083JKPCFB | 39,94 € (2026-11-16 · ACTUAL) | 44,38 € | equivalencia 100.0 ≥ 70 y cumple todas las condiciones premium (marca especializada/profesional, sérum, misma necesidad) |
| 2 | COMPETIDOR DIRECTO PREMIUM | 100 | Nioxin · Nioxin Night Density Rescue 70 ml | sin ASIN | sin precio vigente | — | equivalencia 100.0 ≥ 70 y cumple todas las condiciones premium (marca especializada/profesional, sérum, misma necesidad) |
| 3 | COMPETIDOR DIRECTO PREMIUM | 97 | Redken · Redken Aminexil Advanced 90 ml | sin ASIN | sin precio vigente | — | equivalencia 97.0 ≥ 70 y cumple todas las condiciones premium (marca especializada/profesional, sérum, misma necesidad) |
| 4 | COMPETIDOR DIRECTO PREMIUM | 78 | REDKEN · Redken Acidic Grow Sérum Pelo para Tratamiento Anticaída Pel | B0G59MCQT6 | 29,99 € (2026-05-22 · HISTÓRICO) | 29,99 € | equivalencia 77.5 ≥ 70 y cumple todas las condiciones premium (marca especializada/profesional, sérum, misma necesidad) |
| 5 | COMPETIDOR FUNCIONAL | 87 | The Ordinary · The Ordinary Multi-Peptide Serum for Hair Density 60 ml | sin ASIN | sin precio vigente | — | equivalencia 87.4: finalidad similar; no es premium porque la marca no está documentada como premium/profesional/dermocosmética |
| 6 | COMPETIDOR FUNCIONAL | 80 | Bio-Pilixin · Bio-Pilixin Bio-Pilixin Serum 100 ml | sin ASIN | sin precio vigente | — | equivalencia 80.2: finalidad similar; no es premium porque la marca no está documentada como premium/profesional/dermocosmética |
| 7 | COMPETIDOR FUNCIONAL | 70 | KÉRASTASE · Kérastase Nutritive Sérum Profesional Pelo Para Cuero Cabell | B0BZZK7GJB | 38,89 € (2026-11-03 · RECIENTE) | 43,21 € | equivalencia 70.0: finalidad similar; no es premium porque la necesidad principal no coincide (hidratacion cuero) |
| 8 | COMPETIDOR FUNCIONAL | 68 | ZREVSB · Sérum Anticaída para Cabello, Suero Nutritivo Cuero Cabellud | B0HH6H6FHC | 6,99 € (2026-10-31 · RECIENTE) | 11,65 € | equivalencia 68.2: finalidad similar (marca sin clasificar: nunca puede ser premium) |
| 9 | COMPETIDOR FUNCIONAL | 64 | AROMATICA · AROMATICA Potenciador de raíz de romero 3.38oz/100ml- Spray  | B01MU9AUX7 | 17,06 € (2026-09-03 · HISTÓRICO) | 17,06 € | equivalencia 64.4: finalidad similar |
| 10 | COMPETIDOR FUNCIONAL | 64 | VT COSMETICS · VT COSMETICS PDRN Reedle Shot Sérum Capilar con Cepillo, Cui | B0GGQMYLXM | 35,50 € (2026-11-16 · ACTUAL) | — | equivalencia 64.2: finalidad similar |
| 11 | COMPETIDOR FUNCIONAL | 59 | Transparent Lab · Transparent Lab Scalp Calming Treatment Sérum Cuero Cabellud | B0D5HTCRW6 | 13,27 € (2026-11-10 · RECIENTE) | 26,54 € | equivalencia 59.1: finalidad similar |
| 12 | COMPETIDOR FUNCIONAL | 58 | SERQIA · Serum de crecimiento del cabello con cepillo integrado, Epai | B0HG1D9G3D | 11,99 € (2026-10-28 · RECIENTE) | — | equivalencia 58.2: finalidad similar (marca sin clasificar: nunca puede ser premium) |
| 13 | COMPETIDOR FUNCIONAL | 55 | KTouler · PDRN Hair Scalp Serum Built-In Brush,Masajeador Revitalizant | B0HC63QWN9 | 19,99 € (2026-11-12 · ACTUAL) | — | equivalencia 55.2: finalidad similar (marca sin clasificar: nunca puede ser premium) |
| 14 | ALTERNATIVA ECONÓMICA/MERCADO MASIVO | 59 | L'Oreal Paris · L'Oréal Paris Elvive Growth Booster Serúm Tratamiento Antica | B0DWFSJ9Y4 | 6,26 € (2026-11-09 · RECIENTE) | 6,26 € | marca de mercado masivo documentada; equivalencia 59.3: presión de precio y contexto, no referencia de posicionamiento |
| 15 | ALTERNATIVA ECONÓMICA/MERCADO MASIVO | 59 | Pantene · Pantene Grow Abundant Sérum Anticaída para Un Pelo más Largo | B0FPLQR5XW | 9,99 € (2026-11-10 · RECIENTE) | 16,65 € | marca de mercado masivo documentada; equivalencia 59.3: presión de precio y contexto, no referencia de posicionamiento |
| 16 | ALTERNATIVA ECONÓMICA/MERCADO MASIVO | 52 | Australian Bodycare · Australian Bodycare Scalp Serum 150 ml / Hidratante para el  | B07DJK7R2B | 14,99 € (2026-10-25 · RECIENTE) | 9,99 € | marca de mercado masivo documentada; equivalencia 51.8: presión de precio y contexto, no referencia de posicionamiento |
| 17 | ALTERNATIVA ECONÓMICA/MERCADO MASIVO | 52 | Head & Shoulders · H&S DermaXPro Sérum Hidratante para Cuero Cabelludo Seco y T | B0BDZY6ZDN | 6,99 € (2026-10-27 · RECIENTE) | 4,82 € | marca de mercado masivo documentada; equivalencia 51.8: presión de precio y contexto, no referencia de posicionamiento |
| 18 | ALTERNATIVA ECONÓMICA/MERCADO MASIVO | 44 | Sylk · Sylk Aceite de Romero para el Cabello - Crecimiento, Anticaí | B0HHFQGZ5V | 12,97 € (2026-11-02 · RECIENTE) | — | equivalencia 43.8 (<55): alternativa de menor equivalencia funcional (marca sin clasificar: nunca puede ser premium) |
| 19 | PENDIENTE DE EVIDENCIA | 56 | KÉRASTASE · Kérastase Specifique Sérum de Pelo Profesional Para el Cuero | B09GBBFYF7 | 38,18 € (2026-11-12 · ACTUAL) | 42,42 € | faltan datos esenciales: Necesidad y función principal |
| 20 | PENDIENTE DE EVIDENCIA | 35 | LOBALABS · Lobalabs Raíz Viva Serum Capilar Aceite de Romero para el Ca | B0H4X4RVNH | 13,85 € (2026-11-09 · RECIENTE) | — | aplicación previa al lavado («prelavado»): no está confirmado que sea sin aclarado |
| 21 | PENDIENTE DE EVIDENCIA | 29 | WoldoHealth · WoldoHealth Aceite de Romero Capilar para Cabello - Serum co | B0C6NMCXQR | 14,99 € (2026-11-11 · ACTUAL) | — | faltan datos esenciales: Necesidad y función principal |
| 22 | PENDIENTE DE EVIDENCIA | 19 | FANOLA · Fanola, Cuidado del pelo y del cuero cabelludo - 1 unidad | B00CGPLQY6 | 14,00 € (2026-11-13 · ACTUAL) | — | faltan datos esenciales: Necesidad y función principal, Tipo de producto y aplicación |
| 23 | NO COMPARABLE | 52 | SANA- T ON CALM · SANA-T ON CALM SERUM 125ml. Reduce el picor del cuero cabell | B099ZTJKDL | 14,99 € (2025-06-12 · HISTÓRICO) | 11,99 € | producto con uso médico/farmacológico (oncologico): no es cosmético comparable |
| 24 | NO COMPARABLE | 25 | OGX · OGX ProGrowth + Peptide Champú Clarificante, Exfoliante Capi | B0G6KTWQ8N | 5,41 € (2026-11-10 · RECIENTE) | 1,41 € | producto con aclarado (champu, clarificante): no es un tratamiento leave-on como ACTIVCORE |

Detalle completo (6 componentes por producto, cobertura, evidencia): `ACTIVCORE_K3_CLASIFICACION.csv` y panel «Segmentos K3» de la plataforma.

## 3. Las cinco referencias de la infografía (una a una)
La infografía se usa como referencia de posicionamiento y selección, **no** como evidencia de precios ni ventas (los PVP, ventas y valoraciones de la maqueta no tienen fuente ni fecha).

| Referencia | Segmento K3 | Equiv. | Activos (maqueta) | Precio | Observaciones |
|---|---|--:|---|---|---|
| Kérastase Genesis Sérum (Anticaída) | COMPETIDOR DIRECTO PREMIUM | 100 | aminexil, cafeina | 39,94 € observado (ACTUAL) | Único con ASIN en la caché Keepa (B083JKPCFB): precio observado 39,94 € (2026-11-16, ACTUAL) frente a los 44,40 € de la maqueta → la maqueta queda obsoleta/no verificada. |
| Nioxin Night Density Rescue | COMPETIDOR DIRECTO PREMIUM | 100 | niacinamida, cafeina | maqueta 48,70 €: NO vigente | Sin ASIN ni precio vigente: segmento por función, marca y activos de la maqueta; precio PENDIENTE de consulta. |
| Redken Aminexil Advanced | COMPETIDOR DIRECTO PREMIUM | 97 | aminexil | maqueta 42,90 €: NO vigente | Distinto del Redken Acidic Grow (B0G59MCQT6, en la caché). Sin ASIN ni precio vigente. |
| The Ordinary Multi-Peptide Serum for Hair Density | COMPETIDOR FUNCIONAL | 87 | peptidos | maqueta 21,90 €: NO vigente | Equivalencia alta pero NO premium: posicionamiento de valor/funcional (la marca no está documentada como premium). El precio bajo no es el motivo. |
| Bio-Pilixin Bio-Pilixin Serum | COMPETIDOR FUNCIONAL | 80 | capixyl, redensyl | maqueta 54,30 €: NO vigente | Marca sin clasificar: nunca premium; función muy cercana (Capixyl + Redensyl). |

## 4. Benchmark: premium separado del mercado económico
ACTIVCORE V2 propuesto: 49,90 € / 100 mL = **49,90 €/100 mL**; coste por día **1,00 € TEÓRICO** (2 mL/día PROPUESTO ⇒ 50 días; depende de la dispensación confirmada).

- **A · Competencia directa premium**: 4 productos · 1 con precio vigente (≤30 d) · 1 históricos/sin fecha · 2 sin precio. **NO CONCLUYENTE: MUESTRA INSUFICIENTE (n=1 de precios vigentes; mínimo 3): no se calculan medianas ni rangos.**
- **B · Competencia funcional**: 9 productos · 3 con precio vigente (≤30 d) · 1 históricos/sin fecha · 2 sin precio. Mediana 26,54 €/100 mL, rango 11,65 €–43,21 € (n=3).
- **C · Mercado económico / masivo**: 5 productos · 4 con precio vigente (≤30 d) · 0 históricos/sin fecha · 0 sin precio. Mediana 8,12 €/100 mL, rango 4,82 €–16,65 € (n=4).

Premium con precio: KÉRASTASE 44,38 €/100 mL (ACTUAL); REDKEN 29,99 €/100 mL (HISTÓRICO). Con n=1 vigente no hay mediana ni conclusión de competitividad: solo comparadores individuales. **Nunca se mezclan medianas de segmentos distintos.**

## 5. Director Amazon IA
- «¿Quiénes son los principales competidores de ACTIVCORE?» → lista PRIMERO los premium (diferencias reales: necesidad, activos documentados, formato; precio con fecha y clase; equivalencia; BSR como ranking), después funcionales, contexto económico y excluidos/pendientes.
- «¿Es competitivo ACTIVCORE a 49,90 €?» → compara primero con el segmento premium (€/100 mL y coste por día teórico), luego funcional y económico por separado, excluye históricos y precios de maqueta, y declara datos incompletos y NO CONCLUYENTE.
- «¿Por qué <marca/ASIN> no es competidor?» / «…entra…» → explicación etapa A + 6 variables + condiciones premium. Sin ventas, cuotas ni eficacia inventadas. 5 chips previos intactos (5 respuestas distintas).

## 6. Validación (frente a una clasificación de referencia documentada)
**Importante:** la clasificación de referencia (`tests/k3/gold_referencia.json`, `tests/k3/heldout.json`) la redactó Claude antes de ejecutar el motor; **no es una clasificación humana independiente**. Requiere revisión de José/AHT. Los casos con dos etiquetas son ambiguos (vale cualquiera).

| Conjunto | Casos | Acuerdo | FP «relevante» | FN «relevante» | FP/FN premium |
|---|--:|--:|--:|--:|--:|
| Calibración (20 ASIN + 5 maqueta; 24 filas distintas) | 24 | 100 % | 0 | 0 | 0/0 |
| Independiente v1 (32 casos ES/DE/FR/IT, ANTES de corregir) | 32 | 84 % | 0 | 4 | 0/1 |
| Independiente tras corregir huecos léxicos (no es ya ciego) | 32 | 91 % | 0 | 1 | 0/0 |

Primera pasada ciega (v1): 5 errores (4 FN relevantes: «siero» italiano, «Haarserum» alemán, «Suero», «Wachstum»; 1 FN premium). Corregí esos huecos de vocabulario multilingüe y la regla «sin mención de pelo pero con necesidad y tipo → PENDIENTE (no excluir)»; tras ello no es una medición ciega. Errores que quedan:

- H07: motor = economica, referencia = funcional
- H12: motor = pendiente, referencia = economica
- H26: motor = pendiente, referencia = no_comparable

Lectura honesta: 0 falsos positivos (ningún producto de aclarado, medicamento, suplemento o aceite genérico se cuela como competidor) y 1 falso negativo (Maria Nila, sérum calmante de marca sin clasificar → económica; falta clasificar la marca). **Las pruebas de código en verde no validan por sí solas el motor**: la validez comercial depende de que AHT revise la referencia y la lista de marcas.

## 7. Pruebas
- `tests/k3_segmentacion_test.py` (motor, propiedades, validación, paneles, API, revisión, Director, persistencia, proceso cloud con cookie Secure/Host) y `tests/ui_k3_test.py` (Chromium real: escritorio, tablet, móvil; filtros; ficha; confirmar/rechazar; persistencia).
- Regresión: K2 33/33 (actualizado a la semántica K3, ver abajo), coordinador QA completo 38/38 y auditoría OK.
- Cambio de comportamiento deliberado en K2: el Director ahora segmenta (K3) en lugar de listar por comparabilidad ALTA/MEDIA; 12 de las 33 aserciones de `k2_director_test.py` se reescribieron a la nueva semántica (no se relajaron: se sustituyeron por equivalentes sobre premium/funcional/automático/confirmado).

## 8. Limitaciones y datos que faltan para una comparación comercial fiable
1. **Clasificación humana independiente** de al menos 40-60 productos (hoy la referencia la escribió el propio autor del motor).
2. **Lista de marcas con posicionamiento** (premium/profesional/farmacia/funcional/masivo) validada por AHT; hoy es criterio editorial y las marcas desconocidas quedan «sin clasificar» (nunca premium).
3. **Activos, concentración y función por producto**: los títulos de Amazon casi nunca los traen. Hace falta ficha/INCI/descripción (Keepa de pago o catálogo importado) para puntuar activos (15 %) y afinar necesidad.
4. **Precios vigentes (≤30 d) de los premium**: solo Kérastase Genesis tiene precio vigente; Redken Acidic Grow es de 2026-05-22 (histórico) y Nioxin/Redken Aminexil no tienen ASIN en la caché. Con n<3 no hay mediana premium. Requiere consulta Keepa autorizada (estimar tokens antes).
5. **ASIN de Nioxin Night Density Rescue, Redken Aminexil Advanced, The Ordinary Multi-Peptide y Bio-Pilixin** en Amazon.es (no están en la caché de 20).
6. **Pauta de uso y duración documentadas** de cada competidor para el coste por día (solo Bio-Pilixin trae 30 días «según fabricante» en la maqueta; ACTIVCORE: 2 mL/día es PROPUESTO).
7. **Imágenes autorizadas**: la caché Keepa no incluye imágenes; las fichas muestran «Sin imagen» en vez de copiar imágenes de terceros.
8. **Ventas, conversión, CPC y valoraciones reales** (SP-API/Ads sin conectar): el BSR es solo un ranking.
9. Cosmética facial, magnesio y omega-3: perfiles de categoría por escribir (la arquitectura ya los admite).

## 9. Estado de integración y despliegue
PR creado **sin fusionar y sin desplegar**. Fusionar a `aht-v100-desarrollo` provocaría el redeploy de Render (autodeploy por defecto) y exige tu autorización tras revisar este informe. La verificación en Render autenticado sigue pendiente de tu sesión de administrador.
