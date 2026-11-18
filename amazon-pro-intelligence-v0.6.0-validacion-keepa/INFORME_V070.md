# INFORME V0.7.0 — Entrega candidata (Amazon Pro Intelligence)

Generado desde el estado del coordinador (AUTONOMIA/estado.json). Candidata: NO es producción; no se ha desplegado ni publicado nada.

## Qué incluye V0.7.0

- Datos reales de Keepa (única consulta autorizada, 10 tokens, ES) integrados sin red: `GET /api/v07/keepa-real`.
- Expediente comercial ACTIVCORE: producto, economía, mercado, regulatorio y decisión; veredicto nunca GO por defecto: `GET /api/v07/expediente` (json/md).
- Director IA determinista (sin IA): prioridades, preguntas al propietario y hechos citados: `GET /api/v07/briefing`.
- Experiencia NEON: insignias de procedencia (REAL / CALCULADO / SIN DATOS / NO CONFIRMADO) en LANZAMIENTOS y DIRECTOR IA.

## Objetivos de desarrollo (estado real)

| Clave | Estado | Intentos | Resultado |
|---|---|---|---|
| V7-01 | HECHO | 1 | aceptación OK: 21/21 OK |
| V7-02 | HECHO | 1 | aceptación OK: 40/40 OK |
| V7-03 | HECHO | 1 | aceptación OK: 29/29 OK |
| V7-04 | HECHO | 1 | aceptación OK: 31/31 OK |
| V7-05 | HECHO | 1 | aceptación OK: 23/23 OK |
| V7-06 | HECHO | 1 | aceptación OK: 35/35 OK |
| V7-07 | HECHO | 1 | aceptación OK: 15/15 OK |

## Pruebas (qué se probó)

| Suite | Clase | Estado | Resultado |
|---|---|---|---|
| keepa-cliente | MOCK | PASA | 27/27 OK |
| keepa-misión | MOCK | PASA | 18/18 OK |
| keepa-flujo-Director | MOCK | PASA | 16/16 OK |
| keepa-evidencias-reales | REAL-EVIDENCIA | PASA | 9/9 OK |
| v0.6-operación | MOCK | PASA | 74/74 OK |
| v0.5-catálogo | MOCK | PASA | 43/43 OK |
| API | MOCK | PASA | 51/51 OK |
| lanzador | LOCAL | PASA | 9/9 OK |
| UI-v0.6 | MOCK+NAVEGADOR | PASA | 27/27 OK |
| v0.7-keepa-real | REAL-EVIDENCIA | PASA | 21/21 OK |
| v0.7-expediente | MOCK | PASA | 41/41 OK |
| v0.7-director | MOCK | PASA | 29/29 OK |
| v0.7-seguridad | MOCK | PASA | 23/23 OK |
| UI-v0.7 | MOCK+NAVEGADOR | PASA | 31/31 OK |
| desarrollo | LOCAL | PASA | 9/9 OK |
| relevo | LOCAL | PASA | 14/14 OK |
| v1.0-matriz | LOCAL | PASA | 6/6 OK |
| v1.0-lanzar | MOCK | PASA | 12/12 OK |
| v1.0-vender | MOCK | PASA | 16/16 OK |
| v1.0-finanzas | MOCK | PASA | 20/20 OK |
| v1.0-export | MOCK | PASA | 14/14 OK |
| v1.0-persistencia | MOCK | PASA | 16/16 OK |
| v1.0-ficha | MOCK | PASA | 6/6 OK |
| v1.0-ui | MOCK+NAVEGADOR | PASA | 44/44 OK |
| v1.0-plan | MOCK | PASA | 14/14 OK |
| v1.0-conectores | MOCK | PASA | 16/16 OK |
| v1.0-docs | MOCK | PASA | 10/10 OK |
| v1.0-entrega | LOCAL | PASA | 16/16 OK |
| v1.0-cloud | MOCK | PASA | 29/29 OK |
| v1.0-ui-cloud | MOCK+NAVEGADOR | PASA | 37/37 OK |
| v1.0-respaldo-cloud | MOCK | PASA | 20/20 OK |
| k1-keepa | MOCK | PASA | 29/29 OK |
| k1-http | MOCK | PASA | 12/12 OK |
| k2-director | MOCK | PASA | 33/33 OK |
| v0.7-registro | LOCAL | PASA | 85/85 OK |
| v0.7-entrega | LOCAL | PASA | 15/15 OK |

Resumen: 36 pasan · 0 intermitentes · 0 fallan · 36 total. **MOCK = proveedores simulados, no integraciones reales.**

## Auditoría

- Fecha: 2026-11-18T01:17:59Z · Resultado: **CON FALLOS**
- Detalle: `{"suites": {"pasan": 34, "intermitentes": 1, "fallan": 1, "total": 36}, "escaneo_secretos": 0, "registro_integro": true, "archivos_v060_borrados": [], "pruebas_v07_sin_registrar": []}`

## Qué NO está verificado

- **Windows**: el lanzador y los `.bat` solo se probaron en Linux; no se declara verificado.
- **Conexiones externas**: solo Keepa `/token` y `/search` (ES) tienen llamada real (2026-11-17). Sin verificar: Keepa `/product`, DE/FR/IT/UK, OpenAI, SP-API, Ads API.
- Comparabilidad de competidores: automática, no confirmada por una persona. Los precios pueden ser antiguos (se muestra su fecha).
- Navegador: probado con Chromium (Playwright) en Linux; no en otros navegadores ni en Windows.

## Límites respetados

- Gasto 0 € · 0 tokens Keepa adicionales · 0 llamadas a OpenAI · sin publicación en Amazon · sin despliegue · sin credenciales en el repositorio.

## Conexiones

- Keepa /token y /search ES: REAL VERIFICADO (PARCIAL) (real)
- GitHub GALLARJF/amazon-ai-dashboard (lectura/clonado): VERIFICADO (real)
- GitHub (escritura/push): BLOQUEADO 403 (no real)
- Google Drive (lectura): VERIFICADO (real)
- Entorno cloud (Python, terminal, Playwright): VERIFICADO (real)

## Cómo continuar

Ver `OPERACION_AUTONOMA.md` y `PLAN_FASE_SIGUIENTE.md`. Decisiones del propietario pendientes: costes logísticos, evidencias regulatorias, comparabilidad, autorización de gasto Keepa/IA.
