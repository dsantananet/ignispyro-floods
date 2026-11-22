"""Rótulos por freguesia a partir de pacotes de delineação Copernicus EMS (cheia observada, SAR).
EXPERIMENTAL — NÃO OPERACIONAL. © União Europeia, Copernicus EMS (EMSR861, EMSR864).
Unidade: freguesia (CAOP2025) com ≥50% da área dentro da AOI. y=1 se cheia observada ≥5 ha e ≥0,5% da freguesia (regra fixada antes de ver AUC).
ATENÇÃO: y=0 significa "sem cheia detetada na AOI", NÃO "seco confirmado" (limitações SAR). Não são negativos observados.
Uso: python ai/features/emsr_parish_labels.py DIR_ZIPS [--repo .] [--out ai/data/labels]  (DIR_ZIPS: ZIPs EMSR*_DEL_*; ficheiros .tmp aceites)"""
import argparse, glob, hashlib, json, os, re, sys, tempfile, zipfile
import geopandas as gpd, numpy as np, pandas as pd

KEEP = re.compile(r'(observedEventA|areaOfInterestA)_v\d\.(shp|dbf|shx|prj|cpg)$')


def extract(zdir, tmp):
    man = []
    for f in sorted(glob.glob(os.path.join(zdir, '*.zip')) + glob.glob(os.path.join(zdir, '*.tmp'))):
        try: z = zipfile.ZipFile(f)
        except zipfile.BadZipFile: continue
        names = [n for n in z.namelist() if KEEP.search(n) and '..' not in n and not n.startswith('/')]
        if not names: continue
        prod = re.match(r'(EMSR\d+_AOI\d+_DEL_\w+?)_', os.path.basename(names[0]))[1]
        for n in names: z.extract(n, os.path.join(tmp, prod))
        man.append({'product': prod, 'sha256': hashlib.sha256(open(f, 'rb').read()).hexdigest(), 'bytes': os.path.getsize(f)})
    return man


def main():
    a = argparse.ArgumentParser(); a.add_argument('zdir'); a.add_argument('--repo', default='.'); a.add_argument('--out', default='ai/data/labels'); a = a.parse_args()
    R = os.path.join(a.repo, 'dist/data/')
    par = gpd.read_file(R + 'parishes.geojson').to_crs(3763)[['dtmnfr', 'freguesia', 'geometry']]; par['area_ha'] = par.area / 1e4
    fw = json.load(open(R + 'floodwatch.json'))['parishes'] if os.path.exists(R + 'floodwatch.json') else {}
    sus = json.load(open(R + 'susceptibility.json'))['parishes']; ter = json.load(open(R + 'terrain-susceptibility.json'))['parishes']
    par['f100'] = par.dtmnfr.map(lambda k: sus.get(k, {}).get('f100')); par['f1000'] = par.dtmnfr.map(lambda k: sus.get(k, {}).get('f1000'))
    par['river300'] = par.dtmnfr.map(lambda k: sus.get(k, {}).get('river300')); par['hand_lt5'] = par.dtmnfr.map(lambda k: ter.get(k, {}).get('hand_lt5_frac'))
    par['ias_static_class'] = par.dtmnfr.map(lambda k: fw.get(k, {}).get('s')); par['ias_static_score'] = par.dtmnfr.map(lambda k: fw.get(k, {}).get('sc'))
    with tempfile.TemporaryDirectory() as tmp:
        man = extract(a.zdir, tmp); groups, aois = {}, {}
        for shp in glob.glob(tmp + '/*/*observedEventA*.shp'):
            m = re.match(r'(EMSR\d+)_AOI(\d+)_', os.path.basename(shp)); groups.setdefault((m[1], m[2]), []).append(shp)
        for shp in glob.glob(tmp + '/*/*areaOfInterestA*.shp'):
            m = re.match(r'(EMSR\d+)_AOI(\d+)_', os.path.basename(shp)); aois[(m[1], m[2])] = shp
        rows = []
        for k, shps in sorted(groups.items()):
            obs = pd.concat([gpd.read_file(s) for s in shps]).to_crs(3763); obs = obs[~obs.geometry.is_empty]
            u = obs.geometry.union_all().buffer(0); aoi = gpd.read_file(aois[k]).to_crs(3763).geometry.union_all().buffer(0)
            p = par[par.intersects(aoi)].copy(); p['aoi_cov'] = p.geometry.intersection(aoi).area / 1e4 / p.area_ha; p = p[p.aoi_cov >= 0.5]
            p['flood_ha'] = p.geometry.intersection(u).area / 1e4; p['y'] = ((p.flood_ha >= 5) & (p.flood_ha / p.area_ha >= 0.005)).astype(int)
            p['ems'], p['aoi'], p['n_products'] = k[0], k[1], len(shps); rows.append(p.drop(columns='geometry'))
    D = pd.concat(rows); os.makedirs(a.out, exist_ok=True)
    D.round(4).to_csv(os.path.join(a.out, 'parish_labels_emsr.csv'), index=False)
    json.dump({'source': 'Copernicus EMS Rapid Mapping (EMSR861, EMSR864), delineação observedEventA', 'attribution': '© European Union, Copernicus EMS', 'rule': 'y=1 se cheia ≥5 ha e ≥0,5% da freguesia; freguesia com ≥50% dentro da AOI',
               'warning': 'y=0 = sem cheia detetada, não seco confirmado', 'packages': man}, open(os.path.join(a.out, 'manifest_emsr.json'), 'w'), indent=1, ensure_ascii=False)
    print(D.groupby(['ems', 'aoi']).agg(n=('y', 'size'), pos=('y', 'sum')).to_string())


if __name__ == '__main__':
    sys.exit(main())
