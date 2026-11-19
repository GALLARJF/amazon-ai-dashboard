# Consejero Estratégico Comercial — arquitectura, herramientas y brecha
Se integra DENTRO del Director IA de K4 (no es otra aplicación ni un segundo Director). Reutiliza K3, Pricing Intelligence, expedientes, el contrato de evidencias (`Medida`), aprobaciones (Ops N1–N4), seguimiento y el planificador robusto. IA externa y gasto: siguen en 0 hasta tu autorización.

## 1. Auditoría honesta: qué es el Director HOY
| Capa | Estado real hoy | Evidencia en el código |
|---|---|---|
| Lógica determinista | **Operativa** | `k4_pricing.dictamen` (5 tipos), `eu` (economía unitaria), `k4_bench`, `k4_selection` |
| Reglas comerciales | **Operativas, pero sin umbrales aprobados** (15 %, ±15 %… son ilustrativos) | `k4_umbrales` |
| Plantillas de redacción | **Operativas — NO son razonamiento.** Las 8 secciones, las «hipótesis alternativas» y el «plan de investigación» salen de listas fijas (`PLAN`, `hipotesis_alt`) que se activan según qué datos faltan | `k4_pricing.informe/plan_investigacion` |
| IA generativa conectada | **No operativa.** Existe un adaptador (`ai.py`: openai/anthropic/openai_compat, presupuesto, reserva de coste, comprobación numérica de cifras) pero está desactivado y hace UNA llamada sin herramientas | `AMAZON_PRO_AI_ENABLE=0` |
| Investigación con herramientas | **No existe en el producto.** Hoy no busca en la web, no lee reseñas, no consulta tendencias ni normativa | — |
| Automatización programada | **Planificador robusto probado, solo trabajos internos**, sin hilo activo | `k4_planner` |
| Seguimiento posterior | Operativo (mide, sin atribuir automáticamente) | `k4_director.medir` |
| Independencia de criterio | **Inexistente**: hoy el Director no puede contradecir una premisa que no esté codificada | — |

**Conclusión de la auditoría:** el Director actual es un *calculador con plantilla*. Detecta datos faltantes con fiabilidad, pero no investiga ni razona. No debe presentarse como consejero.

## 2. Arquitectura objetivo
```
Pregunta del directivo ──► [Planificador de investigación] ──► árbol de hipótesis + preguntas + herramientas necesarias
                                   │ (aprobación + coste estimado → Ops N2/N3)
                                   ▼
        ┌──────────── Router de herramientas (interfaz común, sin proveedor único) ────────────┐
        │ DatosInternos: K3, Keepa-caché, importaciones, costes, umbrales, seguimiento (0 €)  │
        │ Web: Buscar(consulta) · Leer(URL)           → adaptadores intercambiables            │
        │ Normativa: EUR-Lex/CosIng/CIMA/AEMPS (lectura de fuentes oficiales)                  │
        │ Literatura: PubMed/PMC/Cochrane (lectura)                                            │
        │ Marketplace (autorizado): SP-API Catalog/Search Terms, Brand Analytics*, Ads*        │
        │ Cálculo: Python determinista (aritmética SIEMPRE fuera del modelo)                   │
        └──────────────────────────────────────────────────────────────────────────────────────┘
                                   ▼
                 [Libro de evidencias]  cada hecho externo = {id, afirmación literal corta, URL, fecha de acceso, hash, tipo de fuente, calidad}
                                   ▼
   [Razonador] LLM de cualquier proveedor (interfaz ProveedorLLM) → salida ESTRUCTURADA:
        HECHOS (con id de evidencia) / HIPÓTESIS / INFERENCIAS (con premisas) / DATOS FALTANTES / DECISIÓN
                                   ▼
   [Verificador] (1) cada HECHO debe citar una evidencia del libro y coincidir con ella; (2) cifras recalculadas en código; (3) 2.º modelo/pasada «abogado del diablo» contra la conclusión; (4) detector de premisas AHT heredadas sin contraste
                                   ▼
   [Informe de 10 apartados] ──► Expediente del producto ──► Aprobación humana (Ops) ──► Seguimiento con indicadores propios
        (*) requiere autorización de vendedor/marca; hoy NO operativo
```
**Principios de diseño**
1. *Sin proveedor único:* `ProveedorLLM`, `ProveedorBusqueda`, `ProveedorLectura` son interfaces; el adaptador actual (`ai.py`) pasa a ser UN implementador. Se pueden usar a la vez modelos de distintos proveedores (p. ej. razonador A + verificador B) y modelos locales vía `openai_compat`.
2. *Ningún hecho sin evidencia:* si el verificador no encuentra la cita, el hecho se degrada a HIPÓTESIS o se elimina.
3. *Aritmética en código, nunca en el modelo.*
4. *Independencia:* el plan de investigación incluye siempre «la hipótesis contraria a la de AHT» y el verificador puntúa si el informe contradice o no alguna premisa de AHT.
5. *Estados claros:* cada herramienta indica `OPERATIVA / NO_OPERATIVA / REQUIERE_AUTORIZACIÓN`; el informe lista qué no pudo investigar.
6. *Integración:* el resultado se guarda como dossier/expediente existente, la decisión pasa por Ops (N3) y el seguimiento mide los indicadores del apartado 10.

## 3. Herramientas necesarias (y estado)
| Necesidad de investigación | Herramienta | Fuente | Estado hoy | Coste/permiso |
|---|---|---|---|---|
| Mercado y categoría | Informes públicos (Stanpa, prensa sectorial) | web | alcanzable con Buscar/Leer | 0 € (fuentes gratuitas; las de pago, no) |
| Competidores directos/indirectos (incl. fármacos OTC) | Webs de farmacia, CIMA/AEMPS (precio máx. y ficha) | web oficial | alcanzable | 0 € |
| Evidencia de activos | PubMed/PMC | literatura | alcanzable (algunas páginas fuera de la lista permitida del entorno) | 0 € |
| Claims y cumplimiento | EUR-Lex 1223/2009, 655/2013, CosIng, manual borderline | oficial | alcanzable | 0 € |
| Precios Amazon vigentes | Keepa (caché 20 ASIN; refresco) | API de pago | **desactivado** | tokens |
| Reseñas y necesidades insatisfechas | Reseñas de Amazon | — | **NO alcanzable de forma autorizada**: el scraping está excluido. Rutas: SP-API *Customer Feedback* (solo reseñas de tus propios ASIN, requiere rol de marca — por verificar) · reseñas que AHT exporte de su cuenta · estudio con clientes propios | permisos |
| Tendencias de búsqueda/demanda | Brand Analytics (Search Query Performance) / Google Trends | Amazon (requiere Brand Registry) / público | **NO operativo** | Brand Registry |
| Calidad de listing | Revisión asistida de TU listing (texto/imágenes que AHT aporte) | interna | alcanzable con datos aportados | 0 € |
| Publicidad y conversión | Amazon Ads API / informes | Amazon | **NO operativo** (CSV importable) | autorización |
| Rentabilidad y costes | Ficha de costes + tarifas oficiales | interna + Amazon | parcial (10,03 € sin alcance) | 0 € |
| Nuevos productos/mercados | K3 ampliado por búsquedas + Keepa | mixto | parcial | tokens |

## 4. Capacidad actual frente al objetivo (brecha)
| Capacidad exigida | Hoy | Objetivo | Qué falta |
|---|---|---|---|
| Investigar más allá de los 24 registros | No | Sí | Router de herramientas + libro de evidencias + planificador de investigación |
| Contradecir a AHT | No | Sí | Verificador adversarial + registro de premisas AHT |
| Diagnóstico causal (hechos/hipótesis/inferencias/faltantes/decisión) | Plantilla fija | Estructura generada y verificada | Razonador estructurado + verificador |
| Informe de 10 apartados | 8 secciones de plantilla | 10 apartados con evidencias a favor/en contra, alternativas e indicadores | Nuevo esquema de informe |
| Aprender del resultado | Medición básica | Contraste predicción vs. resultado | Registro de predicciones del Director y su puntuación |
| Proveedor múltiple | 1 adaptador | N adaptadores | Interfaces + tests de contrato |

**Qué es hoy reutilizable tal cual:** `Medida`/estados, `ai.py` (presupuesto, reservas, anclaje numérico, hosts permitidos), `k4_planner` (leases, reintentos, tope, parada), Ops (aprobación N3), seguimiento, derechos de imagen, exportación.
