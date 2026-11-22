"""Gera uma versão autónoma de zip-flood-map.html com maplibre-gl e shpjs embebidos (funciona em pré-visualizações que bloqueiam scripts externos).
Uso: npm i maplibre-gl@4.7.1 shpjs@6.1.0 (num diretório) e python ai/tool/build_zip_map_standalone.py DIR_NODE_MODULES SAIDA.html
O resultado não é guardado no repositório (≈1 MB, código de terceiros)."""
import pathlib, re, sys
nm = pathlib.Path(sys.argv[1]); out = pathlib.Path(sys.argv[2]); src = pathlib.Path(__file__).with_name('zip-flood-map.html').read_text(encoding='utf-8')
rd = lambda p: (nm / p).read_text(encoding='utf-8')
safe = lambda js: js.replace('</script', '<\\/script')
css = rd('maplibre-gl/dist/maplibre-gl.css'); ml = safe(rd('maplibre-gl/dist/maplibre-gl.js')); sh = safe(rd('shpjs/dist/shp.min.js'))
src = re.sub(r'<link href="https://unpkg.com/maplibre-gl@[^"]+" rel="stylesheet">', lambda m: '<style>' + css + '</style>', src)
src = re.sub(r'<script src="https://unpkg.com/maplibre-gl@[^"]+"></script>', lambda m: '<script>' + ml + '</script>', src)
src = re.sub(r'<script src="https://unpkg.com/shpjs@[^"]+"></script>', lambda m: '<script>' + sh + '</script>', src)
assert 'unpkg.com' not in src
out.write_text(src, encoding='utf-8'); print(out, len(src) // 1024, 'KB')
