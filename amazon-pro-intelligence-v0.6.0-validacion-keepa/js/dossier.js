/* Expediente Pre-Launch V0.2 (puro). Decide GO / REVISAR / NO-GO con bloqueos explicados.
   Regla central: un margen positivo NO basta. GO exige economía viable + benchmark vigente + demanda con fuente/fecha
   + regulatorio y claims documentados + contenido mínimo + stock/logística. No publica nada: solo evalúa. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./economics.js'));
  else root.Dossier = factory(root.Econ);
})(typeof self !== 'undefined' ? self : this, function (Econ) {
  const MAX_COMP_AGE = 30, MAX_KW_AGE = 60, MIN_COMP = 3, MIN_KW = 5;
  const isDate = (s) => /^\d{4}-\d{2}-\d{2}$/.test(s || '') && !isNaN(Date.parse(s));
  const age = (d, today) => Math.round((Date.parse(today) - Date.parse(d)) / 864e5);
  const num = (x) => typeof x === 'number' && isFinite(x);
  const pctl = (a, p) => { const s = [...a].sort((x, y) => x - y), i = (s.length - 1) * p, lo = Math.floor(i), hi = Math.ceil(i); return s[lo] + (s[hi] - s[lo]) * (i - lo); };

  /* Plantillas orientativas: NO sustituyen asesoramiento regulatorio. */
  const REG = {
    cosmetico: [
      ['rp', 'Persona responsable en la UE designada (Reg. CE 1223/2009)', true], ['cpnp', 'Notificación en el portal CPNP', true],
      ['cpsr', 'Informe de seguridad del producto cosmético (CPSR) firmado por evaluador cualificado', true], ['etiq', 'Etiquetado conforme (INCI, lote, PAO, responsable, contenido)', true],
      ['pif', 'Expediente de información del producto (PIF) disponible', true], ['amz', 'Cumplimiento de políticas/restricciones de Amazon para la categoría', true],
    ],
    suplemento: [
      ['notif', 'Notificación de puesta en el mercado de complementos alimenticios (AESAN/autoridad competente)', true], ['etiq', 'Etiquetado conforme (RD 1487/2009 y Reg. UE 1169/2011)', true],
      ['claims', 'Solo declaraciones de salud autorizadas (Reg. CE 1924/2006)', true], ['nf', 'Ingredientes revisados frente a nuevos alimentos (Reg. UE 2015/2283)', true],
      ['spec', 'Especificaciones y análisis de lote del producto', true], ['amz', 'Cumplimiento de políticas/restricciones de Amazon para la categoría', true],
    ],
    otro: [
      ['gpsr', 'Persona responsable y etiquetado conforme (GPSR, Reg. UE 2023/988)', true], ['ce', 'Marcado CE / declaración de conformidad si aplica', false],
      ['reach', 'REACH / RoHS / otras restricciones de sustancias si aplica', false], ['amz', 'Cumplimiento de políticas/restricciones de Amazon para la categoría', true],
    ],
  };
  const CONTENT = [
    ['img_main', 'Imagen principal conforme (fondo blanco, resolución mínima de Amazon)', true], ['title', 'Título redactado', true], ['bullets', 'Bullets redactados (5)', true],
    ['gallery', 'Galería: ≥ 6 imágenes (uso, escala, packaging, infografías)', false], ['aplus', 'Contenido A+ preparado', false], ['video', 'Vídeo de producto', false],
    ['backend', 'Términos de búsqueda (backend) definidos', false],
  ];
  const LOGI = {
    FBA: [['dims', 'Dimensiones y peso verificados (determinan la tarifa FBA)', true], ['fnsku', 'Etiquetado FNSKU / preparación FBA planificado', true], ['inbound', 'Envío de entrada a FBA planificado', true]],
    FBM: [['dims', 'Dimensiones y peso verificados (determinan el envío)', true], ['carrier', 'Transportista y plazo de entrega definidos', true], ['returns', 'Gestión de devoluciones definida', true]],
  };
  const RISKY = ['cura', 'curar', 'trata', 'tratamiento', 'previene', 'elimina', 'clínicamente probado', 'dermatológicamente', 'sana', 'regenera', 'antiinflamatorio', 'adelgaz', 'detox', 'milagro', '100% natural', 'sin efectos secundarios', 'aprobado por'];

  const mkItems = (list) => Object.fromEntries(list.map(([id, label, critical]) => [id, { label, critical, status: 'pendiente', evidence: '', date: '' }]));

  function createEmpty(type, mode) {
    return {
      product: { name: '', regType: type || 'cosmetico', ownPackUnits: 1, ownContent: 100, contentUnit: 'ml' },
      econ: { ...Econ.DEFAULTS }, competitors: [], keywords: [], claims: [],
      regulatory: mkItems(REG[type || 'cosmetico']), content: mkItems(CONTENT),
      logistics: { mode: mode || 'FBA', stockAvailable: null, leadTimeDays: null, forecastUnitsMonth: null, coverTargetDays: 45, items: mkItems(LOGI[mode || 'FBA']) },
    };
  }
  function retemplate(d) { // al cambiar tipo regulatorio o modo logístico, conserva lo ya rellenado
    const reg = mkItems(REG[d.product.regType]); Object.keys(reg).forEach((k) => d.regulatory[k] && (reg[k] = d.regulatory[k])); d.regulatory = reg;
    const lg = mkItems(LOGI[d.logistics.mode]); Object.keys(lg).forEach((k) => d.logistics.items[k] && (lg[k] = d.logistics.items[k])); d.logistics.items = lg; return d;
  }

  function evalChecklist(items, section, F, labelPrefix, warnOnly) {
    Object.entries(items).forEach(([id, it]) => {
      const sev = it.critical && !warnOnly ? 'block' : 'warn';
      if (it.status === 'pendiente') F.push({ id: `${section}.${id}`, section, severity: sev, title: `${labelPrefix}: ${it.label}`, why: 'Pendiente.', fix: 'Completa el punto o márcalo «No aplica» con justificación.' });
      else if (it.status === 'cumplido' && !(it.evidence || '').trim()) F.push({ id: `${section}.${id}`, section, severity: sev, title: `${labelPrefix}: ${it.label}`, why: 'Marcado como cumplido sin evidencia (referencia, documento o enlace).', fix: 'Indica la referencia de la evidencia.' });
      else if (it.status === 'no_aplica' && !(it.evidence || '').trim()) F.push({ id: `${section}.${id}`, section, severity: 'warn', title: `${labelPrefix}: ${it.label}`, why: '«No aplica» sin justificación.', fix: 'Justifica por qué no aplica.' });
    });
  }

  /* Benchmark normalizado: precio por unidad de contenido (envío incluido). */
  function benchmark(d, today) {
    const own = d.product, rows = [], issues = [], seen = new Set(), perRow = [];
    (d.competitors || []).forEach((c, idx) => {
      const name = (c.name || `#${idx + 1}`).trim(), key = (c.asin || c.name || '').trim().toLowerCase();
      const bad = [];
      if (!num(c.priceGross) || c.priceGross <= 0) bad.push('precio');
      if (!num(c.packUnits) || c.packUnits < 1) bad.push('uds. por pack');
      if (!num(c.contentValue) || c.contentValue <= 0) bad.push('contenido');
      if (c.shipping !== undefined && c.shipping !== null && (!num(c.shipping) || c.shipping < 0)) bad.push('envío');
      if (!(c.source || '').trim()) bad.push('fuente');
      if (!isDate(c.date)) bad.push('fecha');
      if (bad.length) { perRow[idx] = { ok: false, reason: 'falta/inválido: ' + bad.join(', ') }; issues.push(`${name}: dato inválido o ausente (${bad.join(', ')}) → excluido`); return; }
      if (age(c.date, today) < 0) { perRow[idx] = { ok: false, reason: 'fecha futura' }; issues.push(`${name}: fecha futura → excluido`); return; }
      if (age(c.date, today) > MAX_COMP_AGE) { perRow[idx] = { ok: false, reason: `caducado (${age(c.date, today)} d)` }; issues.push(`${name}: dato de hace ${age(c.date, today)} días (> ${MAX_COMP_AGE}) → excluido`); return; }
      if (key && seen.has(key)) { perRow[idx] = { ok: false, reason: 'duplicado' }; issues.push(`${name}: duplicado → excluido`); return; }
      if (key) seen.add(key);
      const up = (c.priceGross + (c.shipping || 0)) / (c.packUnits * c.contentValue); perRow[idx] = { ok: true, unitPrice: up }; rows.push({ ...c, name, _idx: idx, unitPrice: up });
    });
    let valid = rows;
    if (rows.length >= 4) { // descarta atípicos extremos (> 3× o < 1/3 de la mediana)
      const med = pctl(rows.map((r) => r.unitPrice), 0.5);
      valid = rows.filter((r) => { const ok = r.unitPrice <= 3 * med && r.unitPrice >= med / 3; if (!ok) { perRow[r._idx] = { ok: false, reason: 'atípico', unitPrice: r.unitPrice }; issues.push(`${r.name}: precio unitario atípico → excluido`); } return ok; });
    }
    const out = { rows: valid, perRow, issues, n: valid.length, sufficient: valid.length >= MIN_COMP, unitLabel: own.contentUnit || 'ud' };
    if (valid.length) {
      const u = valid.map((r) => r.unitPrice), size = (own.ownPackUnits || 1) * (own.ownContent || 1);
      out.unit = { min: Math.min(...u), p25: pctl(u, 0.25), median: pctl(u, 0.5), p75: pctl(u, 0.75), max: Math.max(...u) };
      out.band = { low: out.unit.p25 * size, mid: out.unit.median * size, high: out.unit.p75 * size, size };
      out.ownUnitPrice = null;
    }
    return out;
  }

  function evaluate(d, today) {
    const F = [], S = {}; today = today || new Date().toISOString().slice(0, 10);
    const add = (f) => F.push(f);

    /* 1. Benchmark */
    const bm = benchmark(d, today); S.benchmark = bm;
    bm.issues.forEach((t) => add({ id: 'bench.issue', section: 'benchmark', severity: 'warn', title: 'Benchmark', why: t, fix: 'Corrige o actualiza el dato del competidor.' }));
    if (!bm.sufficient) add({ id: 'bench.insufficient', section: 'benchmark', severity: 'block', title: `Benchmark insuficiente (${bm.n}/${MIN_COMP})`, why: `Se necesitan ≥ ${MIN_COMP} competidores válidos, distintos, con fuente y fecha ≤ ${MAX_COMP_AGE} días.`, fix: 'Añade competidores comparables con su fuente y fecha de captura.' });

    /* 2. Demanda */
    const kws = (d.keywords || []), okk = [], staleK = [];
    kws.forEach((k) => {
      if (!(k.keyword || '').trim() || !num(k.volume) || k.volume < 0 || !(k.source || '').trim() || !isDate(k.date) || age(k.date, today) < 0) return;
      (age(k.date, today) > MAX_KW_AGE ? staleK : okk).push(k);
    });
    S.demand = { valid: okk.length, stale: staleK.length, totalVolume: okk.reduce((s, k) => s + k.volume, 0) };
    if (okk.length === 0) add({ id: 'demand.none', section: 'demand', severity: 'block', title: 'Sin datos de demanda vigentes', why: `No hay keywords válidas con volumen, fuente y fecha ≤ ${MAX_KW_AGE} días${staleK.length ? ` (${staleK.length} caducadas)` : ''}.`, fix: 'Añade keywords con su volumen, fuente (p. ej. exportación Helium 10) y fecha.' });
    else if (okk.length < MIN_KW) add({ id: 'demand.few', section: 'demand', severity: 'warn', title: `Pocas keywords (${okk.length}/${MIN_KW})`, why: 'La estimación de demanda es frágil.', fix: `Añade hasta ${MIN_KW} o más keywords.` });
    if (okk.length && staleK.length) add({ id: 'demand.stale', section: 'demand', severity: 'warn', title: `${staleK.length} keywords caducadas`, why: `Fecha anterior a ${MAX_KW_AGE} días.`, fix: 'Refresca los datos.' });

    /* 3. Economía y precio */
    const u = Econ.unit(d.econ); S.unit = u;
    if (!u.valid) add({ id: 'econ.invalid', section: 'price', severity: 'block', title: 'Datos económicos inválidos', why: u.errors.join(' · '), fix: 'Corrige los campos señalados.' });
    else {
      const mp = Econ.minPrice(d.econ); S.minPrice = mp; S.band = bm.band || null;
      if (u.contribution <= 0) add({ id: 'econ.loss', section: 'price', severity: 'nogo', title: 'Pierdes dinero por unidad', why: `Contribución tras publicidad: ${u.contribution.toFixed(2)} € por unidad al precio planificado.`, fix: 'Reduce costes o sube el precio.' });
      if (!mp) add({ id: 'econ.unreachable', section: 'price', severity: 'nogo', title: 'Margen mínimo inalcanzable', why: `Con estos costes y un ACoS objetivo del ${d.econ.acosTarget} % no existe precio que alcance ${d.econ.minMarginPct} % de margen.`, fix: 'Reduce costes/ACoS objetivo o acepta un margen menor de forma explícita.' });
      else {
        if (S.band && mp.commercial > S.band.high + 0.005) add({ id: 'price.out_of_band', section: 'price', severity: 'nogo', title: 'Precio mínimo rentable fuera de la banda competitiva', why: `Precio mínimo ${mp.commercial.toFixed(2)} € > extremo alto de la banda (${S.band.high.toFixed(2)} €, P75 normalizado a tu formato).`, fix: 'No es competitivo con estos costes: rediseña coste/formato o diferénciate.' });
        else if (u.price < mp.commercial - 1e-9) add({ id: 'price.below_min', section: 'price', severity: 'block', title: 'Precio planificado por debajo del mínimo rentable', why: `Planificado ${u.price.toFixed(2)} € < mínimo ${mp.commercial.toFixed(2)} € (margen objetivo ${d.econ.minMarginPct} %).`, fix: `Sube el precio a ≥ ${mp.commercial.toFixed(2)} € o reduce costes.` });
      }
      if (S.band) {
        if (u.price > S.band.high + 0.005) add({ id: 'price.above', section: 'price', severity: 'warn', title: 'Precio por encima de la banda competitiva', why: `${u.price.toFixed(2)} € > ${S.band.high.toFixed(2)} €.`, fix: 'Justifica el posicionamiento premium.' });
        else if (u.price < S.band.low - 0.005) add({ id: 'price.below', section: 'price', severity: 'warn', title: 'Precio por debajo de la banda competitiva', why: `${u.price.toFixed(2)} € < ${S.band.low.toFixed(2)} €: posible margen sacrificado.`, fix: 'Valora subir hasta la banda.' });
      }
      if (u.breakEvenAcos * 100 < d.econ.acosTarget + 5) add({ id: 'econ.be', section: 'price', severity: 'warn', title: 'ACoS de equilibrio justo', why: `Equilibrio ${(u.breakEvenAcos * 100).toFixed(1)} % vs objetivo ${d.econ.acosTarget} %: poco colchón de lanzamiento.`, fix: 'Reserva más margen para publicidad.' });
      u.warnings.forEach((w) => add({ id: 'econ.assumption', section: 'price', severity: 'warn', title: 'Supuesto económico', why: w, fix: 'Verifícalo antes de operar.' }));
    }

    /* 4. Regulatorio y claims */
    evalChecklist(d.regulatory, 'regulatory', F, 'Regulatorio');
    const claims = d.claims || [];
    claims.forEach((c, i) => { if (!(c.evidence || '').trim()) add({ id: `claims.${i}`, section: 'regulatory', severity: 'block', title: `Claim sin respaldo: «${(c.text || '').slice(0, 60)}»`, why: 'Todo claim del listing necesita evidencia documental.', fix: 'Adjunta el estudio/ensayo/autorización o elimina el claim.' }); });
    const declared = claims.map((c) => (c.text || '').toLowerCase()).join(' ');
    const listingText = ((d.content && d.content.title && d.content.title.evidence) || '') + ' ' + ((d.content && d.content.bullets && d.content.bullets.evidence) || '');
    RISKY.forEach((w) => { if (listingText.toLowerCase().includes(w) && !declared.includes(w)) add({ id: `claims.risky.${w}`, section: 'regulatory', severity: 'warn', title: `Posible claim de riesgo en el listing: «${w}»`, why: 'Términos de este tipo suelen requerir respaldo o están restringidos.', fix: 'Añádelo a la lista de claims con evidencia o reescribe el texto.' }); });
    S.regulatory = { critical: Object.values(d.regulatory).filter((x) => x.critical).length };

    /* 5. Contenido */
    evalChecklist(d.content, 'content', F, 'Contenido');

    /* 6. Stock y logística */
    const L = d.logistics; evalChecklist(L.items, 'logistics', F, 'Logística');
    if (!num(L.stockAvailable) || L.stockAvailable < 0) add({ id: 'log.stock', section: 'logistics', severity: 'block', title: 'Stock disponible no informado', why: 'No se puede comprobar la cobertura de lanzamiento.', fix: 'Indica unidades disponibles (incl. entradas confirmadas).' });
    else if (!num(L.forecastUnitsMonth) || L.forecastUnitsMonth <= 0) add({ id: 'log.forecast', section: 'logistics', severity: 'block', title: 'Previsión de ventas no informada', why: 'Sin previsión no hay cobertura calculable.', fix: 'Indica unidades/mes previstas.' });
    else {
      const need = Math.ceil((L.forecastUnitsMonth / 30) * L.coverTargetDays); S.stockNeed = need;
      if (L.stockAvailable < need) add({ id: 'log.short', section: 'logistics', severity: 'block', title: 'Stock insuficiente para el lanzamiento', why: `Necesitas ${need} uds para ${L.coverTargetDays} días (${L.forecastUnitsMonth}/mes) y hay ${L.stockAvailable}: faltan ${need - L.stockAvailable}.`, fix: 'Aumenta el stock o retrasa el lanzamiento.' });
      if (!num(L.leadTimeDays) || L.leadTimeDays <= 0) add({ id: 'log.lead', section: 'logistics', severity: 'warn', title: 'Plazo de reposición no informado', why: 'No se puede comprobar riesgo de rotura.', fix: 'Indica el plazo de reposición en días.' });
      else if (L.leadTimeDays > L.coverTargetDays) add({ id: 'log.leadlong', section: 'logistics', severity: 'warn', title: 'Reposición más lenta que la cobertura', why: `Plazo ${L.leadTimeDays} d > cobertura ${L.coverTargetDays} d: rotura probable.`, fix: 'Aumenta la cobertura inicial.' });
    }

    const rank = { nogo: 0, block: 1, warn: 2 };
    F.sort((a, b) => rank[a.severity] - rank[b.severity]);
    const n = (s) => F.filter((f) => f.severity === s).length;
    const decision = n('nogo') ? 'NO-GO' : n('block') ? 'REVISAR' : 'GO';
    const sectionStatus = {};
    ['benchmark', 'demand', 'price', 'regulatory', 'content', 'logistics'].forEach((s) => { const fs = F.filter((f) => f.section === s); sectionStatus[s] = fs.some((f) => f.severity === 'nogo') ? 'nogo' : fs.some((f) => f.severity === 'block') ? 'block' : fs.length ? 'warn' : 'ok'; });
    return { decision, findings: F, counts: { nogo: n('nogo'), block: n('block'), warn: n('warn') }, sections: S, sectionStatus, today,
      summary: decision === 'GO' ? 'Sin bloqueos. GO no publica nada: la publicación sigue requiriendo aprobación explícita.' : decision === 'REVISAR' ? `${n('block')} bloqueo(s) por resolver antes de lanzar.` : `${n('nogo')} causa(s) de inviabilidad económica/competitiva.` };
  }

  /* Expedientes de ejemplo (DEMO, ficticios) para demostrar la lógica. */
  function example(kind, today) {
    const d = createEmpty('cosmetico', 'FBA'), D = (n) => { const x = new Date(today + 'T00:00:00Z'); x.setUTCDate(x.getUTCDate() - n); return x.toISOString().slice(0, 10); };
    d.product.name = 'Producto candidato (DEMO ficticio)';
    d.econ = { ...Econ.DEFAULTS, price: 26.9, cost: 4.5, fbaFee: 3.6, acosTarget: 20 };
    d.competitors = [['Comp. A', 22.9, 1, 1, 100, 3], ['Comp. B', 24.5, 0, 1, 100, 5], ['Comp. C', 26.9, 0, 1, 100, 7], ['Comp. D', 27.5, 0, 1, 100, 2], ['Comp. E', 21.9, 4, 1, 100, 9]]
      .map(([name, priceGross, shipping, packUnits, contentValue, ago]) => ({ name, asin: 'DEMO-' + name, priceGross, shipping, packUnits, contentValue, source: 'DEMO ficticio', date: D(ago) }));
    if (kind === 'economia') return d; // solo economía: margen positivo, expediente vacío
    if (kind === 'nogo') { d.econ.cost = 15; return d; }
    d.keywords = ['crema pies secos', 'hidratante pies', 'crema talones', 'pies agrietados', 'crema pies mujer', 'crema pies hombre'].map((k, i) => ({ keyword: k, volume: 9000 - i * 900, source: 'DEMO ficticio', date: D(10) }));
    Object.values(d.regulatory).forEach((it) => { it.status = 'cumplido'; it.evidence = 'DEMO: documento ficticio'; it.date = D(20); });
    Object.values(d.content).forEach((it) => { it.status = 'cumplido'; it.evidence = 'DEMO: archivo ficticio'; });
    d.content.video.status = 'pendiente'; // un aviso, no bloquea
    d.claims = [{ text: 'Hidrata la piel en 24 h', evidence: 'DEMO: ensayo de hidratación ficticio' }];
    Object.values(d.logistics.items).forEach((it) => { it.status = 'cumplido'; it.evidence = 'DEMO'; });
    Object.assign(d.logistics, { stockAvailable: 900, leadTimeDays: 30, forecastUnitsMonth: 300, coverTargetDays: 45 });
    return d;
  }

  return { createEmpty, retemplate, evaluate, benchmark, example, REG, CONTENT, LOGI, RISKY, MAX_COMP_AGE, MAX_KW_AGE, MIN_COMP, MIN_KW };
});
