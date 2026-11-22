// Tabela para ArcGIS Online (juntar à CAOP por dtmnfr) a partir de floodwatch.json.
// Uso: node ai/susceptibility/build-layer.mjs [floodwatch.json] [saida.csv]
import fs from 'node:fs';
const src = process.argv[2] || 'dist/data/floodwatch.json', out = process.argv[3] || 'ai/outputs/ias-live.csv';
const w = JSON.parse(fs.readFileSync(src, 'utf8'));
if (w.schema_version !== 'floods-watch/1') throw new Error('esquema inesperado: ' + w.schema_version);
const N = w.method.classes, head = ['dtmnfr', 'classe_ias', 'classe_nome', 'estrutural_1_5', 'ativacao_1_4', 'computed_at', 'estado'];
const rows = Object.entries(w.parishes).map(([k, p]) => [k, p.a ?? 0, N[p.a ?? 0], p.s ?? '', p.t ?? '', w.computed_at, 'EXPERIMENTAL — NÃO OPERACIONAL']);
fs.mkdirSync(out.replace(/[^/]*$/, '') || '.', { recursive: true });
fs.writeFileSync(out, [head, ...rows].map(r => r.map(v => `"${v}"`).join(',')).join('\n'));
console.log(rows.length, 'freguesias ->', out);
