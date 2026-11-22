"""Floods AI — arnês de treino/validação repetida (RF, XGBoost, logística, IAS, prevalência).
EXPERIMENTAL — NÃO OPERACIONAL. Valida SEMPRE por grupo (evento ou bacia); nunca por células aleatórias.
Recusa treinar sem massa crítica de eventos e de negativos observados (portão definido antes de ver o teste).

Tabela de entrada (CSV): event_id, basin_id, y (0/1), neg_observed (1 se o 0 é negativo observado), ias (classe 0-5 do IAS) e features numéricas.
Uso: python ai/models/harness.py dados.csv --group event_id --repeats 10 --out ai/outputs/run.json
"""
import argparse, hashlib, json, platform, sys
import numpy as np, pandas as pd
import sklearn, xgboost
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

# Portão (fixado antes de qualquer resultado de teste). Ajustar só por decisão explícita do responsável.
GATE = {"min_positive_events": 10, "min_basins": 4, "min_observed_negatives": 200}
NONFEAT = {"event_id", "basin_id", "cell_id", "y", "neg_observed", "ias", "t"}


def gate(df):
    pos_ev = df.loc[df.y == 1, "event_id"].nunique()
    neg = int(((df.y == 0) & (df.neg_observed == 1)).sum())
    res = {"positive_events": int(pos_ev), "basins": int(df.basin_id.nunique()), "observed_negatives": neg}
    miss = [k for k, v in [("min_positive_events", pos_ev), ("min_basins", res["basins"]), ("min_observed_negatives", neg)] if v < GATE[k]]
    return res, miss


def models(seed, feats):
    return {
        "prevalencia": None,
        "ias": None,
        "logistica": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced", random_state=seed)),
        "random_forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=5, class_weight="balanced", n_jobs=2, random_state=seed),
        "xgboost": XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
                                 reg_lambda=1.0, eval_metric="logloss", n_jobs=2, random_state=seed, verbosity=0),
    }


def split_groups(groups, k, seed):
    """Folds por grupo com ordem de grupos embaralhada pela semente: nenhum grupo aparece em treino e teste."""
    u = np.unique(groups); rng = np.random.default_rng(seed); rng.shuffle(u)
    remap = {g: i for i, g in enumerate(u)}
    gi = np.array([remap[g] for g in groups])
    for tr, te in GroupKFold(n_splits=min(k, len(u))).split(np.zeros(len(gi)), groups=gi):
        assert not set(groups[tr]) & set(groups[te]), "fuga: grupo em treino e teste"
        yield tr, te


def metrics(y, p):
    out = {"brier": float(brier_score_loss(y, np.clip(p, 0, 1)))}
    out["roc_auc"] = float(roc_auc_score(y, p)) if len(set(y)) > 1 else None
    out["pr_auc"] = float(average_precision_score(y, p)) if len(set(y)) > 1 else None
    return out


def boot_ci(y, p, groups, n=300, seed=0):
    """IC 95% por bootstrap agrupado (reamostra grupos inteiros)."""
    rng = np.random.default_rng(seed); u = np.unique(groups); vals = []
    idx = {g: np.where(groups == g)[0] for g in u}
    for _ in range(n):
        s = np.concatenate([idx[g] for g in rng.choice(u, len(u))])
        if len(set(y[s])) > 1: vals.append(roc_auc_score(y[s], p[s]))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))] if vals else None


def run(df, group_col, repeats, k, force=False):
    g, miss = gate(df)
    if miss and not force:
        return {"status": "RECUSADO_PELO_PORTAO", "gate": GATE, "found": g, "failed": miss,
                "message": "Dados insuficientes para validação independente; modelação interrompida."}
    feats = [c for c in df.columns if c not in NONFEAT and pd.api.types.is_numeric_dtype(df[c])]
    X, y, grp = df[feats].to_numpy(float), df.y.to_numpy(int), df[group_col].to_numpy()
    res = {}
    for r in range(repeats):
        seed = 1000 + r; pred = {m: np.zeros(len(y)) for m in models(seed, feats)}
        for tr, te in split_groups(grp, k, seed):
            for name, mdl in models(seed, feats).items():
                if name == "prevalencia": pred[name][te] = y[tr].mean()
                elif name == "ias": pred[name][te] = df.ias.to_numpy(float)[te] / 5.0
                else:
                    mdl.fit(X[tr], y[tr]); pred[name][te] = mdl.predict_proba(X[te])[:, 1]
        for name, p in pred.items():
            res.setdefault(name, []).append({**metrics(y, p), "seed": seed, "auc_ci95_group_bootstrap": boot_ci(y, p, grp, seed=seed)})
    summ = {m: {k_: float(np.nanmean([x[k_] for x in v if x[k_] is not None])) for k_ in ("roc_auc", "pr_auc", "brier")} | {"runs": v} for m, v in res.items()}
    return {"status": "EXECUTADO", "validacao": f"grupos={group_col}, {k} folds, {repeats} repetições", "gate_found": g, "features": feats, "resultados": summ,
            "versoes": {"python": platform.python_version(), "sklearn": sklearn.__version__, "xgboost": xgboost.__version__, "numpy": np.__version__},
            "rotulo": "EXPERIMENTAL — NÃO OPERACIONAL"}


if __name__ == "__main__":
    a = argparse.ArgumentParser(); a.add_argument("csv"); a.add_argument("--group", default="event_id")
    a.add_argument("--repeats", type=int, default=10); a.add_argument("--folds", type=int, default=5); a.add_argument("--out", default="ai/outputs/run.json")
    a.add_argument("--force", action="store_true", help="só para testes sintéticos")
    a = a.parse_args(); raw = open(a.csv, "rb").read(); df = pd.read_csv(a.csv)
    out = run(df, a.group, a.repeats, a.folds, a.force); out["dados_sha256"] = hashlib.sha256(raw).hexdigest()
    json.dump(out, open(a.out, "w"), indent=1, ensure_ascii=False); print(out["status"], out.get("failed", ""))
    sys.exit(0 if out["status"] == "EXECUTADO" else 2)
