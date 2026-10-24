/* Shared by flood, fire and other risk maps. Only validated aggregated releases. */
function validatePresence(j,now=Date.now()){
 if(j?.schema_version!=='floods-presence/1')throw Error('Unsupported presence schema');
 if(j.public_redistribution_allowed!==true)throw Error('This dataset cannot be published in a public map');
 if(!['sample_users','sample_devices','relative_index','estimated_people','origin_destination_flows'].includes(j.measurement_kind))throw Error('Unknown measurement kind');
 if(!Number.isFinite(Date.parse(j.observed_from))||!Number.isFinite(Date.parse(j.observed_to))||Date.parse(j.observed_from)>=Date.parse(j.observed_to)||Date.parse(j.observed_to)>now+360000)throw Error('Invalid observation interval');
 if(!j.provider||!j.source_url||!Array.isArray(j.features))throw Error('Missing provenance');
 if(j.measurement_kind==='estimated_people'&&(!j.estimation_method||!j.uncertainty_method))throw Error('Population estimates require calibration and uncertainty methods');
 const expected={sample_users:'users',sample_devices:'devices',relative_index:'ratio',estimated_people:'people',origin_destination_flows:'movements'}[j.measurement_kind];
 for(let f of j.features){if(f.unit!==expected)throw Error('Measurement unit mismatch');if(f.suppressed&&f.value!==null)throw Error('Suppressed cells must not expose a value');if(!f.suppressed&&(!Number.isFinite(f.value)||f.value<0))throw Error('Invalid aggregated value');if(!f.geometry)throw Error('Missing aggregation geography');}
 return j;
}
module.exports={validatePresence};
