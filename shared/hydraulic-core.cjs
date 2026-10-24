/* Physics helpers for a future calibrated reach/reservoir model.
   No synthetic section, datum or release is substituted for missing input. */
function interpolateCurve(curve,x){
 if(!Array.isArray(curve)||curve.length<2||!Number.isFinite(x))throw Error('A surveyed/calibrated curve and finite input are required');
 for(let i=0;i<curve.length;i++)if(!Array.isArray(curve[i])||curve[i].length!==2||!curve[i].every(Number.isFinite)||(i&&curve[i][0]<=curve[i-1][0])||(i&&curve[i][1]<curve[i-1][1]))throw Error('Invalid monotonic curve');
 if(x<curve[0][0]||x>curve.at(-1)[0])throw Error('Outside calibrated curve; extrapolation forbidden');
 for(let i=1;i<curve.length;i++)if(x<=curve[i][0]){let [a,y]=curve[i-1],[b,z]=curve[i];return y+(z-y)*(x-a)/(b-a);}
}
function storageStep({storage_m3,inflow_m3s,outflow_m3s,seconds,capacity_m3}){
 let values=[storage_m3,inflow_m3s,outflow_m3s,seconds,capacity_m3];if(!values.every(v=>Number.isFinite(v)&&v>=0)||!seconds||storage_m3>capacity_m3)throw Error('Invalid water balance input');
 const incoming=inflow_m3s*seconds,requested=outflow_m3s*seconds,release=Math.min(requested,storage_m3+incoming),remaining=storage_m3+incoming-release,overflow=Math.max(0,remaining-capacity_m3),stored=remaining-overflow;
 return {storage_m3:stored,release_m3:release,unrouted_overflow_m3:overflow,balance_error_m3:storage_m3+incoming-release-overflow-stored};
}
function runoffIncrements(cumulativeRain,cn){const C=require('../dist/core.js');if(!Array.isArray(cumulativeRain)||!cumulativeRain.every(Number.isFinite))throw Error('Missing cumulative storm rain');let lastP=0,lastQ=0;return cumulativeRain.map(p=>{if(p<lastP)throw Error('Storm cumulative rain cannot decrease');let q=C.runoff(p,cn);if(q===null)throw Error('Invalid CN/rain');let inc=q-lastQ;lastP=p;lastQ=q;return inc;});}
function publishableInundation(run,now=Date.now()){
 if(!run||run.status!=='validated_hydraulic_model'||!run.calibration_id||!run.vertical_datum||!run.terrain_version||!run.boundary_conditions_id||!run.mass_balance_checked) return false;
 if(!Number.isFinite(Date.parse(run.valid_time))||Math.abs(now-Date.parse(run.valid_time))>3*3600000)return false;
 if(!Array.isArray(run.features)||!run.features.every(f=>f.geometry&&Number.isFinite(f.properties?.depth_m)&&f.properties.depth_m>0&&f.properties.connected_to_river===true))return false;
 return true;
}
module.exports={interpolateCurve,storageStep,runoffIncrements,publishableInundation};
