/* Fase 4 · C — ADMINISTRACIÓN unificada: Aprobaciones, Conexiones, Historial y Auditoría en una sola pantalla.
   Primer nivel = operación diaria (qué hay que hacer hoy, integridad de la auditoría, estado de conexiones). Segundo nivel plegado = configuración técnica.
   Solo lee GET existentes. Las pantallas originales (con todas sus acciones, trazabilidad y seguridad) se conservan intactas dentro de los bloques plegados:
   el servidor sigue rechazando con 403 cualquier escritura del rol viewer; aquí no se añade ninguna acción de escritura. */
(function (root) {
  'use strict';
  if (new URLSearchParams(location.search).get('legacy') === '1') return;
  const X = root.EX, { $, $$, esc, badge, tile, fold } = X;
  let D = null;
  const LAB = { 'sp-api': 'Amazon SP-API', ads: 'Amazon Ads API', keepa: 'Keepa', helium10: 'Helium 10' };
  async function load() {
    const logged = !!X.VV().user, acc = X.VV().account;
    const [st, cn, au, dec] = await Promise.all([logged ? X.get('/api/status') : null, logged ? X.get('/api/v06/connections') : null, logged && acc ? X.get('/api/audit?account=' + encodeURIComponent(acc)) : null, logged ? X.get('/api/v06/decisions') : null]);
    D = { logged, st, cn, au, dec: dec ? dec.decisions : [], local: $$('#apList .ap').filter((e) => $('[data-a="ok"]', e)).length };
    return D;
  }
  /* lógica pura */
  const connState = (c) => (c.enabled ? 'HABILITADO' : 'DESHABILITADO (por defecto)');
  function todo(d) {
    const out = []; if (d.dec.length) out.push(`${d.dec.length} ${d.dec.length === 1 ? 'decisión pendiente' : 'decisiones pendientes'} de aprobar (Decisiones)`);
    if (d.local) out.push(`${d.local} ${d.local === 1 ? 'propuesta local pendiente' : 'propuestas locales pendientes'} (solo registro)`);
    if (d.au && d.au.chain && !d.au.chain.ok) out.push('La cadena de auditoría está ROTA: revisar de inmediato');
    return out;
  }
  function top(d) {
    if (!d.logged) return '<section class="h2head"><h2>Administración ' + badge('SIN DATOS') + '</h2></section><article class="h2c"><p>Inicia sesión para ver la administración.</p></article>';
    const k = X.kind(), ch = d.au && d.au.chain, conns = d.st ? d.st.connectors : [], act = conns.filter((c) => c.enabled).length, td = todo(d);
    const ro = X.VV().viewer ? '<p class="h2note x4ro"><b>Solo lectura:</b> tu rol (viewer) puede consultar, pero el servidor rechaza cualquier cambio.</p>' : '';
    return `<section class="h2head"><h2>Administración ${badge(k)}</h2>${ro}</section>
      <div class="x4tiles">${tile('Por hacer hoy', String(td.length), k, td.length ? 'asuntos pendientes' : 'nada pendiente')}${tile('Decisiones', String(d.dec.length), k, 'pendientes de aprobar')}
      ${tile('Auditoría', ch ? (ch.ok ? '✔ íntegra' : '✘ ROTA') : null, k, ch ? ch.entries + ' entradas encadenadas' : 'sin acceso al registro')}${tile('Conexiones activas', conns.length ? `${act} de ${conns.length}` : null, k, act ? 'habilitadas' : 'todas deshabilitadas por defecto')}</div>
      <article class="h2c"><h3>Operación diaria</h3>${td.length ? `<ul class="x4list">${td.map((t) => `<li class="x4row">${esc(t)}</li>`).join('')}</ul><button type="button" class="h2btn ro-ok" data-h2go="dec">Ir a Decisiones</button>` : '<p>No hay nada pendiente: sin decisiones por aprobar y con la auditoría íntegra.</p>'}</article>`;
  }
  function audit(d) {
    const a = d.au; if (!a) return '<p class="h2note">SIN DATOS: no se pudo leer el registro de auditoría.</p>';
    return `<p class="h2note">Cadena de hashes: ${a.chain && a.chain.ok ? '✔ íntegra' : '✘ ROTA'} · ${a.chain ? a.chain.entries : 0} entradas. Últimos eventos:</p><ul class="x4list">${(a.audit || []).slice(0, 8).map((e) => `<li class="x4row"><b>${esc(e.action)}</b> <span>${esc(e.actor)} · ${esc(String(e.ts).slice(0, 16).replace('T', ' '))}</span></li>`).join('') || '<li class="x4row nd">SIN DATOS</li>'}</ul>`;
  }
  function conns(d) {
    if (!d.st) return '<p class="h2note">SIN DATOS: no se pudo leer el estado de las conexiones.</p>';
    const cn = (d.cn && d.cn.rows) || [];
    return `<ul class="x4list">${d.st.connectors.map((c) => `<li class="x4conn"><b>${esc(LAB[c.id] || c.label)}</b> <span class="x4cs">${esc(connState(c))}</span><small>${c.enabled ? '' : 'Faltan variables: ' + esc((c.missing || []).join(', ')) + ' · '}${esc(c.note || '')}</small></li>`).join('')}</ul>
      ${cn.length ? `<h4 class="x4h4">Estado verificado por fuente</h4><ul class="x4list">${cn.map((r) => `<li class="x4row"><b>${esc(r.name)}</b> <span>${esc(r.state)}</span></li>`).join('')}</ul>` : ''}`;
  }
  function approvals(d) {
    return `<p class="h2note">Las decisiones del servidor (nivel N3: gasto Keepa, IA de pago, publicación, precios, campañas) se aprueban en <b>Decisiones</b>. Aquí queda la cola local de propuestas (solo registro: no ejecuta nada en Amazon).</p><button type="button" class="h2btn ghost ro-ok" data-h2go="dec">Ir a Decisiones</button>`;
  }
  function moveLegacy() {
    const slots = { hist: '#adm2histx', conn: '#adm2connx', apr: '#adm2aprx' };
    const mv = (sel, slot) => { const e = $(sel), s = $(slot); if (e && s && e.parentElement !== s) s.appendChild(e); };
    mv('#histRoot', slots.hist); mv('#estadoRoot', slots.conn); const ap = $('#apList'); if (ap) mv('#tab-aprob > article', slots.apr);
  }
  function ensure() {
    let h = $('#adm2'); if (h) return h; const tab = $('#tab-hist'); if (!tab) return null;
    h = document.createElement('div'); h.id = 'adm2'; h.className = 'h2root x4'; tab.insertBefore(h, tab.firstChild);
    h.innerHTML = '<div id="adm2top"></div>'
      + fold('adm2apr', 'Aprobaciones', '<div id="adm2aprb"></div><details class="h2det x4in"><summary>Cola local de propuestas</summary><div id="adm2aprx"></div></details>')
      + fold('adm2hist', 'Historial y auditoría', '<div id="adm2histb"></div><details class="h2det x4in"><summary>Registro completo (consultas, ejecuciones de IA, aprobaciones, auditoría)</summary><div id="adm2histx"></div></details>')
      + fold('adm2conn', 'Configuración técnica · Conexiones', '<div id="adm2connb"></div><details class="h2det x4in"><summary>Matriz de conexiones y bloqueos (detalle técnico)</summary><div id="adm2connx"></div></details>');
    moveLegacy(); return h;
  }
  async function render() {
    ensure(); const click = (t) => { const b = $(`#tabs button[data-tab="${t}"]`); if (b) b.click(); };
    click('aprob'); click('estado'); click('hist'); moveLegacy();   // las tres pantallas originales se refrescan y quedan dentro de los bloques plegados; la última activa es la que aloja esta pantalla
    const d = await load(); $('#adm2top').innerHTML = top(d); $('#adm2histb').innerHTML = audit(d); $('#adm2connb').innerHTML = conns(d); $('#adm2aprb').innerHTML = approvals(d);
  }
  function onShow(sec) { if (sec === 'adm' && !(X.NS().sub > 0)) render(); }   // sub 1 = Laboratorio DEMO (pantalla heredada «panel»)
  document.addEventListener('DOMContentLoaded', () => { ensure(); setInterval(() => { const u = X.VV().user || null; if (u !== onShow.u) { onShow.u = u; if (X.NS().sec === 'adm' && !(X.NS().sub > 0)) render(); } }, 700); });
  root.ADM2 = { onShow, render, _todo: todo, _connState: connState };
})(self);
