/* Amazon Pro Intelligence — lógica pura (sin DOM). Usable en navegador (window.Calc) y Node (tests). */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.Calc = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  const r2 = (x) => Math.round(x * 100) / 100;
  const safeDiv = (a, b) => (b ? a / b : 0);

  function addDays(iso, n) {
    const d = new Date(iso + 'T00:00:00Z');
    d.setUTCDate(d.getUTCDate() + n);
    return d.toISOString().slice(0, 10);
  }
  function endDate(rows) { return rows.reduce((m, r) => (r.date > m ? r.date : m), ''); }

  /* Filtra por producto / periodo (últimos N días hasta la última fecha del dataset) / marketplace. */
  function filterRows(rows, f, shift) {
    if (!rows.length) return [];
    const days = +f.period || 30;
    const end = addDays(endDate(rows), -(shift || 0) * days);
    const start = addDays(end, -(days - 1));
    return rows.filter((r) =>
      r.date >= start && r.date <= end &&
      (f.product === 'all' || r.product === f.product) &&
      (f.marketplace === 'all' || r.marketplace === f.marketplace));
  }
  const sum = (rows, k) => rows.reduce((s, r) => s + (+r[k] || 0), 0);

  function aggregate(rows) {
    const sales = sum(rows, 'sales'), units = sum(rows, 'units'), cogs = sum(rows, 'cogs'),
      fees = sum(rows, 'fees'), adSpend = sum(rows, 'ad_spend'), adSales = sum(rows, 'ad_sales');
    const returnsCost = sum(rows, 'returns_cost'), storage = sum(rows, 'storage_fees'), other = sum(rows, 'other_costs');
    const margin = sales - cogs - fees - returnsCost - storage - other - adSpend;
    // stock = última fecha disponible por producto|marketplace
    const last = {};
    rows.forEach((r) => {
      const k = r.product + '|' + r.marketplace;
      if (!last[k] || r.date > last[k].date) last[k] = r;
    });
    const stock = Object.values(last).reduce((s, r) => s + (+r.stock || 0), 0);
    return {
      sales: r2(sales), units, cogs: r2(cogs), fees: r2(fees), adSpend: r2(adSpend), adSales: r2(adSales),
      returnsCost: r2(returnsCost), storage: r2(storage), other: r2(other),
      margin: r2(margin), marginPct: safeDiv(margin, sales),
      acos: safeDiv(adSpend, adSales), tacos: safeDiv(adSpend, sales),
      marginBeforeAdsPct: safeDiv(sales - cogs - fees - returnsCost - storage - other, sales), stock,
    };
  }
  const pctDelta = (cur, prev) => (prev ? (cur - prev) / Math.abs(prev) : null);

  function dailySeries(rows) {
    const m = {};
    rows.forEach((r) => {
      const d = (m[r.date] = m[r.date] || { date: r.date, sales: 0, margin: 0, units: 0, ad_spend: 0, ad_sales: 0, p: 0, c: 0, b: 0, n: 0 });
      d.sales += +r.sales; d.units += +r.units; d.ad_spend += +r.ad_spend; d.ad_sales += +r.ad_sales;
      d.margin += r.sales - r.cogs - r.fees - (+r.returns_cost || 0) - (+r.storage_fees || 0) - (+r.other_costs || 0) - r.ad_spend;
      d.p += +r.price; d.c += +r.competitor_price; d.b += +r.bsr; d.n += 1;
    });
    return Object.values(m).sort((a, b) => (a.date < b.date ? -1 : 1)).map((d) => ({
      date: d.date, sales: d.sales, margin: d.margin, units: d.units, ad_spend: d.ad_spend, ad_sales: d.ad_sales,
      price: d.p / d.n, competitor: d.c / d.n, bsr: d.b / d.n,
    }));
  }
  /* Agrupa una serie diaria en n cubos (para barras legibles). */
  function bucket(series, n) {
    if (series.length <= n) return series.map((s) => ({ ...s, label: s.date.slice(5) }));
    const size = Math.ceil(series.length / n), out = [];
    for (let i = 0; i < series.length; i += size) {
      const ch = series.slice(i, i + size);
      const o = { label: ch[0].date.slice(5), date: ch[0].date };
      ['sales', 'margin', 'units', 'ad_spend', 'ad_sales'].forEach((k) => (o[k] = ch.reduce((s, x) => s + x[k], 0)));
      ['price', 'competitor', 'bsr'].forEach((k) => (o[k] = ch.reduce((s, x) => s + x[k], 0) / ch.length));
      out.push(o);
    }
    return out;
  }
  function groupBy(rows, key) {
    const m = {};
    rows.forEach((r) => { (m[r[key]] = m[r[key]] || []).push(r); });
    return m;
  }

  function median(a) {
    if (!a.length) return null;
    const s = [...a].sort((x, y) => x - y), m = Math.floor(s.length / 2);
    return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
  }
  function percentile(a, p) {
    if (!a.length) return null;
    const s = [...a].sort((x, y) => x - y), i = (s.length - 1) * p, lo = Math.floor(i), hi = Math.ceil(i);
    return s[lo] + (s[hi] - s[lo]) * (i - lo);
  }
  /* ---------- CSV ---------- */
  const CSV_COLS = ['date', 'product', 'marketplace', 'units', 'sales', 'cogs', 'fees', 'ad_spend', 'ad_sales', 'price', 'competitor_price', 'bsr', 'stock'];
  const CSV_OPT = ['returns_cost', 'storage_fees', 'other_costs']; // opcionales; si faltan se asume 0 y se AVISA
  function parseCSV(text) {
    const errors = [], rows = [], warnings = [];
    const lines = text.replace(/\r/g, '').split('\n').filter((l) => l.trim());
    if (!lines.length) return { rows, errors: ['Archivo vacío'] };
    const sep = lines[0].includes(';') && !lines[0].includes(',') ? ';' : ',';
    const head = lines[0].split(sep).map((h) => h.trim().toLowerCase());
    const miss = CSV_COLS.filter((c) => !head.includes(c));
    if (miss.length) return { rows, errors: ['Faltan columnas: ' + miss.join(', ')], warnings };
    const optMiss = CSV_OPT.filter((c) => !head.includes(c));
    if (optMiss.length) warnings.push('El CSV no incluye ' + optMiss.join(', ') + ': se asumen 0 y el margen puede estar SOBRESTIMADO.');
    lines.slice(1).forEach((ln, idx) => {
      const c = ln.split(sep), o = {};
      head.forEach((h, k) => (o[h] = (c[k] || '').trim()));
      const bad = [];
      if (!/^\d{4}-\d{2}-\d{2}$/.test(o.date)) bad.push('date');
      if (!o.product) bad.push('product');
      if (!o.marketplace) bad.push('marketplace');
      CSV_COLS.slice(3).forEach((k) => { const n = Number(o[k]); if (o[k] === '' || !isFinite(n)) bad.push(k); else o[k] = n; });
      CSV_OPT.forEach((k) => { if (!head.includes(k) || o[k] === '') o[k] = 0; else { const n = Number(o[k]); if (!isFinite(n)) bad.push(k); else o[k] = n; } });
      ['units', 'sales', 'cogs', 'fees', 'ad_spend', 'ad_sales', 'price', 'competitor_price', 'bsr', 'stock', ...CSV_OPT].forEach((k) => { if (typeof o[k] === 'number' && o[k] < 0) bad.push(k + ' (negativo)'); });
      if (bad.length) errors.push(`Fila ${idx + 2}: valor inválido en ${bad.join(', ')}`);
      else rows.push(o);
    });
    return { rows, errors, warnings };
  }

  return { r2, addDays, endDate, filterRows, aggregate, pctDelta, dailySeries, bucket, groupBy, median, percentile, parseCSV, CSV_COLS, CSV_OPT, safeDiv };
});
