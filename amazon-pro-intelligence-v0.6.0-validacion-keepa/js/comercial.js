/* V1.1 — ECONOMÍA COMERCIAL ACTIVCORE (solo lectura). Lee GET /api/v08/*. Sin entradas, sin escritura, sin red externa, sin almacenamiento.
   HOY/DECISIONES arriba; detalle plegado. Todo parámetro muestra fuente, fecha y estado; nada «verificado» sin evidencia oficial.
   Datos de Ads: solo informes importados por un administrador; sin informes → «SIN DATOS». Los datos demo/sintéticos no se mezclan. */
(function (root) {
  'use strict';
  const $ = (s, r) => (r || document).querySelector(s);
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const eur = (x) => (x == null || typeof x !== 'number' || !isFinite(x) ? 'NO DETERMINABLE' : x.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €');
  const pc = (x) => (x == null ? 'NO DETERMINABLE' : (x * 100).toLocaleString('es-ES', { maximumFractionDigits: 1 }) + ' %');
  const badge = (t, c) => `<span class="b7 ${c || 'b7-wait'}">${esc(t)}</span>`;
  const get = async (p) => { try { const r = await root.V03.api('GET', p); return r.ok ? r.j : { error: (r.j && r.j.error) || ('HTTP ' + r.status) }; } catch (e) { return { error: String(e) }; } };
  const box = () => $('#comRoot');
  const err = (j) => (j && j.error ? `<p class="muted">NO DISPONIBLE: ${esc(j.error)}</p>` : '');

  function ecoRow(e, lab) { return `<tr><td>${esc(lab)}</td><td>${eur(e.precio_neto_sin_iva)}</td><td>${eur(e.margen_bruto_ud)}</td><td><b>${eur(e.contribucion_antes_ads_ud)}</b></td><td>${esc(e.estado_parametros)}</td></tr>`; }
  async function render() {
    const R = box(); if (!R) return; R.innerHTML = '<p class="muted">Cargando…</p>';
    const [fba, fbm, p100, sim, pil, pre, chk, par, ads, al] = await Promise.all([
      get('/api/v08/comercial/economia?canal=FBA&ventas=300&dias=90'), get('/api/v08/comercial/economia?canal=FBM&ventas=300&dias=90'), get('/api/v08/comercial/economia?canal=FBA&ventas=100&dias=90'),
      get('/api/v08/comercial/simulador'), get('/api/v08/comercial/piloto'), get('/api/v08/comercial/presupuesto'), get('/api/v08/comercial/checklist'),
      get('/api/v08/comercial/parametros'), get('/api/v08/comercial/ads'), get('/api/v08/comercial/alertas')]);
    const tc = await Promise.all([0, 0.05, 0.1, 0.15, 0.25].map((t) => get('/api/v08/comercial/economia?canal=FBA&ventas=300&dias=90&tacos=' + t)));
    const E = (j) => (j && j.economia) || {};
    const tacos = tc.map((j) => ({ tacos: E(j).tacos, ads_ud: E(j).ads_ud, contribucion_tras_ads_ud: E(j).contribucion_tras_ads_ud }));
    let h = `<section class="card c-cyan"><h3>HOY · Economía comercial ACTIVCORE ${badge('SOLO LECTURA', 'b7-doc')} ${badge('PARÁMETROS ' + String(E(fba).estado_parametros || 'pendiente').toUpperCase(), 'b7-wait')}</h3>
      <p>Contribución por unidad <b>antes de Ads</b>: FBA 300 ventas/90 d <b>${eur(E(fba).contribucion_antes_ads_ud)}</b> · FBM <b>${eur(E(fbm).contribucion_antes_ads_ud)}</b> · FBA 100 ventas/90 d <b>${eur(E(p100).contribucion_antes_ads_ud)}</b> (plan 39 €/mes prorrateado: no se reutiliza la base de 300).</p>
      <p class="muted">Objetivos 10/15/18/20 € de contribución por unidad: NO garantizados. Ninguna tarifa figura como verificada sin evidencia oficial. Presupuesto de Ads propuesto: NO AUTORIZADO. Ninguna acción se ejecuta desde esta pantalla.</p>${err(fba)}</section>`;
    h += `<section class="card"><h3>DECISIONES pendientes de una persona</h3><ol>
      <li>Autorizar (o no) el Ads piloto de ${esc(((pil.ads_piloto || {}).importe))} € / ${esc(((pil.ads_piloto || {}).dias))} días y el envío FBA de ${esc(((pil.reparto_unidades || {}).fba))} uds: <b>NO AUTORIZADO</b>.</li>
      <li>Confirmar coste del lote 2 (8,99 €, pendiente) y la tarifa FBA 3,81 € (condicionada a peso/dimensiones).</li>
      <li>Confirmar elegibilidad/compatibilidad de incentivos temporales (cero por defecto) y la ventana de atribución de Ads.</li></ol></section>`;
    h += `<details open class="card"><summary><b>Economía unitaria por canal</b></summary><table class="t"><thead><tr><th>Escenario</th><th>Neto sin IVA</th><th>Margen bruto</th><th>Contribución antes de Ads</th><th>Estado</th></tr></thead><tbody>${ecoRow(E(fba), 'FBA · 300 ventas/90 d')}${ecoRow(E(fbm), 'FBM · 300 ventas/90 d')}${ecoRow(E(p100), 'FBA · 100 ventas/90 d')}</tbody></table>
      <p class="muted">Niveles separados: bruto, contribución, operativo, neto, caja e IVA. Neto y caja: NO CALCULABLE sin devoluciones/costes fijos confirmados. IVA repercutido por ud: ${eur(E(fba).iva_repercutido_ud)} (aparte de los márgenes).</p></details>`;
    h += `<details class="card"><summary><b>TACoS 0/5/10/15/25 % (denominador: ventas netas sin IVA)</b></summary><table class="t"><thead><tr><th>TACoS</th><th>Ads/ud</th><th>Contribución tras Ads</th></tr></thead><tbody>${tacos.map((t) => `<tr><td>${pc(t.tacos)}</td><td>${eur(t.ads_ud)}</td><td>${eur(t.contribucion_tras_ads_ud)}</td></tr>`).join('') || '<tr><td colspan="3">SIN DATOS</td></tr>'}</tbody></table></details>`;
    h += `<details class="card"><summary><b>Piloto propuesto y presupuesto escalonado</b> ${badge('NO AUTORIZADO', 'b7-none')}</summary>
      <p>Reparto: ${Object.entries(pil.reparto_unidades || {}).map(([k, v]) => esc(k) + ' ' + esc(v)).join(' · ')} (total ${esc(pil.total_unidades)}). Ventas para cubrir el Ads piloto: ${esc((pil.ads_piloto || {}).ventas_para_cubrir_ads)}.</p>
      <table class="t"><thead><tr><th>Tramo</th><th>Importe</th><th>Acumulado</th></tr></thead><tbody>${(pre.tramos || []).map((t) => `<tr><td>${esc(t.nombre || t.tramo || t.dias || '')}</td><td>${eur(t.importe)}</td><td>${eur(t.acumulado)}</td></tr>`).join('')}</tbody></table>
      <p class="muted">Cada ampliación exige evidencia y aprobación humana, y se ejecuta manualmente fuera de esta herramienta.</p></details>`;
    const info = (ads.informes || []);
    h += `<details class="card"><summary><b>Ads (informes importados)</b> ${badge(info.length ? 'REAL IMPORTADO' : 'SIN DATOS', info.length ? 'b7-real' : 'b7-none')}</summary>${info.length ? `<p>${info.length} informe(s). ACoS/TACoS con denominador explícito; las ventas no atribuidas NO se llaman orgánicas.</p>` : '<p>Sin informes de Ads importados. No se muestran datos de demostración como reales.</p>'}${(ads.recomendaciones || []).map((r) => `<p>• ${esc(r.tipo)} · ${esc(r.termino || '')} — ${esc(r.explicacion || '')}</p>`).join('')}</details>`;
    h += `<details class="card"><summary><b>Alertas</b> (${(al.alertas || []).length})</summary>${(al.alertas || []).map((a) => `<p>${esc(a.codigo)}: ${esc(a.mensaje || '')}</p>`).join('') || '<p>Sin alertas: faltan datos de gasto, stock y ventas reales (no se inventan).</p>'}</details>`;
    h += `<details class="card"><summary><b>Checklist (sincronizado con activcore-launch-control)</b></summary><ul>${(chk.checklist || []).map((c) => `<li>${esc(c.area || c.grupo || '')} — ${esc(c.item || '')} ${badge(c.estado || 'POR CONFIRMAR', 'b7-wait')}</li>`).join('')}</ul></details>`;
    h += `<details class="card"><summary><b>Parámetros (fuente · fecha · estado)</b></summary><table class="t"><thead><tr><th>Parámetro</th><th>Valor</th><th>Fuente</th><th>Fecha</th><th>Estado</th></tr></thead><tbody>${Object.entries(par.parametros || {}).map(([k, v]) => `<tr><td>${esc(k)}</td><td>${esc(v.v)} ${esc(v.unidad || '')}</td><td>${esc(v.fuente)}</td><td>${esc(v.fecha)}</td><td>${esc(v.estado)}</td></tr>`).join('')}</tbody></table></details>`;
    R.innerHTML = h;
  }
  function init() {
    const b = $('[data-tab="comercial"]'); if (b) b.addEventListener('click', () => setTimeout(render, 0));
    const t = $('#tab-comercial'); if (t && 'MutationObserver' in root) new MutationObserver(() => { if (t.classList.contains('on') && !t.dataset.done) { t.dataset.done = '1'; render(); } }).observe(t, { attributes: true, attributeFilter: ['class'] });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
  root.COM = { render };
})(typeof window !== 'undefined' ? window : globalThis);
