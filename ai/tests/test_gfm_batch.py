import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "features"))
from shapely.geometry import Point, box, mapping
import gfm_batch as G


class FakeResp:
    def __init__(self, code, js=None): self.status_code, self._j = code, js
    def json(self): return self._j


class Batch(unittest.TestCase):
    def test_groups_and_probe_skip(self):
        s = {'id': 'S1', 'dt': '2026-02-08T06:34', 'u': 'x', 'g': box(0, 0, 10, 10)}
        ps = [{'k': f'0101{i:02d}', 'geom': mapping(box(1, 1, 2, 2)), 'c': Point(1.5, 1.5)} for i in range(6)]
        ps.append({'k': '020101', 'geom': mapping(box(1, 1, 2, 2)), 'c': Point(50, 50)})
        gl = G.groups([s], ps)
        self.assertEqual(len(gl), 1); self.assertEqual(len(gl[0]), 6)  # fora do footprint excluída
        calls = []
        def post(url, **kw): calls.append(1); return FakeResp(500)
        self.assertEqual(G.run_group(gl[0], set(), post), [])
        self.assertEqual(len(calls), 3)  # sondagem pára após 3 falhas

    def test_valid_rows_and_resume(self):
        s = {'id': 'S1', 'dt': '2026-02-08T06:34', 'u': 'x', 'g': box(0, 0, 10, 10)}
        ps = [{'k': f'0101{i:02d}', 'geom': mapping(box(1, 1, 2, 2)), 'c': Point(1.5, 1.5)} for i in range(2)]
        stats = {'properties': {'statistics': {'b1': {'valid_pixels': 100, 'mean': 0.25, 'masked_pixels': 5}}}}
        rows = G.run_group([(s, p) for p in ps], {('010101', 'S1')}, lambda *a, **k: FakeResp(200, stats))
        self.assertEqual(rows, [['010100', 'S1', '2026-02-08T06:34', 100, 0.25, 5]][:0] or rows)
        self.assertEqual([r[0] for r in rows], ['010100'])  # 010101 já feito


class CollectorPage(unittest.TestCase):
    def test_page_embeds_script_and_label(self):
        import html
        d = Path(__file__).resolve().parents[1] / "susceptibility"
        page = (d / "gfm-collector.html").read_text(encoding="utf-8"); js = (d / "gfm-collector.js").read_text(encoding="utf-8")
        self.assertIn(html.escape(js), page)
        self.assertIn("EXPERIMENTAL — NÃO OPERACIONAL", page)
        self.assertIn("EXPERIMENTAL — NÃO OPERACIONAL", js)
        for forbidden in ("method: 'PUT'", "method: 'DELETE'", "localStorage", "XMLHttpRequest"):
            self.assertNotIn(forbidden, js)
