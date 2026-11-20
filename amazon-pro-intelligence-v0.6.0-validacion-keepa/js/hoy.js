/* P0 · Fase 2 — HOY ejecutivo, bandeja unificada de DECISIONES y DIRECTOR IA simplificado.
   Capa de PRESENTACIÓN: solo lee endpoints GET que ya existen (home, decisions, catalog, k4/centro, k4/seguimientos, demo). No cambia API, cálculos, datos ni seguridad.
   Nada se inventa: lo ausente se muestra SIN DATOS / NO DETERMINABLE (nunca 0). Cada bloque indica REAL, DEMO o SIN DATOS.
   Lo técnico (rutas /api, fuentes, modelos, tokens, llamadas) y la trazabilidad pasan a segundo nivel (bloques plegados «Evidencia» y «Metodología»).
   ?legacy=1 conserva la pantalla antigua (transitorio: docs/p0_hoy/PLAN_RETIRADA_LEGACY.md). */
(function (root) {
  'use strict';
  if (new URLSearchParams(location.search).get('legacy') === '1') { document.addEventListener('DOMContentLoaded', () => { const b = document.querySelector('#tabs [data-tab=decisiones]'), m = document.getElementById('tab-decisiones'); if (b) b.remove(); if (m) m.remove(); }); return; }
  const $ = (s, r) => (r || document).querySelector(s), $$ = (s, r) => [...(r || document).querySelectorAll(s)];
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const VV = () => (root.V03 && root.V03.V) || {};
  const api = (m, p, b) => root.V03.api(m, p, b);
  const NS = () => (root.NAV6 && root.NAV6.state) || { mode: 'real' };
  const STG = () => !!$('#envBanner');
  const isDemo = () => NS().mode === 'demo';
  const useReal = () => !isDemo() || STG();            // en DEMO fuera de staging jamás se consultan ni muestran datos reales
  const eur = (x) => Number(x).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €';
  const WEIGHT = { 'CRÍTICA': 4, ALTA: 3, MEDIA: 2, 'NO CLASIFICADA': 2, BAJA: 1 };
  const LVL = { 'CRÍTICO': 'CRÍTICA', CRITICO: 'CRÍTICA', ALTO: 'ALTA', MEDIO: 'MEDIA', BAJO: 'BAJA' };
  const badge = (k) => `<span class="h2b h2b-${k === 'REAL' ? 'real' : k === 'DEMO' ? 'demo' : 'nd'}">${esc(k)}</span>`;
  const dataKind = () => (isDemo() || STG() ? 'DEMO' : 'REAL');
  const plain = (t) => String(t || '').replace(/\(consume tokens Keepa[^)]*\)/i, '(gasto Keepa: requiere aprobación)').replace(/tokens?\s+Keepa/ig, 'gasto Keepa');   // lo técnico va a Metodología
  const day = (s) => (s ? String(s).slice(0, 10) : '—');

  // ---------------------------------------------------------------------------------------------- carga (solo GET existentes)
  let D = null, stamp = 0, loading = null, CAT = [];
  async function load(force) {
    if (!force && D && D.mode === NS().mode && Date.now() - stamp < 4000) return D;
    if (loading) return loading;
    loading = (async () => {
      const g = async (p) => { try { const r = await api('GET', p); return r.ok ? r.j : null; } catch (e) { return null; } };
      const real = useReal(), logged = !!VV().user;
      const [home, decs, cat, k4, seg, dm] = await Promise.all([
        real && logged ? g('/api/v06/home') : null, real && logged ? g('/api/v06/decisions') : null, real && logged ? g('/api/catalog') : null,
        real && logged ? g('/api/k4/centro') : null, real && logged ? g('/api/k4/seguimientos') : null, isDemo() ? g('/api/v06/demo') : null]);
      D = { mode: NS().mode, home, decs: decs ? decs.decisions : [], cat: cat ? cat.products : [], k4, seg: seg ? seg.seguimientos : [], demo: dm, logged, real };
      D.local = localProposals(); D.list = unify(D); D.risks = risksOf(D); D.prios = priorities(D); stamp = Date.now(); if (D.cat.length) CAT = D.cat;
      const chip = $('#decN'); if (chip) chip.textContent = String(D.logged && D.real ? pendingOnes(D).length : 0);   // el chip siempre refleja la misma bandeja
      return D;
    })();
    try { return await loading; } finally { loading = null; }
  }
  function localProposals() {   // cola local (V0.3): se lee del DOM del panel de aprobaciones; solo registro, no ejecuta nada
    return $$('#apList .ap').map((el) => { const b = $('b', el); const pend = !!$('[data-a="ok"]', el); return { title: b ? b.textContent : '', detail: ($('.muted', el) || {}).textContent || '', pend }; });
  }
  const risksOf = (d) => (d.home && d.home.risks ? d.home.risks : []);
  function riskCounts(rs) {
    const c = { 'CRÍTICA': 0, ALTA: 0, MEDIA: 0, BAJA: 0 }; rs.forEach((r) => { const k = LVL[String(r.level).toUpperCase()] || 'MEDIA'; c[k]++; }); return c;
  }
  const plural = (n, s, p) => (n === 1 ? s : p);
  function riskLine(rs) {
    const c = riskCounts(rs), n = rs.length;
    return `${n} ${plural(n, 'riesgo abierto', 'riesgos abiertos')}: ${c['CRÍTICA']} ${plural(c['CRÍTICA'], 'crítico', 'críticos')} · ${c.ALTA} ${plural(c.ALTA, 'alto', 'altos')} · ${c.MEDIA} ${plural(c.MEDIA, 'medio', 'medios')} · ${c.BAJA} ${plural(c.BAJA, 'bajo', 'bajos')}`;
  }
  function actionFor(r) {
    const t = String(r.risk || '');
    if (/regulatori/i.test(t)) return 'Aportar PIF/CPSR/etiquetado y reflejarlo en la ficha del producto';
    if (/claim/i.test(t)) return 'Aportar evidencia de cada claim o retirarlo del listing';
    if (/coste/i.test(t)) return 'Documentar los costes con fuente y fecha en la ficha del producto';
    return 'Revisar el riesgo y registrar la decisión en la ficha';
  }
  const impactFor = (r) => {
    const t = String(r.risk || '');
    const why = /regulatori/i.test(t) ? 'bloquea la publicación; sin ventas ni costes no se puede traducir a euros' : /claim/i.test(t) ? 'impide usar esos claims; sin ventas no se puede traducir a euros' : /coste/i.test(t) ? 'sin costes no hay contribución calculable' : 'sin datos suficientes';
    return `NO DETERMINABLE · ${why}`;
  };

  // ---------------------------------------------------------------------------------------------- bandeja unificada
  function unify(d) {
    const out = [], pn = (id) => ((d.cat || []).find((p) => p.id === id) || {}).name || id || null;
    (d.decs || []).forEach((x) => {
      const keepa = /keepa/i.test(x.kind || '') || /keepa/i.test(x.title || '');
      out.push({ key: 's' + x.id, origin: 'Servidor · aprobación', cls: 'server', id: x.id, product: x.product, productName: pn(x.product), title: x.title, priority: x.level === 'N4' ? 'CRÍTICA' : 'ALTA',
        deadline: 'SIN FECHA LÍMITE DEFINIDA', since: day(x.requested_at), impact: keepa ? 'Gasto de tokens Keepa · importe en € NO DETERMINABLE (el sistema no lo calcula)' : 'NO DETERMINABLE',
        owner: 'Aprobador (rol approver o admin)', evidence: (x.items || []).map((i) => i.motivo).filter(Boolean).concat(['Nivel ' + (x.level || 'N3') + ': requiere aprobación humana']), state: 'PENDIENTE DE APROBACIÓN',
        action: keepa ? 'Aprobar solo si el presupuesto Keepa está autorizado; hasta entonces la consulta no se ejecuta' : 'Revisar la evidencia y aprobar o rechazar', decidable: true, kind: 'Regla determinista (política N3)', pending: true });
    });
    const k = d.k4;
    if (k && k.decisiones) k.decisiones.forEach((x, i) => out.push({ key: 'k' + i, origin: 'K4 · consejero', cls: 'k4', product: (k.filtros || {}).producto, productName: pn((k.filtros || {}).producto), title: x.title, priority: x.level === 'N4' ? 'CRÍTICA' : 'ALTA',
      deadline: 'SIN FECHA LÍMITE DEFINIDA', impact: 'NO DETERMINABLE', owner: 'Una persona (aprobador)', evidence: ['Dictamen K4: ' + ((k.dictamen || {}).nombre || 'SIN DATOS')], state: 'PENDIENTE', action: (k.dictamen || {}).accion || 'Revisar en Productos › Precio', decidable: false, kind: 'Cálculo (motor de precio)', pending: true }));
    (d.local || []).forEach((x, i) => out.push({ key: 'l' + i, origin: 'Cola local de propuestas', cls: 'local', product: null, productName: null, title: x.title, priority: 'NO CLASIFICADA', deadline: 'SIN FECHA LÍMITE DEFINIDA', impact: 'NO DETERMINABLE',
      owner: 'Sin asignar', evidence: [x.detail || 'Sin detalle'], state: x.pend ? 'PENDIENTE (solo registro: no se ejecuta ningún cambio)' : 'RESUELTA', action: 'Revisar en Administración › Aprobaciones', decidable: false, kind: 'Regla determinista', pending: x.pend }));
    (d.home ? d.home.risks || [] : []).forEach((r, i) => out.push({ key: 'r' + i, origin: 'Regla sobre la ficha', cls: 'rule', product: r.product, productName: r.name, title: r.risk, priority: LVL[String(r.level).toUpperCase()] || 'MEDIA',
      deadline: 'SIN FECHA LÍMITE DEFINIDA', impact: impactFor(r), owner: 'Sin asignar', evidence: [r.why, 'Ficha de ' + r.name + ' (catálogo)'], state: 'ABIERTA', action: actionFor(r), decidable: false, kind: 'Regla determinista', pending: false, rule: true }));
    out.sort((a, b) => (b.pending - a.pending) || (WEIGHT[b.priority] - WEIGHT[a.priority]));
    return out;
  }
  const pendingOnes = (d) => (d.list || []).filter((x) => x.pending);
  function priorities(d) {   // máx. 3: riesgos agrupados por tipo (gravedad, nº de productos) + hueco de datos de ventas
    const g = {}; risksOf(d).forEach((r) => { const k = String(r.risk).replace(/^\d+ /, '#'); const w = LVL[String(r.level).toUpperCase()] || 'MEDIA'; (g[k] = g[k] || { risk: r.risk, level: w, names: [], pids: [] }); g[k].names.push(r.name); g[k].pids.push(r.product); if (WEIGHT[w] > WEIGHT[g[k].level]) g[k].level = w; });
    const items = Object.values(g).map((x) => ({ title: actionFor({ risk: x.risk }), why: x.risk, level: x.level, products: [...new Set(x.names)], pids: [...new Set(x.pids)] }));
    if (d.real && d.home && !salesOf(d).num) items.push({ title: 'Importar un informe de ventas de Amazon', why: 'Sin ventas importadas no hay ventas, margen ni rentabilidad', level: 'MEDIA', products: [], pids: [] });
    items.sort((a, b) => (WEIGHT[b.level] - WEIGHT[a.level]) || (b.products.length - a.products.length));
    return items.slice(0, 3);
  }

  // ---------------------------------------------------------------------------------------------- datos de ventas / margen / stock
  function salesOf(d) {
    if (isDemo() && d.demo) return { num: d.demo.kpis.ventas, kind: 'DEMO', sub: 'Últimos 30 días · datos sintéticos', margin: d.demo.kpis.margen };
    const k = d.home && (d.home.kpis || []).find((x) => x.id === 'ventas');
    if (k && typeof k.value === 'number') return { num: k.value, kind: 'REAL', sub: k.hint || 'Informes de Amazon importados', margin: null };
    return { num: null, kind: 'SIN DATOS', sub: d.home && d.home.mode === 'PRELANZAMIENTO' ? 'Pre-lanzamiento: todavía no hay ventas importadas' : 'Importa un informe de ventas de Amazon para verlas', margin: null };
  }
  function stockOf(d) {
    const ps = d.cat || []; if (!ps.length) return { kind: 'SIN DATOS', text: 'SIN DATOS de catálogo' };
    const ok = ps.filter((p) => p.stock && p.stock.v != null && /VERIFICADO|DOCUMENTADO/.test(p.stock.status || ''));
    if (!ok.length) return { kind: 'SIN DATOS', text: `Stock verificado: SIN DATOS (0 de ${ps.length} productos)` };
    return { kind: dataKind(), text: `Stock verificado: ${ok.reduce((s, p) => s + p.stock.v, 0)} uds en ${ok.length} de ${ps.length} productos` };
  }

  // ---------------------------------------------------------------------------------------------- HOY
  function situation(d) {
    const nr = d.risks.length, c = riskCounts(d.risks), np = pendingOnes(d).length, sal = salesOf(d);
    if (!d.logged) return { color: 'nd', label: 'SIN DATOS', text: 'Inicia sesión para ver la situación del negocio.', kind: 'SIN DATOS' };
    if (isDemo() && !STG()) return { color: 'nd', label: 'DEMO', text: 'Estás viendo datos DEMO/SINTÉTICOS: no describen el negocio real.', kind: 'DEMO' };
    if (!d.home) return { color: 'nd', label: 'SIN DATOS', text: 'No se pudieron cargar los datos del negocio.', kind: 'SIN DATOS' };
    const pre = d.home.mode === 'PRELANZAMIENTO';
    const color = c['CRÍTICA'] > 0 ? 'rd' : nr + np > 0 ? 'am' : sal.num != null ? 'gr' : 'nd';
    const lab = { rd: 'ACCIÓN URGENTE', am: 'ATENCIÓN', gr: 'SIN INCIDENCIAS', nd: 'SIN DATOS' }[color];
    const parts = [];
    parts.push(pre ? 'Pre-lanzamiento: todavía no hay ventas reales.' : (sal.num != null ? 'Negocio en operación.' : 'Negocio en operación, pero sin ventas importadas.'));
    parts.push(nr ? riskLine(d.risks) + '.' : 'Sin riesgos abiertos con las reglas actuales.');
    parts.push(np ? `${np} ${plural(np, 'decisión pendiente', 'decisiones pendientes')} de una persona.` : 'Ninguna decisión pendiente.');
    return { color, label: lab, text: parts.join(' '), kind: dataKind() };
  }
  function hoyHtml(d) {
    const st = situation(d), sal = salesOf(d), stk = stockOf(d), pend = pendingOnes(d);
    const demoOnly = isDemo() && !STG();
    const valTxt = (n) => (n == null ? '<span class="h2na">SIN DATOS</span>' : `<span class="h2num">${eur(n)}</span>`);
    let margin;
    if (sal.margin != null) margin = `<div class="h2v">${valTxt(sal.margin)}</div><p>${((sal.margin / sal.num) * 100).toFixed(1).replace('.', ',')} % de las ventas · datos sintéticos</p>`;
    else margin = `<div class="h2v"><span class="h2na">${sal.num == null ? 'SIN DATOS' : 'NO DETERMINABLE'}</span></div><p>${sal.num == null ? 'Sin ventas ni costes no hay margen: no es un 0.' : 'El margen real exige costes completos y liquidaciones de Amazon.'}</p>`;
    const mk = sal.kind === 'SIN DATOS' ? 'SIN DATOS' : sal.kind;
    const riskBlock = demoOnly ? '<p class="h2na">SIN DATOS</p><p>El dataset DEMO no incluye stock ni riesgos.</p>' : `<p class="h2stk">${esc(stk.text)}</p><p class="h2risk"><b>${esc(d.risks.length ? riskLine(d.risks) : 'Sin riesgos abiertos con las reglas actuales')}</b></p>`;
    const top = pend.slice(0, 3);
    const decBlock = demoOnly ? '<p class="h2na">SIN DATOS</p><p>El dataset DEMO no tiene decisiones.</p>' : (pend.length ? `<ul class="h2list">${top.map((x) => `<li><b>${esc(x.productName || 'Sin producto')}</b> · ${esc(x.priority)}<br><span>${esc(x.action)}</span></li>`).join('')}</ul>` : '<p>No hay decisiones pendientes de una persona.</p>') + (demoOnly ? '' : `<button type="button" class="h2btn ro-ok" data-h2go="dec">Ver decisiones${pend.length ? ' (' + pend.length + ')' : ''}</button>`);
    const prBlock = demoOnly ? '<p class="h2na">SIN DATOS</p><p>En DEMO no hay prioridades reales.</p>' : (d.prios.length ? `<ol class="h2list">${d.prios.map((p) => `<li><b>${esc(p.title)}</b><br><span>${esc(p.level)} · ${esc(p.products.length ? p.products.join(', ') : 'Todo el negocio')}</span></li>`).join('')}</ol>` : '<p>Sin prioridades: no hay riesgos ni datos faltantes con las reglas actuales.</p>');
    return `<section class="h2sit h2s-${st.color}" aria-label="Situación general"><span class="h2dot" aria-hidden="true"></span><div><h2>Situación general ${badge(st.kind)} <em class="h2lab">${esc(st.label)}</em></h2><p class="h2big">${esc(st.text)}</p></div></section>
      <section class="h2grid"><article class="h2c" data-blk="ventas"><h3>Ventas ${badge(mk)}</h3><div class="h2v">${valTxt(sal.num)}</div><p>${esc(sal.sub)}</p></article>
        <article class="h2c" data-blk="margen"><h3>Margen ${badge(sal.margin != null ? 'DEMO' : 'SIN DATOS')}</h3>${margin}</article>
        <article class="h2c" data-blk="stock"><h3>Stock y riesgos ${badge(demoOnly ? 'SIN DATOS' : (d.home ? dataKind() : 'SIN DATOS'))}</h3>${riskBlock}</article></section>
      <section class="h2two"><article class="h2c" data-blk="decisiones"><h3>Decisiones pendientes ${badge(demoOnly || !d.logged ? 'SIN DATOS' : dataKind())}</h3>${decBlock}</article>
        <article class="h2c" data-blk="prioridades"><h3>Tres prioridades ${badge(demoOnly || !d.logged ? 'SIN DATOS' : dataKind())}</h3>${prBlock}</article></section>`;
  }
  function hoyDetail(d) {
    const rows = [['Ventas', isDemo() ? 'GET /api/v06/demo' : 'GET /api/v06/home (kpis)', salesOf(d).kind], ['Margen', isDemo() ? 'GET /api/v06/demo' : 'GET /api/v06/home (kpis)', salesOf(d).margin != null ? 'DEMO' : 'SIN DATOS'],
      ['Stock', 'GET /api/catalog', stockOf(d).kind], ['Riesgos', 'GET /api/v06/home (risks)', d.home ? dataKind() : 'SIN DATOS'], ['Decisiones', 'GET /api/v06/decisions · GET /api/k4/centro · cola local', d.logged ? dataKind() : 'SIN DATOS']];
    return `<p class="h2note"><b>Evidencia</b> — de dónde sale cada bloque. Solo lectura: no se consulta ninguna fuente de pago ni conector externo.</p><ul class="h2src">${rows.map((r) => `<li><b>${esc(r[0])}</b> · ${esc(r[1])} · ${badge(r[2])}</li>`).join('')}</ul>
      <p class="h2note"><b>Metodología</b> — Situación: rojo si hay riesgos críticos; ámbar si hay riesgos o decisiones abiertos; verde si hay ventas y nada abierto; gris si faltan datos. Prioridades: riesgos agrupados por tipo ordenados por gravedad y nº de productos. Lo ausente nunca se muestra como 0. Debajo, la pantalla de Inicio completa (gráficos, trabajo automático, riesgos por producto).</p>`;
  }

  // ---------------------------------------------------------------------------------------------- DECISIONES
  let FILT = 'pend', RESOLVED = null;
  const decCard = (x) => {
    const v = VV(), canDecide = x.decidable && !v.viewer && ['admin', 'approver'].includes(v.role);
    let btn = '';
    if (x.decidable) {
      if (v.viewer) btn = `<div class="h2act"><button type="button" class="h2btn vro" disabled title="No disponible: usuario de solo lectura">Aprobar</button><button type="button" class="h2btn no vro" disabled title="No disponible: usuario de solo lectura">Rechazar</button><span class="h2lock">No disponible: solo lectura</span></div>`;
      else if (canDecide) btn = `<div class="h2act"><button type="button" class="h2btn" data-h2dec="${x.id}" data-ok="1">Aprobar</button><button type="button" class="h2btn no" data-h2dec="${x.id}" data-ok="0">Rechazar</button></div>`;
      else btn = '<div class="h2act"><span class="h2lock">Solo un aprobador puede decidir</span></div>';
    }
    const link = x.product ? `<button type="button" class="h2btn ghost ro-ok" data-h2prod="${esc(x.product)}">Ir al producto</button>` : '';
    return `<article class="h2dec h2p-${esc(x.priority).replace(/[^A-Z]/g, '').toLowerCase()}" data-dkey="${esc(x.key)}"><header><span class="h2pri">${esc(x.priority)}</span><span class="h2org">${esc(x.origin)}</span></header><h3>${esc(x.title)}</h3>
      <dl><dt>Producto</dt><dd>${esc(x.productName || 'Sin producto asociado')}</dd><dt>Prioridad</dt><dd>${esc(x.priority)}</dd><dt>Fecha límite</dt><dd>${esc(x.deadline)}${x.since ? ' · solicitada ' + esc(x.since) : ''}</dd>
      <dt>Impacto estimado</dt><dd>${esc(x.impact)}</dd><dt>Responsable</dt><dd>${esc(x.owner)}</dd><dt>Evidencia</dt><dd>${(x.evidence || []).map(esc).join('<br>') || 'SIN DATOS'}</dd><dt>Estado</dt><dd>${esc(x.state)}</dd><dt>Acción recomendada</dt><dd><b>${esc(x.action)}</b></dd></dl>${btn}${link}</article>`;
  };
  async function decHtml(d) {
    const F = [['pend', 'Pendientes de ti', pendingOnes(d)], ['regla', 'Sugeridas por reglas', d.list.filter((x) => x.rule)], ['seg', 'En seguimiento', d.seg || []], ['res', 'Resueltas', RESOLVED || []]];
    const bar = F.map((f) => `<button type="button" class="h2tab ro-ok ${f[0] === FILT ? 'on' : ''}" data-h2f="${f[0]}">${f[1]} <b>${f[2].length}</b></button>`).join('');
    const cur = F.find((f) => f[0] === FILT)[2]; let body;
    if (FILT === 'seg') body = cur.length ? cur.map((x) => `<article class="h2dec"><header><span class="h2org">K4 · seguimiento</span></header><h3>${esc(x.accion)}</h3><dl><dt>Producto</dt><dd>${esc(x.producto)} ${esc(x.pais || '')}</dd><dt>Estado</dt><dd>${esc(x.estado)}</dd><dt>Impacto estimado</dt><dd>NO DETERMINABLE</dd><dt>Responsable</dt><dd>Una persona</dd></dl></article>`).join('') : '<p class="h2empty">Sin seguimientos todavía.</p>';
    else if (FILT === 'res') body = cur.length ? cur.map((x) => decCard({ key: 'x' + x.id, origin: 'Servidor · resuelta', product: x.product, productName: x.product, title: x.title, priority: 'ALTA', deadline: 'Resuelta ' + day(x.decided_at), impact: 'NO DETERMINABLE', owner: x.decided_by || '—', evidence: [x.note || 'Registrada en el libro de decisiones'], state: x.status, action: 'Ninguna: ya resuelta (ver Administración › Auditoría)', decidable: false })).join('') : '<p class="h2empty">Todavía no hay decisiones resueltas.</p>';
    else body = cur.length ? cur.map(decCard).join('') : `<p class="h2empty">${FILT === 'pend' ? 'No hay decisiones pendientes de una persona. Nada bloqueado por aprobación.' : 'Sin reglas activas.'}</p>`;
    return `<section class="h2head"><h2>Decisiones ${badge(d.logged ? dataKind() : 'SIN DATOS')}</h2><p>Bandeja única: aprobaciones del servidor, consejero K4, cola local y riesgos detectados por reglas.</p></section><div class="h2tabs" role="tablist">${bar}</div><div class="h2decs">${body}</div>`;
  }
  async function renderDec() {
    const el = $('#dec2'); if (!el) return; const d = await load();
    if (FILT === 'res' && !RESOLVED && d.logged && d.real) { const [a, b] = await Promise.all(['APROBADA', 'RECHAZADA'].map((s) => api('GET', '/api/v06/decisions?status=' + s).then((r) => (r.ok ? r.j.decisions : [])).catch(() => []))); RESOLVED = a.concat(b); }
    el.innerHTML = demoGuard() || await decHtml(d);
  }
  const demoGuard = () => (isDemo() && !STG() ? '<section class="h2head"><h2>Decisiones ' + badge('SIN DATOS') + '</h2><p class="h2empty">Modo DATOS DEMO/SINTÉTICOS: el dataset DEMO no tiene decisiones y no se mezclan con las reales.</p></section>' : '');

  // ---------------------------------------------------------------------------------------------- HOY / DIRECTOR: pintado
  function ensureHoy() {
    let h = $('#hoy2'); if (h) return h;
    const tab = $('#tab-inicio'); if (!tab) return null;
    h = document.createElement('div'); h.id = 'hoy2'; h.className = 'h2root';
    h.innerHTML = '<div id="h2top"></div><details class="h2det" id="h2det"><summary>Evidencia y metodología</summary><div id="h2detbody"></div><div id="h2legacy"></div></details>';
    tab.insertBefore(h, tab.firstChild); const lg = $('#v6inicio'); if (lg) $('#h2legacy').appendChild(lg); return h;
  }
  async function renderHoy() { const h = ensureHoy(); if (!h) return; const d = await load(); $('#h2top').innerHTML = hoyHtml(d); $('#h2detbody').innerHTML = hoyDetail(d); }

  function dirBlocks(d) {
    const sal = salesOf(d), k = d.k4, faltan = k && k.faltantes ? k.faltantes : [], dict = k && k.dictamen;
    const insuf = !d.logged || !d.home || (dict && dict.tipo === 5) || sal.num == null;
    const nr = d.risks.length;
    let concl;
    if (!d.logged) concl = 'No puedo concluir nada: inicia sesión para que el Director lea los datos.';
    else if (isDemo() && !STG()) concl = 'Modo DATOS DEMO/SINTÉTICOS: el Director no emite conclusiones sobre el negocio con datos demo.';
    else {
      const a = [];
      a.push(insuf ? 'Datos insuficientes para recomendar cambios de precio, publicidad o reposición.' : 'Hay datos suficientes para valorar el negocio.');
      if (faltan.length) a.push(`Faltan ${faltan.length} datos clave${dict && dict.tipo === 5 ? ' (dictamen K4: evidencia insuficiente: no se modifica el precio)' : ''}.`);
      a.push(nr ? riskLine(d.risks) + '.' : 'Sin riesgos abiertos con las reglas actuales.');
      concl = a.join(' ');
    }
    const pn = (id) => ((d.cat || []).find((p) => p.id === id) || {}).name || id;
    const fromPend = pendingOnes(d).map((x) => ({ title: x.action, why: plain(x.title), level: x.priority, kind: x.kind, prods: x.product ? [{ id: x.product, name: x.productName || x.product }] : [] }));
    const fromRules = (d.prios || []).map((p) => ({ title: p.title, why: p.why, level: p.level, kind: 'Regla determinista', prods: p.pids.map((id) => ({ id, name: pn(id) })) }));
    const decs = fromPend.concat(fromRules).slice(0, 3);
    return { concl, insuf, decs, faltan };
  }
  function ensureDir() {
    let h = $('#dir2'); if (h) return h;
    const tab = $('#tab-dir'); if (!tab) return null;
    h = document.createElement('div'); h.id = 'dir2'; h.className = 'h2root';
    h.innerHTML = '<div id="d2top"></div><details class="h2det" id="d2evi"><summary>Evidencia</summary><div id="d2evibody"></div></details><details class="h2det" id="d2met"><summary>Metodología</summary><div id="d2metbody"></div><div id="d2legacy"></div></details>';
    tab.insertBefore(h, tab.firstChild); const lg = $('#v6dir'); if (lg) $('#d2legacy').appendChild(lg); return h;
  }
  async function renderDir() {
    const h = ensureDir(); if (!h) return; const d = await load(), b = dirBlocks(d);
    const chip = (t, c) => `<span class="h2kind h2k-${c}">${t}</span>`;
    const kindChip = (k) => (/Cálculo/.test(k) ? chip('Cálculo', 'calc') : chip('Regla determinista', 'rule'));
    $('#d2top').innerHTML = `<section class="h2head"><h2>Director IA ${badge(d.logged ? (isDemo() && !STG() ? 'DEMO' : dataKind()) : 'SIN DATOS')}</h2>
      <p class="h2leg">Cada punto indica cómo se obtuvo: ${chip('Regla determinista', 'rule')} ${chip('Cálculo', 'calc')} ${chip('IA generativa', 'gen')} <small>· la IA generativa no participa en esta conclusión; este panel no ejecuta consultas de pago ni conectores externos.</small></p></section>
      <article class="h2c h2conc ${b.insuf ? 'h2insuf' : ''}"><h3>Conclusión</h3><p class="h2big">${esc(b.concl)}</p>${b.insuf && d.logged ? '<p class="h2insmsg"><b>Datos insuficientes</b> — el Director lo dice expresamente en lugar de estimar.</p>' : ''}</article>
      <article class="h2c"><h3>Decisión recomendada <small>(máx. 3)</small></h3>${b.decs.length ? `<ol class="h2recs">${b.decs.map((x) => `<li><b>${esc(x.title)}</b><br><span>${esc(x.prods.length ? x.prods.map((q) => q.name).join(', ') : 'Sin producto asociado')} · ${esc(x.level)} · ${esc(x.why)}</span><br>${kindChip(x.kind)}${x.prods.map((q) => ` <button type="button" class="h2btn ghost ro-ok" data-h2prod="${esc(q.id)}">Ir al producto afectado: ${esc(q.name)}</button>`).join('')}</li>`).join('')}</ol>` : '<p>No hay decisiones recomendadas: sin riesgos ni aprobaciones pendientes.</p>'}</article>`;
    const evid = [];
    b.decs.forEach((x) => evid.push(`${x.prods.map((q) => q.name).join(', ') || 'General'}: ${x.why}`)); (b.faltan || []).slice(0, 6).forEach((f) => evid.push('Falta: ' + f.dato));
    $('#d2evibody').innerHTML = evid.length ? `<ul class="h2src">${evid.map((e) => `<li>${esc(e)}</li>`).join('')}</ul>` : '<p class="h2note">Sin evidencia que mostrar: no hay datos.</p>';
    $('#d2metbody').innerHTML = `<p class="h2note">La conclusión se compone en el navegador a partir de datos ya existentes (GET /api/v06/home, /api/v06/decisions, /api/k4/centro). Las prioridades siguen la misma regla que HOY. Los modelos, tokens, llamadas y rutas se muestran solo aquí, debajo.</p>`;
  }

  // ---------------------------------------------------------------------------------------------- navegación al producto
  function goProduct(pid) {
    if (root.V06 && root.V06.state) root.V06.state.pid = pid;
    root.NAV6.go('prod', 0);
    const name = CAT.find((p) => p.id === pid);
    let n = 0; const t = setInterval(() => {
      const card = $$('#tab-prod .v6prod').find((c) => name && c.textContent.indexOf(name.name) >= 0);
      if (card) { clearInterval(t); $$('#tab-prod .v6prod.h2hl').forEach((c) => c.classList.remove('h2hl')); card.classList.add('h2hl'); card.scrollIntoView({ block: 'center' }); } else if (++n > 40) clearInterval(t);
    }, 150);
  }

  // ---------------------------------------------------------------------------------------------- eventos y ciclo
  async function pendingCount() { const d = await load(); return d.logged && d.real ? pendingOnes(d).length : 0; }
  let cur = 'hoy', lastUser = null;
  function onShow(sec) { cur = sec; D = null;   // cada vez que se muestra una pantalla se relee (datos y modo REAL/DEMO frescos)
    if (sec === 'hoy') renderHoy(); else if (sec === 'dec') renderDec(); else if (sec === 'dir') renderDir(); }
  document.addEventListener('DOMContentLoaded', () => {
    ensureHoy(); ensureDir();
    document.addEventListener('click', async (e) => {
      const g = e.target.closest('[data-h2go]'); if (g) { root.NAV6.go(g.dataset.h2go, 0); return; }
      const p = e.target.closest('[data-h2prod]'); if (p) { goProduct(p.dataset.h2prod); return; }
      const f = e.target.closest('[data-h2f]'); if (f) { FILT = f.dataset.h2f; RESOLVED = null; renderDec(); return; }
      const dc = e.target.closest('[data-h2dec]'); if (dc && !dc.disabled) {
        const r = await api('POST', '/api/v06/decide', { id: Number(dc.dataset.h2dec), approve: dc.dataset.ok === '1' });
        if (r.ok && dc.dataset.ok === '1') await api('POST', '/api/v06/run', {});
        D = null; await renderDec(); const m = $('#dec2 .h2head p'); if (m) m.textContent = r.ok ? (r.j.nota || 'Decisión registrada.') : 'No se pudo registrar: ' + ((r.j && r.j.error) || 'error'); return;
      }
    });
    setInterval(() => { const u = VV().user || null; if (u !== lastUser) { lastUser = u; D = null; RESOLVED = null; onShow(cur); } }, 700);
    setInterval(() => { if (document.visibilityState === 'visible') { D = null; onShow(cur); } }, 20000);
  });
  root.HOY2 = { onShow, pendingCount, refresh: () => { D = null; return load(true); }, riskLine, riskCounts };
})(self);
