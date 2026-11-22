"""Gera a camada GeoJSON (ArcGIS Online) e o visualizador autónomo (HTML com dados embebidos).
Só lê ficheiros do repositório; não inventa dados. Uso: python ai/tool/build_tool.py"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
D = ROOT / "dist" / "data"
OUT = pathlib.Path(__file__).resolve().parent
MARK = "EXPERIMENTAL — NÃO OPERACIONAL"

SPEC = [
    ("coimbra-observed-2019.geojson", "observado_sar_2019", "observado",
     "Copernicus EMSR417 AOI01 v1, Sentinel-1A 2019-12-23 06:43 UTC (recorte do piloto)", None),
    ("coimbra-hindcast-2019.geojson", "simulado_piloto_2019", "modelo",
     "Piloto hidráulico IGNISPYRO (caudal médio diário, não calibrado)", lambda p: p.get("date") == "2019-12-23"),
    ("hydraulic-coverage.geojson", "dominio_piloto", "derivado",
     "Domínio do piloto Mondego/Coimbra (grelha 30 m)", None),
]

feats = []
for fname, layer, nature, source, flt in SPEC:
    for f in json.loads((D / fname).read_text(encoding="utf-8"))["features"]:
        if flt and not flt(f.get("properties", {})):
            continue
        feats.append({"type": "Feature", "geometry": f["geometry"], "properties": {
            "camada": layer, "natureza": nature, "fonte": source,
            "estado": MARK, "nota": "Não é aviso, previsão oficial nem mancha de segurança"}})

coll = {"type": "FeatureCollection", "name": "floods_ai_evidencia", "features": feats}
(OUT / "layers" / "floods-ai-evidence.geojson").write_text(json.dumps(coll, ensure_ascii=False), encoding="utf-8")

# camada opcional de resultados de modelo (só existe se houver modelo validado)
model_path = ROOT / "ai" / "outputs" / "model-score.geojson"
model = json.loads(model_path.read_text(encoding="utf-8")) if model_path.exists() else None

tpl = (OUT / "viewer.template.html").read_text(encoding="utf-8")
html = tpl.replace("/*DATA*/null", json.dumps(coll, ensure_ascii=False)).replace("/*MODEL*/null", json.dumps(model))
(OUT / "floods-ai-viewer.html").write_text(html, encoding="utf-8")
print(len(feats), "feições;", "modelo:", bool(model))
