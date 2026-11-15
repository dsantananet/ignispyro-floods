import { mkdir, rename, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const first = Date.parse('2026-11-10T00:00:00Z');
const last = Date.parse('2026-11-15T00:00:00Z');

export async function archiveCharles(root, monitor, stations, hydrology, simulation) {
  const time = Date.parse(monitor.completed_at);
  if (!Number.isFinite(time) || time < first || time >= last) return false;
  if (!['ok', 'partial'].includes(monitor.status) ||
      !stations?.retrieved_at || stations.retrieved_at !== simulation?.inputs_retrieved_at) {
    throw new Error('incoherent_event_snapshot');
  }
  const directory = join(root, 'charles-20261111');
  await mkdir(directory, { recursive: true, mode: 0o700 });
  const name = new Date(time).toISOString().replace(/[:.]/g, '-');
  const target = join(directory, name + '.json');
  const pending = target + '.pending';
  const snapshot = { schema_version: 'ignispyro-flood-event/1', event: 'Charles',
    monitor, stations, hydrology: hydrology ?? null, simulation };
  await writeFile(pending, JSON.stringify(snapshot), { flag: 'wx', mode: 0o600 });
  await rename(pending, target);
  return true;
}
