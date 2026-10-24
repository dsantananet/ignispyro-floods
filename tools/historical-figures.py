import sys,pathlib,json
sys.path.insert(0,str(pathlib.Path('research/python').resolve()))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
D=pathlib.Path('dist/data');h=json.loads((D/'history.json').read_text(encoding='utf-8-sig'));q=json.loads((D/'t10.json').read_text(encoding='utf-8-sig'));nodes=json.loads((D/'history-nodes.json').read_text(encoding='utf-8-sig'));dates=nodes['dates']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(1,2,figsize=(12,5));years=list(range(2016,2026));annual=[]
for y in years:
 ids=[i for i,d in enumerate(dates) if d.startswith(str(y))];annual.append(np.mean([sum(n['precipitation_mm'][i] for i in ids) for n in nodes['nodes']]))
ax[0].bar(years,annual,color='#168e9e');ax[0].set_xticks(years);ax[0].tick_params(axis='x',rotation=45);ax[0].set_title('2016–2025 · precipitação anual ERA5');ax[0].set_ylabel('mm · média de 28 referências, sem ponderação areal')
valid=[r for r in q['stations'] if r['name']!='RÉGUA'];v=np.array([r['q10_gumbel_moments_m3s'] for r in valid]);lo=np.array([r['bootstrap95_m3s'][0] for r in valid]);hi=np.array([r['bootstrap95_m3s'][1] for r in valid]);ax[1].barh(range(len(valid)),v,color='#d28b49');ax[1].errorbar(v,range(len(valid)),xerr=[v-lo,hi-v],fmt='none',ecolor='#264550',capsize=5);ax[1].set_yticks(range(len(valid)),[r['name'].replace('PONTE SANTA CLARA ','').replace(' (SÃO JOÃO)','') for r in valid]);ax[1].set_title('Q10 diário GloFAS · estudo preliminar');ax[1].set_xlabel('m³/s · Gumbel / bootstrap95%');fig.tight_layout();fig.text(.02,-.04,'Referência modelada, não hidrometria observada. Células por validar; Régua excluída. Q10 diário não é pico instantâneo nem mancha hidráulica.',fontsize=8);fig.savefig('dist/figures/06_historico_t10.png',dpi=190,bbox_inches='tight');fig.savefig('dist/figures/06_historico_t10.svg',bbox_inches='tight');plt.close(fig)
