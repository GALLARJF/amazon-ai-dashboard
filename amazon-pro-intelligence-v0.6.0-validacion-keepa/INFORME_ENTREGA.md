# INFORME DE ENTREGA — Amazon Pro Intelligence (coordinador autónomo)

Generado: 2026-11-18T23:27:12Z · Registro íntegro: **SÍ** (229 líneas)

## 1. Pruebas

| Suite | Clase | Estado | Intentos | Resultado |
|---|---|---|---|---|
| keepa-cliente | MOCK | PASA | 1 | 27/27 OK |
| keepa-misión | MOCK | PASA | 1 | 18/18 OK |
| keepa-flujo-Director | MOCK | PASA | 1 | 16/16 OK |
| keepa-evidencias-reales | REAL-EVIDENCIA | PASA | 1 | 9/9 OK |
| v0.6-operación | MOCK | PASA | 1 | 74/74 OK |
| v0.5-catálogo | MOCK | PASA | 1 | 43/43 OK |
| API | MOCK | PASA | 1 | 51/51 OK |
| lanzador | LOCAL | PASA | 1 | 9/9 OK |
| UI-v0.6 | MOCK+NAVEGADOR | PASA | 1 | 27/27 OK |
| v0.7-keepa-real | REAL-EVIDENCIA | PASA | 1 | 21/21 OK |
| v0.7-expediente | MOCK | PASA | 1 | 41/41 OK |
| v0.7-director | MOCK | PASA | 1 | 29/29 OK |
| v0.7-seguridad | MOCK | PASA | 1 | 23/23 OK |
| UI-v0.7 | MOCK+NAVEGADOR | PASA | 1 | 31/31 OK |
| desarrollo | LOCAL | PASA | 1 | 9/9 OK |
| relevo | LOCAL | PASA | 1 | 14/14 OK |
| v1.0-matriz | LOCAL | PASA | 1 | 6/6 OK |
| v1.0-lanzar | MOCK | PASA | 1 | 12/12 OK |
| v1.0-vender | MOCK | PASA | 1 | 16/16 OK |
| v1.0-finanzas | MOCK | PASA | 1 | 20/20 OK |
| v1.0-export | MOCK | PASA | 1 | 14/14 OK |
| v1.0-persistencia | MOCK | PASA | 1 | 16/16 OK |
| v1.0-ficha | MOCK | PASA | 1 | 6/6 OK |
| v1.0-ui | MOCK+NAVEGADOR | PASA | 1 | 44/44 OK |
| v1.0-plan | MOCK | PASA | 1 | 14/14 OK |
| v1.0-conectores | MOCK | PASA | 1 | 16/16 OK |
| v1.0-docs | MOCK | PASA | 1 | 10/10 OK |
| v1.0-entrega | LOCAL | PASA | 1 | 16/16 OK |
| v1.0-cloud | MOCK | PASA | 1 | 29/29 OK |
| v1.0-ui-cloud | MOCK+NAVEGADOR | PASA | 1 | 37/37 OK |
| v1.0-respaldo-cloud | MOCK | PASA | 1 | 20/20 OK |
| k1-keepa | MOCK | PASA | 1 | 29/29 OK |
| k1-http | MOCK | PASA | 1 | 12/12 OK |
| k2-director | MOCK | PASA | 1 | 33/33 OK |
| k3-segmentacion | MOCK | PASA | 1 | 90/90 OK |
| UI-k3 | MOCK+NAVEGADOR | PASA | 1 | 37/37 OK |
| k4-unidad | MOCK | PASA | 1 | 46/46 OK |
| k4-api | MOCK | PASA | 1 | 43/43 OK |
| UI-k4 | MOCK+NAVEGADOR | PASA | 1 | 34/34 OK |
| v0.7-registro | LOCAL | PASA | 1 | 90/90 OK |
| v0.7-entrega | LOCAL | PASA | 1 | 15/15 OK |

Resumen: 41 pasan · 0 intermitentes · 0 fallan · 41 total. **MOCK = proveedores simulados, no integraciones reales.**

## 2. Conexiones (solo cuenta como verificada la que tiene llamada real y evidencia)

| Conexión | Estado | Real | Evidencia |
|---|---|---|---|
| Keepa /token y /search ES | REAL VERIFICADO (PARCIAL) | SÍ | docs_v06/evidencia_keepa_real/ (60→50 tokens, 10 consumidos) |
| GitHub GALLARJF/amazon-ai-dashboard (lectura/clonado) | VERIFICADO | SÍ | git clone OK (repo vacío) |
| GitHub (escritura/push) | BLOQUEADO 403 | no | git push rechazado: la app de Claude no tiene acceso a la organización |
| Google Drive (lectura) | VERIFICADO | SÍ | list_recent_files devolvió archivos del propietario |
| Entorno cloud (Python, terminal, Playwright) | VERIFICADO | SÍ | pruebas y capturas ejecutadas hoy |

## 3. Incidencias

- INC-001 · UI-v0.6 · RESUELTA · 6 intentos · tipo PERSISTENTE
- INC-002 · v0.7-registro · RESUELTA · 3 intentos · tipo PERSISTENTE
- INC-003 · v0.7-registro · RESUELTA · 3 intentos · tipo PERSISTENTE
- INC-004 · v1.0-entrega · RESUELTA · 3 intentos · tipo PERSISTENTE
- INC-005 · v1.0-ficha · RESUELTA · 3 intentos · tipo PERSISTENTE
- INC-006 · v1.0-entrega · RESUELTA · 3 intentos · tipo PERSISTENTE
- INC-007 · UI-k3 · RESUELTA · 6 intentos · tipo PERSISTENTE
- INC-008 · v1.0-entrega · RESUELTA · 6 intentos · tipo PERSISTENTE
- INC-009 · UI-v0.7 · RESUELTA · 2 intentos · tipo INTERMITENTE
- INC-010 · UI-k3 · RESUELTA · 2 intentos · tipo INTERMITENTE
- INC-011 · v1.0-entrega · RESUELTA · 3 intentos · tipo PERSISTENTE
- INC-012 · UI-v0.6 · RESUELTA · 6 intentos · tipo PERSISTENTE
- INC-013 · v1.0-entrega · RESUELTA · 6 intentos · tipo PERSISTENTE

## 4. Objetivos

- [HECHO] OBJ-001 Escaneo de secretos del proyecto
- [HECHO] OBJ-002 Batería de pruebas con reintentos limitados
- [HECHO] OBJ-003 Copia de seguridad local verificable (ZIP + hash)
- [HECHO] OBJ-004 Informe de entrega
- [PENDIENTE] OBJ-005 PROPIETARIO: instalar/reconectar la app de GitHub para poder hacer push (hoy 403)
- [PENDIENTE] OBJ-006 Claude: subir copia y estado a Drive (carpeta AHT_AMAZON_PRO_AUTONOMIA) tras cada ciclo con conector
- [PENDIENTE] OBJ-007 Fase siguiente (V0.7): preparada en PLAN_FASE_SIGUIENTE.md; NO iniciar hasta validar la infraestructura
- [HECHO] OBJ-008 Mantenimiento: escaneo de secretos
- [PENDIENTE] OBJ-009 Mantenimiento: batería de pruebas con reintentos
- [PENDIENTE] OBJ-010 Mantenimiento: informe de entrega actualizado
- [HECHO] OBJ-011 V0.7.0 · Datos reales de Keepa integrados (sin red ni gasto)
- [HECHO] OBJ-012 V0.7.0 · Expediente comercial ACTIVCORE v0.7
- [HECHO] OBJ-013 V0.7.0 · Director IA: briefing determinista con hechos citados
- [HECHO] OBJ-014 V0.7.0 · Experiencia NEON: Director IA, expediente y procedencia del dato
- [HECHO] OBJ-015 V0.7.0 · Seguridad de los nuevos endpoints /api/v07/*
- [HECHO] OBJ-016 V0.7.0 · Registro de suites v0.7 en la batería y el coordinador
- [HECHO] OBJ-017 V0.7.0 · Entrega candidata V0.7.0 (código, documentación, pruebas, evidencias)
- [HECHO] OBJ-018 V1.0 · Infraestructura de relevo: bloqueo, recuperación y commit controlado
- [HECHO] OBJ-019 V1.0 · Matriz de aceptación V1.0 (4 categorías) generada desde el estado real
- [HECHO] OBJ-020 V1.0 · PREPARAR Y LANZAR: flujo completo ACTIVCORE con persistencia
- [HECHO] OBJ-021 V1.0 · VENDER Y OPTIMIZAR con informes CSV importados (datos simulados etiquetados)
- [HECHO] OBJ-022 V1.0 · Motor financiero determinista: escenarios, sensibilidad, punto de equilibrio
- [HECHO] OBJ-023 V1.0 · Exportaciones CSV/HTML/Markdown con trazabilidad
- [HECHO] OBJ-024 V1.0 · Director IA: plan de coordinación de especialistas
- [HECHO] OBJ-025 V1.0 · Persistencia y recuperación: copia de seguridad, restauración y BD corrupta
- [HECHO] OBJ-026 V1.0 · NEON: cinco secciones en móvil y escritorio (Chromium real) y corrección de desbordes
- [HECHO] OBJ-027 V1.0 · Ficha única de integraciones bloqueadas
- [HECHO] OBJ-028 V1.0 · Manual de Sergio v1.0 y documentación de instalación y operación
- [HECHO] OBJ-029 V1.0 · Entrega candidata V1.0 (ZIP sin claves, copia, evidencias, bloqueos)
- [HECHO] OBJ-030 V1.0 · Adaptadores OpenAI, SP-API y Ads API (solo lectura) con pruebas simuladas identificadas
- [HECHO] OBJ-031 V1.0 · Despliegue cloud privado: modo cloud, HTTPS, usuarios por variables secretas, respaldo y paquete Docker/Render

## 5. Siguientes acciones

- OBJ-009 [1] Mantenimiento: batería de pruebas con reintentos
- OBJ-005 [2] PROPIETARIO: instalar/reconectar la app de GitHub para poder hacer push (hoy 403) (requiere a Claude/persona)
- OBJ-010 [2] Mantenimiento: informe de entrega actualizado
- OBJ-006 [4] Claude: subir copia y estado a Drive (carpeta AHT_AMAZON_PRO_AUTONOMIA) tras cada ciclo con conector (requiere a Claude/persona)
- OBJ-007 [9] Fase siguiente (V0.7): preparada en PLAN_FASE_SIGUIENTE.md; NO iniciar hasta validar la infraestructura (requiere a Claude/persona)

## 6. Límites de gasto y parada

- Presupuesto € / tokens Keepa / llamadas IA: **0 / 0 / 0** (0 = bloqueado)
- Máx. ciclos/24 h: 12 · Máx. fallos seguidos: 3 · Máx. intentos por incidencia: 3
- Parada: no activa

## 7. Limitaciones declaradas

- Ejecución NO continua: solo hay sesiones (manuales o programadas) que invocan el coordinador; entre sesiones no corre nada.
- Windows real no verificado: el lanzador y la corrección de señales se probaron solo en Linux.
- GitHub: lectura/clonado funciona pero el push devuelve 403 hasta que el propietario instale o reconecte la app de Claude en la organización.
- Las pruebas con proveedores simulados (MOCK) no demuestran integraciones reales; solo Keepa /token y /search ES tienen llamada real verificada.
- Keepa /product por ASIN, dominios DE/FR/IT/UK, OpenAI, SP-API y Ads API siguen sin verificar.
- Las sesiones programadas arrancan AISLADAS: no heredan el sistema de archivos (verificado 2026-11-17 02:28 UTC: proyecto inexistente, rama no encontrada, 0 pruebas). Solo Drive (texto) es canal compartido. Recuperar el proyecto exige publicar el codigo en GitHub (push 403: instalar/reconectar la app de Claude en GALLARJF).
