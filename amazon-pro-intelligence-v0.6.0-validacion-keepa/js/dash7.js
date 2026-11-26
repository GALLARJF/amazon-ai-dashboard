/* Rediseño global · fase 1 — Dashboard AHT simplificado (solo lectura, sin menú lateral). Cabecera: marca AHT (vuelve al dashboard), Benchmarking, Director IA, sesión.
   Datos: DEMO aislada y rotulada (js/dash7calc.js); en modo DATOS DE AHT sin fuente conectada → «Sin datos». No escribe, no llama a conectores, no gasta cuota. */
(function (root) {
  'use strict';
  const $ = (s, r) => (r || document).querySelector(s), $$ = (s, r) => [...(r || document).querySelectorAll(s)];
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const D = () => root.D7C, F = { line: 'all', sub: 'all', region: 'all', country: 'all', period: 'mes' };
  const nf = (x, d) => (x == null ? 'Sin datos' : x.toLocaleString('es-ES', { minimumFractionDigits: d, maximumFractionDigits: d }));
  const eur = (x) => (x == null ? 'Sin datos' : nf(x, 2) + ' €'), pc = (x) => (x == null ? 'Sin datos' : nf(x, 2) + ' %');
  const demo = () => !root.NAV6 || root.NAV6.state.mode === 'demo';
  const COL = ['#18e6ff', '#ffb02e', '#b968ff', '#ff4fd8', '#37e08a'];

  const L6 = new URLSearchParams(location.search).get('shell') === '6';   // transición: la interfaz anterior sigue disponible (?shell=6), nada se borra
  function header() {
    const top = $('header.top'); if (!top || $('#hdr7') || L6) return;
    const h = document.createElement('header'); h.id = 'hdr7'; h.className = 'hdr7';
    h.innerHTML = `<button type="button" id="h7Brand" class="h7brand ro-ok" aria-label="AHT · volver al dashboard"><b>AHT</b><span>AMAZON PRO<br><em>INTELLIGENCE GLOBAL</em></span></button>
      <nav class="h7nav" aria-label="Principal"><button type="button" id="h7Bench" class="ro-ok h7b" data-go="bench">Benchmarking</button><button type="button" id="h7Dir" class="ro-ok h7b" data-go="dir">Director IA</button></nav><div id="h7Sess" class="h7sess"></div>`;
    top.insertAdjacentElement('beforebegin', h);
    const sess = $('#sess'); if (sess) $('#h7Sess').appendChild(sess);
    document.body.classList.add('shell7');
    h.addEventListener('click', (e) => { const b = e.target.closest('#h7Brand, [data-go]'); if (!b) return; root.NAV6.go(b.id === 'h7Brand' ? 'hoy' : b.dataset.go, 0); });
  }
  function select(id, label, opts, val, extra) { return `<label class="f7" ${extra || ''}><span>${label}</span><select id="${id}" class="ro-ok" data-view-filter aria-label="${label}">${opts.map(([v, l]) => `<option value="${v}" ${v === val ? 'selected' : ''}>${esc(l)}</option>`).join('')}</select></label>`; }
  function filtersHtml() {
    const d = D(), ln = d.LINES.find((x) => x.id === F.line), rg = d.REGIONS.find((x) => x.id === F.region);
    const lopts = [['all', 'Consolidado AHT'], ...d.LINES.map((x) => [x.id, x.l])];
    const ropts = [['all', 'Todas'], ...d.REGIONS.map((x) => [x.id, x.l])];
    const copts = [['all', 'Todos'], ...(rg ? rg.countries : d.REGIONS.flatMap((x) => x.countries)).map((c) => [c.id, c.l])];
    return `<div class="filt7">${select('f7Line', 'Línea AHT', lopts, F.line)}${ln && ln.subs ? select('f7Sub', 'PHIVITAL', [['all', 'Todas'], ...ln.subs.map((s) => [s.id, s.l])], F.sub) : ''}${select('f7Reg', 'Región', ropts, F.region)}${select('f7Cty', 'País', copts, F.country)}
      <div class="per7" role="group" aria-label="Periodo">${d.PERIODS.map((p) => `<button type="button" class="ro-ok ${p.id === F.period ? 'on' : ''}" data-per="${p.id}" aria-pressed="${p.id === F.period}">${p.l}</button>`).join('')}</div></div>`;
  }
  const kpi = (cls, t, v, s) => `<article class="k7 ${cls}"><h4>${t}</h4><div class="v7">${v}</div><small>${s || ''}</small></article>`;
  function donut(c) {
    if (!c.donut.length) return '<p class="muted">Sin datos</p>';
    let a = -Math.PI / 2; const R = 70, r = 44, cx = 90, cy = 90;
    const segs = c.donut.map((s, i) => { const f = Math.max(0, s.pct) / 100, b = a + f * 2 * Math.PI, big = f > 0.5 ? 1 : 0; const p = (ang, rad) => `${(cx + rad * Math.cos(ang)).toFixed(2)},${(cy + rad * Math.sin(ang)).toFixed(2)}`; const d = `M${p(a, R)} A${R},${R} 0 ${big} 1 ${p(b - 1e-4, R)} L${p(b - 1e-4, r)} A${r},${r} 0 ${big} 0 ${p(a, r)} Z`; a = b; return `<path d="${d}" fill="${COL[i]}"><title>${esc(s.l)}: ${eur(s.eur)} (${pc(s.pct)})</title></path>`; }).join('');
    return `<div class="dn7"><svg viewBox="0 0 180 180" role="img" aria-label="Distribución de ventas netas">${segs}<text x="90" y="86" text-anchor="middle" class="dnt">Netas</text><text x="90" y="104" text-anchor="middle" class="dnv">${nf(c.neto, 0)} €</text></svg>
      <ul class="lg7">${c.donut.map((s, i) => `<li><i style="background:${COL[i]}"></i><span>${esc(s.l)}</span><b>${eur(s.eur)}</b><em>${pc(s.pct)}</em></li>`).join('')}</ul></div>`;
  }
  function render() {
    const el = $('#dash7'); if (!el || L6) return; const isDemo = demo(), c = isDemo ? D().compute(F) : null;
    const g = (k) => (c ? c[k] : null);
    el.innerHTML = `<div class="rot7 ${isDemo ? 'demo' : 'real'}" role="note"><b>${isDemo ? 'DEMO · DATOS FICTICIOS' : 'DATOS DE AHT'}</b><span>${isDemo ? 'Ejemplo coherente y aislado. No representa resultados de AHT.' : 'Sin datos: aún no hay fuente de ventas conectada a este dashboard (pendiente). No se muestra nada inventado.'}</span></div>
      ${filtersHtml()}
      <div class="grid7"><section class="mid7" aria-label="Indicadores">
        <div class="kg7">${kpi('cy', 'Facturación bruta <small>IVA incl.</small>', eur(g('bruto')))}${kpi('gr', 'Ventas netas <small>sin IVA</small>', eur(g('neto')))}${kpi('vi', 'Unidades vendidas', c ? nf(c.uds, 0) : 'Sin datos')}${kpi('am', 'Inversión publicitaria', eur(g('ads')))}${kpi('gr', 'Contribución total', eur(g('contrib')), 'excluye overhead general')}${kpi('cy', 'Contribución %', pc(g('contribPct')), 'ponderada sobre ventas netas')}</div>
        <article class="k7 wide"><h4>Distribución de ventas netas <small>fabricación · comisiones · logística y otros · publicidad · contribución</small></h4>${c ? donut(c) : '<p class="muted">Sin datos</p>'}</article></section>
        <aside class="side7"><article class="card7 noti7"><h4>Notificaciones</h4><div id="n7"></div></article>
          <article class="card7 chat7" id="chat7card"><div class="ch7h"><h4>Director IA</h4><button type="button" id="c7Full" class="ro-ok ic7" aria-label="Pantalla completa" title="Pantalla completa">⛶</button></div><div id="c7Log" class="c7log" aria-live="polite"></div>
            <form id="c7Form" class="c7form"><span id="c7Ro" class="ro7" hidden>Solo lectura: el chat se activa con un rol que pueda escribir</span><textarea id="c7In" rows="3" placeholder="Escribe al Director IA…" aria-label="Mensaje al Director IA"></textarea><div class="c7bar"><label class="ic7 ro-ok" title="Adjuntos: pendiente (aún no se envían al Director)"><input id="c7File" type="file" multiple hidden>📎</label><button type="button" id="c7Mic" class="ic7 ro-ok" title="Dictado por voz">🎤</button><span id="c7Att" class="c7att"></span><span class="grow"></span><button type="submit" class="ro-ok send7" id="c7Send">Enviar ➤</button></div></form></article></aside></div>`;
    chatInit(); notifs(); roHint();
  }
  function roHint() { const V = root.V03 && root.V03.V, ro = document.body.classList.contains('staging') || (V && V.viewer) || document.getElementById('envBanner'); const h = $('#c7Ro'); if (h) h.hidden = !ro; }
  async function notifs() {
    const n = $('#n7'); if (!n) return;
    if (demo()) { n.innerHTML = ['DEMO · Contribución % del periodo por encima del objetivo (ejemplo)', 'DEMO · Stock de un SKU bajo para la reposición prevista (ejemplo)', 'DEMO · Informe de Ads pendiente de importar (ejemplo)'].map((t) => `<p class="nt7"><i></i>${esc(t)}</p>`).join(''); return; }
    if (!(root.V03 && root.V03.V && root.V03.V.user)) { n.innerHTML = '<p class="muted">Sin datos</p>'; return; }
    try { const r = await root.V03.api('GET', '/api/v06/decisions'); const items = r.ok && r.j && r.j.items ? r.j.items : []; n.innerHTML = items.length ? items.slice(0, 6).map((i) => `<p class="nt7"><i></i>${esc(i.title || i.decision_de_negocio || i.motivo || 'Decisión pendiente')}</p>`).join('') : '<p class="muted">Sin notificaciones</p>'; } catch (e) { n.innerHTML = '<p class="muted">Sin datos</p>'; }
  }
  function chatLog() {
    const V = root.V03 && root.V03.V, L = $('#c7Log'); if (!L) return; const m = (V && V.chat) || [];
    L.innerHTML = m.length ? m.map((x) => `<div class="m7 ${x.me ? 'me' : ''}">${esc(x.text)}${x.meta ? `<small>${esc(x.meta)}</small>` : ''}</div>`).join('') : '<p class="muted c7empty">Pregunta por ventas, precios, stock, publicidad o lanzamientos. El Director IA usa los coworkers existentes.</p>';
    L.scrollTop = 1e6;
  }
  function chatInit() {
    chatLog();
    const f = $('#c7Form'), inp = $('#c7In'); if (!f) return;
    f.onsubmit = async (e) => { e.preventDefault(); const q = inp.value.trim(); if (!q) return; inp.value = ''; $('#c7Send').disabled = true; try { await root.V03.ask(q); } catch (er) { root.V03.V.chat.push({ text: 'Error: ' + er }); } $('#c7Send').disabled = false; chatLog(); };
    inp.onkeydown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); f.requestSubmit(); } };
    $('#c7File').onchange = (e) => { const a = [...e.target.files].map((x) => x.name); $('#c7Att').textContent = a.length ? a.length + ' adjunto(s) · PENDIENTE: no se envían todavía' : ''; };
    const mic = $('#c7Mic'), SR = root.SpeechRecognition || root.webkitSpeechRecognition;
    if (!SR) { mic.disabled = true; mic.title = 'Dictado no disponible en este navegador (pendiente)'; } else mic.onclick = () => { const r = new SR(); r.lang = 'es-ES'; r.onresult = (ev) => { inp.value += (inp.value ? ' ' : '') + ev.results[0][0].transcript; }; r.start(); };
    $('#c7Full').onclick = () => { const c = $('#chat7card'); c.classList.toggle('full'); document.body.classList.toggle('c7full', c.classList.contains('full')); };
  }
  function bind() {
    document.addEventListener('change', (e) => {
      const t = e.target; if (!t.id || !t.id.startsWith('f7')) return;
      if (t.id === 'f7Line') { F.line = t.value; F.sub = 'all'; } else if (t.id === 'f7Sub') F.sub = t.value; else if (t.id === 'f7Reg') { F.region = t.value; F.country = 'all'; } else if (t.id === 'f7Cty') F.country = t.value; render();
    });
    document.addEventListener('click', (e) => { const p = e.target.closest('[data-per]'); if (p && $('#dash7').contains(p)) { F.period = p.dataset.per; render(); } });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && document.body.classList.contains('c7full')) { $('#chat7card').classList.remove('full'); document.body.classList.remove('c7full'); } });
  }
  function onShow(id) { document.body.classList.toggle('dash7on', id === 'hoy' || id === 'bench'); if (id === 'hoy') render(); }
  document.addEventListener('DOMContentLoaded', () => { if (L6) { $$('#tabs button[data-tab=dash], #tabs button[data-tab=bench]').forEach((b) => b.remove()); const m = $('#tabs button[data-tab=inicio]'); if (m) m.textContent = 'INICIO'; const d = $('#tab-dash'); if (d) d.classList.remove('on'); const i = $('#tab-inicio'); if (i) i.classList.add('on'); return; } header(); bind(); render(); });
  root.DASH7 = { F, render, onShow };
})(self);
(function (root) {   // marcador de la entrega 2 (se sustituye por la página Benchmarking completa)
  'use strict';
  if (root.BENCH7) return;
  root.BENCH7 = { onShow(id) { document.body.classList.toggle('dash7on', id === 'hoy' || id === 'bench'); const el = document.getElementById('bench7'); if (id === 'bench' && el && !el.dataset.done) { el.dataset.done = '1'; el.innerHTML = '<div class="rot7 demo" role="note"><b>PENDIENTE</b><span>Benchmarking: entrega 2 de este rediseño.</span></div>'; } } };
})(self);
