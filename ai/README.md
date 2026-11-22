# Floods AI — investigação experimental

**EXPERIMENTAL — NÃO OPERACIONAL.** Isolado do módulo Floods e do IGNISPYRO V2.
Plano: ver `docs/FLOODS_AI_EVALUATION.md` (auditoria inicial e decisão).

## Estado
Modelação **interrompida**: dados atuais com 1 evento positivo independente (EMSR417, 2019) e 0 negativos fiáveis.
Não há código de treino. Só há inventário de dados, testes de guarda e um workflow manual que corre esses testes.

## Regras
- Trabalhar só nesta branch; sem merge para `main` sem aprovação explícita.
- Nada em `dist/`; resultados em `ai/outputs/` ou artefactos privados.
- Sem NAS, SSH, Pages, deploy, agendamentos.
- Todo o mapa/output leva a marca "EXPERIMENTAL — NÃO OPERACIONAL".

## Testes de guarda
`python -m unittest discover -s ai/tests`

## Ferramenta visual (independente do Floods)
Painel de adequação com mapa: `ai/tool/floods-ai-viewer.html` (autónomo, dados embebidos; abrir localmente ou
[pré-visualizar](https://htmlpreview.github.io/?https://github.com/dsantananet/ignispyro-floods/blob/feature/floods-ai-research/ai/tool/floods-ai-viewer.html) — serviço de terceiros, só para consulta).
Mostra evidência observada vs. simulada, portão de decisão e, se existir, `ai/outputs/model-score.geojson`.
Regenerar: `python ai/tool/build_tool.py`.

Camada para ArcGIS Online: `ai/tool/layers/floods-ai-evidence.geojson` (Adicionar camada a partir de ficheiro; manter a marca experimental e não partilhar publicamente).
Não há GitHub Pages nem alterações ao portal: a associação ao Floods só depois de o painel mostrar valor.

## Suscetibilidade em tempo real (`ai/susceptibility/`)
O Floods já calcula o IAS em tempo real (`tools/floodwatch.cjs` → `floodwatch.json`, de 15 em 15 min). A plataforma `index.html` mostra-o por freguesia
(verde/amarelo/laranja/vermelho/roxo) e reserva uma camada **IA** que só carrega `ai-susceptibility.json` quando existir um modelo validado.
Não há modelo de IA nem regras próprias: o baseline é o IAS do Floods. `?base=URL/` muda a origem dos dados.
Tabela para ArcGIS Online (juntar à CAOP por `dtmnfr`): `node ai/susceptibility/build-layer.mjs [floodwatch.json] [saida.csv]`.

## Treino repetido (`ai/models/harness.py`)
RF, XGBoost, logística, IAS e prevalência com validação repetida **por grupo** (evento ou bacia), bootstrap agrupado e hashes/versões. Tem um portão
(≥10 eventos positivos, ≥4 bacias, ≥200 negativos observados) e **recusa treinar** abaixo disso. Testado só em dados sintéticos (sem fuga de grupos).
Não há resultados reais: faltam rótulos (ver `docs/FLOODS_AI_EVALUATION.md`).
