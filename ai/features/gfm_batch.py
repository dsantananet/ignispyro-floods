"""Recolha em lote (fora do browser) das estatísticas GFM por freguesia — mesmo esquema que gfm_parish_obs_*.csv.
EXPERIMENTAL — NÃO OPERACIONAL. Só leitura: STAC público (stac.eodc.eu) + TiTiler (titiler.services.eodc.eu). Não escreve em nenhum serviço.
Retoma automaticamente (ignora pares freguesia×cena já no CSV). Corre na máquina do utilizador/QNAP; o ambiente de desenvolvimento não alcança estes anfitriões.
Uso: python ai/features/gfm_batch.py PARISHES.geojson 2025-11-01 2026-03-15 --out saida.csv [--workers 8] [--pause 0.0]
Dependências: requests, shapely (pip). Termos de licença do GFM a confirmar antes de redistribuir."""
import argparse, concurrent.futures as cf, csv, json, os, sys, time
import requests
from shapely.geometry import shape, Point

STAC = 'https://stac.eodc.eu/api/v1/search'; TITILER = 'https://titiler.services.eodc.eu/cog/statistics'
BBOX = [-9.6, 36.9, -6.1, 42.2]  # Portugal continental
HEAD = ['dtmnfr', 'scene_id', 'datetime_utc', 'valid_pixels', 'flood_fraction', 'masked_pixels']


def list_scenes(t0, t1, post=requests.post):
    items, body, tok = [], {'collections': ['GFM'], 'bbox': BBOX, 'datetime': f'{t0}T00:00:00Z/{t1}T00:00:00Z', 'limit': 200}, None
    while True:
        r = post(STAC, json={**body, **(tok or {})}, timeout=60); r.raise_for_status(); j = r.json()
        items += [{'id': f['id'], 'dt': f['properties']['datetime'][:16], 'u': f['assets']['ensemble_flood_extent']['href'], 'g': shape(f['geometry'])}
                  for f in j['features'] if 'ensemble_flood_extent' in f['assets']]
        nl = next((l for l in j.get('links', []) if l.get('rel') == 'next' and l.get('body')), None)
        if not nl: return items
        tok = nl['body']


def stat(url, geom, post=requests.post):
    r = post(TITILER, params={'url': url, 'categorical': 'true'}, json={'type': 'Feature', 'properties': {}, 'geometry': geom}, timeout=120)
    if r.status_code != 200: return None  # sem dados válidos nesta cena/freguesia
    s = r.json()['properties']['statistics']['b1']
    return (s['valid_pixels'], round(s['mean'], 5), s['masked_pixels']) if s['valid_pixels'] > 0 else None


def groups(scenes, parishes):
    """Agrupa freguesias cujo centroide cai no footprint da cena, por município (4 primeiros dígitos)."""
    out = {}
    for s in scenes:
        for p in parishes:
            if s['g'].contains(p['c']): out.setdefault((s['id'], p['k'][:4]), []).append((s, p))
    return list(out.values())


def run_group(g, done, post=requests.post, pause=0.0):
    rows, ok = [], False
    for n, (s, p) in enumerate(g):
        if (p['k'], s['id']) in done: continue
        res = stat(s['u'], p['geom'], post); time.sleep(pause)
        if res: ok = True; rows.append([p['k'], s['id'], s['dt'], *res])
        elif not ok and n >= 2: break  # sondagem: 3 falhas seguidas => município sem dados nesta cena
    return rows


def main():
    a = argparse.ArgumentParser(); a.add_argument('parishes'); a.add_argument('t0'); a.add_argument('t1'); a.add_argument('--out', required=True)
    a.add_argument('--workers', type=int, default=8); a.add_argument('--pause', type=float, default=0.0); a = a.parse_args()
    fc = json.load(open(a.parishes, encoding='utf-8'))
    parishes = [{'k': f['properties']['dtmnfr'], 'geom': f['geometry'], 'c': shape(f['geometry']).representative_point()} for f in fc['features'] if f.get('geometry')]
    done = set()
    if os.path.exists(a.out):
        with open(a.out, newline='') as fh: done = {(r['dtmnfr'], r['scene_id']) for r in csv.DictReader(fh)}
    else:
        with open(a.out, 'w', newline='') as fh: csv.writer(fh).writerow(HEAD)
    scenes = list_scenes(a.t0, a.t1); gl = groups(scenes, parishes)
    print(len(scenes), 'cenas;', len(gl), 'grupos cena×município', file=sys.stderr)
    with open(a.out, 'a', newline='') as fh, cf.ThreadPoolExecutor(a.workers) as ex:
        w = csv.writer(fh)
        for i, rows in enumerate(ex.map(lambda g: run_group(g, done, pause=a.pause), gl)):
            w.writerows(rows); fh.flush()
            if i % 200 == 0: print(f'{i}/{len(gl)}', file=sys.stderr)


if __name__ == '__main__':
    main()
