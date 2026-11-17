# INFORME DE ENTREGA — Amazon Pro Intelligence (coordinador autónomo)

Generado: 2026-11-17T02:31:25Z · Registro íntegro: **SÍ** (35 líneas)

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

Resumen: 9 pasan · 0 intermitentes · 0 fallan · 9 total. **MOCK = proveedores simulados, no integraciones reales.**

## 2. Conexiones (solo cuenta como verificada la que tiene llamada real y evidencia)

| Conexión | Estado | Real | Evidencia |
|---|---|---|---|
| Keepa /token y /search ES | REAL VERIFICADO (PARCIAL) | SÍ | docs_v06/evidencia_keepa_real/ (60→50 tokens, 10 consumidos) |
| GitHub GALLARJF/amazon-ai-dashboard (lectura/clonado) | VERIFICADO | SÍ | git clone OK (repo vacío) |
| GitHub (escritura/push) | BLOQUEADO 403 | no | git push rechazado: la app de Claude no tiene acceso a la organización |
| Google Drive (lectura) | VERIFICADO | SÍ | list_recent_files devolvió archivos del propietario |
| Entorno cloud (Python, terminal, Playwright) | VERIFICADO | SÍ | pruebas y capturas ejecutadas hoy |

## 3. Incidencias

- ninguna

## 4. Objetivos

- [HECHO] OBJ-001 Escaneo de secretos del proyecto
- [HECHO] OBJ-002 Batería de pruebas con reintentos limitados
- [HECHO] OBJ-003 Copia de seguridad local verificable (ZIP + hash)
- [HECHO] OBJ-004 Informe de entrega
- [PENDIENTE] OBJ-005 PROPIETARIO: instalar/reconectar la app de GitHub para poder hacer push (hoy 403)
- [PENDIENTE] OBJ-006 Claude: subir copia y estado a Drive (carpeta AHT_AMAZON_PRO_AUTONOMIA) tras cada ciclo con conector
- [PENDIENTE] OBJ-007 Fase siguiente (V0.7): preparada en PLAN_FASE_SIGUIENTE.md; NO iniciar hasta validar la infraestructura
- [PENDIENTE] OBJ-008 Mantenimiento: escaneo de secretos
- [PENDIENTE] OBJ-009 Mantenimiento: batería de pruebas con reintentos
- [PENDIENTE] OBJ-010 Mantenimiento: informe de entrega actualizado

## 5. Siguientes acciones

- OBJ-008 [0] Mantenimiento: escaneo de secretos
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
