/* Director Amazon IA — V0.2: motor local de reglas sobre los datos filtrados (sin LLM conectado). */
(function (root) {
  const C = root.Calc;
  const eur = (v) => v.toLocaleString('es-ES', { maximumFractionDigits: 0 }) + ' €', pct = (v) => (v * 100).toFixed(1) + '%';

  function answer(q, ctx) {
    const t = q.toLowerCase(), a = C.aggregate(ctx.rows), p = C.aggregate(ctx.prevRows);
    const tag = ctx.source === 'demo' ? ' (DEMO)' : ' (CSV importado)';
    if (!ctx.rows.length) return { text: 'No hay datos para este filtro.' };
    const dl = (c, pv) => { const d = C.pctDelta(c, pv); return d === null ? '' : ` (${d >= 0 ? '+' : ''}${(d * 100).toFixed(1)}% vs periodo anterior)`; };
    if (/resumen|estado|c[oó]mo vamos|general/.test(t))
      return { text: `Resumen${tag}: ventas netas ${eur(a.sales)}${dl(a.sales, p.sales)}, margen ${eur(a.margin)} (${pct(a.marginPct)}), ACoS ${pct(a.acos)}, TACoS ${pct(a.tacos)}, stock ${a.stock} uds.` };
    if (/ventas/.test(t)) return { text: `Ventas netas${tag}: ${eur(a.sales)}${dl(a.sales, p.sales)}; ${a.units} unidades.` };
    if (/margen|rentab|beneficio/.test(t)) {
      const worst = Object.entries(C.groupBy(ctx.rows, 'product')).map(([id, r]) => [id, C.aggregate(r).marginPct]).sort((x, y) => x[1] - y[1])[0];
      return { text: `Margen${tag}: ${eur(a.margin)} (${pct(a.marginPct)})${dl(a.margin, p.margin)}. Margen antes de publicidad ${pct(a.marginBeforeAdsPct)}. Producto con menor margen: ${worst[0]} (${pct(worst[1])}).` };
    }
    if (/acos|tacos|ppc|publicidad|ads/.test(t)) {
      const act = a.acos > a.marginBeforeAdsPct ? [{ type: 'Campaña PPC', title: 'Reducir pujas/presupuesto ~20% en el alcance filtrado', detail: `ACoS ${pct(a.acos)} > equilibrio ${pct(a.marginBeforeAdsPct)}` }] : [];
      return { text: `Publicidad${tag}: gasto ${eur(a.adSpend)}, ACoS ${pct(a.acos)}, TACoS ${pct(a.tacos)}. ACoS de equilibrio ${pct(a.marginBeforeAdsPct)} → ${act.length ? 'estás por encima: la publicidad destruye margen.' : 'dentro de rango.'}`, actions: act };
    }
    if (/stock|inventario|reposici/.test(t)) return { text: `Stock total${tag}: ${a.stock} uds. Ejecuta el coworker Inventario para ver la cobertura por producto.` };
    if (/precio|competenc|keepa/.test(t)) {
      const my = C.safeDiv(ctx.rows.reduce((s, r) => s + r.price, 0), ctx.rows.length), co = C.safeDiv(ctx.rows.reduce((s, r) => s + r.competitor_price, 0), ctx.rows.length);
      return { text: `Precio medio propio ${my.toFixed(2)} € vs competencia ${co.toFixed(2)} € (${((my / co - 1) * 100).toFixed(1)}%)${tag}. Datos de competencia reales requieren Keepa (no conectado).` };
    }
    if (/pre-?launch|lanzamiento|go/.test(t)) return { text: 'Abre la pestaña Pre-Launch: el expediente evalúa economía, benchmark, demanda, regulatorio, contenido y stock. Un margen positivo no basta: la decisión es GO / REVISAR / NO-GO con bloqueos explicados.' };
    if (/conexi|api|sp-?api|helium|keepa/.test(t)) return { text: 'Ninguna API está conectada ni habilitada por defecto. Revisa la pestaña Estado para ver la matriz de conexiones.' };
    return { text: 'Puedo responder sobre: resumen, ventas, margen, ACoS/TACoS, stock, precios/competencia, Pre-Launch y conexiones. Solo analizo los datos cargados; no ejecuto cambios.' };
  }
  root.Director = { answer };
})(self);
