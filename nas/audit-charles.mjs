import { readdir, readFile } from 'node:fs/promises';
import { join } from 'node:path';

const directory = process.argv[2];
if (!directory) throw new Error('Usage: node nas/audit-charles.mjs ARCHIVE_DIRECTORY');
const names = (await readdir(directory)).filter(name => name.endsWith('.json')).sort();
if (!names.length) throw new Error('Empty archive');
const summary = { cycles: 0, first: null, last: null, complete: 0, partial: 0,
  with_hydrology: 0, with_reservoir_outflow: 0, with_observed_rainfall: 0 };
for (const name of names) {
  const { schema_version, event, monitor, stations, hydrology, simulation } =
    JSON.parse(await readFile(join(directory, name), 'utf8'));
  const time = Date.parse(monitor?.completed_at);
  if (schema_version !== 'ignispyro-flood-event/1' || event !== 'Charles' ||
      !(time >= Date.parse('2026-11-10') && time < Date.parse('2026-11-15')) ||
      (summary.last && time <= Date.parse(summary.last)) ||
      !['ok', 'partial'].includes(monitor?.status) ||
      !stations?.retrieved_at || stations.retrieved_at !== simulation?.inputs_retrieved_at ||
      stations.features.length !== monitor.stations || simulation.basins.length !== monitor.basins) {
    throw new Error('Invalid archive cycle: ' + name);
  }
  summary.cycles++;
  summary.first ??= monitor.completed_at;
  summary.last = monitor.completed_at;
  summary[monitor.status === 'ok' ? 'complete' : 'partial']++;
  if (hydrology) {
    summary.with_hydrology++;
    if (hydrology.features.some(({ properties: p }) =>
      p.type === 'estacao_albufeira' && !p.collection_error && Number.isFinite(p.outflow_m3s) &&
      Date.parse(p.outflow_m3s_time) <= time && time - Date.parse(p.outflow_m3s_time) <= 10800000)) {
      summary.with_reservoir_outflow++;
    }
  }
  if (simulation.basins.some(b => !b.modelled_rainfall && Number.isFinite(b.p24_mm))) {
    summary.with_observed_rainfall++;
  }
}
console.log(JSON.stringify(summary, null, 2));
