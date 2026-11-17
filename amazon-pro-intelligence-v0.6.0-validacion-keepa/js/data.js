/* DATASET DEMO determinista (semilla fija). NO son datos reales de Amazon. */
(function (root) {
  function rng(seed) { // mulberry32
    return function () {
      seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  const PRODUCTS = [
    { id: 'DEMO-A', name: 'Producto A (DEMO)', price: 24.9, cost: 5.2, fba: 4.1, units: 14, bsr: 6200, rating: 4.5, reviews: 312, acos: 0.24 },
    { id: 'DEMO-B', name: 'Producto B (DEMO)', price: 17.5, cost: 4.4, fba: 3.4, units: 22, bsr: 3100, rating: 4.1, reviews: 904, acos: 0.31 },
    { id: 'DEMO-C', name: 'Producto C (DEMO)', price: 39.0, cost: 12.8, fba: 5.6, units: 7, bsr: 11800, rating: 4.7, reviews: 88, acos: 0.2 },
    { id: 'DEMO-D', name: 'Producto D (DEMO)', price: 12.9, cost: 4.1, fba: 3.1, units: 18, bsr: 4400, rating: 3.9, reviews: 1204, acos: 0.38 },
  ];
  const MKTS = { ES: 1, DE: 0.9, FR: 0.55, IT: 0.4 };
  const END = '2026-11-15', DAYS = 90;

  function addDays(iso, n) { const d = new Date(iso + 'T00:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); }

  function build() {
    const R = rng(20261116), rows = [];
    PRODUCTS.forEach((p, pi) => {
      Object.entries(MKTS).forEach(([mk, mf], mi) => {
        let stock = Math.round(p.units * mf * 60);
        for (let d = 0; d < DAYS; d++) {
          const date = addDays(END, -(DAYS - 1 - d));
          const dow = new Date(date + 'T00:00:00Z').getUTCDay();
          const season = 1 + 0.18 * Math.sin((d + pi * 9) / 11) + (dow === 0 || dow === 6 ? -0.1 : 0.04) + d / DAYS * (0.12 + pi * 0.03);
          const units = Math.max(0, Math.round(p.units * mf * season * (0.8 + R() * 0.4)));
          const price = +(p.price * (0.97 + R() * 0.06)).toFixed(2);
          const net = (units * price) / 1.21;
          const fees = units * (price * 0.15 + p.fba);
          const adSpend = net * p.acos * (0.55 + R() * 0.5) * 0.45;
          const adSales = adSpend / (p.acos * (0.8 + R() * 0.45));
          const comp = +(p.price * (1.02 + 0.06 * Math.sin((d + pi) / 17) + (R() - 0.5) * 0.05) * (pi === 3 ? 0.88 : 1)).toFixed(2);
          const bsr = Math.round(p.bsr / mf * (1.1 - d / DAYS * 0.25 + (R() - 0.5) * 0.2));
          stock = Math.max(0, stock - units);
          if (stock < p.units * mf * 8 && R() < 0.12) stock += Math.round(p.units * mf * 45);
          rows.push({ date, product: p.id, marketplace: mk, units, sales: +net.toFixed(2), cogs: +(units * p.cost).toFixed(2),
            fees: +fees.toFixed(2), returns_cost: +(units * 0.04 * (1.5 + 0.3 * p.cost)).toFixed(2), storage_fees: +(stock * 0.15 / 30).toFixed(2), other_costs: 0, ad_spend: +adSpend.toFixed(2), ad_sales: +adSales.toFixed(2), price, competitor_price: comp, bsr, stock });
        }
      });
    });
    return rows;
  }
  function keywords() {
    const R = rng(777), base = ['crema', 'hidratante', 'natural', 'pies secos', 'vegano', 'regalo', 'kit viaje', 'premium'], out = [];
    PRODUCTS.forEach((p) => base.slice(0, 6).forEach((w, i) => out.push({
      product: p.id, keyword: w + ' ' + (i % 2 ? 'mujer' : 'hombre'), volume: Math.round(800 + R() * 14000),
      rank: Math.max(1, Math.round(R() * 38)), spend: +(R() * 90).toFixed(2), orders: Math.round(R() * 24),
    })));
    return out;
  }
  root.DemoData = { products: PRODUCTS.map((p) => ({ id: p.id, name: p.name, rating: p.rating, reviews: p.reviews })), rows: build(), keywords: keywords(), end: END };
})(typeof self !== 'undefined' ? self : this);
