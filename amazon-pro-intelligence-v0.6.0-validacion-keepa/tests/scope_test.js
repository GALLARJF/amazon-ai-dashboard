// Compatibilidad de contrato V0.2→V0.3 y aislamiento por cuenta/titular (sin mezclar titularidades).
const fs = require('fs'), path = require('path');
global.self = global; const C = require('../js/calc.js'); global.Calc = C; const I = require('../js/integration.js');
const D = require('../js/data.js'); const DD = global.DemoData || D;
const base = { rows: DD.rows, products: DD.products, filters: { product: 'all', period: '30', marketplace: 'all' }, source: 'demo', dossiers: [{ name: 'P', decision: 'REVISAR', blockers: 2, warnings: 1 }], approvals: [], generatedAt: '2026-11-16T00:00:00Z' };
let ok = 0, bad = 0; const t = (n, c) => { c ? ok++ : bad++; console.log((c ? 'OK   ' : 'FAIL ') + n); };
const v2 = I.buildPackage(base), a = I.buildPackage({ ...base, scope: { account_id: 'acct-a', legal_entity: 'Vendedor A S.L.', seller_central_ref: 'SC-A', marketplaces: ['amazon.es'], brand: null } }), b = I.buildPackage({ ...base, scope: { account_id: 'acct-b', legal_entity: 'Vendedor B S.L.', seller_central_ref: 'SC-B', marketplaces: ['amazon.de'], brand: null } });
const ids = (p) => [...p.channel_snapshots, ...p.alerts, ...p.dossiers, ...p.approvals].map((x) => x.id);
t('sin scope: paquete idéntico en forma a V0.2 (version 0.2, sin source.scope)', v2.version === '0.2' && !v2.source.scope);
t('con scope: version 0.3 y source.scope presente', a.version === '0.3' && a.source.scope.account_id === 'acct-a');
t('cuentas distintas → ningún ID compartido (no se mezclan contabilidades)', ids(a).every((x) => !ids(b).includes(x)) && ids(a).every((x) => !ids(v2).includes(x)));
t('IDs deterministas por cuenta (re-exportar no duplica)', JSON.stringify(ids(a)) === JSON.stringify(ids(I.buildPackage({ ...base, scope: a.source.scope }))));
t('module_views referencian solo IDs de la propia cuenta', Object.values(a.module_views).every((m) => Object.values(m).flat().every((x) => ids(a).includes(x))));
t('validate() del contrato acepta paquetes con y sin scope', I.validate(v2).length === 0 && I.validate(a).length === 0 && I.validate(b).length === 0);
fs.writeFileSync(path.join(__dirname, 'paquete_scope_acct-a_DEMO.json'), JSON.stringify(a));
console.log(`${ok} pruebas de ámbito/compatibilidad OK${bad ? ' · ' + bad + ' FALLAN' : ''}`); process.exit(bad ? 1 : 0);
