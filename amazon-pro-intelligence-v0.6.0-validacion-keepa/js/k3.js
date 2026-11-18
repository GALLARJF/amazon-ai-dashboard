/* AHT Executive Neon · K3 — Segmentación competitiva (motor de equivalencia comercial).
   Todo viene del servidor (/api/eu/k3). Sin manejadores inline (CSP). Todo texto externo (títulos de Amazon) se escapa: son datos no fiables. */
(function (root) {
  const $ = (s, r) => (r || document).querySelector(s), $$ = (s, r) => [...(r || document).querySelectorAll(s)];
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const SEG = { premium: ['PREMIUM', 'k3-premium', 'A · Competencia directa premium'], funcional: ['FUNCIONAL', 'k3-func', 'B · Competencia funcional'], economica: ['ECONÓMICA / MASIVO', 'k3-eco', 'C · Mercado económico'], pendiente: ['PENDIENTE DE EVIDENCIA', 'k3-pend', ''], no_comparable: ['NO COMPARABLE', 'k3-nocomp', ''] };
  const CLS = { ACTUAL: 'k3-fresh', RECIENTE: 'k3-fresh2', 'HISTÓRICO': 'k3-old', 'FECHA DESCONOCIDA': 'k3-old', 'SIN PRECIO': 'k3-none' };
  const eur = (x) => (x == null ? '<span class="muted">n/d</span>' : Number(x).toFixed(2).replace('.', ',') + ' €');
  let C = null; // contexto de eu.js
  const S = { data: null, f: { segmento: '', country: '', activo: '', min_ml: '', max_ml: '', aplicacion: '' }, sel: null, msg: '', expl: null, loading: false };

  async function load() {
    S.loading = true; const qs = Object.entries(S.f).filter(([, v]) => v !== '').map(([k, v]) => k + '=' + encodeURIComponent(v)).join('&');
    const r = await C.api('GET', C.q('/api/eu/k3' + (qs ? '?' + qs : ''))); S.data = r.ok ? r.j : { disponible: false, motivo: (r.j && r.j.error) || 'No se pudo cargar' }; S.loading = false;
  }
  async function explain(key) { const r = await C.api('GET', C.q('/api/eu/k3/explicar?key=' + encodeURIComponent(key))); S.expl = r.ok ? r.j.explicacion : ['No se pudo cargar la explicación.']; }

  const segChip = (code) => `<span class="tagst k3chip ${SEG[code][1]}">${SEG[code][0]}</span>`;
  const priceChip = (r) => `<span class="tagst k3p ${CLS[r.price_class] || ''}">${esc(r.price_class)}</span>`;
  const bar = (v) => `<span class="k3bar" role="img" aria-label="equivalencia ${v} de 100"><i style="width:${Math.max(2, Math.min(100, v))}%"></i></span><b>${Number(v).toFixed(0)}</b>`;

  function priceChart(d) {
    const rows = d.filas.filter((r) => r.price_100ml != null && ['premium', 'funcional', 'economica'].includes(r.codigo)); if (!rows.length) return '<p class="muted">Sin precios por 100 mL para comparar.</p>';
    const own = d.propio.pvp_100ml, items = rows.map((r) => ({ l: (r.brand || r.asin || '').slice(0, 22), v: r.price_100ml, c: r.codigo, old: !['ACTUAL', 'RECIENTE'].includes(r.price_class) })).sort((a, b) => ({ premium: 0, funcional: 1, economica: 2 })[a.c] - ({ premium: 0, funcional: 1, economica: 2 })[b.c] || b.v - a.v);
    if (own) items.unshift({ l: 'ACTIVCORE (propuesto)', v: own, c: 'own', old: false });
    const W = 560, rh = 20, H = items.length * rh + 10, mx = Math.max(...items.map((i) => i.v)) || 1, col = { own: '#ffb02e', premium: '#b968ff', funcional: '#2ee6ff', economica: '#6c8bff' };
    return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Precio normalizado por 100 mL por segmento" class="k3svg">${items.map((it, i) => { const y = 4 + i * rh, w = Math.max(2, (it.v / mx) * 300);
      return `<text x="0" y="${y + 13}" font-size="11" fill="#8ea6bd">${esc(it.l)}</text><rect x="170" y="${y + 2}" width="${w}" height="12" rx="3" fill="${col[it.c]}" opacity="${it.old ? 0.35 : 0.95}" ${it.old ? 'stroke="#8ea6bd" stroke-dasharray="3 2"' : ''}></rect><text x="${176 + w}" y="${y + 13}" font-size="11" fill="#eaf6ff">${it.v.toFixed(1).replace('.', ',')} €${it.old ? ' · histórico' : ''}</text>`; }).join('')}</svg>
      <p class="muted">Barras con trazo discontinuo = precio HISTÓRICO (>30 d) o sin fecha: solo referencia. Colores: ámbar = ACTIVCORE, violeta = premium, cian = funcional, azul = económico.</p>`;
  }

  function panels(d) {
    return `<div class="k3panels">${['premium', 'funcional', 'economica'].map((c) => { const p = d.paneles[c]; return `<div class="k3panel ${SEG[c][1]}"><h4>${esc(SEG[c][2])}</h4><p><b>${p.n}</b> productos · <b>${p.n_precio_vigente}</b> con precio vigente · ${p.n_historico_o_sin_fecha} históricos/sin fecha · ${p.n_sin_precio} sin precio</p>
      ${p.estadisticos ? `<p>Mediana <b>${eur(p.estadisticos.mediana_100ml)}</b>/100 mL · rango ${eur(p.estadisticos.min_100ml)}–${eur(p.estadisticos.max_100ml)} (n=${p.estadisticos.n})</p>${p.posicion ? `<p class="muted">${p.posicion.mas_baratos} más baratos y ${p.posicion.mas_caros} más caros que ACTIVCORE (${eur(p.propio_100ml)}/100 mL)</p>` : ''}` : `<p><span class="tagst t-no">NO CONCLUYENTE</span> <span class="muted">${esc(p.estadisticos_nota || '')}</span></p>${(p.comparadores_individuales || []).map((x) => `<p class="muted">${esc(x.marca)}: ${eur(x.precio_100ml)}/100 mL (${x.vs_propio_pct >= 0 ? '+' : ''}${x.vs_propio_pct} % vs el propio · ${esc(x.clase)})</p>`).join('')}`}</div>`; }).join('')}</div>`;
  }

  function table(d) {
    const rows = d.filas; if (!rows.length) return '<p class="muted">Ningún producto cumple los filtros.</p>';
    return `<div class="k3-scroll"><table class="tbl k3tbl"><caption>Ranking por equivalencia (0-100). El precio NO puntúa.</caption><tr><th>#</th><th>Producto</th><th>Segmento</th><th>Equivalencia</th><th>Precio · fecha</th><th>€/100 mL</th><th>BSR*</th><th>Evidencia</th></tr>${rows.map((r, i) => `<tr class="k3row ${S.sel === r.key ? 'on' : ''}" data-k3="${esc(r.key)}" tabindex="0" role="button" aria-label="Ver ficha de ${esc(r.brand || r.asin)}"><td>${i + 1}</td>
      <td><b>${esc(r.brand || 'marca n/d')}</b><br><span class="muted">${esc((r.title || '').slice(0, 90))}</span><br><small>${r.asin ? esc(r.asin) + ' · ' + esc(r.country) : 'sin ASIN (maqueta)'}</small></td><td>${segChip(r.codigo)}${(r.review && r.review.estado !== 'AUTOMATICO') ? '<br><small>revisado</small>' : ''}</td><td>${bar(r.equivalencia)}</td>
      <td>${r.price == null ? '<span class="muted">sin precio vigente</span>' : eur(r.price)}<br>${priceChip(r)}${r.price_as_of ? `<br><small>${esc(String(r.price_as_of).slice(0, 10))}${r.price_age_days != null ? ' · hace ' + r.price_age_days + ' d' : ''}</small>` : ''}</td>
      <td>${eur(r.price_100ml)}</td><td>${r.bsr == null ? '<span class="muted">n/d</span>' : esc(r.bsr)}</td><td><small>${esc(r.automatic.evidencia)}</small></td></tr>`).join('')}</table></div><p class="muted">*BSR = ranking de categoría de Amazon, NO ventas.</p>`;
  }

  function detail(d) {
    const r = d.filas.find((x) => x.key === S.sel); if (!r) return '<article class="card c-cyan wide"><p class="muted">Selecciona un producto de la tabla para ver su ficha, la explicación de su segmento y confirmarlo o rechazarlo.</p></article>';
    const a = r.automatic, inf = r.infografia;
    const comps = Object.values(a.componentes).map((c) => `<tr><td>${esc(c.nombre)}</td><td>${c.peso} %</td><td>${c.puntos == null ? '<span class="tagst t-no">SIN DATOS</span>' : c.puntos.toFixed(1) + ' / ' + c.peso}</td><td><small>${esc(c.razon)}</small></td></tr>`).join('');
    const hist = (r.review && r.review.historial || []).map((h) => `<li>${esc(h.at.slice(0, 16).replace('T', ' '))} · ${esc(h.actor)} · <b>${esc(h.decision)}</b>${h.segmento ? ' → ' + esc(SEG[h.segmento][0]) : ''} — ${esc(h.motivo)}</li>`).join('');
    const canRev = C.canEdit();
    return `<article class="card c-violet wide k3detail"><h3>${esc(r.brand || '')} · ${esc((r.title || '').slice(0, 110))} ${segChip(r.codigo)}</h3>
      <div class="k3grid"><div class="k3img" role="img" aria-label="Sin imagen disponible"><span>Sin imagen</span><small>${esc(r.image_nota)}</small></div>
      <div><p><b>Segmento:</b> ${esc(r.segmento)} <span class="muted">(${esc(r.segmento_origen)})</span> · <b>Equivalencia:</b> ${a.equivalencia}/100 · <b>Cobertura de evidencia:</b> ${Math.round(a.cobertura * 100)} %</p>
      <p><b>Función y aplicación:</b> necesidad ${esc((a.necesidades[0] || 'no identificada').replace(/_/g, ' '))} · tipo ${esc(a.tipo || 'n/d')} · zona ${esc((a.zona || 'n/d').replace(/_/g, ' '))} · ${a.leave_on === true ? 'sin aclarado' : a.leave_on === false ? 'con aclarado' : 'aclarado no confirmado'}</p>
      <p><b>Activos documentados:</b> ${a.activos.length ? esc(a.activos.join(', ')) + (inf ? ' <span class="tagst t-wait">MAQUETA</span>' : '') : '<span class="muted">NO DOCUMENTADOS</span>'} · <b>Volumen:</b> ${a.volumen_ml ? a.volumen_ml + ' mL (' + esc(a.volumen_fuente) + ')' : 'n/d'} · <b>Marca:</b> ${esc(a.marca_tier)}</p>
      <p><b>Precio observado:</b> ${r.price == null ? 'sin precio vigente' : eur(r.price)} ${priceChip(r)}${r.price_as_of ? ' · ' + esc(String(r.price_as_of).slice(0, 10)) : ''} · <b>€/100 mL:</b> ${eur(r.price_100ml)} · <b>Coste/día:</b> ${r.cost_day == null ? '<span class="muted">' + esc(r.cost_day_nota) + '</span>' : eur(r.cost_day)}${inf && inf.pvp_maqueta_eur ? `<br><span class="tagst t-wait">MAQUETA</span> PVP de la infografía ${eur(inf.pvp_maqueta_eur)} (sin fecha ni fuente: NO es precio actual)${inf.dosis ? ' · pauta: ' + esc(inf.dosis) : ''}` : ''}</p>
      <p>${r.url ? `<a href="${esc(r.url)}" target="_blank" rel="noopener noreferrer">Ver en Amazon</a>` : '<span class="muted">sin enlace (referencia sin ASIN)</span>'} · evidencia: ${esc(a.evidencia)}</p></div></div>
      <p class="k3why"><b>Por qué:</b> ${esc(a.explicacion)}. <b>Elegibilidad (etapa A):</b> ${esc(a.elegibilidad.estado)} — ${esc(a.elegibilidad.razones.join('; '))}.${a.premium.falla.length && a.codigo !== 'no_comparable' && r.codigo !== 'premium' ? ' <b>No es premium porque:</b> ' + esc(a.premium.falla.join('; ')) + '.' : ''}</p>
      <div class="k3-scroll"><table class="tbl"><caption>Desglose de la equivalencia (el precio no interviene)</caption><tr><th>Variable</th><th>Peso</th><th>Puntos</th><th>Razón</th></tr>${comps}</table></div>
      ${a.faltan.length ? `<p class="muted"><b>Faltan para afinar:</b> ${esc(a.faltan.join('; '))}.</p>` : ''}
      <h4>Revisión manual</h4>${canRev ? `<div class="k3rev"><label>Justificación (obligatoria)<input id="k3Why" maxlength="300" placeholder="Por qué confirmas o rechazas"></label><label>Segmento si confirmas<select id="k3Seg">${['premium', 'funcional', 'economica', 'pendiente', 'no_comparable'].map((c) => `<option value="${c}" ${c === r.automatic.codigo ? 'selected' : ''}>${esc(SEG[c][0])}</option>`).join('')}</select></label>
      <button class="btn sm" id="k3Ok">CONFIRMAR</button><button class="btn ghost sm" id="k3No">RECHAZAR (no es competidor)</button><button class="btn ghost sm" id="k3Reset">RESTABLECER</button></div>` : '<p class="muted">Solo aprobador/administrador puede confirmar o rechazar.</p>'}
      <ul class="k3hist">${hist || '<li class="muted">Sin decisiones humanas: clasificación automática.</li>'}</ul>${S.msg ? `<p class="${S.msg.startsWith('✔') ? 'good' : 'bad'}" role="status">${esc(S.msg)}</p>` : ''}</article>`;
  }

  function html() {
    const d = S.data; if (!d) return `<article class="card c-cyan wide"><p class="muted">Cargando segmentación…</p></article>`;
    if (!d.disponible) return `<article class="card c-amber wide"><h3>Segmentación K3</h3><p class="muted">${esc(d.motivo || 'No disponible para este producto.')}</p></article>`;
    const cn = d.conteo, tot = d.n_total, f = S.f; const chips = [['', 'Todos', tot]].concat(Object.keys(SEG).map((c) => [c, SEG[c][0], cn[c] || 0]));
    const actives = ['cafeina', 'luteolina', 'urea', 'mentol', 'aminexil', 'niacinamida', 'peptidos', 'capixyl', 'redensyl', 'pdrn', 'romero'];
    return `<article class="card c-cyan wide k3root"><h3>Segmentación competitiva K3 <small>motor de equivalencia comercial · ${esc(d.version)} · revisable</small></h3>
      <p class="muted">${esc(d.aviso_evidencia)} ${esc(d.nota_precio)}</p>
      <p><b>${esc(d.propio.nombre)}</b>: ${eur(d.propio.pvp)} (${esc(d.propio.pvp_estado)}) · <b>${eur(d.propio.pvp_100ml)}</b>/100 mL · coste/día ${d.propio.coste_dia == null ? 'NO DISPONIBLE' : eur(d.propio.coste_dia) + ' <span class="tagst t-wait">TEÓRICO</span>'}</p>
      <div class="euchips" role="group" aria-label="Selector de segmento">${chips.map(([c, t, n]) => `<button class="euchip k3seg ${f.segmento === c ? 'on' : ''}" data-k3seg="${c}" aria-pressed="${f.segmento === c}">${esc(t)} <small>${n}</small></button>`).join('')}</div>
      <div class="k3filters"><label>País<select id="k3F-country"><option value="">Todos</option>${['ES', 'DE', 'FR', 'IT'].map((c) => `<option ${f.country === c ? 'selected' : ''}>${c}</option>`).join('')}</select></label>
      <label>Activo<select id="k3F-activo"><option value="">Todos</option>${actives.map((c) => `<option ${f.activo === c ? 'selected' : ''}>${c}</option>`).join('')}</select></label>
      <label>Volumen mín. (mL)<input id="k3F-min" type="number" min="0" value="${esc(f.min_ml)}"></label><label>Volumen máx. (mL)<input id="k3F-max" type="number" min="0" value="${esc(f.max_ml)}"></label>
      <label>Aplicación<select id="k3F-app"><option value="">Todas</option>${['serum', 'locion', 'aceite', 'cuero_cabelludo'].map((c) => `<option ${f.aplicacion === c ? 'selected' : ''}>${c}</option>`).join('')}</select></label><button class="btn sm" id="k3Apply">Aplicar filtros</button></div>
      <p class="muted">${d.n_visibles} de ${tot} productos visibles${d.duplicados.length ? ' · ' + d.duplicados.length + ' duplicado(s) descartado(s)' : ''}.</p></article>
      <article class="card c-violet wide"><h3>Benchmark por segmento <small>nunca se mezclan medianas entre segmentos</small></h3>${panels(d)}<h4>Precio normalizado por 100 mL</h4>${priceChart(d)}</article>
      <article class="card c-cyan wide"><h3>Ranking por equivalencia</h3>${table(d)}</article>${detail(d)}`;
  }

  async function reviewCall(decision) {
    const why = ($('#k3Why') || {}).value || '', seg = ($('#k3Seg') || {}).value;
    const r = await C.api('POST', '/api/eu/k3/revision', { product: C.E.pid, key: S.sel, decision, segmento: seg, motivo: why });
    S.msg = r.ok ? '✔ Decisión registrada con tu usuario, fecha y justificación.' : (r.j && r.j.error) || 'No se pudo registrar'; if (r.ok) { await load(); } C.render();
  }

  function bind() {
    if (C.E.view !== 'segmentos') return;
    const reload = async () => { await load(); C.render(); };
    $$('[data-k3seg]').forEach((b) => (b.onclick = () => { S.f.segmento = b.dataset.k3seg; reload(); }));
    const apply = () => { S.f.country = $('#k3F-country').value; S.f.activo = $('#k3F-activo').value; S.f.min_ml = $('#k3F-min').value; S.f.max_ml = $('#k3F-max').value; S.f.aplicacion = $('#k3F-app').value; reload(); };
    $('#k3Apply') && ($('#k3Apply').onclick = apply);
    $$('[data-k3]').forEach((tr) => { const open = async () => { S.sel = tr.dataset.k3; S.msg = ''; await explain(S.sel); C.render(); const dt = $('.k3detail'); if (dt && dt.scrollIntoView) dt.scrollIntoView({ block: 'nearest' }); }; tr.onclick = open; tr.onkeydown = (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); } }; });
    $('#k3Ok') && ($('#k3Ok').onclick = () => reviewCall('CONFIRMAR')); $('#k3No') && ($('#k3No').onclick = () => reviewCall('RECHAZAR')); $('#k3Reset') && ($('#k3Reset').onclick = () => reviewCall('RESTABLECER'));
  }

  root.K3UI = { init: (ctx) => { C = ctx; }, load, html, bind, state: S };
})(typeof window !== 'undefined' ? window : globalThis);
