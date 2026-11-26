/* Rediseño global · fase 1 — Dashboard AHT simplificado (solo lectura, sin menú lateral). Cabecera: marca AHT (vuelve al dashboard), Benchmarking, Director IA, sesión.
   Datos: DEMO aislada y rotulada (js/dash7calc.js); en modo DATOS DE AHT sin fuente conectada → «Sin datos». No escribe, no llama a conectores, no gasta cuota. */
(function (root) {
  'use strict';
  const $ = (s, r) => (r || document).querySelector(s), $$ = (s, r) => [...(r || document).querySelectorAll(s)];
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const D = () => root.D7C, F = { line: 'all', sub: 'all', region: 'all', country: 'all', period: 'mes' };
  const nf = (x, d) => (x == null ? 'Sin datos' : x.toLocaleString('es-ES', { minimumFractionDigits: d, maximumFractionDigits: d, useGrouping: 'always' }));
  const eur = (x) => (x == null ? 'Sin datos' : nf(x, 2) + ' €'), pc = (x) => (x == null ? 'Sin datos' : nf(x, 2) + ' %');
  const demo = () => !root.NAV6 || root.NAV6.state.mode === 'demo';
  const COL = ['#3b82f6', '#ffb02e', '#18e6ff', '#b968ff', '#37e08a'];   // fabricación, comisiones, logística, publicidad, contribución (modelo de dirección)

  const L6 = new URLSearchParams(location.search).get('shell') === '6';   // transición: la interfaz anterior sigue disponible (?shell=6), nada se borra
  function header() {
    const top = $('header.top'); if (!top || $('#hdr7') || L6) return;
    const h = document.createElement('header'); h.id = 'hdr7'; h.className = 'hdr7';
    h.innerHTML = `<button type="button" id="h7Brand" class="h7brand ro-ok" aria-label="AHT · volver al dashboard"><b>AHT</b><span>AMAZON PRO INTELLIGENCE GLOBAL</span></button>
      <nav class="h7nav" aria-label="Principal"><button type="button" id="h7Bench" class="ro-ok h7b" data-go="bench">Benchmarking</button><button type="button" id="h7Dir" class="ro-ok h7b" data-go="dir">Director IA</button></nav><div id="h7Sess" class="h7sess"></div>`;
    top.insertAdjacentElement('beforebegin', h);
    const sess = $('#sess'); if (sess) $('#h7Sess').appendChild(sess);
    document.body.classList.add('shell7');
    h.addEventListener('click', (e) => { const b = e.target.closest('#h7Brand, [data-go]'); if (!b) return; root.NAV6.go(b.id === 'h7Brand' ? 'hoy' : b.dataset.go, 0); });
  }
  function select(id, label, opts, val) { return `<label class="f7"><span>${label} ·</span><select id="${id}" class="ro-ok" data-view-filter aria-label="${label}">${opts.map(([v, l, dis]) => `<option value="${v}" ${v === val ? 'selected' : ''} ${dis ? 'disabled' : ''}>${esc(l)}</option>`).join('')}</select></label>`; }
  function filtersHtml() {
    const d = D(), ln = d.LINES.find((x) => x.id === F.line), rg = d.REGIONS.find((x) => x.id === F.region);
    const lopts = [['all', 'Consolidado AHT'], ...d.LINES.map((x) => [x.id, x.l])];
    const ropts = [['all', 'Global'], ...d.REGIONS.map((x) => [x.id, x.l])];
    const fut = d.FUTURE.filter((c) => !rg || c.region === rg.id).map((c) => [c.id, c.l + ' (futuro, sin configurar)', true]);
    const copts = [['all', 'Todos'], ...(rg ? rg.countries : d.REGIONS.flatMap((x) => x.countries)).map((c) => [c.id, c.l]), ...fut];
    return `${select('f7Line', 'AHT', lopts, F.line)}${ln && ln.subs ? select('f7Sub', 'PHIVITAL', [['all', 'Todas'], ...ln.subs.map((s) => [s.id, s.l])], F.sub) : ''}${select('f7Reg', 'Región', ropts, F.region)}${select('f7Cty', 'País', copts, F.country)}${select('f7Per', 'Periodo', d.PERIODS.map((x) => [x.id, x.l]), F.period)}`;
  }
  // gráfico individual por KPI (área, barras, escalón, barras+línea, medidor). Solo con serie DEMO explícita; sin serie → «Sin datos».
  function spark(kind, ser, col) {
    if (!ser) return '<div class="sp7 none">Sin datos</div>';
    const W = 160, H = 46, mx = Math.max(...ser), mn = Math.min(...ser), rg = mx - mn || 1, X = (i) => (i * (W - 6)) / (ser.length - 1) + 3, Y = (v) => H - 4 - ((v - mn) / rg) * (H - 10);
    const pts = (f) => ser.map((v, i) => X(i).toFixed(1) + ',' + f(v).toFixed(1)).join(' '), id = 'g' + Math.abs(col.charCodeAt(1) * 31 + kind.length);
    const grad = `<defs><linearGradient id="${id}${kind}" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="${col}" stop-opacity=".55"/><stop offset="1" stop-color="${col}" stop-opacity=".05"/></linearGradient></defs>`;
    let g = '';
    if (kind === 'area') g = `${grad}<polygon fill="url(#${id}${kind})" points="${X(0)},${H - 2} ${pts(Y)} ${X(ser.length - 1)},${H - 2}"/><polyline fill="none" stroke="${col}" stroke-width="2.2" points="${pts(Y)}"/>`;
    else if (kind === 'bars') g = ser.map((v, i) => `<rect x="${(X(i) - 4.4).toFixed(1)}" y="${Y(v).toFixed(1)}" width="8.8" height="${(H - 2 - Y(v)).toFixed(1)}" rx="1.5" fill="${col}" opacity="${(0.45 + 0.55 * i / (ser.length - 1)).toFixed(2)}"/>`).join('');
    else if (kind === 'steparea') { const st = ser.map((v, i) => `${X(i).toFixed(1)},${Y(v).toFixed(1)} ${(i < ser.length - 1 ? X(i + 1) : X(i)).toFixed(1)},${Y(v).toFixed(1)}`).join(' '); g = `${grad}<polygon fill="url(#${id}${kind})" points="${X(0)},${H - 2} ${st} ${X(ser.length - 1)},${H - 2}"/><polyline fill="none" stroke="${col}" stroke-width="2.2" points="${st}"/>`; }
    else if (kind === 'barsline') g = ser.map((v, i) => `<rect x="${(X(i) - 4.4).toFixed(1)}" y="${Y(v).toFixed(1)}" width="8.8" height="${(H - 2 - Y(v)).toFixed(1)}" rx="1.5" fill="${col}" opacity=".85"/>`).join('') + `<polyline fill="none" stroke="#fff" stroke-width="1.8" points="${pts((v) => Y(v) - 4)}"/>` + ser.map((v, i) => `<circle cx="${X(i).toFixed(1)}" cy="${(Y(v) - 4).toFixed(1)}" r="2.2" fill="#fff"/>`).join('');
    else { const last = ser[ser.length - 1], f = Math.max(0, Math.min(1, last / 100)), cx = 38, cy = 40, R = 30, ang = Math.PI * (1 + f), P = (a2, r2) => `${(cx + r2 * Math.cos(a2)).toFixed(1)},${(cy + r2 * Math.sin(a2)).toFixed(1)}`;
      g = `<path d="M${P(Math.PI, R)} A${R},${R} 0 0 1 ${P(2 * Math.PI, R)}" fill="none" stroke="#ffffff22" stroke-width="7" stroke-linecap="round"/><path d="M${P(Math.PI, R)} A${R},${R} 0 0 1 ${P(ang, R)}" fill="none" stroke="${col}" stroke-width="7" stroke-linecap="round"/><polyline fill="none" stroke="${col}" stroke-width="2" points="${ser.map((v, i) => (90 + (i * 64) / (ser.length - 1)).toFixed(1) + ',' + (H - 4 - ((v - mn) / rg) * (H - 14)).toFixed(1)).join(' ')}"/>`; }
    return `<svg class="sp7" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="Serie demo de 12 periodos"><title>Serie DEMO (12 periodos): ejemplo ficticio</title>${g}</svg>`;
  }
  // [métrica, clase, título, tipo de gráfico, color, icono, variación DEMO]
  const KP = [['bruto', 'cy', 'Facturación<br>bruta', 'area', '#18e6ff', '€', '+12,4 %'], ['neto', 'cy', 'Ventas netas<br>sin IVA', 'bars', '#18e6ff', 'Σ', '+11,8 %'], ['uds', 'bl', 'Unidades<br>vendidas', 'steparea', '#3b82f6', '▣', '+10,0 %'],
    ['ads', 'vi', 'Inversión<br>publicitaria', 'bars', '#b968ff', '◉', '+8,6 %'], ['contrib', 'gr', 'Contribución<br>total', 'barsline', '#37e08a', '↗', '+14,7 %'], ['pct', 'gr', 'Contribución<br>(%)', 'gauge', '#37e08a', '%', '+2,7 pp']];
  function kpiHtml(c, isDemo) {
    return KP.map(([m, cls, t, kind, col, ic, dl]) => {
      const raw = m === 'pct' ? (c && c.contribPct) : (c && c[m]), v = raw == null ? 'Sin datos' : m === 'pct' ? pc(raw) : m === 'uds' ? nf(raw, 0) : eur(raw);
      const ser = isDemo && raw != null ? D().series(F, m) : null;
      return `<article class="k7 ${cls}" data-k="${m}"><header class="kh7"><i class="ki7" aria-hidden="true">${ic}</i><h4>${t}</h4>${ser ? `<span class="dl7" title="Variación DEMO frente al periodo anterior">▲${dl}</span>` : ''}</header><div class="v7">${v}</div>${spark(kind, ser, col)}${m === 'contrib' ? '<small>excluye overhead general</small>' : m === 'pct' ? '<small>ponderada sobre ventas netas</small>' : ''}</article>`;
    }).join('');
  }
  function donut(c) {
    if (!c || !c.donut.length) return '<p class="muted">Sin datos</p>';
    const loss = c.loss, parts = c.donut.map((s, i) => ({ ...s, i })).filter((s) => !s.neg);
    const tot = parts.reduce((a, s) => a + s.eur, 0) || 1;   // con pérdida: el anillo reparte solo los costes; la contribución negativa NO es un segmento
    let a = -Math.PI / 2; const R = 70, r = 46, cx = 90, cy = 90, p = (ang, rad) => `${(cx + rad * Math.cos(ang)).toFixed(2)},${(cy + rad * Math.sin(ang)).toFixed(2)}`;
    const segs = parts.map((s) => { const f = s.eur / tot, b = a + f * 2 * Math.PI, big = f > 0.5 ? 1 : 0, d = `M${p(a, R)} A${R},${R} 0 ${big} 1 ${p(b - 1e-4, R)} L${p(b - 1e-4, r)} A${r},${r} 0 ${big} 0 ${p(a, r)} Z`; a = b; return `<path d="${d}" fill="${COL[s.i]}"><title>${esc(s.l)}</title></path>`; }).join('');
    const money = (x) => (Number.isInteger(x) ? nf(x, 0) : nf(x, 2)) + ' €';
    return `<div class="dn7 ${loss ? 'loss' : ''}"><svg viewBox="0 0 180 180" role="img" aria-label="Distribución de ventas netas">${segs}<text x="90" y="84" text-anchor="middle" class="dnt">${loss ? 'Pérdida' : 'Ventas netas'}</text><text x="90" y="104" text-anchor="middle" class="dnv">${loss ? eur(c.contrib) : eur(c.neto)}</text></svg>
      <ul class="lg7">${c.donut.map((s, i) => `<li class="${s.neg ? 'neg' : ''}"><i style="background:${s.neg ? 'transparent;border:2px dashed #ff5a5a' : COL[i]}"></i><span>${esc(s.l === 'Comisiones' ? 'Comisiones Amazon' : s.l)}${s.neg ? ' (pérdida · fuera del anillo)' : ''}</span><b>${money(s.eur)}</b><em style="color:${s.neg ? '#ff6b6b' : COL[i]}">${pc(s.pct)}</em></li>`).join('')}</ul></div>`;
  }
  function ctxText() { const d = D(), l = d.LINES.find((x) => x.id === F.line), sb = l && l.subs && l.subs.find((x) => x.id === F.sub), rg = d.REGIONS.find((x) => x.id === F.region), ct = rg && rg.countries.find((x) => x.id === F.country), pr = d.PERIODS.find((x) => x.id === F.period);
    return [l ? l.l : 'Consolidado AHT', sb ? sb.l : null, rg ? rg.l : 'Global', ct ? ct.l : null, pr.l].filter(Boolean).join(' · '); }
  function ctx() { return { line: F.line, sub: F.sub, region: F.region, country: F.country, period: F.period }; }
  function shell() {   // el esqueleto (incluido el chat con su borrador y su estado de pantalla completa) se crea UNA vez; los filtros solo actualizan sus zonas
    const el = $('#dash7'); if (!el || el.dataset.built) return; el.dataset.built = '1';
    el.innerHTML = `<div class="filt7" id="filt7"></div>
      <div class="grid7"><section class="mid7" aria-label="Indicadores"><div class="kg7" id="kg7"></div>
        <article class="k7 wide"><h4><i class="ki7" aria-hidden="true">◔</i>Distribución de las ventas netas</h4><div id="dn7w"></div></article></section>
        <aside class="side7"><article class="card7 noti7"><h4><i class="ki7 bell" aria-hidden="true">!</i>Notificaciones del Director IA</h4><div id="n7"></div></article>
          <article class="card7 chat7" id="chat7card"><div class="ch7h"><h4><i class="ki7 brain" aria-hidden="true">◍</i>Director IA Amazon</h4><span id="c7Ctx" class="c7ctx"></span><button type="button" id="c7Full" class="ro-ok ic7" aria-label="Pantalla completa" title="Pantalla completa">⛶</button></div><div id="c7Log" class="c7log" aria-live="polite"></div>
            <form id="c7Form" class="c7form"><span id="c7Ro" class="ro7" hidden>Solo lectura: el chat se activa con un rol que pueda escribir</span><textarea id="c7In" rows="3" placeholder="Escribe al Director IA…" aria-label="Mensaje al Director IA"></textarea><div class="c7bar"><label class="ic7 ro-ok" title="Adjuntos: pendiente (aún no se envían al Director)"><input id="c7File" type="file" multiple hidden>＋</label><button type="button" id="c7Mic" class="ic7 ro-ok" title="Dictado" aria-label="Dictado">🎤</button><span id="c7Att" class="c7att"></span><button type="submit" id="c7Send" class="c7send" aria-label="Enviar">➤</button></div></form></article></aside></div><div id="rot7"></div>`;
    chatInit();
  }
  function render() {
    shell(); if (!$('#dash7') || L6) return; const isDemo = demo(), c = isDemo ? D().compute(F) : null;
    $('#rot7').innerHTML = `<div class="rot7 ${isDemo ? 'demo' : 'real'}" role="note"><b>${isDemo ? 'DEMO · DATOS FICTICIOS' : 'DATOS DE AHT'}</b><span>${isDemo ? 'Datos simulados · Ejemplo coherente y aislado. No representa resultados de AHT.' : 'Sin datos: aún no hay fuente de ventas conectada a este dashboard (pendiente). No se muestra nada inventado.'}</span></div>`;
    const act = document.activeElement && document.activeElement.id; $('#filt7').innerHTML = filtersHtml(); if (act && /^f7/.test(act)) { const n = document.getElementById(act); if (n) n.focus(); }
    $('#kg7').innerHTML = kpiHtml(c, isDemo);
    $('#dn7w').innerHTML = c && c.empty ? '<p class="muted">Sin datos: la combinación de filtros no tiene ventas.</p>' : donut(c);
    $('#c7Ctx').textContent = ctxText(); notifs(); roHint(); chatLog();
  }
  function roHint() { const V = root.V03 && root.V03.V, ro = document.body.classList.contains('staging') || (V && V.viewer) || document.getElementById('envBanner'); const h = $('#c7Ro'); if (h) h.hidden = !ro; }
  let NSEQ = 0;
  async function notifs() {
    const n = $('#n7'); if (!n) return; const my = ++NSEQ, ct = ctxText();   // descarta respuestas antiguas si cambian los filtros / el modo
    const row = (t, st, ev, cx, k, day) => `<p class="nt7 ${k || ''}"><i></i><span><b>${esc(t)}</b><small>Estado: ${esc(st)} · Evidencia: ${esc(ev)} · ${esc(cx)}</small></span>${day ? `<em>${esc(day)}</em>` : ''}</p>`;
    if (demo()) { n.innerHTML = [['DEMO · Oportunidad comercial', 'abierta (ejemplo)', 'serie DEMO del dashboard', 'ok', 'Hoy'], ['DEMO · Revisión de rentabilidad', 'abierta (ejemplo)', 'contribución DEMO', 'warn', 'Hoy'], ['DEMO · Seguimiento de expansión', 'pendiente (ejemplo)', 'ninguna: ejemplo', 'info', 'Ayer']].map((x) => row(x[0], x[1], x[2], 'Contexto: ' + ct, x[3], x[4])).join(''); return; }
    if (!(root.V03 && root.V03.V && root.V03.V.user)) { n.innerHTML = '<p class="muted">Sin datos</p>'; return; }
    let r; try { r = await root.V03.api('GET', '/api/v06/decisions'); } catch (e) { r = null; }
    if (my !== NSEQ) return;
    if (!r || !r.ok || !r.j) { n.innerHTML = '<p class="muted">Sin datos: no se pudieron cargar las notificaciones' + (r && r.status ? ' (HTTP ' + esc(r.status) + ')' : '') + '</p>'; return; }
    const items = r.j.items || [];
    n.innerHTML = items.length ? items.slice(0, 6).map((i) => row(i.title || i.decision_de_negocio || i.motivo || 'Decisión pendiente', i.estado || i.status || 'sin estado', i.evidencia || i.evidence || 'sin evidencia indicada', 'Alcance: global (no filtrada por el dashboard)')).join('') : '<p class="muted">Sin notificaciones</p>';
  }
  function chatLog() {
    const V = root.V03 && root.V03.V, L = $('#c7Log'); if (!L) return; const m = (V && V.chat) || [];
    L.innerHTML = m.map((x) => `<div class="m7 ${x.me ? 'me' : ''}">${esc(x.text)}${x.meta ? `<small>${esc(x.meta)}</small>` : ''}</div>`).join('');
    L.scrollTop = 1e6;
  }
  function chatInit() {
    const f = $('#c7Form'), inp = $('#c7In'); if (!f) return;
    f.onsubmit = async (e) => { e.preventDefault(); const q = inp.value.trim(); if (!q) return; inp.value = ''; $('#c7Send').disabled = true; const cx = ctx(); try { await root.V03.ask(q, cx); } catch (er) { root.V03.V.chat.push({ text: 'Error: ' + er }); } $('#c7Send').disabled = false; chatLog(); };
    inp.onkeydown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); f.requestSubmit(); } };
    $('#c7File').onchange = (e) => { const a = [...e.target.files].map((x) => x.name); $('#c7Att').textContent = a.length ? a.length + ' adjunto(s) · PENDIENTE: no se envían todavía' : ''; };
    const mic = $('#c7Mic'), SR = root.SpeechRecognition || root.webkitSpeechRecognition;
    if (!SR) { mic.disabled = true; mic.title = 'Dictado no disponible en este navegador (pendiente)'; } else mic.onclick = () => { const r = new SR(); r.lang = 'es-ES'; r.onresult = (ev) => { inp.value += (inp.value ? ' ' : '') + ev.results[0][0].transcript; }; r.start(); };
    $('#c7Full').onclick = () => { const c = $('#chat7card'); c.classList.toggle('full'); document.body.classList.toggle('c7full', c.classList.contains('full')); };
  }
  function bind() {
    document.addEventListener('change', (e) => {
      const t = e.target; if (!t.id || !t.id.startsWith('f7')) return;
      if (t.id === 'f7Line') { F.line = t.value; F.sub = 'all'; } else if (t.id === 'f7Sub') F.sub = t.value; else if (t.id === 'f7Reg') { F.region = t.value; F.country = 'all'; } else if (t.id === 'f7Cty') F.country = t.value; else if (t.id === 'f7Per') F.period = t.value; render();
    });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && document.body.classList.contains('c7full')) { $('#chat7card').classList.remove('full'); document.body.classList.remove('c7full'); } });
  }
  function onShow(id) { document.body.classList.toggle('dash7on', id === 'hoy' || id === 'bench'); if (id === 'hoy') render(); }
  document.addEventListener('DOMContentLoaded', () => { if (L6) { $$('#tabs button[data-tab=dash], #tabs button[data-tab=bench]').forEach((b) => b.remove()); const m = $('#tabs button[data-tab=inicio]'); if (m) m.textContent = 'INICIO'; const d = $('#tab-dash'); if (d) d.classList.remove('on'); const i = $('#tab-inicio'); if (i) i.classList.add('on'); return; } header(); bind(); render(); });
  root.DASH7 = { F, render, onShow, ctx };
})(self);
(function (root) {   // marcador de la entrega 2 (se sustituye por la página Benchmarking completa)
  'use strict';
  if (root.BENCH7) return;
  root.BENCH7 = { onShow(id) { document.body.classList.toggle('dash7on', id === 'hoy' || id === 'bench'); const el = document.getElementById('bench7'); if (id === 'bench' && el && !el.dataset.done) { el.dataset.done = '1'; el.innerHTML = '<div class="rot7 demo" role="note"><b>PENDIENTE</b><span>Benchmarking: entrega 2 de este rediseño.</span></div>'; } } };
})(self);
