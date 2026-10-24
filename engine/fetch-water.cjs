const fs=require('node:fs');
(async()=>{let q='[out:json][timeout:30];(way["natural"="water"](40.17,-8.49,40.25,-8.36);relation["natural"="water"](40.17,-8.49,40.25,-8.36););out geom;';let r=await fetch('https://overpass-api.de/api/interpreter?data='+encodeURIComponent(q),{signal:AbortSignal.timeout(45000)});if(!r.ok)throw Error(r.status);let j=await r.json();fs.writeFileSync('research/terrain/osm-water.json',JSON.stringify(j));console.log(JSON.stringify({elements:j.elements.length,water:j.elements.map(x=>({type:x.type,id:x.id,name:x.tags?.name,water:x.tags?.water})).slice(0,15)}));})();

