const fs=require('node:fs'),assert=require('node:assert/strict');
const load=n=>JSON.parse(fs.readFileSync('dist/data/'+n,'utf8').replace(/^\uFEFF/,''));
let p=load('parishes.geojson'),s=load('simulation.json'),h=load('history.json'),n=load('history-nodes.json'),b=load('bgri-population.json'),t=load('t10.json');
assert.equal(p.features.length,3049);assert.equal(s.basins.length,262);assert.equal(h.basins.length,262);assert.equal(n.dates.length,3653);assert.equal(n.nodes.length,28);assert.equal(b.total,10343066);
for(let x of n.nodes)assert.ok(x.precipitation_mm.length===3653&&x.precipitation_mm.every(v=>Number.isFinite(v)&&v>=0));
for(let x of s.basins){assert.ok(x.rainfall_volume_m3===null||x.rainfall_volume_m3>=0);assert.equal(x.river_stage_m,null);assert.equal(x.population_currently_affected,null);for(let r of x.runoff_sensitivity)if(r.volume_m3!==null)assert.ok(r.volume_m3<=x.rainfall_volume_m3+1e-6);}
for(let f of p.features){let x=f.properties;if(x.vulnerable_age_count!==null)assert.ok(x.vulnerable_age_count<=x.population_2021);assert.equal(x.exposed_population,null);}
for(let x of t.stations){assert.equal(x.annual_maxima.length,10);assert.equal(x.reach_match_verified,false);}
console.log(JSON.stringify({validated:true,parishes:p.features.length,basins:s.basins.length,historical_days:n.dates.length,historical_reference_nodes:n.nodes.length,hydraulic_footprint:'not_validated_no_current_risk_published'}));
