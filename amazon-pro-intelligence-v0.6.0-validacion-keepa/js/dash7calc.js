/* Rediseño global · fase 1 — cálculo PURO del dashboard (sin DOM, sin red). Datos DEMO ficticios y deterministas; nunca reales.
   Contribución = ventas netas − fabricación − comisiones − logística y otros − publicidad (excluye overhead general).
   Los ratios se calculan SIEMPRE sobre sumas (ponderado sobre ventas netas), nunca como promedio de porcentajes. */
(function (root) {
  'use strict';
  const LINES = [
    { id: 'phivital', l: 'PHIVITAL', w: 0.34, subs: [{ id: 'sup', l: 'Suplementos nutricionales', w: 0.6 }, { id: 'dep', l: 'Nutrición deportiva', w: 0.4 }] },
    { id: 'cosm', l: 'Cosmética', w: 0.26 }, { id: 'home', l: 'Home & Care', w: 0.18 }, { id: 'agri', l: 'Agricultura', w: 0.14 }, { id: 'tech', l: 'Nuevas tecnologías', w: 0.08 }];
  const REGIONS = [{ id: 'eu', l: 'Europa', w: 0.8, countries: [{ id: 'ES', l: 'España', w: 0.4 }, { id: 'DE', l: 'Alemania', w: 0.25 }, { id: 'FR', l: 'Francia', w: 0.2 }, { id: 'IT', l: 'Italia', w: 0.15 }] },
    { id: 'na', l: 'Norteamérica', w: 0.2, countries: [{ id: 'US', l: 'Estados Unidos', w: 0.75 }, { id: 'CA', l: 'Canadá', w: 0.25 }] }];
  const PERIODS = [{ id: 'dia', l: 'Día', f: 1 / 30 }, { id: 'semana', l: 'Semana', f: 7 / 30 }, { id: 'mes', l: 'Mes', f: 1 }, { id: 'anio', l: 'Año', f: 12 }];
  // Ejemplo coherente de dirección (Consolidado AHT · Todas · Mes), en céntimos para evitar errores de coma flotante
  const BASE = { bruto: 4990000, neto: 4123967, uds: 1000, ads: 499000, fab: 899000, com: 748500, log: 541000 };
  const VAR = { bruto: 0.00, neto: 0.00, uds: 0.04, ads: 0.15, fab: 0.08, com: 0.03, log: 0.10 };   // variación determinista por línea (solo demo)
  const MET = Object.keys(BASE);
  function leaves() {
    const out = [];
    LINES.forEach((ln, li) => (ln.subs || [{ id: '', l: '', w: 1 }]).forEach((sb) => REGIONS.forEach((rg) => rg.countries.forEach((c, ci) => out.push({ line: ln.id, sub: sb.id, region: rg.id, country: c.id, w: ln.w * sb.w * rg.w * c.w, li, ci })))));
    return out;
  }
  function alloc(total, ws) {   // reparto en enteros con mayor resto: la suma es EXACTA
    const sum = ws.reduce((a, b) => a + b, 0), raw = ws.map((w) => (total * w) / sum), fl = raw.map(Math.floor);
    let rest = total - fl.reduce((a, b) => a + b, 0);
    raw.map((r, i) => [r - fl[i], i]).sort((a, b) => b[0] - a[0] || a[1] - b[1]).forEach(([, i]) => { if (rest > 0) { fl[i]++; rest--; } });
    return fl;
  }
  let CACHE = null;
  function rows() {
    if (CACHE) return CACHE;
    const lv = leaves(), R = lv.map((x) => ({ ...x }));
    MET.forEach((m) => { const ws = lv.map((x) => x.w * (1 + VAR[m] * (((x.li * 7 + x.ci * 3) % 5) - 2) / 2)); alloc(BASE[m], ws).forEach((v, i) => { R[i][m] = v; }); });
    return (CACHE = R);
  }
  function filter(f) { return rows().filter((r) => (!f.line || f.line === 'all' || r.line === f.line) && (!f.sub || f.sub === 'all' || r.sub === f.sub) && (!f.region || f.region === 'all' || r.region === f.region) && (!f.country || f.country === 'all' || r.country === f.country)); }
  const eur = (c) => Math.round(c) / 100;
  function compute(f) {
    const per = PERIODS.find((p) => p.id === (f.period || 'mes')) || PERIODS[2], t = {}, rs = filter(f);
    MET.forEach((m) => { t[m] = rs.reduce((a, r) => a + r[m], 0); });
    const k = (m) => (m === 'uds' ? Math.round(t[m] * per.f) : Math.round(t[m] * per.f));
    const neto = k('neto'), fab = k('fab'), com = k('com'), log = k('log'), ads = k('ads'), contrib = neto - fab - com - log - ads;
    const out = { bruto: eur(k('bruto')), neto: eur(neto), uds: k('uds'), ads: eur(ads), fab: eur(fab), com: eur(com), log: eur(log), contrib: eur(contrib), contribPct: neto > 0 ? Math.round((contrib / neto) * 10000) / 100 : null, rows: rs.length };
    out.donut = neto > 0 ? [['Fabricación', fab], ['Comisiones', com], ['Logística y otros', log], ['Publicidad', ads], ['Contribución', contrib]].map(([l, v]) => ({ l, eur: eur(v), pct: Math.round((v / neto) * 10000) / 100 })) : [];
    return out;
  }
  // ratio ponderado de varias selecciones (suma de contribuciones / suma de netas) — NO promedio de porcentajes
  function weighted(list) { const n = list.reduce((a, x) => a + x.neto, 0), c = list.reduce((a, x) => a + x.contrib, 0); return n > 0 ? Math.round((c / n) * 10000) / 100 : null; }
  const api = { LINES, REGIONS, PERIODS, BASE, compute, weighted, rows };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.D7C = api;
})(typeof self !== 'undefined' ? self : this);
