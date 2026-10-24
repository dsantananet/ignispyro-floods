import sys,pathlib,json,datetime
sys.path.insert(0,str(pathlib.Path('engine').resolve()))
from coimbra_weir import integrate_boundary_volume,terminal_release_sum
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
t=read('dist/data/snirh-telemetry.json');stations={s['id']:s for s in t['stations']};now=datetime.datetime.now(datetime.timezone.utc)
def series(id,q):return next((p for p in stations.get(id,{}).get('series',[]) if p['quantity']==q),{})
def recent(id,q):
 p=series(id,q).get('latest')
 if not p:return None
 age=(now-datetime.datetime.fromisoformat(p['observed_at'].replace('Z','+00:00'))).total_seconds()
 return p if -360<=age<=10800 else None
def rates(q):return {datetime.datetime.fromisoformat(p['observed_at'].replace('Z','+00:00')).timestamp():p['value'] for p in series('1627743374',q).get('rows',[])}
weir={q:recent('1627743374',q) for q in ['inflow_m3s','outflow_m3s','elevation_m']}
terminal={'raiva':recent('1627759328','outflow_m3s'),'fronhas':recent('1627758668','outflow_m3s'),'ceira_conraria':recent('1627759068','flow_m3s')}
times=[p['observed_at'] for p in terminal.values() if p];synchronized=len(set(times))==1 and len(times)==3
total=terminal_release_sum(*[p['value'] if p else None for p in terminal.values()]) if synchronized else None
j={'schema_version':'floods-coimbra-boundaries/1','computed_at':now.isoformat(),'source_retrieved_at':t['retrieved_at'],'weir_observed_boundary':weir,'terminal_release_observations':terminal,'terminal_sum_m3s':total,'terminal_sum_usable':False,'routing_status':'travel times, ungauged inflows, abstractions and flood storage unresolved; simultaneous sum is diagnostic only','no_double_counting':'Aguieira is internal to the Aguieira-Raiva cascade; its release is not added again','weir_volume_budget':integrate_boundary_volume(rates('inflow_m3s'),rates('outflow_m3s')),'gate_regime':'unknown','bathymetry_status':'historical drawings and 2010 project profile located; no verified current XYZ/sections imported','terrain_vertical_transform':None,'operational_inundation_allowed':False,'blocked_by':['gate position and downstream tailwater missing','current bathymetry not verified','vertical datum reconciliation missing','spatial hydraulic calibration and independent flood extent validation missing'],'integration_status':'observed releases integrated into boundary/continuity diagnostics; spatial footprint deliberately gated'}
pathlib.Path('dist/data/coimbra-boundaries.json').write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')),encoding='utf-8');print(json.dumps({'boundary_observations':sum(p is not None for p in weir.values()),'operational_inundation_allowed':False}))
