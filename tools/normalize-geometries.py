import sys,pathlib,json
sys.path.insert(0,str(pathlib.Path('research/python').resolve()))
from shapely.geometry import shape,mapping,MultiPolygon
from shapely.ops import unary_union
D=pathlib.Path('dist/data');stats={}
def polygons(g):
 if g.geom_type=='Polygon':return [g] if g.area>0 else []
 if hasattr(g,'geoms'):return [p for sub in g.geoms for p in polygons(sub)]
 return []
for name in ['risk20.geojson','risk.geojson','risk1000.geojson']:
 j=json.loads((D/name).read_text(encoding='utf-8'));out=[];removed=0
 for f in j['features']:
  parts=polygons(shape(f['geometry']))
  if not parts:removed+=1;continue
  g=unary_union(parts)
  if g.geom_type not in ['Polygon','MultiPolygon']:raise RuntimeError('Non-polygonal union')
  f['geometry']=mapping(g);out.append(f)
 stats[name]={'input':len(j['features']),'areal_features':len(out),'collapsed_non_areal_removed':removed};j['features']=out;j['geometry_policy']='Areal components retained; line/point remnants from source service quantization removed. Display/approximate exposure only; native analytical geometry required for scientific validation.'
 (D/name).write_text(json.dumps(j,separators=(',',':'),ensure_ascii=False),encoding='utf-8')
(D/'geometry-report.json').write_text(json.dumps(stats,indent=2),encoding='utf-8');print(json.dumps(stats))
