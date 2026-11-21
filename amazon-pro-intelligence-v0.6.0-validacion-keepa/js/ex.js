/* Fase 4 — utilidades comunes de las pantallas ejecutivas (Ventas, Productos, Administración). Solo presentación: lee GET existentes. */
(function (root) {
  'use strict';
  const $ = (s, r) => (r || document).querySelector(s), $$ = (s, r) => [...(r || document).querySelectorAll(s)];
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const NS = () => (root.NAV6 && root.NAV6.state) || { mode: 'real', sec: 'hoy', sub: 0 };
  const STG = () => !!$('#envBanner');
  const isDemo = () => NS().mode === 'demo';
  const useReal = () => !isDemo() || STG();               // en DEMO fuera de staging jamás se consultan datos reales
  const VV = () => (root.V03 && root.V03.V) || {};
  const api = (m, p, b) => root.V03.api(m, p, b);
  const get = async (p) => { try { const r = await api('GET', p); return r.ok ? r.j : null; } catch (e) { return null; } };
  const kind = () => (isDemo() || STG() ? 'DEMO' : 'REAL');
  const badge = (k) => `<span class="h2b h2b-${k === 'REAL' ? 'real' : k === 'DEMO' ? 'demo' : 'nd'}">${esc(k)}</span>`;
  const eur = (x) => (x == null || isNaN(x) ? null : Number(x).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €');
  const pct = (x) => (x == null || isNaN(x) ? null : (x * 100).toLocaleString('es-ES', { maximumFractionDigits: 1 }) + ' %');
  const day = (s) => (s ? String(s).slice(0, 10) : 'SIN DATOS');
  /* Cada cifra lleva su procedencia. Un valor ausente es SIN DATOS (nunca 0). */
  const tile = (label, value, k, sub, cls) => `<div class="x4t ${cls || ''}" data-x4t="${esc(label)}"><span class="x4tl">${esc(label)}</span><b class="x4tv ${value == null ? 'nd' : ''}">${value == null ? 'SIN DATOS' : esc(value)}</b>${value == null ? '' : badge(k)}<small>${esc(sub || '')}</small></div>`;
  const fold = (id, title, body, open) => `<details class="h2det" id="${id}" ${open ? 'open' : ''}><summary>${esc(title)}</summary>${body}</details>`;
  /* Crea la raíz de una pantalla y mueve la pantalla heredada a su bloque «Metodología» (plegado). */
  function shell(id, tabSel, legacySel, slots) {
    let h = $('#' + id); if (h) return h; const tab = $(tabSel); if (!tab) return null;
    h = document.createElement('div'); h.id = id; h.className = 'h2root x4'; tab.insertBefore(h, tab.firstChild);
    h.innerHTML = `<div id="${id}top"></div>` + (slots || []).map((s) => fold(id + s[0], s[1], `<div id="${id}${s[0]}b"></div>`)).join('')
      + fold(id + 'met', 'Metodología', `<div id="${id}metb"></div><div id="${id}legacy"></div>`);
    const lg = $(legacySel); if (lg) $('#' + id + 'legacy').appendChild(lg); return h;
  }
  root.EX = { $, $$, esc, NS, STG, isDemo, useReal, VV, api, get, kind, badge, eur, pct, day, tile, fold, shell };
})(self);
