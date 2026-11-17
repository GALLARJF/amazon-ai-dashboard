# Informe V0.3 — Coworkers reales + Director Amazon IA
Fecha de la entrega: 2026-11-16 · Base: V0.2 (intacta) · Alcance: local (127.0.0.1), sin credenciales de Amazon, sin acciones comerciales.

## 1. Resumen de estado (lo que es real y lo que no)
| Elemento | Estado | Prueba |
|---|---|---|
| Adaptador de IA configurable y seguro (anthropic, openai_compat, mock, none) | **Implementado** | `tests/backend_test.py`, `tests/api_test.py` |
| **Ejecución real con proveedor de IA** | **PENDIENTE (no hay clave)** | `demos/demo_director_ia.md`: ninguna ejecución es real |
| Coordinación de 7 coworkers por el Director (tareas, dependencias, pizarra) | **Implementada y demostrada** | `demos/demo_coordinacion_coworkers.md` |
| Coworkers «operativos» | **Ninguno** en esta entrega | Solo se marca «operativo» con ejecución verificada sobre datos USUARIO completos (probado con datos ficticios del test; el piloto real está INCOMPLETO) |
| Persistencia servidor (SQLite) de productos/expedientes/tareas/evidencias/aprobaciones/historial/auditoría | **Implementada** | `tests/store_test.py` |
| Piloto PHIVITAL Magnesio | **Mecanismo completo; datos del usuario pendientes** → decisión **REVISAR** | `docs/PILOTO_PHIVITAL_MAGNESIO.md`, captura 05 |
| Conexiones Amazon/Keepa/Helium 10 | Sin conectar (deshabilitadas por defecto) | pestaña Estado |

## 2. Director Amazon IA
- **Arquitectura:** el Director (`backend/director.py`) planifica qué coworkers hacen falta (router por tema + cierre de dependencias), crea una tarea por coworker, ejecuta en orden compartiendo resultados (pizarra), evalúa el expediente con el motor determinista y numera los **hechos [F#]**. Si hay proveedor de IA, este solo redacta una síntesis a partir de esos hechos; si no, el Director responde con el resumen determinista etiquetado **SIN IA**.
- **Anti-invención:** el prompt prohíbe cifras ajenas a los hechos; tras la respuesta, `grounding()` exige que **cada cifra** coincida con una cifra de los hechos (igual o redondeada a los decimales escritos). Si no, la respuesta se descarta, se registra el motivo y se devuelve el resumen determinista. Es una heurística: detecta cifras inventadas, no prueba veracidad.
- **Inyección de prompt:** los hechos van entre `<datos>…</datos>` declarados como no fiables, se sanean delimitadores/control, la salida nunca se ejecuta y el Director **no tiene herramientas** (no puede escribir en Amazon ni en la BD salvo registrar su propia ejecución).
- **Registro por ejecución (`ai_run`):** modelo, proveedor, modo (REAL / PRUEBA_LOCAL / SIMULADA), inicio/fin, duración, **datasets consultados (id + sha256 del expediente + tareas)**, tokens entrada/salida y su origen (proveedor o estimado), **coste estimado**, respuesta, evidencias citadas, resultado del anclaje, **errores** (códigos fijos) y **limitaciones**. Se ve en *Historial → Ejecuciones de IA*.
- **Claves:** solo variables de entorno del servidor; nunca en el navegador, respuestas, registros ni errores (probado con una clave falsa). Doble consentimiento para llamadas de pago (`AMAZON_PRO_AI_ENABLE=1`), presupuesto de entrada/salida/coste, hosts de proveedor en lista blanca (solo https; loopback solo con bandera de pruebas).
- **Modos y etiquetas:** `IA REAL` solo si el host es oficial y la llamada tuvo éxito; un servidor local de pruebas se etiqueta `PRUEBA LOCAL · no es IA real`; el mock `SIMULADA · no es IA real`. El estado «IA real verificada» solo pasa a SÍ con ≥1 ejecución REAL sin error.

## 3. Coste medido por ejecución de IA
**No hay coste real medido** (no hubo ejecución real). Lo medido es el mecanismo, con **precios de ejemplo NO verificados (3 y 15 por millón de tokens)**:

| Ejecución (demo, datos ficticios) | Modo | Tokens in/out | Origen tokens | Coste con precios de ejemplo |
|---|---|---|---|---|
| Mock | SIMULADA | 936 / 376 | estimado (chars/4) | 0,008448 USD (ilustrativo) |
| Servidor local de pruebas (camino HTTP del adaptador) | PRUEBA_LOCAL | 1500 / 60 (devueltos por el servidor de pruebas) | proveedor de pruebas | 0,0054 USD (ilustrativo) |
| Proveedor real | — | — | — | **PENDIENTE** |

Fórmula: `coste = (tokens_in × precio_in + tokens_out × precio_out) / 1e6`. Sin precios configurados el coste es «no calculado» (no se inventan tarifas). Tamaño típico del prompt del Director con 7 coworkers: ≈ 900 tokens de entrada (estimación chars/4).

## 4. Coworkers (7, deterministas)
Mercado y competencia · Precios y rentabilidad · SEO y keywords · Publicidad PPC · Creatividad/imágenes/vídeos · Inventario y logística · Reputación y cumplimiento. Cada uno devuelve hallazgos tipificados (calc/data/gap/risk) con su origen, datos que faltan y **verificaciones** (recálculo independiente). No consultan Internet ni IA: «no pueden inventar datos externos» está garantizado por construcción y probado (sin keywords no estiman demanda; sin CVR no estiman CPC; sin competidores no hay mercado).
Coordinación: Precios usa la banda de Mercado; PPC usa Precios (ACoS de equilibrio) y SEO (keywords candidatas); Creatividad usa SEO (keywords sin cubrir); Cumplimiento usa Creatividad (listing) y Mercado (reputación). Creatividad **no genera** imágenes/vídeos: produce listado de activos y briefs.
Rendimiento medido: ciclo completo de los 7 coworkers ≈ 0,25 ms; evaluación del expediente ≈ 0,08 ms (CPU local).
**Estado real (UI):** SIN EJECUCIÓN → EJECUTADO SOBRE DATOS PRUEBA/INCOMPLETO (no operativo) → DATOS INSUFICIENTES/ERROR → VERIFICACIÓN FALLIDA → OPERATIVO (solo con datos USUARIO completos y verificaciones OK). Se deduce únicamente de tareas registradas.

## 5. Economía determinista
`backend/engine.py` es un port fiel de `js/economics.js` y `js/dossier.js`. **Paridad JS↔Python: 657/657 casos** (400 económicos aleatorios + 7 extremos + 250 expedientes aleatorios; semilla fija). Los cálculos no pasan por la IA.

## 6. Persistencia, usuarios y auditoría
SQLite local: cuentas (titular legal, Seller Central, marketplaces), usuarios (scrypt), sesiones (hash SHA-256 del token), registros (marcas, productos, expedientes, datasets, evidencias, tareas, ai_runs, consultas, aprobaciones, noticias, costes) y **auditoría con cadena de hashes** (manipulación detectada en test). Roles: analyst (analiza), approver (resuelve aprobaciones y verifica noticias), admin (cuentas). Aprobaciones: solo con evaluación actual **GO**, el solicitante no puede aprobar la suya, y aprobar **no ejecuta nada**. localStorage ya no es la única copia (el Pre-Launch V0.2 local se conserva aparte).

## 7. Interfaz
Panel neón horizontal conservado (1600×840 sin scroll horizontal; móvil 390×844 sin desbordamiento). Nuevo: sesión/cuenta/titular visibles, Director con etiqueta de modo y tokens/coste, coworkers con estado real, pestañas **Piloto PHIVITAL** e **Historial · Auditoría**, noticias **solo verificadas** (fuente+URL+fecha+aprobador). Sin botones decorativos (cada botón ejecuta una acción real).

## 8. Seguridad
Hereda las 53 comprobaciones de V0.2 (solo 127.0.0.1, CSP, conectores deshabilitados, solo lectura, sin secretos). Añade: sesión HttpOnly+SameSite, CSRF, límite de intentos de login, anti-DNS-rebinding, aislamiento por cuenta, errores con códigos fijos. **No** solicita credenciales de Amazon, **no** conecta pagos, **no** se expone a Internet. Riesgos residuales: ver `BLOQUEOS_Y_PENDIENTES_V0.3.md` (#9–#10).

## 9. Pruebas automatizadas (ver ejecución final en la sección 11)
JS heredadas 11+21+29+16 · ámbito/compatibilidad 6 · paridad 657 · store/auditoría 17 · backend 51 · API 50 · seguridad heredada 53 · esquema 5 · UI en navegador real 40 · total ≈ 957 comprobaciones. Reproducir: `bash tests/run_all.sh`. Capturas reales en `capturas/` (1600×840 y móvil 390×844).

## 10. Limitaciones conocidas
- El anclaje de cifras no valida afirmaciones cualitativas.
- El router de temas del Director es por palabras clave (preguntas ambiguas ejecutan los 7 coworkers).
- Marca: sin entidad propia en UI (campo del expediente); marketplaces informativos hasta tener conectores.
- Tarifas de comisión orientativas (`verified:false`) hasta contrastarlas.
- La auditoría es detectable pero no inmutable frente a quien controle el fichero SQLite.
