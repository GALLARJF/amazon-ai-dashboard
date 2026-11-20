/* P0 · Fase 3 — LANZAMIENTOS GUIADOS.
   Capa de PRESENTACIÓN: solo lee GET existentes (catalog, v06/launch, v06/decisions, v06/tasks). No cambia API, cálculos, datos ni seguridad,
   no ejecuta Keepa, IA de pago, publicaciones ni acciones comerciales.
   Cuatro niveles: 1 Conclusión · 2 Decisión · 3 Evidencia (plegada: expediente guiado en 10 pasos) · 4 Metodología (plegada: las 11 secciones originales, intactas).
   Reglas: nada se inventa; lo ausente es SIN DATOS (nunca 0); cada bloque indica REAL, DEMO o SIN DATOS; GO nunca se emite por defecto.
   ?legacy=1 conserva la pantalla antigua (transitorio: docs/p0_hoy/PLAN_RETIRADA_LEGACY.md). */
(function (root) {
  'use strict';
  const $ = (s, r) => (r || document).querySelector(s), $$ = (s, r) => [...(r || document).querySelectorAll(s)];
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const eur = (x) => (x == null || isNaN(x) ? 'NO DETERMINABLE' : Number(x).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €');
  const pct = (x) => (x == null ? 'NO DETERMINABLE' : (x * 100).toFixed(1) + ' %');
  const day = (s) => (s ? String(s).slice(0, 10) : 'SIN DATOS');

  // ---------------------------------------------------------------------------------------------- lógica pura (probada desde el navegador)
  const NODATA = /SIN DATOS|NO CALCULABLE|NO DETERMINABLE|NO DISPONIBLE|NO_DISPONIBLE|PENDIENTE DE CONEXI/i;
  /* Estado del lanzamiento. GO solo si TODO lo exigible está documentado; el servidor actual nunca lo emite y aquí tampoco se inventa. */
  function statusOf(L, steps) {
    const sec = (id) => (L.sections || []).find((s) => s.id === id) || {};
    const rec = sec('recomendacion'), eco = sec('economia'), cum = sec('cumplimiento'), pais = sec('paises');
    const rows = (eco.rows || []).filter((r) => r.contribution != null && r.margin != null);
    const blockers = (rec.reasons || []).length, undecidable = /NO DECIDIBLE/i.test(rec.verdict || '');
    if (rows.length && rows.every((r) => r.contribution < 0) && rows.length === (eco.rows || []).length) return { v: 'NO GO', why: 'La contribución por unidad es negativa en todos los países calculados (' + rows.length + ').' };
    const withData = steps.filter((s) => s.state !== 'SIN DATOS').length;
    if (undecidable && !steps.some((s) => ['economia', 'benchmark', 'cumplimiento'].includes(s.id) && s.state !== 'SIN DATOS')) return { v: 'SIN DATOS', why: 'El servidor no puede decidir todavía y ni la economía, ni el benchmark, ni el cumplimiento tienen datos (' + withData + ' de ' + steps.length + ' pasos con algún dato).' };
    if (!undecidable && !blockers && cum.open === 0 && rows.length && (eco.rows || []).every((r) => r.contribution != null && r.contribution > 0) && (pais.ranking || []).length) return { v: 'GO', why: 'Economía positiva en todos los países, cumplimiento sin requisitos abiertos y ranking de países disponible.' };
    return { v: 'REVISAR', why: blockers ? blockers + ' bloqueo(s) abiertos con datos parciales: hay que resolverlos antes de decidir.' : 'Hay datos mínimos: decide el país piloto con el ranking y la economía.' };
  }
  const ROLE = [[/regulator|cumplimiento|cpnp|pif|cpsr|notific|etiquet|claims/i, 'Responsable regulatorio'], [/keepa|descubrimiento|autoriz|presupuesto/i, 'Aprobador (autoriza el gasto Keepa)'],
    [/coste|log[ií]stic|tarifa|transporte|stock|env[ií]o|lote|almac/i, 'Operaciones / Compras'], [/competidor|comparab|benchmark|demanda|keyword/i, 'Analista de mercado'], [/imagen|documento|composici|sku|asin|ficha|contenido/i, 'Responsable de producto']];
  const roleOf = (t) => { const r = ROLE.filter((x) => x[0].test(t || '')).map((x) => x[1]); return (r.length ? r.slice(0, 2).join(' y ') : 'Responsable de producto') + ' · sin persona asignada'; };

  function stepsOf(L, P) {
    const sec = (id) => (L.sections || []).find((s) => s.id === id) || {};
    const eco = sec('economia'), cum = sec('cumplimiento'), fic = sec('ficha'), comp = sec('competidores'), rec = sec('recomendacion'), eu = sec('europa');
    const pv = (P.pvp || {}).REF || {}, st = P.stock || {}, cg = (P.costs || {}).cogs || {}, docs = P.documents || [];
    const calc = (eco.rows || []).filter((r) => r.contribution != null), missEco = [...new Set([].concat(...(eco.rows || []).map((r) => r.missing || [])))];
    const miss = (what, who) => ({ what, who: who || roleOf(what) });
    const S = [];
    S.push({ id: 'producto', n: 1, title: 'Producto y mercado', state: (fic.missing || []).length ? 'PARCIAL' : 'OK',
      lines: [['Producto', P.name + ' · ' + (P.brand || 'SIN DATOS')], ['Categoría', (P.category || 'SIN DATOS') + (P.subcategory ? ' · ' + P.subcategory : '')], ['Formato', (P.format || {}).description || 'SIN DATOS'], ['Mercados objetivo', (P.target_markets || []).join(', ') || 'SIN DATOS'],
        ['Países con datos de mercado', (eu.countries || []).filter((c) => c.state !== 'SIN DATOS' && !/PENDIENTE/.test(c.state)).length + ' de ' + (eu.countries || []).length + (eu.countries && eu.countries.length ? '' : '')]],
      missing: (fic.missing || []).map((m) => miss(m)) });
    S.push({ id: 'economia', n: 2, title: 'Economía unitaria', state: calc.length === (eco.rows || []).length && calc.length ? 'OK' : calc.length ? 'PARCIAL' : 'SIN DATOS',
      lines: [['Modo logístico', eco.mode || 'SIN DATOS'], ['Coste del producto (COGS)', cg.v != null ? eur(cg.v) + ' · ' + (cg.status || '') + (/HISTORICO/.test(cg.status || '') ? ' (histórico, no es coste puesto en Amazon)' : '') : 'SIN DATOS'],
        ['Países calculables', calc.length + ' de ' + (eco.rows || []).length], ...calc.map((r) => ['Contribución ' + r.country, eur(r.contribution) + ' · margen ' + pct(r.margin) + ' · ACoS equilibrio ' + pct(r.breakeven_acos)])],
      missing: missEco.map((m) => miss(m, 'Operaciones / Compras · sin persona asignada')) });
    S.push({ id: 'precio', n: 3, title: 'Precio y margen', state: pv.v == null ? 'SIN DATOS' : calc.length ? 'OK' : 'PARCIAL',
      lines: [['PVP de referencia', pv.v != null ? eur(pv.v) + ' · ' + (pv.status || '') : 'SIN DATOS'], ['Fuente del precio', pv.v != null ? (pv.source || 'SIN DATOS') + (pv.date ? ' (' + pv.date + ')' : '') : 'SIN DATOS'], ['Margen', calc.length ? calc.map((r) => r.country + ' ' + pct(r.margin)).join(' · ') : 'NO DETERMINABLE (no se calcula sin costes completos)']],
      missing: pv.v == null ? [miss('PVP de referencia con fuente y fecha', 'Responsable de producto · sin persona asignada')] : (pv.status === 'PROPUESTO' ? [miss('Aprobar el PVP propuesto', 'Dirección · sin persona asignada')] : []) });
    S.push({ id: 'benchmark', n: 4, title: 'Benchmark y competidores', state: (comp.rows || []).length ? 'PARCIAL' : 'SIN DATOS',
      lines: [['Competidores con datos', String((comp.rows || []).length)], ['Referencias del usuario (pistas, no evidencia)', (P.reference_competitors || []).join(' · ') || 'SIN DATOS'], ['Comparables confirmados', 'SIN DATOS: faltan comparables confirmados con BSR y precio por unidad']],
      cards: (comp.rows || []).map((c) => ({ t: (c.brand || '') + ' ' + c.asin + ' · ' + c.country, d: 'Precio ' + (c.price == null ? 'ND' : c.price) + ' · por unidad ' + (c.price_norm == null ? 'ND' : c.price_norm) + ' · ' + (c.comparabilidad || '—') })),
      missing: (comp.rows || []).length ? [] : [miss('Descubrimiento de competidores (gasto Keepa aprobado)'), miss('Confirmar comparabilidad de competidores', 'Analista de mercado · sin persona asignada')] });
    S.push({ id: 'demanda', n: 5, title: 'Demanda', state: 'SIN DATOS', lines: [['Volumen de búsqueda', 'SIN DATOS'], ['Fuente de demanda conectada', 'Ninguna: no se estima demanda sin fuente y fecha'], ['Ventas propias', 'SIN DATOS: sin informe de ventas importado']],
      missing: [miss('Keywords con volumen, fuente y fecha (p. ej. exportación Helium 10)', 'Analista de mercado · sin persona asignada')] });
    S.push({ id: 'stock', n: 6, title: 'Stock y logística', state: st.v != null && !/HISTORICO|NO_DISP/.test(st.status || '') ? 'OK' : st.v != null ? 'PARCIAL' : 'SIN DATOS',
      lines: [['Stock', st.v != null ? st.v + ' uds · ' + (st.status || '') + (/HISTORICO/.test(st.status || '') ? ' (histórico: NO es stock disponible hoy)' : '') : 'SIN DATOS (no se asume 0)'], ['Fecha del dato', day(st.date)], ['Fuente', st.source || 'SIN DATOS'], ['Costes logísticos', missEco.filter((m) => /Transporte|Preparaci|Tarifa|Almacen|Devol/i.test(m)).length ? 'SIN DATOS: ' + missEco.filter((m) => /Transporte|Preparaci|Tarifa|Almacen|Devol/i.test(m)).join(', ') : 'Documentados']],
      missing: (st.v == null || /HISTORICO/.test(st.status || '') ? [miss('Stock disponible verificado hoy', 'Operaciones / Compras · sin persona asignada')] : []).concat(missEco.filter((m) => /Transporte|Preparaci|Tarifa|Almacen|Devol/i.test(m)).length ? [miss('Costes logísticos reales', 'Operaciones / Compras · sin persona asignada')] : []) });
    S.push({ id: 'cumplimiento', n: 7, title: 'Cumplimiento regulatorio', state: cum.open === 0 ? 'OK' : cum.ok ? 'PARCIAL' : 'SIN DATOS',
      lines: [['Veredicto', cum.verdict || 'SIN DATOS'], ['Requisitos con evidencia', (cum.ok || 0) + ' de ' + ((cum.ok || 0) + (cum.open || 0))], ['Flujo aplicable', cum.flow || 'SIN DATOS'], ...(cum.by_country || []).map((c) => [c.country, c.ok + '/' + c.total + ' requisitos'])],
      missing: cum.open ? [miss('Evidencias regulatorias (' + cum.open + ' requisitos sin evidencia)', 'Responsable regulatorio · sin persona asignada')] : [], note: cum.limit });
    S.push({ id: 'documentos', n: 8, title: 'Documentos y fuentes', state: docs.length ? 'PARCIAL' : 'SIN DATOS',
      lines: [['Documentos registrados', String(docs.length)], ['Imágenes', (P.images || []).length ? String((P.images || []).length) : 'SIN DATOS']],
      cards: docs.map((d) => ({ t: d.name, d: (d.type || '') + ' · ' + (d.date || 'SIN FECHA') + ' · ' + (d.ref || '') })),
      missing: (docs.length ? [] : [miss('Documentos del producto (fichas técnicas, informes de análisis)', 'Responsable de producto · sin persona asignada')]).concat((P.images || []).length ? [] : [miss('Imágenes del producto', 'Responsable de producto · sin persona asignada')]) });
    const reasons = rec.reasons || [];
    S.push({ id: 'riesgos', n: 9, title: 'Riesgos y bloqueos', state: reasons.length ? 'SIN DATOS' : 'OK', lines: reasons.length ? reasons.map((r, i) => ['Bloqueo ' + (i + 1), r]) : [['Bloqueos', 'Ninguno registrado']], missing: [] });
    S.push({ id: 'final', n: 10, title: 'Recomendación final', state: /NO DECIDIBLE/.test(rec.verdict || '') ? 'SIN DATOS' : rec.verdict ? 'PARCIAL' : 'SIN DATOS',
      lines: [['Veredicto del servidor', rec.verdict || 'SIN DATOS'], ...(rec.next_steps || []).map((x, i) => ['Siguiente paso ' + (i + 1), x]), ['Borradores (listing, PPC, calendario)', 'BORRADOR · no publicado · requiere revisión humana']], missing: [], note: rec.rule });
    return S;
  }
  function summarize(L, P, decs) {
    const steps = stepsOf(L, P), stt = statusOf(L, steps), rec = (L.sections.find((s) => s.id === 'recomendacion') || {});
    const blockers = rec.reasons || [], next = (rec.next_steps || [])[0] || 'SIN DATOS: no hay siguiente paso definido', done = steps.filter((s) => s.state === 'OK').length, part = steps.filter((s) => s.state === 'PARCIAL').length;
    const missing = [].concat(...steps.map((s) => s.missing.map((m) => ({ ...m, step: s.title }))));
    const pend = (decs || []).filter((d) => d.product === P.id && /PEND/i.test(d.status || 'PENDIENTE'));
    const concl = stt.v === 'SIN DATOS' ? P.name + ': todavía no se puede decidir; faltan datos clave.' : stt.v === 'REVISAR' ? P.name + ': revisar antes de decidir; hay bloqueos abiertos.' : stt.v === 'NO GO' ? P.name + ': no lanzar con la economía actual.' : P.name + ': cumple las condiciones para decidir el lanzamiento.';
    return { P, L, steps, status: stt, concl, blockers, next, owner: roleOf(next), done, part, missing, pend, updated: day(P.updated_at) };
  }

  // ---------------------------------------------------------------------------------------------- carga
  const VV = () => (root.V03 && root.V03.V) || {}, api = (m, p, b) => root.V03.api(m, p, b);
  const NS = () => (root.NAV6 && root.NAV6.state) || { mode: 'real' }, STG = () => !!$('#envBanner'), isDemo = () => NS().mode === 'demo';
  const kind = () => (isDemo() || STG() ? 'DEMO' : 'REAL');
  const badge = (k) => `<span class="h2b h2b-${k === 'REAL' ? 'real' : k === 'DEMO' ? 'demo' : 'nd'}">${esc(k)}</span>`;
  const SC = { 'GO': 'go', 'REVISAR': 'rev', 'NO GO': 'nogo', 'SIN DATOS': 'nd', OK: 'go', PARCIAL: 'rev' };
  let D = null, SEL = '', stamp = 0, loading = null;
  async function load() {
    if (D && D.mode === NS().mode && Date.now() - stamp < 3000) return D;
    if (loading) return loading;
    loading = (async () => {
      const logged = !!VV().user, demoOnly = isDemo() && !STG();
      if (!logged || demoOnly) { D = { mode: NS().mode, logged, demoOnly, items: [] }; stamp = Date.now(); return D; }
      const g = async (p) => { try { const r = await api('GET', p); return r.ok ? r.j : null; } catch (e) { return null; } };
      const [cat, dec] = await Promise.all([g('/api/catalog'), g('/api/v06/decisions')]);
      const prods = cat ? cat.products.filter((p) => !p.archived) : [];
      const ls = await Promise.all(prods.map((p) => g('/api/v06/launch?product=' + encodeURIComponent(p.id))));
      const items = prods.map((p, i) => (ls[i] ? summarize(ls[i], p, dec ? dec.decisions : []) : null)).filter(Boolean);
      D = { mode: NS().mode, logged, demoOnly, items, failed: prods.length - items.length }; stamp = Date.now(); return D;
    })();
    try { return await loading; } finally { loading = null; }
  }

  // ---------------------------------------------------------------------------------------------- pintado
  const chip = (v) => `<span class="lzst lzst-${SC[v] || 'nd'}">${esc(v)}</span>`;
  const sk = (s) => (s.state === 'SIN DATOS' ? 'SIN DATOS' : kind());
  function cardHtml(x, sel) {
    const top = x.blockers.slice(0, 2);
    return `<article class="h2c lzc ${sel ? 'on' : ''}" data-lz-card="${esc(x.P.id)}">
      <h3>${esc(x.P.name)} ${chip(x.status.v)}</h3><p class="lzconc">${esc(x.concl)}</p>
      <dl class="lzdl"><dt>Bloqueos críticos</dt><dd>${top.length ? `<ul class="lzul">${top.map((b) => `<li>${esc(b)}</li>`).join('')}</ul>${x.blockers.length > 2 ? `<small>+${x.blockers.length - 2} más en «Decisión»</small>` : ''}` : 'Ninguno registrado'}</dd>
        <dt>Próxima acción</dt><dd>${esc(x.next)}</dd><dt>Responsable</dt><dd>${esc(x.owner)}</dd>
        <dt>Progreso del expediente</dt><dd><span class="lzbar" role="img" aria-label="${x.done} de 10 pasos completos"><i style="width:${x.done * 10}%"></i><b>${x.done}/10</b></span> ${x.done} de 10 completos · ${x.part} parciales · ${10 - x.done - x.part} sin datos</dd>
        <dt>Última actualización</dt><dd>${esc(x.updated)}</dd></dl>
      <button class="btn lzopen" data-lz-open="${esc(x.P.id)}" aria-pressed="${sel ? 'true' : 'false'}">${sel ? 'Expediente abierto ↓' : 'Abrir expediente guiado'}</button></article>`;
  }
  function stepHtml(s) {
    const dl = `<dl class="lzdl">${s.lines.map((l) => `<dt>${esc(l[0])}</dt><dd>${esc(l[1])}</dd>`).join('')}</dl>`;
    const cards = (s.cards || []).length ? `<ul class="lzul lzcards">${s.cards.map((c) => `<li><b>${esc(c.t)}</b><br><small>${esc(c.d)}</small></li>`).join('')}</ul>` : '';
    const ms = s.missing.length ? `<p class="lzmiss"><b>Falta y quién lo aporta</b></p><ul class="lzul">${s.missing.map((m) => `<li>${esc(m.what)} → <i>${esc(m.who)}</i></li>`).join('')}</ul>` : '';
    return `<details class="lzstep" data-lz-step="${s.id}"><summary><span class="lzn">${s.n}</span> ${esc(s.title)} ${chip(s.state)} ${badge(sk(s))}</summary><div>${dl}${cards}${ms}${s.note ? `<p class="h2note">${esc(s.note)}</p>` : ''}</div></details>`;
  }
  function detailHtml(x) {
    const mfs = x.missing.slice(0, 12);
    return `<section class="lzdet" data-lz-detail="${esc(x.P.id)}">
      <article class="h2c lzl1" data-lz-level="1"><h3>1 · Conclusión · ${esc(x.P.name)} ${chip(x.status.v)}${x.status.v === 'SIN DATOS' ? '' : ' ' + badge(kind())}</h3><p class="lzconc">${esc(x.concl)}</p><p>${esc(x.status.why)}</p></article>
      <article class="h2c lzl2" data-lz-level="2"><h3>2 · Decisión</h3>
        <dl class="lzdl"><dt>Decisión solicitada</dt><dd>${x.pend.length ? x.pend.map((d) => esc(d.title)).join(' · ') + ' (aprobar o rechazar en Decisiones)' : 'Ninguna decisión pendiente en la bandeja. Siguiente: ' + esc(x.next)}</dd>
          <dt>Qué bloquea el lanzamiento</dt><dd>${x.blockers.length ? `<ul class="lzul">${x.blockers.map((b) => `<li>${esc(b)}</li>`).join('')}</ul>` : 'Nada registrado'}</dd>
          <dt>Próxima acción</dt><dd>${esc(x.next)}</dd><dt>Responsable</dt><dd>${esc(x.owner)}</dd>
          <dt>Datos que faltan</dt><dd>${mfs.length ? `<ul class="lzul">${mfs.map((m) => `<li>${esc(m.what)} <small>(${esc(m.step)})</small> → <i>${esc(m.who)}</i></li>`).join('')}</ul>${x.missing.length > 12 ? `<small>+${x.missing.length - 12} más en Evidencia</small>` : ''}` : 'Ninguno'}</dd></dl>
        <div class="lzdir"><b>Director IA · resumen sin consumo de IA</b><p>${esc(x.P.name)} está en <b>${esc(x.status.v)}</b>. ${x.blockers.length ? 'Lo que lo bloquea: ' + esc(x.blockers.slice(0, 3).join(' ')) : 'No hay bloqueos registrados.'} Siguiente acción: ${esc(x.next)}.</p></div>
        <div class="lzacts"><button class="btn ghost" data-h2go="dec">Ir a Decisiones${x.pend.length ? ' (' + x.pend.length + ')' : ''}</button><button class="btn ghost" data-h2go="dir">Ver Director IA</button><button class="btn ghost" data-h2prod="${esc(x.P.id)}">Ver ficha en Productos</button></div></article>
      <details class="h2det lzl3" id="lzevi" data-lz-level="3"><summary>3 · Evidencia · expediente guiado en 10 pasos</summary><div>${x.steps.map(stepHtml).join('')}</div></details>
      <details class="h2det lzl4" id="lzmet" data-lz-level="4"><summary>4 · Metodología y expediente completo (11 secciones originales)</summary><div id="lzmetbody"><ul class="h2src"><li>El estado sale de reglas fijas sobre los datos del servidor: GO solo con economía positiva, cumplimiento completo y ranking; NO GO solo si la contribución es negativa en todos los países calculados; SIN DATOS si el servidor no puede decidir y no hay economía, benchmark ni cumplimiento; en otro caso REVISAR.</li><li>Fuentes (solo lectura): GET /api/catalog, /api/v06/launch, /api/v06/decisions. No se ejecuta Keepa, IA de pago, publicación ni acción comercial.</li><li>Los responsables son roles propuestos por regla; el sistema no tiene asignación de personas.</li></ul><div id="lzlegacy"></div></div></details></section>`;
  }
  function html(d) {
    if (!d.logged) return '<section class="h2head"><h2>Lanzamientos ' + badge('SIN DATOS') + '</h2><p class="h2empty">Inicia sesión para ver los lanzamientos.</p></section>';
    if (d.demoOnly) return '<section class="h2head"><h2>Lanzamientos ' + badge('SIN DATOS') + '</h2><p class="h2empty">Modo DATOS DEMO/SINTÉTICOS: no hay lanzamientos demo y no se mezclan con los reales.</p></section>';
    if (!d.items.length) return '<section class="h2head"><h2>Lanzamientos ' + badge('SIN DATOS') + '</h2><p class="h2empty">No hay productos en el catálogo' + (d.failed ? ' (' + d.failed + ' no se pudieron leer)' : '') + '.</p></section>';
    if (!d.items.find((x) => x.P.id === SEL)) SEL = d.items[0].P.id;
    const cur = d.items.find((x) => x.P.id === SEL), cnt = (v) => d.items.filter((x) => x.status.v === v).length;
    return `<section class="h2head"><h2>Lanzamientos ${badge(kind())}</h2><p>${d.items.length} lanzamientos · ${cnt('GO')} GO · ${cnt('REVISAR')} REVISAR · ${cnt('NO GO')} NO GO · ${cnt('SIN DATOS')} SIN DATOS</p></section>
      <section class="lzgrid">${d.items.map((x) => cardHtml(x, x.P.id === SEL)).join('')}</section>${detailHtml(cur)}`;
  }
  function ensure() {
    let h = $('#lanz2'); if (h) return h;
    const tab = $('#tab-lanz'); if (!tab) return null;
    h = document.createElement('div'); h.id = 'lanz2'; h.className = 'h2root lz'; tab.insertBefore(h, tab.firstChild); return h;
  }
  const openState = () => $$('#lanz2 details[open]').map((e) => e.id || e.dataset.lzStep).filter(Boolean);
  async function render() {
    const h = ensure(); if (!h) return; const d = await load(), keep = openState(), lg = $('#v6lanz');
    if (lg) $('#tab-lanz').appendChild(lg);   // se saca antes de repintar para no destruir la pantalla original
    h.innerHTML = html(d); const slot = $('#lzlegacy'); if (lg && slot) slot.appendChild(lg);
    else if (lg && !slot && lg.parentElement !== $('#tab-lanz')) $('#tab-lanz').appendChild(lg);   // sin lista: el original queda accesible
    keep.forEach((k) => { const e = $('#' + k, h) || $('[data-lz-step="' + k + '"]', h); if (e) e.open = true; });
  }
  async function select(pid) {
    SEL = pid; if (root.V06 && root.V06.state) { root.V06.state.pid = pid; try { root.V06.render(); } catch (e) { /* ignorar */ } }
    await render(); const dt = $('#lanz2 .lzdet'); if (dt && root.matchMedia('(max-width: 760px)').matches) dt.scrollIntoView({ block: 'start' });
  }
  function onShow(sec) { if (sec !== 'lanz' || NS().sub > 0) return; D = null; if (root.scrollX) root.scrollTo(0, root.scrollY); render(); }
  if (new URLSearchParams(location.search).get('legacy') === '1') return;
  document.addEventListener('DOMContentLoaded', () => {
    ensure();
    document.addEventListener('click', (e) => { const o = e.target.closest('[data-lz-open]'); if (o) select(o.dataset.lzOpen); });
    setInterval(() => { const u = VV().user || null; if (u !== (onShow.u || null)) { onShow.u = u; D = null; if (NS().sec === 'lanz') render(); } }, 700);
  });
  root.LANZ2 = { onShow, render, _statusOf: statusOf, _stepsOf: stepsOf, _summarize: summarize, _roleOf: roleOf };
})(self);
