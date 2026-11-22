// Gera a tabela de suscetibilidade (CSV + JSON) a partir de dados Floods (por defeito dist/data).
// Uso: node ai/susceptibility/build-layer.mjs [dirDados] [dirSaida] [agoraISO]
import fs from 'node:fs'; import path from 'node:path'; import { createRequire } from 'node:module';
const require = createRequire(import.meta.url); const F = require('./core.js');
const dir = process.argv[2] || 'dist/data', out = process.argv[3] || 'ai/outputs';
const now = Date.parse(process.argv[4] || new Date().toISOString());
const J = f => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
const sim = new Map(J('simulation.json').basins.map(b => [b.id, b]));
const hist = new Map(J('history.json').basins.map(b => [b.id, b]));
const sus = J('susceptibility.json').parishes, terr = J('terrain-susceptibility.json').parishes;
const par = J('parishes.geojson').features.map(f => f.properties);
const rows = par.map(p => {
  const basins = (p.basin_ids || []).map(id => ({ sim: sim.get(id), hist: hist.get(id) }));
  const r = F.scoreParish({ sus: sus[p.dtmnfr], terr: terr[p.dtmnfr], basins }, now);
  return { dtmnfr: p.dtmnfr, freguesia: p.freguesia, municipio: p.municipio, classe: r.cls.key, score: r.score == null ? '' : r.score.toFixed(3),
    estatica: r.static == null ? '' : r.static.toFixed(3), dinamica: r.dynamic == null ? '' : r.dynamic.toFixed(3) };
});
fs.mkdirSync(out, { recursive: true });
const meta = { schema: 'floods-ai-susceptibility/1', model: F.MODEL, computed_for: new Date(now).toISOString(), inputs_computed_at: J('simulation.json').computed_at,
  note: 'Suscetibilidade relativa (regras v0), não é probabilidade nem previsão de inundação.', counts: rows.reduce((a, r) => (a[r.classe] = (a[r.classe] || 0) + 1, a), {}) };
fs.writeFileSync(path.join(out, 'susceptibility-live.json'), JSON.stringify({ meta, parishes: rows }));
fs.writeFileSync(path.join(out, 'susceptibility-live.csv'), Object.keys(rows[0]).join(',') + '\n' + rows.map(r => Object.values(r).map(v => `"${v}"`).join(',')).join('\n'));
console.log(JSON.stringify(meta));
