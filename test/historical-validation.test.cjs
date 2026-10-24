const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const j=JSON.parse(fs.readFileSync('dist/data/coimbra-validation.json','utf8'));
test('historical screening cannot enable operational flood alerts',()=>{
 assert.equal(j.operationally_accepted,false);assert.equal(j.events.length,10);
 for(const r of j.events)if(r.comparison)assert.equal(r.comparison.operationally_accepted,false);
});
test('unobserved historical extents do not get fabricated spatial scores',()=>{
 for(const r of j.events.filter(r=>r.date<'2019'))assert.equal(r.comparison,undefined);
 assert.equal(j.observation_time_utc,'2019-12-23T06:43:00Z');
 assert.match(j.source_zip_sha256,/^[a-f0-9]{64}$/);
});
test('population is explicitly census exposure with allocation uncertainty',()=>{
 for(const p of j.parish_exposure){const c=p.observed_census2021;assert.equal(c.not_event_population,true);if(c.uniform_area_estimates){assert.ok(c.uniform_area_estimates[0]<=c.intersected_units_upper_allocation_bounds[0]);}}
});
