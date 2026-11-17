// Evidencia de auditoría: mismos casos contra el código REAL de V0.1 y contra V0.2. Uso: node tests/evidence.js <ruta V0.1>
const path = require('path'); const V1 = require(path.resolve(process.argv[2] || '../amazon-pro-intelligence-v0.1', 'js/calc.js')); const E = require('../js/economics.js'); const D = require('../js/dossier.js');
const base1 = { ...V1.PL_DEFAULTS, price: 24.9, cost: 5.2, fulfil: 4.1, competitors: [22, 24, 26] };
const cases = [['precio negativo (-10)', { price: -10 }], ['IVA negativo (-50 %)', { vatPct: -50 }], ['precio NaN', { price: NaN }], ['comisión 150 %', { referralPct: 150 }], ['devoluciones 100 %', { returnsPct: 100 }],
  ['3 competidores = el mismo dato', { competitors: [24, 24, 24], cost: 4, fulfil: 3.5 }], ['solo margen + 3 precios (cost 4)', { cost: 4, fulfil: 3.5, competitors: [27, 29, 31], price: 29.9 }]];
console.log('caso'.padEnd(36), 'V0.1'.padEnd(26), 'V0.2 (motor económico)');
cases.forEach(([n, o]) => {
  const r1 = V1.evaluatePrelaunch({ ...base1, ...o }); const o2 = { ...E.DEFAULTS, price: o.price !== undefined ? o.price : 24.9, vatPct: o.vatPct !== undefined ? o.vatPct : 21, returnsPct: o.returnsPct !== undefined ? o.returnsPct : 4, cost: o.cost || 5.2 };
  if (o.referralPct) { o2.feeSchedule = 'personalizado'; o2.customReferralPct = o.referralPct; }
  const u = E.unit(o2); const v2 = u.valid ? `válido; contribución ${(u.contributionPct * 100).toFixed(1)} %` : 'RECHAZADO: ' + u.errors[0];
  console.log(n.padEnd(36), (r1.decision + ' (margen ' + (r1.unit.marginPct * 100).toFixed(1) + '%)').padEnd(26), v2);
});
const T = new Date().toISOString().slice(0, 10), d = D.example('economia', T);
console.log('\nExpediente con margen positivo pero SIN regulatorio/contenido/stock/demanda:'); console.log('  V0.1 → GO (solo exigía margen, mediana y 3 precios)'); const r = D.evaluate(d, T); console.log('  V0.2 →', r.decision, `(${r.counts.block} bloqueos)`);
