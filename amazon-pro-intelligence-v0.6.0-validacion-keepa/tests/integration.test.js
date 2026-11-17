const assert = require('assert'); const I = require('../js/integration.js'); const C = require('../js/calc.js');
const fs = require('fs'); const vm = require('vm'); const ctx = { self: {} }; vm.createContext(ctx); vm.runInContext(fs.readFileSync(__dirname + '/../js/data.js', 'utf8'), ctx); const Demo = ctx.self.DemoData;
let n = 0; const t = (name, fn) => { fn(); n++; console.log('OK  ' + name); };
const base = { rows: Demo.rows, products: Demo.products, filters: { period: '30' }, source: 'demo', generatedAt: '2026-11-16T10:00:00Z' };
const P = I.buildPackage(base);
t('paquete válido estructuralmente', () => assert.deepStrictEqual(I.validate(P), []));
t('un snapshot por producto×marketplace (4×4=16)', () => assert.strictEqual(P.channel_snapshots.length, 16));
t('IDs deterministas: mismo input → mismos ids', () => assert.deepStrictEqual(I.buildPackage(base).channel_snapshots.map((x) => x.id), P.channel_snapshots.map((x) => x.id)));
t('re-export en otro instante NO cambia ids ni claves (sin duplicados al hacer upsert)', () => {
  const Q = I.buildPackage({ ...base, generatedAt: '2027-01-01T00:00:00Z' }); const keys = (p) => [...p.channel_snapshots, ...p.alerts].map((x) => x.key + '=' + x.id).sort();
  assert.deepStrictEqual(keys(P), keys(Q));
});
t('upsert simulado: importar dos veces el mismo paquete deja el mismo nº de registros', () => {
  const store = new Map(); [P, I.buildPackage(base)].forEach((p) => p.channel_snapshots.concat(p.alerts).forEach((x) => store.set(x.key, x)));
  assert.strictEqual(store.size, P.channel_snapshots.length + P.alerts.length);
});
t('ids únicos y claves únicas', () => { const all = [...P.channel_snapshots, ...P.alerts]; assert.strictEqual(new Set(all.map((x) => x.id)).size, all.length); assert.strictEqual(new Set(all.map((x) => x.key)).size, all.length); });
t('DEMO → ingest_allowed=false; CSV → true con api_verified=false', () => {
  assert.strictEqual(P.ingest_allowed, false); assert.strictEqual(P.source.dataSource, 'DEMO');
  const csv = I.buildPackage({ ...base, source: 'csv' }); assert.strictEqual(csv.ingest_allowed, true); assert.strictEqual(csv.source.api_verified, false);
});
t('validación rechaza DEMO con ingest_allowed=true', () => { const bad = { ...P, ingest_allowed: true }; assert.ok(I.validate(bad).some((e) => e.includes('DEMO'))); });
t('validación detecta ids inválidos, duplicados, NaN y vistas colgantes', () => {
  const bad = JSON.parse(JSON.stringify(P)); bad.channel_snapshots[0].id = 'x'; bad.channel_snapshots[1].id = bad.channel_snapshots[2].id; bad.channel_snapshots[3].margin_eur = NaN; bad.module_views.finanzas.snapshots.push('amz-snap-0000000000000000');
  const e = I.validate(bad); assert.ok(e.some((x) => x.includes('id inválido')) && e.some((x) => x.includes('duplicado')) && e.some((x) => x.includes('no finito')) && e.some((x) => x.includes('inexistente')));
});
t('las vistas por módulo referencian ids, no copian registros', () => { Object.values(P.module_views).forEach((v) => Object.values(v).flat().forEach((id) => assert.strictEqual(typeof id, 'string'))); assert.ok(P.module_views['ventas.canal_amazon'].snapshots.length === 16); });
t('alertas por módulo coherentes con la regla', () => { P.alerts.forEach((a) => { assert.ok(['ventas', 'marketing', 'finanzas', 'logistica'].includes(a.module)); }); assert.ok(P.alerts.length > 0); });
t('alerta estable: misma regla+ámbito+fecha → mismo id', () => { const a1 = I.alerts(Demo.rows, { period: '30' }, Demo.products), a2 = I.alerts(Demo.rows, { period: '30' }, Demo.products); assert.deepStrictEqual(a1.map((x) => x.id), a2.map((x) => x.id)); });
t('importes del snapshot cuadran con el agregado', () => {
  const s = P.channel_snapshots.find((x) => x.sku === 'DEMO-A' && x.marketplace === 'ES'); const a = C.aggregate(C.filterRows(Demo.rows, { product: 'DEMO-A', marketplace: 'ES', period: '30' }));
  assert.ok(Math.abs(s.sales_net_eur - a.sales) < 0.01 && s.units === a.units && Math.abs(s.margin_eur - a.margin) < 0.01);
});
t('aprobaciones y expedientes se exportan sin duplicar por clave de negocio', () => {
  const p = I.buildPackage({ ...base, approvals: [{ type: 'Campaña PPC', title: 'X', status: 'pendiente', source: 'PPC' }, { type: 'Campaña PPC', title: 'X', status: 'aprobada', source: 'PPC' }], dossiers: [{ name: 'Prod', decision: 'REVISAR', blockers: 3, warnings: 1 }, { name: ' prod ', decision: 'GO', blockers: 0, warnings: 0 }] });
  assert.strictEqual(p.approvals.length, 1); assert.strictEqual(p.dossiers.length, 1);
});
t('paquete serializable a JSON sin pérdidas', () => assert.deepStrictEqual(JSON.parse(JSON.stringify(P)), P));
t('sin datos → paquete vacío válido (no lanza)', () => { const p = I.buildPackage({ rows: [], products: [], filters: { period: '30' }, source: 'csv', generatedAt: 'x' }); assert.strictEqual(p.channel_snapshots.length, 0); });
console.log(`\n${n} pruebas de integración OK`);
