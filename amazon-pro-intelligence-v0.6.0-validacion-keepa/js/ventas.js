/* Fase 4 · A — VENTAS ejecutivo. Resumen: ventas, margen, publicidad, stock, alertas. Conclusión · Decisión · Evidencia · Metodología.
   Solo lee GET existentes (home, imports, catalog, demo). Lo ausente es SIN DATOS (nunca 0). Sin rutas ni detalles técnicos en el primer nivel. */
(function (root) {
  'use strict';
  if (new URLSearchParams(location.search).get('legacy') === '1') return;
  const X = root.EX, { $, esc, eur, pct, badge, tile, fold } = X;
  let D = null;
  async function load() {
    const real = X.useReal() && !!X.VV().user, demo = X.isDemo() && !X.STG();
    const [home, cat, dm] = await Promise.all([real ? X.get('/api/v06/home') : null, real ? X.get('/api/catalog') : null, demo ? X.get('/api/v06/demo') : null]);
    const products = cat ? cat.products : [];
    const imps = real ? await Promise.all(products.map(async (p) => { const j = await X.get('/api/v06/imports?product=' + encodeURIComponent(p.id)); return { p, sum: j && j.summary, reports: (j && j.reports) || [] }; })) : [];
    D = { real, demo, home, products, dm, imps, logged: !!X.VV().user };
    return D;
  }
  /* Lógica pura: cifras agregadas (solo desde informes importados o el panel DEMO). */
  function figures(d) {
    if (d.demo && d.dm) { const k = d.dm.kpis; return { kind: 'DEMO', sales: k.ventas, margin: k.margen, ads: { spend: d.dm.spend.reduce((a, b) => a + b, 0), acos: k.acos }, tacos: k.tacos, src: 'Datos sintéticos de demostración (30 días)' }; }
    const s = d.imps.filter((x) => x.sum && x.sum.sales && typeof x.sum.sales.total === 'number'), a = d.imps.filter((x) => x.sum && x.sum.ads && typeof x.sum.ads.spend === 'number');
    const sales = s.length ? s.reduce((t, x) => t + x.sum.sales.total, 0) : null;
    const spend = a.length ? a.reduce((t, x) => t + x.sum.ads.spend, 0) : null, adsales = a.length ? a.reduce((t, x) => t + x.sum.ads.sales, 0) : null;
    return { kind: X.kind(), sales, margin: null, ads: spend == null ? null : { spend, acos: adsales ? spend / adsales : null }, tacos: sales && spend != null ? spend / sales : null, src: s.length ? 'Informes de Amazon importados sin modificar' : 'Ningún informe importado' };
  }
  function stockLine(d) {
    const ps = d.products || []; if (!ps.length) return { v: null, sub: 'Sin catálogo' };
    const ok = ps.filter((p) => p.stock && p.stock.v != null && /VERIFICADO|DOCUMENTADO/.test(p.stock.status || ''));
    const hist = ps.filter((p) => p.stock && p.stock.v != null && /HISTORICO/.test(p.stock.status || ''));
    if (ok.length) return { v: ok.reduce((t, p) => t + p.stock.v, 0) + ' uds', sub: `verificado en ${ok.length} de ${ps.length} productos` };
    if (hist.length) return { v: null, sub: `solo hay existencias históricas en ${hist.length} producto(s): no son stock de hoy` };
    return { v: null, sub: 'ningún producto con stock verificado' };
  }
  function conclusion(d, f) {
    if (!d.logged) return 'Inicia sesión para ver las ventas del negocio.';
    if (d.demo) return 'Estás viendo datos DEMO/SINTÉTICOS: no describen el negocio real.';
    if (!d.home) return 'No se pudieron cargar los datos de ventas.';
    if (f.sales == null) return (d.home.mode === 'PRELANZAMIENTO' ? 'Pre-lanzamiento: ' : '') + 'todavía no hay ventas importadas, así que no hay ventas, margen ni rentabilidad que mostrar.';
    return `Ventas importadas: ${eur(f.sales)}.` + (f.margin == null ? ' El margen no es determinable sin los costes completos de Amazon.' : '');
  }
  function decision(d, f) {
    if (!d.logged || d.demo) return 'Ninguna: esta vista no sirve para decidir con datos DEMO o sin sesión.';
    if (f.sales == null) return 'Importar un informe de ventas de Amazon (Seller Central → Informes de negocio) para activar ventas, margen y publicidad. Responsable: analista.';
    if (f.ads == null) return 'Importar también el informe de publicidad para calcular ACoS y TACoS. Responsable: analista.';
    return 'Revisar ACoS/TACoS frente al margen de equilibrio de cada producto antes de tocar presupuestos (cualquier cambio de campaña requiere aprobación).';
  }
  function html(d) {
    const f = figures(d), st = stockLine(d), nr = d.home ? (d.home.risks || []).length : null, k = f.kind;
    const tiles = [tile('Ventas', f.sales == null ? null : eur(f.sales), k, f.src), tile('Margen', f.margin == null ? null : eur(f.margin), k, f.margin == null ? 'NO DETERMINABLE: faltan costes de Amazon' : 'margen sintético'),
      tile('Publicidad', f.ads ? `${eur(f.ads.spend)}${f.ads.acos != null ? ' · ACoS ' + pct(f.ads.acos) : ''}` : null, k, f.ads ? (f.tacos != null ? 'TACoS ' + pct(f.tacos) : 'TACoS no determinable') : 'sin informe de publicidad'),
      tile('Stock', st.v, k, st.sub), tile('Alertas', d.logged && d.home ? String(nr) : null, k, nr ? 'riesgos abiertos en las fichas' : 'sin riesgos abiertos con las reglas actuales')].join('');
    return `<section class="h2head"><h2>Ventas ${badge(d.logged ? (d.demo ? 'DEMO' : f.sales == null ? 'SIN DATOS' : k) : 'SIN DATOS')}</h2><p class="h2note">${esc(f.src)}</p></section>
      <div class="x4tiles">${tiles}</div>
      <article class="h2c h2conc"><h3>Conclusión</h3><p class="h2big">${esc(conclusion(d, f))}</p></article>
      <article class="h2c"><h3>Decisión</h3><p>${esc(decision(d, f))}</p>${nr ? '<button type="button" class="h2btn ghost ro-ok" data-h2go="dec">Ver decisiones pendientes</button>' : ''}</article>`;
  }
  function evidence(d) {
    if (d.demo) return '<p class="h2note">Serie diaria sintética de 30 días (no real). El panel DEMO está en esta misma sección.</p>';
    const rows = d.imps.map((x) => { const s = x.sum && x.sum.sales && typeof x.sum.sales.total === 'number' ? x.sum.sales : null;
      return `<li class="x4row"><b>${esc(x.p.name)}</b> <span>${s ? eur(s.total) + ' · ' + esc(s.from || '') + ' → ' + esc(s.to || '') : '<b class="nd">SIN DATOS</b> · sin informe de ventas'}</span> <span>${x.reports.length} ${x.reports.length === 1 ? 'informe' : 'informes'}</span></li>`; });
    return rows.length ? `<ul class="x4list">${rows.join('')}</ul>` : '<p class="h2note">Sin evidencia que mostrar: no hay productos o no hay sesión.</p>';
  }
  async function render() {
    const h = X.shell('ventas2', '#tab-ventas', '#v6ventas', [['evi', 'Evidencia']]); if (!h) return; const d = await load();
    $('#ventas2top').innerHTML = html(d); $('#ventas2evib').innerHTML = evidence(d);
    $('#ventas2metb').innerHTML = '<p class="h2note">Las cifras salen solo de informes de Amazon importados sin modificar (ventas y publicidad) o, en modo DEMO, de datos sintéticos. TACoS = gasto publicitario ÷ ventas totales de los mismos periodos. El margen solo se muestra cuando la economía del producto está completa. Debajo, la pantalla original de importación y cálculo, intacta.</p>';
  }
  function onShow(sec) { if (sec === 'ventas' && (X.NS().sub || 0) === 0) render(); }
  document.addEventListener('DOMContentLoaded', () => { X.shell('ventas2', '#tab-ventas', '#v6ventas', [['evi', 'Evidencia']]); setInterval(() => { const u = X.VV().user || null; if (u !== onShow.u) { onShow.u = u; if (X.NS().sec === 'ventas') render(); } }, 700); });
  root.VENTAS2 = { onShow, render, _figures: figures, _conclusion: conclusion };
})(self);
