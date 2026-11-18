/* AHT Executive Neon · K4 — Centro de mando ejecutivo: 4 vistas, filtros globales, benchmarking visual, Pricing Intelligence y Director con dossiers.
   Todo viene de /api/k4/*. Sin manejadores inline (CSP). Todo texto externo se escapa. Una cifra sin dato se muestra SIN DATO (nunca 0). */
(function (root) {
  const $ = (s, r) => (r || document).querySelector(s), $$ = (s, r) => [...(r || document).querySelectorAll(s)];
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const fmt = (x, d) => (x == null || typeof x !== 'number' || !isFinite(x) ? null : x.toLocaleString('es-ES', { minimumFractionDigits: d == null ? 2 : d, maximumFractionDigits: d == null ? 2 : d }));
  const SEGC = { premium: 'k3-premium', funcional: 'k3-func', economica: 'k3-eco', pendiente: 'k3-pend', nocomparable: 'k3-nocomp' };
  const S = { view: 'centro', f: { producto: 'PRD-ACTIVCORE-V2', pais: 'ES', periodo: 'todo', canal: 'TODOS' }, est: null, d: {}, seg: '', msg: '', busy: false, dos: null, sel: null };
  const api = (m, p, b) => root.V03.api(m, p, b);
  const qs = () => { const f = S.f, o = { producto: f.producto, pais: f.pais, canal: f.canal }; if (f.periodo !== 'todo') { const d = new Date(); d.setDate(d.getDate() - Number(f.periodo)); o.desde = d.toISOString().slice(0, 10); } return Object.entries(o).map(([k, v]) => k + '=' + encodeURIComponent(v)).join('&'); };
  const roleOk = (r) => ({ analyst: 1, approver: 2, admin: 3 }[(root.V03 && root.V03.V && root.V03.V.role) || ''] || 0) >= { analyst: 1, approver: 2, admin: 3 }[r];

  const badge = (e) => `<span class="k4st k4st-${esc(e)}">${esc(e)}</span>`;
  function medida(label, m, unit) {
    const sin = !m || m.estado === 'SIN_DATO'; const v = sin ? null : (m.unidad === 'ratio' ? fmt(m.valor * 100, 1) + ' %' : (fmt(m.valor, m.unidad === 'uds' || m.unidad === 'sesiones' ? 0 : 2) + ' ' + (m.moneda || m.unidad || '')));
    return `<div class="k4kpi ${sin ? 'k4none' : ''}"><small>${esc(label)}</small><b>${sin ? 'SIN DATO' : esc(v)}</b><span>${sin ? 'No hay datos importados (no es 0)' : badge(m.estado) + ' ' + esc(m.fuente || '') + ' · ' + esc(m.fecha_dato || '')}</span></div>`;
  }
  function imgBox(im) {
    if (im && im.estado === 'VERIFICADA' && im.url) return `<div class="k4img"><img src="${esc(im.url)}" alt="Imagen verificada ${esc(im.origen)}" width="64" height="64"><small>${esc(im.origen)}</small></div>`;
    return `<div class="k4img k4pend" title="${esc((im && im.falta) || '')}"><b>IMAGEN PENDIENTE DE VERIFICAR</b><small>Falta: ${esc((im && im.falta) || 'autorización')}</small></div>`;
  }
  const filters = () => `<section class="k4f card c-cyan" aria-label="Filtros globales">
    <label>Producto <select id="k4fp">${((S.est && S.est.productos) || [{ id: S.f.producto, name: S.f.producto }]).map((p) => `<option value="${esc(p.id)}" ${p.id === S.f.producto ? 'selected' : ''}>${esc(p.name)}</option>`).join('')}</select></label>
    <label>País <select id="k4fc">${['ES', 'DE', 'FR', 'IT', 'NL', 'PL', 'TODOS'].map((c) => `<option ${c === S.f.pais ? 'selected' : ''}>${c}</option>`).join('')}</select></label>
    <label>Periodo <select id="k4fd">${[['7', 'Últimos 7 días'], ['30', 'Últimos 30 días'], ['90', 'Últimos 90 días'], ['todo', 'Todo']].map(([v, l]) => `<option value="${v}" ${v === S.f.periodo ? 'selected' : ''}>${l}</option>`).join('')}</select></label>
    <label>Canal <select id="k4fk">${['TODOS', 'FBA', 'FBM'].map((c) => `<option ${c === S.f.canal ? 'selected' : ''}>${c}</option>`).join('')}</select></label>
    <span class="grow"></span><span class="k4env">Entorno de datos: <b>PRODUCCIÓN</b> · gasto adicional 0 € · IA externa desactivada</span></section>`;
  const tabs = () => `<div class="k4views" role="tablist">${[['centro', 'Centro de mando'], ['bench', 'Benchmarking visual'], ['precio', 'Pricing Intelligence'], ['dir', 'Director · Datos']].map(([k, l]) => `<button role="tab" data-k4v="${k}" class="${S.view === k ? 'on' : ''}" aria-selected="${S.view === k}">${l}</button>`).join('')}</div>`;

  function capsHtml(c) {
    return `<article class="card c-amber"><h3>Qué hace hoy el Director <small>capacidades reales</small></h3><div class="k4caps">
      <div><h4>Determinista (operativo)</h4><ul>${c.deterministas_actuales.map((x) => `<li>${esc(x)}</li>`).join('')}</ul></div>
      <div><h4>IA externa</h4><p>${esc(c.ia_externa)}</p><h4>Autonomía verificada</h4><p>${badge('NO_VERIFICADA')} ${esc(c.autonomia_verificada.detalle)}</p></div>
      <div><h4>No operativo</h4><ul>${c.no_operativo.map((x) => `<li>${esc(x)}</li>`).join('')}</ul></div></div><p class="muted">${esc(c.aviso)}</p></article>`;
  }
  function dictHtml(d, full) {
    const t = d.tipo; const cl = { 1: 'up', 2: 'keep', 3: 'down', 4: 'other', 5: 'insuf' }[t];
    return `<article class="card k4dict k4d-${cl}"><h3>Dictamen de precio <small>${esc(d.producto)} · ${esc(d.pais)} · ${esc(d.entorno)}</small></h3>
      <p class="k4verdict"><b>${t}. ${esc(d.tipo_nombre)}</b> <span class="k4conf">confianza ${esc(d.confianza)}</span></p>
      <p>PVP propuesto: <b>${fmt(d.precio_actual.pvp_propuesto) || 'SIN DATO'} €</b> <small class="muted">${esc(d.precio_actual.estado || '')} — ${esc(d.precio_actual.nota)}</small></p>
      ${d.intervalo_recomendado ? `<p>Intervalo recomendado: <b>${fmt(d.intervalo_recomendado.min)}–${fmt(d.intervalo_recomendado.max)} €</b> <small class="muted">${esc(d.intervalo_recomendado.base)}</small></p>` : '<p class="muted">Sin intervalo recomendado: la evidencia no lo permite.</p>'}
      <ul class="k4just">${d.justificacion.map((a) => `<li><span class="k4cl k4cl-${esc(a.clase)}">${esc(a.clase)}</span> ${esc(a.texto)}</li>`).join('')}</ul>
      <p><b>Acción propuesta:</b> ${esc(d.proxima_accion)}</p><p><b>Criterio de revisión:</b> ${esc(d.criterio_revision)}</p>
      ${d.riesgos.length ? `<h4>Riesgos</h4><ul>${d.riesgos.map((r) => `<li>${esc(r)}</li>`).join('')}</ul>` : ''}
      ${full ? `<h4>Escenarios</h4>${d.escenarios.length ? `<table class="k4tb"><tr><th>PVP</th><th>Margen antes de Ads</th><th>Contribución/ud</th><th>Uds/día</th></tr>${d.escenarios.map((e) => `<tr><td>${fmt(e.pvp)} €</td><td>${e.margen_antes_ads == null ? 'SIN DATO' : fmt(e.margen_antes_ads * 100, 1) + ' %'}</td><td>${e.contribucion_ud == null ? 'SIN DATO' : fmt(e.contribucion_ud) + ' €'}</td><td>${e.uds_dia ? esc(e.uds_dia.join(' – ')) + ' <small class="muted">' + esc(e.uds_dia_estado) + '</small>' : '<span class="muted">' + esc(e.uds_dia_estado) + '</span>'}</td></tr>`).join('')}</table>` : '<p class="muted">Sin escenarios: faltan datos.</p>'}
      <h4>Trazabilidad</h4><table class="k4tb"><tr><th>Input</th><th>Valor</th><th>Estado</th><th>Fuente</th><th>Fecha</th></tr>${d.trazabilidad.map((t_) => `<tr><td>${esc(t_.input)}</td><td>${esc(t_.valor)}</td><td>${badge(t_.estado)}</td><td>${esc(t_.fuente)}</td><td>${esc(t_.fecha)}</td></tr>`).join('')}</table>` : ''}
      ${d.faltantes.length ? `<h4>Datos faltantes y cómo obtenerlos</h4><ul class="k4falt">${d.faltantes.map((f) => `<li><b>${esc(f.dato)}</b><br><small>${esc(f.como)}</small></li>`).join('')}</ul>` : ''}</article>`;
  }

  async function loadView() {
    S.busy = true; draw();
    if (!S.est) { const r = await api('GET', '/api/k4/estado'); S.est = r.ok ? r.j : null; }
    const q = qs();
    if (S.view === 'centro') { const r = await api('GET', '/api/k4/centro?' + q); S.d.centro = r.ok ? r.j : { error: (r.j && r.j.error) || 'No disponible' }; }
    if (S.view === 'bench') { const r = await api('GET', '/api/k4/benchmark?' + q); S.d.bench = r.ok ? r.j : { error: (r.j && r.j.error) || 'No disponible' }; }
    if (S.view === 'precio') { const [a, b] = await Promise.all([api('GET', '/api/k4/dictamen?' + q), api('GET', '/api/k4/costes?producto=' + encodeURIComponent(S.f.producto))]); S.d.precio = a.ok ? a.j : { error: (a.j && a.j.error) || 'No disponible' }; S.d.costes = b.ok ? b.j : null; }
    if (S.view === 'dir') { const [a, b, c] = await Promise.all([api('GET', '/api/k4/dossiers'), api('GET', '/api/k4/seguimientos'), api('GET', '/api/k4/medios')]); S.d.dos = a.ok ? a.j.dossiers : []; S.d.seg = b.ok ? b.j.seguimientos : []; S.d.med = c.ok ? c.j.registro : []; }
    S.busy = false; draw();
  }

  function viewCentro() {
    const d = S.d.centro; if (!d) return '<p class="muted">Cargando…</p>'; if (d.error) return `<p class="k4err">${esc(d.error)}</p>`;
    const k = d.kpis;
    return `<div class="k4grid"><article class="card c-cyan"><h3>Indicadores comerciales <small>${esc(d.filtros.producto)} · ${esc(d.filtros.pais || 'TODOS')}</small></h3><div class="k4kpis">${medida('Unidades', k.unidades)}${medida('Ventas netas', k.ventas_netas)}${medida('Sesiones', k.sesiones)}${medida('Conversión', k.conversion)}${medida('Gasto Ads', k.gasto_ads)}${medida('ACoS', k.acos)}${medida('Devoluciones', k.tasa_devolucion)}${medida('Stock', k.stock)}</div>
      <p class="muted">Sin importación documentada (CSV de Seller Central/Ads) no hay ventas: SP-API y Ads siguen NO OPERATIVOS. Los datos sintéticos nunca se mezclan con producción.</p></article>
      <article class="card k4d-${{ 1: 'up', 2: 'keep', 3: 'down', 4: 'other', 5: 'insuf' }[d.dictamen.tipo]}"><h3>Decisión de precio <small>resumen</small></h3><p class="k4verdict"><b>${d.dictamen.tipo}. ${esc(d.dictamen.nombre)}</b> <span class="k4conf">confianza ${esc(d.dictamen.confianza)}</span></p><p>${esc(d.dictamen.accion)}</p><button class="btn" data-k4go="precio">Ver dictamen completo</button></article>
      <article class="card c-lime"><h3>Qué falta <small>${d.faltantes.length} datos · ${d.costes_pendientes} costes pendientes</small></h3><ul class="k4falt">${d.faltantes.map((f) => `<li><b>${esc(f.dato)}</b><br><small>${esc(f.como)}</small></li>`).join('') || '<li>Nada crítico.</li>'}</ul></article>
      <article class="card c-violet"><h3>Decisiones pendientes de una persona <small>${d.decisiones.length}</small></h3><ul>${d.decisiones.map((x) => `<li>${esc(x.title)} <small class="muted">${esc(x.level)}</small></li>`).join('') || '<li class="muted">Ninguna. Las acciones externas están bloqueadas.</li>'}</ul></article></div>${capsHtml(d.capacidades)}`;
  }
  function viewBench() {
    const d = S.d.bench; if (!d) return '<p class="muted">Cargando…</p>'; if (d.error) return `<p class="k4err">${esc(d.error)}</p>`;
    const segs = [['', 'Todos'], ['premium', 'Premium'], ['funcional', 'Funcional'], ['economica', 'Económico'], ['pendiente', 'Pendiente'], ['nocomparable', 'No comparable']];
    const items = d.items.filter((i) => !S.seg || i.codigo === S.seg); const mx = Math.max(1, ...items.map((i) => i.precio_100ml || 0), (d.propio.pvp && d.propio.ml ? d.propio.pvp / d.propio.ml * 100 : 0));
    const own = d.propio.pvp && d.propio.ml ? d.propio.pvp / d.propio.ml * 100 : null;
    return `<article class="card c-amber k4own"><h3>${esc(d.propio.nombre)} <small>producto propio · centro de la comparativa</small></h3><div class="k4ownrow">${imgBox(d.propio.imagen)}<div><p>PVP propuesto <b>${fmt(d.propio.pvp) || 'SIN DATO'} €</b> <small class="muted">${esc(d.propio.pvp_estado)}</small></p><p>${own ? 'Precio/100 ml: <b>' + fmt(own) + ' €</b>' : 'Precio/100 ml: SIN DATO'}</p></div></div></article>
      <div class="k3segs" role="group" aria-label="Segmento">${segs.map(([k, l]) => `<button class="euchip ${S.seg === k ? 'on' : ''}" data-k4seg="${k}">${l}</button>`).join('')}</div>
      <div class="k4cards">${items.map((i) => `<article class="card k4comp"><div class="k4comphead"><span class="tagst k3chip ${SEGC[i.codigo] || ''}">${esc(i.segmento)}</span> <span class="tagst">${i.origen === 'keepa' ? 'ASIN Keepa' : 'Referencia sin ASIN'}</span></div>${imgBox(i.imagen)}<b>${esc(i.marca || 'marca n/d')}</b><small class="k4t">${esc((i.titulo || '').slice(0, 90))}</small>
        <div class="k4bar"><i style="width:${Math.max(2, ((i.precio_100ml || 0) / mx) * 100)}%"></i></div><p>${i.precio_100ml == null ? 'SIN PRECIO VIGENTE' : fmt(i.precio_100ml) + ' €/100 ml'} <small class="muted">${i.precio_100ml == null && i.clase_precio === 'SIN PRECIO' ? '' : esc(i.clase_precio)}${i.fecha_precio ? ' · ' + esc(String(i.fecha_precio).slice(0, 10)) : ''}</small></p>
        <p><small>Equivalencia ESTIMADA ${esc(i.equivalencia)}/100 · confianza ${esc(i.confianza)}</small></p>${i.asin ? `<small class="muted">ASIN ${esc(i.asin)} · ${esc(i.pais)}</small>` : ''}</article>`).join('') || '<p class="muted">Sin referencias para este filtro.</p>'}</div>
      <p class="muted">${esc(d.nota)} La equivalencia es una estimación de K3 y no una validación comercial independiente.</p>
      <div class="k4exp"><button class="btn" data-k4exp="pdf">Exportar PDF</button> <button class="btn" data-k4exp="svg">Exportar SVG</button> <button class="btn" data-k4exp="png">Exportar PNG</button> <small class="muted">Las imágenes solo salen con derecho de exportación verificado; cada exportación queda auditada.</small></div>`;
  }
  function viewPrecio() {
    const d = S.d.precio; if (!d) return '<p class="muted">Cargando…</p>'; if (d.error) return `<p class="k4err">${esc(d.error)}</p>`;
    const c = S.d.costes; const ap = roleOk('approver');
    return dictHtml(d.dictamen, true) + `<article class="card c-cyan"><h3>Ficha de costes <small>fuente · fecha · unidad · moneda · validación</small></h3><p class="muted">${esc(c ? c.nota : '')}</p><table class="k4tb"><tr><th>Concepto</th><th>Valor</th><th>Estado</th><th>Fuente</th><th>Fecha</th><th>Acción</th></tr>
      ${(c ? c.ficha : []).map((r) => `<tr><td>${esc(r.etiqueta)}</td><td>${r.valor == null ? 'SIN DATO' : esc(fmt(r.valor) + ' ' + r.unidad)}</td><td>${badge(r.estado)}</td><td>${esc(r.fuente || '—')}</td><td>${esc(r.fecha || '—')}</td><td>${esc(r.accion || '')}${ap && r.id && r.estado === 'PENDIENTE_VALIDAR' ? ` <button class="chip" data-k4val="${r.id}">Validar</button>` : ''}</td></tr>`).join('')}</table></article>
      <article class="card c-lime"><h3>Importar datos comerciales <small>CSV documentado · no sintético</small></h3>${ap ? `<form id="k4imp"><label>Tipo <select id="k4it"><option value="sales">Ventas (producto,pais,fecha,unidades,ventas_netas,moneda,sesiones,pedidos,devoluciones_uds,precio_medio,canal)</option><option value="ads">Ads (producto,pais,fecha,gasto,ventas_ads,clics,impresiones,moneda)</option><option value="inventory">Inventario (producto,pais,fecha,stock)</option></select></label>
      <label>Origen <select id="k4io"><option value="EXPORT_SELLER_CENTRAL">Export Seller Central</option><option value="EXPORT_ADS">Export Ads</option><option value="MANUAL_AHT">Manual AHT</option></select></label><textarea id="k4ic" rows="5" placeholder="Pega el CSV con cabecera"></textarea><button class="btn" id="k4ib" type="submit">Importar</button></form>` : '<p class="muted">Requiere rol aprobador.</p>'}<p class="k4msg" id="k4m">${esc(S.msg)}</p></article>
      <div class="k4exp">${roleOk('analyst') ? '<button class="btn" id="k4mkdos">Generar dossier del Director</button>' : ''} <button class="btn" data-k4exp="pdf">Exportar PDF</button></div>`;
  }
  function viewDir() {
    const dosL = S.d.dos || [], seg = S.d.seg || [], med = S.d.med || []; const ap = roleOk('approver');
    return `<div class="k4grid"><article class="card c-cyan"><h3>Dossiers del Director <small>${dosL.length}</small></h3><ul>${dosL.map((x) => `<li><button class="chip" data-k4dos="${esc(x.id)}">${esc(x.id)}</button> ${esc(x.tipo)} · ${esc(x.titulo)}</li>`).join('') || '<li class="muted">Aún no hay dossiers. Genera uno desde Pricing Intelligence.</li>'}</ul></article>
      <article class="card c-violet"><h3>Seguimiento de decisiones <small>mide sin atribuir automáticamente</small></h3><ul>${seg.map((x) => `<li>#${x.id} ${esc(x.estado)} · ${esc(x.producto)} ${esc(x.pais)} — ${esc(x.accion)}${ap && x.estado === 'EJECUTADA_POR_PERSONA' ? ` <button class="chip" data-k4med="${x.id}">Medir</button>` : ''}</li>`).join('') || '<li class="muted">Sin seguimientos.</li>'}</ul></article>
      <article class="card c-amber"><h3>Registro de imágenes y derechos <small>${med.length}</small></h3><ul>${med.map((m) => `<li>${esc(m.id)} · ${esc(m.asin || 'propio')} · ${esc(m.origen)} · ${badge(m.estado)} <small class="muted">visualizar ${m.derechos.visualizar ? 'sí' : 'no'} · almacenar ${m.derechos.almacenar ? 'sí' : 'no'} · exportar ${m.derechos.exportar ? 'sí' : 'no'}</small></li>`).join('') || '<li class="muted">Sin imágenes registradas: todas las tarjetas muestran IMAGEN PENDIENTE DE VERIFICAR con la autorización que falta.</li>'}</ul></article>
      <article class="card c-lime"><h3>Nuevo producto <small>dossier de investigación</small></h3><form id="k4np"><label>Título <input id="k4npt" maxlength="120"></label><label>Necesidad del cliente <input id="k4npn" maxlength="200"></label><button class="btn" type="submit">Crear dossier</button></form><p class="k4msg" id="k4m">${esc(S.msg)}</p></article></div>
      ${S.dos ? `<article class="card c-cyan k4dossier"><h3>${esc(S.dos.id)} <small>${esc(S.dos.tipo)}</small></h3><p><b>Problema detectado:</b> ${esc(S.dos.problema_detectado)}</p>${S.dos.dictamen ? `<p><b>Dictamen:</b> ${esc(S.dos.dictamen.nombre)} · confianza ${esc(S.dos.confianza)}</p><h4>Hipótesis alternativas</h4><ul>${S.dos.hipotesis_alternativas.map((h) => `<li>${esc(h.texto)}</li>`).join('')}</ul><h4>Investigación realizada</h4><ul>${S.dos.investigacion_realizada.map((i) => `<li>${esc(i.paso)}: ${esc(i.resultado)}</li>`).join('')}</ul><p><b>Acción:</b> ${esc(S.dos.accion_recomendada)}</p><p><b>Responsable:</b> ${esc(S.dos.responsable)}</p><p><b>Criterio de éxito:</b> ${esc(S.dos.criterio_exito)}</p><p><b>Revisión posterior:</b> ${esc(S.dos.revision_posterior)}</p><h4>Cómo obtener datos faltantes / experimentos</h4><ul>${S.dos.como_obtenerlos.map((x) => `<li>${esc(x.para)} → ${esc(x.experimento)}</li>`).join('')}</ul>${ap && S.dos.dictamen.tipo !== 5 ? `<button class="btn" data-k4prop="${esc(S.dos.id)}">Proponer a aprobación (N3)</button>` : '<p class="muted">Con evidencia insuficiente no hay decisión de precio que proponer.</p>'}` : `<p>${esc(S.dos.regla || '')}</p><ul>${(S.dos.datos_faltantes || []).map((f) => `<li>${esc(f.dato)} · ${badge(f.estado)}</li>`).join('')}</ul>`}</article>` : ''}`;
  }

  function draw() {
    const el = $('#k4Root'); if (!el) return;
    const body = S.view === 'centro' ? viewCentro() : S.view === 'bench' ? viewBench() : S.view === 'precio' ? viewPrecio() : viewDir();
    el.innerHTML = `<h2 class="k4h">K4 · Centro de mando ejecutivo <small>decidir, no decorar</small></h2>${filters()}${tabs()}${S.busy ? '<p class="muted k4load">Cargando…</p>' : ''}<div class="k4body" data-view="${S.view}">${body}</div>`;
    bind();
  }
  async function exportar(fmtx) {
    if (fmtx !== 'png') { const r = await fetch('/api/k4/export?' + qs() + '&fmt=' + fmtx, { credentials: 'same-origin' }); if (!r.ok) { S.msg = 'No se pudo exportar'; return draw(); } return download(await r.blob(), 'k4_' + S.f.producto + '_' + S.f.pais + '.' + fmtx); }
    const r = await fetch('/api/k4/export?' + qs() + '&fmt=svg', { credentials: 'same-origin' }); if (!r.ok) return; const svg = await r.text(); const im = new Image(); const u = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svg)));
    im.onload = () => { const c = document.createElement('canvas'); c.width = im.width || 900; c.height = im.height || 600; c.getContext('2d').drawImage(im, 0, 0); c.toBlob((b) => b && download(b, 'k4_' + S.f.producto + '_' + S.f.pais + '.png')); }; im.src = u;
  }
  function download(blob, name) { const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 2000); }
  function bind() {
    const f = S.f, on = (id, k) => { const e = $(id); if (e) e.onchange = () => { f[k] = e.value; S.d = {}; loadView(); }; };
    on('#k4fp', 'producto'); on('#k4fc', 'pais'); on('#k4fd', 'periodo'); on('#k4fk', 'canal');
    $$('[data-k4v]').forEach((b) => (b.onclick = () => { S.view = b.dataset.k4v; S.msg = ''; loadView(); }));
    $$('[data-k4go]').forEach((b) => (b.onclick = () => { S.view = b.dataset.k4go; loadView(); }));
    $$('[data-k4seg]').forEach((b) => (b.onclick = () => { S.seg = b.dataset.k4seg; draw(); }));
    $$('[data-k4exp]').forEach((b) => (b.onclick = () => exportar(b.dataset.k4exp)));
    $$('[data-k4val]').forEach((b) => (b.onclick = async () => { const r = await api('POST', '/api/k4/costes/validar', { id: Number(b.dataset.k4val), estado: 'VALIDADO' }); S.msg = r.ok ? 'Coste validado' : (r.j.error || 'Error'); loadView(); }));
    const imp = $('#k4imp'); if (imp) imp.onsubmit = async (e) => { e.preventDefault(); const r = await api('POST', '/api/k4/importar', { tipo: $('#k4it').value, origen: $('#k4io').value, csv: $('#k4ic').value, nombre: 'importación manual' }); S.msg = r.ok ? `Importadas ${r.j.filas} filas (${r.j.n_rechazadas} rechazadas)` : (r.j.error || 'Error'); loadView(); };
    const mk = $('#k4mkdos'); if (mk) mk.onclick = async () => { const r = await api('POST', '/api/k4/dossier', { producto: S.f.producto, pais: S.f.pais === 'TODOS' ? 'ES' : S.f.pais }); S.msg = r.ok ? 'Dossier ' + r.j.id + ' creado' : (r.j.error || 'Error'); if (r.ok) { S.dos = r.j; S.view = 'dir'; } loadView(); };
    $$('[data-k4dos]').forEach((b) => (b.onclick = async () => { const r = await api('GET', '/api/k4/dossier/' + encodeURIComponent(b.dataset.k4dos)); if (r.ok) { S.dos = r.j; draw(); } }));
    $$('[data-k4prop]').forEach((b) => (b.onclick = async () => { const r = await api('POST', '/api/k4/dossier/proponer', { id: b.dataset.k4prop }); S.msg = r.ok ? 'Decisión ' + r.j.decision_id + ' registrada para aprobación (sin ejecución externa)' : (r.j.error || 'Error'); loadView(); }));
    $$('[data-k4med]').forEach((b) => (b.onclick = async () => { const r = await api('POST', '/api/k4/seguimiento/medir', { id: Number(b.dataset.k4med) }); S.msg = r.ok ? 'Medición registrada (sin atribución automática)' : (r.j.error || 'Error'); loadView(); }));
    const np = $('#k4np'); if (np) np.onsubmit = async (e) => { e.preventDefault(); const r = await api('POST', '/api/k4/nuevo-producto', { titulo: $('#k4npt').value, necesidad: $('#k4npn').value }); S.msg = r.ok ? 'Dossier ' + r.j.id + ' creado' : (r.j.error || 'Error'); if (r.ok) S.dos = r.j.dossier; loadView(); };
  }
  function init() { const t = $('#tabs'); if (!t) return; t.addEventListener('click', (e) => { const b = e.target.closest('button'); if (b && b.dataset.tab === 'k4') { S.est = null; loadView(); } }); }
  root.K4UI = { S, draw, loadView }; if (document.readyState !== 'loading') init(); else document.addEventListener('DOMContentLoaded', init);
})(window);
