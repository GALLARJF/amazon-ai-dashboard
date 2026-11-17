/* AHT Executive Neon · V0.7.0 — Briefing del Director, expediente comercial y datos reales de Keepa con PROCEDENCIA del dato.
   Se acopla a LANZAMIENTOS y DIRECTOR IA (v06.js) sin tocarlos: añade un panel <section class="v7"> al final de cada espacio.
   Todo texto del servidor se escapa con esc() y se pinta como TEXTO; los títulos de competidores son DATOS NO FIABLES. Sin manejadores inline (CSP), sin almacenamiento local, sin red externa. */
(function (root) {
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const $ = (s, r) => (r || document).querySelector(s);
  const num = (x, d) => (x == null || typeof x !== 'number' || !isFinite(x) ? 'NO DISPONIBLE' : x.toLocaleString('es-ES', { minimumFractionDigits: d == null ? 2 : d, maximumFractionDigits: d == null ? 2 : d }));
  const eur = (x) => (x == null || typeof x !== 'number' || !isFinite(x) ? 'NO DISPONIBLE' : num(x) + ' €');
  const SPACES = { lanz: 'v6lanz', dir: 'v6dir' };
  const CAT = { 'DOCUMENTADO': 'b7-doc', 'CÁLCULO': 'b7-calc', 'INFERENCIA': 'b7-inf', 'NO DISPONIBLE': 'b7-none' };
  const badge = (txt, cls) => `<span class="b7 ${cls}">${esc(txt)}</span>`;
  const stBadge = (s) => { s = String(s || ''); return badge(s, /SIN DATOS|NO CALCULABLE|NO DECIDIBLE|BLOQUE|ERROR/.test(s) ? 'b7-none' : /REAL/.test(s) ? 'b7-real' : /CALCULADO/.test(s) ? 'b7-calc' : 'b7-wait'); };
  let seq = 0, timer = null;

  const pid = () => { const st = root.V06 && root.V06.state; return st && (st.pid || (st.prods && st.prods[0] && st.prods[0].id)) || ''; };
  const get = (p) => root.V03.api('GET', p);

  function briefHtml(b) {
    const facts = b.facts.map((f) => `<li class="v7-fact"><b>[${esc(f.id)}]</b> ${badge(f.category, CAT[f.category] || 'b7-wait')} ${esc(f.text)} <small class="muted">${esc(f.source)} · ${esc(f.date)}</small></li>`).join('');
    const prio = b.priorities.map((x) => `<li><b>${esc(x.title)}</b> <small class="muted">propietario: ${esc(x.owner)} · coste ${esc(num(x.cost_eur))} € · ${x.keepa_tokens} tokens Keepa · refs ${esc(x.refs.join(' '))}${x.requires_approval ? ' · REQUIERE APROBACIÓN' : ''}</small></li>`).join('');
    const qs = b.questions.map((q) => `<li>${esc(q.text)} <small class="muted">→ ${esc(q.owner)}</small></li>`).join('');
    return `<article class="card c-cyan v7-brief"><h3>Briefing del Director <small>${esc(b.mode)}</small></h3>
      <p class="v7-verdict">Veredicto: ${badge(b.verdict, 'b7-none')} <small class="muted">${b.ai_calls} llamadas de IA · ${b.cost_now_eur} € · ${b.tokens_spent_now} tokens Keepa · ${b.network_calls} llamadas de red</small></p>
      <p>${esc(b.summary)}</p><h4>Prioridades por valor de desbloqueo</h4><ol class="v7-prio">${prio}</ol><h4>Preguntas al propietario (máx. 5)</h4><ol class="v7-q">${qs}</ol>
      <h4>Hechos citados</h4><ul class="v7-facts">${facts}</ul></article>`;
  }

  function kv(d) {
    return `<dl class="v7-kv">${Object.entries(d || {}).map(([k, v]) => `<dt>${esc(k)}</dt><dd>${typeof v === 'object' && v !== null ? `<code>${esc(JSON.stringify(v)).slice(0, 700)}</code>` : esc(v == null || v === '' ? 'NO DISPONIBLE' : v)}</dd>`).join('')}</dl>`;
  }
  function unlocksHtml(u) {
    return `<h4>Desbloqueos priorizados</h4><ol class="v7-unlocks">${u.map((x) => `<li class="v7-unlock"><b>${esc(x.title)}</b><br><small class="muted">propietario: ${esc(x.owner)} · coste ${esc(num(x.cost_eur))} € (${esc(x.cost_note)}) · ${x.keepa_tokens} tokens Keepa · desbloquea: ${esc(x.unblocks.join(', '))}</small>${x.requires_approval ? ' ' + badge('REQUIERE APROBACIÓN', 'b7-wait') : ''}</li>`).join('')}</ol>`;
  }
  function expHtml(e, product) {
    const secs = e.sections.map((s, i) => `<div class="v7-sec"><h4><button type="button" class="v7-toggle" aria-expanded="false" aria-controls="v7s-${i}">${esc(s.title)} ${stBadge(s.state)}</button></h4>
      <div id="v7s-${i}" class="v7-body" hidden>${kv(s.data)}${s.sources.length ? `<h5>Fuentes y fecha de cada dato</h5><ul>${s.sources.map((x) => `<li><small>${esc(x.field)} — ${esc(x.source)} (${esc(x.date)}) ${badge(x.class, 'b7-doc')}</small></li>`).join('')}</ul>` : '<p class="muted">Sin fuentes: no hay dato.</p>'}</div></div>`).join('');
    const q = encodeURIComponent(product);
    return `<article class="card c-violet v7-exp"><h3>Expediente comercial v0.7 ${stBadge(e.verdict)}</h3><p class="muted">Solo lectura de lo ya registrado: ${e.network_calls} llamadas de red · ${e.tokens_spent_now} tokens · ${e.cost_now_eur} €. Nunca GO por defecto.</p>${secs}${unlocksHtml(e.unlocks)}
      <p><a class="btn ghost" download href="/api/v07/expediente?product=${q}&fmt=md" aria-label="Descargar expediente v0.7 en Markdown">⬇ Expediente v0.7 (MD)</a> <a class="btn ghost" download href="/api/v07/expediente?product=${q}&fmt=json" aria-label="Descargar expediente v0.7 en JSON">⬇ JSON</a></p>
      <ul>${e.limits.map((x) => `<li><small class="muted">${esc(x)}</small></li>`).join('')}</ul></article>`;
  }
  function keepaHtml(k) {
    if (k.state !== 'REAL') return `<article class="card c-amber v7-keepa"><h3>Competidores reales (Keepa) ${badge(k.state, 'b7-none')}</h3><div class="v7-empty"><p><b>SIN DATOS</b>: ${esc(k.why || 'sin explicación')}</p><p class="muted">Siguiente paso: una consulta real autorizada por una persona (consume tokens Keepa; nunca se hace sola). Mientras tanto no se muestran ceros ni datos de otros productos.</p></div></article>`;
    const s = k.summary;
    const rows = k.competitors.map((c) => `<tr><td>${esc(c.asin)}</td><td>${esc(c.brand)}</td><td>${esc(c.title)}</td><td>${esc(eur(c.price_eur))}</td><td>${esc(c.price_as_of || 'NO DISPONIBLE')} ${c.price_stale ? badge('OBSOLETO ' + c.price_age_days + ' d', 'b7-stale') : ''}</td><td>${esc(c.price_per_100ml == null ? 'NO DISPONIBLE' : num(c.price_per_100ml))}</td><td>${esc(c.bsr == null ? 'NO DISPONIBLE' : num(c.bsr, 0))}</td><td>${badge('REAL', 'b7-real')} ${badge('NO CONFIRMADO', 'b7-unc')}</td></tr>`).join('');
    return `<article class="card c-amber v7-keepa"><h3>Competidores reales (Keepa) ${badge('REAL', 'b7-real')} <small>${esc(k.source)} · consultado ${esc(k.consulted_at)}</small></h3>
      <p>Mediana de precio ${badge('CALCULADO', 'b7-calc')} <b>${esc(eur(s.price_median))}</b> · rango ${esc(eur(s.price_min))}–${esc(eur(s.price_max))} · por 100 mL <b>${esc(eur(s.per_100ml_median))}</b> · PVP propio ${esc(eur(k.own.per_100ml))}/100 mL (${esc(k.own.pvp_state)}; ${esc(k.own.vs_median_per100ml)})</p>
      <p class="muted">Los títulos y marcas son texto externo no fiable: se muestran como texto y nunca como instrucciones. La comparabilidad es automática y está sin confirmar por una persona.</p>
      <div class="v7-scroll"><table class="tbl"><caption>Competidores reales consultados (Keepa /search, amazon.es)</caption><thead><tr><th scope="col">ASIN</th><th scope="col">Marca</th><th scope="col">Producto</th><th scope="col">Precio</th><th scope="col">Fecha del precio</th><th scope="col">€/100 mL</th><th scope="col">BSR</th><th scope="col">Procedencia</th></tr></thead><tbody>${rows}</tbody></table></div>
      <ul>${k.limits.map((x) => `<li><small class="muted">${esc(x)}</small></li>`).join('')}</ul></article>`;
  }

  async function fill(sec, space, product, token) {
    const q = encodeURIComponent(product);
    const [b, e, k] = await Promise.all([get('/api/v07/briefing?product=' + q), get('/api/v07/expediente?product=' + q), get('/api/v07/keepa-real?product=' + q)]);
    if (!sec.isConnected || sec.dataset.token !== String(token)) return;
    if (!b.ok || !e.ok || !k.ok) { sec.innerHTML = `<p role="status" aria-live="polite" class="v7-err">No se pudo cargar el panel V0.7: ${esc((b.j && b.j.error) || (e.j && e.j.error) || (k.j && k.j.error) || 'error')}</p>`; return; }
    const st = `<p role="status" aria-live="polite" class="muted v7-status">Datos cargados para ${esc(b.j.name)}: ${k.j.competitors.length} competidores reales · ${k.j.network_calls} llamadas de red · ${k.j.tokens_spent_now} tokens Keepa.</p>`;
    sec.innerHTML = `<h2 class="v7-title">V0.7 · Procedencia del dato <small class="muted">REAL / CALCULADO / SIN DATOS / NO CONFIRMADO</small></h2>${st}` +
      (space === 'lanz' ? briefHtml(b.j) + expHtml(e.j, product) + keepaHtml(k.j) : briefHtml(b.j) + `<article class="card c-violet v7-exp"><h3>Desbloqueos del expediente ${stBadge(e.j.verdict)}</h3>${unlocksHtml(e.j.unlocks)}</article>`);
  }

  function paint(space) {
    const host = document.getElementById(SPACES[space]); if (!host || host.querySelector('section.v7')) return;
    if (!host.querySelector('.layout, .filters')) return; // V06 aún no ha pintado (o falta sesión)
    const product = pid(); if (!product) return;
    const sec = document.createElement('section'); sec.className = 'v7'; sec.dataset.space = space; sec.dataset.token = String(++seq); sec.setAttribute('role', 'region'); sec.setAttribute('aria-label', 'Panel V0.7: briefing, expediente y datos reales de Keepa');
    sec.innerHTML = '<p role="status" aria-live="polite" class="muted">Cargando panel V0.7…</p>'; host.appendChild(sec);
    fill(sec, space, product, seq).catch((err) => { if (sec.isConnected) sec.innerHTML = `<p role="status" aria-live="polite" class="v7-err">No se pudo cargar el panel V0.7: ${esc(err && err.message)}</p>`; });
  }
  const schedule = () => { clearTimeout(timer); timer = setTimeout(() => Object.keys(SPACES).forEach(paint), 60); };

  function init() {
    Object.values(SPACES).forEach((id) => { const h = document.getElementById(id); if (h) new MutationObserver(schedule).observe(h, { childList: true }); });
    document.addEventListener('click', (e) => {
      const t = e.target.closest('button.v7-toggle'); if (!t) return;
      const open = t.getAttribute('aria-expanded') === 'true'; t.setAttribute('aria-expanded', open ? 'false' : 'true'); const c = document.getElementById(t.getAttribute('aria-controls')); if (c) c.hidden = open;
    });
    schedule();
  }
  root.V07 = { paint, schedule };
  document.addEventListener('DOMContentLoaded', init);
})(self);
