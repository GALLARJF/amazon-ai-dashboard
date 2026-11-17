# K2 — Director Amazon IA: respuestas deterministas por intención (2026-11-18)

**Estado:** PR sin fusionar ni desplegar. Rama `aht-director-competidores` (base `aht-v100-desarrollo`, que ya incluye K1).

## Causa
`EUDirector.deterministic()` añadía el bloque genérico «[DATOS QUE FALTAN]» siempre que no había ranking, y para «competidores» solo contaba ASIN con `scoped_records`; no listaba nada. Además «competitivo» (precio) coincidía con la búsqueda de «compet». En Render, tras importar los 20 ASIN, la respuesta seguía siendo el resumen de datos faltantes.

## Cambio
- `backend/eu_director.py`: una intención por pregunta (precio > competidores > riesgos > faltantes > país > general) y una respuesta específica por intención.
  - **Competidores:** marca, producto, ASIN, precio, precio/100 mL (y % frente al PVP de referencia), comparabilidad, estado (**CONFIRMADO** frente a **CANDIDATO AUTOMÁTICO/SIN CONFIRMAR**), BSR (marcado «ranking, no ventas») y motivo. Orden: comparabilidad → precio/100 mL → BSR. Los BAJA se cuentan como excluidos. Sin ventas, cuota ni conclusiones.
  - **Precio:** economía por país + posición frente a candidatos (marcados no confirmados) + «no concluyente» sin ventas/CPC.
  - **País / Faltantes / Riesgos:** contenido propio (sin repeticiones entre intenciones).
- La respuesta incluye `intent` y `competitors` estructurados. La IA externa y Keepa de pago siguen apagados (no se tocó la ruta de IA).
- Arreglo previo no relacionado: `ops.py` calculaba el límite diario N2 con fecha local y los registros están en UTC → fallaba entre 00:00 y 01:00 (Madrid). Ahora UTC.

## Resultado (todo simulado, 0 red, 0 tokens)
| Prueba | Resultado |
|---|---|
| `k2_director_test` (nueva): intenciones, 20 ASIN, candidato frente a confirmado, orden, sin ventas inventadas, determinismo, 5 chips distintos entre sí, IA/Keepa off, persistencia tras reinicio (SQLite), proceso real en modo cloud con HTTPS simulado/Host/cookies/logs | 27/27 |
| Regresión: eu 30/30, director v0.7 29/29, plan V1 14/14, UI EU 18/18, cloud 29/29, K1 29+12 | OK |
| Suite completa (coordinador) | ver resumen final |

## Límites
La comparabilidad es automática (reglas K1) y los títulos de la evidencia están truncados: son candidatos hasta que una persona los confirme. Los precios son el último dato observado (algunos con 76–180 días). Sin ventas reales (SP-API/Ads sin conectar). El despliegue real en Render no se ha probado (solo proceso cloud local).
