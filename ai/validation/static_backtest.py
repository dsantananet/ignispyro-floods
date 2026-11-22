"""Retroanálise DESCRITIVA da componente estrutural do IAS contra rótulos EMSR (não é treino nem validação independente).
Limitações: 2 eventos meteorológicos, Mondego domina (EMSR861-05 e EMSR864-05 sobrepõem-se), AOI escolhidas onde houve cheia, y=0 = não detetado.
Uso: python ai/validation/static_backtest.py [ai/data/labels/parish_labels_emsr.csv] [saida.json]"""
import json, sys
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score
src = sys.argv[1] if len(sys.argv) > 1 else 'ai/data/labels/parish_labels_emsr.csv'; out = sys.argv[2] if len(sys.argv) > 2 else 'ai/outputs/static_backtest.json'
D = pd.read_csv(src); VARS = ['ias_static_score', 'ias_static_class', 'f100', 'f1000', 'river300', 'hand_lt5']
def auc(d, c):
    d = d.dropna(subset=[c]); return float(roc_auc_score(d.y, d[c])) if d.y.nunique() > 1 else None
def ap(d, c):
    d = d.dropna(subset=[c]); return float(average_precision_score(d.y, d[c])) if d.y.nunique() > 1 else None
def boot(c, n=500, seed=0):
    rng = np.random.default_rng(seed); keys = list(D.groupby(['ems', 'aoi']).groups); idx = {k: D[(D.ems == k[0]) & (D.aoi == k[1])] for k in keys}; v = []
    for _ in range(n):
        s = pd.concat([idx[keys[i]] for i in rng.integers(0, len(keys), len(keys))]); a = auc(s, c)
        if a is not None: v.append(a)
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if v else None
res = {'n': len(D), 'positives': int(D.y.sum()), 'prevalence': float(D.y.mean()), 'por_variavel': {}}
for c in VARS:
    res['por_variavel'][c] = {'auc_pooled': auc(D, c), 'ap_pooled': ap(D, c), 'auc_ci95_bootstrap_por_AOI': boot(c),
                              'auc_por_AOI': {f'{e}-{a}': (None if auc(g, c) is None else round(auc(g, c), 2)) for (e, a), g in D.groupby(['ems', 'aoi'])}}
res['aviso'] = 'Descritivo; IC por bootstrap de AOI com apenas 6 AOI e 2 eventos meteorológicos — muito largo. EXPERIMENTAL — NÃO OPERACIONAL.'
import os; os.makedirs(os.path.dirname(out) or '.', exist_ok=True); json.dump(res, open(out, 'w'), indent=1)
for c, r in res['por_variavel'].items(): print(c, round(r['auc_pooled'], 3), 'AP', round(r['ap_pooled'], 3), 'IC95', [round(x, 2) for x in r['auc_ci95_bootstrap_por_AOI']] if r['auc_ci95_bootstrap_por_AOI'] else None)
print('prevalência', round(res['prevalence'], 3))
