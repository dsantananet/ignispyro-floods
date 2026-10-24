"""Reproducible territorial joins; install shapely in an isolated environment."""
import sys,json,pathlib,datetime
sys.path.insert(0,str(pathlib.Path('research/python').resolve()))
from shapely.geometry import shape,mapping
from shapely import make_valid
from shapely.strtree import STRtree
D=pathlib.Path('dist/data'); R=pathlib.Path('research/raw');R.mkdir(parents=True,exist_ok=True)
def read(name):return json.loads((D/name).read_text(encoding='utf-8-sig'))
def write(name,obj):(D/name).write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
def geom(f):
 d=f['geometry']
 def coords(x):
  if isinstance(x,list) and x and not isinstance(x[0],list):return x[:2]
  return [coords(y) for y in x]
 return make_valid(shape({**d,'coordinates':coords(d['coordinates'])}))
parishes=read('parishes.geojson'); basins=read('basins.geojson'); old=read('caop2021.geojson');pop=read('bgri-population.json'); primary=read('population.json')
lookup={r['DTMNFR21']:r for r in pop['rows']}; exact={r['geocod']:int(r['valor']) for r in primary.get('rows',[])}
oldgeoms={f['properties']['Dicofre']:geom(f) for f in old['features']}
rank={'Muito Baixo':1,'Baixo':2,'Médio':3,'Alto':4,'Muito Alto':5}
scenarios={}; trees={}; geoms={};report={'parishes':len(parishes['features']),'population_matched':0,'population_missing':0,'geography_review':0,'risk_counts':{},'build_time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
for t,name in [(20,'risk20.geojson'),(100,'risk.geojson'),(1000,'risk1000.geojson')]:
 rawfile=R/name
 if not rawfile.exists():rawfile.write_bytes((D/name).read_bytes())
 j=json.loads(rawfile.read_text(encoding='utf-8-sig'));scenarios[t]=j;geoms[t]=[geom(f).simplify(.0001,preserve_topology=True) for f in j['features']];trees[t]=STRtree(geoms[t]);report['risk_counts'][str(t)]=len(j['features']);print('Prepared T',t,flush=True)
bg=[geom(f) for f in basins['features']];btree=STRtree(bg)
for fi,f in enumerate(parishes['features']):
 if fi%500==0:print('Join',fi,flush=True)
 p=f['properties'];g=geom(f);code=p['dtmnfr'];pr=lookup.get(code);og=oldgeoms.get(code)
 iou=g.intersection(og).area/g.union(og).area if og is not None else 0
 compatible=iou>=.995
 p.update(population_2021=exact.get(code,pr['residents'] if compatible and pr else None),children_0_14=pr['children'] if compatible and pr else None,elderly_65_plus=pr['elderly'] if compatible and pr else None,vulnerable_age_count=(pr['children']+pr['elderly']) if compatible and pr else None,geography_compatibility_iou=round(iou,5),population_source='INE 0014584' if code in exact else 'BGRI2021 / CAOP2021, compatibilidade geométrica >=99,5%' if compatible else 'harmonização pendente',exposed_population=None,vulnerable_count=None)
 if p['population_2021'] is None:report['population_missing']+=1
 else:report['population_matched']+=1
 if not compatible:report['geography_review']+=1
 p['basin_ids']=[str(basins['features'][int(i)]['properties']['objectid']) for i in btree.query(g,predicate='intersects')]
 for t in scenarios:
  ids=trees[t].query(g,predicate='intersects');features=[scenarios[t]['features'][int(i)] for i in ids];p['risk_t'+str(t)]=max((rank.get(sf['properties']['risco'],0) for sf in features),default=0) or None;p['sites_t'+str(t)]=sorted(set(sf['properties']['local'] for sf in features))
 p['scenario_risk']=p['risk_t100'];p['scenario_sites']=p['sites_t100']
 f['geometry']=mapping(g.simplify(.00015,preserve_topology=True))
write('parishes.geojson',parishes)
for t,j in scenarios.items():
 for i,f in enumerate(j['features']):f['geometry']=mapping(geoms[t][i].simplify(.00010,preserve_topology=True))
 j['display_simplification_degrees']=.00010;j['note']='Cartografia de cenário APA; geometrias simplificadas para visualização. Não é mancha atual.';write({20:'risk20.geojson',100:'risk.geojson',1000:'risk1000.geojson'}[t],j)
for f,g in zip(basins['features'],bg):f['geometry']=mapping(g.simplify(.0002,preserve_topology=True))
report['prototype_spatial_tolerance_degrees']=.0001;report['note']='Triagem com geometria simplificada; confirmar interseções de fronteira em dados analíticos originais para publicação científica.'
write('basins.geojson',basins);write('build-report.json',report);print(json.dumps(report,ensure_ascii=False))
