'use strict';
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto'),S=require('../shared/snirh.cjs');
const base='https://infoagua.apambiente.pt/',dir=path.resolve('dist/data'),now=Date.now(),failures=[];
async function page(url){let r=await fetch(url,{signal:AbortSignal.timeout(30000)});if(!r.ok)throw Error('HTTP '+r.status);return r.text();}
async function save(n,j){await fs.writeFile(path.join(dir,n),JSON.stringify(j));}
async function main(){
 let stations;try{stations=S.embeddedJSON(await page(base+'pt/cheias/cheias-pesquisa'),'DATA_Stations');}catch(e){let previous=JSON.parse(await fs.readFile(path.join(dir,'snirh-telemetry.json'),'utf8'));previous.collection_status='upstream_error';previous.last_attempt_at=new Date(now).toISOString();previous.failures=[e.message];await save('snirh-telemetry.json',previous);console.log('SNIRH unavailable; preserving original observation times');return;}
 let catalogue=[...new Map(stations.filter(s=>['estacao_hidrometrica','estacao_albufeira'].includes(s.station_type_id)).map(s=>[s.snirh_source_id,s])).values()],records=[],index=0;
 async function worker(){while(index<catalogue.length){let s=catalogue[index++],url=base+'pt/cheias/cheia-detalhe/'+s.snirh_source_id;try{
 let html=await page(url),params=S.embeddedJSON(html,'DATA_StationParameters'),series=params.map(p=>S.observations(p,now)).filter(Boolean),lon=Number(s.longitude),lat=Number(s.latitude);if(!Number.isFinite(lon)||!Number.isFinite(lat))throw Error('Missing geometry');
 records.push({id:String(s.snirh_source_id),name:s.station_name,type:s.station_type_id,basin:s.basin_name,basin_id:s.basin_id,river:s.river,geometry:{type:'Point',coordinates:[lon,lat]},source_url:url,source:'APA InfoAgua / SNIRH',retrieved_at:new Date(now).toISOString(),source_sha256:crypto.createHash('sha256').update(html).digest('hex'),time_zone_assumption:'Europe/Lisbon; source HTML has no explicit UTC offset; ambiguous DST hour rejected',vertical_datum:'source_local_unverified',series});
 }catch(e){failures.push({id:String(s.snirh_source_id),error:e.message});}}}
 await Promise.all([worker(),worker(),worker()]);
 let old;try{old=JSON.parse(await fs.readFile(path.join(dir,'snirh-telemetry.json'),'utf8'));}catch{}
 for(let f of failures){let r=old?.stations.find(s=>s.id===f.id);if(r)records.push({...r,collection_error:f.error});}
 records.sort((a,b)=>a.id.localeCompare(b.id));
 const telemetry={schema_version:'floods-snirh-telemetry/1',retrieved_at:new Date(now).toISOString(),collection_status:failures.length?'partial':'connected',catalogue_url:base+'pt/cheias/cheias-pesquisa',catalogue_count:catalogue.length,failures,stations:records};await save('snirh-telemetry.json',telemetry);
 let rivers=[],reservoirs=[],features=[];
 for(let s of records){let row={id:s.id,name:s.name,source_url:s.source_url,geometry:s.geometry,vertical_datum:s.vertical_datum,observations:{}};
 for(let p of s.series){row.observations[p.quantity]=p.latest;if(p.latest)row[p.quantity]=p.latest.value;}
 let times=Object.values(row.observations).filter(Boolean).map(x=>x.observed_at).sort();row.observed_at=times.at(-1)||null;row.fresh_quantities=s.series.filter(p=>S.fresh(p.latest,now)).map(p=>p.quantity);row.station_code=s.id==='1627759222'?'12G/04H':null;
 (s.type==='estacao_albufeira'?reservoirs:rivers).push(row);
 features.push({type:'Feature',geometry:s.geometry,properties:{id:s.id,name:s.name,type:s.type,basin:s.basin,source_url:s.source_url,fresh:row.fresh_quantities.length>0,...Object.fromEntries(s.series.map(p=>[p.quantity,p.latest?.value??null])),...Object.fromEntries(s.series.map(p=>[p.quantity+'_time',p.latest?.observed_at??null]))}});
 }
 await save('snirh-observations.geojson',{type:'FeatureCollection',retrieved_at:telemetry.retrieved_at,features});
 await save('hydrology.json',{schema_version:'floods-hydrology/1',retrieved_at:telemetry.retrieved_at,status:telemetry.collection_status,rivers,reservoirs,note:'Observações oficiais APA/InfoÁgua de origem SNIRH. Hora por grandeza; nível de régua não é altitude do terreno. Dados antigos continuam identificados; não determinam inundação sem modelo validado.'});
 console.log(JSON.stringify({catalogue:catalogue.length,stations:records.length,failures:failures.length,fresh_stations:features.filter(f=>f.properties.fresh).length,observations:records.reduce((n,s)=>n+s.series.reduce((a,p)=>a+p.rows.length,0),0)}));
}
main().catch(e=>{console.error(e.message);process.exitCode=1;});
