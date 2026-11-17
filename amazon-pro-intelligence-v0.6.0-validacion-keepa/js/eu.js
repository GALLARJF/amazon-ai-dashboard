/* AHT Executive Neon · Amazon Pro Intelligence V0.5.0 — EUROPA multiproducto.
   Navegación: Categoría → Producto → Europa → Expediente → Director IA. Todo viene del servidor; lo que falta se muestra NO DISPONIBLE / NO EVALUABLE.
   Sin claves en el navegador. Sin manejadores inline (CSP). */
(function (root) {
  const $ = (s, r) => (r || document).querySelector(s), $$ = (s, r) => [...(r || document).querySelectorAll(s)];
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const NA = '<span class="tagst t-no">NO DISPONIBLE</span>';
  const E = { cats: [], prods: [], meta: null, cat: null, pid: null, view: 'europa', ov: null, country: 'DE', pvp: null, econ: null, bench: null, comp: 'all', evq: 'all', confirmedOnly: false, period: 'all', chat: {}, busy: false, msg: '', plan: null, run: null, running: false, archived: false, edit: null, versions: [] };
  const api = (m, p, b) => root.V03.api(m, p, b);
  const n2 = (x, d = 2) => (x == null ? NA : Number(x).toFixed(d));
  const pct = (x) => (x == null ? NA : (x * 100).toFixed(1) + ' %');
  const chip = (s) => `<span class="tagst ${({ VERIFICADO: 't-ok', DOCUMENTADO: 't-ok', A_CONFIRMAR: 't-wait', HISTORICO_A_REVALIDAR: 't-wait', HIPOTESIS: 't-wait', PROPUESTO: 't-wait', NO_DISPONIBLE: 't-no' })[s] || 't-wait'}">${esc(s)}</span>`;
  const stCls = (s) => (/EVALUABLE|SIN DATOS|SIN EJEC|INCOMPLETO|SIN REVISAR/.test(s) ? 't-no' : /OPERATIVO|OK/.test(s) ? 't-ok' : 't-wait');
  const role = () => root.V03.V.role; const isAdmin = () => role() === 'admin'; const canEdit = () => ['admin', 'approver'].includes(role());
  const P = () => E.prods.find((p) => p.id === E.pid);
  const q = (path) => path + (path.includes('?') ? '&' : '?') + 'product=' + encodeURIComponent(E.pid);
  const fv = (f, u) => (!f || f.v == null ? NA : esc(f.v) + (u ? ' ' + u : '') + ' ' + chip(f.status));

  function bars(items, opt) {
    opt = opt || {}; const W = 520, rowH = 22, H = items.length * rowH + 8, max = Math.max(...items.map((i) => i.v), opt.max || 0.0001);
    return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(opt.label || 'gráfico')}" style="width:100%;max-width:620px;height:auto">${items.map((it, i) => { const w = Math.max(2, (it.v / max) * 300); const y = 4 + i * rowH; return `<text x="0" y="${y + 14}" fill="#8ea6bd" font-size="11">${esc(it.label)}</text><rect x="150" y="${y + 2}" width="${w}" height="14" rx="3" fill="${esc(it.color || '#18e6ff')}"/><text x="${156 + w}" y="${y + 14}" fill="#eaf6ff" font-size="11">${esc(it.text != null ? it.text : it.v)}</text>`; }).join('')}</svg>`;
  }
  const trend = (h, days) => { // pendiente del BSR en el periodo (positiva = mejora de posición). n/d si faltan puntos.
    if (!h || h.length < 3) return NA; const last = h[h.length - 1][0], t1 = Date.parse(last); const sel = days === 'all' ? h : h.filter((x) => (t1 - Date.parse(x[0])) / 86400000 <= days);
    if (sel.length < 3 || !(sel[0][1] > 0)) return NA; const d = (sel[0][1] - sel[sel.length - 1][1]) / sel[0][1]; return `<span class="${d >= 0 ? 'good' : 'bad'}">${d >= 0 ? '▲' : '▼'} ${(Math.abs(d) * 100).toFixed(0)} %</span>`;
  };

  // ------------------------------------------------------------------ carga ----------------------------------------------------------------------
  async function load() {
    const el = $('#euRoot'); if (!el) return;
    if (!root.V03.V.user) { el.innerHTML = '<article class="card c-amber wide"><p class="muted">Inicia sesión para ver la inteligencia de mercado europea.</p></article>'; return; }
    const r = await api('GET', '/api/catalog' + (E.archived ? '?archived=1' : ''));
    if (!r.ok) { el.innerHTML = `<article class="card c-amber wide"><p class="muted">${esc(r.j.error || 'Sin acceso')}</p></article>`; return; }
    E.cats = r.j.categories; E.prods = r.j.products; E.meta = r.j;
    if (!E.cat || !E.cats.find((c) => c.id === E.cat)) E.cat = (E.prods[0] || {}).category || (E.cats[0] || {}).id;
    if (E.pid && !P()) E.pid = null;
    if (E.pid) await loadProduct(); else render();
  }
  async function loadProduct() { // al seleccionar un producto se cargan automáticamente todos los paneles
    E.plan = null; E.run = null; E.msg = ''; E.edit = null;
    const r = await api('GET', q('/api/eu/overview'));
    if (!r.ok) { E.ov = null; E.denied = r.j.error || 'Sin acceso a este producto'; return render(); }
    E.denied = null; E.ov = r.j; E.pvp = E.ov.settings.pvp_ref || null; if (!E.ov.names[E.country]) E.country = 'DE';
    await Promise.all([loadEcon(), loadBench()]); render();
  }
  async function loadEcon() { const r = await api('GET', q(`/api/eu/economics?country=${E.country}&pvp=${E.pvp || 0}`)); E.econ = r.ok ? r.j : null; }
  async function loadBench() { const r = await api('GET', q(`/api/eu/benchmark?country=${E.country}`)); E.bench = r.ok ? r.j : null; }
  async function loadVersions() { const r = await api('GET', '/api/catalog/product?id=' + encodeURIComponent(E.pid)); E.versions = r.ok ? r.j.versions : []; }

  // ------------------------------------------------------------------ navegación ---------------------------------------------------------------
  function nav() {
    const p = P(), steps = [['Categoría', !!E.cat], ['Producto', !!E.pid], ['Europa', E.pid && E.view === 'europa'], ['Expediente', E.pid && E.view === 'expediente'], ['Director IA', E.pid && E.view === 'director']];
    const cats = E.cats.map((c) => `<button class="euchip ${c.id === E.cat ? 'on' : ''}" data-cat="${esc(c.id)}">${esc(c.name)} <small>${E.prods.filter((x) => x.category === c.id).length}</small></button>`).join('') + (canEdit() ? '<button class="euchip add" id="euNewCat">+ categoría</button>' : '');
    const prods = E.prods.filter((x) => x.category === E.cat).map((x) => `<button class="eucard ${x.id === E.pid ? 'on' : ''} ${x.archived ? 'arch' : ''}" data-pid="${esc(x.id)}"><b>${esc(x.name)}</b><small>${esc(x.brand)} · ${esc(x.subcategory || 'sin subcategoría')}${x.archived ? ' · ARCHIVADO' : ''}</small>
      <span>${x.format.content == null ? 'formato: ' + NA : esc(x.format.content) + ' ' + esc(x.format.unit)} · PVP ${x.pvp.REF ? esc(x.pvp.REF.v) + ' € ' + chip(x.pvp.REF.status) : NA}</span><em>${x.missing.length ? 'falta: ' + esc(x.missing.slice(0, 3).join(', ')) + (x.missing.length > 3 ? '…' : '') : 'ficha completa'}</em></button>`).join('') + (canEdit() ? '<button class="eucard add" id="euNewProd">+ Nuevo producto</button>' : '');
    return `<article class="card c-cyan wide eunav"><h3>AHT EXECUTIVE NEON · EUROPEAN MARKET INTELLIGENCE <small>multiproducto · multicategoría · multipaís</small></h3>
      <ol class="eusteps">${steps.map((s, i) => `<li class="${s[1] ? 'on' : ''}">${i + 1}. ${s[0]}</li>`).join('')}</ol>
      <div class="euchips" id="euCats">${cats}</div><div class="eucards" id="euProds">${prods || '<span class="muted">No hay productos en esta categoría.</span>'}</div>
      <label class="chk"><input id="euArch" type="checkbox" ${E.archived ? 'checked' : ''}> mostrar archivados</label></article>`;
  }

  function header() {
    const p = P(); if (!p) return '';
    const view = (v, t) => `<button class="euview ${E.view === v ? 'on' : ''}" data-view="${v}">${t}</button>`;
    return `<article class="card c-violet wide euhead"><div class="eubar"><h3>${esc(p.name)} <small>${esc(p.brand)} · ${esc(E.cats.find((c) => c.id === p.category).name)} · v${p.version}</small></h3>
      <button class="btn" id="euAnalyze" ${E.denied ? 'disabled' : ''}>ANALIZAR EUROPA</button></div>
      <div class="euviews">${view('europa', 'Europa')}${view('expediente', 'Expediente')}${view('director', 'Director IA')}${view('ficha', 'Ficha y versiones')}</div></article>`;
  }

  function kpis() {
    const ov = E.ov, rk = ov.ranking, f = ov.card || {}, bm = E.bench && E.bench.benchmark, es = E.econ && E.econ.scenarios.find((s) => s.pvp_gross === E.pvp) || (E.econ && E.econ.scenarios[Math.floor(E.econ.scenarios.length / 2)]);
    const all = [...rk.ranking, ...rk.pending], cp = all.find((x) => x.country === E.country) || {}, needs = rk.pending.reduce((n, p) => n + p.missing.length, 0), kill = ov.claims.filter((c) => c.state === 'REFORMULAR_O_ELIMINAR').length;
    const kp = (t, v, c, s) => `<div class="kpi" style="--c:${c}"><small>${t}</small><b>${v}</b>${s ? `<em>${s}</em>` : ''}</div>`;
    return `<div class="kpis">${kp('Precio mediano comparables (€/' + esc(ov.norm_unit) + ')', bm && bm.price_norm ? n2(bm.price_norm.median) : 'NO DISPONIBLE', '#18e6ff', bm && bm.price_norm ? `n=${bm.price_norm.n} comparables` : 'sin comparables')}
      ${kp('Margen estimado (' + E.country + (E.pvp ? ', PVP ' + n2(E.pvp) : '') + ')', es && es.complete ? pct(es.margin_before_ads) : 'NO CALCULABLE', '#b6ff2e', es && es.complete ? esc(es.label) : es ? esc((es.missing || []).length ? 'faltan datos' : '') : '')}
      ${kp('ACoS de equilibrio (sin IVA)', es && es.complete ? pct(es.breakeven_acos_ex_vat) : 'NO CALCULABLE', '#ffb02e', es && es.complete ? 'con IVA: ' + pct(es.breakeven_acos_inc_vat) : '')}
      ${kp('Oportunidad del país', cp.evaluable ? n2(cp.score, 1) : 'NO EVALUABLE', '#ff4fd8', 'cobertura ' + ((cp.coverage || 0) * 100).toFixed(0) + ' %')}
      ${kp('Competidores analizados', bm ? bm.used + ' / ' + bm.total : '0', '#18e6ff', bm ? (bm.automatic || 0) + ' automáticos · ' + (bm.total - bm.unconfirmed) + ' confirmados' : 'ejecuta «Analizar Europa»')}
      ${kp('Datos faltantes', needs, '#ff5d5d', 'criterio-país sin dato')}
      ${kp('Stock', f.stock && f.stock.v != null ? esc(f.stock.v) + ' uds' : 'NO DISPONIBLE', '#ffb02e', f.stock && f.stock.v != null ? esc(f.stock.status) : 'sin stock verificado')}
      ${kp('Riesgos críticos', kill, '#ff5d5d', 'claims a reformular/eliminar')}</div>`;
  }

  function filters() {
    const ov = E.ov;
    return `<div class="eufil"><label>Categoría<select disabled><option>${esc(E.cats.find((c) => c.id === P().category).name)}</option></select></label><label>Producto<select disabled><option>${esc(P().name)}</option></select></label>
      <label>País / marketplace<select id="euCountry">${Object.keys(ov.names).map((c) => `<option value="${c}" ${c === E.country ? 'selected' : ''}>${esc(ov.names[c])} · ${esc(ov.market[c])}${['NL', 'PL', 'SE', 'BE', 'IE'].includes(c) ? ' (sin Keepa)' : ''}</option>`).join('')}</select></label>
      <label>PVP con IVA (€)<select id="euPvp">${(ov.pvp_scenarios && ov.pvp_scenarios.length ? ov.pvp_scenarios : [29.9, 34.9, 39.9, 44.9, 49.9, 54.9, 59.9]).map((p) => `<option value="${p}" ${p === E.pvp ? 'selected' : ''}>${Number(p).toFixed(2)}</option>`).join('')}</select></label>
      <label>PVP personalizado<input id="euPvpC" type="number" min="1" step="0.1" placeholder="p. ej. 47.5"></label>
      <label>Periodo BSR<select id="euPeriod">${[['all', 'todo'], [30, '30 días'], [90, '90 días'], [180, '180 días'], [365, '365 días']].map(([v, t]) => `<option value="${v}" ${String(E.period) === String(v) ? 'selected' : ''}>${t}</option>`).join('')}</select></label>
      <label>Comparabilidad<select id="euComp">${['all', 'ALTA', 'MEDIA', 'BAJA'].map((c) => `<option value="${c}" ${c === E.comp ? 'selected' : ''}>${c === 'all' ? 'todas' : c}</option>`).join('')}</select></label>
      <label>Calidad de evidencia<select id="euEvq">${['all', 'ALTA', 'BAJA'].map((c) => `<option value="${c}" ${c === E.evq ? 'selected' : ''}>${c === 'all' ? 'todas' : c}</option>`).join('')}</select></label>
      <label class="chk"><input id="euConf" type="checkbox" ${E.confirmedOnly ? 'checked' : ''}> solo confirmados</label>
      <span class="muted">Fuente: Keepa API (caché local) · datos reales parciales · nada simulado en este módulo</span></div>`;
  }

  // ------------------------------------------------------------------ descubrimiento ----------------------------------------------------------
  function discoveryPanel() {
    const pl = E.plan, run = E.run, ov = E.ov, d = ov.discovery;
    let h = `<article class="card c-amber wide" id="euDisc"><h3>Descubrimiento automático de competidores <small>sin introducir ASIN · coste previo · autorización · trazabilidad</small></h3>`;
    if (d && !run) h += `<p class="muted">Última ejecución: ${esc(d.at)} · ${esc(d.status)} · ${d.tokens_spent} tokens · ${d.countries.map((c) => c.country + ': ' + c.registered + ' candidatos').join(' · ')}${d.pending.length ? ' · ' + d.pending.length + ' pendientes (reanudable)' : ''}</p>`;
    if (!pl && !run) h += `<p class="muted">Pulsa <b>ANALIZAR EUROPA</b>: se generan los términos de búsqueda por idioma, se calcula el coste en tokens de Keepa ANTES de gastar y se pide tu autorización.</p>`;
    if (E.running) h += '<p class="al media">Consultando Keepa… (la cuota del plan es 1 token/min: las ejecuciones grandes pueden quedar PARCIALES y reanudarse)</p>';
    if (pl) {
      h += `<div class="euscroll"><table class="tbl"><tr><th>País</th><th>Estado</th><th>Términos de búsqueda</th><th>Búsquedas / caché</th><th>Tokens máx.</th></tr>${pl.countries.map((c) => `<tr><td>${esc(ov.names[c.country] || c.country)}</td><td><span class="tagst ${c.status === 'LISTO' ? 't-ok' : 't-no'}">${esc(c.status)}</span></td><td>${c.terms ? esc(c.terms.join(' · ')) + `<br><small class="muted">${esc(c.terms_origin)}</small>` : esc(c.explanation)}</td><td>${c.status === 'LISTO' ? c.queries_to_run + ' / ' + c.queries_cached : '—'}</td><td>${c.tokens}</td></tr>`).join('')}</table></div>
        <p>Consumo máximo previsto: <b>${pl.estimated_tokens_max} tokens</b> · presupuesto por lote ${pl.batch_budget} · tope ${pl.hard_cap} · saldo conocido ${pl.tokens_left_known == null ? 'n/d' : pl.tokens_left_known} · recarga ${pl.refill_per_min == null ? 'n/d' : pl.refill_per_min + '/min'}${pl.eta_minutes_if_short ? ' · espera estimada si falta saldo ≈ ' + pl.eta_minutes_if_short + ' min' : ''}.</p>
        <p class="muted">${esc(pl.assumptions)}</p><details><summary>Fórmula de comparabilidad (transparente)</summary><p class="muted">${esc(pl.formula)}</p></details>
        <div class="eufil"><label>Profundidad<select id="dsDepth">${['ligera', 'normal', 'profunda'].map((x) => `<option ${x === pl.depth ? 'selected' : ''}>${x}</option>`).join('')}</select></label><label>Máx. ASIN por país<input id="dsMax" type="number" min="3" max="30" value="${pl.max_candidates}"></label><label>Autorizar hasta (tokens)<input id="dsTok" type="number" min="1" value="${pl.estimated_tokens_max || 30}"></label>
        <button class="btn ghost sm" id="dsRe">Recalcular plan</button>${isAdmin() ? '<button class="btn" id="dsGo" ' + (pl.keepa_enabled ? '' : 'disabled') + '>Autorizar y ejecutar</button>' : '<span class="muted">Solo el administrador ejecuta consultas Keepa.</span>'}<button class="btn no sm" id="dsNo">Cancelar</button></div>
        ${pl.keepa_enabled ? '' : '<p class="f warn">Keepa no está habilitado (keepa.env: clave y ENABLE=1). El plan se muestra, pero no se puede ejecutar.</p>'}`;
    }
    if (run) {
      h += `<p><span class="tagst ${run.status === 'COMPLETO' ? 't-ok' : 't-wait'}">${esc(run.status)}</span> ${run.explanation ? esc(run.explanation) : ''}${run.tokens_spent != null ? ' · tokens gastados ' + run.tokens_spent : ''}</p>`;
      if (run.countries) h += `<div class="euscroll"><table class="tbl"><tr><th>País</th><th>Estado</th><th>Candidatos</th><th>Consultados</th><th>Registrados</th><th>Tokens</th></tr>${run.countries.map((c) => `<tr><td>${esc(ov.names[c.country])}</td><td>${esc(c.status)}</td><td>${c.candidates_found}</td><td>${c.fetched}</td><td>${c.registered}</td><td>${c.tokens}</td></tr>`).join('')}</table></div>`;
      if (run.pending && run.pending.length) h += `<p class="muted">${run.pending.length} pasos pendientes (${esc([...new Set(run.pending.map((p) => p.reason))].join(', '))}). Vuelve a ejecutar: la caché evita repetir lo ya consultado.</p>`;
      (run.errors || []).forEach((e) => (h += `<p class="f warn">${esc(e.explanation || e.code)}</p>`));
    }
    if (isAdmin()) h += `<details><summary>Entrada manual de ASIN (opción avanzada)</summary><p class="muted">No es el flujo normal. Los ASIN manuales no cuentan en el benchmark hasta confirmar su comparabilidad.</p><textarea id="dsAsins" rows="2" placeholder="ASIN del país seleccionado (${esc(E.country)}), separados por comas o líneas" style="width:100%"></textarea><button class="btn ghost sm" id="dsMan">Registrar y consultar</button></details>`;
    return h + '</article>';
  }

  // ------------------------------------------------------------------ vistas -----------------------------------------------------------------------
  function viewEuropa() {
    const ov = E.ov, rk = ov.ranking, ec = E.econ, bm = E.bench && E.bench.benchmark, kst = ov.keepa;
    const ses = rk.ranking.length ? 'RECOMENDACIÓN PROVISIONAL' : 'SIN DATOS SUFICIENTES (REVISAR)';
    const h = [];
    h.push(`<article class="card c-cyan wide"><h3>Resumen ejecutivo · ${esc(P().name)}</h3><div class="eudec ${rk.ranking.length ? 'ok' : 'no'}"><b>${ses}</b> · ${rk.ranking.length ? `Primer país provisional: ${esc(ov.names[rk.launch])}${rk.second ? ' · segundo: ' + esc(ov.names[rk.second]) : ''} (cambia si cambian los datos)` : 'No hay recomendación de país, PVP ni secuencia de lanzamiento: faltan datos con fuente y fecha (ver «Qué falta»).'}</div>${kpis()}${filters()}</article>`);
    h.push(discoveryPanel());
    h.push(`<article class="card c-violet"><h3>Ranking europeo multicriterio <small>pesos editables · NO EVALUABLE si faltan datos</small></h3>
      ${rk.ranking.length ? bars(rk.ranking.map((p) => ({ label: ov.names[p.country], v: p.score, text: p.score.toFixed(1), color: '#b968ff' })), { max: 100, label: 'Ranking' }) : '<p class="muted">Ningún país alcanza la cobertura mínima de datos verificados: no se ordena a nadie por intuición.</p>'}
      <div class="euscroll"><table class="tbl"><tr><th>País</th><th>Estado</th><th>Punt.</th><th>Cobertura</th><th>Atractivo</th><th>Viabilidad</th><th>Qué falta</th></tr>${[...rk.ranking, ...rk.pending].map((p) => `<tr><td>${esc(p.name)}</td><td><span class="tagst ${p.evaluable ? 't-ok' : 't-no'}">${p.evaluable ? 'EVALUABLE #' + p.rank : 'NO EVALUABLE'}</span></td><td>${p.score == null ? '—' : p.score.toFixed(1)}</td><td>${(p.coverage * 100).toFixed(0)} %</td><td>${p.attractiveness == null ? '—' : p.attractiveness.toFixed(1)}</td><td>${p.viability == null ? '—' : p.viability.toFixed(1)}</td><td>${esc((p.missing[0] || { motivo: '' }).motivo)}${p.missing.length > 1 ? ' (+' + (p.missing.length - 1) + ')' : ''}</td></tr>`).join('')}</table></div>
      ${rk.sensitivity ? `<p class="muted">Sensibilidad: el primer país se mantiene en ${(rk.sensitivity.stable_share * 100).toFixed(0)} % de ${rk.sensitivity.scenarios} variaciones de ±10 puntos. Presets → conservadora: ${esc(rk.presets.conservadora.top)} · crecimiento: ${esc(rk.presets.crecimiento.top)}.</p>` : ''}
      <details><summary>Pesos y fórmulas</summary><div class="euw">${Object.keys(ov.criteria).map((k) => `<label>${esc(ov.criteria[k].name)}<input type="number" min="0" max="100" data-w="${k}" value="${rk.weights[k]}" ${canEdit() ? '' : 'disabled'}></label>`).join('')}
      ${canEdit() ? '<button class="btn sm" id="euSaveW">Guardar pesos (suman 100)</button> <button class="btn ghost sm" data-preset="conservadora">Conservadora</button> <button class="btn ghost sm" data-preset="crecimiento">Crecimiento</button> <button class="btn ghost sm" data-preset="base">Base 30/30/20/15/5</button>' : ''}</div>
      ${Object.keys(ov.criteria).map((k) => `<p class="muted"><b>${esc(ov.criteria[k].name)}:</b> ${esc(ov.criteria[k].formula)}</p>`).join('')}</details>
      <div class="euexp"><a class="btn ghost sm" href="${q('/api/eu/export?what=ranking')}" download>CSV ranking</a></div></article>`);
    h.push(`<article class="card c-lime"><h3>Rentabilidad por país · ${esc(ov.names[E.country])} <small>escenarios de PVP · IVA del país</small></h3>
      ${ec ? `<div class="euscroll"><table class="tbl"><tr><th>PVP</th><th>Base sin IVA</th><th>Comisión</th><th>Contribución</th><th>Margen</th><th>ACoS eq.</th></tr>${ec.scenarios.map((s) => `<tr class="${s.pvp_gross === E.pvp ? 'sel' : ''}"><td>${s.pvp_gross == null ? NA : n2(s.pvp_gross)}</td><td>${s.net_price == null ? NA : n2(s.net_price)}</td><td>${s.referral_fee == null ? NA : n2(s.referral_fee)}</td><td>${s.complete ? n2(s.contribution_before_ads) : NA}</td><td>${s.complete ? pct(s.margin_before_ads) : NA}</td><td>${s.complete ? pct(s.breakeven_acos_ex_vat) : NA}</td></tr>`).join('')}</table></div>
      ${ec.scenarios[0].complete ? bars(ec.scenarios.map((s) => ({ label: s.pvp_gross.toFixed(2) + ' €', v: Math.max(0, s.margin_before_ads), text: pct(s.margin_before_ads), color: '#b6ff2e' })), { max: 0.6, label: 'Margen por PVP' }) : `<p class="muted">${esc(ec.scenarios[0].label || '')} ${(ec.scenarios[0].missing || []).length ? 'Faltan: ' + esc((ec.scenarios[0].missing || []).map((k) => ec.labels[k] || k).join(', ')) + '.' : ''} No se muestra margen (no se convierte en cero).</p>`}
      ${(ec.scenarios[Math.floor(ec.scenarios.length / 2)] || {}).complete ? `<p class="muted">${esc(ec.scenarios[Math.floor(ec.scenarios.length / 2)].label)}</p>` : ''}
      <details><summary>Supuestos y su estado (editables)</summary><div class="euscroll"><table class="tbl"><tr><th>Variable</th><th>Valor</th><th>Estado</th><th>Fuente</th>${canEdit() ? '<th>Editar</th>' : ''}</tr>${['vat', 'cogs', 'inbound', 'prep', 'fulfillment', 'storage', 'returns', 'promo', 'other'].map((k) => { const a = ec.assumptions[k]; return `<tr><td>${esc(ec.labels[k])}</td><td>${a.v == null ? NA : k === 'vat' ? pct(a.v) : n2(a.v)}</td><td>${chip(a.status)}</td><td class="muted">${esc(a.source || '').slice(0, 90)}</td>${canEdit() ? `<td><input data-av="${k}" type="number" min="0" step="0.01" style="width:70px"> <select data-as="${k}"><option>HIPOTESIS</option><option>DOCUMENTADO</option><option>VERIFICADO</option></select> <input data-ar="${k}" placeholder="fuente" style="width:110px"> <button class="btn sm" data-asave="${k}">OK</button></td>` : ''}</tr>`; }).join('')}
      <tr><td>Comisión Amazon</td><td>15 % (8 % ≤ 10 €, mín. 0,30 €)</td><td>${chip(ec.assumptions.referral.status)}</td><td class="muted">${esc(ec.assumptions.referral.source).slice(0, 120)}</td>${canEdit() ? '<td>—</td>' : ''}</tr></table></div>
      ${canEdit() ? '<button class="btn ghost sm" id="euHyp">Cargar hipótesis de ejemplo (etiquetadas HIPÓTESIS)</button> <span class="muted">solo rellena huecos; nunca pisa datos verificados</span>' : ''}</details>` : '<p class="muted">Sin datos.</p>'}
      <div class="euexp"><a class="btn ghost sm" href="${q('/api/eu/export?what=economics')}" download>CSV economía</a></div></article>`);
    const rows = bm ? bm.rows.filter((r) => (E.comp === 'all' || (r.comparability || r.comparability_suggested) === E.comp) && (E.evq === 'all' || r.evidence_quality === E.evq) && (!E.confirmedOnly || r.comparability_status === 'CONFIRMADA')) : [];
    h.push(`<article class="card c-cyan wide"><h3>Benchmarking de competidores · ${esc(ov.names[E.country])} <small>Keepa API · precios y BSR (señal indirecta, no ventas)</small></h3>
      <div class="eukp"><span class="tagst ${kst.can_call ? 't-ok' : 't-no'}">Keepa: ${kst.can_call ? 'HABILITADO' : kst.key_present ? 'DESACTIVADO (ENABLE=0)' : 'SIN CLAVE'}</span> <span class="muted">cobertura: ${Object.values(kst.supported).join(', ')} · sin cobertura: ${Object.values(kst.unsupported).join(', ')}</span>
        ${isAdmin() ? '<button class="btn ghost sm" id="kpTest">Probar conexión (saldo de tokens, gratis)</button> <a class="btn ghost sm" href="/api/keepa/export?fmt=csv" download>CSV caché</a> <a class="btn ghost sm" href="/api/keepa/export?fmt=json" download>JSON caché</a>' : ''}</div>
      <div id="kpOut" class="muted">${esc(E.msg)}</div>
      ${E.bench && !E.bench.keepa_supported ? `<p class="f warn">${esc(E.bench.note)}. Aporta datos por otra vía o el país seguirá NO EVALUABLE.</p>` : ''}
      ${bm ? `${bm.price_norm ? bars(rows.filter((r) => r.price_norm != null).slice(0, 12).map((r) => ({ label: (r.brand || r.asin).slice(0, 18), v: r.price_norm, text: r.price_norm.toFixed(1) + ' €/' + bm.norm_unit, color: ['CONFIRMADA', 'AUTOMATICA'].includes(r.comparability_status) && ['ALTA', 'MEDIA'].includes(r.comparability) ? '#18e6ff' : '#8ea6bd' })), { label: 'Precio normalizado' }) + `<p class="muted">Mediana ${n2(bm.price_norm.median)} · Q1 ${n2(bm.price_norm.q1)} · Q3 ${n2(bm.price_norm.q3)} · IQR ${n2(bm.price_norm.iqr)} · dispersión ${bm.price_norm.dispersion == null ? 'n/d' : bm.price_norm.dispersion} · más barato ${bm.cheapest ? esc(bm.cheapest.brand) + ' ' + n2(bm.cheapest.price_norm) : 'n/d'} · premium ${bm.premium ? esc(bm.premium.brand) + ' ' + n2(bm.premium.price_norm) : 'n/d'} (por ${esc(bm.norm_unit)})</p>` : '<p class="muted">Aún no hay comparables ALTA/MEDIA con formato conocido: no se calculan estadísticos.</p>'}
        <div class="euscroll"><table class="tbl"><tr><th>ASIN</th><th>Marca</th><th>Producto</th><th>Formato</th><th>Precio</th><th>€/${esc(bm.norm_unit)}</th><th>BSR · categoría · fecha</th><th>Tendencia</th><th>Val.</th><th>Reseñas</th><th>Fecha</th><th>Comparabilidad</th></tr>${rows.map((r) => `<tr><td><a href="${esc(r.url)}" target="_blank" rel="noopener noreferrer">${esc(r.asin)}</a></td><td>${esc(r.brand)}</td><td>${esc(r.title).slice(0, 56)}${r.injection_suspect ? ' <span class="tagst t-no">TEXTO SOSPECHOSO (dato, no instrucción)</span>' : ''}</td><td>${bm.norm_unit === '100 mL' ? (r.volume_ml == null ? NA : r.volume_ml + ' mL') : (r.units == null ? NA : r.units + ' uds')}</td><td>${r.price == null ? NA : n2(r.price) + ' ' + esc(r.currency)}</td><td>${r.price_norm == null ? NA : n2(r.price_norm)}</td><td>${r.bsr == null ? NA : r.bsr + ' · ' + esc((r.bsr_category || {}).name || 'categoría n/d') + ' · ' + esc(r.bsr_date || '')}</td><td>${trend(r.bsr_history, E.period)}</td><td>${r.rating == null ? NA : r.rating}</td><td>${r.reviews == null ? NA : r.reviews}</td><td class="muted">${esc((r.fetched_at || '').slice(0, 10))}</td>
        <td><span class="tagst ${r.comparability_status === 'CONFIRMADA' ? 't-ok' : r.comparability_status === 'AUTOMATICA' ? 't-wait' : 't-no'}">${esc(r.comparability_status)}</span> ${esc(r.comparability || r.comparability_suggested)}${r.comparability_score != null ? ' · ' + r.comparability_score : ''}${canEdit() ? `<br><select data-cmp="${esc(r.asin)}"><option value="">${r.comparability_status === 'CONFIRMADA' ? 'confirmada' : 'revisar → confirmar'}</option>${['ALTA', 'MEDIA', 'BAJA'].map((c) => `<option>${c}</option>`).join('')}</select>` : ''}</td></tr>`).join('')}</table></div>` : '<p class="muted">Sin consultas Keepa para este producto y país. Pulsa «ANALIZAR EUROPA».</p>'}
      <div class="euexp"><a class="btn ghost sm" href="${q('/api/eu/export?what=benchmark')}" download>CSV benchmark</a></div></article>`);
    const al = []; if (!kst.can_call) al.push('Keepa no está habilitado: no hay datos de mercado.'); const needs = rk.pending.reduce((n, p) => n + p.missing.length, 0); if (needs) al.push(needs + ' datos críticos faltan para decidir (ver ranking).'); (ov.completeness || []).length && al.push('Ficha incompleta: ' + ov.completeness.join(', ') + '.');
    h.push(`<article class="card c-amber"><h3>Alertas sustentadas <small>derivadas del estado del sistema, no de supuestos</small></h3>${al.map((a) => `<div class="al media">${esc(a)}</div>`).join('') || '<p class="muted">Sin alertas.</p>'}</article>
      <article class="card c-cyan"><h3>Noticias verificadas <small>Amazon · regulación · competencia</small></h3><p class="muted">Sin noticias verificadas. Solo se muestran noticias con fuente, URL y fecha confirmadas por un aprobador; no se inventan.</p></article>`);
    return h.join('');
  }

  function viewExpediente() {
    const ov = E.ov, p = ov.card || P(), comp = ov.compliance[E.country], cw = Object.values(ov.coworkers); const h = [];
    h.push(`<article class="card c-cyan wide"><h3>Expediente · ${esc(p.name)} <small>${esc(p.id)} · versión ${p.version}</small></h3><div class="euscroll"><table class="tbl"><tr><th>Dato</th><th>Valor</th></tr>
      <tr><td>Marca / categoría</td><td>${esc(p.brand)} · ${esc(p.category)} · ${esc(p.subcategory || '—')}</td></tr><tr><td>Formato</td><td>${p.format.content == null ? NA : esc(p.format.content) + ' ' + esc(p.format.unit) + ' ' + chip(p.format.status)} <span class="muted">${esc(p.format.source || '')}</span></td></tr>
      <tr><td>PVP</td><td>${Object.keys(p.pvp).length ? Object.keys(p.pvp).map((k) => esc(k) + ': ' + fv(p.pvp[k], '€') + ' <span class="muted">' + esc(p.pvp[k].source || '') + '</span>').join('<br>') : NA}</td></tr>
      <tr><td>Costes</td><td>${Object.keys(p.costs).length ? Object.keys(p.costs).map((k) => esc(k) + ': ' + fv(p.costs[k], '€') + ' <span class="muted">' + esc(p.costs[k].source || '') + ' · ' + esc(p.costs[k].date || '') + '</span>').join('<br>') : NA}</td></tr>
      <tr><td>Stock</td><td>${fv(p.stock, 'uds')} <span class="muted">${esc(p.stock.source || '')}</span></td></tr><tr><td>Estado regulatorio</td><td><span class="tagst ${p.regulatory.state === 'CONFORME_DOCUMENTADO' ? 't-ok' : 't-wait'}">${esc(p.regulatory.state)}</span> ${esc(p.regulatory.note || '')}</td></tr>
      <tr><td>Marketplaces activos / objetivo</td><td>${esc((p.marketplaces || []).join(', ') || 'ninguno')} / ${esc((p.target_markets || []).join(', '))}</td></tr><tr><td>ASIN propios</td><td>${Object.keys(p.own_asins || {}).map((k) => esc(k) + ': ' + esc(p.own_asins[k])).join(' · ') || NA}</td></tr>
      <tr><td>Documentos</td><td>${(p.documents || []).map((d) => esc(d.name) + ' <span class="muted">' + esc(d.ref || '') + ' ' + esc(d.date || '') + '</span>').join('<br>') || NA}</td></tr><tr><td>Imágenes</td><td>${(p.images || []).map((d) => esc(d.ref)).join(', ') || NA}</td></tr>
      <tr><td>Expedientes enlazados</td><td>${(p.dossiers || []).map((d) => esc(d.label || d.account) + ' (' + esc(d.account) + ')').join('<br>') || NA}</td></tr><tr><td>Notas</td><td class="muted">${esc(p.notes || '')}</td></tr></table></div></article>`);
    h.push(`<article class="card c-amber wide"><h3>Siete coworkers <small>estado real: ninguno se declara OPERATIVO sin datos verificados</small></h3><div class="eucw">${cw.map((c) => `<div class="cwc"><b>${esc(c.name)}</b> <span class="tagst ${stCls(c.state)}">${esc(c.state)}</span>
      <div class="muted">Última ejecución: ${esc(c.last_run || 'nunca')} · Fuente: ${esc(c.source)}</div><div>Datos: ${esc(c.data_used)}</div>${c.findings.map((x) => `<div>• ${esc(x)}</div>`).join('')}${c.blockers.length ? `<div class="bad">Bloqueos: ${esc(c.blockers.join(' · '))}</div>` : ''}<div class="muted">Próxima acción: ${esc(c.next_action)}</div><div class="muted">Expediente: ${esc(c.link.account)} / ${esc(c.link.product || c.link.record || '—')}</div></div>`).join('')}</div></article>`);
    h.push(`<article class="card c-violet wide"><h3>Cumplimiento regulatorio · ${esc(ov.names[E.country])} <small>checklist de ${esc(ov.category_checklist)} · no se declara cumplimiento sin documentación</small></h3>
      <label>País <select id="euCountry2">${Object.keys(ov.names).map((c) => `<option value="${c}" ${c === E.country ? 'selected' : ''}>${esc(ov.names[c])}</option>`).join('')}</select></label>
      ${ov.claims.length ? `<p class="f warn">Claims utilizables con respaldo suficiente: <b>${ov.usable_claims.length}</b>. No se modifica ninguna etiqueta ni fórmula.</p><div class="euscroll"><table class="tbl"><tr><th>Claim</th><th>Clasificación</th><th>Motivo</th><th>Evidencia pendiente</th></tr>${ov.claims.map((c) => `<tr><td>${esc(c.claim)}</td><td><span class="tagst ${c.state === 'CONFORME_DESCRIPTIVO' ? 't-ok' : c.state === 'PENDIENTE_EVIDENCIA' ? 't-wait' : 't-no'}">${esc(c.state)}</span></td><td>${esc(c.why)}</td><td>${esc(c.evidence)}</td></tr>`).join('')}</table></div>` : '<p class="f warn">Sin registro de claims para este producto: ningún claim es utilizable hasta registrar y respaldar cada uno.</p>'}
      <h4>Checklist</h4><div class="euscroll"><table class="tbl"><tr><th>Requisito</th><th>Referencia</th><th>Estado</th><th>Evidencia</th></tr>${ov.checklist.map((i) => { const c = comp[i.id]; return `<tr><td>${esc(i.text)}</td><td class="muted">${esc(i.ref)}</td><td>${canEdit() ? `<select data-ck="${i.id}">${['PENDIENTE', 'OK', 'NO_CUMPLE', 'NO_APLICA'].map((s) => `<option ${c.state === s ? 'selected' : ''}>${s}</option>`).join('')}</select>` : esc(c.state)}</td><td>${canEdit() ? `<input data-ce="${i.id}" value="${esc(c.evidence)}" placeholder="documento/fecha (obligatorio para OK)" style="width:100%">` : esc(c.evidence)}</td></tr>`; }).join('')}</table></div>
      ${(ov.product.discrepancies || []).length ? '<h4>Discrepancias detectadas</h4>' + ov.product.discrepancies.map((d) => `<p class="muted"><b>${esc(d.id)}</b> ${esc(d.text)} <i>→ ${esc(d.action)}</i></p>`).join('') : ''}</article>`);
    return h.join('');
  }

  function viewDirector() {
    const chat = E.chat[E.pid] || [];
    return `<article class="card c-pink wide"><h3>Director Amazon IA · ${esc(P().name)} <small>determinista por defecto · la IA solo redacta con tu consentimiento por consulta</small></h3>
      <div class="euchat" id="euChat">${(chat.length ? chat : [{ text: 'Pregúntame, por ejemplo: «¿En qué país europeo conviene lanzar este producto?», «¿Es competitivo un PVP de X €?» o «¿Qué datos faltan para decidir?». Respondo con cálculos deterministas, te digo qué falta y nunca inventaré cifras. No ejecuto cambios en Amazon.' }]).map((m) => `<div class="msg ${m.me ? 'me' : 'ai'}">${m.mode ? `<span class="mtag">${esc(m.mode)}</span>` : ''}${esc(m.text).replace(/\n/g, '<br>')}${m.meta ? `<div class="muted">${esc(m.meta)}</div>` : ''}</div>`).join('')}</div>
      <form id="euForm" class="euask"><input id="euQ" placeholder="Pregunta al Director…" maxlength="1000" style="flex:1"><label class="chk"><input id="euUseAi" type="checkbox" ${canEdit() ? '' : 'disabled'}> usar IA (pide confirmación)</label><button class="btn" ${E.busy ? 'disabled' : ''}>Preguntar</button></form>
      <div class="chips" id="euChips">${['¿En qué país europeo conviene lanzar este producto?', '¿Es competitivo un precio de 49,90 €?', '¿Qué datos faltan para decidir?', '¿Qué riesgos regulatorios tenemos?', '¿Cuáles son los competidores más peligrosos?'].map((x) => `<button type="button">${esc(x)}</button>`).join('')}</div></article>`;
  }

  // ------------------------------------------------------------------ ficha / versiones (crear, editar, archivar) --------------------------------------
  function formProduct(p, isNew) {
    const cats = E.cats.map((c) => `<option value="${esc(c.id)}" ${p.category === c.id ? 'selected' : ''}>${esc(c.name)}</option>`).join(''), st = (id, v) => `<select id="${id}">${E.meta.statuses.map((s) => `<option ${s === v ? 'selected' : ''}>${s}</option>`).join('')}</select>`;
    const fld = (k, lab, f, u) => `<tr><td>${lab}</td><td><input data-f="${k}.v" type="number" step="any" min="0" value="${f && f.v != null ? esc(f.v) : ''}" style="width:90px"> ${u || ''}</td><td>${st('fs_' + k, (f && f.status) || 'A_CONFIRMAR')}</td><td><input data-f="${k}.source" value="${esc((f && f.source) || '')}" placeholder="fuente" style="width:100%"></td><td><input data-f="${k}.date" type="date" value="${esc((f && f.date) || '')}"></td></tr>`;
    const pv = p.pvp || {}, cs = p.costs || {}, ctry = E.meta.countries;
    const costNames = [...new Set([...Object.keys(cs), 'cogs', 'inbound', 'prep', 'fulfillment'])];
    return `<article class="card c-lime wide"><h3>${isNew ? 'Nuevo producto' : 'Editar ficha · ' + esc(p.name)} <small>los datos documentados exigen fuente y fecha · nada se inventa</small></h3><div class="euform">
      <label>Nombre<input id="fName" value="${esc(p.name || '')}" maxlength="80"></label><label>Marca<input id="fBrand" value="${esc(p.brand || '')}" maxlength="60"></label><label>Categoría<select id="fCat">${cats}</select></label><label>Subcategoría<input id="fSub" value="${esc(p.subcategory || '')}" maxlength="80"></label><label>Versión/etiqueta<input id="fVer" value="${esc(p.version_label || '')}" maxlength="40"></label>
      <label>Contenido<input id="fFmt" type="number" min="0" step="any" value="${p.format && p.format.content != null ? esc(p.format.content) : ''}"></label><label>Unidad<select id="fUnit">${['ml', 'g', 'unidades'].map((u) => `<option ${p.format && p.format.unit === u ? 'selected' : ''}>${u}</option>`).join('')}</select></label><label>Fuente del formato<input id="fFmtSrc" value="${esc((p.format && p.format.source) || '')}"></label><label>Estado del formato${st('fFmtSt', (p.format && p.format.status) || 'A_CONFIRMAR')}</label></div>
      <h4>PVP con IVA (REF = referencia general)</h4><div class="euscroll"><table class="tbl"><tr><th>Mercado</th><th>€</th><th>Estado</th><th>Fuente</th><th>Fecha</th></tr>${['REF', ...ctry].map((k) => fld('pvp.' + k, k, pv[k], '€')).join('')}</table></div>
      <h4>Costes unitarios sin IVA (cogs, inbound, prep, fulfillment… ampliable con otro nombre)</h4><div class="euscroll"><table class="tbl"><tr><th>Concepto</th><th>€</th><th>Estado</th><th>Fuente</th><th>Fecha</th></tr>${costNames.map((k) => fld('costs.' + k, k, cs[k], '€')).join('')}<tr><td><input id="fNewCost" placeholder="nuevo concepto (minúsculas_y_guion_bajo)"></td><td colspan="4"><span class="muted">se guarda al escribir su valor en la fila «nuevo»:</span> <input id="fNewCostV" type="number" step="any" min="0" style="width:90px"> ${st('fNewCostSt', 'A_CONFIRMAR')} <input id="fNewCostSrc" placeholder="fuente"> <input id="fNewCostD" type="date"></td></tr></table></div>
      <h4>Stock verificado</h4><div class="euscroll"><table class="tbl"><tr><th>Dato</th><th>Uds</th><th>Estado</th><th>Fuente</th><th>Fecha</th></tr>${fld('stock', 'Stock', p.stock, 'uds')}</table></div>
      <div class="euform"><label>Estado regulatorio<select id="fReg">${E.meta.reg_states.map((s) => `<option ${p.regulatory && p.regulatory.state === s ? 'selected' : ''}>${s}</option>`).join('')}</select></label><label>Nota regulatoria<input id="fRegN" value="${esc((p.regulatory && p.regulatory.note) || '')}"></label>
      <label>Marketplaces activos (códigos)<input id="fMk" value="${esc((p.marketplaces || []).join(','))}" placeholder="ES,DE"></label><label>Mercados objetivo<input id="fTg" value="${esc((p.target_markets || ['DE', 'FR', 'IT', 'ES']).join(','))}"></label>
      <label>ASIN propios (PAÍS:ASIN, …)<input id="fOwn" value="${esc(Object.keys(p.own_asins || {}).map((k) => k + ':' + p.own_asins[k]).join(', '))}" placeholder="ES:B0XXXXXXXX"></label><label>Atributos/ingredientes (coma)<input id="fAttr" value="${esc((p.attributes || []).join(', '))}"></label>
      <label>Competidores de referencia (coma; solo pistas)<input id="fRef" value="${esc((p.reference_competitors || []).join(', '))}"></label><label>Notas<input id="fNotes" value="${esc(p.notes || '')}" maxlength="600"></label></div>
      <h4>Términos de búsqueda por idioma (uno por línea; vacío = se usa la biblioteca genérica si existe)</h4><div class="euform">${['ES', 'DE', 'FR', 'IT'].map((l) => `<label>${l}<textarea id="fTerms${l}" rows="3">${esc(((p.search_terms || {})[l] || []).join('\n'))}</textarea></label>`).join('')}</div>
      <h4>Documentos e imágenes (una línea por elemento: nombre | referencia | AAAA-MM-DD)</h4><div class="euform"><label>Documentos<textarea id="fDocs" rows="3">${esc((p.documents || []).map((d) => [d.name, d.ref || '', d.date || ''].join(' | ')).join('\n'))}</textarea></label><label>Imágenes (referencia | nota)<textarea id="fImgs" rows="3">${esc((p.images || []).map((d) => [d.ref, d.note || ''].join(' | ')).join('\n'))}</textarea></label></div>
      <div class="eufil"><label>Motivo del cambio<input id="fNote" placeholder="qué cambia"></label><button class="btn" id="fSave">${isNew ? 'Crear producto' : 'Guardar (nueva versión)'}</button><button class="btn no sm" id="fCancel">Cancelar</button><span class="muted" id="fMsg"></span></div></article>`;
  }

  function viewFicha() {
    const p = P(), h = [];
    if (E.edit) return formProduct(E.edit.product, E.edit.isNew);
    h.push(`<article class="card c-lime wide"><h3>Ficha · ${esc(p.name)} <small>${esc(p.id)} · versión ${p.version}${p.archived ? ' · ARCHIVADO' : ''}</small></h3>
      <div class="eufil">${canEdit() ? `<button class="btn" id="fEdit" ${p.archived ? 'disabled' : ''}>Editar ficha</button><button class="btn ${p.archived ? '' : 'no'} sm" id="fArch">${p.archived ? 'Restaurar' : 'Archivar'}</button>` : '<span class="muted">Solo aprobador/administrador editan fichas.</span>'}</div>
      <p class="muted">Falta en la ficha: ${esc((p.missing || []).join(', ') || 'nada obligatorio')}</p>
      <h4>Historial de versiones (auditado)</h4><div class="euscroll"><table class="tbl"><tr><th>Versión</th><th>Fecha</th><th>Usuario</th><th>Cambio</th></tr>${(p.changelog || []).slice().reverse().map((c) => `<tr><td>${c.version}</td><td>${esc(c.at)}</td><td>${esc(c.by)}</td><td>${esc(c.note)}</td></tr>`).join('')}</table></div>
      <p class="muted">Instantáneas inmutables de versiones anteriores: ${E.versions.length} (v${E.versions.map((v) => v.version).join(', v') || '—'}).</p></article>`);
    return h.join('');
  }

  function parseForm() {
    const num = (v) => (v === '' || v == null ? null : Number(v)), val = (id) => ($('#' + id) || {}).value, lines = (id) => (val(id) || '').split('\n').map((x) => x.trim()).filter(Boolean);
    const field = (k) => ({ v: num(($(`[data-f="${k}.v"]`) || {}).value), status: val('fs_' + k), source: ($(`[data-f="${k}.source"]`) || {}).value, date: ($(`[data-f="${k}.date"]`) || {}).value || null });
    const pvp = {}, costs = {}; $$('[data-f^="pvp."][data-f$=".v"]').forEach((i) => { const k = i.dataset.f.slice(0, -2); const f = field(k); if (f.v != null) pvp[k.slice(4)] = f; });
    $$('[data-f^="costs."][data-f$=".v"]').forEach((i) => { const k = i.dataset.f.slice(0, -2); const f = field(k); if (f.v != null) costs[k.slice(6)] = f; });
    const nc = (val('fNewCost') || '').trim(), ncv = num(val('fNewCostV')); if (nc && ncv != null) costs[nc] = { v: ncv, status: val('fNewCostSt'), source: val('fNewCostSrc'), date: val('fNewCostD') || null };
    const own = {}; (val('fOwn') || '').split(',').map((x) => x.trim()).filter(Boolean).forEach((x) => { const [c, a] = x.split(':'); if (c && a) own[c.trim().toUpperCase()] = a.trim().toUpperCase(); });
    const csv = (id) => (val(id) || '').split(',').map((x) => x.trim()).filter(Boolean), terms = {}; ['ES', 'DE', 'FR', 'IT'].forEach((l) => { const t = lines('fTerms' + l); if (t.length) terms[l] = t; });
    return { name: val('fName'), brand: val('fBrand'), category: val('fCat'), subcategory: val('fSub'), version_label: val('fVer'), notes: val('fNotes'),
      format: { content: num(val('fFmt')), unit: val('fUnit'), status: val('fFmtSt'), source: val('fFmtSrc') }, pvp, costs, stock: field('stock'), regulatory: { state: val('fReg'), note: val('fRegN') },
      marketplaces: csv('fMk').map((x) => x.toUpperCase()), target_markets: csv('fTg').map((x) => x.toUpperCase()), own_asins: own, attributes: csv('fAttr'), reference_competitors: csv('fRef'), search_terms: terms,
      documents: lines('fDocs').map((l) => { const [name, ref, date] = l.split('|').map((x) => x.trim()); return { name, ref: ref || '', date: date || '' }; }), images: lines('fImgs').map((l) => { const [ref, note] = l.split('|').map((x) => x.trim()); return { ref, note: note || '' }; }) };
  }

  // ------------------------------------------------------------------ render ------------------------------------------------------------------------
  function render() {
    const el = $('#euRoot'); if (!el) return; let h = nav();
    if (E.edit && E.edit.isNew) h += formProduct(E.edit.product, true);
    else if (E.pid && E.denied) h += `<article class="card c-amber wide"><p class="muted">${esc(E.denied)} — tu usuario necesita acceso a la cuenta de este producto.</p></article>` + header() + (E.view === 'ficha' ? viewFicha() : '');
    else if (E.pid && E.ov) h += header() + (E.view === 'europa' ? viewEuropa() : E.view === 'expediente' ? viewExpediente() : E.view === 'director' ? viewDirector() : viewFicha());
    else h += '<article class="card c-cyan wide"><p class="muted">Selecciona un producto para cargar su inteligencia de mercado europea.</p></article>';
    el.innerHTML = h; bind();
  }

  function bind() {
    const rerender = async () => { await Promise.all([loadEcon(), loadBench()]); render(); };
    $$('[data-cat]').forEach((b) => (b.onclick = () => { E.cat = b.dataset.cat; E.pid = null; E.ov = null; render(); }));
    $$('[data-pid]').forEach((b) => (b.onclick = async () => { E.pid = b.dataset.pid; E.view = 'europa'; E.versions = []; await loadVersions(); await loadProduct(); }));
    $('#euArch') && ($('#euArch').onchange = (e) => { E.archived = e.target.checked; load(); });
    $('#euNewProd') && ($('#euNewProd').onclick = () => { E.edit = { isNew: true, product: { category: E.cat, format: { unit: (E.cats.find((c) => c.id === E.cat) || {}).normalization === 'unit' ? 'unidades' : 'ml' }, target_markets: ['DE', 'FR', 'IT', 'ES'] } }; render(); });
    $('#euNewCat') && ($('#euNewCat').onclick = async () => { const name = prompt('Nombre de la nueva categoría'); if (!name) return; const unit = confirm('¿Se compara por UNIDADES (cápsulas, piezas)? Aceptar = unidades · Cancelar = mililitros') ? 'unit' : 'ml'; const r = await api('POST', '/api/catalog/category', { name, normalization: unit, checklist: 'GENERICA', subcategories: [] }); if (!r.ok) alert(r.j.error || 'Error'); else { E.cat = r.j.category.id; load(); } });
    $$('[data-view]').forEach((b) => (b.onclick = async () => { E.view = b.dataset.view; E.edit = null; if (E.view === 'ficha') await loadVersions(); render(); }));
    $('#euAnalyze') && ($('#euAnalyze').onclick = async () => { E.view = 'europa'; E.run = null; const r = await api('GET', q('/api/discovery/plan')); E.plan = r.ok ? r.j : null; E.msg = r.ok ? '' : r.j.error; render(); const d = $('#euDisc'); d && d.scrollIntoView({ block: 'start' }); });
    $('#dsNo') && ($('#dsNo').onclick = () => { E.plan = null; render(); });
    const replan = async () => { const r = await api('GET', q(`/api/discovery/plan?depth=${$('#dsDepth').value}&max=${$('#dsMax').value}`)); if (r.ok) { E.plan = r.j; render(); } };
    $('#dsRe') && ($('#dsRe').onclick = replan);
    $('#dsGo') && ($('#dsGo').onclick = async () => { const tok = parseInt($('#dsTok').value, 10) || 0; if (!confirm(`Vas a autorizar el consumo de hasta ${tok} tokens de Keepa para analizar ${P().name}.\n\n¿Autorizas la consulta?`)) return; E.running = true; render(); const r = await api('POST', '/api/discovery/run', { product: E.pid, depth: $('#dsDepth') ? $('#dsDepth').value : 'normal', max: parseInt(($('#dsMax') || {}).value || 20, 10), approved_tokens: tok }); E.running = false; E.run = r.j; E.plan = null; await loadProduct(); E.run = r.j; render(); });
    $('#dsMan') && ($('#dsMan').onclick = async () => { const a = ($('#dsAsins').value.toUpperCase().match(/[A-Z0-9]{10}/g) || []); if (!a.length) return; const r = await api('POST', '/api/discovery/manual', { product: E.pid, country: E.country, asins: a }); E.msg = r.ok ? `Registrados ${r.j.registered} · consultados ${(r.j.fetch || {}).fetched || 0} · pendientes ${(r.j.fetch || {}).pending || 0}` : r.j.error; await rerender(); });
    $('#euCountry') && ($('#euCountry').onchange = async (e) => { E.country = e.target.value; await rerender(); }); $('#euCountry2') && ($('#euCountry2').onchange = async (e) => { E.country = e.target.value; await rerender(); });
    $('#euPvp') && ($('#euPvp').onchange = async (e) => { E.pvp = parseFloat(e.target.value); await rerender(); });
    $('#euPvpC') && ($('#euPvpC').onchange = async (e) => { const v = parseFloat(e.target.value); if (v > 0) { E.pvp = v; await rerender(); } });
    $('#euPeriod') && ($('#euPeriod').onchange = (e) => { E.period = e.target.value === 'all' ? 'all' : parseInt(e.target.value, 10); render(); });
    $('#euComp') && ($('#euComp').onchange = (e) => { E.comp = e.target.value; render(); }); $('#euEvq') && ($('#euEvq').onchange = (e) => { E.evq = e.target.value; render(); }); $('#euConf') && ($('#euConf').onchange = (e) => { E.confirmedOnly = e.target.checked; render(); });
    const saveW = async (w) => { const r = await api('POST', '/api/eu/settings', { product: E.pid, weights: w }); if (!r.ok) alert(r.j.error || 'Error'); await loadProduct(); };
    $('#euSaveW') && ($('#euSaveW').onclick = () => { const w = {}; $$('[data-w]').forEach((i) => (w[i.dataset.w] = parseFloat(i.value) || 0)); saveW(w); }); $$('[data-preset]').forEach((b) => (b.onclick = () => saveW(E.ov.presets[b.dataset.preset])));
    $$('[data-asave]').forEach((b) => (b.onclick = async () => { const k = b.dataset.asave; const v = parseFloat($(`[data-av="${k}"]`).value); const r = await api('POST', '/api/eu/assumption', { product: E.pid, country: E.country, field: k, value: isNaN(v) ? null : (k === 'vat' ? v / 100 : v), status: $(`[data-as="${k}"]`).value, source: $(`[data-ar="${k}"]`).value }); if (!r.ok) alert(r.j.error || 'Error'); await loadProduct(); }));
    $('#euHyp') && ($('#euHyp').onclick = async () => { await api('POST', '/api/eu/hypotheses', { product: E.pid, countries: [E.country] }); await loadProduct(); });
    $$('[data-cmp]').forEach((s) => (s.onchange = async () => { if (!s.value) return; const r = await api('POST', '/api/eu/competitor', { product: E.pid, country: E.country, asin: s.dataset.cmp, comparability: s.value }); if (!r.ok) alert(r.j.error || 'Error'); await loadProduct(); }));
    const ck = async (id) => { const r = await api('POST', '/api/eu/compliance', { product: E.pid, country: E.country, item: id, state: $(`[data-ck="${id}"]`).value, evidence: $(`[data-ce="${id}"]`).value }); if (!r.ok) alert(r.j.error || 'Error'); await loadProduct(); E.view = 'expediente'; render(); };
    $$('[data-ck]').forEach((s) => (s.onchange = () => ck(s.dataset.ck))); $$('[data-ce]').forEach((s) => (s.onchange = () => ck(s.dataset.ce)));
    $('#kpTest') && ($('#kpTest').onclick = async () => { const r = await api('POST', '/api/keepa/test', {}); E.msg = r.j.ok ? `Conexión correcta · tokens: ${r.j.tokens_left} · recarga ${r.j.refill_rate_per_min}/min · ${r.j.checked_at}` : (r.j.explanation || r.j.error || 'Error'); const o = $('#kpOut'); if (o) o.textContent = E.msg; });
    $('#euForm') && ($('#euForm').onsubmit = (e) => { e.preventDefault(); const t = $('#euQ').value.trim(); if (t) ask(t); }); $$('#euChips button').forEach((b) => (b.onclick = () => ask(b.textContent)));
    $('#fEdit') && ($('#fEdit').onclick = () => { E.edit = { isNew: false, product: JSON.parse(JSON.stringify(P())) }; render(); });
    $('#fArch') && ($('#fArch').onclick = async () => { const p = P(); if (!p.archived && !confirm('¿Archivar ' + p.name + '? Dejará de aparecer en el listado (se conserva todo el historial).')) return; const r = await api('POST', '/api/catalog/archive', { id: p.id, archived: !p.archived }); if (!r.ok) return alert(r.j.error || 'Error'); await load(); });
    $('#fCancel') && ($('#fCancel').onclick = () => { E.edit = null; render(); });
    $('#fSave') && ($('#fSave').onclick = async () => {
      const body = parseForm(), isNew = E.edit.isNew; const r = isNew ? await api('POST', '/api/catalog/product', body) : await api('POST', '/api/catalog/update', { id: E.pid, patch: body, note: $('#fNote').value });
      if (!r.ok) { $('#fMsg').textContent = r.j.error || 'Error'; return; } E.edit = null; E.cat = r.j.product.category; E.pid = r.j.product.id; E.view = 'ficha'; E.archived = E.archived; const l = await api('GET', '/api/catalog' + (E.archived ? '?archived=1' : '')); E.cats = l.j.categories; E.prods = l.j.products; E.meta = l.j; await loadVersions(); await loadProduct();
    });
  }

  function consentDialog(r) {
    return new Promise((res) => {
      const p = r.preview, cur = esc(p.currency || 'USD'), o = document.createElement('div'); o.className = 'confirm-ov'; o.setAttribute('role', 'dialog'); o.setAttribute('aria-modal', 'true');
      o.innerHTML = `<div class="confirm-box"><h3>Consentimiento para enviar datos REALES a la IA</h3><p>${esc(r.explanation)}</p><ul><li>Proveedor: <b>${esc(p.provider)}</b> · modelo <b>${esc(p.model)}</b></li><li>Finalidad: ${esc(p.purpose)}</li><li>Coste máximo posible: <b>≈ ${p.estimated_worst_case == null ? 'no calculado' : p.estimated_worst_case.toFixed(5)} ${cur}</b> (tope por consulta ${p.max_cost_per_run}; presupuesto mensual ${p.monthly_budget}; disponible ${p.budget_remaining == null ? 'n/d' : p.budget_remaining.toFixed(4)} ${cur})</li><li>${esc(p.data_sent)}</li></ul><details><summary>Ver el texto exacto que se enviaría</summary><pre style="white-space:pre-wrap;max-height:220px;overflow:auto">${esc(p.user)}</pre></details><div class="confirm-btns"><button id="cfNo">Cancelar (no se envía nada)</button><button id="cfYes" class="primary">Consiento y enviar</button></div></div>`;
      document.body.appendChild(o); const done = (v) => { o.remove(); res(v); }; $('#cfNo', o).onclick = () => done(false); $('#cfYes', o).onclick = () => done(true); $('#cfNo', o).focus();
    });
  }
  async function ask(text) {
    if (E.busy) return; const useAi = $('#euUseAi') && $('#euUseAi').checked, pid = E.pid; E.busy = true; (E.chat[pid] = E.chat[pid] || []).push({ me: true, text }); render(); if ($('#euUseAi')) $('#euUseAi').checked = !!useAi;
    let r = await api('POST', '/api/eu/director', { product: pid, question: text, use_ai: !!useAi }); let j = r.j;
    if (j.needs_confirmation) { if (!(await consentDialog(j))) { E.chat[pid].push({ text: 'Cancelado: no se ha enviado nada a la IA. Respuesta determinista:\n' + j.answer, mode: 'SIN IA' }); E.busy = false; return render(); }
      r = await api('POST', '/api/eu/director', { product: pid, question: text, use_ai: true, confirm: { accepted: true, model: j.preview.model, data_hash: j.data_hash } }); j = r.j; }
    const s = j.ai_summary; E.chat[pid].push({ text: j.answer || j.error || 'Error', mode: j.ai && j.ai.mode === 'REAL' ? 'IA REAL' : 'SIN IA', meta: (j.ai && j.ai.reason_text ? j.ai.reason_text + ' ' : '') + (s ? `Modelo ${s.model} · ${s.tokens_in}/${s.tokens_out} tokens · ${s.duration_ms} ms · coste estimado ${s.cost_estimate} ${s.currency}${s.origin_verified ? ' · procedencia OpenAI verificada' : ''}` : '') + (j.facts ? ` · ${j.facts.length} hechos de apoyo` : '') });
    E.busy = false; render(); const c = $('#euChat'); if (c) c.scrollTop = 1e6;
  }
  root.EU = { load, state: E };
  document.addEventListener('click', (e) => { const b = e.target.closest('#tabs button'); if (b && b.dataset.tab === 'europa') load(); });
})(self);
