'use strict';
const el = id => document.getElementById(id);
const number = value => Number.isFinite(value) ? new Intl.NumberFormat('pt-PT', { maximumFractionDigits: 2 }).format(value) : 'Sem dados';
const kinds = { observed: '#c45b0d', simulated: '#236ac7', rain: '#007c71', hydro: '#7140a0', dams: '#20476a' };
const empty = () => ({ type: 'FeatureCollection', features: [] });
const events = {
  '2019': ['2019-12-18', '2019-12-26', '2019-12-23'],
  '2016-02': ['2016-02-10', '2016-02-18', '2016-02-14'],
  '2016-01': ['2016-01-07', '2016-01-15', '2016-01-11'],
  '2001': ['2001-01-23', '2001-01-31', '2001-01-27'],
};
const get = async (name, format = 'json') => {
  const response = await fetch('data/' + name, { cache: 'no-cache' });
  if (!response.ok) throw new Error(name);
  return response[format]();
};
const svg = (tag, attrs) => {
  const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  el('chart').append(node);
  return node;
};
function metrics(entries) {
  el('metrics').replaceChildren(...entries.flatMap(([label, value]) => {
    const dt = document.createElement('dt'), dd = document.createElement('dd');
    dt.textContent = label;
    dd.textContent = value;
    return [dt, dd];
  }));
}
let map, popup;
let report, flow, observed, simulated, series = [], timer, revision = 0;
function data(id, collection = empty()) {
  map?.getSource(id)?.setData(collection);
}
function visibility(id) {
  if (map?.getLayer(id)) map.setLayoutProperty(id, 'visibility', el(id).checked ? 'visible' : 'none');
}
function chart(index) {
  el('chart').querySelectorAll(':not(title)').forEach(node => node.remove());
  const top = Math.max(1, ...series.map(row => row.value ?? 0));
  const x = i => 58 + i * 563 / Math.max(1, series.length - 1);
  const y = value => 111 - 93 * value / top;
  for (const value of [0, top / 2, top]) {
    const height = y(value);
    svg('line', { x1: 58, x2: 621, y1: height, y2: height, stroke: '#d6e4e1' });
    svg('text', { x: 4, y: height + 4, fill: '#48635f', 'font-size': 12 }).textContent = number(value);
  }
  for (let i = 0; i < series.length; i++) {
    const row = series[i], previous = series[i - 1];
    if (!Number.isFinite(row.value)) continue;
    if (Number.isFinite(previous?.value)) {
      svg('line', { x1: x(i - 1), y1: y(previous.value), x2: x(i), y2: y(row.value), stroke: '#065752', 'stroke-width': 3 });
    }
    svg('circle', { cx: x(i), cy: y(row.value), r: i === index ? 6 : 3, fill: i === index ? '#c45b0d' : '#065752' });
  }
  for (const i of new Set([0, index, series.length - 1])) {
    svg('text', { x: x(i), y: 134, 'text-anchor': 'middle', fill: '#48635f', 'font-size': 12 }).textContent = series[i].date.slice(5);
  }
}
function renderDay() {
  const index = Number(el('day').value), { date, value } = series[index];
  el('date').textContent = date;
  el('day').setAttribute('aria-valuetext', date);
  const scenario = report.events.find(entry => entry.date === date && entry.duration_assumed_h === 24);
  const match = date === report.observation_time_utc.slice(0, 10);
  data('observed', match ? observed : empty());
  data('simulated', points(simulated, ({ properties }) => properties.date === date));
  chart(index);
  const entries = [['Caudal descarregado', Number.isFinite(value) ? number(value) + ' m³/s' : 'Sem dados']];
  if (scenario) entries.push(['Área simulada total (cenário de 24 h)', number(scenario.overbank_area_m2 / 10000) + ' ha']);
  if (match && scenario?.comparison) {
    entries.push(['Área observada na grelha comum', number(scenario.comparison.observed_area_m2 / 10000) + ' ha'],
      ['Área simulada na grelha comum', number(scenario.comparison.simulated_area_m2 / 10000) + ' ha'],
      ['Interseção na grelha comum', number(scenario.comparison.intersection_m2 / 10000) + ' ha']);
  }
  metrics(entries);
  el('notice').textContent = match
    ? 'Sentinel-1A, 23/12 às 06:43 UTC. O cenário usa a média diária. O confronto espacial falhou.'
    : scenario
      ? 'Mancha exploratória do piloto para este dia. Sem observação independente comparável.'
      : 'Sem mancha disponível para este dia. O gráfico mostra observações diárias.';
}
const recent = (time, now) => Number.isFinite(Date.parse(time)) && Date.parse(time) <= now && now - Date.parse(time) <= 10800000;
function points(collection, predicate) {
  return { ...empty(), features: collection?.features.filter(predicate) ?? [] };
}
function stop() {
  clearInterval(timer);
  timer = undefined;
  el('play').textContent = 'Reproduzir';
}
async function render() {
  const request = ++revision;
  stop();
  popup?.remove();
  const event = el('event').value;
  const historical = Boolean(events[event]);
  el('historical-layers').hidden = !historical;
  el('live-layers').hidden = event !== 'live';
  el('timeline').hidden = !historical;
  for (const id of Object.keys(kinds)) data(id);
  metrics([]);
  if (historical) {
    const [start, end, selected] = events[event];
    series = [];
    for (let t = Date.parse(start); t <= Date.parse(end); t += 86400000) {
      const date = new Date(t).toISOString().slice(0, 10);
      series.push({ date, value: flow.get(date) });
    }
    el('day').max = series.length - 1;
    el('day').value = series.findIndex(row => row.date === selected);
    map?.jumpTo({ center: [-8.446, 40.203], zoom: 11.3 });
    renderDay();
    return;
  }
  map?.jumpTo({ center: [-8.1, 39.6], zoom: 5.6 });
  if (event === 'charles') {
    el('notice').textContent = 'A depressão passou em 11/11/2026. O arquivo de telemetria do evento está no ambiente privado. A comparação espacial aguarda uma mancha independente.';
    return;
  }
  el('notice').textContent = 'A verificar a data das observações…';
  const results = await Promise.allSettled([get('stations.geojson'), get('snirh-observations.geojson')]);
  if (request !== revision) return;
  const [weather, telemetry] = results.map(result => result.status === 'fulfilled' ? result.value : null);
  const now = Date.now();
  const rain = points(weather, ({ properties: p }) => recent(p.observed_at, now) && Number.isFinite(p.p1));
  const hydro = points(telemetry, ({ properties: p }) => !p.collection_error && p.type === 'estacao_hidrometrica' &&
    ['flow_m3s', 'level_m', 'elevation_m'].some(key => Number.isFinite(p[key]) && recent(p[key + '_time'], now)));
  const dams = points(telemetry, ({ properties: p }) => !p.collection_error && p.type === 'estacao_albufeira' &&
    ['outflow_m3s', 'inflow_m3s', 'storage_percent', 'elevation_m', 'level_m'].some(key => Number.isFinite(p[key]) && recent(p[key + '_time'], now)));
  for (const [id, collection] of Object.entries({ rain, hydro, dams })) data(id, collection);
  metrics([['IPMA · estações com chuva horária recente', weather ? number(rain.features.length) : 'Indisponível'],
    ['SNIRH · estações recentes', telemetry ? number(hydro.features.length) : 'Indisponível'],
    ['SNIRH · albufeiras com dados recentes', telemetry ? number(dams.features.length) : 'Indisponível']]);
  el('notice').textContent = 'Observações das últimas três horas. Uma camada vazia indica ausência de registos recentes neste painel.';
}
async function initialize() {
  try {
    let csv;
    [report, csv, observed, simulated] = await Promise.all([
      get('coimbra-validation.json'), get('coimbra-weir-daily.csv', 'text'),
      get('coimbra-observed-2019.geojson'), get('coimbra-hindcast-frames.geojson'),
    ]);
    flow = new Map(csv.trim().split(/\r?\n/).slice(1).map(line => {
      const [date, , , value] = line.split(',');
      return [date, value ? Number(value) : null];
    }));
  } catch {
    el('notice').textContent = 'Os dados históricos não puderam ser carregados. Consulte Validação e fontes.';
    return;
  }

  el('day').addEventListener('input', () => { stop(); renderDay(); });
  el('play').addEventListener('click', () => {
    if (timer) return stop();
    el('play').textContent = 'Pausar';
    timer = setInterval(() => {
      el('day').value = (Number(el('day').value) + 1) % series.length;
      renderDay();
    }, 850);
  });
  el('event').addEventListener('change', render);
  for (const id of Object.keys(kinds)) el(id).addEventListener('change', () => visibility(id));
  try {
    map = new maplibregl.Map({ container: 'map', center: [-8.446, 40.203], zoom: 11.3, style: {
      version: 8,
      sources: { osm: { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256, attribution: '© OpenStreetMap contributors' } },
      layers: [{ id: 'base', type: 'raster', source: 'osm' }],
    } });
    map.addControl(new maplibregl.NavigationControl());
    map.on('load', () => {
      for (const [id, color] of Object.entries(kinds)) {
        const polygon = ['observed', 'simulated'].includes(id);
        map.addSource(id, { type: 'geojson', data: empty() });
        map.addLayer({ id, type: polygon ? 'fill' : 'circle', source: id, paint: polygon
          ? { 'fill-color': color, 'fill-opacity': 0.65, 'fill-outline-color': color }
          : { 'circle-color': color, 'circle-radius': 5, 'circle-stroke-width': 1, 'circle-stroke-color': '#fff' } });
        visibility(id);
      }
      map.on('click', event => {
        const feature = map.queryRenderedFeatures(event.point, { layers: ['rain', 'hydro', 'dams'] })[0];
        if (!feature) return;
        const p = feature.properties, content = document.createElement('div');
        const title = document.createElement('strong');
        title.textContent = p.name;
        content.append(title);
        const names = { p1: 'Chuva 1 h (mm)', flow_m3s: 'Caudal (m³/s)', inflow_m3s: 'Afluência (m³/s)',
          outflow_m3s: 'Descarga (m³/s)', storage_percent: 'Enchimento (%)', elevation_m: 'Cota (m)', level_m: 'Nível (m)' };
        for (const [key, label] of Object.entries(names)) {
          const time = key === 'p1' ? p.observed_at : p[key + '_time'];
          if (!recent(time, Date.now()) || !Number.isFinite(p[key])) continue;
          const row = document.createElement('div');
          row.textContent = label + ' · ' + number(p[key]) + ' · ' + new Date(time).toISOString();
          content.append(row);
        }
        popup?.remove();
        popup = new maplibregl.Popup().setLngLat(event.lngLat).setDOMContent(content).addTo(map);
      });
      render();
    });
  } catch {
    el('map').textContent = 'Mapa indisponível neste navegador. O gráfico e os indicadores continuam acessíveis.';
    map = null;
  }
  await render();
  setInterval(() => { if (el('event').value === 'live') render(); }, 300000);
}
initialize();
