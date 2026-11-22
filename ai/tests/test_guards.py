"""Testes de guarda: isolamento do Floods AI (stdlib apenas)."""
import json, pathlib, re, unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
WF = ROOT / ".github" / "workflows" / "floods-ai-research.yml"
FORBIDDEN = [r"pages:\s*write", r"id-token", r"deploy-pages", r"upload-pages-artifact",
             r"\bschedule\s*:", r"\bssh\b", r"tailscale", r"cloudflare", r"qnap", r"asustor",
             r"\brsync\b", r"secrets\.", r"push\s*:", r"pull_request"]


class WorkflowGuard(unittest.TestCase):
    def setUp(self):
        self.text = WF.read_text(encoding="utf-8")

    def test_manual_only(self):
        self.assertIn("workflow_dispatch", self.text)

    def test_no_forbidden_constructs(self):
        for pat in FORBIDDEN:
            self.assertIsNone(re.search(pat, self.text, re.I), pat)

    def test_least_privilege(self):
        self.assertRegex(self.text, r"contents:\s*read")
        self.assertNotRegex(self.text, r"contents:\s*write")

    def test_restricted_to_experimental_branch(self):
        self.assertIn("feature/floods-ai-research", self.text)


class ExistingWorkflowsUntouchedByAI(unittest.TestCase):
    def test_publish_does_not_reference_ai(self):
        for f in (ROOT / ".github" / "workflows").glob("*.yml"):
            if f.name == WF.name:
                continue
            self.assertNotIn("ai/", f.read_text(encoding="utf-8"), f.name)


class OutputsPolicy(unittest.TestCase):
    def test_no_ai_outputs_in_dist(self):
        self.assertEqual(list((ROOT / "dist").rglob("*floods-ai*")), [])


class Manifest(unittest.TestCase):
    def test_sources_have_required_fields(self):
        m = json.loads((ROOT / "ai/data/manifests/sources.json").read_text(encoding="utf-8"))
        for s in m["sources"]:
            for k in ("id", "nature", "role", "license", "status"):
                self.assertIn(k, s)
            self.assertIn(s["nature"], {"observado", "estimado", "modelo", "derivado"})


if __name__ == "__main__":
    unittest.main()


class ViewerGuard(unittest.TestCase):
    def test_layer_marked_experimental(self):
        d = json.loads((ROOT / "ai/tool/layers/floods-ai-evidence.geojson").read_text(encoding="utf-8"))
        self.assertTrue(d["features"])
        for f in d["features"]:
            self.assertIn("EXPERIMENTAL", f["properties"]["estado"])
            self.assertIn(f["properties"]["natureza"], {"observado", "estimado", "modelo", "derivado"})

    def test_viewer_marked_and_self_contained(self):
        h = (ROOT / "ai/tool/floods-ai-viewer.html").read_text(encoding="utf-8")
        self.assertIn("EXPERIMENTAL — NÃO OPERACIONAL", h)
        self.assertNotIn("/*DATA*/", h)
        self.assertNotRegex(h, r"(?i)qnap|asustor|tailscale")

    def test_viewer_up_to_date(self):
        import subprocess, sys, hashlib
        p = ROOT / "ai/tool/floods-ai-viewer.html"
        before = hashlib.sha256(p.read_bytes()).hexdigest()
        subprocess.run([sys.executable, str(ROOT / "ai/tool/build_tool.py")], check=True, capture_output=True)
        self.assertEqual(before, hashlib.sha256(p.read_bytes()).hexdigest(), "reexecutar ai/tool/build_tool.py")
