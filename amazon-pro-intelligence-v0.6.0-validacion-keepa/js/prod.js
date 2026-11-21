/* Fase 4 · B — PRODUCTOS: una ficha ejecutiva por producto (precio, coste, margen, inventario, ventas, publicidad, documentación, estado).
   ACTIVCORE (cosmética) y PHIVITAL (suplementos) se distinguen por familia, cabecera y color. Solo lee GET existentes.
   La ausencia de un dato es SIN DATOS / NO DETERMINABLE: jamás se convierte en 0. La pantalla original (ficha completa) queda en «Metodología». */
(function (root) {
  'use strict';
  if (new URLSearchParams(location.search).get('legacy') === '1') return;
  const X = root.EX, { $, $$, esc, eur, pct, badge } = X;
  let D = null, SEL = null;
  const family = (p) => (/activcore/i.test(p.brand + ' ' + p.name) ? { id: 'activcore', name: 'ACTIVCORE', sub: 'Cosmética' } : /phivital/i.test(p.brand + ' ' + p.name) ? { id: 'phivital', name: 'PHIVITAL', sub: 'Suplementos' } : { id: 'otro', name: p.brand || 'Otros', sub: p.category || '' });
  async function load() {
    const real = X.useReal() && !!X.VV().user;
    const cat = real ? await X.get('/api/catalog') : null, home = real ? await X.get('/api/v06/home') : null, products = cat ? cat.products.filter((p) => !p.archived) : [];
    const ex = await Promise.all(products.map(async (p) => { const q = encodeURIComponent(p.id);
      const [econ, imp] = await Promise.all([X.get('/api/v06/econ?product=' + q), X.get('/api/v06/imports?product=' + q)]); return { econ, imp }; }));
    D = { logged: !!X.VV().user, real, home, items: products.map((p, i) => ({ p, econ: ex[i].econ, imp: ex[i].imp, risks: home ? (home.risks || []).filter((r) => r.product === p.id) : [] })) };
    return D;
  }
  /* ---- lógica pura (probada desde el navegador) ---- */
  const STATUS = { HISTORICO_A_REVALIDAR: 'histórico, a revalidar', DOCUMENTADO: 'documentado', VERIFICADO: 'verificado', NO_DISPONIBLE: 'no disponible' };
  const stat = (s) => STATUS[s] || String(s || '').toLowerCase().replace(/_/g, ' ');
  function price(p) { const e = Object.entries(p.pvp || {}).filter(([k, v]) => k !== 'REF' && v && v.v != null);
    if (!e.length) return { v: null, sub: 'sin PVP documentado' };
    return { v: e.map(([k, v]) => `${k} ${eur(v.v)}`).join(' · '), sub: `PVP ${stat(e[0][1].status)} · ${X.day(e[0][1].date)}` }; }
  function cost(p) { const c = p.costs && p.costs.cogs; return c && c.v != null ? { v: eur(c.v), sub: 'coste unitario ' + stat(c.status) + ' · sin IVA' } : { v: null, sub: 'sin coste documentado' }; }
  function margin(it) { const rows = ((it.econ && it.econ.rows) || []).filter((r) => r.result && r.result.margin != null && r.result.contribution != null);
    if (rows.length) { const m = rows.map((r) => r.result.margin); return { v: m.length > 1 ? `${pct(Math.min(...m))} – ${pct(Math.max(...m))}` : pct(m[0]), sub: 'margen de contribución (' + rows.length + ' país/es)' }; }
    const miss = [...new Set(((it.econ && it.econ.rows) || []).flatMap((r) => (r.result && r.result.missing) || []))];
    return { v: null, sub: it.econ && it.econ.rows && it.econ.rows.length ? 'NO DETERMINABLE: faltan ' + miss.length + ' costes de Amazon (transporte, preparación, tarifa FBA/FBM, almacenaje, devoluciones)' : 'NO DETERMINABLE: sin economía calculada' }; }
  function stock(p) { const s = p.stock; if (!s || s.v == null) return { v: null, sub: 'sin inventario documentado' };
    return /HISTORICO/.test(s.status || '') ? { v: s.v + ' uds (histórico)', sub: 'existencias históricas: no es stock disponible hoy' } : { v: s.v + ' uds', sub: stat(s.status) + ' · ' + X.day(s.date) }; }
  function sales(it) { const s = it.imp && it.imp.summary && it.imp.summary.sales; return s && typeof s.total === 'number' ? { v: eur(s.total), sub: `${s.from || ''} → ${s.to || ''} · informe importado` } : { v: null, sub: 'sin informe de ventas importado' }; }
  function ads(it) { const a = it.imp && it.imp.summary && it.imp.summary.ads; return a && typeof a.spend === 'number' ? { v: eur(a.spend) + (a.acos != null ? ' · ACoS ' + pct(a.acos) : ''), sub: 'informe de publicidad importado' } : { v: null, sub: 'sin informe de publicidad (Ads API: PENDIENTE DE CONEXIÓN)' }; }
  function docs(p) { const r = p.regulatory || {}, n = (p.documents || []).length;
    return { v: (r.state || 'SIN DATOS') + ' · ' + n + ' ' + (n === 1 ? 'documento' : 'documentos'), sub: (p.missing || []).length ? 'faltan: ' + p.missing.join(', ') : 'ficha completa', nd: !r.state }; }
  function state(it) { const n = it.risks.length, hasS = sales(it).v != null; return { v: hasS ? 'En operación' : 'Pre-lanzamiento', sub: n ? `${n} ${n === 1 ? 'riesgo abierto' : 'riesgos abiertos'}` : 'sin riesgos abiertos', n }; }
  const row = (label, o, k) => `<div class="x4f" data-x4f="${esc(label)}"><span class="x4fl">${esc(label)}</span><b class="${o.v == null || o.nd ? 'nd' : ''}">${o.v == null ? 'SIN DATOS' : esc(o.v)}</b>${o.v == null ? '' : badge(k)}<small>${esc(o.sub)}</small></div>`;
  function card(it, k) {
    const p = it.p, f = family(p), st = state(it);
    return `<article class="h2c x4prod x4f-${f.id}" id="px-${esc(p.id)}" data-pid="${esc(p.id)}"><header><span class="x4fam">${esc(f.name)} · ${esc(f.sub)}</span><h3>${esc(p.name)}</h3><span class="x4st">${esc(st.v)} · ${esc(st.sub)}</span></header>
      <div class="x4grid">${row('Precio', price(p), k)}${row('Coste', cost(p), k)}${row('Margen', margin(it), k)}${row('Inventario', stock(p), k)}${row('Ventas', sales(it), k)}${row('Publicidad', ads(it), k)}${row('Documentación', docs(p), k)}</div>
      ${it.risks.length ? `<ul class="x4risks">${it.risks.map((r) => `<li><b>${esc(r.risk)}</b> · ${esc(r.level)} — ${esc(r.why)}</li>`).join('')}</ul>` : ''}
      <p class="x4act"><button type="button" class="h2btn ghost ro-ok" data-h2go="lanz">Ver lanzamiento</button></p></article>`;
  }
  function html(d) {
    const k = X.kind();
    if (!d.logged) return `<section class="h2head"><h2>Productos ${badge('SIN DATOS')}</h2></section><article class="h2c"><p>Inicia sesión para ver los productos.</p></article>`;
    if (!d.items.length) return `<section class="h2head"><h2>Productos ${badge('SIN DATOS')}</h2></section><article class="h2c"><p>No hay productos en el catálogo.</p></article>`;
    const fams = {}; d.items.forEach((it) => (fams[family(it.p).id] = fams[family(it.p).id] || []).push(it));
    const head = (id) => { const f = family(fams[id][0].p); return `<h3 class="x4famh x4fh-${id}">${esc(f.name)} <small>${esc(f.sub)} · ${fams[id].length} ${fams[id].length === 1 ? 'producto' : 'productos'}</small></h3>`; };
    return `<section class="h2head"><h2>Productos ${badge(k)}</h2><p class="h2note">Una ficha por producto. Un dato ausente se muestra como SIN DATOS, nunca como 0.</p></section>`
      + Object.keys(fams).map((id) => head(id) + fams[id].map((it) => card(it, k)).join('')).join('');
  }
  async function render() {
    const h = X.shell('prod2', '#tab-prod', '#v6prod', []); if (!h) return; const d = await load();
    $('#prod2top').innerHTML = html(d);
    $('#prod2metb').innerHTML = '<p class="h2note">Cada ficha lee el catálogo, la economía calculada por el motor determinista y los informes de Amazon importados. Debajo, la ficha original completa (edición, costes, documentos, historial), intacta.</p>';
    if (SEL) { hl(SEL); SEL = null; }
  }
  function hl(pid) { const c = $('#px-' + pid); if (!c) return false; $$('#prod2 .x4prod.h2hl').forEach((e) => e.classList.remove('h2hl')); c.classList.add('h2hl'); c.scrollIntoView({ block: 'start' }); return true; }
  async function open(pid) { SEL = pid; if (root.V06 && root.V06.state) root.V06.state.pid = pid; root.NAV6.go('prod', 0); if ((X.NS().sec !== 'prod')) await render(); }
  function onShow(sec) { if (sec === 'prod' && (X.NS().sub || 0) === 0) render(); }
  document.addEventListener('DOMContentLoaded', () => { X.shell('prod2', '#tab-prod', '#v6prod', []); setInterval(() => { const u = X.VV().user || null; if (u !== onShow.u) { onShow.u = u; if (X.NS().sec === 'prod') render(); } }, 700); });
  root.PROD2 = { onShow, render, open, _price: price, _cost: cost, _margin: margin, _stock: stock, _sales: sales, _ads: ads, _docs: docs, _family: family };
})(self);
