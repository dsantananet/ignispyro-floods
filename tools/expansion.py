"""Geographic coverage inventory. A point in a basin does not prove network representativeness."""
import sys,pathlib,json,datetime
sys.path.insert(0,str(pathlib.Path('research/python').resolve()))
from shapely.geometry import shape
from shapely.ops import unary_union
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
t=read('dist/data/snirh-telemetry.json');basins=read('dist/data/basins.geojson');pilot=unary_union([shape(f['geometry']) for f in read('dist/data/hydraulic-coverage.geojson')['features']]);now=datetime.datetime.now(datetime.timezone.utc)
stations=[]
for s in t['stations']:
 fresh=[]
 for q in s['series']:
  p=q['latest']
  if p and -360<=(now-datetime.datetime.fromisoformat(p['observed_at'].replace('Z','+00:00'))).total_seconds()<=10800:fresh.append(q['quantity'])
 stations.append((shape(s['geometry']),s['id'],fresh))
features=[]
for f in basins['features']:
 g=shape(f['geometry']);inside=[s for s in stations if g.covers(s[0])];count=lambda q:sum(q in s[2] for s in inside)
 p={**f['properties'],'telemetry_station_ids':[s[1] for s in inside],'fresh_level_points':count('level_m'),'fresh_flow_points':count('flow_m3s'),'fresh_release_points':count('outflow_m3s'),'experimental_pilot_intersects':g.intersects(pilot),'operational_hydraulic_ready':False,'status':'observations_only' if any(s[2] for s in inside) else 'additional_observations_required','geographic_join_only':True,'next_steps':['verify upstream network and lateral inflows','survey terrain, bathymetry, gates and vertical datum','calibrate and independently validate flood events','intersect accepted dated inundation with CAOP/BGRI']}
 features.append({'type':'Feature','geometry':f['geometry'],'properties':p})
result={'type':'FeatureCollection','computed_at':now.isoformat(),'scope':'262 APA mainland level-3 basins; Azores and Madeira require regional data','note':'Point-in-polygon inventory only, not hydrological coverage or national flood hazard','features':features}
pathlib.Path('dist/data/national-expansion.geojson').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print(json.dumps({'basins':len(features),'with_recent_geographic_points':sum(f['properties']['status']=='observations_only' for f in features),'operational_ready':0}))
