/* Amazon Pro Intelligence V0.3.3 — capa de servidor: sesión, cuentas, Director IA, coworkers reales, piloto PHIVITAL, historial/auditoría, noticias verificadas.
   No hay claves en el navegador: solo cookie de sesión HttpOnly + token CSRF en memoria. */
(function (root) {
  const $ = (s, r) => (r || document).querySelector(s), $$ = (s, r) => [...(r || document).querySelectorAll(s)];
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const V = { user: null, role: null, csrf: null, account: null, accounts: [], dossiers: [], dossierId: null, P: null, origin: null, ai: null, cw: null, ev: null, chat: [] };
  const today = () => new Date().toISOString().slice(0, 10);
  const CW = { mercado: 'Analiza competidores importados, precio normalizado y banda', precios: 'Economía determinista, escenarios de PVP y ACoS de equilibrio', seo: 'Keywords vigentes y cobertura del listing', ppc: 'Colchón de ACoS y CPC máximo (con CVR aportada)', creatividad: 'Activos de contenido pendientes y briefs', inventario: 'Cobertura de stock y reposición', cumplimiento: 'Checklist regulatorio, claims y términos de riesgo' };

  async function api(method, path, body) {
    if (V.viewer && method !== 'GET' && path !== '/api/login' && path !== '/api/logout') return { ok: false, status: 403, j: { error: 'Solo lectura: el usuario viewer no puede modificar ni ejecutar nada' } };
    const h = {}; if (body !== undefined) h['Content-Type'] = 'application/json'; if (method === 'POST' && V.csrf) h['X-CSRF-Token'] = V.csrf;
    try { const r = await fetch(path, { method, headers: h, credentials: 'same-origin', body: body !== undefined ? JSON.stringify(body) : undefined }); let j = null; try { j = await r.json(); } catch (e) { /* sin cuerpo */ } return { ok: r.ok, status: r.status, j: j || {} }; }
    catch (e) { return { ok: false, status: 0, j: { error: 'servidor no disponible' } }; }
  }
  const acct = () => V.account;

  /* ---------- sesión ---------- */
  function loginForm(msg, u0) {
    root.APP.openModal(`<h3>Acceso <small>sesión local · solo 127.0.0.1</small></h3>${msg ? `<div class="f warn">${esc(msg)}</div>` : ''}
      <form id="lgForm"><label class="fld">Usuario<input id="lgU" autocomplete="username" value="${esc(u0 || '')}"></label><label class="fld">Contraseña<input id="lgP" type="password" autocomplete="current-password"></label>
      <p style="margin-top:8px"><button class="btn" id="lgGo">Entrar</button></p></form><p class="muted">El primer arranque muestra la contraseña del usuario «admin» en la consola del servidor.</p>`);
    $('#lgForm').onsubmit = async (e) => { e.preventDefault(); const r = await api('POST', '/api/login', { username: $('#lgU').value, password: $('#lgP').value }); if (!r.ok) return loginForm(r.j.error || 'Error de acceso', $('#lgU').value); $('#modal').hidden = true; setRole(r.j.role); V.user = r.j.user; V.csrf = r.j.csrf; await boot(); };
  }
  function setRole(r) { V.roleReal = r; V.viewer = r === 'viewer'; V.role = V.viewer ? 'admin' : r; document.body.classList.toggle('viewer', V.viewer); if (V.viewer) lockUi(); }
  /* viewer: la interfaz bloquea además lo que ya bloquea el backend (403) */
  function lockUi() {
    const W = /(guardar|crear|nuevo|nueva|aprobar|rechazar|lanzar|ejecutar|analizar|importar|publicar|activar|archivar|añadir|editar|enviar|proponer|investigar|reanudar|probar|confirmar|eliminar|borrar|registrar|validar|generar|iniciar|aplicar|actualizar|solicitar|reconciliar|fijar|cancelar plan|descartar|marcar|verificar|(?:^|\s)subir|(?:^|\s)cargar|restaurar|respaldo|preguntar|consultar al|enviar)/i;
    const apply = () => document.querySelectorAll('button, textarea, input[type=submit], form input[type=text]').forEach((el) => { if (el.closest('#tabs') || el.closest('#lgForm') || el.matches('#lgOut,#lgOpen,.ro-ok,[data-tab]')) return; const w = el.tagName !== 'BUTTON' || el.type === 'submit' || el.hasAttribute('data-test') || W.test(el.textContent || ''); if (w && !el.disabled) { el.disabled = true; el.title = 'Solo lectura (viewer)'; el.classList.add('vro'); } });
    if (!lockUi.mo) { lockUi.mo = new MutationObserver(() => { clearTimeout(lockUi.t); lockUi.t = setTimeout(apply, 30); }); lockUi.mo.observe(document.body, { childList: true, subtree: true }); }
    apply();
  }
  async function boot() {
    const a = await api('GET', '/api/accounts'); V.accounts = a.j.accounts || []; V.account = (V.accounts.find((x) => x.id === V.account) || V.accounts.find((x) => !['activcore-eu', 'catalogo-aht', 'sintetico-primera-llamada'].includes(x.id)) || V.accounts[0] || {}).id || null;
    const s = await api('GET', '/api/ai/status'); V.ai = s.j; V.usage = null; if (V.role === 'admin') { const u = await api('GET', '/api/ai/usage'); V.usage = u.ok ? u.j : null; } renderSession(); await refreshAll();
  }
  async function refreshAll() { if (!acct()) return renderAll(); await Promise.all([loadDossiers(), loadCw(), loadNews()]); renderAll(); }
  async function loadSynth() { V.synth = null; const a = (V.accounts || []).find((x) => x.id === 'sintetico-primera-llamada'); if (!a) return; const r = await api('GET', `/api/records?account=${a.id}&kind=dossier`); const d = (r.j.records || [])[0]; if (d) V.synth = { account: a.id, id: d.id, name: d.data.name, origin: d.data.origin }; }
  async function loadDossiers() { const r = await api('GET', `/api/records?account=${acct()}&kind=dossier`); V.dossiers = r.j.records || []; await loadSynth(); if (!V.dossiers.find((d) => d.id === V.dossierId)) V.dossierId = V.dossiers.length ? V.dossiers[0].id : null; const d = V.dossiers.find((x) => x.id === V.dossierId); V.P = d ? d.data.dossier : null; V.origin = d ? d.data.origin : null; }
  async function loadCw() { const r = await api('GET', `/api/coworkers/status?account=${acct()}`); V.cw = r.ok ? r.j : null; }
  let NEWS = [];
  async function loadNews() { const r = await api('GET', `/api/news?account=${acct()}`); NEWS = r.ok ? r.j.news || [] : []; }

  function renderSession() {
    const el = $('#sess'); if (!el) return;
    if (!V.user) { el.innerHTML = '<button class="btn sm" id="lgOpen">Iniciar sesión</button>'; $('#lgOpen').onclick = () => loginForm(); return; }
    el.innerHTML = `<span class="sessu">${esc(V.user)} · ${esc(V.roleReal || V.role)}</span><select id="acSel" title="Cuenta (titular legal y Seller Central)">${V.accounts.map((a) => `<option value="${esc(a.id)}" ${a.id === V.account ? 'selected' : ''}>${esc(a.name)} · ${esc(a.legal_entity)} · ${esc(a.marketplaces.join(','))}</option>`).join('')}</select><button class="btn ghost sm" id="lgOut">Salir</button>`;
    $('#acSel').onchange = async (e) => { V.account = e.target.value; V.dossierId = null; V.chat = []; await refreshAll(); };
    $('#lgOut').onclick = async () => { await api('POST', '/api/logout', {}); Object.assign(V, { viewer: false, roleReal: null, user: null, role: null, csrf: null, account: null, dossiers: [], P: null, cw: null }); renderSession(); renderAll(); };
  }

  /* ---------- Director ---------- */
  const modeTag = (m) => ({ SIN_IA: 'SIN IA', SIMULADA: 'SIMULADA · no es IA real', PRUEBA_LOCAL: 'PRUEBA LOCAL · no es IA real', REAL: 'IA REAL' }[m] || m);
  function renderDirector() {
    const ai = V.ai; $('#dirEngine').innerHTML = !V.user ? 'Inicia sesión para usar el Director (análisis en servidor).' : ai ? `Proveedor: <b>${esc(ai.provider)}</b>${ai.model ? ' · modelo <b>' + esc(ai.model) + '</b>' : ''} · ${esc(ai.status)}${V.usage && V.usage.monthly_budget != null ? ' · gasto real del mes: <b>' + V.usage.real_cost.toFixed(4) + ' / ' + V.usage.monthly_budget + ' ' + esc(V.usage.currency) + '</b>' + (V.usage.uncertain_calls ? ' · <b class="bad">' + V.usage.uncertain_calls + ' consumo(s) INCIERTO(s): conciliar con el panel de OpenAI</b>' : '') : ''}` : '…';
    const sel = $('#dirDossier'); sel.innerHTML = '<option value="">— expediente —</option>' + V.dossiers.map((d) => `<option value="${esc(d.id)}" ${d.id === V.dossierId && !V.synthSel ? 'selected' : ''}>${esc(d.data.name)} · ${esc(d.data.origin)}</option>`).join('') + (V.synth ? `<option value="__synth__" ${V.synthSel ? 'selected' : ''}>🧪 ${esc(V.synth.name)} · ${esc(V.synth.origin)} (prueba segura de la API)</option>` : '');
    $('#chat').innerHTML = (V.chat.length ? V.chat : [{ text: 'Soy el Director Amazon. Asigno tareas a 7 coworkers deterministas, coordino sus resultados y, si hay proveedor de IA, redacto la síntesis. Sin IA configurada respondo con el resumen determinista (etiquetado SIN IA). No ejecuto cambios en Amazon.' }])
      .map((m) => `<div class="msg ${m.me ? 'me' : 'ai'}">${m.mode ? `<span class="mtag m-${esc(m.mode)}">${esc(modeTag(m.mode))}</span>` : ''}${esc(m.text).replace(/\n/g, '<br>')}${m.meta ? `<div class="muted">${esc(m.meta)}</div>` : ''}</div>`).join('');
    $('#chat').scrollTop = 1e6;
  }
  function confirmDialog(i) {
    return new Promise((res) => {
      const o = document.createElement('div'); o.className = 'confirm-ov'; o.setAttribute('role', 'dialog'); o.setAttribute('aria-modal', 'true');
      const cur = esc(i.currency || 'USD');
      o.innerHTML = `<div class="confirm-box"><h3>Primera llamada de pago a OpenAI</h3><p>${esc(i.explanation || '')}</p><ul><li>Proveedor: <b>${esc(i.provider)}</b> · modelo <b>${esc(i.model)}</b></li><li>Coste máximo posible de esta consulta: <b>≈ ${i.estimated_worst_case == null ? 'no calculado' : i.estimated_worst_case.toFixed(5)} ${cur}</b> (tope por consulta ${i.max_cost_per_run} ${cur}; presupuesto mensual ${i.monthly_budget} ${cur})</li><li>Se envía: ${esc(i.data_sent)}</li><li>La clave no sale del servidor ni se muestra.</li></ul><div class="confirm-btns"><button id="cfNo">Cancelar (no se envía nada)</button><button id="cfYes" class="primary">Confirmar y llamar a OpenAI</button></div></div>`;
      document.body.appendChild(o); const done = (v) => { o.remove(); res(v); };
      $('#cfNo', o).onclick = () => done(false); $('#cfYes', o).onclick = () => done(true); $('#cfNo', o).focus();
    });
  }
  async function ask(q) {
    if (!q.trim()) return;
    if (!V.user) return loginForm();
    const tgt = V.synthSel && V.synth ? { account: V.synth.account, dossier: V.synth.id } : { account: acct(), dossier: V.dossierId };
    if (!tgt.dossier) { V.chat.push({ text: 'Selecciona o crea un expediente (pestaña Piloto) antes de preguntar.' }); return renderDirector(); }
    V.chat.push({ me: true, text: q }); V.chat.push({ text: 'Analizando con los coworkers…' }); renderDirector();
    let r = await api('POST', '/api/director/ask', { ...tgt, question: q });
    if (r.ok && r.j.needs_confirmation) {  // primera llamada facturable: confirmación humana explícita
      const okc = await confirmDialog(r.j); V.chat.pop();
      if (!okc) { V.chat.push({ text: 'Cancelado por ti: no se ha enviado nada a OpenAI y no se ha cobrado nada.' }); return renderDirector(); }
      V.chat.push({ text: 'Llamando a OpenAI…' }); renderDirector();
      r = await api('POST', '/api/director/ask', { ...tgt, question: q, confirm: { accepted: true, model: r.j.model } });
    }
    V.chat.pop();
    if (!r.ok) V.chat.push({ text: 'Error: ' + (r.j.error || r.status) }); else {
      const j = r.j, s = j.ai_summary; let meta = `Decisión determinista: ${j.decision} · coworkers: ${j.plan.join(' → ')}`;
      if (s && s.tokens_in == null) meta += ` · modelo ${s.model || '—'} · ${s.duration_ms} ms · sin tokens facturados (la llamada no llegó a completarse)`;
      else if (s) meta += ` · modelo ${s.model || '—'} · ${s.duration_ms} ms · tokens ${s.tokens_in}/${s.tokens_out} (${s.token_source || '—'}) · coste est. ${s.cost_estimate == null ? 'no calculado (precios sin configurar)' : s.cost_estimate.toFixed(6) + ' ' + s.currency}`;
      if (s && s.mode === 'REAL') meta += s.origin_verified ? ` · ✔ procede de OpenAI (HTTPS api.openai.com, respuesta ${s.response_id})` : ' · procedencia de OpenAI NO verificada (no se declara IA real verificada)';
      if (j.ai.reason && j.ai.mode === 'SIN_IA') meta += ` · motivo: ${j.ai.reason_text || j.ai.reason}`;
      V.chat.push({ text: j.answer, mode: j.ai.mode, meta });
    }
    await Promise.all([loadCw(), loadDossiers()]); renderDirector(); renderCoworkers();
  }

  /* ---------- Coworkers ---------- */
  function renderCoworkers() {
    const g = $('#cwGrid'); if (!g) return; const cw = V.cw && V.cw.coworkers;
    g.innerHTML = Object.keys(CW).map((id) => { const c = cw && cw[id]; const lab = !V.user ? 'INICIA SESIÓN' : c ? c.label : '…';
      return `<button class="cwb ${c && c.operational ? 'opn' : ''}" data-cw="${id}"><b>${esc((c && c.name) || id)}</b><span>${esc(CW[id])}</span><em class="st">${esc(lab)}${c && c.runs ? ` · ${c.runs} ejec.` : ''}</em></button>`; }).join('') +
      `<div class="muted" style="grid-column:1/-1">Estado deducido solo de ejecuciones registradas. «Operativo» exige ejecución verificada sobre datos del usuario completos. IA real verificada: <b>${V.cw && V.cw.ai.real_verified ? 'SÍ' : 'NO (pendiente)'}</b>.</div>`;
  }
  async function openCw(id) {
    if (!V.user) return loginForm();
    const r = await api('GET', `/api/records?account=${acct()}&kind=task&limit=200`); const t = (r.j.records || []).find((x) => x.data.coworker === id && x.data.state === 'done');
    const c = V.cw.coworkers[id], res = t && t.data.result;
    root.APP.openModal(`<h3>${esc(c.name)} <small>${esc(c.label)}</small></h3><p class="muted">${esc(CW[id])}. Depende de: ${esc((V.cw.defs[id].depends_on.join(', ')) || 'nadie')}. Determinista: sin IA ni datos externos.</p>
      <p><button class="btn" id="cwGo">Ejecutar vía Director sobre el expediente seleccionado</button></p><div id="cwOut">${res ? cwHtml(res, t.data) : '<p class="muted">Sin ejecuciones.</p>'}</div>`);
    $('#cwGo').onclick = async () => { if (!V.dossierId) { $('#cwOut').innerHTML = '<div class="f warn">Selecciona un expediente.</div>'; return; } $('#cwOut').innerHTML = 'Ejecutando…'; const a = await api('POST', '/api/director/ask', { account: acct(), dossier: V.dossierId, question: 'ejecución manual ' + id, coworkers: [id] }); await loadCw(); renderCoworkers(); const r2 = await api('GET', `/api/records?account=${acct()}&kind=task&limit=50`); const t2 = (r2.j.records || []).find((x) => x.data.coworker === id && x.data.state === 'done'); $('#cwOut').innerHTML = a.ok && t2 ? cwHtml(t2.data.result, t2.data) : `<div class="f warn">${esc(a.j.error || 'error')}</div>`; };
  }
  const cwHtml = (res, d) => `<div class="muted">Origen de datos: <b>${esc(d.origin)}</b> · ${esc(d.finished_at)} · ${d.duration_ms} ms · estado ${esc(res.status)} · verificaciones: ${res.checks.length ? res.checks.map((c) => (c.ok ? '✔' : '✘') + esc(c.name)).join(' · ') : 'n/a'}</div>` +
    res.findings.map((f) => `<div class="f ${f.kind === 'risk' ? 'warn' : f.kind === 'gap' ? 'info' : 'ok'}">${esc(f.text)}</div>`).join('') + (res.needs.length ? `<h3 style="margin-top:8px;font-size:14px">Datos que faltan</h3>${res.needs.map((n) => `<div class="f info">${esc(n)}</div>`).join('')}` : '');

  /* ---------- Noticias ---------- */
  function renderNews() {
    const el = $('#newsBox'); if (!el) return;
    el.innerHTML = NEWS.length ? NEWS.slice(0, 4).map((n) => `<div class="al media"><b>${esc(n.data.source)}</b> <a href="${esc(n.data.url)}" target="_blank" rel="noopener noreferrer">${esc(n.data.title)}</a> <span class="muted">${esc(n.data.date)} · verificada por ${esc(n.data.verified_by)}</span></div>`).join('')
      : '<p class="muted">Sin noticias verificadas. Solo se muestran noticias con fuente, URL y fecha verificadas por un aprobador.</p>';
  }

  /* ---------- Piloto PHIVITAL (expediente en servidor) ---------- */
  const getp = (p) => p.split('.').reduce((o, k) => (o == null ? o : o[k]), V.P);
  const setp = (p, v) => { const ks = p.split('.'), l = ks.pop(); ks.reduce((o, k) => o[k], V.P)[l] = v; };
  const inp = (p, label, t) => `<label class="fld">${label}<input data-p="${p}" data-t="${t || 'num'}" type="${t === 'text' ? 'text' : t === 'date' ? 'date' : 'number'}" step="any" value="${esc(getp(p))}"></label>`;
  const COSTS = { price: ['PVP planificado con IVA (€)', ['econ.price']], vat: ['IVA (%)', ['econ.vatPct']], cost: ['Coste de producto en almacén (€)', ['econ.cost']], fulfil: ['Tarifa FBA (€)', ['econ.fbaFee']],
    storage: ['Almacenaje (€/ud/mes · meses)', ['econ.storageMonthly', 'econ.storageMonths']], returns: ['Devoluciones (% · €/devolución)', ['econ.returnsPct', 'econ.returnProcessing']], referral: ['Comisión categoría (% · mínimo €)', ['econ.customReferralPct', 'econ.customMinFee']], ads: ['ACoS objetivo % · margen mínimo %', ['econ.acosTarget', 'econ.minMarginPct']] };

  function renderPilot() {
    const L = $('#pilLeft'), R = $('#pilRight'); if (!L) return;
    if (!V.user) { L.innerHTML = '<article class="card c-amber"><h3>Piloto PHIVITAL Magnesio</h3><p class="muted">Inicia sesión para trabajar con expedientes guardados en el servidor.</p><button class="btn" id="pilLogin">Iniciar sesión</button></article>'; R.innerHTML = ''; $('#pilLogin').onclick = () => loginForm(); return; }
    if (!V.P) { L.innerHTML = `<article class="card c-lime"><h3>Piloto PHIVITAL Magnesio <small>cuenta ${esc(acct())}</small></h3><p class="muted">Crea el expediente piloto: solo trae la identidad del producto (ASIN y formato) y costes SIN documentar. No hay demanda ni ventas inventadas.</p><button class="btn" id="pilInit">Crear expediente piloto</button></article>`; R.innerHTML = ''; $('#pilInit').onclick = async () => { const r = await api('POST', '/api/pilot/phivital/init', { account: acct() }); if (r.ok) { V.dossierId = r.j.id; await loadDossiers(); renderAll(); } }; return; }
    const P = V.P, cd = P.costDocs || {};
    const costRows = Object.entries(COSTS).map(([k, [lab, fields]]) => `<tr><td>${lab}</td><td>${fields.map((f) => `<input class="sm" data-p="${f}" data-t="num" type="number" step="any" value="${esc(getp(f))}">`).join(' ')}</td><td><input data-p="costDocs.${k}.evidence" data-t="text" type="text" placeholder="Factura / presupuesto / tarifa vigente" value="${esc((cd[k] || {}).evidence)}"></td><td><input data-p="costDocs.${k}.date" data-t="date" type="date" value="${esc((cd[k] || {}).date)}"></td></tr>`).join('');
    const reg = Object.entries(P.regulatory).map(([id, it]) => `<div class="ckrow"><span>${esc(it.label)}${it.critical ? '<span class="crit">OBLIGATORIO</span>' : ''}</span><select data-p="regulatory.${id}.status" data-t="text">${[['pendiente', 'Pendiente'], ['cumplido', 'Cumplido'], ['no_aplica', 'No aplica']].map(([v, l]) => `<option value="${v}" ${it.status === v ? 'selected' : ''}>${l}</option>`).join('')}</select><input data-p="regulatory.${id}.evidence" data-t="text" type="text" placeholder="Evidencia" value="${esc(it.evidence)}"></div>`).join('');
    const kw = (P.keywords || []).map((k) => [k.keyword, k.volume, k.source, k.date].join(';')).join('\n');
    L.innerHTML = `<article class="card c-lime"><h3>${esc(P.product.name)} <small>ASIN ${esc(P.product.asin || '—')} · origen ${esc(V.origin)}</small></h3>
      <label class="fld">Expediente <select id="pilSel">${V.dossiers.map((d) => `<option value="${esc(d.id)}" ${d.id === V.dossierId ? 'selected' : ''}>${esc(d.data.name)} · ${esc(d.data.origin)}</option>`).join('')}</select></label>
      <p class="note">${esc(P.notes || '')}</p><p class="note">«Origen USUARIO» solo si los 8 costes tienen evidencia y fecha; mientras tanto el piloto es INCOMPLETO y ningún coworker se declara operativo.</p></article>
    <details class="sec card c-cyan" open><summary>1 · Costes documentados</summary><table class="tbl"><tr><th>Concepto</th><th>Valor</th><th>Evidencia</th><th>Fecha</th></tr>${costRows}</table></details>
    <details class="sec card c-amber" open><summary>2 · Competidores (CSV)</summary><p class="note">Columnas: name, asin, priceGross, shipping, packUnits, contentValue, source, date [, rating, reviews]. Separador , o ;. Cada fila necesita fuente y fecha ≤ 30 días.</p>
      <p><label class="btn" for="pilCsv">Importar CSV</label><input type="file" id="pilCsv" accept=".csv,text/csv" hidden> <button class="btn ghost sm" id="pilTpl">Plantilla CSV</button> <span class="muted">${(P.competitors || []).length} filas cargadas</span></p>
      <div id="pilBench"></div></details>
    <details class="sec card c-violet"><summary>3 · Demanda (keywords aportadas)</summary><p class="note">Una por línea: keyword;volumen;fuente;AAAA-MM-DD (≤ 60 días). No se estima demanda.</p><textarea id="pilKw" rows="5">${esc(kw)}</textarea></details>
    <details class="sec card c-cyan"><summary>4 · Escenarios de PVP y datos de publicidad</summary><div class="grid2"><label class="fld full">PVP a comparar (€, separados por coma)<input id="pilSc" type="text" value="${esc((P.pvpScenarios || []).join(', '))}"></label>${inp('cvrPct', 'CVR real aportada (%) — opcional')}${inp('adBudgetMonth', 'Presupuesto ads €/mes — opcional')}${inp('ownRating', 'Valoración propia (★) — opcional')}</div></details>
    <details class="sec card c-lime"><summary>5 · Regulatorio pendiente</summary>${reg}</details>
    <details class="sec card c-amber"><summary>6 · Stock, logística y listing</summary><div class="grid2">${inp('logistics.stockAvailable', 'Stock disponible (uds)')}${inp('logistics.forecastUnitsMonth', 'Previsión (uds/mes) — decisión humana')}${inp('logistics.leadTimeDays', 'Reposición (días)')}${inp('logistics.coverTargetDays', 'Cobertura objetivo (días)')}
      <label class="fld full">Título del listing<input data-p="listing.title" data-t="text" type="text" value="${esc((P.listing || {}).title)}"></label><label class="fld full">Bullets (uno por línea)<textarea id="pilBul" rows="3">${esc(((P.listing || {}).bullets || []).join('\n'))}</textarea></label></div></details>
    <p style="margin:8px 0"><button class="btn" id="pilSave">Guardar y evaluar</button> <button class="btn warn" id="pilReq">Solicitar aprobación</button></p><div id="pilMsg" class="muted">${V.msg || ''}</div>`;
    wirePilot(); if (V.ev) renderEval(); else evaluate();
  }
  function collect() {
    const P = V.P;
    P.keywords = $('#pilKw').value.split('\n').map((l) => l.split(';').map((x) => x.trim())).filter((a) => a[0]).map(([keyword, v, source, date]) => ({ keyword, volume: v === '' || v == null ? null : +v, source: source || '', date: date || '' }));
    P.pvpScenarios = $('#pilSc').value.split(',').map((x) => +x.trim()).filter((x) => x > 0);
    P.listing = { ...(P.listing || {}), bullets: $('#pilBul').value.split('\n').map((x) => x.trim()).filter(Boolean), backend: (P.listing || {}).backend || '' };
    ['cvrPct', 'adBudgetMonth', 'ownRating'].forEach((k) => { if (P[k] === '' || Number.isNaN(P[k])) delete P[k]; });
  }
  async function save() { collect(); const d = V.dossiers.find((x) => x.id === V.dossierId); const r = await api('POST', '/api/dossiers', { account: acct(), id: V.dossierId, name: d.data.name, origin: (V.origin === 'PRUEBA' || V.origin === 'DEMO') ? V.origin : 'USUARIO', dossier: V.P }); if (!r.ok) { $('#pilMsg').textContent = 'Error al guardar: ' + (r.j.error || r.status); return false; } await loadDossiers(); return true; }
  async function evaluate() { const r = await api('POST', '/api/dossiers/evaluate', { account: acct(), id: V.dossierId, today: today() }); if (r.ok) { V.ev = r.j; renderEval(); } }
  function wirePilot() {
    const L = $('#pilLeft');
    L.oninput = (e) => { const el = e.target; if (!el.dataset.p) return; const v = el.dataset.t === 'num' ? (el.value === '' ? null : +el.value) : el.value; if (!(el.dataset.p.startsWith('costDocs.') || el.dataset.p.startsWith('listing.')) || true) { if (el.dataset.p.startsWith('costDocs.') && !V.P.costDocs) V.P.costDocs = {}; if (el.dataset.p.startsWith('listing.') && !V.P.listing) V.P.listing = {}; setp(el.dataset.p, v); } };
    $('#pilSel').onchange = async (e) => { V.dossierId = e.target.value; V.ev = null; await loadDossiers(); renderAll(); };
    $('#pilSave').onclick = async () => { if (await save()) { await evaluate(); await loadCw(); renderAll(); V.msg = 'Guardado en servidor y evaluado.'; if ($('#pilMsg')) $('#pilMsg').textContent = V.msg; } };
    $('#pilTpl').onclick = () => { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob(['name,asin,priceGross,shipping,packUnits,contentValue,source,date,rating,reviews\n'], { type: 'text/csv' })); a.download = 'plantilla_competidores.csv'; a.click(); };
    $('#pilCsv').onchange = (e) => { const f = e.target.files[0]; if (!f) return; const rd = new FileReader(); rd.onload = async () => { await save(); const r = await api('POST', '/api/competitors/import', { account: acct(), dossier: V.dossierId, csv: String(rd.result), filename: f.name }); V.msg = r.ok ? `Importadas ${r.j.imported} filas.${(r.j.warnings || []).map((w) => '<br>⚠ ' + esc(w)).join('')}` : esc(r.j.error || 'error') + (r.j.warnings || []).map((w) => '<br>⚠ ' + esc(w)).join(''); await loadDossiers(); V.ev = null; renderAll(); }; rd.readAsText(f); e.target.value = ''; };
    $('#pilReq').onclick = async () => { const r = await api('POST', '/api/approvals', { account: acct(), dossier: V.dossierId, note: 'Solicitud desde piloto' }); $('#pilMsg').textContent = r.ok ? `Solicitud registrada (evaluación actual: ${r.j.decision}). Un aprobador debe resolverla; no se ejecuta nada en Amazon.` : (r.j.error || 'error'); };
  }
  function renderEval() {
    const R = $('#pilRight'), ev = V.ev; if (!R || !ev) return; const e = ev.evaluation, u = e.sections.unit, mp = e.sections.minPrice, bm = e.sections.benchmark, cls = e.decision === 'NO-GO' ? 'NOGO' : e.decision;
    const grp = (sev, t) => { const fs = e.findings.filter((x) => x.severity === sev); return fs.length ? `<div class="sevh">${t} (${fs.length})</div>` + fs.map((x) => `<div class="fnd ${sev}"><b>${esc(x.title)}</b>${esc(x.why)}<div class="fx">→ ${esc(x.fix)}</div></div>`).join('') : ''; };
    const sc = (e.scenarios || []).filter((s) => s.valid), maxC = Math.max(1, ...sc.map((s) => Math.abs(s.contribution)));
    R.innerHTML = `<article class="card c-${e.decision === 'GO' ? 'lime' : e.decision === 'REVISAR' ? 'amber' : 'pink'}"><h3>Decisión <small>origen ${esc(V.origin)}</small></h3><div class="dec2 ${cls}">${e.decision}</div><p style="margin:6px 0">${esc(e.summary)}</p>
      <p style="font-size:12.5px"><b>${e.counts.nogo}</b> inviabilidad · <b>${e.counts.block}</b> bloqueos · <b>${e.counts.warn}</b> avisos</p>${e.pilot && e.pilot.provisional ? `<p class="note">Decisión PROVISIONAL: costes sin documentar (${esc(e.pilot.missing_costs.join('; '))}).</p>` : ''}</article>
      <article class="card c-cyan" style="margin-top:8px"><h3>Economía y escenarios de PVP <small>cálculo determinista</small></h3>${u && u.valid ? `<p style="font-size:13px">A ${u.price.toFixed(2)} €: neto <b>${u.net.toFixed(2)} €</b> · comisión ${u.referral.toFixed(2)} € · contribución <b>${u.contribution.toFixed(2)} €</b> (${(u.contributionPct * 100).toFixed(1)} %) · ACoS de equilibrio <b>${(u.breakEvenAcos * 100).toFixed(1)} %</b>${mp ? ` · PVP mínimo rentable <b>${mp.commercial.toFixed(2)} €</b>` : ''}</p>` : '<p class="muted">Datos económicos inválidos.</p>'}
      ${sc.length ? `<table class="tbl"><tr><th>PVP</th><th>Contribución</th><th>%</th><th>ACoS eq.</th><th></th></tr>${sc.map((s) => `<tr><td>${s.price.toFixed(2)} €</td><td>${s.contribution.toFixed(2)} €</td><td>${(s.contributionPct * 100).toFixed(1)}</td><td>${(s.breakEvenAcos * 100).toFixed(1)} %</td><td><div class="sbar ${s.contribution < 0 ? 'neg' : ''}" style="width:${Math.max(2, Math.abs(s.contribution) / maxC * 100).toFixed(0)}%"></div></td></tr>`).join('')}</table>` : ''}</article>
      <article class="card c-amber" style="margin-top:8px"><h3>Precios normalizados <small>€ por ${esc(bm.unitLabel)} (envío incluido)</small></h3>${bm.rows.length ? `<table class="tbl"><tr><th>Competidor</th><th>€/${esc(bm.unitLabel)}</th><th>Fuente · fecha</th></tr>${bm.rows.map((r) => `<tr><td>${esc(r.name)}</td><td>${r.unitPrice.toFixed(4)}</td><td>${esc(r.source)} · ${esc(r.date)}</td></tr>`).join('')}</table><p class="note">${bm.band ? `Banda para tu formato: ${bm.band.low.toFixed(2)} – ${bm.band.high.toFixed(2)} € (mediana ${bm.band.mid.toFixed(2)} €).` : ''} Válidos ${bm.n}/${Object.keys(bm.perRow).length}.</p>` : '<p class="muted">Sin competidores válidos: importa un CSV con fuente y fecha.</p>'}</article>
      <article class="card c-violet" style="margin-top:8px"><h3>Bloqueos y pendientes <small>qué falta y cómo resolverlo</small></h3>${grp('nogo', 'Inviabilidad')}${grp('block', 'Bloqueos')}${grp('warn', 'Avisos')}</article>`;
    const b = $('#pilBench'); if (b) b.innerHTML = (V.P.competitors || []).length ? `<table class="tbl"><tr><th>Competidor</th><th>Estado</th></tr>${V.P.competitors.map((c, i) => { const r = bm.perRow[i]; return `<tr><td>${esc(c.name)}</td><td class="${r && r.ok ? 'good' : 'bad'}">${r ? (r.ok ? r.unitPrice.toFixed(4) + ' ✔' : esc(r.reason)) : '—'}</td></tr>`; }).join('')}</table>` : '';
  }

  /* ---------- Historial y auditoría ---------- */
  async function renderHist() {
    const el = $('#histRoot'); if (!el) return; if (!V.user) { el.innerHTML = '<article class="card c-amber"><p class="muted">Inicia sesión para ver historial y auditoría.</p></article>'; return; }
    const [q, r, a, ap] = await Promise.all([api('GET', `/api/records?account=${acct()}&kind=query&limit=30`), api('GET', `/api/records?account=${acct()}&kind=ai_run&limit=30`), api('GET', `/api/audit?account=${acct()}`), api('GET', `/api/records?account=${acct()}&kind=approval&limit=30`)]);
    const qs = q.j.records || [], runs = r.j.records || [], au = a.j.audit || [], aps = ap.j.records || [];
    el.innerHTML = `<article class="card c-cyan"><h3>Historial de consultas <small>${qs.length}</small></h3>${qs.length ? `<table class="tbl"><tr><th>Cuándo</th><th>Usuario</th><th>Pregunta</th><th>Coworkers</th><th>Decisión</th><th>Modo</th></tr>${qs.map((x) => `<tr><td>${esc(x.data.at)}</td><td>${esc(x.data.actor)}</td><td>${esc(x.data.question)}</td><td>${esc(x.data.plan.join(', '))}</td><td>${esc(x.data.decision)}</td><td>${esc(modeTag(x.data.ai.mode))}</td></tr>`).join('')}</table>` : '<p class="muted">Sin consultas.</p>'}</article>
      <article class="card c-violet"><h3>Ejecuciones de IA <small>modelo · duración · tokens · coste estimado · errores</small></h3>${runs.length ? `<table class="tbl"><tr><th>Inicio</th><th>Modelo</th><th>Modo</th><th>ms</th><th>Tokens in/out</th><th>Coste est.</th><th>Error</th><th>Anclaje</th></tr>${runs.map((x) => { const d = x.data; return `<tr><td>${esc(d.started_at)}</td><td>${esc(d.model || '—')}</td><td>${esc(modeTag(d.mode))}</td><td>${d.duration_ms == null ? '—' : d.duration_ms}</td><td>${d.tokens_in == null ? '—' : d.tokens_in + ' / ' + d.tokens_out} ${esc(d.token_source || '')}</td><td>${d.cost_estimate == null ? 'n/d' : d.cost_estimate.toFixed(6) + ' ' + esc(d.currency)}</td><td>${esc(d.error || '—')}</td><td>${d.grounding ? (d.grounding.ok ? '✔' : '✘ ' + esc(d.grounding.ungrounded.join(','))) : '—'}</td></tr>`; }).join('')}</table>` : '<p class="muted">Sin ejecuciones de IA registradas (no se ha llamado a ningún proveedor).</p>'}</article>
      <article class="card c-amber"><h3>Aprobaciones <small>solo registro: no se ejecuta nada en Amazon</small></h3>${aps.length ? aps.map((x) => `<div class="ap"><div class="grow"><b>${esc(x.data.status.toUpperCase())}</b> · solicitada por ${esc(x.data.requested_by)} (evaluación ${esc(x.data.decision_at_request)})<br><span class="muted">${esc(x.data.note || '')}${x.data.decided_by ? ' · decidida por ' + esc(x.data.decided_by) : ''}</span></div>${x.data.status === 'pendiente' && (V.role === 'approver' || V.role === 'admin') ? `<button class="btn" data-ap="aprobada" data-id="${esc(x.id)}">Aprobar</button><button class="btn no" data-ap="rechazada" data-id="${esc(x.id)}">Rechazar</button>` : ''}</div>`).join('') : '<p class="muted">Sin aprobaciones.</p>'}</article>
      <article class="card c-lime"><h3>Registro de auditoría <small>cadena de hashes: ${a.j.chain && a.j.chain.ok ? '✔ íntegra' : '✘ ROTA en #' + (a.j.chain && a.j.chain.broken_at)} · ${a.j.chain ? a.j.chain.entries : 0} entradas</small></h3><table class="tbl"><tr><th>#</th><th>Fecha</th><th>Actor</th><th>Acción</th><th>Detalle</th><th>Hash</th></tr>${au.slice(0, 60).map((x) => `<tr><td>${x.seq}</td><td>${esc(x.ts)}</td><td>${esc(x.actor)}</td><td>${esc(x.action)}</td><td>${esc(JSON.stringify(x.detail)).slice(0, 90)}</td><td>${esc(x.hash)}</td></tr>`).join('')}</table></article>`;
    $$('[data-ap]', el).forEach((b) => (b.onclick = async () => { const rr = await api('POST', '/api/approvals/decide', { account: acct(), id: b.dataset.id, decision: b.dataset.ap, reason: 'decisión desde interfaz' }); if (!rr.ok) alert(rr.j.error); renderHist(); }));
  }

  function renderAll() { renderDirector(); renderCoworkers(); renderNews(); renderPilot(); if ($('#tab-hist').classList.contains('on')) renderHist(); }
  root.V03 = { V, api, renderHist, renderPilot, openCw, ask, loginForm, renderAll };
  document.addEventListener('DOMContentLoaded', async () => {
    $('#dirSynth') && ($('#dirSynth').onclick = () => { if (!V.synth) { V.chat.push({ text: 'El expediente SINTÉTICO no está disponible para tu usuario (solo el administrador lo ve).' }); return renderDirector(); } V.synthSel = true; renderDirector(); ask('resumen general'); });
    $('#dirDossier').onchange = (e) => { if (e.target.value === '__synth__') { V.synthSel = true; renderDirector(); return; } V.synthSel = false; V.dossierId = e.target.value || null; const d = V.dossiers.find((x) => x.id === V.dossierId); V.P = d ? d.data.dossier : null; V.origin = d ? d.data.origin : null; V.ev = null; renderAll(); };
    $('#chatForm').onsubmit = (e) => { e.preventDefault(); const q = $('#chatIn').value; $('#chatIn').value = ''; ask(q); };
    $('#chips').innerHTML = ['Resumen general', 'Precio y margen', 'Competencia', 'Keywords', 'Stock', 'Cumplimiento'].map((c) => `<button type="button">${c}</button>`).join(''); $$('#chips button').forEach((b) => (b.onclick = () => ask(b.textContent)));
    $('#cwGrid').addEventListener('click', (e) => { const b = e.target.closest('[data-cw]'); if (b) openCw(b.dataset.cw); });
    document.addEventListener('click', (e) => { const b = e.target.closest('#tabs button'); if (!b) return; if (b.dataset.tab === 'hist') renderHist(); if (b.dataset.tab === 'piloto') renderPilot(); });
    const me = await api('GET', '/api/me'); if (me.j.user) { setRole(me.j.role); V.user = me.j.user; V.csrf = me.j.csrf; await boot(); } else { renderSession(); renderAll(); }
  });
})(self);
