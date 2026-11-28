# Auditoría comercial ACTIVCORE → Amazon Pro Intelligence (V1.1)
Rama `aht-motor-comercial-activcore` (apilada sobre `aht-regresion-y-auditoria-4-2-1`; no toca la PR #5 ni producción). Instrucciones: comentarios #7161097828 y #7163951829 (PR #5).
Estado: HECHO = implementado y probado en local · HIPÓTESIS/POR CONFIRMAR = dato aportado por la auditoría sin evidencia oficial · NO DISPONIBLE = falta fuente.

## Qué ya existía (auditado antes de cambiar)
- Motor de economía por país (`econ6.py`, `eu.py`), clases de dato OBSERVADO…SINTÉTICO, importador CSV, RBAC viewer con POST bloqueado centralmente, modo staging sintético, Lanzamientos/Decisiones, 86 suites.
- NO existía: economía por lote/canal con redondeo por partida, prorrateo del plan por ventas, objetivos de contribución/CPA máximo, inventario enviadas/Vine/vendidas/devueltas, lectura de informes de términos de Ads, presupuesto escalonado, checklist comercial.

## Qué se añade (HECHO)
| Área | Implementación | Pruebas |
|---|---|---|
| Motor económico | `backend/comercial.py`: PVP 49,90, IVA 21 %, lote 1 = 12,55 (incluye regulación), lote 2 = 8,99 (pendiente), comisión 15 %, FBA 3,81 (pendiente), entrada/preparación/almacén, plan 39 €/mes prorrateado, promociones/incidencias, FBM 4+1 (provisional). Base FBA 15,40 · FBM 14,81 (300 ventas/90 d) · FBA 14,62 (100 ventas/90 d). Cada parámetro con fuente, fecha y estado; ninguno «verificado». | `tests/comercial_test.py` (67) |
| Niveles | Bruto, contribución, operativo, neto, caja e IVA separados; neto/caja NO CALCULABLE sin devoluciones/fijos. Sin doble imputación (regulación en lote, muestras una vez, descuento anula provisión de promociones, incentivos confirmados vs simulados). | ídem |
| Simulador | Precio, lote, canal FBA/FBM, TACoS 0/5/10/15/25 %, ventas, descuento, incentivos (cero por defecto), muestras, overrides marcados «simulado». Farmacia/web: NO CALCULABLE (sin parámetros). Tope 600 celdas. | ídem |
| Objetivos | 10/15/18/20 % de contribución, CPA máximo y presupuesto residual; NO garantizados; inalcanzable se declara. | ídem |
| Inventario/tesorería | Enviadas, Vine, vendidas, devueltas, reintegradas, stock; tesorería con IVA aparte y plazos POR CONFIRMAR. | ídem |
| Piloto y presupuesto | 100 FBA + 100 reserva AHT + 350 otros canales (NO AUTORIZADO); Ads 150 € / 10 días; tramos 150+350+750+1000, acumulado 2.250, NO AUTORIZADO; escalado BLOQUEADO sin evidencia y aprobación humana; nunca ejecuta. | ídem |
| Ads (solo lectura) | `backend/ads_lectura.py`: importación de informe de términos (CSV, ES/EN), CPC, CVR, ACoS, TACoS con denominador explícito, ventas atribuidas / no atribuidas (nunca «orgánicas»), ventana de atribución, propuestas (negativa, migrar a manual, bajar puja, esperar) con evidencia y explicación, exportación CSV para ejecución humana con neutralización de fórmulas. Umbrales los aporta la persona; si faltan se dice cuáles. | ídem |
| API | `backend/api_comercial.py` `/api/v08/*`: solo GET para viewer; único POST (importar informe) solo admin y solo a la base local. | ídem (RBAC real) |
| UI | `js/comercial.js`, sub-sección «Economía comercial» en Lanzamientos: HOY, DECISIONES y detalle plegado; sin entradas; REAL vs SIN DATOS separado. | `tests/comercial_visual_test.py` (1440/390/360/Pixel 7), capturas en `docs/comercial/capturas/` |
| Checklist | Seller, marca/Brand Registry, incentivos, regulación, listing, FBA, Vine, contenido y dependencias; sincronizado con activcore-launch-control (PR #1). | ídem |

## Qué falta / POR CONFIRMAR
- Tarifa FBA 3,81 € (peso/dimensiones), coste del lote 2 (8,99 €), FBM 4+1, ventana de atribución, base de ventas de Ads (bruta/neta), devoluciones: sin evidencia oficial → «pendiente».
- Elegibilidad y compatibilidad de incentivos temporales; Brand Registry.
- Informes reales de Ads: ninguno importado (SIN DATOS); no se han invocado API de Amazon.
- Auditoría visual en el Render real: NO DISPONIBLE (sin URL/credenciales).
- Objetivos 18–22 % de contribución: no garantizados.

## Límites respetados
Sin escrituras a Amazon, sin gasto, sin conectores reales, sin secretos, sin merge ni despliegue. El presupuesto y el piloto son propuestas, no autorizaciones.

## Regresión
`bash tests/run_all.sh`: 88 suites, 87 rc=0 en la ejecución completa (log: `regresion_run_all.log`). La única que falló (`ui_lanz_test`, exigía exactamente 3 subsecciones en Lanzamientos) se corrigió al pasar a 4 por la nueva «Economía comercial» y se reejecutó sola: 110/110. No se ha repetido la batería completa tras ese ajuste de una línea de test.
