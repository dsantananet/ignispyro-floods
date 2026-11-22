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
Plataforma HTML independente (`index.html`): colore as freguesias a verde/amarelo/laranja/vermelho com os dados em tempo real do Floods (`?base=URL/` para outra origem).
Modelo atual: **regras v0, não aprendido** (`core.js`). A camada de IA só entra quando houver validação em eventos independentes.
Tabela para ArcGIS Online (juntar a CAOP por `dtmnfr`): `node ai/susceptibility/build-layer.mjs [dirDados] [dirSaida]`.
Regenerar o HTML: `python ai/susceptibility/build_viewer.py`. Testes: `node --test ai/tests/*.test.cjs`.
