/* IGNISPYRO Floods AI — Recolha GFM por freguesia (EXPERIMENTAL — NÃO OPERACIONAL). Só leitura.
   Correr com o separador em https://titiler.services.eodc.eu/docs (único anfitrião que aceita os pedidos POST).
   STAC público (stac.eodc.eu) + TiTiler /cog/statistics. Saída: CSV dtmnfr,scene_id,datetime_utc,valid_pixels,flood_fraction,masked_pixels */
(() => {
  if (document.getElementById('gfm-collector')) return;
  const PARISHES = 'https://dsantananet.github.io/ignispyro-floods/data/parishes.geojson';
  const STAC = 'https://stac.eodc.eu/api/v1/search', STAT = 'https://titiler.services.eodc.eu/cog/statistics';
  const BBOX = [-9.6, 36.9, -6.1, 42.2], HEAD = 'dtmnfr,scene_id,datetime_utc,valid_pixels,flood_fraction,masked_pixels';
  const S = { run: false, rows: [], done: new Set(), parishes: null, tot: 0, doneJobs: 0, t0: 0 };
  const box = document.createElement('div'); box.id = 'gfm-collector';
  box.style.cssText = 'position:fixed;top:10px;right:10px;z-index:99999;width:360px;background:#0f172a;color:#e2e8f0;font:13px system-ui,sans-serif;border:2px solid #f59e0b;border-radius:10px;padding:12px;box-shadow:0 8px 30px #0008';
  box.innerHTML = `<b>GFM por freguesia</b> <span style="background:#f59e0b;color:#000;padding:1px 6px;border-radius:4px;font-size:11px">EXPERIMENTAL — NÃO OPERACIONAL</span>
  <div style="margin:8px 0;display:grid;grid-template-columns:1fr 1fr;gap:6px">
   <label>Início<br><input id="gc-t0" type="date" value="2026-01-25" style="width:100%"></label>
   <label>Fim<br><input id="gc-t1" type="date" value="2026-02-11" style="width:100%"></label>
   <label>Âmbito<br><select id="gc-sc" style="width:100%"><option value="all">Todas as freguesias</option><option value="s10">Amostra 10 %</option><option value="s4">Amostra 4 %</option></select></label>
   <label>Pedidos em paralelo<br><input id="gc-w" type="number" min="1" max="24" value="12" style="width:100%"></label></div>
  <label style="display:block;margin-bottom:6px">Retomar de CSV (opcional)<br><input id="gc-f" type="file" accept=".csv" style="width:100%"></label>
  <button id="gc-go">Iniciar</button> <button id="gc-stop" disabled>Parar</button> <button id="gc-dl" disabled>Descarregar CSV</button>
  <div id="gc-st" style="margin-top:8px;white-space:pre-line;color:#93c5fd">Pronto.</div>
  <div style="font-size:11px;color:#94a3b8;margin-top:6px">Sem cheia = não detetada (SAR), não "seco". Termos de licença GFM a confirmar antes de redistribuir.</div>`;
  document.body.appendChild(box);
  const $ = id => box.querySelector('#' + id), say = t => { $('gc-st').textContent = t; };
  const ctr = g => { let a = 1e9, b = -1e9, c = 1e9, d = -1e9; const w = cs => { if (typeof cs[0] === 'number') { a = Math.min(a, cs[0]); b = Math.max(b, cs[0]); c = Math.min(c, cs[1]); d = Math.max(d, cs[1]); } else cs.forEach(w); }; w(g.coordinates); return [(a + b) / 2, (c + d) / 2]; };
  const pip = (p, ring) => { let ins = false; for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) { const [xi, yi] = ring[i], [xj, yj] = ring[j]; if ((yi > p[1]) !== (yj > p[1]) && p[0] < (xj - xi) * (p[1] - yi) / (yj - yi) + xi) ins = !ins; } return ins; };
  const inside = (p, g) => (g.type === 'Polygon' ? [g.coordinates] : g.coordinates).some(poly => pip(p, poly[0]));
  async function scenes(t0, t1) {
    let items = [], tok = null; const body = { collections: ['GFM'], bbox: BBOX, datetime: t0 + 'T00:00:00Z/' + t1 + 'T00:00:00Z', limit: 200 };
    for (let n = 0; n < 200; n++) {
      const r = await fetch(STAC, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(tok ? { ...body, ...tok } : body) });
      if (!r.ok) throw new Error('STAC ' + r.status); const j = await r.json();
      items = items.concat(j.features.filter(f => f.assets.ensemble_flood_extent).map(f => ({ id: f.id, dt: f.properties.datetime.slice(0, 16), u: f.assets.ensemble_flood_extent.href, g: f.geometry })));
      say('A listar cenas… ' + items.length); const nl = (j.links || []).find(l => l.rel === 'next' && l.body); if (!nl) break; tok = nl.body;
    }
    return items;
  }
  async function stat(u, g) {
    try {
      const r = await fetch(STAT + '?url=' + encodeURIComponent(u) + '&categorical=true', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ type: 'Feature', properties: {}, geometry: g }) });
      if (r.status !== 200) return null; const s = (await r.json()).properties.statistics.b1;
      return s.valid_pixels > 0 ? [s.valid_pixels, +s.mean.toFixed(5), s.masked_pixels] : null;
    } catch (e) { return null; }
  }
  const csv = () => HEAD + '\n' + S.rows.map(r => r.join(',')).join('\n') + '\n';
  const progress = () => { const el = (Date.now() - S.t0) / 1000, rate = S.doneJobs / Math.max(el, 1); say(`${S.doneJobs}/${S.tot} grupos · ${S.rows.length} observações · ${rate.toFixed(1)} grupos/s${S.run ? '' : ' · parado'}`); };
  $('gc-f').onchange = async e => { const f = e.target.files[0]; if (!f) return; const L = (await f.text()).trim().split('\n').slice(1); S.rows = L.map(l => l.split(',').slice(0, 6)).filter(r => r.length === 6); S.done = new Set(S.rows.map(r => r[0] + '|' + r[1])); say(S.rows.length + ' observações carregadas (serão ignoradas ao retomar).'); $('gc-dl').disabled = false; };
  $('gc-stop').onclick = () => { S.run = false; };
  $('gc-dl').onclick = () => { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([csv()], { type: 'text/csv' })); a.download = `gfm_parish_obs_${$('gc-t0').value}_${$('gc-t1').value}.csv`; a.click(); };
  $('gc-go').onclick = async () => {
    if (S.run) return; S.run = true; $('gc-go').disabled = true; $('gc-stop').disabled = false;
    try {
      if (!S.parishes) { say('A obter freguesias…'); const g = await (await fetch(PARISHES)).json(); S.parishes = g.features.filter(f => f.geometry).map(f => ({ k: f.properties.dtmnfr, g: f.geometry, c: ctr(f.geometry) })); }
      const sc = $('gc-sc').value; let rnd = 1; const rand = () => (rnd = (rnd * 1664525 + 1013904223) % 4294967296) / 4294967296;
      const frac = sc === 's10' ? 0.1 : sc === 's4' ? 0.04 : 1; const P = S.parishes.filter(() => frac === 1 || rand() < frac);
      const SC = await scenes($('gc-t0').value, $('gc-t1').value); say(SC.length + ' cenas. A agrupar…');
      const gm = new Map(); for (const s of SC) for (const p of P) if (inside(p.c, s.g)) { const k = s.id + '|' + p.k.slice(0, 4); if (!gm.has(k)) gm.set(k, []); gm.get(k).push([s, p]); }
      const G = [...gm.values()]; S.tot = G.length; S.doneJobs = 0; S.t0 = Date.now(); let gi = 0; $('gc-dl').disabled = false;
      const worker = async () => {
        while (S.run && gi < G.length) {
          const g = G[gi++]; let ok = false;
          for (let n = 0; n < g.length && S.run; n++) {
            const [s, p] = g[n]; if (S.done.has(p.k + '|' + s.id)) continue;
            const r = await stat(s.u, p.g);
            if (r) { ok = true; S.rows.push([p.k, s.id, s.dt, ...r]); S.done.add(p.k + '|' + s.id); } else if (!ok && n >= 2) break; /* sondagem: município sem dados nesta cena */
          }
          S.doneJobs++; if (S.doneJobs % 25 === 0) progress();
        }
      };
      await Promise.all(Array.from({ length: Math.max(1, Math.min(24, +$('gc-w').value || 12)) }, worker));
      progress(); say($('gc-st').textContent + (gi >= G.length ? '\nConcluído — descarregue o CSV.' : '\nParado — pode descarregar ou retomar.'));
    } catch (e) { say('Erro: ' + e.message); }
    S.run = false; $('gc-go').disabled = false; $('gc-stop').disabled = true; $('gc-dl').disabled = false;
  };
})();
