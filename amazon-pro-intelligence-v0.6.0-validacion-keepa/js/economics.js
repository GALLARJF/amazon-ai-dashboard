/* Amazon Pro Intelligence V0.2 — motor económico unitario (puro, sin DOM).
   Convenciones:
   - price = PVP CON IVA. net = price / (1 + IVA). Todos los costes en € por unidad vendida.
   - Comisión de referencia: se calcula sobre el PVP con IVA, con esquema por categoría.
   - Margen de contribución = ingreso neto - todos los costes variables - publicidad.
   - ACoS de equilibrio se expresa sobre la MISMA base que el ACoS objetivo (adsBasis: 'gross' = PVP con IVA, 'net' = neto).
   Las tarifas de la tabla FEE_SCHEDULES son ORIENTATIVAS (verified:false): deben confirmarse con las tarifas vigentes de Amazon. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.Econ = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  const EPS = 1e-9;
  const FEE_SCHEDULES = {
    generico_15: { label: 'Genérica 15 % (orientativa)', mode: 'flat', tiers: [{ upTo: Infinity, pct: 15 }], minFee: 0.3, verified: false },
    belleza_8_15: { label: 'Belleza / cuidado personal: 8 % hasta 10 €, 15 % por encima (orientativa)', mode: 'threshold', tiers: [{ upTo: 10, pct: 8 }, { upTo: Infinity, pct: 15 }], minFee: 0.3, verified: false },
    tramos_marginales: { label: 'Tramos marginales de ejemplo: 15 % hasta 100 €, 8 % el exceso (ejemplo)', mode: 'marginal', tiers: [{ upTo: 100, pct: 15 }, { upTo: Infinity, pct: 8 }], minFee: 0.3, verified: false },
    personalizado: { label: 'Personalizada (introduce % y mínimo)', mode: 'flat', tiers: [{ upTo: Infinity, pct: 15 }], minFee: 0, verified: false, custom: true },
  };

  function schedule(input) {
    const base = FEE_SCHEDULES[input.feeSchedule || 'generico_15'];
    if (!base) return null;
    if (base.custom) return { ...base, tiers: [{ upTo: Infinity, pct: +input.customReferralPct }], minFee: +(input.customMinFee || 0) };
    return base;
  }
  /* Comisión de referencia (€) para un PVP con IVA. */
  function referralFee(price, sch) {
    let fee = 0;
    if (sch.mode === 'marginal') {
      let lo = 0;
      for (const t of sch.tiers) { const hi = Math.min(price, t.upTo); if (hi > lo) fee += (hi - lo) * t.pct / 100; lo = t.upTo; if (price <= t.upTo) break; }
    } else {
      const t = sch.tiers.find((x) => price <= x.upTo) || sch.tiers[sch.tiers.length - 1];
      fee = price * t.pct / 100;
    }
    return Math.max(fee, sch.minFee || 0);
  }

  const DEFAULTS = {
    price: 24.9, vatPct: 21, feeSchedule: 'belleza_8_15', customReferralPct: 15, customMinFee: 0,
    cost: 5.2, prep: 0, fulfilMode: 'FBA', fbaFee: 4.1, fbmShipping: 0, fbmPackaging: 0, fbmHandling: 0,
    storageMonthly: 0.15, storageMonths: 2, returnsPct: 4, returnProcessing: 1.5, unsellablePct: 30, otherCosts: 0,
    acosTarget: 25, adsBasis: 'gross', minMarginPct: 15,
  };
  const NUM_RULES = [
    ['price', 'PVP con IVA', 0.01, 100000], ['vatPct', 'IVA %', 0, 30], ['cost', 'Coste de producto', 0, 100000], ['prep', 'Preparación/etiquetado', 0, 100000],
    ['fbaFee', 'Tarifa FBA', 0, 1000], ['fbmShipping', 'Envío FBM', 0, 1000], ['fbmPackaging', 'Embalaje FBM', 0, 1000], ['fbmHandling', 'Manipulación FBM', 0, 1000],
    ['storageMonthly', 'Almacenaje €/ud/mes', 0, 1000], ['storageMonths', 'Meses de almacenaje', 0, 60], ['returnsPct', 'Devoluciones %', 0, 100],
    ['returnProcessing', 'Coste por devolución', 0, 1000], ['unsellablePct', '% devoluciones no vendibles', 0, 100], ['otherCosts', 'Otros costes', 0, 100000],
    ['acosTarget', 'ACoS objetivo %', 0, 99], ['minMarginPct', 'Margen mínimo %', 0, 95],
  ];

  function validate(i) {
    const errors = [];
    NUM_RULES.forEach(([k, label, lo, hi]) => {
      const v = i[k];
      if (typeof v !== 'number' || !isFinite(v)) errors.push(`${label}: valor no numérico`);
      else if (v < lo || v > hi) errors.push(`${label}: fuera de rango (${lo}–${hi})`);
    });
    const sch = schedule(i);
    if (!sch) errors.push('Esquema de comisión desconocido');
    else if (sch.custom) {
      if (!isFinite(sch.tiers[0].pct) || sch.tiers[0].pct < 0 || sch.tiers[0].pct >= 100) errors.push('Comisión personalizada: fuera de rango (0–<100)');
      if (!isFinite(sch.minFee) || sch.minFee < 0) errors.push('Comisión mínima inválida');
    }
    if (!['FBA', 'FBM'].includes(i.fulfilMode)) errors.push('Modo logístico debe ser FBA o FBM');
    if (!['gross', 'net'].includes(i.adsBasis)) errors.push('Base de ACoS debe ser gross o net');
    return errors;
  }

  /* Economía unitaria. Devuelve { valid, errors, warnings, ... }. Nunca lanza. */
  function unit(raw, priceOverride) {
    const i = { ...DEFAULTS, ...raw };
    if (priceOverride !== undefined) i.price = priceOverride;
    const errors = validate(i);
    if (errors.length) return { valid: false, errors, warnings: [] };
    const sch = schedule(i), v = i.vatPct / 100, g = 1 / (1 + v), p = i.price;
    const net = p * g, referral = referralFee(p, sch);
    const fulfil = i.fulfilMode === 'FBA' ? i.fbaFee : i.fbmShipping + i.fbmPackaging + i.fbmHandling;
    const storage = i.fulfilMode === 'FBA' ? i.storageMonthly * i.storageMonths : 0;
    const returns = (i.returnsPct / 100) * (i.returnProcessing + (i.unsellablePct / 100) * i.cost);
    const fixed = i.cost + i.prep + fulfil + storage + returns + i.otherCosts;
    const beforeAds = net - fixed - referral;
    const adsBase = i.adsBasis === 'gross' ? p : net;
    const ads = (i.acosTarget / 100) * adsBase;
    const contribution = beforeAds - ads;
    const warnings = [];
    if (!sch.verified) warnings.push('Comisión basada en tarifa orientativa NO verificada: confirmar en las tarifas vigentes de Amazon para la categoría.');
    if (i.vatPct === 0) warnings.push('IVA 0 %: confirmar que el PVP no incluye IVA (régimen/destino).');
    if (i.adsBasis === 'gross') warnings.push('ACoS sobre PVP con IVA: verificar que los informes de Amazon Ads reportan ventas con IVA.');
    if (i.fulfilMode === 'FBA' && i.storageMonthly * i.storageMonths === 0) warnings.push('Almacenaje FBA = 0: el margen puede estar sobrestimado.');
    if (i.returnsPct === 0) warnings.push('Devoluciones 0 %: poco realista; el margen puede estar sobrestimado.');
    if (i.cost > net) warnings.push('El coste de producto supera el ingreso neto: pérdida garantizada.');
    return {
      valid: true, errors: [], warnings, input: i, schedule: sch,
      price: p, net, referral, fulfil, storage, returns, prep: i.prep, cost: i.cost, other: i.otherCosts, ads, adsBase,
      beforeAds, contribution, contributionPct: net > 0 ? contribution / net : 0,
      breakEvenAcos: adsBase > 0 ? beforeAds / adsBase : 0,
      costBreakdown: [
        ['Producto', i.cost], ['Prep./etiquetado', i.prep], ['Logística', fulfil], ['Almacenaje', storage], ['Comisión', referral],
        ['Devoluciones', returns], ['Otros', i.otherCosts], ['Publicidad', ads],
      ],
    };
  }

  /* Precio mínimo (PVP con IVA) que alcanza `marginPct` de contribución sobre neto tras publicidad.
     Resuelve cada tramo de comisión de forma exacta (la comisión por umbral es discontinua) y devuelve el menor válido. */
  function minPrice(raw, marginPct) {
    const i = { ...DEFAULTS, ...raw };
    const m = (marginPct === undefined ? i.minMarginPct : marginPct) / 100;
    if (validate({ ...i, price: 1 }).length) return null;
    const sch = schedule(i), g = 1 / (1 + i.vatPct / 100), acos = i.acosTarget / 100, c = i.adsBasis === 'gross' ? 1 : g;
    const fulfil = i.fulfilMode === 'FBA' ? i.fbaFee : i.fbmShipping + i.fbmPackaging + i.fbmHandling;
    const storage = i.fulfilMode === 'FBA' ? i.storageMonthly * i.storageMonths : 0;
    const K = i.cost + i.prep + fulfil + storage + (i.returnsPct / 100) * (i.returnProcessing + (i.unsellablePct / 100) * i.cost) + i.otherCosts;
    const regimes = []; // fee = A + B p válido en (lo, hi]
    if (sch.mode === 'marginal') {
      let lo = 0, acc = 0;
      sch.tiers.forEach((t) => { regimes.push({ A: acc - lo * t.pct / 100, B: t.pct / 100, lo, hi: t.upTo }); acc += (Math.min(t.upTo, 1e9) - lo) * t.pct / 100; lo = t.upTo; });
    } else {
      let lo = 0;
      sch.tiers.forEach((t) => { regimes.push({ A: 0, B: t.pct / 100, lo, hi: t.upTo }); lo = t.upTo; });
    }
    if (sch.minFee > 0) regimes.push({ A: sch.minFee, B: 0, lo: 0, hi: Infinity });
    let best = null;
    regimes.forEach((r) => {
      const den = g * (1 - m) - r.B - acos * c;
      if (den <= EPS) return;
      const p = (K + r.A) / den;
      if (!(p > r.lo - EPS && p <= r.hi + EPS) || p < 0.01) return;
      const u = unit(i, p);
      if (u.valid && u.contributionPct >= m - 1e-7 && (best === null || p < best)) best = p;
    });
    if (best === null) return null;
    let commercial = Math.ceil(best * 100 - 1e-9) / 100;
    for (let k = 0; k < 500; k++, commercial = Math.round((commercial + 0.01) * 100) / 100) {
      const u = unit(i, commercial);
      if (u.valid && u.contributionPct >= m - 1e-9) return { exact: best, commercial };
    }
    return { exact: best, commercial: null };
  }

  return { FEE_SCHEDULES, DEFAULTS, referralFee, schedule, validate, unit, minPrice, EPS };
});
