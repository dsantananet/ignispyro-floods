"""Static flood-susceptibility components per parish (run occasionally, output committed).

Inputs (dist/data): parishes, APA flood zones T20/T100/T1000, river network.
Output: dist/data/susceptibility.json  — area fractions, never flood depths.
Population in zones is an AREA-WEIGHTED ESTIMATE (parish residents x zone share)."""
import sys,json,pathlib,datetime
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent/'engine'))
import numpy as np
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform,unary_union
from shapely import make_valid
from shapely.strtree import STRtree
from terrain import roc_auc
D=pathlib.Path('dist/data');to=Transformer.from_crs(4326,3763,always_xy=True).transform
load=lambda n:json.loads((D/n).read_text(encoding='utf-8-sig'))
def geom(g):
    s=transform(to,shape(g));return s if s.is_valid else make_valid(s)
parishes=load('parishes.geojson')['features']
pg=[geom(f['geometry']) for f in parishes];tree=STRtree(pg)
zones={}
for t,name in (('t20','risk20.geojson'),('t100','risk.geojson'),('t1000','risk1000.geojson')):
    zones[t]=unary_union([x for x in (geom(f['geometry']).buffer(0) for f in load(name)['features']) if not x.is_empty]);print(t,'zone km2',round(zones[t].area/1e6,1))
rivers=[geom(f['geometry']) for f in load('rivers.geojson')['features']]
river_zone=unary_union([r.buffer(300) for r in rivers]);print('river buffer km2',round(river_zone.area/1e6,1))
rows={}
for f,g in zip(parishes,pg):
    p=f['properties'];a=g.area
    def frac(z):
        if not g.intersects(z):return 0.
        return min(1.,g.intersection(z).area/a)
    fr={t:frac(z) for t,z in zones.items()};river=frac(river_zone);pop=p.get('population_2021') or 0;vul=p.get('vulnerable_age_count') or 0
    rows[p['dtmnfr']]={'f20':round(fr['t20'],4),'f100':round(fr['t100'],4),'f1000':round(fr['t1000'],4),'river300':round(river,4),
        'apa_class_t100':p.get('risk_t100'),'pop_t20_est':round(pop*fr['t20']),'pop_t100_est':round(pop*fr['t100']),'pop_t1000_est':round(pop*fr['t1000']),'vulnerable_t100_est':round(vul*fr['t100'])}
# diagnostic: does river proximity alone discriminate parishes that APA mapped as flood-prone?
codes=list(rows);auc=roc_auc([rows[c]['river300'] for c in codes],[rows[c]['f100']>0.01 for c in codes])
out={'schema_version':'floods-susceptibility-static/1','computed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'method':'Area fractions of parish (EPSG:3763) inside APA T20/T100/T1000 zones and within 300 m of Strahler>=6 rivers. Population = parish residents x zone share (area-weighted estimate, BGRI subsections not intersected).',
 'sources':['APA Directiva 2007/60/CE 2.º ciclo','APA rede hidrográfica','CAOP2025','INE BGRI2021 via parishes.geojson'],
 'diagnostics':{'auc_river300_vs_apa_t100_presence':auc,'note':'Diagnostic only: APA zones cover only studied reaches, so absence is not absence of hazard.'},
 'parishes':rows}
(D/'susceptibility.json').write_text(json.dumps(out,separators=(',',':'),ensure_ascii=False),encoding='utf-8')
print(json.dumps({'parishes':len(rows),'with_zone':sum(1 for r in rows.values() if r['f100']>0 or r['f20']>0),'auc':auc}))
