const fs=require('node:fs/promises'),T=require('@turf/turf'),C=require('../dist/core.js');
(async()=>{
 const [b,s,h,e]=await Promise.all(['basins.geojson','stations.geojson','hydrology.json','rainfall-estimates.json'].map(async n=>JSON.parse(await fs.readFile('dist/data/'+n,'utf8'))));
 const model=new Map(e.basins.map(b=>[b.id,b]));
 const rows=b.features.map(f=>{
  let inside=s.features.filter(p=>C.fresh(p.properties.observed_at)&&T.booleanPointInPolygon(p,f));
  let end=inside.map(s=>s.properties.observed_at).sort().at(-1);
  inside=inside.filter(s=>s.properties.observed_at===end&&['p1','p6','p24'].every(k=>s.properties[k]!==null));
  const id=String(f.properties.objectid),area=T.area(f)/1e6,estimated=inside.length<2,grid=model.get(id);
  const mean=k=>estimated?grid?.[k+'_mm']??null:inside.reduce((a,s)=>a+s.properties[k],0)/inside.length;
  let p1=mean('p1'),p6=mean('p6'),p24=mean('p24');
  return {id,area_km2:area,observed_at:estimated?null:end||null,valid_time:estimated?grid?.valid_time:end||null,source:estimated?'ECMWF IFS model point via Open-Meteo':'IPMA stations, synchronized interior mean',modelled_rainfall:estimated,station_count:inside.length,stations:inside.map(s=>s.properties.id),p1_mm:p1,p6_mm:p6,p24_mm:p24,rainfall_volume_m3:C.volume(p24,area),rainfall_pressure:C.rainPressure(p1,p6,p24),runoff_sensitivity:[55,75,90].map(cn=>({cn,runoff_mm:C.runoff(p24,cn),volume_m3:C.volume(C.runoff(p24,cn),area)})),flood_return_period:null,peak_flow_m3s:null,river_stage_m:null,population_currently_affected:null,hydrology_assimilated:false,status:p24===null?'insufficient_inputs':estimated?'experimental_modelled_rainfall_runoff':'experimental_observed_rainfall_runoff'};
 });
 const out={schema_version:'floods-simulation/2',computed_at:new Date().toISOString(),inputs_retrieved_at:s.retrieved_at,model_retrieved_at:e.retrieved_at,method:'SCS-CN sensitivity CN55/75/90, Ia=0.2S. Observations preferred; ECMWF model point gap-fill. No hydraulic routing or calibrated inundation.',hydrology_status:h.status,basins:rows};
 await fs.writeFile('dist/data/simulation.json',JSON.stringify(out));console.log(JSON.stringify({basins:rows.length,observed:rows.filter(r=>!r.modelled_rainfall&&r.p24_mm!==null).length,modelled:rows.filter(r=>r.modelled_rainfall&&r.p24_mm!==null).length,missing:rows.filter(r=>r.p24_mm===null).length}));
})();
