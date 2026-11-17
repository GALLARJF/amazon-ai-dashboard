/* Contrato de integración con Executive Neon (V0.2). Genera un PAQUETE JSON de solo lectura:
   - IDs deterministas (misma clave de negocio → mismo id): re-exportar nunca duplica; el consumidor hace upsert por `key`.
   - Los módulos (Ventas>Canal Amazon, Marketing, Finanzas, Logística) reciben VISTAS que referencian ids, no copias.
   - Un paquete DEMO lleva ingest_allowed:false y NO debe ingestarse en la plataforma principal.
   Esta app no escribe en la plataforma principal: solo produce el paquete. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./calc.js'));
  else root.Integration = factory(root.Calc);
})(typeof self !== 'undefined' ? self : this, function (C) {
  const SCHEMA = 'executive-neon/amazon-channel@1';
  function hash(str) { // FNV-1a ×2 → 16 hex (determinista, sin dependencias)
    let a = 0x811c9dc5, b = 0x01000193 ^ 0xdeadbeef;
    for (let i = 0; i < str.length; i++) { a = Math.imul(a ^ str.charCodeAt(i), 0x01000193) >>> 0; b = Math.imul(b ^ str.charCodeAt(i), 0x85ebca6b) >>> 0; b = (b ^ (b >>> 13)) >>> 0; }
    return a.toString(16).padStart(8, '0') + b.toString(16).padStart(8, '0');
  }
  const mkId = (kind, key) => `amz-${kind}-${hash(key)}`;
  const round = (x, d = 4) => (isFinite(x) ? Math.round(x * 10 ** d) / 10 ** d : 0);

  function snapshots(rows, filters) {
    const period = +filters.period || 30, to = C.endDate(rows), out = [];
    const cur = C.filterRows(rows, { product: 'all', marketplace: 'all', period: String(period) });
    const byPM = {};
    cur.forEach((r) => { const k = r.product + '|' + r.marketplace; (byPM[k] = byPM[k] || []).push(r); });
    Object.keys(byPM).sort().forEach((k) => {
      const [sku, mk] = k.split('|'), a = C.aggregate(byPM[k]), key = `amazon|${mk}|${sku}|${to}|${period}d`;
      out.push({ id: mkId('snap', key), key, entity: 'sales_channel_snapshot', channel: 'amazon', marketplace: mk, sku, period_to: to, period_days: period,
        sales_net_eur: round(a.sales, 2), units: a.units, margin_eur: round(a.margin, 2), margin_pct: round(a.marginPct), ad_spend_eur: round(a.adSpend, 2),
        ad_sales_eur: round(a.adSales, 2), acos: round(a.acos), tacos: round(a.tacos), stock_units: a.stock });
    });
    return { list: out, to, period };
  }

  /* Alertas deterministas a partir de los datos (misma regla+ámbito+fecha → mismo id). */
  function alerts(rows, filters, products) {
    const period = String(+filters.period || 30), to = C.endDate(rows), out = [];
    const cur = C.filterRows(rows, { product: 'all', marketplace: 'all', period }), by = C.groupBy(cur, 'product');
    const nm = (id) => (products.find((p) => p.id === id) || {}).name || id;
    const push = (module, rule, scope, severity, title, detail) => { const key = `alert|${module}|${rule}|${scope}|${to}`; out.push({ id: mkId('alert', key), key, entity: 'alert', module, rule, scope, severity, title, detail, period_to: to }); };
    Object.keys(by).sort().forEach((id) => {
      const rs = by[id], a = C.aggregate(rs), days = new Set(rs.map((r) => r.date)).size, daily = C.safeDiv(a.units, days);
      if (a.marginPct < 0.1) push('finanzas', 'margen_bajo', id, a.marginPct < 0 ? 'critica' : 'alta', `${nm(id)}: margen ${(a.marginPct * 100).toFixed(1)} %`, 'Margen de contribución inferior al 10 % en el periodo.');
      if (a.acos > a.marginBeforeAdsPct) push('marketing', 'acos_sobre_equilibrio', id, 'alta', `${nm(id)}: ACoS ${(a.acos * 100).toFixed(1)} % > equilibrio ${(a.marginBeforeAdsPct * 100).toFixed(1)} %`, 'La publicidad destruye margen.');
      if (daily > 0 && a.stock / daily < 30) push('logistica', 'cobertura_baja', id, 'alta', `${nm(id)}: cobertura ${(a.stock / daily).toFixed(0)} días`, 'Cobertura inferior a 30 días (plazo de reposición supuesto).');
      const my = C.safeDiv(rs.reduce((s, r) => s + r.price, 0), rs.length), co = C.safeDiv(rs.reduce((s, r) => s + r.competitor_price, 0), rs.length);
      if (co && my / co > 1.1) push('ventas', 'precio_sobre_competencia', id, 'media', `${nm(id)}: precio ${((my / co - 1) * 100).toFixed(1)} % sobre competencia`, 'Precio medio >10 % sobre el competidor de referencia.');
    });
    return out;
  }

  function buildPackage(o) {
    const snap = snapshots(o.rows, o.filters), al = alerts(o.rows, o.filters, o.products || []);
    const dossiers = (o.dossiers || []).map((d) => { const key = `dossier|${(d.name || '').trim().toLowerCase()}`; return { id: mkId('dossier', key), key, entity: 'launch_dossier', name: d.name, decision: d.decision, blockers: d.blockers, warnings: d.warnings }; });
    const approvals = (o.approvals || []).map((a) => { const key = `approval|${a.type}|${a.title}|${a.source || ''}`; return { id: mkId('approval', key), key, entity: 'approval_request', type: a.type, title: a.title, status: a.status, source: a.source || '' }; });
    const ids = (arr) => arr.map((x) => x.id);
    const dedupe = (arr) => { const m = new Map(); arr.forEach((x) => m.set(x.key, x)); return [...m.values()]; };
    const S = dedupe(snap.list), A = dedupe(al), D = dedupe(dossiers), P = dedupe(approvals);
    if (o.scope) { // V0.3: aislamiento por cuenta/titular — las claves llevan el prefijo de la cuenta para no mezclar contabilidades ni titularidades
      const pfx = 'acct:' + o.scope.account_id + '|', rk = (arr) => arr.forEach((x) => { const kind = x.id.split('-')[1]; x.key = pfx + x.key; x.id = mkId(kind, x.key); });
      [S, A, D, P].forEach(rk);
    }
    return {
      schema: SCHEMA, version: o.scope ? '0.3' : '0.2', generatedAt: o.generatedAt || new Date().toISOString(),
      source: { system: 'amazon-pro-intelligence', dataSource: o.source === 'demo' ? 'DEMO' : 'CSV_IMPORTADO', api_verified: false, ...(o.scope ? { scope: o.scope } : {}) },
      ingest_allowed: o.source !== 'demo', period: { to: snap.to, days: snap.period },
      channel_snapshots: S, alerts: A, dossiers: D, approvals: P,
      module_views: { // solo referencias por id (sin duplicar registros)
        'ventas.canal_amazon': { snapshots: ids(S), alerts: ids(A.filter((x) => x.module === 'ventas')), dossiers: ids(D) },
        marketing: { snapshots: ids(S), alerts: ids(A.filter((x) => x.module === 'marketing')) },
        finanzas: { snapshots: ids(S), alerts: ids(A.filter((x) => x.module === 'finanzas')) },
        logistica: { snapshots: ids(S), alerts: ids(A.filter((x) => x.module === 'logistica')) },
      },
      upsert_rule: 'El consumidor debe hacer upsert por `key`. `id` es estable. No ingerir si ingest_allowed=false.',
    };
  }

  /* Validación estructural mínima (el esquema JSON formal está en schemas/amazon-channel.schema.json). */
  function validate(p) {
    const e = [], seen = new Set();
    if (p.schema !== SCHEMA) e.push('schema incorrecto');
    ['channel_snapshots', 'alerts', 'dossiers', 'approvals'].forEach((k) => {
      if (!Array.isArray(p[k])) { e.push(k + ' debe ser array'); return; }
      p[k].forEach((x) => {
        if (!/^amz-[a-z]+-[0-9a-f]{16}$/.test(x.id || '')) e.push(`${k}: id inválido ${x.id}`);
        if (!x.key) e.push(`${k}: falta key`);
        if (seen.has(x.id)) e.push('id duplicado ' + x.id); seen.add(x.id);
        Object.entries(x).forEach(([f, v]) => { if (typeof v === 'number' && !isFinite(v)) e.push(`${k}.${f} no finito`); });
      });
    });
    (p.alerts || []).forEach((a) => { if (!['critica', 'alta', 'media', 'baja'].includes(a.severity)) e.push('severidad inválida'); if (!['ventas', 'marketing', 'finanzas', 'logistica'].includes(a.module)) e.push('módulo inválido'); });
    if (typeof p.ingest_allowed !== 'boolean') e.push('ingest_allowed requerido');
    if (p.source && p.source.dataSource === 'DEMO' && p.ingest_allowed) e.push('un paquete DEMO no puede tener ingest_allowed=true');
    const all = new Set(seen); Object.values(p.module_views || {}).forEach((v) => Object.values(v).flat().forEach((id) => { if (!all.has(id)) e.push('vista referencia id inexistente ' + id); }));
    return e;
  }
  return { SCHEMA, hash, mkId, snapshots, alerts, buildPackage, validate };
});
