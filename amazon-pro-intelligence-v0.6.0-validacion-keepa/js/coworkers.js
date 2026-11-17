/* Coworkers: análisis locales por reglas sobre el dataset activo (DEMO o CSV importado).
   Ninguno ejecuta acciones reales: las propuestas van a la cola de aprobación. */
(function (root) {
  const C = root.Calc;
  const eur = (v) => v.toFixed(2) + ' €', pct = (v) => (v * 100).toFixed(1) + '%';
  const byProduct = (ctx) => Object.entries(C.groupBy(ctx.rows, 'product')).map(([id, rs]) => ({
    id, name: (ctx.products.find((p) => p.id === id) || {}).name || id, rows: rs, agg: C.aggregate(rs),
  }));

  const LIST = [
    { id: 'mercado', name: 'Mercado', desc: 'Demanda y competencia', color: '#18e6ff', needs: ['sp-api', 'helium10'],
      run(ctx) {
        const f = [];
        byProduct(ctx).forEach((p) => {
          const s = C.dailySeries(p.rows), h = Math.floor(s.length / 2);
          if (h < 3) return;
          const a = s.slice(0, h).reduce((x, d) => x + d.units, 0) / h, b = s.slice(h).reduce((x, d) => x + d.units, 0) / (s.length - h);
          const d = C.pctDelta(b, a);
          if (d !== null) f.push({ level: d < -0.1 ? 'warn' : 'ok', text: `${p.name}: unidades/día ${d >= 0 ? '+' : ''}${(d * 100).toFixed(0)}% (2ª mitad del periodo vs 1ª).` });
        });
        const mk = Object.entries(C.groupBy(ctx.rows, 'marketplace')).map(([k, r]) => [k, C.aggregate(r).sales]).sort((a, b) => b[1] - a[1]);
        const tot = mk.reduce((s, x) => s + x[1], 0);
        if (mk.length) f.push({ level: 'info', text: 'Reparto por marketplace: ' + mk.map(([k, v]) => `${k} ${(C.safeDiv(v, tot) * 100).toFixed(0)}%`).join(' · ') });
        return { findings: f, proposals: [] };
      } },
    { id: 'precios', name: 'Precios', desc: 'Rentabilidad y posicionamiento', color: '#ffb02e', needs: ['keepa', 'sp-api'],
      run(ctx) {
        const f = [], pr = [];
        byProduct(ctx).forEach((p) => {
          const my = C.safeDiv(p.rows.reduce((s, r) => s + r.price, 0), p.rows.length), co = C.safeDiv(p.rows.reduce((s, r) => s + r.competitor_price, 0), p.rows.length);
          const gap = co ? my / co - 1 : 0;
          f.push({ level: gap > 0.1 ? 'warn' : 'ok', text: `${p.name}: precio medio ${eur(my)} vs competencia ${eur(co)} (${gap >= 0 ? '+' : ''}${(gap * 100).toFixed(1)}%). Margen neto ${pct(p.agg.marginPct)}.` });
          if (gap > 0.1 && p.agg.marginPct > 0.12)
            pr.push({ type: 'Cambio de precio', title: `${p.name}: bajar precio a ${eur(co * 1.05)}`, detail: `Hoy ${eur(my)}; competencia ${eur(co)}; margen actual ${pct(p.agg.marginPct)}. Validar margen mínimo antes de aprobar.` });
        });
        return { findings: f, proposals: pr };
      } },
    { id: 'seo', name: 'SEO', desc: 'Keywords y visibilidad', color: '#b968ff', needs: ['helium10', 'brand-analytics'],
      run(ctx) {
        const ids = new Set(ctx.rows.map((r) => r.product));
        const kw = ctx.keywords.filter((k) => ids.has(k.product));
        const gaps = kw.filter((k) => k.rank > 10).sort((a, b) => b.volume - a.volume).slice(0, 5);
        const f = gaps.map((k) => ({ level: 'warn', text: `"${k.keyword}" (${k.product}): vol. ${k.volume.toLocaleString('es-ES')} · posición ${k.rank}.` }));
        f.unshift({ level: 'info', text: `${kw.filter((k) => k.rank <= 10).length}/${kw.length} keywords en primera página. Volúmenes y posiciones: ${ctx.source === 'demo' ? 'DEMO' : 'dataset de keywords DEMO (Helium 10 no conectado)'}.` });
        return { findings: f, proposals: gaps.slice(0, 2).map((k) => ({ type: 'Contenido / SEO', title: `Reforzar "${k.keyword}" en título y backend de ${k.product}`, detail: `Volumen ${k.volume}, posición ${k.rank}.` })) };
      } },
    { id: 'ppc', name: 'PPC', desc: 'Publicidad y rendimiento', color: '#27d3ff', needs: ['ads'],
      run(ctx) {
        const f = [], pr = [];
        byProduct(ctx).forEach((p) => {
          const be = p.agg.marginBeforeAdsPct;
          const bad = p.agg.acos > be;
          f.push({ level: bad ? 'warn' : 'ok', text: `${p.name}: ACoS ${pct(p.agg.acos)} vs ACoS de equilibrio ${pct(be)}; TACoS ${pct(p.agg.tacos)}; gasto ${eur(p.agg.adSpend)}.` });
          if (bad) pr.push({ type: 'Campaña PPC', title: `${p.name}: reducir pujas/presupuesto ~20%`, detail: `ACoS ${pct(p.agg.acos)} supera el equilibrio ${pct(be)}.` });
        });
        return { findings: f, proposals: pr };
      } },
    { id: 'creatividad', name: 'Creatividad', desc: 'Fichas, imágenes, A+ y vídeos', color: '#ff4fd8', needs: ['sp-api'], input: 'listing',
      run(ctx) {
        const t = (ctx.listingText || '').trim();
        if (!t) return { findings: [{ level: 'info', text: 'Pega título y bullets (primera línea = título, siguientes = bullets) para auditar la ficha. Sin conexión a SP-API no se leen fichas reales; imágenes/A+/vídeo no se pueden evaluar aún.' }], proposals: [] };
        const L = t.split('\n').map((x) => x.trim()).filter(Boolean), title = L[0], bullets = L.slice(1), f = [];
        f.push({ level: title.length >= 80 && title.length <= 200 ? 'ok' : 'warn', text: `Título: ${title.length} caracteres (orientativo 80–200; verificar límite de la categoría).` });
        f.push({ level: bullets.length === 5 ? 'ok' : 'warn', text: `${bullets.length} bullets (recomendado 5).` });
        bullets.forEach((b, i) => { if (b.length > 250) f.push({ level: 'warn', text: `Bullet ${i + 1}: ${b.length} caracteres (>250, se recomienda acortar).` }); });
        const low = t.toLowerCase(), top = ctx.keywords.slice().sort((a, b) => b.volume - a.volume).slice(0, 8).filter((k) => !low.includes(k.keyword.split(' ')[0]));
        if (top.length) f.push({ level: 'info', text: 'Palabras clave DEMO de alto volumen ausentes: ' + top.slice(0, 4).map((k) => k.keyword).join(', ') });
        return { findings: f, proposals: [] };
      } },
    { id: 'inventario', name: 'Inventario', desc: 'Stock, oferta y logística', color: '#b6ff2e', needs: ['sp-api'],
      run(ctx) {
        const LEAD = 30, f = [], pr = []; // supuesto de plazo de reposición (editable en código)
        const m = C.groupBy(ctx.rows, 'product');
        Object.entries(m).forEach(([id, rs]) => {
          const days = new Set(rs.map((r) => r.date)).size;
          const daily = C.safeDiv(C.aggregate(rs).units, days), stock = C.aggregate(rs).stock, cover = daily ? stock / daily : Infinity;
          const nm = (ctx.products.find((p) => p.id === id) || {}).name || id;
          const lvl = cover < LEAD ? 'warn' : cover > 120 ? 'info' : 'ok';
          f.push({ level: lvl, text: `${nm}: stock ${stock} uds · ${isFinite(cover) ? cover.toFixed(0) : '∞'} días de cobertura (plazo supuesto ${LEAD} d).` });
          if (cover < LEAD) pr.push({ type: 'Reposición', title: `${nm}: preparar envío de reposición`, detail: `Cobertura ${cover.toFixed(0)} d < plazo supuesto ${LEAD} d.` });
        });
        return { findings: f, proposals: pr };
      } },
    { id: 'reputacion', name: 'Reputación', desc: 'Reseñas y valoraciones', color: '#ff6b6b', needs: ['sp-api', 'brand-analytics'],
      run(ctx) {
        const ids = [...new Set(ctx.rows.map((r) => r.product))];
        const f = ids.map((id) => {
          const p = ctx.products.find((x) => x.id === id) || { name: id, rating: null };
          if (p.rating == null) return { level: 'info', text: `${id}: sin datos de reseñas en el dataset.` };
          return { level: p.rating < 4.2 ? 'warn' : 'ok', text: `${p.name}: ${p.rating.toFixed(1)}★ con ${p.reviews} reseñas (${ctx.source === 'demo' ? 'DEMO' : 'dato del dataset'}).` };
        });
        return { findings: f, proposals: [] };
      } },
  ];
  root.Coworkers = { LIST };
})(self);
