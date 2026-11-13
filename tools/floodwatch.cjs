// Real-time susceptibility activation (IAS) per parish. Screening product: never a flood depth/extent.
// Inputs are the files produced earlier in the 15-minute cycle; every missing input degrades to "unknown", never to zero.
const fs=require('node:fs'),T=require('@turf/turf'),C=require('../dist/core.js'),F=require('../dist/floodwatch-core.js');
const D=(process.env.FLOODWATCH_DATA_DIR||'dist/data')+'/',load=(n,opt)=>{try{return JSON.parse(fs.readFileSync(D+n,'utf8').replace(/^﻿/,''));}catch(e){if(opt)return null;throw e;}};
const now=process.env.FLOODWATCH_NOW?Date.parse(process.env.FLOODWATCH_NOW):Date.now(),BASE_CN=75,DEFAULT_SLOPE=.02;
const sim=load('simulation.json'),est=load('rainfall-estimates.json'),res=load('reservoir-bulletin.json',1),tele=load('snirh-telemetry.json',1),stat=load('susceptibility.json'),terrain=load('terrain-susceptibility.json',1);
const basinsGeo=load('basins.geojson'),parishes=load('parishes.geojson');
const estimates=new Map(est.basins.map(b=>[b.id,b]));
// ---- basins -------------------------------------------------------------------------------
const basins=new Map();
for(const b of sim.basins){
 const e=estimates.get(b.id),age=F.ageHours(b.valid_time,now),stale=age===null||age>3;
 const amc=F.amcClass(e?.p24_prev_mm),cn=amc?F.adjustCN(BASE_CN,amc):BASE_CN;
 const q=stale?null:C.runoff(b.p24_mm,cn);
 const trig=stale?{trigger:null,current:null,forecast:null}:F.triggerClass({p1:b.p1_mm,p6:b.p6_mm,p24:b.p24_mm,f6:e?.f6_mm,f24:e?.f24_mm,runoffMm:q});
 const peak=q!==null&&q>0?F.peakFlow(q,b.area_km2,DEFAULT_SLOPE):null;
 basins.set(b.id,{id:b.id,area_km2:b.area_km2,valid_time:b.valid_time,source:b.modelled_rainfall?'ECMWF':'IPMA',stale,p1_mm:b.p1_mm,p6_mm:b.p6_mm,p24_mm:b.p24_mm,f6_mm:e?.f6_mm??null,f24_mm:e?.f24_mm??null,
  amc,cn_used:cn,runoff_mm:q,runoff_volume_m3:q===null?null:C.volume(q,b.area_km2),mean_flow_24h_m3s:q===null?null:C.volume(q,b.area_km2)/86400,
  peak_flow_m3s:peak&&peak.valid_area?peak.peak_m3s:null,peak_note:peak?(peak.valid_area?'SCS UH lumped, Tc Kirpich, slope 0.02 assumed':'basin >500 km2: lumped peak not meaningful'):null,
  ...trig,dam_class:0,rising_stations:0});
}
const basinOf=pt=>{for(const f of basinsGeo.features)if(T.booleanPointInPolygon(pt,f))return String(f.properties.objectid);return null;};
// ---- reservoirs -------------------------------------------------------------------------------
const dams=[];
for(const r of res?.records||[]){
 if(!r.geometry||!Number.isFinite(r.fill_percent))continue;
 const ref=r.reference_period,end=/^\d{4}-\d{2}$/.test(ref)?Date.UTC(+ref.slice(0,4),+ref.slice(5,7),0):Date.parse(ref),age=(now-end)/86400000;
 const cls=F.damClass(r.fill_percent,age),b=basinOf({type:'Feature',geometry:r.geometry,properties:{}});
 dams.push({name:r.name,coordinates:r.geometry.coordinates,fill_percent:r.fill_percent,storage_hm3:r.storage_hm3,capacity_hm3:r.capacity_hm3,reference:ref,resolution:r.temporal_resolution,age_days:Math.round(age),class:cls,basin_id:b});
 if(b&&cls&&basins.has(b))basins.get(b).dam_class=Math.max(basins.get(b).dam_class,cls);
}
// ---- river gauges: only a trend flag; no thresholds exist, so no absolute classification ------------
const rivers=[];
for(const s of tele?.stations||[]){
 for(const q of s.series||[]){
  if(!['level_m','flow_m3s'].includes(q.quantity)||!q.latest||!C.fresh(q.latest.observed_at,now,3))continue;
  const t6=now-6*3600000,earlier=q.rows.filter(r=>Date.parse(r.observed_at)<=Date.parse(q.latest.observed_at)-3*3600000&&Date.parse(r.observed_at)>=Date.parse(q.latest.observed_at)-8*3600000);
  if(!earlier.length)continue;const base=Math.min(...earlier.map(r=>r.value)),delta=q.latest.value-base;
  const rising=q.quantity==='level_m'?delta>=.3:(delta>=5&&q.latest.value>=1.5*Math.max(base,1));
  const b=s.geometry?basinOf({type:'Feature',geometry:s.geometry,properties:{}}):null;
  rivers.push({id:s.id,name:s.name,river:s.river,quantity:q.quantity,value:q.latest.value,observed_at:q.latest.observed_at,delta_3_8h:+delta.toFixed(3),rising,coordinates:s.geometry?.coordinates,basin_id:b});
  if(rising&&b&&basins.has(b))basins.get(b).rising_stations++;
 }
}
// ---- parishes -----------------------------------------------------------------------------------
const out={},counts=[0,0,0,0,0,0];let popZone=0,popVuln=0;const list=[];
for(const f of parishes.features){
 const p=f.properties,s=stat.parishes[p.dtmnfr]||{},tr=terrain?.parishes?.[p.dtmnfr];
 const st=F.staticScore({f20:s.f20,f100:s.f100,f1000:s.f1000,river300:s.river300,handLow:tr?.hand_lt5_frac});
 const bs=p.basin_ids.map(id=>basins.get(id)).filter(Boolean);
 const trig=bs.map(b=>b.trigger).filter(v=>v!==null);const t=trig.length?Math.max(...trig):null;
 const bump=bs.some(b=>b.dam_class>=3||b.rising_stations>0)?1:0;
 const a=st.class&&t?F.alertClass(st.class,t,bump):null;
 const cls=a??0;counts[cls]++;
 if(a&&a>=3){popZone+=s.pop_t100_est||0;popVuln+=s.vulnerable_t100_est||0;}
 out[p.dtmnfr]={f20:s.f20??null,f100:s.f100??null,rv:s.river300??null,vul:s.vulnerable_t100_est??null,s:st.class,ev:st.evidence?.[0]||null,sc:st.score===null?null:+st.score.toFixed(3),t,a,bump,pz:s.pop_t100_est??null,pz20:s.pop_t20_est??null,b:p.basin_ids};
 if(a&&a>=3)list.push([a,s.pop_t100_est||0,p.dtmnfr]);
}
list.sort((x,y)=>y[0]-x[0]||y[1]-x[1]);
const result={schema_version:'floods-watch/1',computed_at:new Date(now).toISOString(),valid_for_hours:3,
 method:{static:'APA T20/T100/T1000 area fractions + 300 m river proximity (+ HAND<5 m share when terrain-susceptibility.json exists); expert weights, not fitted.',
  trigger:'max(rain class 1/6/24 h, SCS-CN runoff class); CN75 adjusted by antecedent 24 h rain (AMC proxy); ECMWF forecast raises one class at most; reservoir >=90% full or rising gauge adds one class.',
  matrix:F.MATRIX,classes:F.CLASSES,limits:'Screening index. Not flood depth, extent, probability or an official warning. Population = area-weighted estimate inside APA T100 zones.'},
 inputs:{simulation:sim.computed_at,rain_estimates:est.computed_at,reservoirs:res?.retrieved_at||null,snirh:tele?.retrieved_at||null,static:stat.computed_at,terrain:terrain?.computed_at||null},
 summary:{parishes_by_class:Object.fromEntries(F.CLASSES.map((n,i)=>[n,counts[i]])),population_in_t100_zone_of_parishes_class3plus_est:popZone,vulnerable_age_in_t100_zone_est:popVuln,top:list.slice(0,40).map(x=>x[2]),basins_with_data:[...basins.values()].filter(b=>b.trigger!==null).length,basins_stale:[...basins.values()].filter(b=>b.stale).length,rising_gauges:rivers.filter(r=>r.rising).length},
 basins:[...basins.values()],dams,rivers,parishes:out};
fs.writeFileSync(D+'floodwatch.json',JSON.stringify(result));
console.log(JSON.stringify({classes:result.summary.parishes_by_class,basins_with_data:result.summary.basins_with_data,stale:result.summary.basins_stale,dams:dams.length,gauges:rivers.length}));
