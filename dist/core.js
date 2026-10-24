(function(root){
 const matrix=[[1,1,2,2,3],[1,2,3,3,4],[2,3,3,4,4],[2,3,4,4,5],[3,4,4,5,5]];
 function valid(v){return typeof v==='number'&&Number.isFinite(v)&&v>=0;}
 function utc(s){return /Z$|[+-]\d\d:\d\d$/.test(s)?s:s+'Z';}
 function rainfall(rows,end,hours){const t=Date.parse(end);if(!Number.isFinite(t))return null;const unique=new Map();for(const r of rows){let d=Date.parse(r.time);if(d>t-hours*3600000&&d<=t&&valid(r.mm))unique.set(d,r.mm);}if(unique.size!==hours)return null;for(let h=0;h<hours;h++)if(!unique.has(t-h*3600000))return null;return [...unique.values()].reduce((a,b)=>a+b,0);}
 function fresh(time,now=Date.now(),maxHours=3){let age=(now-Date.parse(time))/3600000;return Number.isFinite(age)&&age>=-0.1&&age<=maxHours;}
 // Exploratory rainfall screening only. Not a flood probability or official alert.
 function rainPressure(p1,p6,p24){if(p1===null||p6===null||p24===null)return null;return Math.max(p1>=30?4:p1>=20?3:p1>=10?2:1,p6>=80?4:p6>=50?3:p6>=25?2:1,p24>=120?4:p24>=80?3:p24>=40?2:1);}
 function runoff(p,cn){if(!valid(p)||!Number.isFinite(cn)||cn<=0||cn>100)return null;let s=25400/cn-254,ia=.2*s;return p<=ia?0:(p-ia)**2/(p+.8*s);}
 function volume(q,areaKm2){return valid(q)&&valid(areaKm2)?q*areaKm2*1000:null;}
 function risk(h,c){return Number.isInteger(h)&&h>=1&&h<=5&&Number.isInteger(c)&&c>=1&&c<=5?matrix[c-1][h-1]:null;}
 function hazard(d,v){if(!valid(d)||!valid(v))return null;let x=d*(v+.5);return x<.75?1:x<1.25?2:x<2.5?3:x<=7?4:5;}
 const api={matrix,valid,utc,rainfall,fresh,rainPressure,runoff,volume,risk,hazard};if(typeof module!=='undefined')module.exports=api;root.FloodCore=api;
})(typeof window==='undefined'?globalThis:window);
