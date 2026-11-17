const assert = require('assert'); const C = require('../js/calc.js');
let n = 0; const t = (name, fn) => { fn(); n++; console.log('OK  ' + name); };
const rows = [
 {date:'2026-11-14',product:'A',marketplace:'ES',units:2,sales:100,cogs:20,fees:30,ad_spend:10,ad_sales:50,price:10,competitor_price:11,bsr:100,stock:50},
 {date:'2026-11-15',product:'A',marketplace:'ES',units:3,sales:200,cogs:40,fees:60,ad_spend:20,ad_sales:80,price:10,competitor_price:11,bsr:90,stock:40},
 {date:'2026-11-15',product:'B',marketplace:'DE',units:1,sales:50,cogs:10,fees:10,ad_spend:0,ad_sales:0,price:5,competitor_price:5,bsr:300,stock:7},
 {date:'2026-10-01',product:'A',marketplace:'ES',units:9,sales:999,cogs:0,fees:0,ad_spend:0,ad_sales:0,price:1,competitor_price:1,bsr:1,stock:1},
];
t('filtro periodo/producto/marketplace', () => {
  assert.strictEqual(C.filterRows(rows,{product:'all',period:'7',marketplace:'all'}).length, 3);
  assert.strictEqual(C.filterRows(rows,{product:'A',period:'7',marketplace:'all'}).length, 2);
  assert.strictEqual(C.filterRows(rows,{product:'all',period:'7',marketplace:'DE'}).length, 1);
  assert.strictEqual(C.filterRows(rows,{product:'all',period:'90',marketplace:'all'}).length, 4);
});
t('agregados', () => {
  const a = C.aggregate(rows.slice(0,3));
  assert.strictEqual(a.sales, 350); assert.strictEqual(a.margin, 350-70-100-30);
  assert.ok(Math.abs(a.acos - 30/130) < 1e-9); assert.ok(Math.abs(a.tacos - 30/350) < 1e-9);
  assert.strictEqual(a.stock, 40 + 7); // último día por producto|mkt
});
t('periodo anterior', () => { assert.strictEqual(C.filterRows(rows,{product:'all',period:'30',marketplace:'all'},1).length, 1); assert.strictEqual(C.filterRows(rows,{product:'all',period:'7',marketplace:'all'},1).length, 0); });
t('serie diaria', () => { const s = C.dailySeries(rows.slice(0,3)); assert.strictEqual(s.length,2); assert.strictEqual(s[1].sales,250); });
t('mediana y percentiles', () => { assert.strictEqual(C.median([1,3,2]),2); assert.strictEqual(C.median([1,2,3,4]),2.5); assert.strictEqual(C.percentile([1,2,3,4,5],0.5),3); });
t('CSV válido', () => {
  const r = C.parseCSV(C.CSV_COLS.join(',')+'\n2026-11-01,X,ES,1,2,3,4,5,6,7,8,9,10\n'); assert.strictEqual(r.rows.length,1); assert.strictEqual(r.errors.length,0);
});
t('CSV inválido', () => {
  assert.ok(C.parseCSV('a,b\n1,2').errors[0].includes('Faltan columnas'));
  const r = C.parseCSV(C.CSV_COLS.join(',')+'\n2026-11-01,X,ES,uno,2,3,4,5,6,7,8,9,10\n'); assert.strictEqual(r.rows.length,0); assert.ok(r.errors[0].includes('units'));
});
t('costes opcionales (devoluciones, almacenaje, otros) restan del margen', () => {
  const r = rows.slice(0, 1).map((x) => ({ ...x, returns_cost: 5, storage_fees: 3, other_costs: 2 })); const a = C.aggregate(r);
  assert.strictEqual(a.margin, 100 - 20 - 30 - 5 - 3 - 2 - 10); assert.ok(Math.abs(a.marginBeforeAdsPct - (100 - 20 - 30 - 10) / 100) < 1e-9);
});
t('CSV sin columnas opcionales: advertencia de margen sobrestimado', () => { const r = C.parseCSV(C.CSV_COLS.join(',') + '\n2026-11-01,X,ES,1,2,3,4,5,6,7,8,9,10\n'); assert.ok(r.warnings[0].includes('SOBRESTIMADO')); assert.strictEqual(r.rows[0].returns_cost, 0); });
t('CSV con columnas opcionales: sin advertencia', () => { const r = C.parseCSV(C.CSV_COLS.concat(C.CSV_OPT).join(',') + '\n2026-11-01,X,ES,1,2,3,4,5,6,7,8,9,10,1,2,3\n'); assert.strictEqual(r.warnings.length, 0); assert.strictEqual(r.rows[0].storage_fees, 2); });
t('CSV rechaza valores negativos', () => { const r = C.parseCSV(C.CSV_COLS.join(',') + '\n2026-11-01,X,ES,-1,2,3,4,5,6,7,8,9,10\n'); assert.strictEqual(r.rows.length, 0); assert.ok(r.errors[0].includes('negativo')); });
console.log(`\n${n} grupos de pruebas OK`);
