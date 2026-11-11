import assert from 'node:assert/strict';
import { mkdtemp, readdir, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { archiveCharles } from './archive-charles.mjs';

const root = await mkdtemp(join(tmpdir(), 'ignis-charles-'));
try {
  const stations = {retrieved_at:'2026-11-11T10:00:00Z',features:[]};
  const simulation = {inputs_retrieved_at:stations.retrieved_at};
  const monitor = {completed_at:'2026-11-11T10:01:00Z',status:'ok'};
  assert.equal(await archiveCharles(root, monitor, stations, null, simulation),true);
  const names = await readdir(join(root,'charles-20261111'));
  assert.equal(names.length,1);
  assert.equal(JSON.parse(await readFile(join(root,'charles-20261111',names[0]))).hydrology,null);
  assert.equal(await archiveCharles(root,{...monitor,completed_at:'2026-11-15T00:00:00Z'},stations,null,simulation),false);
  await assert.rejects(archiveCharles(root,monitor,stations,null,{}),/incoherent/);
  console.log('Arquivo atómico, janela temporal, fonte ausente e coerência passaram.');
} finally {
  await rm(root,{recursive:true,force:true});
}
