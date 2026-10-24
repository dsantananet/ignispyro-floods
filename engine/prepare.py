import sys,pathlib,json,math
sys.path.insert(0,str(pathlib.Path('research/python').resolve()))
import numpy as np
import rasterio
from rasterio.warp import reproject,Resampling
from rasterio.transform import from_origin
from shapely.geometry import shape,Point,box,LineString
from shapely.ops import transform as geom_transform
from pyproj import Transformer
root=pathlib.Path('.');cfg=json.loads((root/'engine/pilot.json').read_text(encoding='utf-8-sig'));out=root/'engine/terrain';out.mkdir(exist_ok=True)
toxy=Transformer.from_crs(4326,3763,always_xy=True).transform;tolon=Transformer.from_crs(3763,4326,always_xy=True).transform
roi=geom_transform(toxy,box(*cfg['bbox_wgs84']));reference=geom_transform(toxy,Point(cfg['reference_point_wgs84']));rivers=json.loads((root/'dist/data/rivers.geojson').read_text(encoding='utf-8-sig'))['features'];features={int(f['properties']['objectid']):f for f in rivers};geo={k:geom_transform(toxy,shape(f['geometry'])) for k,f in features.items()};candidates=[k for k,f in features.items() if int(f['properties']['streamorder_order'])>=5 and geo[k].intersects(roi)]
if not candidates:raise RuntimeError('No major river geometry in pilot')
seed=min(candidates,key=lambda k:geo[k].distance(reference));chain=[seed];seen={seed}
while True:
 target=features[chain[0]]['properties']['from_node'];up=[k for k,f in features.items() if f['properties']['to_node']==target and k not in seen]
 if not up:break
 k=max(up,key=lambda k:(int(features[k]['properties']['streamorder_order']),geo[k].length));
 if not geo[k].intersects(roi.buffer(300)):break
 chain.insert(0,k);seen.add(k)
while True:
 k=features[chain[-1]]['properties']['nextdownid']
 if k not in features or k in seen or not geo[k].intersects(roi.buffer(300)):break
 chain.append(k);seen.add(k)
coords=[]
for k in chain:
 g=geo[k]
 if g.geom_type!='LineString':raise RuntimeError('Non-linear reach geometry')
 xy=list(g.coords)
 if coords and math.dist(coords[-1],xy[-1])<math.dist(coords[-1],xy[0]):xy.reverse()
 if coords and math.dist(coords[-1],xy[0])>100:raise RuntimeError('Disconnected river chain')
 coords.extend(xy if not coords else xy[1:])
line=LineString(coords).intersection(roi)
if line.geom_type=='MultiLineString':line=max(line.geoms,key=lambda g:g.length)
if line.length<1000:raise RuntimeError('Pilot reach too short')
minx,miny,maxx,maxy=roi.buffer(cfg['section_half_width_m']+100).bounds;step=cfg['grid_m'];width=math.ceil((maxx-minx)/step);height=math.ceil((maxy-miny)/step);aff=from_origin(minx,maxy,step,step);dem=np.full((height,width),np.nan,dtype='float32')
with rasterio.open('research/terrain/coimbra-source.tif') as src:
 reproject(source=rasterio.band(src,1),destination=dem,src_transform=src.transform,src_crs=src.crs,dst_transform=aff,dst_crs=3763,resampling=Resampling.bilinear,dst_nodata=np.nan)
if np.isnan(dem).any():raise RuntimeError('Terrain coverage has gaps')
distances=np.arange(0,line.length+1,cfg['section_spacing_m']);centres=np.array([[line.interpolate(d).x,line.interpolate(d).y] for d in distances]);normals=[]
for d in distances:
 a=line.interpolate(max(0,d-20));b=line.interpolate(min(line.length,d+20));v=np.array([b.x-a.x,b.y-a.y]);v/=np.linalg.norm(v);normals.append([-v[1],v[0]])
offsets=np.arange(-cfg['section_half_width_m'],cfg['section_half_width_m']+1,cfg['section_sample_m']);xy=centres[:,None,:]+np.array(normals)[:,None,:]*offsets[None,:,None];rows=np.clip(((maxy-xy[:,:,1])/step).astype(int),0,height-1);cols=np.clip(((xy[:,:,0]-minx)/step).astype(int),0,width-1);profiles=dem[rows,cols].astype(float)
middle=np.abs(offsets)<=cfg['estimated_channel_width_m']/3;water=np.quantile(profiles[:,middle],.2,axis=1)
# Remove isolated bridge/vegetation spikes with a five-section median; no survey is inferred.
smooth=np.array([np.median(water[max(0,i-2):min(len(water),i+3)]) for i in range(len(water))]);slope=max(cfg['minimum_slope'],min(.02,float(-np.polyfit(distances,smooth,1)[0])))
bed=smooth-cfg['estimated_channel_incision_m'];channel=np.abs(offsets)<=cfg['estimated_channel_width_m']/2;profiles[:,channel]=bed[:,None]
np.savez_compressed(out/'coimbra.npz',dem=dem,transform=np.array(tuple(aff)[:6]),centres=centres,profiles=profiles,offsets=offsets,chainage=distances,bed=bed,water_reference=smooth,slope=slope,line_xy=np.array(line.coords))
meta={'source':cfg['terrain_url'],'terrain':cfg['terrain_name'],'vertical_datum':cfg['terrain_vertical_datum'],'horizontal_crs':cfg['crs'],'grid_m':step,'shape':list(dem.shape),'reach_length_m':line.length,'apa_reach_ids':chain,'cross_sections':len(centres),'section_half_width_m':cfg['section_half_width_m'],'normal_flow_slope':slope,'bed_incision_estimated_m':cfg['estimated_channel_incision_m'],'note':'DSM-derived sections with assumed incised channel; not bathymetric survey. Source stored locally; this is a derived pilot crop.'}
(out/'coimbra.json').write_text(json.dumps(meta,indent=2),encoding='utf-8');print(json.dumps(meta))

