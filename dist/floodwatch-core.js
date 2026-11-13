(function(root){
 'use strict';
 const C=(typeof module!=='undefined'&&typeof require==='function')?require('./core.js'):root.FloodCore;
 // Index of activation of susceptibility (IAS). Screening only: NOT a flood depth, extent or official warning.
 const CLASSES=['Sem dados','Baixa','Moderada','Elevada','Muito elevada','Crítica'];
 const COLORS=['#9aa9ad','#4fae7b','#e3c941','#ee9b3d','#d9503f','#8e2f78'];
 // rows: static susceptibility 1..5 · columns: live trigger 1..4. Monotonic in both axes (tested).
 const MATRIX=[[1,1,1,2],[1,1,2,3],[1,2,3,4],[1,3,4,5],[2,3,5,5]];
 const ok=v=>typeof v==='number'&&Number.isFinite(v);
 const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
 // --- antecedent moisture (SCS AMC) ------------------------------------------------------
 // Thresholds are SCS 5-day dormant-season limits applied to the 24 h before the event window: a proxy, flagged as such.
 function amcClass(prev24){if(!ok(prev24)||prev24<0)return null;return prev24<13?1:prev24<28?2:3;}
 function adjustCN(cn,amc){if(!ok(cn)||cn<=0||cn>100)return null;if(amc===1)return 4.2*cn/(10-.058*cn);if(amc===3)return 23*cn/(10+.13*cn);if(amc===2)return cn;return null;}
 // --- lumped SCS triangular unit hydrograph (HEC-HMS principle) ---------------------------------
 // Tc by Kirpich with Hack's-law length; ONLY order-of-magnitude, valid for small/medium basins.
 function timeOfConcentrationH(areaKm2,slope=.02){if(!ok(areaKm2)||areaKm2<=0||!ok(slope)||slope<=0)return null;const L=1400*areaKm2**.6;return .0195*L**.77*slope**-.385/60;}
 // Tp = D/2 + 0.6 Tc with D = 0.133 Tc (SCS triangular UH)
 function peakFlow(runoffMm,areaKm2,slope){const tc=timeOfConcentrationH(areaKm2,slope);if(tc===null||!ok(runoffMm)||runoffMm<0)return null;const tpH=Math.max(.25,.6665*tc);return {peak_m3s:.208*areaKm2*runoffMm/tpH,tc_h:tc,tp_h:tpH,valid_area:areaKm2<=500};}
 // --- triggers ----------------------------------------------------------------------------
 function runoffClass(q){return !ok(q)?null:q<5?1:q<20?2:q<45?3:4;}
 function triggerClass({p1,p6,p24,f6,f24,runoffMm}){
  const now=C.rainPressure(p1??null,p6??null,p24??null);
  const rc=runoffClass(runoffMm);
  const fcClass=ok(f6)&&ok(f24)?Math.max(f6>=80?4:f6>=50?3:f6>=25?2:1,f24>=120?4:f24>=80?3:f24>=40?2:1):null;
  const parts=[now,rc].filter(v=>v!==null);
  const current=parts.length?Math.max(...parts):null;
  // forecast raises the trigger by at most one class: it is model rain, never observation.
  let t=current;
  if(fcClass!==null){if(t===null)t=Math.max(1,fcClass-1);else if(fcClass>t)t=Math.min(4,t+1);}
  return {trigger:t,current,forecast:fcClass,rain_class:now,runoff_class:rc};
 }
 // --- reservoirs ---------------------------------------------------------------------------
 function damClass(fillPercent,ageDays){if(!ok(fillPercent)||!ok(ageDays)||ageDays>35)return null;return fillPercent>=97?4:fillPercent>=90?3:fillPercent>=80?2:1;}
 // --- static susceptibility -----------------------------------------------------------------
 // Weights are expert priors (AHP-style ordering from the literature: distance to river and relief dominate), not fitted.
 const W={zone:.5,hand:.3,river:.2};
 function staticScore({f20,f100,f1000,river300,handLow}){
  const sat=(v,s)=>ok(v)?Math.min(1,v/s):null;
  const e20=sat(f20,.1),e100=sat(f100,.1),e1000=sat(f1000,.1);
  const zone=[e20!==null?e20:null,e100!==null?.75*e100:null,e1000!==null?.5*e1000:null].filter(v=>v!==null);
  const parts=[];if(zone.length)parts.push(['zone',Math.max(...zone)]);
  if(ok(handLow))parts.push(['hand',Math.min(1,handLow/.3)]);
  if(ok(river300))parts.push(['river',Math.min(1,river300/.25)]);
  if(!parts.length)return {score:null,class:null,components:{}};
  const wsum=parts.reduce((a,[k])=>a+W[k],0);const score=parts.reduce((a,[k,v])=>a+W[k]*v,0)/wsum;
  const hasZone=parts.some(([k])=>k==='zone'&&parts.find(p=>p[0]==='zone')[1]>0);
  let cls=score<.1?1:score<.25?2:score<.45?3:score<.65?4:5;
  // proximity/terrain alone cannot support more than "Elevada" without a mapped APA zone
  if(!hasZone)cls=Math.min(cls,3);
  return {score,class:cls,components:Object.fromEntries(parts),evidence:hasZone?'apa_zone':'terrain_or_river_only'};
 }
 function alertClass(s,t,damBump=0){if(!Number.isInteger(s)||s<1||s>5||!Number.isInteger(t)||t<1||t>4)return null;const tt=Math.min(4,t+(t>=2?damBump:0));return MATRIX[s-1][tt-1];}
 function ageHours(iso,now=Date.now()){const t=Date.parse(iso);return Number.isFinite(t)?(now-t)/3600000:null;}
 const api={CLASSES,COLORS,MATRIX,amcClass,adjustCN,timeOfConcentrationH,peakFlow,runoffClass,triggerClass,damClass,staticScore,alertClass,ageHours,W};
 if(typeof module!=='undefined')module.exports=api;root.FloodWatch=api;
})(typeof window==='undefined'?globalThis:window);
