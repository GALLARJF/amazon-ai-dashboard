/* Amazon Pro Intelligence V0.3 — controlador de interfaz */
(function () {
  const C = Calc, $ = (s, r) => (r || document).querySelector(s), $$ = (s, r) => [...(r || document).querySelectorAll(s)];
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const eur = (v) => v.toLocaleString('es-ES', { maximumFractionDigits: 0 }) + ' €', pct = (v) => (v * 100).toFixed(1) + '%';

  const S = { tab: 'panel', f: { product: 'all', period: '30', marketplace: 'all' }, ds: null, source: 'demo', listingText: '', approvals: [], conn: null, warnings: [], dossierSummary: [] };
  const store = {
    get() { try { return JSON.parse(localStorage.getItem('api_approvals') || '[]'); } catch (e) { return []; } },
    set(v) { try { localStorage.setItem('api_approvals', JSON.stringify(v)); } catch (e) { /* sin almacenamiento */ } },
  };
  S.approvals = store.get();
  const loadDemo = () => { S.ds = { rows: DemoData.rows, products: DemoData.products, keywords: DemoData.keywords }; S.source = 'demo'; };
  loadDemo();

  const ctx = () => {
    const rows = C.filterRows(S.ds.rows, S.f), prevRows = C.filterRows(S.ds.rows, S.f, 1);
    return { rows, prevRows, products: S.ds.products, keywords: S.ds.keywords, source: S.source, listingText: S.listingText };
  };

  /* ---------- Cabecera / filtros ---------- */
  function renderBadge() {
    const b = $('#badge');
    if (S.source === 'demo') { b.textContent = 'DEMO · DATOS FICTICIOS'; b.className = 'badge'; }
    else { b.textContent = 'DATOS IMPORTADOS (CSV) · SIN VERIFICAR VÍA API'; b.className = 'badge csv'; }
  }
  function renderProducts() {
    const sel = $('#fProduct'), cur = S.f.product;
    sel.innerHTML = '<option value="all">Todos los productos</option>' + S.ds.products.map((p) => `<option value="${esc(p.id)}">${esc(p.name)}</option>`).join('');
    sel.value = S.ds.products.some((p) => p.id === cur) ? cur : 'all'; S.f.product = sel.value;
  }

  /* ---------- KPIs ---------- */
  function renderKpis(c) {
    const a = C.aggregate(c.rows), p = C.aggregate(c.prevRows), demo = S.source === 'demo';
    const dl = (cur, pv, invert) => { const d = C.pctDelta(cur, pv); if (d === null) return '<div class="d">sin periodo previo</div>'; const good = invert ? d < 0 : d > 0; return `<div class="d ${good ? 'up' : 'dn'}">${d >= 0 ? '▲' : '▼'} ${Math.abs(d * 100).toFixed(1)}% vs ant.</div>`; };
    const K = [
      ['Ventas netas', eur(a.sales), dl(a.sales, p.sales), '#18e6ff'],
      ['Margen', `${eur(a.margin)} · ${pct(a.marginPct)}`, dl(a.margin, p.margin), '#b6ff2e'],
      ['TACoS', pct(a.tacos), dl(a.tacos, p.tacos, true), '#ffb02e'],
      ['ACoS', pct(a.acos), dl(a.acos, p.acos, true), '#ff4fd8'],
      ['Stock (uds)', a.stock.toLocaleString('es-ES'), '<div class="d">último día del periodo</div>', '#b968ff'],
    ];
    $('#kpis').innerHTML = K.map((k) => `<div class="card kpi" style="--c:${k[3]}">${demo ? '<span class="tg">DEMO</span>' : ''}<div class="l">${k[0]}</div><div class="v">${k[1]}</div>${k[2]}</div>`).join('');
  }

  /* ---------- Gráficos ---------- */
  function renderCharts(c) {
    const s = C.dailySeries(c.rows), b = C.bucket(s, 12), L = s.map((d) => d.date.slice(5));
    Charts.line($('#chSales'), { labels: L, series: [
      { name: 'Ventas', color: '#18e6ff', values: s.map((d) => d.sales), area: true, fmt: (v) => v.toFixed(0) + ' €' },
      { name: 'Margen', color: '#b968ff', values: s.map((d) => d.margin), fmt: (v) => v.toFixed(0) + ' €' }] });
    Charts.line($('#chComp'), { labels: L, zero: false, series: [
      { name: 'Propio', color: '#ffb02e', values: s.map((d) => d.price), fmt: (v) => v.toFixed(2) + ' €' },
      { name: 'Competidor', color: '#18e6ff', values: s.map((d) => d.competitor), fmt: (v) => v.toFixed(2) + ' €' }] });
    Charts.bars($('#chAds'), { labels: b.map((d) => d.label), series: [
      { name: 'Gasto ads', color: '#ff4fd8', values: b.map((d) => d.ad_spend), fmt: (v) => v.toFixed(0) + ' €' },
      { name: 'Ventas ads', color: '#18e6ff', values: b.map((d) => d.ad_sales), fmt: (v) => v.toFixed(0) + ' €' }] });
    Charts.line($('#chBsr'), { labels: L, zero: false, invert: true, series: [{ name: 'BSR medio', color: '#b6ff2e', values: s.map((d) => d.bsr), area: true, fmt: (v) => Math.round(v).toLocaleString('es-ES') }] });
    const ids = new Set(c.rows.map((r) => r.product)), kw = S.ds.keywords.filter((k) => ids.has(k.product)).sort((x, y) => y.volume - x.volume).slice(0, 5);
    $('#kwTable').innerHTML = kw.length
      ? `<table><tr><th>Keyword</th><th>Vol.</th><th>Pos.</th><th>Ads €</th></tr>${kw.map((k) => `<tr><td>${esc(k.keyword)}</td><td>${k.volume.toLocaleString('es-ES')}</td><td>${k.rank}</td><td>${k.spend.toFixed(0)}</td></tr>`).join('')}</table><div class="muted">Keywords ${S.source === 'demo' ? 'DEMO' : ''} · Helium 10 no conectado</div>`
      : '<div class="muted">Sin datos de keywords (Helium 10 no conectado; el CSV no incluye keywords).</div>';
  }

  /* ---------- Coworkers ---------- */
  const srcLabel = () => (S.source === 'demo' ? 'DEMO' : 'CSV');
  function renderCoworkers() { /* V0.3: lo gestiona js/v03.js (estado real desde el servidor) */ }
  function openModal(html) { $('#mBody').innerHTML = html; $('#modal').hidden = false; }
  /* ---------- Aprobaciones ---------- */
  function addApproval(p) {
    S.approvals.unshift({ id: Date.now() + Math.random(), at: new Date().toISOString().slice(0, 16).replace('T', ' '), status: 'pendiente', ...p });
    store.set(S.approvals); renderApprovals();
  }
  function renderApprovals() {
    const pend = S.approvals.filter((a) => a.status === 'pendiente').length; $('#apCount').textContent = pend;
    $('#apList').innerHTML = S.approvals.length ? S.approvals.map((a) => `<div class="ap"><div class="grow"><b>[${esc(a.type)}] ${esc(a.title)}</b><br><span class="muted">${esc(a.detail || '')} · ${esc(a.source || '')} · ${a.at}</span></div>
      ${a.status === 'pendiente' ? `<button class="btn" data-a="ok" data-id="${a.id}">Aprobar</button><button class="btn no" data-a="no" data-id="${a.id}">Rechazar</button>`
        : `<span class="tagst ${a.status === 'rechazada' ? 't-no' : 't-wait'}">${a.status === 'aprobada' ? 'APROBADA · NO EJECUTADA (sin conector de escritura: V0.3 no ejecuta nada)' : 'RECHAZADA'}</span>`}</div>`).join('')
      : '<p class="muted">Sin propuestas. Los coworkers, el Director y Pre-Launch envían aquí cualquier cambio de precio, campaña o publicación.</p>';
    $$('[data-a]').forEach((b) => (b.onclick = () => { const a = S.approvals.find((x) => String(x.id) === b.dataset.id); a.status = b.dataset.a === 'ok' ? 'aprobada' : 'rechazada'; store.set(S.approvals); renderApprovals(); }));
  }

  function initChat() { /* V0.3: el Director es server-side (js/v03.js) */ }

  /* ---------- CSV ---------- */
  function importCsv(file) {
    const rd = new FileReader();
    rd.onload = () => {
      const { rows, errors, warnings } = C.parseCSV(String(rd.result));
      if (errors.length || !rows.length) { openModal(`<h3>CSV no importado</h3>${errors.slice(0, 12).map((e) => `<div class="f warn">${esc(e)}</div>`).join('')}<p class="muted">Usa «Plantilla CSV» como guía.</p>`); return; }
      const ids = [...new Set(rows.map((r) => r.product))];
      S.ds = { rows, products: ids.map((id) => ({ id, name: id, rating: null, reviews: null })), keywords: [] }; S.source = 'csv'; S.warnings = warnings;
      S.warnings = warnings; renderProducts(); renderAll();
    };
    rd.readAsText(file);
  }

  /* ---------- Orquestación ---------- */
  function renderPanel() { const c = ctx(); renderKpis(c); renderCharts(c); renderAlerts(); }
  function renderBanner() {
    const el = $('#dq'); const w = S.source === 'csv' ? S.warnings : [];
    el.hidden = !w.length; el.innerHTML = w.map((x) => '⚠ ' + esc(x)).join('<br>');
  }
  function renderAlerts() {
    const al = Integration.alerts(S.ds.rows, S.f, S.ds.products).filter((a) => ['critica', 'alta', 'media', 'baja'].includes(a.severity)).sort((x, y) => ['critica', 'alta', 'media', 'baja'].indexOf(x.severity) - ['critica', 'alta', 'media', 'baja'].indexOf(y.severity));
    $('#alerts').innerHTML = al.length ? al.slice(0, 5).map((a) => `<div class="al ${a.severity}"><b>${esc(a.module)}</b> ${esc(a.title)}</div>`).join('') + (al.length > 5 ? `<div class="muted">+${al.length - 5} más (Estado → paquete de integración)</div>` : '')
      : '<p class="muted">Sin alertas con las reglas actuales.</p>';
    $('#alertSrc').textContent = S.source === 'demo' ? 'DEMO' : 'CSV';
  }
  function renderAll() { renderBadge(); renderBanner(); renderPanel(); renderCoworkers(); }
  function showTab(t) {
    S.tab = t; $$('.tab').forEach((x) => x.classList.toggle('on', x.id === 'tab-' + t)); $$('#tabs button').forEach((b) => b.classList.toggle('on', b.dataset.tab === t));
    if (t === 'panel') renderPanel(); if (t === 'estado') EstadoUI.render(); if (t === 'aprob') renderApprovals(); if (t === 'prelaunch') PrelaunchUI.render();
  }

  window.AmazonPro = {
    version: '0.3', exportSummary() {
      const c = ctx(), a = C.aggregate(c.rows);
      return { version: '0.3', channel: 'Amazon', dataSource: S.source === 'demo' ? 'DEMO (no real)' : 'CSV importado', filters: { ...S.f }, asOf: C.endDate(S.ds.rows),
        kpis: { sales_net_eur: a.sales, margin_eur: a.margin, margin_pct: +(a.marginPct * 100).toFixed(2), acos_pct: +(a.acos * 100).toFixed(2), tacos_pct: +(a.tacos * 100).toFixed(2), stock_units: a.stock } };
    },
    exportPackage() { const V = window.V03 && window.V03.V, ac = V && V.accounts.find((x) => x.id === V.account); return Integration.buildPackage({ rows: S.ds.rows, products: S.ds.products, filters: S.f, source: S.source, dossiers: S.dossierSummary, approvals: S.approvals, scope: ac ? { account_id: ac.id, legal_entity: ac.legal_entity, seller_central_ref: ac.seller_central_ref || null, marketplaces: ac.marketplaces, brand: null } : undefined }); },
    _state: S,
  };
  window.APP = { S, C, esc, eur, pct, addApproval, ctx, srcLabel, openModal, renderApprovals };

  document.addEventListener('DOMContentLoaded', () => {
    renderProducts(); initChat(); renderApprovals(); renderAll(); PrelaunchUI.init();
    $('#fProduct').onchange = (e) => { S.f.product = e.target.value; renderPanel(); };
    $('#fPeriod').onchange = (e) => { S.f.period = e.target.value; renderPanel(); };
    $('#fMkt').onchange = (e) => { S.f.marketplace = e.target.value; renderPanel(); };
    $('#tabs').onclick = (e) => { const b = e.target.closest('button'); if (b) showTab(b.dataset.tab); };
    $('#mClose').onclick = () => ($('#modal').hidden = true);
    $('#modal').onclick = (e) => { if (e.target.id === 'modal') $('#modal').hidden = true; };
    $('#csvFile').onchange = (e) => { if (e.target.files[0]) importCsv(e.target.files[0]); e.target.value = ''; };
    $('#resetDemo').onclick = () => { loadDemo(); S.warnings = []; renderProducts(); renderAll(); };
    $('#csvTpl').onclick = () => {
      const t = C.CSV_COLS.concat(C.CSV_OPT).join(',') + '\n2026-11-01,MI-PRODUCTO,ES,10,150.00,52.00,38.00,12.00,60.00,24.90,25.90,5400,320,3.00,2.00,0\n';
      const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([t], { type: 'text/csv' })); a.download = 'plantilla_amazon_pro_intelligence.csv'; a.click();
    };
    let tm; window.addEventListener('resize', () => { clearTimeout(tm); tm = setTimeout(() => S.tab === 'panel' && renderPanel(), 120); });
  });
})();
