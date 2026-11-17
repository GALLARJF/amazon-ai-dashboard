# Informe de auditoría — Amazon Pro Intelligence V0.2
Fecha: 2026-11-16 · Base auditada: código real de V0.1 (copia intacta conservada, verificada por hash) · Credenciales reales: **no solicitadas ni usadas**.

## 1. Resumen ejecutivo
- V0.1 **no era fiable financieramente**: daba **GO con precio negativo, IVA negativo, tres competidores idénticos y sin ningún dato regulatorio, de contenido o de stock** (evidencia reproducible en `docs/evidencia_V01_vs_V02.txt`).
- V0.1 tenía además fallos de seguridad (prueba de conectores por GET sin autenticación, servidor que exponía su propio código, conectores activos por defecto).
- V0.2 corrige estos puntos y deja la plataforma **lista para recibir datos reales, pero no para operar**: 11 bloqueos siguen abiertos (`docs/BLOQUEOS_ANTES_DE_OPERAR.md`). Ninguna conexión real se ha probado.

## 2. Hallazgos en V0.1 y resolución
| ID | Sev. | Hallazgo (evidencia) | Resolución V0.2 |
|---|---|---|---|
| A-01 | Crítica | Precio −10 € → **GO**, margen 171 % | Validación de rangos: el cálculo se **rechaza** (`unit().valid=false`) |
| A-02 | Crítica | IVA −50 % → **GO** | Rango IVA 0–30 % |
| A-03 | Alta | Sin validación de entradas (comisión 150 %, NaN, textos…) | 17 clases de entrada inválida rechazadas con mensaje |
| A-04 | Alta | GO solo con margen + mediana + 3 precios | Nueva regla: GO exige economía, benchmark vigente, demanda con fuente/fecha, regulatorio, claims, contenido y stock. Sin ello: **REVISAR** |
| A-05 | Alta | Modelo sin almacenamiento, otros costes, preparación ni FBM | Modelo completo (§3) |
| A-06 | Media | Comisión única plana | Esquemas por categoría: plano, **por umbral** (p. ej. 8 %/15 %) y **marginal**, con comisión mínima |
| A-07 | Media | ACoS de equilibrio sobre neto mezclado con ACoS de Ads | Base explícita del ACoS (PVP con IVA / neto) y advertencia |
| A-08 | Media | Benchmark sin normalizar; duplicados y datos sin fuente aceptados | €/unidad de contenido con envío, fuente y fecha obligatorias, ≤ 30 días, duplicados y atípicos excluidos |
| A-09 | Alta | `GET /api/connectors/test` sin autenticación (efecto lateral, CSRF/DNS rebinding) | `POST` + token + JSON + Origin/Host + límite de frecuencia |
| A-10 | Alta | El servidor servía todo el directorio (incl. `server.py`, tests, informe) | Lista blanca de estáticos |
| A-11 | Media | Conectores activos si existían variables de entorno | **Deshabilitados por defecto** (`AMAZON_PRO_CONNECTORS`) |
| A-12 | Media | Errores devolvían texto de excepción (posible fuga de secretos) | Códigos fijos |
| A-13 | Baja | Sin cabeceras de seguridad | CSP estricta, nosniff, X-Frame-Options, etc. |
| A-14 | Media | Margen del panel omitía devoluciones y almacenaje (sobrestimado) | Margen incluye costes opcionales; CSV sin ellos → aviso de **margen sobrestimado**. En DEMO el margen pasó de 17,1 % a 15,8 % |
| A-15 | Baja | Etiquetas «PREPARADO» y tarjeta «Radar» sin contenido (indicadores sin respaldo) | «Datos: DEMO/CSV» y tarjeta de **Alertas** calculadas |

## 3. Modelo de rentabilidad V0.2 (`js/economics.js`)
Por unidad: `neto = PVP/(1+IVA)` · `comisión = f(PVP con IVA)` según categoría (mín. incluido) · logística FBA (tarifa) o FBM (envío+embalaje+manipulación) · almacenaje FBA (€/ud/mes × meses) · producto + preparación + otros · devoluciones `% × (coste devolución + % no vendible × coste producto)` · publicidad `ACoS × base`.
`contribución = neto − costes − comisión − publicidad` · `margen = contribución/neto` · `ACoS de equilibrio = (contribución antes de ads)/base del ACoS`.
**Precio mínimo rentable**: resuelto en forma cerrada por tramo de comisión (la comisión por umbral es discontinua) y verificado; se devuelve el mínimo en céntimos que cumple el margen objetivo.

### Casos con resultado esperado calculado a mano (todos pasan, `tests/economics.test.js`)
| Caso | Esperado | Resultado |
|---|---|---|
| PVP 121 €, IVA 21 % | neto 100,00 | ✔ |
| Comisión 10 %, coste 30, FBA 10, ACoS 10 % (base PVP) | comisión 12,10 · ads 12,10 · contribución 35,80 (35,8 %) · ACoS equilibrio 39,587 % | ✔ |
| Mismo caso, base neto | ads 10,00 · contribución 37,90 · equilibrio 47,9 % | ✔ |
| Coherencia | con ACoS = equilibrio, contribución = 0 (ambas bases) | ✔ |
| Belleza 8 %/15 % | 9,99 € → 0,7992 · 10,00 € → 0,80 · 10,01 € → 1,5015 | ✔ |
| Comisión mínima | 1,50 € × 15 % = 0,225 → 0,30 | ✔ |
| Tramos marginales (15 % hasta 100, 8 % exceso) | 150 € → 19,00 · 100 € → 15,00 | ✔ |
| Devoluciones 10 %, 3 €, 50 % no vendible, coste 30 | 1,80 € | ✔ |
| FBM 4,5 + 0,4 + 0,6 · almacenaje 0,15×3 | 5,50 · 0,45 | ✔ |
| Entradas inválidas (precio 0/negativo/NaN/∞/texto, IVA −5/100, coste negativo, devoluciones 101 %, ACoS 100 %, margen 100 %, esquema desconocido…) | rechazadas | ✔ (17 casos) |
| Extremos válidos (0,01 € y 100 000 €) | sin excepción, valores finitos | ✔ |
| ACoS 60 % + margen 60 % | precio mínimo inalcanzable (`null`) | ✔ |

## 4. Expediente Pre-Launch (`js/dossier.js`)
Secciones: producto · economía y precio · benchmark normalizado · demanda/keywords (fuente+fecha ≤ 60 d) · regulatorio y claims (plantilla por cosmético/complemento/otro; «cumplido» sin evidencia no cuenta; claims sin respaldo bloquean; detección de términos de riesgo) · ficha/imágenes/vídeo/A+ · stock y logística (cobertura = previsión/30 × días objetivo).
**Decisión**: `NO-GO` si hay inviabilidad económica/competitiva (pérdida por unidad, margen inalcanzable, precio mínimo fuera de la banda competitiva) · `REVISAR` si no hay inviabilidad pero sí bloqueos (faltan datos, evidencias o stock, o el precio planificado está bajo el mínimo rentable) · `GO` solo sin bloqueos. **GO no publica nada**: pide aprobación.
Prueba clave: expediente con margen positivo y sin el resto → **REVISAR (14 bloqueos)**; en V0.1 era GO.

## 5. Pruebas ejecutadas (todas pasan)
| Suite | Comprobaciones |
|---|---|
| `calc.test.js` (agregados, filtros, CSV) | 11 |
| `economics.test.js` | 21 |
| `dossier.test.js` | 29 |
| `integration.test.js` | 16 |
| `security_test.py` (secretos falsos, transporte simulado, sin red) | 53 |
| `ui_test.py` (Playwright/Chromium, 1600×840 y 390×844) | 51 |
| `schema_test.py` (JSON Schema formal) | 5 |
Defecto encontrado y corregido durante la construcción: el hash de IDs podía producir valores con signo; lo detectó el validador del paquete antes de la entrega. Un aviso de banda saltaba por redondeo (26,90 > 26,90) y se corrigió con tolerancia de 0,005 €.

## 6. Lo que NO está verificado (límites honestos)
- Ninguna API real: el código de prueba de SP-API/Ads/Keepa se ha probado solo con transporte simulado. Endpoints, permisos y regiones reales están sin validar.
- Tarifas de comisión por categoría, FBA, almacenaje y devoluciones: **orientativas**; deben contrastarse con Amazon antes de decidir.
- Base del ACoS (con/sin IVA) sin confirmar en informes de Ads.
- Listas regulatorias y de claims: plantillas orientativas, **no asesoramiento legal**.
- Probado solo en Chromium; sin pruebas en Edge/Firefox/Windows.
- La versión previa de AHT Executive Neon no era accesible: el diseño sigue la referencia aprobada y la integración queda como contrato, no como enlace.
- Aprobaciones y expedientes viven en el navegador (`localStorage`): sin autenticación ni auditoría de servidor.
