/* AHT Executive Neon · Amazon Pro Intelligence V0.6.0 — cinco espacios: INICIO · LANZAMIENTOS · MIS VENTAS · PRODUCTOS · DIRECTOR IA.
   Todo viene del servidor. Lo ausente se muestra SIN DATOS / NO DETERMINABLE / PENDIENTE DE CONEXIÓN (nunca ceros simulados). DEMO = datos sintéticos, separado y rotulado.
   Sin manejadores inline (CSP): delegación de eventos con data-act. */
(function (root) {
  const $ = (s, r) => (r || document).querySelector(s), $$ = (s, r) => [...(r || document).querySelectorAll(s)];
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const api = (m, p, b) => root.V03.api(m, p, b);
  const S6 = { pid: '', home: null, demo: false, prods: [], cats: [], launch: null, decs: [], tasks: null, opsd: null, imports: null, conn: null, econ: null, msg: '', edit: null, user: null };
  const ST = (s) => `<span class="tagst ${/SIN DATOS|NO DETERMINABLE|NO CALCULABLE|NO EVALUABLE|BLOQ|FALLIDA|RIESGO|ALTO/.test(s) ? 't-no' : /PENDIENTE|PARCIAL|BORRADOR|ESPERA|HIPOTESIS|ESTIMADO|DEMO|A_CONFIRMAR|MEDIO|REVISAR|SEPARADO/.test(s) ? 't-wait' : 't-ok'}">${esc(s)}</span>`;
  const eur = (x) => (x == null || isNaN(x) ? 'NO DISPONIBLE' : Number(x).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €');
  const pct = (x) => (x == null ? 'NO DETERMINABLE' : (x * 100).toFixed(1) + ' %');
  const canEdit = () => ['admin', 'approver'].includes(root.V03.V.role), isAdmin = () => root.V03.V.role === 'admin';
  const loggedIn = () => !!(root.V03 && root.V03.V && root.V03.V.user);
  const root$ = (id) => $('#' + id);
  const empty = (msg) => `<article class="card c-amber wide"><p class="muted">${esc(msg)}</p></article>`;

  async function loadBase() {
    const [c, d] = await Promise.all([api('GET', '/api/catalog'), api('GET', '/api/v06/decisions')]);
    S6.prods = c.ok ? c.j.products : []; S6.cats = c.ok ? c.j.categories : []; S6.decs = d.ok ? d.j.decisions : [];
    if (S6.pid && !S6.prods.find((p) => p.id === S6.pid)) S6.pid = '';
  }
  const prodSel = (all) => `<label>Producto <select id="v6Prod-${S6.space}" data-v6prod>${all ? '<option value="">Todos los productos</option>' : ''}${S6.prods.map((p) => `<option value="${esc(p.id)}" ${p.id === S6.pid ? 'selected' : ''}>${esc(p.name)}</option>`).join('')}</select></label>`;
  const pName = (id) => (S6.prods.find((p) => p.id === id) || {}).name || id;

  // ======================================================================================= INICIO
  function chartCard(c, color) {
    const foot = `<div class="v6foot"><span>Fuente: ${esc(c.source)}</span><span>Periodo: ${esc(c.period)}</span><span>Actualizado: ${esc(c.updated || '—')}</span><span>${ST(c.state)}</span></div>`;
    const head = `<h3>${esc(TITLES[c.id])} <small>${esc(c.question)}</small></h3>`;
    if (!c.series.length) return `<article class="card ${color} v6chart">${head}<div class="v6empty"><b>${esc(c.state)}</b><p>${esc(c.why || '')}</p></div>${foot}</article>`;
    return `<article class="card ${color} v6chart">${head}<div class="chart" id="ch-${c.id}"></div><div class="lg">${LEG[c.id] || ''}</div>${foot}</article>`;
  }
  const TITLES = { ventas: 'Ventas y rentabilidad', competencia: 'Competencia y precios', publicidad: 'Publicidad y retorno', posicionamiento: 'Posicionamiento' };
  const LEG = { ventas: '<i style="background:#18e6ff"></i>Ventas importadas (€)', publicidad: '<i style="background:#ff4fd8"></i>Gasto <i style="background:#18e6ff"></i>Ventas ads', competencia: '<i style="background:#ffb02e"></i>Mediana de la competencia (por 100 mL/100 uds)' };
  function drawCharts(h) {
    if (!root.Charts) return;
    h.charts.forEach((c) => {
      const el = $('#ch-' + c.id); if (!el || !c.series.length) return;
      if (c.id === 'ventas') root.Charts.line(el, { labels: c.series.map((x) => x.date.slice(5)), series: [{ name: 'Ventas', color: '#18e6ff', values: c.series.map((x) => x.sales), area: true, fmt: (v) => v.toFixed(2) + ' €' }] });
      if (c.id === 'publicidad') root.Charts.line(el, { labels: c.series.map((x) => x.date.slice(5)), series: [{ name: 'Gasto', color: '#ff4fd8', values: c.series.map((x) => x.spend), fmt: (v) => v.toFixed(2) + ' €' }, { name: 'Ventas ads', color: '#18e6ff', values: c.series.map((x) => x.sales), fmt: (v) => v.toFixed(2) + ' €' }] });
      if (c.id === 'competencia') root.Charts.bars(el, { labels: c.series.map((x) => x.country), series: [{ name: 'Mediana competencia', color: '#ffb02e', values: c.series.map((x) => x.median), fmt: (v) => v.toFixed(2) + ' €' }].concat(c.own_price_norm ? [{ name: 'Tu precio', color: '#18e6ff', values: c.series.map(() => c.own_price_norm), fmt: (v) => v.toFixed(2) + ' €' }] : []) });
    });
  }
  function demoCharts(d) {
    const mk = (id, color, body) => `<article class="card ${color} v6chart"><h3>${TITLES[id]} <small>${esc(CHQ[id])}</small></h3>${body}<div class="v6foot"><span>Fuente: SINTÉTICA</span><span>Periodo: 30 días ficticios</span><span>${ST('DEMO · SINTÉTICO')}</span></div></article>`;
    return mk('ventas', 'c-cyan', '<div class="chart" id="dm-ventas"></div>') + mk('competencia', 'c-amber', '<div class="chart" id="dm-comp"></div>') + mk('publicidad', 'c-violet', '<div class="chart" id="dm-ads"></div>') + mk('posicionamiento', 'c-lime', '<div class="chart" id="dm-bsr"></div>');
  }
  const CHQ = { ventas: '¿Cuánto vendo y cuánto gano?', competencia: '¿Cómo estoy de precio frente a la competencia?', publicidad: '¿Qué retorno me da la publicidad?', posicionamiento: '¿Dónde estoy posicionado?' };
  function drawDemo(d) {
    const L = d.days.map((x) => x.slice(5));
    root.Charts.line($('#dm-ventas'), { labels: L, series: [{ name: 'Ventas', color: '#18e6ff', values: d.sales, area: true, fmt: (v) => v.toFixed(0) + ' €' }, { name: 'Margen', color: '#b968ff', values: d.margin, fmt: (v) => v.toFixed(0) + ' €' }] });
    root.Charts.bars($('#dm-comp'), { labels: ['Propio'].concat(d.comp.map((x) => x[0])), series: [{ name: 'Precio €', color: '#ffb02e', values: [d.own_price].concat(d.comp.map((x) => x[1])), fmt: (v) => v.toFixed(2) + ' €' }] });
    root.Charts.line($('#dm-ads'), { labels: L, series: [{ name: 'Gasto', color: '#ff4fd8', values: d.spend, fmt: (v) => v.toFixed(0) + ' €' }, { name: 'Ventas ads', color: '#18e6ff', values: d.ads_sales, fmt: (v) => v.toFixed(0) + ' €' }] });
    root.Charts.line($('#dm-bsr'), { labels: L, series: [{ name: 'BSR', color: '#b6ff2e', values: d.bsr, fmt: (v) => String(Math.round(v)) }], zero: false });
  }
  function kpiCards(ks) {
    const col = ['c-cyan', 'c-lime', 'c-violet', 'c-amber'];
    return ks.map((k, i) => `<article class="card kpi ${col[i % 4]}"><span class="l">${esc(k.label)}</span><div class="v ${typeof k.value === 'string' && /SIN DATOS|NO DETERMINABLE/.test(k.value) ? 'v6na' : ''}">${typeof k.value === 'number' && k.unit ? eur(k.value) : (k.id === 'ads' && typeof k.value === 'number' ? pct(k.value) : esc(k.value))}</div><span class="d">${esc(k.hint || '')}</span><span class="tg">${esc(k.state)}</span></article>`).join('');
  }
  function decisionCard(d) {
    return `<div class="v6dec"><b>${esc(d.title)}</b>${ST(d.level)}<ul>${d.items.map((i) => `<li>${esc(i.decision_de_negocio || i.motivo || JSON.stringify(i)).slice(0, 200)}${i.motivo && i.decision_de_negocio ? '<br><small>' + esc(i.motivo).slice(0, 120) + '</small>' : ''}</li>`).join('')}</ul>${canEdit() ? `<button class="btn" data-act="decide" data-id="${d.id}" data-ok="1">APROBAR</button> <button class="btn no" data-act="decide" data-id="${d.id}" data-ok="0">RECHAZAR</button>` : '<span class="muted">Solo un aprobador puede decidir.</span>'}</div>`;
  }
  async function viewInicio(el) {
    if (S6.demo) {
      const d = (await api('GET', '/api/v06/demo')).j;
      el.innerHTML = `<div class="v6demo">${esc(d.banner)} <button class="btn ghost" data-act="demo-off">Salir de DEMO</button></div><div class="layout"><div class="left"><section class="kpis v6k">${kpiCards([{ label: 'Ventas netas', value: d.kpis.ventas, unit: '€', state: 'DEMO' }, { label: 'Margen', value: d.kpis.margen, unit: '€', state: 'DEMO' }, { label: 'ACoS', value: d.kpis.acos, id: 'ads', state: 'DEMO' }, { label: 'TACoS', value: d.kpis.tacos, id: 'ads', state: 'DEMO' }])}</section><section class="v6charts v6isdemo">${demoCharts(d)}</section></div><aside class="right">${directorCard()}</aside></div>`;
      drawDemo(d); return;
    }
    const r = await api('GET', '/api/v06/home' + (S6.pid ? '?product=' + encodeURIComponent(S6.pid) : '')); if (!r.ok) return (el.innerHTML = empty(r.j.error || 'Sin acceso'));
    const h = S6.home = r.j;     const cols = ['c-cyan', 'c-amber', 'c-violet', 'c-lime'];
    el.innerHTML = `<section class="filters neon-v">${prodSel(true)}<span class="v6mode">${ST(h.mode)} <small class="muted">${h.mode === 'PRELANZAMIENTO' ? 'sin ventas reales todavía: se muestra la preparación' : 'datos de informes de Amazon importados'}</small></span><span class="grow"></span><button class="btn ghost" data-act="demo-on">Ver DEMO (datos sintéticos)</button></section>
      <div class="layout"><div class="left"><section class="kpis v6k">${kpiCards(h.kpis)}</section><section class="v6charts">${h.charts.map((c, i) => chartCard(c, cols[i])).join('')}</section>
      <section class="v6two"><article class="card c-pink"><h3>Trabajo automático en curso <small>tareas del Director</small></h3>${h.work.length ? `<table class="tbl"><tr><th>Tarea</th><th>Estado</th><th>Por qué ahora</th></tr>${h.work.map((t) => `<tr><td>${esc(t.kind)}<br><small class="muted">${esc(t.decision_label)}</small></td><td>${ST(t.state)}</td><td><small>${esc(t.priority_why)}</small></td></tr>`).join('')}</table>` : '<p class="muted">Sin tareas en curso. Pulsa «Preparar lanzamiento» en LANZAMIENTOS para que el Director empiece.</p>'}</article>
      <article class="card c-amber"><h3>Productos en riesgo <small>reglas sobre la ficha</small></h3>${h.risks.length ? h.risks.map((x) => `<div class="f warn"><b>${esc(x.name)}</b> ${ST(x.level)} — ${esc(x.risk)}<br><small class="muted">${esc(x.why)}</small></div>`).join('') : '<p class="muted">Sin riesgos detectados con las reglas actuales.</p>'}</article></section></div>
      <aside class="right">${directorCard()}</aside></div>`;
    drawCharts(h);
  }
  function directorCard() {
    const pend = S6.decs;
    return `<article class="card c-cyan director v6dir"><h3>Director Amazon IA <small>un orquestador · 7 especialidades como herramientas</small></h3>
      <p class="muted">Ordena y el Director ejecuta lo permitido (N1), te pide solo lo crítico (N3) y bloquea lo inseguro (N4).</p>
      ${canEdit() ? `<div class="euchips"><button class="euchip" data-act="order" ${S6.pid ? '' : 'disabled title="Elige un producto"'}>🚀 Preparar lanzamiento europeo${S6.pid ? ': ' + esc(pName(S6.pid)) : ''}</button><button class="euchip" data-act="run">▶ Ejecutar tareas pendientes</button></div>` : ''}
      <h3 style="margin-top:8px">Bandeja de decisiones <small>${pend.length} pendiente(s)</small></h3>${pend.length ? pend.map(decisionCard).join('') : '<p class="muted">Nada pendiente de tu aprobación.</p>'}<p class="v6msg">${esc(S6.msg)}</p></article>`;
  }

  // ======================================================================================= LANZAMIENTOS
  async function viewLanz(el) {
    if (!S6.pid) { el.innerHTML = `<section class="filters neon-v">${prodSel(false)}</section>` + empty('Elige un producto para ver o preparar su lanzamiento.'); S6.pid = S6.prods[0] ? S6.prods[0].id : ''; if (S6.pid) return viewLanz(el); return; }
    const [r, t] = await Promise.all([api('GET', '/api/v06/launch?product=' + encodeURIComponent(S6.pid)), api('GET', '/api/v06/tasks?product=' + encodeURIComponent(S6.pid))]); if (!r.ok) return (el.innerHTML = empty(r.j.error || 'Error'));
    const d = S6.launch = r.j; const secs = d.sections;
    const body = (s) => {
      let h = '';
      if (s.id === 'europa') h = `<table class="tbl"><tr><th>País</th><th>Estado</th><th>Competidores</th><th>Detalle</th></tr>${s.countries.map((c) => `<tr><td>${esc(c.name)}</td><td>${ST(c.state)}</td><td>${c.competitors || 0}</td><td><small>${esc(c.why || '')}</small></td></tr>`).join('')}</table><p class="f info">${esc(s.uk.why)} ${ST(s.uk.state)}</p>`;
      else if (s.id === 'competidores') h = s.rows.length ? `<div class="euscroll"><table class="tbl"><tr><th>País</th><th>ASIN</th><th>Marca</th><th>Precio</th><th>Por 100</th><th>Tipo</th><th>Comparabilidad</th></tr>${s.rows.map((c) => `<tr><td>${c.country}</td><td>${esc(c.asin)}</td><td>${esc(c.brand || '')}</td><td>${c.price == null ? 'ND' : c.price}</td><td>${c.price_norm == null ? 'ND' : c.price_norm}</td><td>${ST(c.tipo)}</td><td>${esc(c.comparabilidad || '—')} <small>${esc(c.estado_comparabilidad || '')}</small></td></tr>`).join('')}</table></div>` : '<p class="muted">SIN DATOS: aún no hay competidores. Aprueba el descubrimiento Keepa en la bandeja.</p>';
      else if (s.id === 'economia') h = `<table class="tbl"><tr><th>País</th><th>Estado</th><th>Contribución/ud</th><th>Margen</th><th>ACoS equilibrio</th></tr>${s.rows.map((x) => `<tr><td>${x.country}</td><td>${ST(x.state || '')}${x.missing ? '<br><small class="muted">falta: ' + esc(x.missing.join(', ')) + '</small>' : ''}</td><td>${x.contribution == null ? 'NO CALCULABLE' : eur(x.contribution)}</td><td>${pct(x.margin)}</td><td>${pct(x.breakeven_acos)}</td></tr>`).join('')}</table>`;
      else if (s.id === 'paises') h = (s.ranking && s.ranking.length ? s.ranking.map((x) => `<div class="f">${esc(x.name)} — ${esc(x.score)}</div>`).join('') : '') + `<p class="muted">${esc(s.note)}</p>` + (s.pending || []).map((x) => `<div class="f warn"><b>${esc(x.name)}</b> ${ST('NO EVALUABLE')}<br><small class="muted">${esc((x.why || []).join(' · '))}</small></div>`).join('');
      else if (s.id === 'recomendacion') h = `<p class="eudec">${esc(s.verdict)}</p>${(s.reasons || []).map((x) => `<div class="f warn">${esc(x)}</div>`).join('')}<h4>Siguientes pasos</h4>${(s.next_steps || []).map((x) => `<div class="f info">${esc(x)}</div>`).join('')}`;
      else if (s.id === 'listing') h = `<p>${ST('BORRADOR')} <b>${esc(s.listing_title)}</b></p><ul>${s.bullets.map((b) => `<li>${esc(b)}</li>`).join('')}</ul><p class="muted">${esc(s.description)}</p><p>Revisión de claims: ${s.lint.blocks ? ST(s.lint.blocks + ' BLOQUEADO(S)') : ST('Sin bloqueos')} ${s.lint.reviews ? ST(s.lint.reviews + ' a revisar') : ''}</p>${(s.claims_sin_respaldo_excluidos || []).length ? '<p class="f warn">Excluidos por falta de respaldo: ' + esc(s.claims_sin_respaldo_excluidos.join(' · ')) + '</p>' : ''}<details><summary>A+ · FAQ · imágenes · guion de vídeo (borradores)</summary><ul>${s.a_plus.concat(s.faq, s.images_plan, s.video_script).map((x) => `<li>${esc(x)}</li>`).join('')}</ul><p class="muted">${esc(s.visual_proposals)} ${esc(s.keywords_note)}</p></details>`;
      else if (s.id === 'cumplimiento') h = `<p class="f info">${esc(s.flow)}</p><p class="eudec ${s.open ? '' : 'ok'}">${esc(s.verdict)}</p><table class="tbl"><tr><th>País</th><th>Requisitos OK</th></tr>${s.by_country.map((c) => `<tr><td>${c.country}</td><td>${c.ok}/${c.total}</td></tr>`).join('')}</table><p class="muted">${esc(s.limit)}</p>`;
      else if (s.id === 'ppc') h = `<table class="tbl"><tr><th>Campaña</th><th>Objetivo</th><th>Presupuesto</th></tr>${s.campaigns.map((c) => `<tr><td>${esc(c.tipo)}</td><td>${esc(c.objetivo)}</td><td>${ST(c.presupuesto)}</td></tr>`).join('')}</table><p>ACoS máximo: ${s.acos_cap.valor == null ? ST('NO DETERMINABLE') + ' <small class="muted">' + esc(s.acos_cap.why) + '</small>' : pct(s.acos_cap.valor)}</p><p class="muted">${esc(s.rule)}</p>`;
      else if (s.id === 'calendario') h = `<table class="tbl"><tr><th>Ventana</th><th>Hito</th><th>Puerta</th></tr>${s.phases.map((p) => `<tr><td>${esc(p.ventana)}</td><td>${esc(p.hito)}</td><td>${ST(p.estado_puerta)}</td></tr>`).join('')}</table><p class="muted">${esc(s.note)}</p>`;
      else if (s.id === 'ficha') h = `<p class="muted">Falta: ${esc((s.missing || []).join(', ') || 'nada')}</p><p class="muted">${esc(s.note)}</p>`;
      else if (s.id === 'limites') h = s.items.map((x) => `<div class="f info">${esc(x)}</div>`).join('');
      return h;
    };
    el.innerHTML = `<section class="filters neon-v">${prodSel(false)}<span>${ST(d.recommendation)}</span><span class="grow"></span>${canEdit() ? '<button class="btn" data-act="order">🚀 Preparar lanzamiento europeo</button>' : ''}<a class="btn ghost" href="/api/v06/launch?product=${encodeURIComponent(S6.pid)}&fmt=md" download>⬇ Markdown</a><a class="btn ghost" href="/api/v06/launch?product=${encodeURIComponent(S6.pid)}&fmt=html" download>⬇ HTML (imprimir/PDF)</a></section>
      <p class="v6msg">${esc(S6.msg)}</p><div class="layout"><div class="left">${secs.map((s) => `<article class="card c-cyan v6sec"><h3>${esc(s.title)} ${ST(s.state)}</h3>${body(s)}</article>`).join('')}</div><aside class="right">${directorCard()}<article class="card c-pink"><h3>Tareas del producto</h3>${t.ok && t.j.tasks.length ? t.j.tasks.map((x) => `<div class="f"><b>${esc(x.kind)}</b> ${ST(x.state)}<br><small class="muted">${esc(x.decision_label)}${x.error ? ' · ' + esc(x.error) : ''}</small></div>`).join('') : '<p class="muted">Sin tareas todavía.</p>'}</article></aside></div>`;
  }

  // ======================================================================================= MIS VENTAS
  async function viewVentas(el) {
    if (!S6.pid && S6.prods[0]) S6.pid = S6.prods[0].id;
    const q = encodeURIComponent(S6.pid), [im, cn] = await Promise.all([api('GET', '/api/v06/imports?product=' + q), api('GET', '/api/v06/connections')]); const sm = im.ok ? im.j.summary : null, E0 = S6.econ || {};
    el.innerHTML = `<section class="filters neon-v">${prodSel(false)}<span class="muted">Datos reales = informes de Amazon importados sin modificar. La conexión API directa está PENDIENTE DE CONEXIÓN.</span></section>
      <div class="estg"><article class="card c-cyan"><h3>Importar informes de Amazon <small>CSV descargado de Seller Central / Ads</small></h3>${canEdit() ? `<p><input type="file" id="v6File" accept=".csv,.txt"> <select id="v6Kind"><option value="">Detectar tipo</option><option value="ventas">Informe de ventas</option><option value="publicidad">Informe de publicidad</option></select> <button class="btn" data-act="import">Importar</button></p>` : '<p class="muted">Solo aprobador/administrador.</p>'}<p class="v6msg">${esc(S6.msg)}</p>
        ${im.ok && im.j.reports.length ? `<table class="tbl"><tr><th>Archivo</th><th>Tipo</th><th>Cobertura</th><th>Importado</th></tr>${im.j.reports.map((r) => `<tr><td>${esc(r.filename)}<br><small class="muted">SHA ${esc(r.sha256.slice(0, 12))}</small></td><td>${esc(r.type)}</td><td>${esc(r.metrics.coverage.from || '—')} → ${esc(r.metrics.coverage.to || '—')} · ${r.metrics.coverage.rows} filas</td><td>${esc(r.imported_at.slice(0, 10))} ${ST('IMPORTADO')}</td></tr>${(r.warnings || []).map((w) => `<tr><td colspan="4" class="f warn">${esc(w)}</td></tr>`).join('')}`).join('')}</table>` : '<p>' + ST('SIN DATOS') + ' No hay informes importados para este producto.</p>'}</article>
      <article class="card c-lime"><h3>Resumen real <small>solo lo importado</small></h3>${sm && sm.state === 'IMPORTADO' ? `<div class="f">Ventas: ${sm.sales.total != null ? eur(sm.sales.total) + ' (' + esc(sm.sales.from) + ' → ' + esc(sm.sales.to) + ')' : ST('SIN DATOS')}</div><div class="f">Publicidad: ${sm.ads.spend != null ? 'gasto ' + eur(sm.ads.spend) + ' · ACoS ' + pct(sm.ads.acos) : ST('SIN DATOS')}</div><div class="f">TACoS: ${sm.tacos.valor != null ? pct(sm.tacos.valor) : ST('NO DETERMINABLE') + ' <small class="muted">' + esc(sm.tacos.why || '') + '</small>'}</div><p class="muted">${esc((sm.sales && sm.sales.note) || '')}</p>` : '<p class="muted">Sin datos reales todavía. No se muestran ceros: importa un informe.</p>'}</article>
      <article class="card c-violet wide"><h3>Rentabilidad por país <small>motor determinista · cada dato con su clase</small></h3><div class="eufil"><label>PVP con IVA (€)<input type="number" step="0.1" id="v6Pvp" value="${E0.pvp || ''}"></label><label>Logística<select id="v6Mode"><option>FBA</option><option>FBM</option></select></label><label>ACoS objetivo (0–1)<input type="number" step="0.01" id="v6Acos" value="${E0.acos || ''}"></label><label>% ventas por ads (0–1)<input type="number" step="0.05" id="v6Share" value="${E0.share || ''}"></label><button class="btn" data-act="econ">Calcular</button></div><div id="v6EconOut">${S6.econOut || '<p class="muted">Pulsa Calcular. Si faltan costes se dice cuáles: no se rellenan por defecto.</p>'}</div></article>
      <article class="card c-amber wide"><h3>Inventario <small>solo con hipótesis tuyas (no se inventa demanda)</small></h3><div class="eufil"><label>Ventas esperadas (uds/mes)<input type="number" id="v6Upm"></label><label>Plazo reposición (días)<input type="number" id="v6Lead"></label><label>Seguridad (días)<input type="number" id="v6Safe"></label><label>Stock verificado (uds)<input type="number" id="v6Stock"></label><button class="btn" data-act="inv">Calcular</button></div><div id="v6InvOut"><p class="muted">NO DETERMINABLE hasta que indiques ventas esperadas y plazo.</p></div></article>
      <article class="card c-pink wide"><h3>Conexiones <small>estado real verificado</small></h3>${cn.ok ? `<table class="tbl"><tr><th>Conexión</th><th>Código</th><th>Estado</th><th>Límites</th></tr>${cn.j.rows.map((x) => `<tr><td>${esc(x.name)}</td><td>${ST(x.code)}</td><td>${ST(x.state)}</td><td><small>${esc(x.limits)}</small></td></tr>`).join('')}</table>` : ''}</article></div>`;
  }
  const clsTag = (c) => (c ? `<span class="tagst ${c === 'OBSERVADO' || c === 'IMPORTADO' || c === 'DERIVADO' ? 't-ok' : 't-wait'}">${c}</span>` : '');
  async function doEcon() {
    const v = (id) => ($(id).value === '' ? null : Number($(id).value)); let qs = 'product=' + encodeURIComponent(S6.pid) + '&mode=' + $('#v6Mode').value;
    if (v('#v6Pvp') != null) qs += '&pvp=' + v('#v6Pvp'); if (v('#v6Acos') != null) qs += '&acos=' + v('#v6Acos'); if (v('#v6Share') != null) qs += '&ads_share=' + v('#v6Share');
    S6.econ = { pvp: v('#v6Pvp'), acos: v('#v6Acos'), share: v('#v6Share') };
    const r = await api('GET', '/api/v06/econ?' + qs); if (!r.ok) { S6.econOut = `<p class="f warn">${esc(r.j.error)}</p>`; return render(); }
    S6.econOut = r.j.rows ? `<table class="tbl"><tr><th>País</th><th>Estado</th><th>Neto</th><th>Contribución/ud</th><th>Margen</th><th>ACoS equil.</th><th>TACoS</th></tr>${r.j.rows.map((x) => { const q = x.result || {}; return `<tr><td>${x.country}</td><td>${ST(x.state || 'NO CALCULABLE')} ${clsTag(x.class)}${x.missing ? '<br><small class="muted">falta: ' + esc(x.missing.join(', ')) + '</small>' : ''}</td><td>${eur(q.net_price)}</td><td>${x.complete ? eur(q.contribution_before_ads) : 'NO CALCULABLE'}</td><td>${x.complete ? pct(q.margin_before_ads) : 'NO CALCULABLE'}</td><td>${x.complete ? pct((x.breakeven_acos || {}).sin_iva) : '—'}</td><td>${x.tacos && x.tacos.valor != null ? pct(x.tacos.valor) + ' ' + clsTag('HIPOTESIS') : 'NO DETERMINABLE'}</td></tr>`; }).join('')}</table><p class="muted">Clases: ${Object.entries(r.j.classes).map(([k, h]) => k + ' = ' + h).join(' · ')}. El resultado hereda la clase del dato más débil.</p>` : `<p>${ST(r.j.state)} ${esc(r.j.why)}</p>`; render();
  }
  async function doInv() {
    const v = (id) => ($(id).value === '' ? '' : Number($(id).value)); const r = await api('GET', `/api/v06/inventory?units_per_month=${v('#v6Upm')}&lead_time_days=${v('#v6Lead')}&safety_days=${v('#v6Safe')}&stock=${v('#v6Stock')}`);
    $('#v6InvOut').innerHTML = r.ok && r.j.state.startsWith('CALCULADO') ? `<p>${ST(r.j.state)} Punto de pedido <b>${r.j.reorder_point_units}</b> uds · ventas/día ${r.j.daily_units}${r.j.cover_days != null ? ' · cobertura ' + r.j.cover_days + ' días' : ''}${r.j.order_units != null ? ' · pedido sugerido <b>' + r.j.order_units + '</b> uds' : ''}</p><p class="muted">${esc(r.j.formula)} (HIPÓTESIS del usuario).</p>` : `<p>${ST('NO DETERMINABLE')} ${esc((r.j || {}).why || (r.j || {}).error || '')}</p>`;
  }

  // ======================================================================================= PRODUCTOS
  const fieldv = (f) => (f && f.v != null ? `${esc(f.v)} ${ST(f.status)}` : ST('NO DISPONIBLE'));
  async function viewProd(el) {
    const cat = S6.cats; const ed = S6.edit;
    const form = ed ? formProd(ed) : '';
    el.innerHTML = `<section class="filters neon-v"><b>Catálogo central</b><span class="muted">${S6.prods.length} producto(s) · se añaden, editan y archivan sin programar</span><span class="grow"></span>${canEdit() ? '<button class="btn" data-act="new">＋ Añadir producto</button>' : ''}</section><p class="v6msg">${esc(S6.msg)}</p>${form}
      ${cat.map((c) => `<article class="card c-cyan"><h3>${esc(c.name)} <small>normalización por ${c.normalization === 'ml' ? '100 mL' : '100 unidades'}</small></h3><div class="eucards">${S6.prods.filter((p) => p.category === c.id).map((p) => `<div class="eucard v6prod"><b>${esc(p.name)}</b> ${ST(p.commercial_state || 'PRELANZAMIENTO')}<br><small class="muted">${esc(p.brand)} · ${esc(p.subcategory || '')}</small><br>Formato: ${p.format.content ? esc(p.format.content + ' ' + p.format.unit) : ST('NO DISPONIBLE')}<br>PVP ref.: ${fieldv(p.pvp.REF || Object.values(p.pvp)[0])}<br>Stock: ${fieldv(p.stock)}<br>SKU: ${esc(p.sku || '—')}<br>${(p.missing || []).length ? '<small class="muted">Falta: ' + esc(p.missing.join(', ')) + '</small>' : ST('Ficha completa')}<br>${canEdit() ? `<button class="btn ghost" data-act="edit" data-id="${esc(p.id)}">Editar</button> <button class="btn ghost" data-act="archive" data-id="${esc(p.id)}">Archivar</button>` : ''} <button class="btn ghost" data-act="goto-lanz" data-id="${esc(p.id)}">Lanzamiento</button></div>`).join('') || '<p class="muted">Sin productos en esta categoría.</p>'}</div></article>`).join('')}`;
  }
  function formProd(ed) {
    const p = ed.p, isNew = !p.id; const g = (k, d) => esc(p[k] == null ? d || '' : p[k]); const pv = (p.pvp && (p.pvp.REF || {}).v) || ''; const co = (p.costs && (p.costs.cogs || {}).v) || '';
    return `<article class="card c-amber wide"><h3>${isNew ? 'Nuevo producto' : 'Editar ' + esc(p.name)}</h3><div class="euform">
      <label>Nombre<input id="fpName" value="${g('name')}"></label><label>Marca<input id="fpBrand" value="${g('brand')}"></label>
      <label>Categoría<select id="fpCat">${S6.cats.map((c) => `<option value="${esc(c.id)}" ${p.category === c.id ? 'selected' : ''}>${esc(c.name)}</option>`).join('')}</select></label><label>Subcategoría<input id="fpSub" value="${g('subcategory')}"></label>
      <label>SKU<input id="fpSku" value="${g('sku')}"></label><label>Estado comercial<select id="fpState">${['IDEA', 'DESARROLLO', 'PRELANZAMIENTO', 'LANZADO', 'PAUSADO', 'RETIRADO'].map((s) => `<option ${p.commercial_state === s ? 'selected' : ''}>${s}</option>`).join('')}</select></label>
      <label>Contenido<input id="fpCont" type="number" value="${p.format && p.format.content != null ? esc(p.format.content) : ''}"></label><label>Unidad<select id="fpUnit">${['ml', 'g', 'unidades'].map((u) => `<option ${p.format && p.format.unit === u ? 'selected' : ''}>${u}</option>`).join('')}</select></label>
      <label>PVP referencia con IVA (€)<input id="fpPvp" type="number" step="0.01" value="${esc(pv)}"></label><label>Estado del PVP<select id="fpPvpSt">${['PROPUESTO', 'DOCUMENTADO', 'VERIFICADO', 'A_CONFIRMAR'].map((u) => `<option>${u}</option>`).join('')}</select></label>
      <label>Coste unitario sin IVA (€)<input id="fpCogs" type="number" step="0.01" value="${esc(co)}"></label><label>Fuente del coste (si DOCUMENTADO/VERIFICADO)<input id="fpSrc" placeholder="p. ej. factura 2026-11-01 de Laboratorios…"></label>
      <label class="wide">Composición (una por línea; sin verificar contra INCI salvo que lo indiques)<textarea id="fpComp" rows="3">${esc((p.composition || []).map((c) => c.name).join('\n'))}</textarea></label>
      <label class="wide">Claims (uno por línea · «texto | evidencia»; sin evidencia = SIN RESPALDO y se excluye del listing)<textarea id="fpClaims" rows="3">${esc((p.claims || []).map((c) => c.text + (c.evidence ? ' | ' + c.evidence : '')).join('\n'))}</textarea></label>
      <label>ASIN Amazon.es (si existe)<input id="fpAsin" value="${esc(((p.amazon_connections || {}).ES || {}).asin || '')}"></label>
    </div><p><button class="btn" data-act="save">Guardar</button> <button class="btn ghost" data-act="cancel">Cancelar</button></p></article>`;
  }
  async function saveProd() {
    const v = (id) => $(id).value.trim(), num = (id) => (v(id) === '' ? null : Number(v(id))); const ed = S6.edit, isNew = !ed.p.id;
    const b = { name: v('#fpName'), brand: v('#fpBrand'), category: $('#fpCat').value, subcategory: v('#fpSub'), sku: v('#fpSku'), commercial_state: $('#fpState').value, format: { content: num('#fpCont'), unit: $('#fpUnit').value, status: 'A_CONFIRMAR', source: '' },
      composition: v('#fpComp').split('\n').map((x) => x.trim()).filter(Boolean).map((n) => ({ name: n, status: 'A_CONFIRMAR' })), claims: v('#fpClaims').split('\n').map((x) => x.trim()).filter(Boolean).map((l) => { const [t, ...e] = l.split('|'); return { text: t.trim(), evidence: e.join('|').trim() }; }) };
    if (num('#fpPvp') != null) b.pvp = { REF: { v: num('#fpPvp'), status: $('#fpPvpSt').value, source: 'Indicado por el usuario en la ficha', date: new Date().toISOString().slice(0, 10) } };
    if (num('#fpCogs') != null) { const st = v('#fpSrc').length >= 8 ? 'DOCUMENTADO' : 'A_CONFIRMAR'; b.costs = { cogs: { v: num('#fpCogs'), status: st, source: v('#fpSrc') || 'Indicado por el usuario (sin fuente)', date: new Date().toISOString().slice(0, 10) } }; }
    if (v('#fpAsin')) b.amazon_connections = { ES: { asin: v('#fpAsin') } };
    const r = isNew ? await api('POST', '/api/catalog/product', b) : await api('POST', '/api/catalog/update', { id: ed.p.id, patch: b, note: 'edición desde PRODUCTOS' });
    S6.msg = r.ok ? (isNew ? 'Producto creado. El Director ha arrancado su expediente automáticamente (N1); el gasto Keepa espera tu aprobación.' : 'Ficha guardada (nueva versión).') : 'No se guardó: ' + (r.j.error || 'error'); if (r.ok) S6.edit = null; await loadBase(); render();
  }

  // ======================================================================================= DIRECTOR IA
  async function viewDir(el) {
    const [o, t, l, c, a] = await Promise.all([api('GET', '/api/v06/ops'), api('GET', '/api/v06/tasks'), api('GET', '/api/v06/ledger'), api('GET', '/api/v06/connections'), isAdmin() ? api('GET', '/api/v06/ai/calls') : Promise.resolve({ ok: false })]);
    const od = o.ok ? o.j : { tasks: {}, policies: [], events: [], levels: {}, kill_switch: {} };
    el.innerHTML = `<section class="filters neon-v"><b>Centro operativo del Director</b><span>${od.kill_switch.on ? ST('INTERRUPTOR DE EMERGENCIA ACTIVO') : ST('Automatizaciones externas permitidas por política')}</span><span class="grow"></span>${canEdit() ? `<button class="btn ${od.kill_switch.on ? '' : 'no'}" data-act="kill" data-on="${od.kill_switch.on ? 0 : 1}">${od.kill_switch.on ? 'Reanudar (admin)' : '⛔ PARAR automatizaciones externas'}</button>` : ''}<button class="btn ghost" data-act="open-chat">💬 Conversar con el Director (por producto)</button></section><p class="v6msg">${esc(S6.msg)}</p>
      <div class="layout"><div class="left"><article class="card c-pink"><h3>Cola de tareas <small>ordenada por prioridad explicable</small></h3>${t.ok && t.j.tasks.length ? `<table class="tbl"><tr><th>#</th><th>Tarea · decisión de negocio</th><th>Producto</th><th>Estado</th><th>Intentos</th><th>Prioridad (por qué)</th></tr>${t.j.tasks.map((x) => `<tr><td>${x.id}</td><td>${esc(x.kind)}<br><small class="muted">${esc(x.decision_label)}</small></td><td>${esc(pName(x.product))}</td><td>${ST(x.state)}${x.error ? '<br><small class="muted">' + esc(x.error) + '</small>' : ''}</td><td>${x.attempts}/${x.max_attempts}</td><td><small>${esc(x.priority_why)}</small></td></tr>`).join('')}</table>` : '<p class="muted">Sin tareas. Ordena «Preparar lanzamiento» a un producto.</p>'}</article>
      <article class="card c-lime"><h3>Libro de decisiones <small>sin atribución automática de ventas a la IA</small></h3>${l.ok && l.j.ledger.length ? l.j.ledger.map((x) => `<div class="f"><b>${esc(x.objective)}</b><br><small class="muted">Aprobación: ${esc(x.approval || '—')} · Acción: ${esc(x.action || '—')} · Resultado observado: ${esc(x.observed_result || 'PENDIENTE')} · Atribución: ${esc(x.attribution)}</small></div>`).join('') : '<p class="muted">Aún no hay decisiones registradas.</p>'}</article>
      <article class="card c-violet"><h3>Autonomía por niveles</h3>${Object.entries(od.levels).map(([k, v]) => `<div class="f"><b>${k}</b> ${esc(v)}</div>`).join('')}<h4>Políticas N2 vigentes</h4>${od.policies.length ? od.policies.map((p) => `<div class="f">${esc(p.action)} · ${p.enabled ? ST('ACTIVA') : ST('INACTIVA')} · máx ${p.max_per_day}/día · ${p.max_eur} €</div>`).join('') : '<p class="muted">Ninguna: toda acción con efectos externos o gasto pide aprobación (N3).</p>'}</article>
      <article class="card c-cyan"><h3>Modelos de IA <small>política por tarea · sin router complejo</small></h3><table class="tbl"><tr><th>Tarea</th><th>Modelo</th><th>Validador</th><th>Escalado</th><th>Tope €</th></tr>${Object.entries(od.task_policy || {}).map(([k, v]) => `<tr><td>${esc(k)}</td><td>${esc(v.tier)}</td><td>${esc(v.validator || '—')}</td><td>${v.escalate ? 'máx. 1' : 'no'}</td><td>${v.budget_eur == null ? '—' : v.budget_eur}</td></tr>`).join('')}</table>${a.ok ? `<h4>Últimas llamadas (tokens · coste · latencia · error)</h4>${a.j.calls.length ? '<table class="tbl">' + a.j.calls.slice(0, 12).map((x) => `<tr><td>${esc(x.ts.slice(11, 19))}</td><td>${esc(x.task_type)}</td><td>${esc(x.model || '—')}</td><td>${x.tokens_in || 0}/${x.tokens_out || 0}</td><td>${x.cost == null ? '—' : x.cost}</td><td>${x.latency_ms == null ? '—' : x.latency_ms + ' ms'}</td><td>${ST(x.state)} ${esc(x.error_class || '')}</td></tr>`).join('') + '</table>' : '<p class="muted">Ninguna llamada de IA registrada.</p>'}` : ''}</article></div>
      <aside class="right">${directorCard()}<article class="card c-amber"><h3>Eventos recientes</h3>${od.events.slice(0, 12).map((e) => `<div class="f"><small>${esc(e.ts.slice(11, 19))} · ${esc(e.type)} · ${esc(e.detail.slice(0, 90))}</small></div>`).join('') || '<p class="muted">—</p>'}</article></aside></div>`;
  }

  // ======================================================================================= núcleo
  const VIEWS = { inicio: viewInicio, lanz: viewLanz, ventas: viewVentas, prod: viewProd, dir: viewDir };
  const IDS = { inicio: 'tab-inicio', lanz: 'tab-lanz', ventas: 'tab-ventas', prod: 'tab-prod', dir: 'tab-dir' };
  let busy = false, again = false;
  async function render() { // serializa y fusiona: la última petición de pintado siempre se ejecuta la última (sin carreras)
    if (busy) { again = true; return; }
    busy = true;
    try {
      do {
        again = false; const sp = S6.space; const el = $('#v6' + sp); if (!el) break;
        if (!loggedIn()) { el.innerHTML = empty('Inicia sesión (botón «Acceso» arriba a la derecha) para ver el Director Comercial.'); break; }
        await loadBase(); await VIEWS[sp](el);
      } while (again);
    } finally { busy = false; }
  }
  async function act(a, t) {
    if (a === 'demo-on') { S6.demo = true; return render(); }
    if (a === 'demo-off') { S6.demo = false; return render(); }
    if (a === 'order') { if (!S6.pid) return; S6.msg = 'Ejecutando…'; render(); const r = await api('POST', '/api/v06/order', { product: S6.pid }); S6.msg = r.ok ? `Hecho: ${r.j.executed.filter((x) => x.state === 'COMPLETADA').length} tarea(s) completadas automáticamente · ${r.j.decisions_pending.length} decisión(es) esperan tu aprobación.` : 'Error: ' + (r.j.error || ''); return render(); }
    if (a === 'run') { const r = await api('POST', '/api/v06/run', {}); S6.msg = r.ok ? r.j.executed.length + ' tarea(s) procesadas.' : (r.j.error || 'error'); return render(); }
    if (a === 'decide') { const r = await api('POST', '/api/v06/decide', { id: Number(t.dataset.id), approve: t.dataset.ok === '1' }); S6.msg = r.ok ? (r.j.nota || 'Registrado') : (r.j.error || 'error'); if (r.ok && t.dataset.ok === '1') await api('POST', '/api/v06/run', {}); return render(); }
    if (a === 'kill') { const r = await api('POST', '/api/v06/kill', { on: t.dataset.on === '1', reason: 'desde la interfaz' }); S6.msg = r.ok ? 'Interruptor ' + (r.j.on ? 'ACTIVADO' : 'desactivado') : (r.j.error || 'error'); return render(); }
    if (a === 'new') { S6.edit = { p: { category: (S6.cats[0] || {}).id, commercial_state: 'PRELANZAMIENTO' } }; return render(); }
    if (a === 'edit') { S6.edit = { p: JSON.parse(JSON.stringify(S6.prods.find((p) => p.id === t.dataset.id))) }; return render(); }
    if (a === 'cancel') { S6.edit = null; return render(); }
    if (a === 'save') return saveProd();
    if (a === 'archive') { const r = await api('POST', '/api/catalog/archive', { id: t.dataset.id, archived: true }); S6.msg = r.ok ? 'Producto archivado (se conserva su historial).' : r.j.error; return render(); }
    if (a === 'goto-lanz') { S6.pid = t.dataset.id; return setSpace('lanz'); }
    if (a === 'econ') return doEcon();
    if (a === 'inv') return doInv();
    if (a === 'open-chat') { if (root.EU) { const sel = $('#tabs button[data-tab=europa]'); if (sel) sel.click(); } return; }
    if (a === 'import') {
      const f = $('#v6File').files[0]; if (!f) { S6.msg = 'Elige un archivo CSV.'; return render(); } const buf = new Uint8Array(await f.arrayBuffer()); let bin = ''; buf.forEach((x) => (bin += String.fromCharCode(x)));
      const r = await api('POST', '/api/v06/import', { product: S6.pid, filename: f.name, content_b64: btoa(bin), kind: $('#v6Kind').value || undefined }); S6.msg = r.ok ? 'Importado: ' + r.j.type + ' (' + r.j.metrics.coverage.rows + ' filas).' : 'No importado: ' + (r.j.error || ''); return render();
    }
  }
  function setSpace(sp) { S6.space = sp; $$('#tabs button').forEach((b) => b.classList.toggle('on', b.dataset.tab === sp)); $$('.tab').forEach((x) => x.classList.toggle('on', x.id === IDS[sp])); render(); }
  function init() {
    S6.space = 'inicio'; document.body.classList.add('inv6');
    document.addEventListener('click', (e) => {
      const nb = e.target.closest('#tabs button'); if (nb) document.body.classList.toggle('inv6', !!VIEWS[nb.dataset.tab]); if (nb && VIEWS[nb.dataset.tab]) { S6.space = nb.dataset.tab; render(); return; }
      const b = e.target.closest('[data-act]'); if (b && b.closest('.v6root')) act(b.dataset.act, b);
    });
    document.addEventListener('change', (e) => { if (e.target.hasAttribute('data-v6prod')) { S6.pid = e.target.value; render(); } });
    let last = null; setInterval(() => { const u = loggedIn() ? root.V03.V.user : null; if (u !== last) { last = u; render(); } }, 700);
    render();
  }
  root.V06 = { state: S6, render, setSpace };
  document.addEventListener('DOMContentLoaded', init);
})(self);
