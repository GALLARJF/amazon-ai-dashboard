/* Gráficos SVG propios (sin dependencias). */
(function (root) {
  const NS = 'http://www.w3.org/2000/svg';
  const fmtK = (v) => (Math.abs(v) >= 1000 ? (v / 1000).toFixed(1).replace(/\.0$/, '') + 'k' : v.toFixed(v % 1 ? 1 : 0));

  function frame(el) {
    el.innerHTML = '';
    const W = Math.max(el.clientWidth, 200), H = Math.max(el.clientHeight, 110);
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', W); svg.setAttribute('height', H); svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    el.appendChild(svg);
    const tip = document.createElement('div'); tip.className = 'tip'; tip.style.display = 'none'; el.appendChild(tip);
    return { svg, tip, W, H, m: { l: 46, r: 12, t: 10, b: 22 } };
  }
  const s = (n, a, p) => { const e = document.createElementNS(NS, n); Object.entries(a).forEach(([k, v]) => e.setAttribute(k, v)); p && p.appendChild(e); return e; };

  /* o: {labels[], series:[{name,color,values[],fmt}], invert?, zero?} */
  function line(el, o) {
    const f = frame(el), { svg, tip, W, H, m } = f, n = o.labels.length;
    if (!n) { el.textContent = 'Sin datos para el filtro'; return; }
    const all = o.series.flatMap((x) => x.values);
    let lo = o.zero === false ? Math.min(...all) : Math.min(0, ...all), hi = Math.max(...all);
    if (lo === hi) hi = lo + 1;
    const pad = (hi - lo) * 0.06; hi += pad; if (o.zero === false) lo -= pad;
    const X = (i) => m.l + (n === 1 ? 0 : (i * (W - m.l - m.r)) / (n - 1));
    const Y = (v) => { const t = (v - lo) / (hi - lo); return m.t + (o.invert ? t : 1 - t) * (H - m.t - m.b); };
    for (let k = 0; k <= 3; k++) {
      const v = lo + ((hi - lo) * k) / 3, y = Y(v);
      s('line', { x1: m.l, x2: W - m.r, y1: y, y2: y, class: 'grid' }, svg);
      const t = s('text', { x: m.l - 6, y: y + 4, class: 'ax', 'text-anchor': 'end' }, svg); t.textContent = fmtK(v);
    }
    [0, Math.floor((n - 1) / 2), n - 1].forEach((i) => {
      const t = s('text', { x: X(i), y: H - 6, class: 'ax', 'text-anchor': i === 0 ? 'start' : i === n - 1 ? 'end' : 'middle' }, svg); t.textContent = o.labels[i];
    });
    o.series.forEach((se) => {
      const pts = se.values.map((v, i) => `${X(i).toFixed(1)},${Y(v).toFixed(1)}`);
      if (se.area) s('polygon', { points: `${X(0)},${Y(lo)} ${pts.join(' ')} ${X(n - 1)},${Y(lo)}`, fill: se.color, opacity: 0.13 }, svg);
      s('polyline', { points: pts.join(' '), fill: 'none', stroke: se.color, 'stroke-width': 2.2, 'stroke-linejoin': 'round', style: `filter:drop-shadow(0 0 4px ${se.color})` }, svg);
    });
    const cur = s('line', { y1: m.t, y2: H - m.b, class: 'cursor', style: 'display:none' }, svg);
    const dots = o.series.map((se) => s('circle', { r: 4, fill: se.color, style: 'display:none' }, svg));
    svg.addEventListener('mousemove', (e) => {
      const r = svg.getBoundingClientRect(), x = e.clientX - r.left;
      const i = Math.max(0, Math.min(n - 1, Math.round(((x - m.l) / (W - m.l - m.r)) * (n - 1))));
      cur.setAttribute('x1', X(i)); cur.setAttribute('x2', X(i)); cur.style.display = '';
      dots.forEach((d, k) => { d.setAttribute('cx', X(i)); d.setAttribute('cy', Y(o.series[k].values[i])); d.style.display = ''; });
      tip.style.display = 'block';
      tip.innerHTML = `<b>${o.labels[i]}</b>` + o.series.map((se) => `<div><i style="background:${se.color}"></i>${se.name}: ${(se.fmt || fmtK)(se.values[i])}</div>`).join('');
      tip.style.left = Math.min(X(i) + 10, W - 150) + 'px'; tip.style.top = '4px';
    });
    svg.addEventListener('mouseleave', () => { cur.style.display = 'none'; dots.forEach((d) => (d.style.display = 'none')); tip.style.display = 'none'; });
  }

  /* Barras agrupadas. */
  function bars(el, o) {
    const f = frame(el), { svg, tip, W, H, m } = f, n = o.labels.length;
    if (!n) { el.textContent = 'Sin datos para el filtro'; return; }
    const hi = Math.max(1, ...o.series.flatMap((x) => x.values)) * 1.08;
    const Y = (v) => m.t + (1 - v / hi) * (H - m.t - m.b);
    for (let k = 0; k <= 3; k++) {
      const v = (hi * k) / 3, y = Y(v);
      s('line', { x1: m.l, x2: W - m.r, y1: y, y2: y, class: 'grid' }, svg);
      const t = s('text', { x: m.l - 6, y: y + 4, class: 'ax', 'text-anchor': 'end' }, svg); t.textContent = fmtK(v);
    }
    const slot = (W - m.l - m.r) / n, bw = Math.max(3, (slot * 0.78) / o.series.length);
    o.labels.forEach((lb, i) => {
      o.series.forEach((se, k) => {
        const x = m.l + i * slot + slot * 0.11 + k * bw, y = Y(se.values[i]);
        const r = s('rect', { x, y, width: bw - 1, height: Math.max(0, H - m.b - y), rx: 2, fill: se.color, style: `filter:drop-shadow(0 0 3px ${se.color})` }, svg);
        r.addEventListener('mousemove', () => {
          tip.style.display = 'block';
          tip.innerHTML = `<b>${lb}</b>` + o.series.map((q) => `<div><i style="background:${q.color}"></i>${q.name}: ${(q.fmt || fmtK)(q.values[i])}</div>`).join('');
          tip.style.left = Math.min(x + 10, W - 150) + 'px'; tip.style.top = '4px';
        });
        r.addEventListener('mouseleave', () => (tip.style.display = 'none'));
      });
      if (i % Math.ceil(n / 6) === 0) { const t = s('text', { x: m.l + i * slot + slot / 2, y: H - 6, class: 'ax', 'text-anchor': 'middle' }, svg); t.textContent = lb; }
    });
  }

  /* Barra apilada horizontal de costes: parts [{label,value,color}] */
  function stack(el, parts) {
    const tot = parts.reduce((a, p) => a + Math.max(0, p.value), 0) || 1;
    el.innerHTML = '<div class="stackbar">' + parts.filter((p) => p.value > 0).map((p) =>
      `<span style="flex:${p.value / tot};background:${p.color}" title="${p.label}: ${p.value.toFixed(2)} €"></span>`).join('') + '</div>' +
      '<div class="stacklg">' + parts.map((p) => `<span><i style="background:${p.color}"></i>${p.label} ${p.value.toFixed(2)} €</span>`).join('') + '</div>';
  }
  root.Charts = { line, bars, stack };
})(self);
