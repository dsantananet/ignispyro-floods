"""Gera ai/susceptibility/index.html (autónomo) com core.js embebido. Uso: python ai/susceptibility/build_viewer.py"""
import pathlib
d = pathlib.Path(__file__).resolve().parent
t = (d / "viewer.template.html").read_text(encoding="utf-8")
(d / "index.html").write_text(t.replace("/*CORE*/", (d / "core.js").read_text(encoding="utf-8")), encoding="utf-8")
