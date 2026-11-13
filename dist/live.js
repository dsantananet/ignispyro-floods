'use strict';
/* Real-time susceptibility activation (IAS). Loaded last: it owns the default view and never labels an area as flooded.
   Data: data/floodwatch.json, recomputed every 15 min by tools/floodwatch.cjs and re-read here every 5 min. */
(function(){
 const FW=FloodWatch,REFRESH_MS=300000;
 let watch=null,watchAt=null,mapReady=false,busy=false;
 const opt=document.createElement('option');opt.value='live';opt.textContent='Monitorização em tempo real · suscetibilidade';$('view').prepend(opt);$('view').value='live';
 const label=document.querySelector('#parish-count')?.nextElementSibling;const labelDefault=label?.textContent;
 const klass=a=>FW.CLASSES[a||0],color=a=>FW.COLORS[a||0];
 const age=()=>watch?FW.ageHours(watch.computed_at):null;
 function parishList(){return data.parishes?.features||[];}
 function applyWatch(){
  if(!watch||!data.parishes)return;const h=age(),expired=h===null||h>12;
  for(const f of parishList()){const w=watch.parishes[f.properties.dtmnfr];f.properties.live=expired||!w?0:(w.a||0);f.properties.live_s=w?.s||0;}
  if(map?.getSource('parishes'))map.getSource('parishes').setData(data.parishes);
  const toGeo=(rows,fn)=>({type:'FeatureCollection',features:rows.filter(r=>r.coordinates).map(r=>({type:'Feature',geometry:{type:'Point',coordinates:r.coordinates},properties:fn(r)}))});
  const d=toGeo(watch.dams,r=>({name:r.name,fill:r.fill_percent,cls:r.class||0,cap:r.capacity_hm3||0,ref:r.reference,res:r.resolution}));
  const g=toGeo(watch.rivers,r=>({name:r.name,quantity:r.quantity,value:r.value,rising:r.rising?1:0,at:r.observed_at}));
  if(map?.getSource('dams-live'))map.getSource('dams-live').setData(d);if(map?.getSource('gauges-live'))map.getSource('gauges-live').setData(g);
 }
 function ensureLayers(){
  if(mapReady||!map?.getLayer('parishes-fill'))return;
  map.addSource('dams-live',{type:'geojson',data:{type:'FeatureCollection',features:[]}});map.addSource('gauges-live',{type:'geojson',data:{type:'FeatureCollection',features:[]}});
  map.addLayer({id:'dams-live',type:'circle',source:'dams-live',paint:{'circle-radius':['interpolate',['linear'],['get','cap'],0,4,500,8,4000,13],'circle-color':['match',['get','cls'],4,FW.COLORS[4],3,FW.COLORS[3],2,FW.COLORS[2],1,FW.COLORS[1],FW.COLORS[0]],'circle-stroke-width':2,'circle-stroke-color':'#173c65'}});
  map.addLayer({id:'gauges-live',type:'circle',source:'gauges-live',paint:{'circle-radius':['case',['==',['get','rising'],1],7,4],'circle-color':['case',['==',['get','rising'],1],FW.COLORS[4],'#4d7fa1'],'circle-stroke-width':1.5,'circle-stroke-color':'white'}});
  for(const id of ['dams-live','gauges-live'])map.on('click',id,e=>{const p=e.features[0].properties;new maplibregl.Popup().setLngLat(e.lngLat).setHTML(id==='dams-live'?'<b>'+E(p.name)+'</b><p>Enchimento '+num(p.fill,0)+' % · '+E(p.res==='monthly'?'boletim mensal':'boletim diário')+' '+E(p.ref)+'<br>Classe de reserva: '+klass(Number(p.cls))+'</p><p>Sem afluências nem descargas em contínuo: não prevê cheia a jusante.</p>':'<b>'+E(p.name)+'</b><p>'+E(p.quantity==='level_m'?'Nível':'Caudal')+': '+num(p.value,2)+(p.quantity==='level_m'?' m':' m³/s')+'<br>'+date(p.at)+'<br>'+(Number(p.rising)?'<b>Em subida</b> nas últimas horas':'Sem subida relevante')+'</p>').addTo(map);});
  mapReady=true;applyWatch();render();
 }
 async function load(){
  if(busy)return;busy=true;
  try{const r=await fetch('data/floodwatch.json?v='+Math.floor(Date.now()/60000));if(!r.ok)throw Error('floodwatch indisponível');const j=await r.json();if(j.schema_version!=='floods-watch/1')throw Error('esquema inesperado');const changed=j.computed_at!==watchAt;watch=j;watchAt=j.computed_at;if(changed){ensureLayers();applyWatch();}render();}
  catch(e){watch=null;if($('view').value==='live')render();console.warn(e);}finally{busy=false;}
 }
 const prevRender=render;
 function setLiveLayers(on){for(const id of ['dams-live','gauges-live'])if(map?.getLayer(id))map.setLayoutProperty(id,'visibility',on?'visible':'none');}
 render=function(){
  if($('view').value!=='live'){setLiveLayers(false);if(label)label.textContent=labelDefault;prevRender();return;}
  liveRender();
 };
 function liveRender(){
  const notice=document.querySelector('.notice');$('period').parentElement.hidden=true;
  const h=age();
  if(!watch){$('legend').innerHTML='<b>Monitorização em tempo real</b><small>A carregar ou indisponível. Sem cálculo atual, nenhuma freguesia é classificada.</small>';notice.innerHTML='<b>Monitorização em tempo real</b><p>Índice indisponível neste momento. Não se assume ausência de risco.</p>';$('results').innerHTML='';return;}
  const stale=h===null||h>3,expired=h===null||h>12,sum=watch.summary.parishes_by_class;
  notice.innerHTML='<b>Suscetibilidade em ativação · rastreio</b><p>Combina suscetibilidade estrutural (zonas APA T20/T100/T1000, proximidade de rios'+(watch.inputs.terrain?', MDT':'')+') com chuva, escoamento SCS-CN, previsão ECMWF, albufeiras e subida de níveis. <b>Não é altura de água, mancha, probabilidade nem aviso oficial.</b></p><p class="live-age'+(stale?' stale':'')+'">Calculado '+date(watch.computed_at)+' · '+(h===null?'idade desconhecida':h<1?'há '+Math.round(h*60)+' min':'há '+num(h,1)+' h')+(expired?' · <b>desatualizado: cores suspensas</b>':stale?' · atenção: atraso na atualização':'')+'</p>';
  const n3=(sum['Elevada']||0)+(sum['Muito elevada']||0)+(sum['Crítica']||0);
  $('parish-count').textContent=num(n3,0);if(label)label.textContent='freguesias com ativação elevada ou superior';
  $('legend').innerHTML='<b>Ativação da suscetibilidade</b>'+[5,4,3,2,1,0].map(i=>'<div class="legend-row"><i class="swatch" style="background:'+color(i)+'"></i>'+klass(i)+' · '+num(sum[klass(i)]||0,0)+'</div>').join('')+'<small>Moderada sem chuva = suscetibilidade estrutural elevada, sem ativação. Albufeiras: círculos azul-escuro; hidrométricas: vermelho = em subida.</small>';
  if(map?.getLayer('parishes-fill')){map.setPaintProperty('parishes-fill','fill-color',['match',['coalesce',['get','live'],0],1,FW.COLORS[1],2,FW.COLORS[2],3,FW.COLORS[3],4,FW.COLORS[4],5,FW.COLORS[5],FW.COLORS[0]]);map.setPaintProperty('parishes-fill','fill-opacity',expired?.12:.72);}
  const risk=document.querySelector('[data-layer=risk]');risk.disabled=false;risk.parentElement.hidden=false;
  if(map?.getLayer('rivers')){map.setPaintProperty('rivers','line-color','#168ec0');}
  setLiveLayers(true);
  const q=$('search').value.toLocaleLowerCase('pt-PT');
  const rows=parishList().filter(f=>(f.properties.freguesia+' '+f.properties.municipio).toLocaleLowerCase('pt-PT').includes(q));
  rows.sort((a,b)=>(b.properties.live||0)-(a.properties.live||0)||(watch.parishes[b.properties.dtmnfr]?.pz||0)-(watch.parishes[a.properties.dtmnfr]?.pz||0)||(b.properties.population_2021||0)-(a.properties.population_2021||0));
  $('result-count').textContent=rows.length.toLocaleString('pt-PT');
  $('results').innerHTML=rows.slice(0,70).map(f=>{const p=f.properties,w=watch.parishes[p.dtmnfr];return '<button class="result" data-code="'+E(p.dtmnfr)+'"><span class="badge" style="background:'+color(p.live)+'55;color:#17323b">'+E(klass(p.live))+'</span><strong>'+E(p.freguesia)+'</strong><small>'+E(p.municipio)+' · '+num(p.population_2021,0)+' residentes'+(w?.pz?' · ~'+num(w.pz,0)+' em zona T100 (est.)':'')+'</small></button>';}).join('')||'<p>Sem resultados.</p>';
  document.querySelector('.map-note').textContent='Rastreio de suscetibilidade · não é cheia em curso nem aviso oficial · sem dados ≠ sem risco';
  const u=$('updated');if(u&&!u.textContent.includes('IAS'))u.textContent+=' · IAS '+date(watch.computed_at);
 }
 const prevShow=showParish;
 showParish=function(code,fly=true){
  prevShow(code,fly);if($('view').value!=='live'||!watch)return;const w=watch.parishes[code];if(!w)return;
  const root=$('detail-content'),h2=root.querySelector('h2');if(!h2)return;const a=$('view').value==='live'?(parishList().find(f=>f.properties.dtmnfr===code)?.properties.live||0):0;
  const basins=w.b.map(id=>watch.basins.find(b=>b.id===id)).filter(Boolean).sort((x,y)=>(y.trigger||0)-(x.trigger||0));
  const dams=watch.dams.filter(d=>w.b.includes(d.basin_id)),gauges=watch.rivers.filter(r=>w.b.includes(r.basin_id));
  let html='<h3>Ativação da suscetibilidade</h3><span class="badge" style="background:'+color(a)+'66">'+E(klass(a))+'</span><p>Suscetibilidade estrutural <b>'+E(klass(w.s))+'</b> ('+(w.ev==='a'?'zona APA mapeada':'só proximidade/relevo: no máximo «Elevada»')+') × ativação da bacia <b>'+(w.t?['','reduzida','moderada','elevada','muito elevada'][w.t]:'sem dados')+'</b>'+(w.bump?' · +1 por albufeira cheia ou nível a subir':'')+'.</p><dl>'+metric('Área em zona APA T20 / T100',num((w.f20||0)*100,1)+' % / '+num((w.f100||0)*100,1)+' %')+metric('Residentes em zona T100 (estimativa por área)',w.pz===null?'n.d.':'~'+num(w.pz,0))+metric('Idade 0–14 e 65+ nessa zona (est.)',w.vul===null?'n.d.':'~'+num(w.vul,0))+'</dl>';
  const b=basins[0];
  if(b)html+='<h3>Chuva → escoamento · bacia #'+E(b.id)+'</h3><dl>'+metric('Fonte',E(b.source==='IPMA'?'Estações IPMA':'Modelo ECMWF')+' · '+date(b.valid_time))+metric('Chuva 1 / 6 / 24 h',num(b.p1_mm)+' / '+num(b.p6_mm)+' / '+num(b.p24_mm)+' mm')+metric('Previsão 6 / 24 h (modelo)',num(b.f6_mm)+' / '+num(b.f24_mm)+' mm')+metric('Humidade antecedente (proxy)',b.amc?['','seca','normal','húmida'][b.amc]+' · CN '+num(b.cn_used,0):'n.d. · CN 75')+metric('Escoamento direto',num(b.runoff_mm)+' mm')+metric('Volume escoado',b.runoff_volume_m3===null?'n.d.':num(b.runoff_volume_m3/1e6,3)+' hm³')+metric('Caudal médio 24 h',num(b.mean_flow_24h_m3s)+' m³/s')+metric('Ponta (hidrograma SCS, ordem de grandeza)',b.peak_flow_m3s===null?'não aplicável':num(b.peak_flow_m3s,0)+' m³/s')+'</dl><p>Escoamento SCS-CN agregado na bacia; sem propagação em canal nem calibração local.</p>';
  if(dams.length)html+='<h3>Albufeiras na bacia</h3>'+dams.map(d=>'<p><b>'+E(d.name)+'</b> · '+num(d.fill_percent,0)+' % ('+E(d.resolution==='monthly'?'mensal':'diário')+' '+E(d.reference)+')'+(d.class?'':' · dado antigo, não usado')+'</p>').join('');
  if(gauges.length)html+='<h3>Hidrométricas com dados recentes</h3>'+gauges.slice(0,6).map(r=>'<p><b>'+E(r.name)+'</b> · '+num(r.value,2)+(r.quantity==='level_m'?' m':' m³/s')+(r.rising?' · <b>em subida</b>':'')+'</p>').join('');
  h2.nextElementSibling.insertAdjacentHTML('afterend',html);
 };
 // Wait for app.js to build the map and load parishes, then start polling.
 const wait=setInterval(()=>{if(typeof map!=='undefined'&&map?.getLayer?.('parishes-fill')&&data.parishes){clearInterval(wait);load();setInterval(()=>{if(!document.hidden)load();},REFRESH_MS);}},250);
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)load();});
 $('refresh').addEventListener('click',()=>load());
})();
