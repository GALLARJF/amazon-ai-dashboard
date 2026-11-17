// Pruebas del motor económico con resultados esperados calculados a mano.
const assert = require('assert'); const E = require('../js/economics.js');
let n = 0; const t = (name, fn) => { fn(); n++; console.log('OK  ' + name); };
const near = (a, b, tol = 1e-9) => assert.ok(Math.abs(a - b) <= tol, `esperado ${b}, obtenido ${a}`);
const zero = { ...E.DEFAULTS, prep: 0, storageMonthly: 0, storageMonths: 0, returnsPct: 0, returnProcessing: 0, unsellablePct: 0, otherCosts: 0, fbaFee: 0 };
const flat10 = { ...zero, feeSchedule: 'personalizado', customReferralPct: 10, customMinFee: 0, vatPct: 21, price: 121, cost: 30, fbaFee: 10, acosTarget: 10 };

t('IVA: PVP 121 con 21% → neto 100', () => near(E.unit(flat10).net, 100));
t('caso base (base bruta): comisión 12,10; ads 12,10; contribución 35,80; BE 39,587%', () => {
  const u = E.unit(flat10);
  near(u.referral, 12.1); near(u.ads, 12.1); near(u.beforeAds, 47.9); near(u.contribution, 35.8); near(u.contributionPct, 0.358); near(u.breakEvenAcos, 47.9 / 121);
});
t('base neta: ads 10; contribución 37,90; BE 47,9%', () => {
  const u = E.unit({ ...flat10, adsBasis: 'net' });
  near(u.ads, 10); near(u.contribution, 37.9); near(u.breakEvenAcos, 0.479);
});
t('coherencia: con ACoS = ACoS de equilibrio la contribución es 0', () => {
  ['gross', 'net'].forEach((b) => { const be = E.unit({ ...flat10, adsBasis: b }).breakEvenAcos * 100; near(E.unit({ ...flat10, adsBasis: b, acosTarget: be }).contribution, 0, 1e-9); });
});
t('belleza por umbral: 9,99 € → 8 %; 10,01 € → 15 % (discontinuidad)', () => {
  near(E.referralFee(9.99, E.FEE_SCHEDULES.belleza_8_15), 0.7992); near(E.referralFee(10, E.FEE_SCHEDULES.belleza_8_15), 0.8); near(E.referralFee(10.01, E.FEE_SCHEDULES.belleza_8_15), 1.5015);
});
t('comisión mínima: 1,50 € × 15 % = 0,225 → mínimo 0,30', () => near(E.referralFee(1.5, E.FEE_SCHEDULES.generico_15), 0.3));
t('tramos marginales: 150 € → 15 + 4 = 19', () => { near(E.referralFee(150, E.FEE_SCHEDULES.tramos_marginales), 19); near(E.referralFee(100, E.FEE_SCHEDULES.tramos_marginales), 15); near(E.referralFee(50, E.FEE_SCHEDULES.tramos_marginales), 7.5); });
t('devoluciones: 10 % × (3 + 50 % × 30) = 1,80', () => near(E.unit({ ...flat10, returnsPct: 10, returnProcessing: 3, unsellablePct: 50 }).returns, 1.8));
t('FBM: 4,5 + 0,4 + 0,6 = 5,5 y sin almacenaje FBA', () => { const u = E.unit({ ...flat10, fulfilMode: 'FBM', fbmShipping: 4.5, fbmPackaging: 0.4, fbmHandling: 0.6, storageMonthly: 9, storageMonths: 9 }); near(u.fulfil, 5.5); near(u.storage, 0); });
t('almacenaje FBA: 0,15 × 3 = 0,45', () => near(E.unit({ ...flat10, storageMonthly: 0.15, storageMonths: 3 }).storage, 0.45));
t('prep y otros costes restan 1:1', () => { const a = E.unit(flat10).contribution, b = E.unit({ ...flat10, prep: 0.5, otherCosts: 0.25 }).contribution; near(a - b, 0.75); });
t('IVA 0 %: neto = PVP y advertencia', () => { const u = E.unit({ ...flat10, vatPct: 0, price: 100 }); near(u.net, 100); assert.ok(u.warnings.some((w) => w.includes('IVA 0'))); });

t('entradas inválidas NUNCA devuelven resultado (V0.1 daba GO con precio negativo)', () => {
  [{ price: 0 }, { price: -10 }, { price: NaN }, { price: Infinity }, { price: '24' }, { vatPct: -5 }, { vatPct: 100 }, { cost: -1 }, { returnsPct: 101 }, { acosTarget: 100 },
    { minMarginPct: 100 }, { feeSchedule: 'inexistente' }, { fulfilMode: 'XYZ' }, { adsBasis: 'raro' }, { feeSchedule: 'personalizado', customReferralPct: 100 }, { feeSchedule: 'personalizado', customReferralPct: -1 }, { fbaFee: NaN }]
    .forEach((c) => { const u = E.unit({ ...E.DEFAULTS, ...c }); assert.strictEqual(u.valid, false, JSON.stringify(c)); assert.ok(u.errors.length); });
});
t('casos extremos válidos: precio 0,01 y 1e5 no lanzan y dan pérdida/valores finitos', () => {
  const lo = E.unit({ ...E.DEFAULTS, price: 0.01 }); assert.ok(lo.valid && lo.contribution < 0 && isFinite(lo.contributionPct));
  const hi = E.unit({ ...E.DEFAULTS, price: 100000 }); assert.ok(hi.valid && isFinite(hi.contribution));
});
t('coste > neto: pérdida y advertencia', () => { const u = E.unit({ ...E.DEFAULTS, cost: 100 }); assert.ok(u.contribution < 0); assert.ok(u.warnings.some((w) => w.includes('pérdida'))); });

t('precio mínimo (flat): contribución = objetivo exacto', () => {
  const i = { ...flat10, minMarginPct: 20 }; const r = E.minPrice(i); near(E.unit(i, r.exact).contributionPct, 0.2, 1e-9);
  // cálculo manual: g=1/1.21; den = g*0.8 - 0.10 - 0.10 = 0.46116; K=40 → p = 40/0.46116 = 86,7
  near(r.exact, 40 / (0.8 / 1.21 - 0.2), 1e-9);
});
t('precio mínimo comercial es el mínimo céntimo que cumple', () => {
  const i = { ...E.DEFAULTS, minMarginPct: 20 }; const r = E.minPrice(i);
  assert.ok(E.unit(i, r.commercial).contributionPct >= 0.2 - 1e-9, 'el comercial cumple');
  assert.ok(E.unit(i, Math.round((r.commercial - 0.01) * 100) / 100).contributionPct < 0.2, 'un céntimo menos NO cumple');
  assert.ok(r.commercial >= r.exact - 1e-9 && r.commercial - r.exact < 0.0101);
});
t('precio mínimo con comisión por umbral: elige el tramo válido más barato', () => {
  const i = { ...E.DEFAULTS, feeSchedule: 'belleza_8_15', cost: 2, fbaFee: 2, storageMonthly: 0, returnsPct: 0, acosTarget: 10, minMarginPct: 20 };
  const r = E.minPrice(i); assert.ok(r && r.exact <= 10, 'debería caber en el tramo 8 %'); assert.ok(E.unit(i, r.commercial).contributionPct >= 0.2 - 1e-9);
});
t('precio mínimo: ACoS + margen inalcanzables → null', () => { assert.strictEqual(E.minPrice({ ...E.DEFAULTS, acosTarget: 60, minMarginPct: 60 }), null); });
t('precio mínimo: entradas inválidas → null', () => assert.strictEqual(E.minPrice({ ...E.DEFAULTS, cost: -1 }), null));
t('monotonía: subir el coste de producto sube el precio mínimo', () => { const a = E.minPrice({ ...E.DEFAULTS, cost: 5 }).exact, b = E.minPrice({ ...E.DEFAULTS, cost: 8 }).exact; assert.ok(b > a); });
console.log(`\n${n} pruebas del motor económico OK`);
