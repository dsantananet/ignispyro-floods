"""Rótulos por freguesia a partir de estatísticas por freguesia do Copernicus GFM (ENSEMBLE observed flood extent, 20 m).
EXPERIMENTAL — NÃO OPERACIONAL. Fonte: Copernicus EMS Global Flood Monitoring (STAC público stac.eodc.eu; COG data.eodc.eu).
Entrada: CSV dtmnfr,scene_id,datetime_utc,valid_pixels,flood_fraction,masked_pixels (uma linha por freguesia×cena com dados válidos).
y=1 se cheia máx. ≥5 ha e ≥0,5 % da freguesia em alguma cena; observado_sem_cheia=1 se cobertura válida ≥80 % da freguesia (valid/(valid+masked)) e cheia máx. <0,5 ha. flood_ha = fração de cheia × cobertura × área da freguesia.
ATENÇÃO: "sem cheia" = não detetada pelo GFM (SAR; sem exclusão por zonas urbanas/vegetação aplicada aqui), não seco confirmado.
Uso: python ai/features/gfm_parish_labels.py CSV [--repo .] [--out ai/data/labels/parish_labels_gfm.csv]"""
import argparse, json, os
import geopandas as gpd, pandas as pd


a = argparse.ArgumentParser(); a.add_argument('csv'); a.add_argument('--repo', default='.'); a.add_argument('--out', default='ai/data/labels/parish_labels_gfm.csv'); a = a.parse_args()
R = os.path.join(a.repo, 'dist/data/')
par = gpd.read_file(R + 'parishes.geojson').to_crs(3763)[['dtmnfr', 'freguesia', 'geometry']]; par['area_ha'] = par.area / 1e4
sus = json.load(open(R + 'susceptibility.json'))['parishes']; ter = json.load(open(R + 'terrain-susceptibility.json'))['parishes']
fw = json.load(open(R + 'floodwatch.json'))['parishes'] if os.path.exists(R + 'floodwatch.json') else {}
D = pd.read_csv(a.csv, dtype={'dtmnfr': str})
# O TiTiler devolve contagens de pixéis numa grelha de leitura que não é necessariamente 20 m: usar proporções, não pixéis×área.
D['cobertura'] = D.valid_pixels / (D.valid_pixels + D.masked_pixels)
g = D.groupby('dtmnfr').agg(n_obs=('scene_id', 'size'), n_dias=('datetime_utc', lambda s: s.str[:10].nunique())).reset_index()
g = g.merge(par.drop(columns='geometry'), on='dtmnfr')
D = D.merge(par[['dtmnfr', 'area_ha']], on='dtmnfr'); D['flood_ha'] = D.flood_fraction * D.cobertura * D.area_ha
g = g.merge(D.groupby('dtmnfr').agg(flood_ha=('flood_ha', 'max'), cobertura=('cobertura', 'max')).reset_index(), on='dtmnfr')
g['y'] = ((g.flood_ha >= 5) & (g.flood_ha / g.area_ha >= 0.005)).astype(int)
g['observado_sem_cheia'] = ((g.cobertura >= 0.8) & (g.flood_ha < 0.5)).astype(int)
g['f100'] = g.dtmnfr.map(lambda k: sus.get(k, {}).get('f100')); g['f1000'] = g.dtmnfr.map(lambda k: sus.get(k, {}).get('f1000'))
g['river300'] = g.dtmnfr.map(lambda k: sus.get(k, {}).get('river300')); g['hand_lt5'] = g.dtmnfr.map(lambda k: ter.get(k, {}).get('hand_lt5_frac'))
g['ias_static_class'] = g.dtmnfr.map(lambda k: fw.get(k, {}).get('s')); g['ias_static_score'] = g.dtmnfr.map(lambda k: fw.get(k, {}).get('sc'))
os.makedirs(os.path.dirname(a.out), exist_ok=True); g.round(4).to_csv(a.out, index=False)
print(len(g), 'freguesias;', int(g.y.sum()), 'positivas;', int(g.observado_sem_cheia.sum()), 'observadas sem cheia (cobertura>=80%)')
