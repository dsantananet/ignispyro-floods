"""MDT (Copernicus GLO-30) -> per-parish height-above-nearest-drainage share. Needs network (S3 COG tiles).
Output: dist/data/terrain-susceptibility.json. Optional input of tools/floodwatch.cjs; absent file = component skipped."""
import sys,json,pathlib,datetime,os
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent/'engine'))
os.environ.setdefault('AWS_NO_SIGN_REQUEST','YES');os.environ.setdefault('GDAL_DISABLE_READDIR_ON_OPEN','EMPTY_DIR')
import numpy as np,rasterio,rasterio.features
from rasterio.transform import from_origin
from rasterio.warp import reproject,Resampling
from shapely.geometry import shape
from terrain import parish_terrain_stats,roc_auc
D=pathlib.Path('dist/data');RES=0.0009;W,E,S,N=-9.6,-6.1,36.9,42.2
width=int(round((E-W)/RES));height=int(round((N-S)/RES));aff=from_origin(W,N,RES,RES)
load=lambda n:json.loads((D/n).read_text(encoding='utf-8-sig'))
dem=np.full((height,width),np.nan,dtype='float32');used=[]
for lat in range(36,42):
    for lon in range(-10,-6):
        name=f'Copernicus_DSM_COG_10_N{lat:02d}_00_W{abs(lon):03d}_00_DEM';url=f'/vsicurl/https://copernicus-dem-30m.s3.amazonaws.com/{name}/{name}.tif'
        try:
            with rasterio.open(url) as src:
                tile=np.full((height,width),np.nan,dtype='float32')
                reproject(source=rasterio.band(src,1),destination=tile,src_transform=src.transform,src_crs=src.crs,dst_transform=aff,dst_crs='EPSG:4326',resampling=Resampling.average,dst_nodata=np.nan)
                dem=np.where(np.isnan(dem),tile,dem);used.append(name)
        except Exception as e:print('skip',name,type(e).__name__)
if not used:raise SystemExit('No DEM tiles available')
rivers=[shape(f['geometry']) for f in load('rivers.geojson')['features']]
drain=rasterio.features.rasterize([(g,1) for g in rivers],out_shape=(height,width),transform=aff,all_touched=True,dtype='uint8').astype(bool)
parishes=load('parishes.geojson')['features'];codes=[f['properties']['dtmnfr'] for f in parishes]
labels=rasterio.features.rasterize([(shape(f['geometry']),i+1) for i,f in enumerate(parishes)],out_shape=(height,width),transform=aff,fill=0,dtype='int32')
st=parish_terrain_stats(dem,drain,labels,len(codes),RES,39.5)
rows={c:{'hand_lt5_frac':None if np.isnan(st['hand_lt_threshold_frac'][i]) else round(float(st['hand_lt_threshold_frac'][i]),4),'dem_coverage':round(float(st['dem_coverage_frac'][i]),3) if not np.isnan(st['dem_coverage_frac'][i]) else 0,'mean_slope_deg':None if np.isnan(st['mean_slope_deg'][i]) else round(float(st['mean_slope_deg'][i]),2)} for i,c in enumerate(codes)}
stat=load('susceptibility.json')['parishes'];auc=roc_auc([rows[c]['hand_lt5_frac'] if rows[c]['hand_lt5_frac'] is not None else np.nan for c in codes],[stat[c]['f100']>0.01 for c in codes])
out={'schema_version':'floods-terrain-susceptibility/1','computed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':'Copernicus GLO-30 DSM (DSM, not bare-earth MDT) via AWS open data','tiles':used,'grid_deg':RES,
 'method':'HAND approximated as elevation minus elevation of Euclidean-nearest river cell (rivers Strahler>=6), capped at 3 km; share of parish cells with HAND<5 m. Not flow-routed HAND.','diagnostics':{'auc_hand_vs_apa_t100_presence':auc},'parishes':rows}
(D/'terrain-susceptibility.json').write_text(json.dumps(out,separators=(',',':')),encoding='utf-8');print(json.dumps({'tiles':len(used),'auc':auc}))
