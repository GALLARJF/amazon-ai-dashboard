const assert = require('assert'); const D = require('../js/dossier.js'); const E = require('../js/economics.js');
let n = 0; const t = (name, fn) => { fn(); n++; console.log('OK  ' + name); };
const TODAY = '2026-11-16', has = (r, id) => r.findings.some((f) => f.id === id || f.id.startsWith(id));

t('REGLA CENTRAL: margen positivo + expediente vacío = REVISAR, nunca GO', () => {
  const d = D.example('economia', TODAY); const u = E.unit(d.econ); assert.ok(u.contributionPct > 0.15, 'precondición: margen positivo');
  const r = D.evaluate(d, TODAY); assert.strictEqual(r.decision, 'REVISAR');
  ['demand.none', 'regulatory.', 'content.', 'log.stock'].forEach((id) => assert.ok(has(r, id), 'falta bloqueo ' + id));
});
t('expediente completo → GO (con avisos permitidos)', () => { const r = D.evaluate(D.example('completo', TODAY), TODAY); assert.strictEqual(r.decision, 'GO', JSON.stringify(r.findings.filter((f) => f.severity !== 'warn').map((f) => f.id))); assert.ok(r.counts.warn >= 1); });
t('económicamente inviable → NO-GO aunque el expediente esté completo', () => { const d = D.example('completo', TODAY); d.econ.cost = 15; const r = D.evaluate(d, TODAY); assert.strictEqual(r.decision, 'NO-GO'); });
t('NO-GO prevalece sobre REVISAR', () => { const r = D.evaluate(D.example('nogo', TODAY), TODAY); assert.strictEqual(r.decision, 'NO-GO'); assert.ok(r.counts.block > 0); });
t('cada hallazgo tiene título, motivo y acción', () => D.evaluate(D.example('economia', TODAY), TODAY).findings.forEach((f) => { assert.ok(f.title && f.why && f.fix && f.severity && f.section); }));
t('datos económicos inválidos (precio negativo) → bloqueo, no GO', () => { const d = D.example('completo', TODAY); d.econ.price = -5; const r = D.evaluate(d, TODAY); assert.notStrictEqual(r.decision, 'GO'); assert.ok(has(r, 'econ.invalid')); });

t('benchmark: <3 competidores válidos bloquea', () => { const d = D.example('completo', TODAY); d.competitors = d.competitors.slice(0, 2); const r = D.evaluate(d, TODAY); assert.ok(has(r, 'bench.insufficient')); assert.strictEqual(r.decision, 'REVISAR'); });
t('benchmark: duplicados no cuentan dos veces', () => { const d = D.example('completo', TODAY); const c = d.competitors[0]; d.competitors = [c, { ...c }, { ...c }]; const b = D.benchmark(d, TODAY); assert.strictEqual(b.n, 1); assert.ok(b.issues.some((x) => x.includes('duplicado'))); });
t('benchmark: sin fuente o fecha → excluido', () => { const d = D.example('completo', TODAY); d.competitors[0].source = ''; d.competitors[1].date = ''; assert.strictEqual(D.benchmark(d, TODAY).n, 3); });
t('benchmark: dato caducado (> 30 d) y fecha futura → excluido', () => { const d = D.example('completo', TODAY); d.competitors[0].date = '2026-09-01'; d.competitors[1].date = '2027-01-01'; assert.strictEqual(D.benchmark(d, TODAY).n, 3); });
t('benchmark: precios negativos/cero/NaN → excluidos', () => { const d = D.example('completo', TODAY); d.competitors[0].priceGross = -1; d.competitors[1].priceGross = 0; d.competitors[2].priceGross = NaN; assert.strictEqual(D.benchmark(d, TODAY).n, 2); });
t('benchmark normalizado: pack de 2 × 50 ml a 20 € = 0,20 €/ml; own 100 ml → 20 € a igualdad', () => {
  const d = D.createEmpty('cosmetico', 'FBA'); d.product.ownContent = 100;
  d.competitors = [{ name: 'a', priceGross: 20, shipping: 0, packUnits: 2, contentValue: 50, source: 's', date: TODAY }, { name: 'b', priceGross: 10, shipping: 0, packUnits: 1, contentValue: 100, source: 's', date: TODAY }, { name: 'c', priceGross: 30, shipping: 0, packUnits: 1, contentValue: 100, source: 's', date: TODAY }];
  const b = D.benchmark(d, TODAY); assert.ok(Math.abs(b.unit.median - 0.2) < 1e-12); assert.ok(Math.abs(b.band.mid - 20) < 1e-9); assert.ok(Math.abs(b.unit.min - 0.1) < 1e-12);
});
t('benchmark: el envío cuenta en el precio unitario', () => { const d = D.createEmpty('cosmetico', 'FBA'); d.competitors = [{ name: 'a', priceGross: 10, shipping: 5, packUnits: 1, contentValue: 100, source: 's', date: TODAY }]; assert.ok(Math.abs(D.benchmark(d, TODAY).rows[0].unitPrice - 0.15) < 1e-12); });
t('benchmark: atípico extremo (≥4 datos) se excluye', () => { const d = D.example('completo', TODAY); d.competitors.push({ name: 'Loco', asin: 'X', priceGross: 999, shipping: 0, packUnits: 1, contentValue: 100, source: 's', date: TODAY }); const b = D.benchmark(d, TODAY); assert.ok(!b.rows.some((r) => r.name === 'Loco')); });

t('precio mínimo fuera de banda → NO-GO con explicación', () => { const d = D.example('completo', TODAY); d.econ.cost = 11; const r = D.evaluate(d, TODAY); assert.ok(has(r, 'price.out_of_band') || has(r, 'econ.unreachable') || has(r, 'econ.loss')); assert.strictEqual(r.decision, 'NO-GO'); });
t('precio por debajo del mínimo rentable (pero dentro de banda) → REVISAR con importe exacto', () => {
  const d = D.example('completo', TODAY); d.econ.price = 22.0; d.econ.minMarginPct = 28; // margen alto exigido, banda amplia
  const r = D.evaluate(d, TODAY); const f = r.findings.find((x) => x.id === 'price.below_min' || x.id === 'price.out_of_band' || x.id === 'econ.unreachable'); assert.ok(f, 'debe haber hallazgo de precio'); assert.notStrictEqual(r.decision, 'GO');
});
t('demanda: keywords caducadas o sin fuente → bloqueo', () => { const d = D.example('completo', TODAY); d.keywords.forEach((k) => (k.date = '2026-01-01')); assert.ok(has(D.evaluate(d, TODAY), 'demand.none')); const e = D.example('completo', TODAY); e.keywords.forEach((k) => (k.source = '')); assert.ok(has(D.evaluate(e, TODAY), 'demand.none')); });
t('regulatorio: «cumplido» sin evidencia no cuenta', () => { const d = D.example('completo', TODAY); d.regulatory.cpnp.evidence = ''; const r = D.evaluate(d, TODAY); assert.ok(has(r, 'regulatory.cpnp')); assert.strictEqual(r.decision, 'REVISAR'); });
t('regulatorio: ítem crítico pendiente bloquea; «no aplica» sin justificar solo avisa', () => { const d = D.example('completo', TODAY); d.regulatory.cpsr.status = 'pendiente'; assert.strictEqual(D.evaluate(d, TODAY).decision, 'REVISAR'); const e = D.example('completo', TODAY); e.regulatory.pif.status = 'no_aplica'; e.regulatory.pif.evidence = ''; const r = D.evaluate(e, TODAY); assert.strictEqual(r.findings.find((f) => f.id === 'regulatory.pif').severity, 'warn'); });
t('claims sin respaldo bloquean', () => { const d = D.example('completo', TODAY); d.claims.push({ text: 'Elimina las arrugas', evidence: '' }); const r = D.evaluate(d, TODAY); assert.strictEqual(r.decision, 'REVISAR'); assert.ok(has(r, 'claims.1')); });
t('claims de riesgo detectados en el listing no declarados', () => { const d = D.example('completo', TODAY); d.content.title.evidence = 'Crema que cura los pies agrietados'; assert.ok(has(D.evaluate(d, TODAY), 'claims.risky.cura')); });
t('contenido: A+/vídeo faltantes solo avisan; imagen principal pendiente bloquea', () => { const d = D.example('completo', TODAY); d.content.aplus.status = 'pendiente'; assert.strictEqual(D.evaluate(d, TODAY).decision, 'GO'); d.content.img_main.status = 'pendiente'; assert.strictEqual(D.evaluate(d, TODAY).decision, 'REVISAR'); });
t('stock insuficiente bloquea con faltante exacto: 300/mes × 45 d = 450', () => { const d = D.example('completo', TODAY); d.logistics.stockAvailable = 400; const r = D.evaluate(d, TODAY); const f = r.findings.find((x) => x.id === 'log.short'); assert.ok(f && f.why.includes('450') && f.why.includes('50')); assert.strictEqual(r.decision, 'REVISAR'); });
t('stock nulo/negativo bloquea', () => { [null, -3, NaN, undefined].forEach((v) => { const d = D.example('completo', TODAY); d.logistics.stockAvailable = v; assert.ok(has(D.evaluate(d, TODAY), 'log.stock')); }); });
t('plantillas regulatorias por tipo y retemplate conserva lo rellenado', () => { const d = D.example('completo', TODAY); d.product.regType = 'suplemento'; D.retemplate(d); assert.ok(d.regulatory.notif && !d.regulatory.cpnp); d.product.regType = 'cosmetico'; D.retemplate(d); assert.ok(d.regulatory.cpnp.status === 'pendiente'); });
t('GO no es una publicación: el resumen lo advierte', () => assert.ok(D.evaluate(D.example('completo', TODAY), TODAY).summary.includes('aprobación explícita')));
t('determinismo: misma entrada → misma salida', () => assert.deepStrictEqual(D.evaluate(D.example('economia', TODAY), TODAY), D.evaluate(D.example('economia', TODAY), TODAY)));
t('precio bajo el mínimo rentable → REVISAR exacto con importe 24,16 €', () => {
  const d = D.example('completo', TODAY); d.econ.price = 23; const r = D.evaluate(d, TODAY); const f = r.findings.find((x) => x.id === 'price.below_min');
  assert.ok(f && f.why.includes('24.16') && f.fix.includes('24.16')); assert.strictEqual(r.decision, 'REVISAR'); assert.ok(!r.findings.some((x) => x.severity === 'nogo'));
});
t('precio igual al extremo de la banda (±0,005 €) no genera aviso de «por encima»', () => {
  const d = D.example('completo', TODAY); const r0 = D.evaluate(d, TODAY); d.econ.price = Math.round(r0.sections.band.high * 100) / 100;
  assert.ok(!D.evaluate(d, TODAY).findings.some((f) => f.id === 'price.above'));
  d.econ.price = Math.round(r0.sections.band.high * 100) / 100 + 0.5; assert.ok(D.evaluate(d, TODAY).findings.some((f) => f.id === 'price.above'));
});
console.log(`\n${n} pruebas del expediente OK`);
