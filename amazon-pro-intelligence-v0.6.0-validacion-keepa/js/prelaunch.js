/* Interfaz del expediente Pre-Launch (V0.2). La decisión la calcula Dossier.evaluate(): aquí solo se edita y se muestra. */
(function (root) {
  const D = root.Dossier, E = root.Econ;
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const today = () => new Date().toISOString().slice(0, 10);
  let M = null, result = null;

  function load() { try { const j = JSON.parse(localStorage.getItem('api_dossier') || 'null'); if (j && j.product && j.econ) return D.retemplate(j); } catch (e) { /* sin storage */ } return D.createEmpty('cosmetico', 'FBA'); }
  function save() { try { localStorage.setItem('api_dossier', JSON.stringify(M)); } catch (e) { /* ok */ } }
  function getp(path) { return path.split('.').reduce((o, k) => (o == null ? o : o[k]), M); }
  function setp(path, v) { const ks = path.split('.'), last = ks.pop(); ks.reduce((o, k) => o[k], M)[last] = v; }
  const parse = (el) => { const t = el.dataset.t; if (t === 'num') return el.value === '' ? NaN : +el.value; if (t === 'nnum') return el.value === '' ? null : +el.value; return el.value; };

  const f = (path, label, t, extra) => `<label class="fld">${label}<input data-m="${path}" data-t="${t || 'num'}" type="${t === 'text' ? 'text' : t === 'date' ? 'date' : 'number'}" step="any" value="${esc(getp(path))}" ${extra || ''}></label>`;
  const sel = (path, label, opts) => `<label class="fld">${label}<select data-m="${path}" data-t="text" data-re="1">${opts.map(([v, l]) => `<option value="${v}" ${getp(path) === v ? 'selected' : ''}>${esc(l)}</option>`).join('')}</select></label>`;
  const checklist = (base, items) => Object.entries(items).map(([id, it]) => `<div class="ckrow"><span>${esc(it.label)}${it.critical ? '<span class="crit">OBLIGATORIO</span>' : ''}</span>
    <select data-m="${base}.${id}.status" data-t="text">${[['pendiente', 'Pendiente'], ['cumplido', 'Cumplido'], ['no_aplica', 'No aplica']].map(([v, l]) => `<option value="${v}" ${it.status === v ? 'selected' : ''}>${l}</option>`).join('')}</select>
    <input data-m="${base}.${id}.evidence" data-t="text" type="text" placeholder="Evidencia / referencia / justificación" value="${esc(it.evidence)}"></div>`).join('');
  const sec = (id, title, body) => `<details class="sec card c-cyan" data-sec="${id}" ${openSecs.has(id) ? 'open' : ''}><summary>${title}<span class="chip ok" data-chip="${id}">…</span></summary>${body}</details>`;
  const openSecs = new Set(['producto', 'economia', 'benchmark']);

  function renderLeft() {
    const L = document.getElementById('plLeft'), top = L.scrollTop;
    $$('details.sec', L).forEach((d) => (d.open ? openSecs.add(d.dataset.sec) : openSecs.delete(d.dataset.sec)));
    const e = M.econ, custom = e.feeSchedule === 'personalizado';
    const bench = `<table class="tbl"><tr><th>Competidor</th><th>ASIN</th><th>PVP € (IVA)</th><th>Envío €</th><th>Uds/pack</th><th>Contenido</th><th>Fuente</th><th>Fecha</th><th>€/${esc(M.product.contentUnit)}</th><th></th></tr>
      ${M.competitors.map((c, i) => `<tr><td><input data-m="competitors.${i}.name" data-t="text" type="text" value="${esc(c.name)}"></td><td><input data-m="competitors.${i}.asin" data-t="text" type="text" value="${esc(c.asin)}"></td>
        <td><input data-m="competitors.${i}.priceGross" data-t="num" type="number" step="any" value="${esc(c.priceGross)}"></td><td><input data-m="competitors.${i}.shipping" data-t="num" type="number" step="any" value="${esc(c.shipping)}"></td>
        <td><input data-m="competitors.${i}.packUnits" data-t="num" type="number" step="any" value="${esc(c.packUnits)}"></td><td><input data-m="competitors.${i}.contentValue" data-t="num" type="number" step="any" value="${esc(c.contentValue)}"></td>
        <td><input data-m="competitors.${i}.source" data-t="text" type="text" value="${esc(c.source)}" placeholder="p. ej. Keepa"></td><td><input data-m="competitors.${i}.date" data-t="date" type="date" value="${esc(c.date)}"></td>
        <td class="ro" data-bm="${i}">—</td><td><button class="btn no sm" data-del="competitors.${i}" aria-label="Eliminar">✕</button></td></tr>`).join('')}</table>
      <button class="btn ghost sm" data-add="competitor">+ Competidor</button><p class="note">Se compara el precio por unidad de contenido (envío incluido), no el PVP. Se excluyen datos sin fuente/fecha, con más de ${D.MAX_COMP_AGE} días, duplicados y atípicos. Mínimo ${D.MIN_COMP} válidos.</p>`;
    const kw = `<table class="tbl"><tr><th>Keyword</th><th>Volumen/mes</th><th>Fuente</th><th>Fecha</th><th></th></tr>
      ${M.keywords.map((k, i) => `<tr><td><input data-m="keywords.${i}.keyword" data-t="text" type="text" value="${esc(k.keyword)}"></td><td><input data-m="keywords.${i}.volume" data-t="num" type="number" value="${esc(k.volume)}"></td>
        <td><input data-m="keywords.${i}.source" data-t="text" type="text" value="${esc(k.source)}" placeholder="p. ej. Helium 10 export"></td><td><input data-m="keywords.${i}.date" data-t="date" type="date" value="${esc(k.date)}"></td>
        <td><button class="btn no sm" data-del="keywords.${i}" aria-label="Eliminar">✕</button></td></tr>`).join('')}</table>
      <button class="btn ghost sm" data-add="keyword">+ Keyword</button><p class="note">Cada dato necesita fuente y fecha (≤ ${D.MAX_KW_AGE} días). Mínimo recomendado: ${D.MIN_KW}.</p>`;
    const claims = `<table class="tbl"><tr><th>Claim del listing</th><th>Evidencia (estudio, ensayo, autorización)</th><th></th></tr>${(M.claims || []).map((c, i) => `<tr><td><input data-m="claims.${i}.text" data-t="text" type="text" value="${esc(c.text)}"></td><td><input data-m="claims.${i}.evidence" data-t="text" type="text" value="${esc(c.evidence)}"></td><td><button class="btn no sm" data-del="claims.${i}" aria-label="Eliminar">✕</button></td></tr>`).join('')}</table><button class="btn ghost sm" data-add="claim">+ Claim</button>`;
    L.innerHTML = `<div class="card c-lime" style="margin-bottom:8px"><h3>Pre-Launch · expediente <small>evaluar antes de publicar; no publica nada</small></h3>
      <div style="display:flex;gap:6px;flex-wrap:wrap"><button class="btn ghost sm" data-ex="economia">Ejemplo DEMO: solo economía</button><button class="btn ghost sm" data-ex="completo">Ejemplo DEMO: completo</button><button class="btn ghost sm" data-ex="nogo">Ejemplo DEMO: inviable</button><button class="btn no sm" data-ex="vacio">Vaciar</button></div></div>
      ${sec('producto', 'Producto', `<div class="grid2"><label class="fld full">Nombre<input data-m="product.name" data-t="text" type="text" value="${esc(M.product.name)}"></label>
        ${sel('product.regType', 'Tipo regulatorio', [['cosmetico', 'Cosmético'], ['suplemento', 'Complemento alimenticio'], ['otro', 'Otro producto']])}
        ${f('product.ownPackUnits', 'Uds/pack propio')}${f('product.ownContent', 'Contenido propio (por ud)')}${f('product.contentUnit', 'Unidad (ml, g…)', 'text')}</div>`)}
      ${sec('economia', 'Economía unitaria y precio', `<div class="grid2">${f('econ.price', 'PVP con IVA (€)')}${f('econ.vatPct', 'IVA (%)')}${sel('econ.feeSchedule', 'Comisión por categoría', Object.entries(E.FEE_SCHEDULES).map(([k, v]) => [k, v.label]))}
        ${custom ? f('econ.customReferralPct', 'Comisión personalizada (%)') + f('econ.customMinFee', 'Comisión mínima (€)') : ''}
        ${f('econ.cost', 'Coste producto (€)')}${f('econ.prep', 'Prep./etiquetado (€)')}${sel('econ.fulfilMode', 'Logística', [['FBA', 'FBA'], ['FBM', 'FBM']])}
        ${e.fulfilMode === 'FBA' ? f('econ.fbaFee', 'Tarifa FBA (€)') + f('econ.storageMonthly', 'Almacenaje €/ud/mes') + f('econ.storageMonths', 'Meses en almacén') : f('econ.fbmShipping', 'Envío FBM (€)') + f('econ.fbmPackaging', 'Embalaje FBM (€)') + f('econ.fbmHandling', 'Manipulación FBM (€)')}
        ${f('econ.returnsPct', 'Devoluciones (%)')}${f('econ.returnProcessing', 'Coste por devolución (€)')}${f('econ.unsellablePct', '% devueltas no vendibles')}${f('econ.otherCosts', 'Otros costes (€)')}
        ${f('econ.acosTarget', 'ACoS objetivo (%)')}${sel('econ.adsBasis', 'Base del ACoS', [['gross', 'PVP con IVA (informes Ads)'], ['net', 'Ingreso neto']])}${f('econ.minMarginPct', 'Margen mínimo (%)')}</div>
        <p class="note">Las tarifas de comisión son orientativas y no verificadas: confirma en Amazon antes de operar.</p>`)}
      ${sec('benchmark', 'Benchmarking de competidores (normalizado)', bench)}
      ${sec('demand', 'Demanda y keywords', kw)}
      ${sec('regulatory', 'Regulatorio y claims', `<p class="note">Plantilla orientativa por tipo de producto. No es asesoramiento legal: valídala con tu responsable regulatorio.</p>${checklist('regulatory', M.regulatory)}<h3 style="margin-top:10px;font-size:14px">Claims</h3>${claims}`)}
      ${sec('content', 'Ficha, imágenes, vídeo y A+', `<p class="note">El texto del título/bullets se escribe en «Evidencia» para detectar claims de riesgo.</p>${checklist('content', M.content)}`)}
      ${sec('logistics', 'Stock y logística', `<div class="grid2">${sel('logistics.mode', 'Modo', [['FBA', 'FBA'], ['FBM', 'FBM']])}${f('logistics.stockAvailable', 'Stock disponible (uds)', 'nnum')}${f('logistics.forecastUnitsMonth', 'Previsión (uds/mes)', 'nnum')}${f('logistics.leadTimeDays', 'Plazo reposición (días)', 'nnum')}${f('logistics.coverTargetDays', 'Cobertura objetivo (días)')}</div>${checklist('logistics.items', M.logistics.items)}`)}`;
    L.scrollTop = top; refresh();
  }
  const $$ = (s, r) => [...(r || document).querySelectorAll(s)];

  function refresh() {
    result = D.evaluate(M, today()); const R = result, A = root.APP;
    const lab = { benchmark: 'benchmark', demand: 'demand', price: 'economia', regulatory: 'regulatory', content: 'content', logistics: 'logistics' };
    const sym = { ok: '✔ OK', warn: '⚠ avisos', block: '⛔ bloqueo', nogo: '✘ inviable' };
    Object.entries(R.sectionStatus).forEach(([s, st]) => { const el = document.querySelector(`[data-chip=${lab[s]}]`); if (el) { el.className = 'chip ' + (st === 'warn' ? 'warn' : st); el.textContent = sym[st]; } });
    const pe = document.querySelector('[data-chip=producto]'); if (pe) { pe.className = 'chip ok'; pe.textContent = M.product.name ? '✔' : '—'; }
    const bm = R.sections.benchmark; $$('[data-bm]').forEach((td) => { const r = bm.perRow[+td.dataset.bm]; td.className = 'ro ' + (r ? (r.ok ? 'good' : 'bad') : ''); td.textContent = r ? (r.ok ? r.unitPrice.toFixed(3) + ' ✔' : r.reason) : '—'; });
    A.S.dossierSummary = M.product.name ? [{ name: M.product.name, decision: R.decision, blockers: R.counts.nogo + R.counts.block, warnings: R.counts.warn }] : [];
    renderRight(R);
  }

  function renderRight(R) {
    const u = R.sections.unit, cls = R.decision === 'NO-GO' ? 'NOGO' : R.decision, mp = R.sections.minPrice, band = R.sections.band, A = root.APP;
    const grp = (sev, title) => { const fs = R.findings.filter((x) => x.severity === sev); return fs.length ? `<div class="sevh">${title} (${fs.length})</div>` + fs.map((x) => `<div class="fnd ${sev}"><b>${esc(x.title)}</b>${esc(x.why)}<div class="fx">→ ${esc(x.fix)}</div></div>`).join('') : ''; };
    let econ = '<p class="muted">Corrige los datos económicos para ver el cálculo.</p>';
    if (u.valid) econ = `<p style="font-size:13px">Ingreso neto <b>${u.net.toFixed(2)} €</b> · comisión ${u.referral.toFixed(2)} € · contribución/ud <b>${u.contribution.toFixed(2)} €</b> (<b>${(u.contributionPct * 100).toFixed(1)} %</b> s/neto)<br>ACoS de equilibrio <b>${(u.breakEvenAcos * 100).toFixed(1)} %</b> (${u.input.adsBasis === 'gross' ? 'base PVP con IVA' : 'base neto'}) · precio mínimo rentable <b>${mp ? mp.commercial.toFixed(2) + ' €' : 'inalcanzable'}</b></p><div id="plStack"></div>`;
    let bandHtml = '';
    if (u.valid && (band || mp)) {
      const vals = [u.price, mp && mp.commercial, band && band.low, band && band.high].filter((x) => x != null), lo = Math.min(...vals) * 0.9, hi = Math.max(...vals) * 1.08, X = (v) => ((v - lo) / (hi - lo) * 100).toFixed(1) + '%';
      bandHtml = `<h3 style="margin-top:8px;font-size:14px">Precio vs banda competitiva</h3><div class="band">${band ? `<div class="bar" style="left:${X(band.low)};width:calc(${X(band.high)} - ${X(band.low)})"></div>` : ''}
        <div class="mk" style="left:${X(u.price)};background:#18e6ff"><span style="color:#18e6ff">Tu precio ${u.price.toFixed(2)}</span></div>${mp ? `<div class="mk" style="left:${X(mp.commercial)};background:#ffb02e;top:-10px;height:46px"><span style="color:#ffb02e;top:44px">Mín. rentable ${mp.commercial.toFixed(2)}</span></div>` : ''}</div>
        <p class="note">${band ? `Banda (P25–P75 normalizado a tu formato): ${band.low.toFixed(2)} – ${band.high.toFixed(2)} €` : 'Sin banda: benchmark insuficiente.'}</p>`;
    }
    document.getElementById('plRight').innerHTML = `<article class="card c-${R.decision === 'GO' ? 'lime' : R.decision === 'REVISAR' ? 'amber' : 'pink'}"><h3>Decisión <small>${esc(M.product.name || 'sin nombre')}</small></h3>
      <div class="dec2 ${cls}">${R.decision}</div><p style="margin:6px 0">${esc(R.summary)}</p>
      <p style="font-size:12.5px"><b>${R.counts.nogo}</b> inviabilidad · <b>${R.counts.block}</b> bloqueos · <b>${R.counts.warn}</b> avisos</p>
      <p class="note">Un margen positivo no basta: GO exige economía, benchmark, demanda, regulatorio, contenido y stock documentados.</p>
      <p style="margin-top:6px"><button class="btn warn" id="plApprove" ${R.decision === 'GO' ? '' : 'disabled'}>Solicitar aprobación para publicar</button></p></article>
      <article class="card c-cyan" style="margin-top:8px"><h3>Economía <small>por unidad</small></h3>${econ}${bandHtml}</article>
      <article class="card c-violet" style="margin-top:8px"><h3>Bloqueos y avisos <small>qué impide lanzar y cómo resolverlo</small></h3>${grp('nogo', 'Inviabilidad')}${grp('block', 'Bloqueos')}${grp('warn', 'Avisos')}${R.findings.length ? '' : '<p class="muted">Sin hallazgos.</p>'}</article>`;
    if (u.valid) root.Charts.stack(document.getElementById('plStack'), u.costBreakdown.map(([l, v], i) => ({ label: l, value: v, color: ['#18e6ff', '#7aa2ff', '#b968ff', '#ff9f43', '#ffb02e', '#ff5d5d', '#8ea6bd', '#ff4fd8'][i] })).concat([{ label: 'Contribución', value: Math.max(0, u.contribution), color: '#b6ff2e' }]));
    const b = document.getElementById('plApprove'); if (b) b.onclick = () => { root.APP.addApproval({ type: 'Publicación', title: `Publicar ${M.product.name || 'producto'} a ${u.price.toFixed(2)} €`, detail: `Expediente GO: ${R.counts.warn} aviso(s). La aprobación solo se registra; no se publica nada.`, source: 'Pre-Launch' }); b.disabled = true; b.textContent = 'En cola de aprobación'; };
  }

  function wire() {
    const L = document.getElementById('plLeft');
    L.addEventListener('input', (e) => { const el = e.target; if (!el.dataset.m || el.dataset.re) return; setp(el.dataset.m, parse(el)); save(); refresh(); });
    L.addEventListener('change', (e) => {
      const el = e.target; if (!el.dataset.m) return; setp(el.dataset.m, parse(el));
      if (el.dataset.m === 'product.regType' || el.dataset.m === 'logistics.mode') { if (el.dataset.m === 'logistics.mode') M.econ.fulfilMode = M.logistics.mode; D.retemplate(M); save(); renderLeft(); }
      else if (el.dataset.m === 'econ.fulfilMode') { M.logistics.mode = M.econ.fulfilMode; D.retemplate(M); save(); renderLeft(); }
      else if (el.dataset.m === 'econ.feeSchedule') { save(); renderLeft(); }
      else { save(); refresh(); }
    });
    L.addEventListener('click', (e) => {
      const b = e.target.closest('button'); if (!b) return;
      if (b.dataset.ex) { M = b.dataset.ex === 'vacio' ? D.createEmpty('cosmetico', 'FBA') : D.example(b.dataset.ex, today()); D.retemplate(M); save(); renderLeft(); }
      else if (b.dataset.add) { const t = b.dataset.add; if (t === 'competitor') M.competitors.push({ name: '', asin: '', priceGross: null, shipping: 0, packUnits: 1, contentValue: null, source: '', date: today() }); if (t === 'keyword') M.keywords.push({ keyword: '', volume: null, source: '', date: today() }); if (t === 'claim') M.claims.push({ text: '', evidence: '' }); save(); renderLeft(); }
      else if (b.dataset.del) { const [k, i] = b.dataset.del.split('.'); M[k].splice(+i, 1); save(); renderLeft(); }
    });
  }
  root.PrelaunchUI = { init() { M = load(); wire(); renderLeft(); }, render() { renderLeft(); }, setModel(m) { M = D.retemplate(m); save(); renderLeft(); }, get result() { return result; }, get model() { return M; } };
})(self);
