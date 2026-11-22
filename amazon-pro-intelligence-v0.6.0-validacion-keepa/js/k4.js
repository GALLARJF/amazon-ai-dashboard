/* AHT Executive Neon · K4 — Centro de mando ejecutivo: 4 vistas, filtros globales, benchmarking visual, Pricing Intelligence y Director con dossiers.
   Todo viene de /api/k4/*. Sin manejadores inline (CSP). Todo texto externo se escapa. Una cifra sin dato se muestra SIN DATO (nunca 0). */
(function (root) {
  const $ = (s, r) => (r || document).querySelector(s), $$ = (s, r) => [...(r || document).querySelectorAll(s)];
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const fmt = (x, d) => (x == null || typeof x !== 'number' || !isFinite(x) ? null : x.toLocaleString('es-ES', { minimumFractionDigits: d == null ? 2 : d, maximumFractionDigits: d == null ? 2 : d }));
  const SEGC = { premium: 'k3-premium', funcional: 'k3-func', economica: 'k3-eco', pendiente: 'k3-pend', nocomparable: 'k3-nocomp' };
  const S = { view: 'centro', f: { producto: 'PRD-ACTIVCORE-V2', pais: 'ES', periodo: 'todo', canal: 'TODOS' }, est: null, d: {}, seg: '', msg: '', busy: false, dos: null, sel: null, bv: 'comp', par: null, x: { q: '', seg: '', pc: '', ord: 'equiv', sel: false } };
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
    <span class="grow"></span><span class="k4env">Entorno de datos: <b>${document.body.classList.contains('staging') ? 'STAGING · DATOS SINTÉTICOS · NO USAR PARA DECISIONES REALES' : 'PRODUCCIÓN'}</b> · gasto adicional 0 € · IA externa desactivada</span></section>`;
  const tabs = () => `<div class="k4views" role="tablist">${[['centro', 'Centro de mando'], ['bench', 'Benchmarking visual'], ['precio', 'Pricing Intelligence'], ['dir', 'Director · Datos']].map(([k, l]) => `<button role="tab" data-k4v="${k}" class="${S.view === k ? 'on' : ''}" aria-selected="${S.view === k}">${l}</button>`).join('')}</div>`;

  function capsHtml(c) {
    return `<article class="card c-amber"><h3>Qué hace hoy el Director <small>capacidades reales</small></h3><div class="k4caps">
      <div><h4>Determinista (operativo)</h4><ul>${c.deterministas_actuales.map((x) => `<li>${esc(x)}</li>`).join('')}</ul></div>
      <div><h4>IA externa</h4><p>${esc(c.ia_externa)}</p><h4>Autonomía verificada</h4><p>${badge('NO_VERIFICADA')} ${esc(c.autonomia_verificada.detalle)}</p></div>
      <div><h4>No operativo</h4><ul>${c.no_operativo.map((x) => `<li>${esc(x)}</li>`).join('')}</ul></div></div><p class="muted">${esc(c.aviso)}</p></article>`;
  }
  function dictHtml(d, full) {
    const t = d.tipo; const cl = { 1: 'up', 2: 'keep', 3: 'down', 4: 'other', 5: 'insuf' }[t];
    return `<article class="card k4dict k4d-${cl}"><h3>Dictamen de precio <small>${esc(d.producto)} · ${esc(d.pais)} · ${document.body.classList.contains('staging') ? 'STAGING · DATOS SINTÉTICOS' : esc(d.entorno)}</small></h3>
      <p class="k4verdict"><b>${t}. ${esc(d.tipo_nombre)}</b> <span class="k4conf">confianza ${esc(d.confianza)}</span></p>
      <p>PVP propuesto: <b>${fmt(d.precio_actual.pvp_propuesto) || 'SIN DATO'} €</b> <small class="muted">${esc(d.precio_actual.estado || '')} — ${esc(d.precio_actual.nota)}</small></p>
      ${d.intervalo_recomendado ? `<p>Intervalo recomendado: <b>${fmt(d.intervalo_recomendado.min)}–${fmt(d.intervalo_recomendado.max)} €</b> <small class="muted">${esc(d.intervalo_recomendado.base)}</small></p>` : '<p class="muted">Sin intervalo recomendado: la evidencia no lo permite.</p>'}
      <ul class="k4just">${d.justificacion.map((a) => `<li><span class="k4cl k4cl-${esc(a.clase)}">${esc(a.clase)}</span> ${esc(a.texto)}</li>`).join('')}</ul>
      <p><b>Acción propuesta:</b> ${esc(d.proxima_accion)}</p><p><b>Criterio de revisión:</b> ${esc(d.criterio_revision)}</p>
      ${d.riesgos.length ? `<h4>Riesgos</h4><ul>${d.riesgos.map((r) => `<li>${esc(r)}</li>`).join('')}</ul>` : ''}
      ${full ? `<h4>Escenarios</h4>${d.escenarios.length ? `<div class="k4scroll" tabindex="0" role="region" aria-label="Tabla (desplaza en pantallas pequeñas)"><table class="k4tb"><tr><th>PVP</th><th>Margen antes de Ads</th><th>Contribución/ud</th><th>Uds/día</th></tr>${d.escenarios.map((e) => `<tr><td>${fmt(e.pvp)} €</td><td>${e.margen_antes_ads == null ? 'SIN DATO' : fmt(e.margen_antes_ads * 100, 1) + ' %'}</td><td>${e.contribucion_ud == null ? 'SIN DATO' : fmt(e.contribucion_ud) + ' €'}</td><td>${e.uds_dia ? esc(e.uds_dia.join(' – ')) + ' <small class="muted">' + esc(e.uds_dia_estado) + '</small>' : '<span class="muted">' + esc(e.uds_dia_estado) + '</span>'}</td></tr>`).join('')}</table></div>` : '<p class="muted">Sin escenarios: faltan datos.</p>'}
      <h4>Trazabilidad</h4><div class="k4scroll" tabindex="0" role="region" aria-label="Tabla (desplaza en pantallas pequeñas)"><table class="k4tb"><tr><th>Input</th><th>Valor</th><th>Estado</th><th>Fuente</th><th>Fecha</th></tr>${d.trazabilidad.map((t_) => `<tr><td>${esc(t_.input)}</td><td>${esc(t_.valor)}</td><td>${badge(t_.estado)}</td><td>${esc(t_.fuente)}</td><td>${esc(t_.fecha)}</td></tr>`).join('')}</table></div>` : ''}
      ${d.faltantes.length ? `<h4>Datos faltantes y cómo obtenerlos</h4><ul class="k4falt">${d.faltantes.map((f) => `<li><b>${esc(f.dato)}</b><br><small>${esc(f.como)}</small></li>`).join('')}</ul>` : ''}</article>`;
  }

  async function loadView() {
    S.busy = true; draw();
    if (!S.est) { const r = await api('GET', '/api/k4/estado'); S.est = r.ok ? r.j : null; }
    const q = qs();
    if (S.view === 'centro') { const r = await api('GET', '/api/k4/centro?' + q); S.d.centro = r.ok ? r.j : { error: (r.j && r.j.error) || 'No disponible' }; }
    if (S.view === 'bench') { const [a, e] = await Promise.all([api('GET', '/api/k4/benchmark/ejecutivo?' + q), api('GET', '/api/k4/benchmark/explorador?' + q)]); S.d.ej = a.ok ? a.j : { error: (a.j && a.j.error) || 'No disponible' }; S.d.expl = e.ok ? e.j : { error: (e.j && e.j.error) || 'No disponible' }; }
    if (S.view === 'precio') { const [a, b] = await Promise.all([api('GET', '/api/k4/dictamen?' + q), api('GET', '/api/k4/costes?producto=' + encodeURIComponent(S.f.producto))]); S.d.precio = a.ok ? a.j : { error: (a.j && a.j.error) || 'No disponible' }; S.d.costes = b.ok ? b.j : null; }
    if (S.view === 'dir') { const [a, b, c] = await Promise.all([api('GET', '/api/k4/dossiers'), api('GET', '/api/k4/seguimientos'), api('GET', '/api/k4/medios')]); S.d.dos = a.ok ? a.j.dossiers : []; S.d.seg = b.ok ? b.j.seguimientos : []; S.d.med = c.ok ? c.j.registro : []; }
    S.busy = false; draw();
  }

  function viewCentro() {
    const d = S.d.centro; if (!d) return '<p class="muted">Cargando…</p>'; if (d.error) return `<p class="k4err">${esc(d.error)}</p>`;
    const k = d.kpis;
    return `<div class="k4grid"><article class="card c-cyan"><h3>Indicadores comerciales <small>${esc(d.filtros.producto)} · ${esc(d.filtros.pais || 'TODOS')}</small></h3><div class="k4kpis">${medida('Unidades', k.unidades)}${medida('Ventas netas', k.ventas_netas)}${medida('Sesiones', k.sesiones)}${medida('Conversión', k.conversion)}${medida('Gasto Ads', k.gasto_ads)}${medida('ACoS', k.acos)}${medida('Devoluciones', k.tasa_devolucion)}${medida('Stock', k.stock)}</div>
      <p class="muted">Sin importación documentada (CSV de Seller Central/Ads) no hay ventas: SP-API y Ads siguen NO OPERATIVOS. Los datos sintéticos nunca se mezclan con los datos de AHT.</p></article>
      <article class="card k4d-${{ 1: 'up', 2: 'keep', 3: 'down', 4: 'other', 5: 'insuf' }[d.dictamen.tipo]}"><h3>Decisión de precio <small>resumen</small></h3><p class="k4verdict"><b>${d.dictamen.tipo}. ${esc(d.dictamen.nombre)}</b> <span class="k4conf">confianza ${esc(d.dictamen.confianza)}</span></p><p>${esc(d.dictamen.accion)}</p><button class="btn" data-k4go="precio">Ver dictamen completo</button></article>
      <article class="card c-lime"><h3>Qué falta <small>${d.faltantes.length} datos · ${d.costes_pendientes} costes pendientes</small></h3><ul class="k4falt">${d.faltantes.map((f) => `<li><b>${esc(f.dato)}</b><br><small>${esc(f.como)}</small></li>`).join('') || '<li>Nada crítico.</li>'}</ul></article>
      <article class="card c-violet"><h3>Decisiones pendientes de una persona <small>${d.decisiones.length}</small></h3><ul>${d.decisiones.map((x) => `<li>${esc(x.title)} <small class="muted">${esc(x.level)}</small></li>`).join('') || '<li class="muted">Ninguna. Las acciones externas están bloqueadas.</li>'}</ul></article></div>${capsHtml(d.capacidades)}`;
  }
  const ESTC = { OBSERVADO: 'OBSERVADO', HISTORICO: 'HISTÓRICO', MAQUETA: 'MAQUETA · no verificado', DECLARADO: 'DECLARADO', DERIVADO: 'DERIVADO', ESTIMADO: 'ESTIMADO', SIN_DATO: 'SIN DATO' };
  const cell = (c) => c ? `<div class="k4cell k4cs-${esc(c.estado)}"><span>${esc(c.texto)}</span><em class="k4st k4st-${esc(c.estado)}">${esc(ESTC[c.estado] || c.estado)}</em>${c.nota ? `<small>${esc(c.nota)}</small>` : ''}</div>` : '';
  const DCL = { 1: 'up', 2: 'keep', 3: 'down', 4: 'other', 5: 'insuf' };
  const list = (a) => (Array.isArray(a) ? a : [a]).filter(Boolean).map((x) => `<li>${esc(typeof x === 'object' ? (x.texto || x.dato || x.nombre || JSON.stringify(x)) : x)}</li>`).join('');
  function dictEjec(d) {
    if (!d) return ''; const i = d.informe || {}, dg = d.diagnostico || {};
    const sec = (n, t, body) => `<details class="k4sec" ${n === 1 || n === 7 ? 'open' : ''}><summary>${n}. ${t}</summary><div>${body}</div></details>`;
    const par = (x) => (Array.isArray(x) ? `<ul>${list(x)}</ul>` : `<p>${esc(x == null ? 'SIN DATO' : typeof x === 'object' ? JSON.stringify(x) : x)}</p>`);
    return `<article class="card k4dict k4d-${DCL[d.tipo]}" id="k4dictamen" aria-labelledby="k4dh"><h3 id="k4dh">Recomendación del Director IA <small>${esc(d.producto)} · ${esc(d.pais)}</small></h3>
      <p class="k4verdict"><b>${d.tipo}. ${esc(d.tipo_nombre)}</b> <span class="k4conf">confianza ${esc(d.confianza)}</span></p><p class="k4acc"><b>Acción prioritaria:</b> ${esc(i.accion_prioritaria || d.proxima_accion)}</p>
      <div class="k4diag">${Object.entries({ 'PVP adecuado': dg.pvp_adecuado, '¿Subir o bajar?': dg.subir_o_bajar, 'Causa de la falta de ventas': dg.causa_falta_de_ventas, 'Ventaja competitiva': dg.ventaja_competitiva }).map(([k, v]) => `<div><small>${esc(k)}</small><span>${Array.isArray(v) ? v.map((x) => `<span class="k4dl">${esc(x)}</span>`).join('') : esc(typeof v === 'object' && v ? JSON.stringify(v) : v == null ? 'SIN DATO' : v)}</span></div>`).join('')}</div>
      ${sec(1, 'Conclusión', par(i.conclusion))}${sec(2, 'Evidencia', par(i.evidencia))}${sec(3, 'Hipótesis alternativas', par(i.hipotesis_alternativas))}${sec(4, 'Escenarios económicos', par(i.escenarios_economicos))}${sec(5, 'Riesgos', par(i.riesgos))}${sec(6, 'Recomendación', par(i.recomendacion))}${sec(7, 'Acción prioritaria', par(i.accion_prioritaria))}${sec(8, 'Condiciones para reconsiderar la decisión', par(i.condiciones_para_reconsiderar))}
      ${(d.investigacion || []).length ? `<details class="k4sec"><summary>Investigación propuesta (datos que faltan y cómo obtenerlos)</summary><ol>${d.investigacion.map((x) => `<li>${esc(typeof x === 'object' ? (x.paso || x.dato || '') + (x.como ? ' — ' + x.como : '') : x)}</li>`).join('')}</ol></details>` : ''}</article>`;
  }
  function tarjetas(d) {   // primer nivel de Competencia: una tarjeta por referencia (la tabla completa vive en «Evidencia»)
    const ids = ['precio', 'precio_100ml', 'volumen', 'posicionamiento', 'evidencia', 'equivalencia'], fl = d.filas.filter((f) => ids.includes(f.id)).slice(0, 4), filas = fl.length ? fl : d.filas.slice(0, 4);
    const card = (c, own) => `<article class="card k4tc ${own ? 'k4tc-own' : ''}"><h3>${esc(own ? c.nombre : (c.marca || 'marca n/d'))} ${own ? '<span class="tagst">PRODUCTO PROPIO</span>' : `<span class="tagst k3chip ${SEGC[c.codigo] || ''}">${esc(c.segmento)}</span>`}</h3>${own ? '' : `<small class="muted">${esc((c.titulo || '').slice(0, 80))}</small>`}
      <dl>${filas.map((f) => `<div><dt>${esc(f.etiqueta)}</dt><dd>${cell(c.celdas && c.celdas[f.id])}</dd></div>`).join('')}</dl>${own ? '' : `<button class="chip" data-k4exp360="${esc(c.key)}">Expediente 360°</button>`}</article>`;
    return `<section class="k4tcs" aria-label="Competidores en tarjetas">${[card(d.propio, true)].concat(d.competidores.map((c) => card(c, false))).join('')}</section><p class="muted">La tabla completa está en «Evidencia».</p>`;
  }
  function matriz(d) {
    const cols = [d.propio].concat(d.competidores); const par = S.par != null && d.competidores[S.par] ? [d.propio, d.competidores[S.par]] : cols;
    const head = (c, own) => `<th scope="col" class="${own ? 'k4own-col' : ''}">${imgBox(c.imagen)}<b>${esc(own ? c.nombre : (c.marca || 'marca n/d'))}</b>${own ? '<span class="tagst">PRODUCTO PROPIO</span>' : `<small class="k4t">${esc((c.titulo || '').slice(0, 70))}</small><span class="tagst k3chip ${SEGC[c.codigo] || ''}">${esc(c.segmento)}</span>${c.seleccion && c.seleccion.origen_seleccion ? `<small class="muted">${esc(c.seleccion.origen_seleccion)}</small>` : ''}<button class="chip" data-k4exp360="${esc(c.key)}">Expediente 360°</button>`}</th>`;
    return `<div class="k4pair" role="group" aria-label="Comparación por pares (móvil)"><label>Comparar ACTIVCORE con <select id="k4par"><option value="">Los cinco a la vez</option>${d.competidores.map((c, i) => `<option value="${i}" ${S.par === i ? 'selected' : ''}>${esc(c.marca)}</option>`).join('')}</select></label></div>
      <div class="k4scroll" tabindex="0" role="region" aria-label="Comparativa ejecutiva; desplaza horizontalmente en pantallas pequeñas"><table class="k4cmp"><caption>ACTIVCORE frente a ${d.competidores.length} competidores de referencia (selección K3 con ajustes auditados)</caption>
      <thead><tr><th scope="col"><span class="sr">Concepto</span></th>${par.map((c, i) => head(c, c === d.propio)).join('')}</tr></thead>
      <tbody>${d.filas.map((f) => `<tr class="k4r-${esc(f.id)}"><th scope="row">${esc(f.etiqueta)}</th>${par.map((c) => `<td class="${c === d.propio ? 'k4own-col' : ''}">${cell(c.celdas[f.id])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  }
  function ajustes(d) {
    const ap = roleOk('approver'); const ex = S.d.expl; const sel = d.competidores.map((c) => c.key);
    return `<details class="k4adv"><summary>Cómo se eligieron los cinco y ajustes manuales (auditados)</summary><p class="muted">${esc(d.seleccion.regla)}</p><ul>${d.competidores.map((c) => `<li><b>${esc(c.marca)}</b> — ${esc((c.seleccion && c.seleccion.justificacion) || '')} ${ap ? `<button class="chip" data-k4quitar="${esc(c.key)}">Quitar</button>` : ''}</li>`).join('')}</ul>
      ${d.seleccion.ajustes.length ? `<h4>Ajustes registrados</h4><ul>${d.seleccion.ajustes.map((a) => `<li>${esc(a.accion)} ${esc(a.key)} — ${esc(a.motivo)} <small class="muted">${esc(a.actor)} · ${esc(String(a.creado).slice(0, 10))}</small></li>`).join('')}</ul>` : ''}
      <p class="muted">Para añadir otra referencia usa «Añadir a la comparativa» en el explorador (máximo cinco; hay que indicar un motivo).</p></details>`;
  }
  function viewBench() {
    const bv = S.bv || 'comp';
    const sub = `<div class="k4sub" role="tablist" aria-label="Niveles de benchmarking">${[['comp', '1 · Comparativa ejecutiva'], ['expl', '2 · Explorador (24)'], ['exp', '3 · Expediente 360°']].map(([k, l]) => `<button role="tab" data-k4bv="${k}" class="${bv === k ? 'on' : ''}" aria-selected="${bv === k}">${l}</button>`).join('')}</div>`;
    if (bv === 'expl') return sub + viewExpl();
    if (bv === 'exp') return sub + viewExp();
    const d = S.d.ej; if (!d) return sub + '<p class="muted">Cargando…</p>'; if (d.error) return sub + `<p class="k4err">${esc(d.error)}</p>`;
    if (d.disponible === false) return sub + `<p class="muted">${esc(d.motivo)}</p>`;
    return sub + `<p class="k4q">¿Cómo estamos posicionados? ¿Quiénes son los competidores relevantes, qué precio tienen y qué recomienda el Director?</p>${tarjetas(d)}<p class="muted k4pn">${esc(d.pvp_nota)} Las cifras de maqueta (infografía) se muestran etiquetadas «MAQUETA · no verificado» y no entran en ningún estadístico.</p>${dictEjec(d.dictamen)}${ajustes(d)}
      <details class="k4adv" id="k4evi"><summary>Evidencia, exportación, tabla completa y procedencia de las imágenes</summary><div class="k4tabla-ev">${matriz(d)}</div><p class="muted">Las imágenes solo se muestran si están VERIFICADAS con derecho de visualización; sin autorización aparece IMAGEN PENDIENTE DE VERIFICAR y qué permiso falta. La equivalencia K3 es una estimación, no una validación comercial.</p><div class="k4exp"><button class="btn" data-k4exp="pdf">Exportar PDF</button> <button class="btn" data-k4exp="svg">Exportar SVG</button> <button class="btn" data-k4exp="png">Exportar PNG</button></div></details>`;
  }
  function viewExpl() {
    const d = S.d.expl; if (!d) return '<p class="muted">Cargando…</p>'; if (d.error || d.disponible === false) return `<p class="k4err">${esc(d.error || 'Sin perfil K3')}</p>`;
    const X = S.x; const q = (X.q || '').toLowerCase(); const ap = roleOk('approver');
    let it = d.items.filter((i) => (!X.seg || i.codigo === X.seg) && (!X.pc || (X.pc === 'vigente' ? ['ACTUAL', 'RECIENTE'].includes(i.clase_precio) : !['ACTUAL', 'RECIENTE'].includes(i.clase_precio))) && (!X.sel || i.en_comparativa) && (!q || ((i.marca || '') + ' ' + (i.titulo || '') + ' ' + (i.asin || '')).toLowerCase().includes(q)));
    const key = { equiv: (i) => -(i.equivalencia || 0), precio: (i) => (i.precio_100ml == null ? 1e9 : i.precio_100ml), marca: (i) => (i.marca || 'zzz').toLowerCase() }[X.ord] || ((i) => -(i.equivalencia || 0));
    it = it.slice().sort((a, b) => (key(a) > key(b) ? 1 : key(a) < key(b) ? -1 : 0));
    return `<section aria-label="Explorador de competidores"><div class="k4xf"><label>Buscar <input id="k4xq" type="search" value="${esc(X.q || '')}" placeholder="marca, título o ASIN"></label>
      <label>Segmento <select id="k4xs">${[['', 'Todos'], ['premium', 'Premium'], ['funcional', 'Funcional'], ['economica', 'Económico'], ['pendiente', 'Pendiente'], ['nocomparable', 'No comparable']].map(([v, l]) => `<option value="${v}" ${X.seg === v ? 'selected' : ''}>${l}</option>`).join('')}</select></label>
      <label>Precio <select id="k4xp">${[['', 'Todos'], ['vigente', 'Con precio vigente'], ['sin', 'Sin precio vigente']].map(([v, l]) => `<option value="${v}" ${X.pc === v ? 'selected' : ''}>${l}</option>`).join('')}</select></label>
      <label>Ordenar <select id="k4xo">${[['equiv', 'Equivalencia K3'], ['precio', '€/100 mL'], ['marca', 'Marca']].map(([v, l]) => `<option value="${v}" ${X.ord === v ? 'selected' : ''}>${l}</option>`).join('')}</select></label>
      <label class="k4chk"><input type="checkbox" id="k4xe" ${X.sel ? 'checked' : ''}> Solo los de la comparativa</label></div>
      <p class="muted" role="status" aria-live="polite">${it.length} de ${d.total} referencias · sin fotografías en esta vista · ${esc(d.nota)} ${esc(S.msg)}</p>
      <div class="k4scroll" tabindex="0" role="region" aria-label="Tabla de competidores"><table class="k4tb k4expl"><caption class="sr">24 referencias con filtros</caption><thead><tr><th scope="col">Marca / producto</th><th scope="col">Segmento</th><th scope="col">€/100 mL</th><th scope="col">Estado precio</th><th scope="col">Equiv. K3</th><th scope="col">Confianza</th><th scope="col">En comparativa</th><th scope="col">Acciones</th></tr></thead><tbody>
      ${it.map((i) => `<tr class="${i.en_comparativa ? 'k4insel' : ''}"><th scope="row"><b>${esc(i.marca || 'marca n/d')}</b><br><small class="muted">${esc((i.titulo || '').slice(0, 60))}${i.asin ? ' · ' + esc(i.asin) : ' · sin ASIN'}</small></th><td><span class="tagst k3chip ${SEGC[i.codigo] || ''}">${esc(i.segmento)}</span></td><td>${i.precio_100ml == null ? 'SIN DATO' : fmt(i.precio_100ml) + ' €'}</td><td>${esc(i.clase_precio)}</td><td>${esc(i.equivalencia)}</td><td>${esc(i.confianza)}</td><td>${i.en_comparativa ? '✔ ' + esc(i.motivo_seleccion || '') : '—'}</td>
      <td><button class="chip" data-k4exp360="${esc(i.key)}">Expediente</button> ${ap ? (i.en_comparativa ? `<button class="chip" data-k4quitar="${esc(i.key)}">Quitar</button>` : `<button class="chip" data-k4anadir="${esc(i.key)}">Añadir a la comparativa</button>`) : ''}</td></tr>`).join('') || '<tr><td colspan="8" class="muted">Ninguna referencia cumple los filtros.</td></tr>'}</tbody></table></div></section>`;
  }
  function viewExp() {
    const d = S.d.exp; if (!d) return '<p class="muted">Elige una referencia en la comparativa o en el explorador para abrir su expediente 360°.</p>'; if (d.error) return `<p class="k4err">${esc(d.error)}</p>`;
    const rows = [['precio', 'Precio'], ['volumen', 'Volumen'], ['precio_100ml', '€/100 mL'], ['activos', 'Activos documentados'], ['dosis', 'Dosis'], ['duracion', 'Duración'], ['posicionamiento', 'Posicionamiento'], ['evidencia', 'Evidencia'], ['equivalencia', 'Equivalencia'], ['ventajas', 'Diferencias frente a ACTIVCORE']];
    const p = d.propio || {};
    return `<article class="card c-cyan k4exp360"><h3>${esc(d.marca || 'marca n/d')} <small>${esc(d.segmento)} · ${esc(d.pais)}</small></h3><div class="k4ownrow">${imgBox(d.imagen)}<div><p>${esc(d.titulo)}</p><p><small class="muted">Identificador ${esc(d.key)} · ASIN ${esc(d.asin || 'sin ASIN (referencia manual)')}</small></p>
      <p>Precio vigente: <b>${d.precio.vigente == null ? 'SIN PRECIO VIGENTE' : fmt(d.precio.vigente) + ' €'}</b> <small class="muted">${esc(d.precio.clase)}${d.precio.fecha ? ' · ' + esc(String(d.precio.fecha).slice(0, 10)) : ''}${d.precio.ultimo_conocido != null && d.precio.vigente == null ? ' · último conocido ' + fmt(d.precio.ultimo_conocido) + ' € (histórico, fuera de estadísticos)' : ''}</small></p><p class="muted">${esc(d.precio.historico_nota)}</p></div></div>
      <div class="k4scroll" tabindex="0" role="region" aria-label="Comparación detallada con ACTIVCORE"><table class="k4cmp k4cmp2"><caption>Comparación detallada con ACTIVCORE</caption><thead><tr><th scope="col"><span class="sr">Concepto</span></th><th scope="col" class="k4own-col">ACTIVCORE</th><th scope="col">${esc(d.marca)}</th></tr></thead><tbody>${rows.map(([k, l]) => `<tr><th scope="row">${l}</th><td class="k4own-col">${cell(p[k])}</td><td>${cell(d.celdas[k])}</td></tr>`).join('')}</tbody></table></div>
      <h4>Fortalezas y debilidades</h4><ul>${(d.ventajas_propias || []).map((v) => `<li>${esc(v)}</li>`).join('') || '<li class="muted">SIN DATO suficiente.</li>'}</ul><p class="muted">${esc(d.equivalencia.nota)} · confianza ${esc((d.equivalencia.confianza || {}).nivel || 'n/d')}.</p><button class="btn" data-k4bv="comp">Volver a la comparativa</button></article>`;
  }
  function viewPrecio() {
    const d = S.d.precio; if (!d) return '<p class="muted">Cargando…</p>'; if (d.error) return `<p class="k4err">${esc(d.error)}</p>`;
    const c = S.d.costes; const ap = roleOk('approver');
    return dictHtml(d.dictamen, true) + `<article class="card c-cyan"><h3>Ficha de costes <small>fuente · fecha · unidad · moneda · validación</small></h3><p class="muted">${esc(c ? c.nota : '')}</p><div class="k4scroll" tabindex="0" role="region" aria-label="Tabla (desplaza en pantallas pequeñas)"><table class="k4tb"><tr><th>Concepto</th><th>Valor</th><th>Estado</th><th>Fuente</th><th>Fecha</th><th>Acción</th></tr>
      ${(c ? c.ficha : []).map((r) => `<tr><td>${esc(r.etiqueta)}</td><td>${r.valor == null ? 'SIN DATO' : esc(fmt(r.valor) + ' ' + r.unidad)}</td><td>${badge(r.estado)}</td><td>${esc(r.fuente || '—')}</td><td>${esc(r.fecha || '—')}</td><td>${esc(r.accion || '')}${ap && r.id && r.estado === 'PENDIENTE_VALIDAR' ? ` <button class="chip" data-k4val="${r.id}">Validar</button>` : ''}</td></tr>`).join('')}</table></div></article>
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
    $$('[data-k4bv]').forEach((b) => (b.onclick = () => { S.bv = b.dataset.k4bv; draw(); }));
    $$('[data-k4exp360]').forEach((b) => (b.onclick = async () => { const r = await api('GET', '/api/k4/benchmark/expediente?' + qs() + '&key=' + encodeURIComponent(b.dataset.k4exp360)); S.d.exp = r.ok ? r.j : { error: (r.j && r.j.error) || 'No disponible' }; S.bv = 'exp'; draw(); const h = $('.k4exp360 h3'); if (h) { h.setAttribute('tabindex', '-1'); h.focus(); } }));
    const par = $('#k4par'); if (par) par.onchange = () => { S.par = par.value === '' ? null : Number(par.value); draw(); };
    const xs = { '#k4xq': ['q', 'input'], '#k4xs': ['seg', 'change'], '#k4xp': ['pc', 'change'], '#k4xo': ['ord', 'change'] };
    Object.entries(xs).forEach(([id, [k, ev]]) => { const e = $(id); if (e) e['on' + ev] = () => { S.x[k] = e.value; const pos = e.selectionStart; draw(); const n = $(id); if (n && k === 'q') { n.focus(); try { n.setSelectionRange(pos, pos); } catch (_) {} } }; });
    const xe = $('#k4xe'); if (xe) xe.onchange = () => { S.x.sel = xe.checked; draw(); };
    const ajusta = async (key, accion) => { const motivo = root.prompt ? root.prompt((accion === 'ANADIR' ? 'Motivo para añadir' : 'Motivo para quitar') + ' (mín. 8 caracteres, queda auditado):') : ''; if (!motivo) return; const r = await api('POST', '/api/k4/seleccion/ajustar', { producto: S.f.producto, pais: S.f.pais === 'TODOS' ? 'ES' : S.f.pais, key, accion, motivo }); S.msg = r.ok ? 'Selección actualizada (auditada)' : (r.j.error || 'Error'); loadView(); };
    $$('[data-k4anadir]').forEach((b) => (b.onclick = () => ajusta(b.dataset.k4anadir, 'ANADIR'))); $$('[data-k4quitar]').forEach((b) => (b.onclick = () => ajusta(b.dataset.k4quitar, 'QUITAR')));
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
