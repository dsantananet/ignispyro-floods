"""Run a dated, explicitly experimental Coimbra hydraulic estimate."""
import sys,pathlib,json,datetime,urllib.request,math,warnings
sys.path.insert(0,str(pathlib.Path('research/python').resolve()))
import numpy as np
import rasterio,rasterio.features
from rasterio.transform import Affine
from shapely.geometry import shape,mapping,LineString,Point,box
from shapely.ops import transform as transform_geometry,unary_union
from shapely import points as make_points,distance as geom_distance
from pyproj import Transformer
from hydraulics import solve_stage,section_properties,linear_reservoir,terrain_footprint
warnings.filterwarnings('ignore',category=DeprecationWarning)
ROOT=pathlib.Path('.');DATA=ROOT/'dist/data';CACHE=ROOT/'.cache';CACHE.mkdir(exist_ok=True)
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def write(p,j):pathlib.Path(p).write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
def remote(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'IgnispyroFloods-research/0.2'}),timeout=60) as r:return json.load(r)
cfg=read('engine/pilot.json');terrain=np.load('engine/terrain/coimbra.npz');meta=read('engine/terrain/coimbra.json');now=datetime.datetime.now(datetime.timezone.utc);valid=now.replace(minute=0,second=0,microsecond=0)
flowurl='https://flood-api.open-meteo.com/v1/flood?latitude=40.206&longitude=-8.431&past_days=3&forecast_days=3&daily=river_discharge&timezone=GMT'
try:
 flow=remote(flowurl)
 if flow.get('error'):raise ValueError(flow.get('reason'))
 flow['retrieved_at']=now.isoformat();write(CACHE/'coimbra-flow.json',flow)
except Exception:
 flow=read(CACHE/'coimbra-flow.json')
 if (now-datetime.datetime.fromisoformat(flow['retrieved_at'])).total_seconds()>86400:raise RuntimeError('River model unavailable and cached daily input older than 24h')
days=flow['daily']['time'];values=flow['daily']['river_discharge'];today=valid.date().isoformat()
if today not in days:raise RuntimeError('Current model day missing')
model_current=values[days.index(today)]
if model_current is None or not np.isfinite(model_current):raise RuntimeError('Missing model discharge')
sim=read(DATA/'simulation.json');estimate=read(DATA/'rainfall-estimates.json');rain=next(b for b in sim['basins'] if b['id']==cfg['local_rainfall_basin_id']);modelrain=next(b for b in estimate['basins'] if b['id']==rain['id']);cn=cfg['runoff_differential_cn']
def runoff(p):
 if p is None:return None
 s=25400/cn-254
 return 0. if p<=.2*s else (p-.2*s)**2/(p+.8*s)
correction=0.;delta_volume=0.;rain_assimilated=False
if not rain['modelled_rainfall'] and rain['p24_mm'] is not None and modelrain['p24_mm'] is not None:
 delta_volume=(runoff(rain['p24_mm'])-runoff(modelrain['p24_mm']))*rain['area_km2']*1000
 correction=cfg['observed_runoff_differential_weight']*delta_volume/86400;rain_assimilated=True
start=valid-datetime.timedelta(hours=72);times=[start+datetime.timedelta(hours=i) for i in range(73)];incoming=[]
for t in times:
 day=t.date().isoformat()
 if day not in days or values[days.index(day)] is None:raise RuntimeError('Missing daily model flow for routing')
 q=float(values[days.index(day)])+(correction if t>valid-datetime.timedelta(hours=24) else 0);incoming.append(max(0.,q))
x=terrain['offsets'];profiles=terrain['profiles'];centres=terrain['centres'];slope=float(terrain['slope']);width=cfg['estimated_channel_width_m'];n=cfg['manning_channel'];nf=cfg['manning_floodplain'];qref=read(DATA/'t10.json');q10=next(r for r in qref['stations'] if r['id']==cfg['reference_station'])['q10_gumbel_moments_m3s']
initial_sections=[solve_stage(x,z,max(.001,incoming[0]),slope,width,n,nf) for z in profiles];velocity=max(.1,float(np.median([a[2] for a in initial_sections])));response=max(1800,min(86400,meta['reach_length_m']/velocity));routed,balance=linear_reservoir(incoming,3600,response);current=float(routed[-1]);bank_capacity=float(min(section_properties(x,z,h,slope,width,n,nf)[0] for z,h in zip(profiles,terrain['water_reference'])));available=float(sum(max(0,q-bank_capacity)*3600 for q in routed))
height,gridwidth=terrain['dem'].shape;aff=Affine(*terrain['transform']);rr,cc=np.indices((height,gridwidth));gx=aff.c+(cc+.5)*aff.a;gy=aff.f+(rr+.5)*aff.e;xy=np.column_stack([gx.ravel(),gy.ravel()]);idxs=[];weights=[]
for offset in range(0,len(xy),5000):
 d=np.sum((xy[offset:offset+5000,None,:]-centres[None,:,:])**2,axis=2);ii=np.argpartition(d,2,axis=1)[:,:3];dd=np.take_along_axis(d,ii,axis=1);w=1/np.maximum(1.,dd);w/=w.sum(axis=1,keepdims=True);idxs.append(ii);weights.append(w)
idxs=np.vstack(idxs);weights=np.vstack(weights)
def field(values):return np.sum(np.asarray(values)[idxs]*weights,axis=1).reshape((height,gridwidth))
line=LineString(terrain['line_xy']);distance=geom_distance(line,make_points(xy[:,0],xy[:,1])).reshape((height,gridwidth));channel=distance<=width/2;seed=distance<=cfg['grid_m']*.85;corridor=distance<=cfg['section_half_width_m'];dem=terrain['dem'].astype(float).copy();bedgrid=field(terrain['bed']);dem[channel]=np.minimum(dem[channel],bedgrid[channel]);cellarea=cfg['grid_m']**2
to_ll=Transformer.from_crs(3763,4326,always_xy=True).transform;to_xy=Transformer.from_crs(4326,3763,always_xy=True).transform
def compute_frame(q,volume_budget,tag,incision_delta=0.):
 pp=profiles.copy();within=abs(x)<=width/2;pp[:,within]-=incision_delta
 sections=[solve_stage(x,z,q,slope,width,n,nf) for z in pp];levels=[a[0] for a in sections];water=field(levels);local_dem=dem.copy();local_dem[channel]-=incision_delta
 depth,mask,storage=terrain_footprint(local_dem,water,channel,seed,corridor,cellarea,cfg['minimum_mapped_overbank_depth_m'],volume_budget)
 velocity=(1/nf)*np.maximum(depth,0.)**(2/3)*math.sqrt(slope);intensity=depth*(velocity+.5);classes=np.select([intensity<.75,intensity<1.25,intensity<2.5,intensity<=7],[1,2,3,4],default=5).astype('uint8');classes[~mask]=0;features=[];areas=[]
 for geometry,klass in rasterio.features.shapes(classes,mask=mask,transform=aff,connectivity=4):
  g=shape(geometry)
  if g.is_empty:continue
  pixels=rasterio.features.geometry_mask([geometry],out_shape=mask.shape,transform=aff,invert=True)&mask;polygon=transform_geometry(to_ll,g.simplify(3,preserve_topology=True));areas.append(g)
  features.append({'type':'Feature','geometry':mapping(polygon),'properties':{'frame':tag,'hazard_class':int(klass),'depth_mean_m':round(float(depth[pixels].mean()),3),'depth_max_m':round(float(depth[pixels].max()),3),'velocity_estimated_mean_m_s':round(float(velocity[pixels].mean()),3),'area_m2':round(g.area,1),'connected_to_river':True,'experimental':True,'valid_time':valid.isoformat()}})
 refpoint=transform_geometry(to_xy,Point(cfg['reference_point_wgs84']));refindex=int(np.argmin(np.sum((centres-np.array([refpoint.x,refpoint.y]))**2,axis=1)))
 summary={'tag':tag,'discharge_m3s':q,'reference_water_level_m_egm2008':levels[refindex]-storage['stage_reduction_for_volume_constraint_m'],'reference_depth_above_assumed_bed_m':levels[refindex]-float(terrain['bed'][refindex])+incision_delta-storage['stage_reduction_for_volume_constraint_m'],'water_level_min_m_egm2008':min(levels),'water_level_max_m_egm2008':max(levels),'mean_cross_section_velocity_m_s':float(np.mean([a[2] for a in sections])),'overbank_area_m2':int(mask.sum()*cellarea),'overbank_max_depth_m':float(depth[mask].max()) if mask.any() else 0.,'inundated_polygons':len(features),**storage}
 return {'type':'FeatureCollection','features':features,'summary':summary},areas,depth,mask
current_frame,current_polygons,current_depth,current_mask=compute_frame(current,available,'current_estimate');q10_budget=max(0.,q10-bank_capacity)*6*3600;q10_frame,q10_polygons,_,_=compute_frame(q10,q10_budget,'q10_six_hour_sensitivity')
sensitivity=[]
for delta in [-1.,1.]:
 frame,_,_,_=compute_frame(current,available,'channel_incision_sensitivity',delta);sensitivity.append({'channel_incision_m':cfg['estimated_channel_incision_m']+delta,**frame['summary']})

def census_population(geometries,physical_frame):
 if not geometries:return {'type':'FeatureCollection','features':[],'note':'No modelled overbank polygon in this frame; outside pilot remains unknown.'}
 mask=unary_union(geometries);cache=CACHE/'bgri-coimbra.geojson'
 if cache.exists():bgri=read(cache)
 else:
  base='https://services.arcgis.com/CCZiGSEQbAxxFVh3/ArcGIS/rest/services/BGRI_Censos_2021/FeatureServer/3/query';records=[];offset=0
  while True:
   from urllib.parse import urlencode
   query=urlencode({'f':'geojson','where':'1=1','geometry':','.join(map(str,cfg['bbox_wgs84'])),'geometryType':'esriGeometryEnvelope','inSR':4326,'outSR':4326,'spatialRel':'esriSpatialRelIntersects','outFields':'BGRI2021,N_INDIVIDUOS,N_INDIVIDUOS_0_14,N_INDIVIDUOS_65_OU_MAIS','resultRecordCount':1000,'resultOffset':offset,'orderByFields':'OBJECTID','returnGeometry':'true'})
   batch=remote(base+'?'+query)
   if batch.get('error') or 'features' not in batch:raise RuntimeError('BGRI query failed')
   records+=batch['features']
   if not batch.get('exceededTransferLimit') and len(batch['features'])<1000:break
   offset+=len(batch['features'])
   if offset>50000:raise RuntimeError('Excessive pilot BGRI count')
  bgri={'type':'FeatureCollection','features':records,'source_url':base};write(cache,bgri)
 units=[]
 for f in bgri['features']:
  g=transform_geometry(to_xy,shape(f['geometry']))
  if g.area and g.intersects(mask):units.append((g,f['properties']))
 parishes=read(DATA/'parishes.geojson');features=[];matrix=[[1,1,2,2,3],[1,2,3,3,4],[2,3,3,4,4],[2,3,4,4,5],[3,4,4,5,5]]
 for f in parishes['features']:
  g=transform_geometry(to_xy,shape(f['geometry']))
  if not g.intersects(mask):continue
  flood=g.intersection(mask)
  if flood.area<1:continue
  total=young=old=0.;missing=False
  for unit,p in units:
   if not unit.intersects(flood):continue
   ratio=unit.intersection(flood).area/unit.area
   if ratio<=0:continue
   vals=[p.get(k) for k in ['N_INDIVIDUOS','N_INDIVIDUOS_0_14','N_INDIVIDUOS_65_OU_MAIS']]
   if any(v is None or v<0 for v in vals):missing=True;continue
   total+=vals[0]*ratio;young+=vals[1]*ratio;old+=vals[2]*ratio
  hazard=0
  for fp in physical_frame['features']:
   if g.intersects(transform_geometry(to_xy,shape(fp['geometry']))):hazard=max(hazard,fp['properties']['hazard_class'])
  if not hazard:hazard=1
  consequence=1 if total<1 else 2 if total<=10 else 3 if total<=100 else 4 if total<=1000 else 5
  p={**f['properties'],'exposed_residents_estimate':None if missing else round(total,2),'exposed_children_estimate':None if missing else round(young,2),'exposed_elderly_estimate':None if missing else round(old,2),'flooded_area_m2':round(flood.area,1),'hazard_class':hazard,'experimental_risk_class':None if missing else matrix[consequence-1][hazard-1],'consequence_class_experimental':consequence,'population_method':'BGRI2021 uniform area weighting in EPSG3763; no live population','missing_census':missing,'experimental':True}
  features.append({'type':'Feature','geometry':f['geometry'],'properties':p})
 return {'type':'FeatureCollection','features':features,'source':'BGRI2021 public hosted copy; CAOP2025 approximate display geometry','note':'Risk matrix combines estimated physical hazard and experimental exposure bins 0/10/100/1000. Not an official or validated risk score.'}
exposed=census_population(current_polygons,current_frame);exposed_q10=census_population(q10_polygons,q10_frame)
coverage_geom=transform_geometry(to_ll,line.buffer(cfg['section_half_width_m']))
coverage={'type':'FeatureCollection','features':[{'type':'Feature','geometry':mapping(coverage_geom),'properties':{'pilot_id':cfg['id'],'status':'experimental_estimate','grid_m':cfg['grid_m']}}]}
result={'schema_version':'floods-hydraulic-pilot/1','status':'experimental_normal_flow_connected_terrain_screening','calibrated':False,'computed_at':now.isoformat(),'valid_time':valid.isoformat(),'source_discharge_resolution':'daily model discharge, held constant within each UTC day, then routed hourly','source_discharge_model':'GloFAS via Open-Meteo; not an observed gauge','discharge_source_url':flowurl,'discharge_retrieved_at':flow['retrieved_at'],'model_grid':[flow['longitude'],flow['latitude']],'glofas_current_daily_m3s':model_current,'observed_rainfall_correction_applied':rain_assimilated,'runoff_volume_difference_m3':delta_volume,'runoff_differential_weight':cfg['observed_runoff_differential_weight'],'rainfall_correction_m3s':correction,'assumed_bank_capacity_m3s':bank_capacity,'reservoir_releases_assimilated':False,'current':current_frame['summary'],'q10_six_hour_sensitivity':q10_frame['summary'],'channel_depth_sensitivity':sensitivity,'routing_mass_balance':balance,'terrain':meta,'assumptions':cfg,'affected_parishes_count':len(exposed['features']),'method_limits':['Normal-flow equilibrium per section; not full unsteady Saint-Venant or 2D momentum solution','DSM is surface elevation, with assumed channel incision and roughness; not surveyed bathymetry','Measured reservoir releases not assimilated; weir gates, bridges and downstream backwater unresolved','Mapped overbank storage bounded by an accumulated spill-volume upper bound; no calibrated floodplain drainage','Local runoff differential is exploratory bias correction, not calibrated data assimilation','No operational alert is issued by this research pilot']}
if (DATA/'snirh-telemetry.json').exists():
 telemetry=read(DATA/'snirh-telemetry.json');result['real_telemetry_connected']=True;result['real_telemetry_retrieved_at']=telemetry['retrieved_at'];result['real_telemetry_station_ids']=[r['id'] for r in telemetry['stations'] if r['basin']=='Mondego'];result['observation_assimilation_status']='not_assimilated_pending_calibration_datum_and_cascade_routing'
result['q10_six_hour_sensitivity']['intersected_parishes']=len(exposed_q10['features']);result['q10_six_hour_sensitivity']['exposed_residents_estimate']=sum(f['properties']['exposed_residents_estimate'] or 0 for f in exposed_q10['features']);result['q10_six_hour_sensitivity']['exposed_children_estimate']=sum(f['properties']['exposed_children_estimate'] or 0 for f in exposed_q10['features']);result['q10_six_hour_sensitivity']['exposed_elderly_estimate']=sum(f['properties']['exposed_elderly_estimate'] or 0 for f in exposed_q10['features'])
for name,data in [('hydraulic-current.geojson',current_frame),('hydraulic-q10.geojson',q10_frame),('hydraulic-parishes.geojson',exposed),('hydraulic-q10-parishes.geojson',exposed_q10),('hydraulic-coverage.geojson',coverage),('hydraulic-pilot.json',result)]:write(DATA/name,data)
with rasterio.open(DATA/'hydraulic-current-depth.tif','w',driver='GTiff',height=height,width=gridwidth,count=1,dtype='float32',crs=3763,transform=aff,nodata=-9999,compress='deflate') as dst:
 layer=np.where(corridor&~channel,np.where(current_mask,current_depth,0),-9999).astype('float32');dst.write(layer,1);dst.update_tags(description='Experimental estimated OVERBANK depth, not channel depth. Current input is model discharge, not observed stage.',valid_time=valid.isoformat(),calibrated='false',vertical_datum=cfg['terrain_vertical_datum'])
np.savez_compressed(CACHE/'hydraulic-coimbra-current.npz',depth=current_depth,mask=current_mask,dem=dem,transform=np.array(tuple(aff)[:6]))
print(json.dumps({'current_q_m3s':current,'bank_capacity_m3s':bank_capacity,'current_overbank_m2':current_frame['summary']['overbank_area_m2'],'q10_overbank_m2':q10_frame['summary']['overbank_area_m2'],'affected_parishes':len(exposed['features']),'mass_balance_error_m3':balance['mass_balance_error_m3'],'calibrated':False},ensure_ascii=False))
