'use strict';
/* Basemap selector: streets, satellite imagery, hybrid (imagery + labels), topographic, light. Choice is remembered per browser. */
(function(){
 const ESRI='https://server.arcgisonline.com/ArcGIS/rest/services/',ESRI_ATTR='Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community',CARTO_ATTR='© CARTO © OpenStreetMap contributors';
 const SOURCES={
  imagery:{tiles:[ESRI+'World_Imagery/MapServer/tile/{z}/{y}/{x}'],attribution:ESRI_ATTR,maxzoom:18},
  topo:{tiles:[ESRI+'World_Topo_Map/MapServer/tile/{z}/{y}/{x}'],attribution:'Tiles © Esri — Esri, DeLorme, NAVTEQ, USGS, NPS',maxzoom:18},
  light:{tiles:['https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png','https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png'],attribution:CARTO_ATTR,maxzoom:19},
  labels:{tiles:[ESRI+'Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}'],attribution:ESRI_ATTR,maxzoom:18}
 };
 // layers shown per option ('base' = OpenStreetMap, always present in the style)
 const OPTIONS=[['osm','Mapa',['base']],['imagery','Satélite',['bm-imagery']],['hybrid','Híbrido',['bm-imagery','bm-labels']],['topo','Topográfico',['bm-topo']],['light','Claro',['bm-light']]];
 const ALL=['base','bm-imagery','bm-topo','bm-light','bm-labels'];
 let current='osm';
 try{const saved=localStorage.getItem('floods-basemap');if(OPTIONS.some(o=>o[0]===saved))current=saved;}catch(e){}
 function apply(id){
  const opt=OPTIONS.find(o=>o[0]===id);if(!opt||!map?.getLayer('base'))return;current=id;
  for(const l of ALL)if(map.getLayer(l))map.setLayoutProperty(l,'visibility',opt[2].includes(l)?'visible':'none');
  document.querySelectorAll('.bm-switch button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.id===id)));
  try{localStorage.setItem('floods-basemap',id);}catch(e){}
 }
 function setup(){
  const first=map.getStyle().layers.find(l=>l.id!=='base')?.id;
  for(const k of ['imagery','topo','light','labels'])map.addSource('bm-'+k,{type:'raster',tileSize:256,...SOURCES[k]});
  for(const k of ['imagery','topo','light'])map.addLayer({id:'bm-'+k,type:'raster',source:'bm-'+k,layout:{visibility:'none'}},first);
  map.addLayer({id:'bm-labels',type:'raster',source:'bm-labels',layout:{visibility:'none'}}); // labels stay above the data layers
  const box=document.createElement('div');box.className='bm-switch';box.setAttribute('role','group');box.setAttribute('aria-label','Mapa base');
  box.innerHTML=OPTIONS.map(o=>'<button type="button" data-id="'+o[0]+'" aria-pressed="false">'+o[1]+'</button>').join('');
  box.addEventListener('click',e=>{const b=e.target.closest('button');if(b)apply(b.dataset.id);});
  document.querySelector('.map-region').append(box);apply(current);
 }
 const wait=setInterval(()=>{if(typeof map!=='undefined'&&map?.getLayer?.('parishes-fill')){clearInterval(wait);setup();}},250);
})();
