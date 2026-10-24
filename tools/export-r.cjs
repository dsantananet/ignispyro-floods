const fs=require('node:fs');
const j=JSON.parse(fs.readFileSync('dist/data/coimbra-weir-history.json','utf8'));
const columns=['date','inflow_daily_m3s','outflow_daily_m3s','discharged_daily_m3s','elevation_sample_count','elevation_full_24h','elevation_mean_m','flags_present'];
fs.writeFileSync('dist/data/coimbra-weir-daily.csv',columns.join(',')+'\n'+j.daily.map(r=>columns.map(k=>r[k]===null?'':typeof r[k]==='boolean'?Number(r[k]):r[k]).join(',')).join('\n')+'\n');
