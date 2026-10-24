"""Frozen historical screening against EMSR417, not an operational validation.
Run from repository root after extracting the official vector ZIP to research/emsr417.
Uses the existing pilot equations, geometry and assumptions without fitting to the image.
"""
import sys,pathlib,json,csv,hashlib,datetime
ROOT=pathlib.Path('.');sys.path[:0]=[str(ROOT/'research/python'),str(ROOT/'engine')]
import numpy as np
import rasterio.features
from rasterio.transform import Affine
from shapely.geometry import shape,mapping,LineString
from shapely.ops import transform,unary_union
from shapely import points,distance,make_valid
from pyproj import Transformer
from hydraulics import solve_stage,section_properties,terrain_footprint
from validation import overlap_metrics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

DATA=ROOT/'dist/data';OUT=ROOT/'dist/analysis';OUT.mkdir(exist_ok=True)
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def write(p,j):pathlib.Path(p).write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
src=ROOT/'research/emsr417';cfg=read('engine/pilot.json');t=np.load('engine/terrain/coimbra.npz');aff=Affine(*t['transform'])
xy_crs=Transformer.from_crs(4326,3763,always_xy=True).transform;ll=Transformer.from_crs(3763,4326,always_xy=True).transform
def layer(name):
    j=read(next(src.glob('*_'+name+'_*.json')))
    return unary_union([make_valid(transform(xy_crs,shape(f['geometry']))) for f in j['features'] if f['geometry']])
observed=layer('observedEventA');aoi=layer('areaOfInterestA');image=layer('imageFootprintA');permanent=layer('hydrographyA')
line=LineString(t['line_xy']);coverage=line.buffer(cfg['section_half_width_m']);common=coverage.intersection(aoi).intersection(image)
h,w=t['dem'].shape;rr,cc=np.indices((h,w));gx=aff.c+(cc+.5)*aff.a;gy=aff.f+(rr+.5)*aff.e;xy=np.column_stack([gx.ravel(),gy.ravel()])
dist=distance(line,points(xy[:,0],xy[:,1])).reshape((h,w));channel=dist<=cfg['estimated_channel_width_m']/2;seed=dist<=cfg['grid_m']*.85;corridor=dist<=cfg['section_half_width_m']
def raster(g):return rasterio.features.geometry_mask([mapping(g)],out_shape=(h,w),transform=aff,invert=True) if not g.is_empty else np.zeros((h,w),bool)
domain=raster(common)&~channel&~raster(permanent);obs=raster(observed)&domain
idx=[];weights=[]
for start in range(0,len(xy),5000):
    d=np.sum((xy[start:start+5000,None,:]-t['centres'][None,:,:])**2,axis=2);ii=np.argpartition(d,2,axis=1)[:,:3];dd=np.take_along_axis(d,ii,axis=1);ww=1/np.maximum(1.,dd);ww/=ww.sum(axis=1,keepdims=True);idx.append(ii);weights.append(ww)
idx=np.vstack(idx);weights=np.vstack(weights)
def field(v):return np.sum(np.asarray(v)[idx]*weights,axis=1).reshape((h,w))
dem=t['dem'].astype(float).copy();bed=field(t['bed']);dem[channel]=np.minimum(dem[channel],bed[channel]);x=t['offsets'];slope=float(t['slope']);width=cfg['estimated_channel_width_m'];n=cfg['manning_channel'];nf=cfg['manning_floodplain'];cell=cfg['grid_m']**2
capacity=float(min(section_properties(x,z,level,slope,width,n,nf)[0] for z,level in zip(t['profiles'],t['water_reference'])))
rows=list(csv.DictReader(open(DATA/'coimbra-weir-daily.csv',encoding='utf-8')))
windows=[('2001-01','2001-01-01','2001-01-31'),('2016-01','2016-01-09','2016-01-13'),('2016-02','2016-02-12','2016-02-15'),('2019-12','2019-12-19','2019-12-24')]
events=[]
for label,start,end in windows:
    available=[r for r in rows if start<=r['date']<=end and r['discharged_daily_m3s'] and r['flags_present']=='0']
    if available:
        peak=max(available,key=lambda r:float(r['discharged_daily_m3s']));events.append({'event':label,'date':peak['date'],'q_daily_m3s':float(peak['discharged_daily_m3s']),'reference_extent_available':label=='2019-12'})
same=next(r for r in rows if r['date']=='2019-12-23');events.append({'event':'2019-image-day','date':same['date'],'q_daily_m3s':float(same['discharged_daily_m3s']),'reference_extent_available':True})
results=[];preds={}
for event in events:
    for hours in [6,24]:
        q=event['q_daily_m3s'];levels=[solve_stage(x,z,q,slope,width,n,nf)[0] for z in t['profiles']]
        budget=max(0.,q-capacity)*hours*3600
        depth,mask,storage=terrain_footprint(dem,field(levels),channel,seed,corridor,cell,cfg['minimum_mapped_overbank_depth_m'],budget)
        item={**event,'duration_assumed_h':hours,'overbank_area_m2':int(mask.sum()*cell),'volume_diagnostics':storage,'instantaneous_hydrograph_available':False}
        if event['reference_extent_available']:
            item['comparison']=overlap_metrics(mask,obs,domain,cell)
            item['observed_recall_with_60m_simulation_tolerance']=float((obs&raster(unary_union([shape(g) for g,v in rasterio.features.shapes(mask.astype('uint8'),mask=mask&domain,transform=aff)]).buffer(60))).sum()/obs.sum()) if obs.any() else None
        results.append(item);preds[(event['event'],hours)]=mask
        if event['event']=='2019-image-day' and hours==24:
            features=[{'type':'Feature','geometry':mapping(transform(ll,shape(g))),'properties':{'date':'2019-12-23','scenario':'daily_mean_24h_screening','operationally_accepted':False}} for g,v in rasterio.features.shapes(mask.astype('uint8'),mask=mask,transform=aff)]
            write(DATA/'coimbra-hindcast-2019.geojson',{'type':'FeatureCollection','features':features})
clipobs=observed.intersection(common).difference(permanent).difference(line.buffer(width/2))
write(DATA/'coimbra-observed-2019.geojson',{'type':'FeatureCollection','source':'© European Union, Copernicus EMS EMSR417 AOI01 v1','observation_time_utc':'2019-12-23T06:43:00Z','features':[{'type':'Feature','geometry':mapping(transform(ll,clipobs)),'properties':{'kind':'satellite_detected_flood','not_peak_envelope':True}}]})
# Exposure comparison uses the same census and administrative geometry for both masks.
# A containing BGRI unit's whole population is an upper allocation bound, not an estimate.
bgri=read('.cache/bgri-coimbra.geojson');units=[(make_valid(transform(xy_crs,shape(f['geometry']))),f['properties']) for f in bgri['features']]
sim=unary_union([shape(g) for g,v in rasterio.features.shapes(preds[('2019-image-day',24)].astype('uint8'),mask=preds[('2019-image-day',24)]&domain,transform=aff)])
exposure=[]
for f in read(DATA/'parishes.geojson')['features']:
    pg=make_valid(transform(xy_crs,shape(f['geometry'])));og=pg.intersection(clipobs);sg=pg.intersection(sim)
    if og.area<1 and sg.area<1:continue
    row={'properties':f['properties'],'observed_flood_area_m2':og.area,'simulated_flood_area_m2':sg.area}
    for name,geom in [('observed',og),('simulated',sg)]:
        sums=[0.,0.,0.];upper=[0.,0.,0.];missing=False
        for unit,p in units:
            if unit.is_empty or unit.area<=0 or not unit.intersects(geom):continue
            area=unit.intersection(geom).area
            if area<=0:continue
            vals=[p.get(k) for k in ['N_INDIVIDUOS','N_INDIVIDUOS_0_14','N_INDIVIDUOS_65_OU_MAIS']]
            if any(v is None or v<0 for v in vals):missing=True;continue
            for i,v in enumerate(vals):sums[i]+=v*area/unit.area;upper[i]+=v
        covered=unary_union([u for u,p in units if u.intersects(geom)]).intersection(geom).area if not geom.is_empty else 0
        coverage_ratio=covered/geom.area if geom.area else None
        if geom.area and coverage_ratio<.999:missing=True
        row[name+'_census2021']={'uniform_area_estimates':None if missing else sums,'intersected_units_upper_allocation_bounds':None if missing else upper,'lower_allocation_bounds':[0,0,0],'missing_census':missing,'spatial_coverage_fraction':coverage_ratio,'order':['residents','children_0_14','age65plus'],'not_event_population':True}
    exposure.append(row)
source_url='https://cems-mapping-website.s3.eu-west-1.amazonaws.com/static/activations/EMSR417/EMSR417_AOI01_DEL_PRODUCT_r1_RTP01_v1_vector.zip'
report={'schema':'coimbra-historical-validation/1','computed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'diagnostic_comparison_not_operational_validation','operationally_accepted':False,'source_url':source_url,'source_zip_sha256':hashlib.sha256((ROOT/'research/emsr417-vector.zip').read_bytes()).hexdigest(),'source_attribution':'© European Union, Copernicus Emergency Management Service, EMSR417 AOI01 delineation v1','observation_time_utc':'2019-12-23T06:43:00Z','satellite':'Sentinel-1A SAR 10m; source geometric RMSE <=12.5m; thematic accuracy lower in urban/forest areas','comparison_grid_m':30,'assumed_bank_capacity_m3s':capacity,'observed_all_aoi_m2':observed.area,'observed_pilot_common_overbank_m2':clipobs.area,'image_coverage_of_pilot_fraction':common.area/coverage.area,'events':results,'parish_exposure':exposure,'limitations':['Daily weir discharge used uniformly throughout a 16 km branched reach; not routed historical instantaneous inflows','6h/24h durations are assumed sensitivity scenarios, not measured flood duration','Image acquired after event peaks; event-maximum comparison asynchronous and not a validation score','SAR nondetection does not prove dry ground; no confirmed dry control sample','Permanent mapped water and assumed 150m channel excluded; channel geometry uncertain','2019 flood involved dike breaches; pilot has no breach, bridge, weir/backwater or unsteady dynamics','No current bathymetry or reconciled vertical datums','BGRI2021/CAOP2025 applied retrospectively: exposure estimates, not people affected in 2019; children/elderly only partial vulnerability proxies','2001 and 2016 lack imported timestamped independent observed extent; no spatial metrics assigned']}
write(DATA/'coimbra-validation.json',report)
with open(OUT/'coimbra-historical-comparison.csv','w',newline='',encoding='utf-8') as f:
    fields=['event','date','q_daily_m3s','duration_assumed_h','overbank_area_m2','iou_diagnostic','observed_recall_diagnostic','simulation_precision_diagnostic'];wr=csv.DictWriter(f,fieldnames=fields);wr.writeheader()
    for row in results:wr.writerow({k:row.get(k,row.get('comparison',{}).get(k)) for k in fields})
fig,axes=plt.subplots(1,2,figsize=(13,6),layout='constrained');extent=[gx.min(),gx.max(),gy.min(),gy.max()]
for ax,(label,key) in zip(axes,[('23 dez.: caudal médio diário, 24h',('2019-image-day',24)),('Máximo médio diário do evento, 24h',('2019-12',24))]):
    p=preds[key]&domain;cat=np.full((h,w),np.nan);cat[obs&~p]=1;cat[p&~obs]=2;cat[p&obs]=3
    ax.imshow(t['dem'],extent=extent,cmap='Greys',origin='upper',alpha=.3);ax.plot(*line.xy,color='#777777',lw=.6,alpha=.65);ax.imshow(cat,extent=extent,cmap=matplotlib.colors.ListedColormap(['#e69f00','#0072b2','#009e73']),vmin=1,vmax=3,origin='upper',interpolation='nearest');ax.set_title(label);ax.set_xlabel('ETRS89 / PT-TM06 — m');ax.ticklabel_format(style='plain',useOffset=False)
fig.legend(handles=[Patch(color='#e69f00',label='Só observado SAR'),Patch(color='#0072b2',label='Só simulado'),Patch(color='#009e73',label='Interseção')],loc='outside lower center',ncol=3)
fig.suptitle('Confronto exploratório · imagem 23/12/2019 06:43 UTC\nMáximo do evento não coincide com a imagem; ausência SAR não prova solo seco',fontsize=12)
fig.savefig('dist/figures/13_validacao_2019.png',dpi=160);plt.close(fig)
print(json.dumps({'events':[{k:r.get(k,r.get('comparison',{}).get(k)) for k in ['event','duration_assumed_h','q_daily_m3s','overbank_area_m2','iou_diagnostic','observed_recall_diagnostic']} for r in results],'observed_pilot_ha':clipobs.area/10000,'parishes':len(exposure),'accepted':False}))
