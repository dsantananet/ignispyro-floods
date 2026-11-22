"""Gera ai/susceptibility/gfm-collector.html a partir de gfm-collector.js (script embebido para copiar/colar). EXPERIMENTAL — NÃO OPERACIONAL."""
import html, pathlib
D = pathlib.Path(__file__).parent
js = (D / 'gfm-collector.js').read_text(encoding='utf-8')
page = f'''<!doctype html><html lang="pt"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GFM por freguesia — recolha no browser (EXPERIMENTAL)</title>
<style>body{{font:15px/1.5 system-ui,sans-serif;max-width:820px;margin:24px auto;padding:0 16px;color:#0f172a}}
.tag{{background:#f59e0b;padding:2px 8px;border-radius:4px;font-weight:700;font-size:12px}}ol li{{margin:10px 0}}
button,a.btn{{background:#0f172a;color:#fff;border:0;border-radius:6px;padding:8px 14px;font-size:14px;cursor:pointer;text-decoration:none;display:inline-block}}
textarea{{width:100%;height:120px;font:11px monospace}}code{{background:#e2e8f0;padding:1px 5px;border-radius:4px}}.warn{{background:#fef3c7;border-left:4px solid #f59e0b;padding:8px 12px}}</style></head><body>
<h1>GFM por freguesia — recolha no browser <span class="tag">EXPERIMENTAL — NÃO OPERACIONAL</span></h1>
<p>Calcula, a partir do <b>Copernicus Global Flood Monitoring</b> (catálogo STAC público), a cheia detetada em cada freguesia para um intervalo de datas, e gera um CSV para a retroanálise <i>Floods AI</i>. Só leitura; não altera nenhum serviço.</p>
<div class="warn">Os pedidos de estatísticas só são aceites a partir do próprio anfitrião TiTiler, por isso o painel corre nesse separador (não nesta página).</div>
<ol>
<li><a class="btn" href="https://titiler.services.eodc.eu/docs" target="_blank" rel="noopener">1. Abrir o separador TiTiler</a></li>
<li><button id="cp">2. Copiar o script</button> <span id="ok"></span></li>
<li>No separador TiTiler abra a consola (F12 → Consola), escreva <code>allow pasting</code> se o Chrome pedir, cole o script e prima Enter. Aparece o painel laranja "GFM por freguesia".</li>
<li>Escolha as datas (ex.: um inverno inteiro: 2025-11-01 a 2026-03-15), o âmbito e <b>Iniciar</b>. Pode <b>Parar</b> e <b>Descarregar CSV</b> a qualquer momento, e <b>retomar</b> carregando o CSV já gravado.</li>
<li>Guarde o CSV em <code>ai/data/labels/</code> e gere rótulos: <code>python ai/features/gfm_parish_labels.py ficheiro.csv --repo .</code></li>
</ol>
<p><b>Leitura dos resultados.</b> "Sem cheia" significa não detetada por satélite (SAR), não "seco confirmado"; a cobertura válida média por freguesia é cerca de 50 %. Termos de licença do GFM a confirmar antes de redistribuir dados.</p>
<textarea id="src" readonly>{html.escape(js)}</textarea>
<script>document.getElementById('cp').onclick=async()=>{{const t=document.getElementById('src');t.select();try{{await navigator.clipboard.writeText(t.value);document.getElementById('ok').textContent='Copiado ✓'}}catch(e){{document.execCommand('copy');document.getElementById('ok').textContent='Copiado ✓ (ou use Ctrl+C na caixa abaixo)'}}}}</script>
</body></html>'''
(D / 'gfm-collector.html').write_text(page, encoding='utf-8')
print('gerado', len(page), 'bytes')
