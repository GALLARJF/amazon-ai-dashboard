// Evalúa casos con el motor JS V0.2 (referencia). Entrada: JSON por stdin. Salida: JSON.
const E = require('../js/economics.js'), D = require('../js/dossier.js');
let s = ''; process.stdin.on('data', c => s += c).on('end', () => {
  const cases = JSON.parse(s), out = { econ: [], dossier: [] };
  cases.econ.forEach(c => { const u = E.unit(c.input, c.price === null ? undefined : c.price); const mp = E.minPrice(c.input);
    out.econ.push({ valid: u.valid, contribution: u.valid ? u.contribution : null, net: u.valid ? u.net : null, referral: u.valid ? u.referral : null, be: u.valid ? u.breakEvenAcos : null, mp: mp ? mp.commercial : null, errors: u.errors }); });
  cases.dossier.forEach(d => { const r = D.evaluate(d, cases.today); out.dossier.push({ decision: r.decision, ids: r.findings.map(f => f.id + '|' + f.severity), counts: r.counts }); });
  process.stdout.write(JSON.stringify(out));
});
