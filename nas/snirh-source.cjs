'use strict';
// Public APA HTML embeds JSON. Parse data, never execute source JavaScript.
function embeddedJSON(html,name){
 const match=new RegExp('\\bvar\\s+'+name+'\\s*=\\s*').exec(html);if(!match)throw Error('Missing '+name);
 const start=match.index+match[0].length;let quoted=false,escaped=false,depth=0;
 if(!['[','{'].includes(html[start]))throw Error('Expected JSON container');
 for(let i=start;i<html.length;i++){let c=html[i];if(quoted){if(escaped)escaped=false;else if(c==='\\')escaped=true;else if(c==='"')quoted=false;}else{if(c==='"')quoted=true;else if(c==='['||c==='{')depth++;else if(c===']'||c==='}')if(--depth===0)return JSON.parse(html.slice(start,i+1));}}
 throw Error('Incomplete JSON');
}
const fmt=new Intl.DateTimeFormat('sv-SE',{timeZone:'Europe/Lisbon',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});
function sourceTime(text){
 if(typeof text!=='string'||!/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(text))return null;
 let wall=Date.parse(text.replace(' ','T')+'Z'),matches=[];
 for(let offset of [0,3600000]){let t=wall-offset;if(fmt.format(new Date(t))===text)matches.push(new Date(t).toISOString());}
 // Autumn repeated hour has no offset in the source: do not guess.
 return matches.length===1?matches[0]:null;
}
function observations(parameter,now=Date.now()){
 let expected={1:['flow_m3s','m3/s'],2:['outflow_m3s','m3/s'],3:['elevation_m','m'],4:['level_m','m'],6:['inflow_m3s','m3/s'],7:['storage_percent','%']}[parameter.id];
 if(!expected||parameter.unit?.trim()!==expected[1])return null;
 let unique=new Map(),rejected=0;
 for(let row of parameter.values||[]){let time=sourceTime(row.moment),v=row.value;if(!time||typeof v!=='number'||!Number.isFinite(v)||v===-99||(['flow_m3s','outflow_m3s','inflow_m3s','storage_percent'].includes(expected[0])&&v<0)||Date.parse(time)>now+360000){rejected++;continue;}let old=unique.get(time);if(old&&old.value!==v){unique.set(time,{invalid:true});rejected++;}else if(!old)unique.set(time,{observed_at:time,value:v,source_time:row.moment});}
 let rows=[...unique.values()].filter(r=>!r.invalid).sort((a,b)=>a.observed_at.localeCompare(b.observed_at));
 return {quantity:expected[0],unit:expected[1],parameter_id:parameter.id,rows,rejected,latest:rows.at(-1)||null};
}
function fresh(row,now=Date.now()){return !!row&&Number.isFinite(Date.parse(row.observed_at))&&now-Date.parse(row.observed_at)>=-360000&&now-Date.parse(row.observed_at)<=10800000;}
module.exports={embeddedJSON,sourceTime,observations,fresh};
