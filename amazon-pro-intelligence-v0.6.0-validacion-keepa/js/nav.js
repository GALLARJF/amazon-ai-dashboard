/* P0 · Fase 1 — capa de navegación (6 secciones + selector de datos + barra inferior Android).
   NO cambia pantallas, cálculos ni API: cada sub-sección activa la pantalla heredada correspondiente (clic programático sobre #tabs, que queda oculto).
   ?legacy=1 conserva la navegación antigua SOLO como transición (criterio de retirada: docs/p0_hoy/PLAN_RETIRADA_LEGACY.md, Fase 5). */
(function (root) {
  'use strict';
  const Q = new URLSearchParams(location.search);
  if (Q.get('legacy') === '1') { document.addEventListener('DOMContentLoaded', () => { const n = document.createElement('div'); n.className = 'legacybar'; n.textContent = 'NAVEGACIÓN ANTIGUA (?legacy=1) — transitoria; se retirará en la Fase 5'; document.body.insertBefore(n, document.body.firstChild); }); return; }
  const $ = (s, r) => (r || document).querySelector(s), $$ = (s, r) => [...(r || document).querySelectorAll(s)];
  const STAGING = () => !!$('#envBanner');
  // sección → sub-secciones (tab heredada, vista K4 opcional, demo = solo en modo DEMO)
  const SECS = [
    { id: 'hoy', l: 'Hoy', s: 'Hoy', i: '◉', subs: [{ l: 'Hoy', tab: 'inicio' }] },
    { id: 'ventas', l: 'Ventas', s: 'Ventas', i: '€', subs: [{ l: 'Mis ventas', tab: 'ventas' }, { l: 'Indicadores', tab: 'k4', k4: 'centro' }] },
    { id: 'prod', l: 'Productos', s: 'Productos', i: '▣', subs: [{ l: 'Catálogo', tab: 'prod' }, { l: 'Precio', tab: 'k4', k4: 'precio' }, { l: 'Competencia', tab: 'k4', k4: 'bench' }, { l: 'Expediente PHIVITAL', tab: 'piloto' }] },
    { id: 'lanz', l: 'Lanzamientos', s: 'Lanzam.', i: '✈', subs: [{ l: 'Expediente', tab: 'lanz' }, { l: 'Pre-Launch', tab: 'prelaunch' }, { l: 'Europa · Mercados', tab: 'europa' }, { l: 'Economía comercial', tab: 'comercial' }] },
    { id: 'dir', l: 'Director IA', s: 'Director', i: '✦', subs: [{ l: 'Director', tab: 'dir' }, { l: 'Datos del Director', tab: 'k4', k4: 'dir' }] },
    { id: 'dec', l: 'Decisiones', s: 'Decisiones', i: '✔', hidden: true, subs: [{ l: 'Decisiones', tab: 'decisiones' }] },
    { id: 'adm', l: 'Administración', s: 'Admin', i: '⚙', admin: true, subs: [{ l: 'Administración', tab: 'hist' }, { l: 'Laboratorio DEMO', tab: 'panel', demo: true }] },
  ];
  const ST = { mode: 'real', sec: 'hoy', sub: 0, guard: false };
  try { const m = sessionStorage.getItem('apiMode'); if (m === 'demo' || m === 'real') ST.mode = m; } catch (e) { /* sin almacenamiento */ }
  const tabOf = (s) => { const x = $('.tab.on'); return x ? x.id.replace(/^tab-/, '') : null; };
  const subs = (sec) => sec.subs.filter((x) => !x.demo || ST.mode === 'demo');
  const allowedInDemo = (sec, sub) => STAGING() || sec.admin || sec.id === 'hoy' || sec.id === 'dec' || sub.demo;   // modo DEMO: nunca se muestran datos reales
  const allowedInReal = (sub) => !sub.demo;

  function build() {
    document.body.classList.add('shell6');
    const top = $('header.top'); if (!top) return;
    const bar = document.createElement('div'); bar.id = 'nav6bar'; bar.className = 'nav6bar';
    bar.innerHTML = '<nav id="nav6" class="nav6" aria-label="Secciones"></nav><div class="nav6r"><label class="dmode" title="Procedencia de los datos que se muestran"><span class="dml">DATOS</span><select id="dmode" aria-label="Procedencia de los datos"><option value="real">DATOS REALES</option><option value="demo">DATOS DEMO/SINTÉTICOS</option></select></label><button type="button" id="decChip" class="decchip ro-ok" title="Decisiones pendientes: bandeja única">Decisiones · <b id="decN">0</b></button></div>';
    top.insertAdjacentElement('afterend', bar);
    const sub = document.createElement('div'); sub.id = 'subnav6'; sub.className = 'subnav6'; bar.insertAdjacentElement('afterend', sub);
    const strip = document.createElement('div'); strip.id = 'modeBar'; strip.className = 'modebar'; sub.insertAdjacentElement('afterend', strip);
    const guard = document.createElement('main'); guard.id = 'modeGuard'; guard.className = 'modeguard'; guard.hidden = true; strip.insertAdjacentElement('afterend', guard);
    const bn = document.createElement('nav'); bn.id = 'bnav'; bn.className = 'bnav'; bn.setAttribute('aria-label', 'Secciones (móvil)'); document.body.appendChild(bn);
    $('#dmode').onchange = (e) => setMode(e.target.value);
    $('#decChip').onclick = () => go('dec', 0);
    $('#modeGuard').addEventListener('click', (e) => { if (e.target.closest('[data-togreal]')) setMode('real'); });
    if (STAGING()) { ST.mode = 'demo'; const o = $('#dmode option[value=real]'); o.disabled = true; o.textContent = 'DATOS DE AHT (no disponibles en staging)'; $('#dmode').title = 'Staging: solo datos sintéticos'; }
    $('#dmode').value = ST.mode; paintNav(); applyMode(true);
  }
  function paintNav() {
    const mk = (cls) => SECS.filter((s) => !s.hidden).map((s) => `<button type="button" class="${cls} ro-ok ${s.id === ST.sec ? 'on' : ''}" data-sec="${s.id}" ${s.id === ST.sec ? 'aria-current="page"' : ''}>${cls === 'bn' ? '<i>' + s.i + '</i><span>' + s.s + '</span>' : s.l}</button>`).join('');
    $('#nav6').innerHTML = mk('n6'); $('#bnav').innerHTML = mk('bn');
    const sec = SECS.find((s) => s.id === ST.sec), ss = subs(sec);
    $('#subnav6').innerHTML = ss.length > 1 ? ss.map((x, i) => `<button type="button" class="sn ro-ok ${i === ST.sub ? 'on' : ''}" data-sub="${i}">${x.l}</button>`).join('') : '';
    $('#subnav6').hidden = ss.length <= 1;
  }
  function modeBar() {
    const demo = ST.mode === 'demo', st = STAGING();
    $('#modeBar').className = 'modebar ' + (demo ? 'demo' : 'real');
    const hd = demo ? (st ? 'DATOS FICTICIOS — NO REPRESENTAN RESULTADOS DE AHT' : 'DATOS DEMO/SINTÉTICOS') : 'DATOS REALES', tl = demo ? (st ? 'DATOS DEMO/SINTÉTICOS · entorno de auditoría de solo lectura' : 'no son datos reales · no se mezclan con los reales') : 'solo informes importados y fuentes verificadas · sin datos demo';
    $('#modeBar').innerHTML = `<b>${hd}</b><span class="mbx"> · ${tl}</span>`;   // en móvil solo la parte en negrita (una línea)
  }
  function clickLegacy(tab, k4) {
    const b = $(`#tabs button[data-tab="${tab}"]`); if (!b) return;
    b.click();
    if (k4) { let n = 0; const t = setInterval(() => { const v = $(`[data-k4v="${k4}"]`); if (v) { clearInterval(t); if (!v.classList.contains('on')) v.click(); } else if (++n > 40) clearInterval(t); }, 120); }
  }
  function show(sec, i) {
    const sub = subs(sec)[i] || subs(sec)[0]; ST.sec = sec.id; ST.sub = Math.max(0, subs(sec).indexOf(sub)); ST.guard = false;
    const ok = ST.mode === 'demo' ? allowedInDemo(sec, sub) : allowedInReal(sub);
    $('#modeGuard').hidden = ok; $$('main.tab').forEach((m) => { if (!ok) m.classList.remove('on'); });
    if (ok) clickLegacy(sub.tab, sub.k4);
    else { ST.guard = true; $('#modeGuard').innerHTML = `<article class="card c-amber"><h3>Modo DATOS DEMO/SINTÉTICOS</h3><p>Esta sección muestra datos de AHT, y en este modo nunca se mezclan con los demo. ${STAGING() ? 'En staging no hay datos de AHT: usa «Hoy» y «Administración › Laboratorio DEMO».' : 'Cambia a <b>DATOS REALES</b> para verla, o usa «Hoy» y «Administración › Laboratorio DEMO».'}</p>${STAGING() ? '' : '<p><button type="button" class="btn ro-ok" data-togreal="1">Cambiar a DATOS REALES</button></p>'}</article>`; }
    if (ok && sub.tab === 'panel') { const tp = $('#tab-panel'); if (tp && !tp.querySelector('.ficticio')) { const m = document.createElement('div'); m.className = 'ficticio'; m.setAttribute('role', 'note'); m.textContent = 'DATOS FICTICIOS — NO REPRESENTAN RESULTADOS DE AHT'; tp.insertBefore(m, tp.firstChild); } }
    paintNav(); scrollTo(0, 0); const hd = $('header.top'); if (hd) hd.classList.remove('acct-open');
    if (ok && root.HOY2) root.HOY2.onShow(sec.id);
    if (ok && root.LANZ2) root.LANZ2.onShow(sec.id);
    if (ok && root.VENTAS2) root.VENTAS2.onShow(sec.id);
    if (ok && root.PROD2) root.PROD2.onShow(sec.id);
    if (ok && root.ADM2) root.ADM2.onShow(sec.id);
  }
  function go(id, i) { const sec = SECS.find((s) => s.id === id); if (sec) show(sec, i || 0); }
  function setMode(m) {
    if (STAGING() && m === 'real') { $('#dmode').value = 'demo'; return; }
    ST.mode = m; try { sessionStorage.setItem('apiMode', m); } catch (e) { /* ignorar */ }
    $('#dmode').value = m; applyMode(false);
  }
  function applyMode(first) {
    modeBar();
    if (root.V06 && root.V06.state) { root.V06.state.demo = ST.mode === 'demo'; if (!first) root.V06.render(); else setTimeout(() => root.V06.render(), 0); }
    const sec = SECS.find((s) => s.id === ST.sec); const sub = subs(sec)[ST.sub] || subs(sec)[0];
    if (sub && sub.demo && ST.mode !== 'demo') ST.sub = 0;
    show(sec, ST.sub);
  }
  // sincroniza el resaltado si otras partes de la app cambian de pantalla (p. ej. «Preparar lanzamiento»)
  function sync() {
    if (ST.guard) return; const t = tabOf(); if (!t) return; const k = $('.k4views button.on'); const kv = k ? k.dataset.k4v : null;
    for (const s of SECS) { const i = subs(s).findIndex((x) => x.tab === t && (!x.k4 || x.k4 === kv)); if (i >= 0) { if (ST.sec !== s.id || ST.sub !== i) { ST.sec = s.id; ST.sub = i; paintNav(); } return; } }
  }
  async function decisions() {
    try {
      const V = root.V03 && root.V03.V; if (!V || !V.user) { $('#decN').textContent = '0'; return; }
      $('#decN').textContent = String(root.HOY2 ? await root.HOY2.pendingCount() : 0);   // bandeja única (Fase 2)
    } catch (e) { /* sin dato */ }
  }
  document.addEventListener('DOMContentLoaded', () => {
    build();
    document.addEventListener('click', (e) => {
      const su = e.target.closest('.sessu'); if (su) { $('header.top').classList.toggle('acct-open'); return; }
      if (!e.target.closest('#sess')) $('header.top').classList.remove('acct-open');
      const n = e.target.closest('#nav6 [data-sec], #bnav [data-sec]'); if (n) { go(n.dataset.sec, 0); return; }
      const s = e.target.closest('#subnav6 [data-sub]'); if (s) go(ST.sec, Number(s.dataset.sub));
    });
    setInterval(() => { const u = $('.sessu'); if (u && !u.hasAttribute('role')) { u.setAttribute('role', 'button'); u.setAttribute('tabindex', '0'); u.setAttribute('aria-label', 'Cuenta activa: ' + u.textContent + ' (abre el menú de cuenta)'); } }, 700);
    setInterval(sync, 400); setInterval(decisions, 15000); setTimeout(decisions, 1500);
  });
  root.NAV6 = { go, setMode, state: ST };
})(self);
