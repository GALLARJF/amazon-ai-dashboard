# Operación autónoma de Amazon Pro Intelligence (V0.6.1 · infraestructura)

## Qué hay (y qué NO hay)
- **Hay:** un coordinador (`tools/coordinador.py`, solo biblioteca estándar de Python) con estado persistente en `AUTONOMIA/`, ciclos acotados, QA con reintentos limitados, parada automática, límites de gasto, escaneo de secretos, copia de seguridad e informe de entrega.
- **Hay:** una tarea programada (ver §5) que abre una sesión nueva y ejecuta el coordinador.
- **NO hay ejecución continua.** Entre sesiones no corre nada. Lo que existe son *sesiones* (manuales o programadas) que invocan el coordinador.

## Archivos de estado (`AUTONOMIA/`, sin secretos)
| Archivo | Contenido |
|---|---|
| `estado.json` | objetivos, incidencias, pruebas, conexiones (con evidencia), limitaciones, siguientes acciones |
| `registro.jsonl` | registro de solo-añadir con cadena de hashes (`verificar` detecta manipulaciones) |
| `limites.json` | límites; presupuesto € / tokens Keepa / llamadas IA = 0 (**solo el propietario** debe cambiarlos y debe rellenar `autorizado_por`) |
| `PARAR` | si existe, ningún ciclo se ejecuta (parada manual o automática) |
| `ciclo.lock` | candado (30 min) para que no corran dos ciclos a la vez |

## Comandos
`python3 tools/coordinador.py` + `init | estado | ciclo | qa | objetivo add "título" [handler|-] [prio] [cada_horas] | objetivo hecho|bloquear|reabrir OBJ-00N | conexion nombre estado evidencia real|no | limitacion "texto" | escaneo | informe | verificar | parar "motivo" | reanudar | respaldo`

## Ciclo
guardia → escaneo de secretos → objetivo PENDIENTE de menor prioridad con manejador (`qa`, `informe`, `respaldo`, `escaneo`) → registro → estado guardado. Los objetivos con `cada_horas` se reabren solos.

## QA con reintentos
Cada suite se reintenta hasta `max_intentos_incidencia` (3). Resultado: **PASA**, **INTERMITENTE** (pasó tras reintento; abre incidencia) o **FALLA** (persistente). Los intentos se acumulan entre sesiones; al llegar al máximo la incidencia pasa a **BLOQUEADA** y requiere a una persona. Cada suite corre en su propio grupo de procesos y se mata entero al terminar o expirar (esto evita el bloqueo que tenía el lanzador).

## Gasto y parada automática
- Las pruebas corren con el entorno **saneado**: sin variables de claves y con `AMAZON_PRO_KEEPA_ENABLE=0`. Un ciclo no puede gastar tokens Keepa ni llamar a IA de pago.
- Parada si: existe `PARAR`; hay `keepa.env`/`ai.env` dentro del proyecto; el escaneo encuentra una clave; presupuesto > 0 sin `autorizado_por`; > 12 ciclos en 24 h; 3 ciclos fallidos seguidos.

## Persistencia entre sesiones: lo que está verificado
Ver `INFORME_ENTREGA.md` §2 y el informe ejecutivo. Resumen: el estado vive en `AUTONOMIA/` del proyecto; el respaldo exige subirse a Drive como texto (el conector no admite subir binarios por referencia desde esta sesión) y GitHub necesita que el propietario instale/reconecte la app de Claude (push → 403 hoy).

## Windows
El lanzador y su corrección de señales solo se han probado en Linux. **Windows no está verificado.**
