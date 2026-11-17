# Demostración de coordinación de coworkers (V0.3)

Petición al Director: «ejecuta la campaña de publicidad (ppc)» + cumplimiento. El Director añade las dependencias, asigna las tareas y las ejecuta en orden compartiendo resultados (pizarra).

**Plan con dependencias:** mercado → seo → precios → creatividad → ppc → cumplimiento

**Flujo de resultados entre coworkers:** mercado→precios, seo→creatividad, precios→ppc, seo→ppc, creatividad→cumplimiento, mercado→cumplimiento

| Coworker | Depende de | Estado | Verificaciones | ms | Hallazgos |
|---|---|---|---|---|---|
| mercado | — | ok | True | 0 | 4 |
| seo | — | ok | True | 0 | 4 |
| precios | mercado | ok | True | 0 | 10 |
| creatividad | seo | ok | True | 0 | 5 |
| ppc | precios, seo | ok | True | 0 | 5 |
| cumplimiento | creatividad, mercado | ok | True | 0 | 2 |

**Estado de coworkers tras la ejecución (deducido de ejecuciones registradas):**

- mercado: EJECUTADO SOBRE DATOS PRUEBA (no operativo)
- seo: EJECUTADO SOBRE DATOS PRUEBA (no operativo)
- inventario: SIN EJECUCIÓN
- precios: EJECUTADO SOBRE DATOS PRUEBA (no operativo)
- creatividad: EJECUTADO SOBRE DATOS PRUEBA (no operativo)
- ppc: EJECUTADO SOBRE DATOS PRUEBA (no operativo)
- cumplimiento: EJECUTADO SOBRE DATOS PRUEBA (no operativo)

**Hallazgos del PPC que consumen resultados de Precios y SEO:**

- ACoS objetivo 18 % vs equilibrio 43.4 %: colchón 25.4 pts.
- CPC máximo de equilibrio con CVR 10 % (dato aportado): 0.86 € (= ACoS_eq × precio × CVR).
- Con presupuesto 300 €/mes y ACoS 18 %, hacen falta 1667 € de ventas publicitarias/mes (83.8 uds.) para cumplir el objetivo.
- Coordinado con SEO: 5 keywords vigentes candidatas para campañas (volúmenes aportados, no estimados).
- Solo propuesta analítica: no se crea ni modifica ninguna campaña (acciones de escritura no implementadas).