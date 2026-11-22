import pathlib, sys, unittest
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "models"))
import harness as H


def synth(events=14, basins=5, n=120, signal=True, seed=0):
    rng = np.random.default_rng(seed); rows = []
    for e in range(events):
        b = e % basins; shift = rng.normal()
        for i in range(n):
            x1, x2 = rng.normal(), rng.normal(); y = int((1.5 * x1 + shift + rng.normal()) > 1.0) if signal else int(rng.random() < .3)
            rows.append(dict(event_id=e, basin_id=b, y=y, neg_observed=1, ias=int(np.clip(2 + x1 + rng.normal(), 0, 5)), x1=x1, x2=x2))
    return pd.DataFrame(rows)


class Harness(unittest.TestCase):
    def test_gate_refuses_real_world_sized_data(self):
        df = synth(events=2, basins=1, n=50)
        r = H.run(df, "event_id", 2, 3)
        self.assertEqual(r["status"], "RECUSADO_PELO_PORTAO")

    def test_no_group_leakage(self):
        df = synth(); g = df.event_id.to_numpy()
        for tr, te in H.split_groups(g, 5, 7):
            self.assertFalse(set(g[tr]) & set(g[te]))

    def test_runs_on_synthetic_and_beats_prevalence(self):
        r = H.run(synth(), "event_id", 2, 4)
        self.assertEqual(r["status"], "EXECUTADO")
        self.assertGreater(r["resultados"]["xgboost"]["roc_auc"], 0.7)
        self.assertLess(r["resultados"]["xgboost"]["brier"], r["resultados"]["prevalencia"]["brier"] + 0.02)

    def test_noise_gives_no_skill(self):
        r = H.run(synth(signal=False), "event_id", 2, 4)
        self.assertLess(r["resultados"]["random_forest"]["roc_auc"], 0.6)


if __name__ == "__main__":
    unittest.main()
