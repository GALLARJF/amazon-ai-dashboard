/* Rediseño F2 — Benchmarking a pantalla completa. LOCAL: sin red externa, sin Keepa, sin gasto. Historial persistente en SQLite (/api/bench7/*).
   Controles aún no operativos (adjuntos, voz, web, PDF) rotulados PENDIENTE; el prompt se guarda, su interpretación por IA está pendiente. */
(function (root) {
  'use strict';
  const $ = (s, r) => (r || document).querySelector(s), esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const S = { opts: null, hist: [], cur: null, busy: false, seq: 0 };
  const api = (m, u, b) => root.V03.api(m, u, b);
  const ro = () => document.body.classList.contains('staging') || !!(root.V03 && root.V03.V && root.V03.V.viewer);
  const nf = (x, d) => (x == null ? 'Sin datos' : Number(x).toLocaleString('es-ES', { minimumFractionDigits: d, maximumFractionDigits: d, useGrouping: 'always' }));
  const tag = (s) => `<span class="tg7 ${/REAL|CACH/.test(s) ? 'ok' : /ESTIMADO/.test(s) ? 'am' : 'no'}">${esc(s)}</span>`;

  function table(rows) {
    if (!rows || !rows.length) return '<p class="muted">Sin datos</p>';
    const ks = Object.keys(rows[0]);
    return `<div class="tw7"><table class="tb7"><thead><tr>${ks.map((k) => `<th>${esc(k.replace(/_/g, ' '))}</th>`).join('')}</tr></thead><tbody>${rows.map((r) => `<tr>${ks.map((k) => `<td>${/^(estado|origen)$/.test(k) ? tag(r[k]) : typeof r[k] === 'number' ? nf(r[k], Number.isInteger(r[k]) ? 0 : 2) : esc(r[k] == null ? '—' : r[k])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  }
  function chart(rows) {   // barras de precio por competidor (solo REAL en caché local)
    const d = (rows || []).filter((r) => typeof r.precio_eur === 'number').slice(0, 12); if (!d.length) return '';
    const mx = Math.max(...d.map((r) => r.precio_eur)), W = 520, H = 120, bw = W / d.length;
    return `<figure class="ch7"><svg viewBox="0 0 ${W} ${H + 18}" role="img" aria-label="Precio por competidor (caché local)">${d.map((r, i) => `<rect x="${(i * bw + 4).toFixed(1)}" y="${(H - (r.precio_eur / mx) * H).toFixed(1)}" width="${(bw - 8).toFixed(1)}" height="${((r.precio_eur / mx) * H).toFixed(1)}" rx="3" fill="#18e6ff" opacity=".85"><title>${esc(r.asin)} · ${nf(r.precio_eur, 2)} €</title></rect><text x="${(i * bw + bw / 2).toFixed(1)}" y="${H + 13}" text-anchor="middle" font-size="9" fill="#9db4c9">${esc(r.asin.slice(-4))}</text>`).join('')}</svg><figcaption>Precio observado (€) · REAL, caché local de Keepa</figcaption></figure>`;
  }
  function section(x) {
    let body = '';
    if (x.tipo === 'tabla') body = chart(x.filas) + table(x.filas) + (x.resumen ? `<p class="sm7">Mediana de precio fresco: <b>${nf(x.resumen.mediana_precio_fresco_eur, 2)} €</b> · mediana €/100 mL: <b>${nf(x.resumen.mediana_100ml, 2)}</b> · ${esc(x.resumen.competidores)} competidores</p>` : '') + (x.nota ? `<p class="muted">${esc(x.nota)}</p>` : '');
    else if (x.tipo === 'escenarios') body = x.state === 'ESTIMADO' ? table(x.filas) + `<p class="muted">${esc(x.nota)}</p>` : `<p class="muted"><b>NO CALCULABLE</b> — faltan: ${esc((x.faltan || []).join(', '))}. ${esc(x.nota || '')}</p>`;
    else body = `<p>${esc(x.texto)}</p>`;
    return `<section class="rs7"><h5>${esc(x.titulo)} ${x.estado ? tag(x.estado) : x.state ? tag(x.state) : ''}</h5>${body}</section>`;
  }
  function renderResult(r) {
    const res = $('#b7Res'); if (!res) return;
    if (!r) { res.innerHTML = ''; return; }
    res.innerHTML = `<div class="m7 me">${esc(r.prompt)}<small>${esc(r.context.product || 'sin producto')} · ${esc(r.context.country)} · ${esc(r.context.period)}${r.context.asin ? ' · ' + esc(r.context.asin) : ''}</small></div>
      <div class="m7 ans7"><pre class="an7">${esc(r.result.answer)}</pre><small>${esc(r.result.mode)} · 0 llamadas de red · 0 tokens</small></div>${r.result.sections.map(section).join('')}`;
    res.scrollTop = 0;
  }
  function mdOf(r) { return `# Benchmarking · ${r.creado || ''}\n\n**Prompt:** ${r.prompt}\n\n**Contexto:** ${JSON.stringify(r.context)}\n\n${r.result.answer}\n\n` + r.result.sections.map((x) => `## ${x.titulo}${x.estado ? ' [' + x.estado + ']' : ''}\n` + (x.filas ? (x.filas.length ? '| ' + Object.keys(x.filas[0]).join(' | ') + ' |\n|' + Object.keys(x.filas[0]).map(() => '---|').join('') + '\n' + x.filas.map((f) => '| ' + Object.values(f).map((v) => (v == null ? '—' : String(v).replace(/\|/g, '/'))).join(' | ') + ' |').join('\n') : 'Sin datos') : (x.texto || (x.faltan ? 'NO CALCULABLE: ' + x.faltan.join(', ') : ''))) + '\n').join('\n'); }
  function csvOf(r) { const rows = (r.result.sections.find((x) => x.id === 'mercado') || {}).filas || []; if (!rows.length) return 'sin datos\n'; const ks = Object.keys(rows[0]); return '﻿' + [ks.join(';'), ...rows.map((x) => ks.map((k) => '"' + String(x[k] == null ? '' : x[k]).replace(/"/g, '""').replace(/^[=+\-@]/, "'$&") + '"').join(';'))].join('\n'); }
  function dl(name, text, type) { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], { type })); a.download = name; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 1500); }

  function shell() {
    const el = $('#bench7'); if (!el || el.dataset.built) return; el.dataset.built = '1';
    el.innerHTML = `<div class="bn7"><aside class="hs7 card7"><h4>Historial <small>persistente · SQLite</small></h4><ul id="b7Hist" class="hl7"></ul><p class="muted sm7">Los resultados se guardan en el servidor y entran en el respaldo existente.</p></aside>
      <section class="mn7"><div class="ctx7">
        <label class="f7"><span>Producto ·</span><select id="b7Prod" class="ro-ok" data-view-filter><option value="">Sin producto</option></select></label>
        <label class="f7"><span>ASIN ·</span><input id="b7Asin" class="ro-ok" data-view-filter maxlength="10" placeholder="B0XXXXXXXX" aria-label="ASIN"></label>
        <label class="f7"><span>País ·</span><select id="b7Cty" class="ro-ok" data-view-filter></select></label>
        <label class="f7"><span>Periodo ·</span><select id="b7Per" class="ro-ok" data-view-filter></select></label>
        <span id="b7Kp" class="kp7" title="Estado de Keepa (sin llamar)">Keepa: …</span></div>
        <div id="b7Res" class="res7" aria-live="polite"></div>
        <details class="hy7"><summary>Hipótesis de costes (escenarios de contribución, por unidad)</summary><div class="hg7">${[['pvp', 'PVP (IVA incl.) €'], ['coste_unit', 'Coste unidad €'], ['comision_pct', 'Comisión (0–1)'], ['logistica_unit', 'Logística €'], ['ads_unit', 'Publicidad €']].map(([k, l]) => `<label>${l}<input id="b7h_${k}" class="ro-ok" data-view-filter inputmode="decimal" aria-label="${l}"></label>`).join('')}</div></details>
        <form id="b7Form" class="cf7"><span id="b7Ro" class="ro7" hidden>Solo lectura: ejecutar requiere un rol que pueda escribir</span><textarea id="b7In" rows="3" placeholder="Escribe tu petición de benchmarking…" aria-label="Petición de benchmarking"></textarea>
          <div class="c7bar"><label class="ic7 ro-ok" title="Adjuntos: PENDIENTE"><input id="b7File" type="file" multiple hidden>＋</label><button type="button" id="b7Mic" class="ic7" disabled title="Voz: PENDIENTE">🎤</button><span class="pd7">Adjuntos, voz, búsqueda web e informe PDF: PENDIENTES</span><span id="b7Err" class="er7" role="alert"></span>
            <button type="button" id="b7Md" class="ic7 ro-ok">Exportar MD</button><button type="button" id="b7Csv" class="ic7 ro-ok">CSV</button><button type="button" id="b7Js" class="ic7 ro-ok">JSON</button><button type="submit" id="b7Run" class="c7send">Ejecutar ➤</button></div></form></section></div>`;
    $('#b7Form').onsubmit = (e) => { e.preventDefault(); run(); };
    $('#b7In').onkeydown = (e) => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); run(); } };
    $('#b7File').onchange = (e) => { $('#b7Err').textContent = [...e.target.files].length ? 'Adjuntos PENDIENTES: no se envían todavía.' : ''; };
    $('#b7Md').onclick = () => S.cur && dl('benchmarking.md', mdOf(S.cur), 'text/markdown'); $('#b7Csv').onclick = () => S.cur && dl('benchmarking.csv', csvOf(S.cur), 'text/csv'); $('#b7Js').onclick = () => S.cur && dl('benchmarking.json', JSON.stringify(S.cur, null, 1), 'application/json');
    $('#b7Hist').onclick = async (e) => { const b = e.target.closest('[data-rid]'); if (!b) return; const r = await api('GET', '/api/bench7/run?id=' + encodeURIComponent(b.dataset.rid)); if (r.ok) { S.cur = { ...r.j, context: r.j.context, result: r.j.result }; renderResult(S.cur); } };
  }
  async function load() {
    const my = ++S.seq, [o, k, h] = await Promise.all([api('GET', '/api/bench7/opciones'), api('GET', '/api/bench7/keepa'), api('GET', '/api/bench7/historial')]);
    if (my !== S.seq) return;
    if (o.ok) { S.opts = o.j; const sel = (id, arr, f) => { const e = $(id), v = e.value; e.innerHTML = arr.map(f).join(''); if (v) e.value = v; };
      sel('#b7Prod', [{ id: '', nombre: 'Sin producto' }, ...o.j.productos], (x) => `<option value="${esc(x.id)}">${esc(x.nombre)}</option>`); sel('#b7Cty', o.j.paises.map((c) => ({ id: c })), (x) => `<option ${x.id === 'ES' ? 'selected' : ''}>${x.id}</option>`); sel('#b7Per', o.j.periodos, (x) => `<option value="${x.id}" ${x.id === 'mes' ? 'selected' : ''}>${esc(x.l)}</option>`); }
    $('#b7Kp').textContent = k.ok ? `Keepa: clave ${k.j.clave_presente ? 'presente' : 'ausente'} · ${k.j.puede_llamar ? 'habilitado' : 'deshabilitado'} · sin llamadas · suscripción ≠ acceso API` : 'Keepa: Sin datos';
    $('#b7Hist').innerHTML = h.ok ? (h.j.items.length ? h.j.items.map((i) => `<li><button type="button" class="ro-ok" data-rid="${esc(i.id)}"><b>${esc(i.prompt)}</b><small>${esc(i.creado.slice(0, 16).replace('T', ' '))} · ${esc(i.contexto.country)}</small></button></li>`).join('') : '<li class="muted">Sin historial</li>') : '<li class="muted">Sin datos: no se pudo cargar el historial</li>';
    const rh = $('#b7Ro'); if (rh) rh.hidden = !ro(); $('#b7In').disabled = ro(); $('#b7Run').disabled = ro();
  }
  async function run() {
    if (S.busy || ro()) return; const q = $('#b7In').value.trim(), er = $('#b7Err'); if (!q) { er.textContent = 'Escribe una petición.'; return; }
    const num = (id) => { const v = $(id).value.trim().replace(',', '.'); return v === '' ? null : Number(v); }, ctx = { product: $('#b7Prod').value, asin: $('#b7Asin').value.trim(), country: $('#b7Cty').value, period: $('#b7Per').value };
    ['pvp', 'coste_unit', 'comision_pct', 'logistica_unit', 'ads_unit'].forEach((k) => { const v = num('#b7h_' + k); if (v !== null) ctx[k] = v; });
    S.busy = true; $('#b7Run').disabled = true; er.textContent = '';
    try { const r = await api('POST', '/api/bench7/run', { prompt: q, context: ctx }); if (r.ok) { S.cur = r.j; $('#b7In').value = ''; renderResult(S.cur); await load(); } else er.textContent = 'Error: ' + ((r.j && r.j.error) || r.status); }
    catch (e) { er.textContent = 'Error de red'; }
    S.busy = false; $('#b7Run').disabled = ro();
  }
  function onShow(id) {
    document.body.classList.toggle('dash7on', id === 'hoy' || id === 'bench');
    if (id === 'bench') { shell(); if (root.V03 && root.V03.V && root.V03.V.user) load(); else { const h = $('#b7Hist'); if (h) h.innerHTML = '<li class="muted">Inicia sesión para ver el historial</li>'; } }
  }
  root.BENCH7 = { onShow, load, S };
})(self);
