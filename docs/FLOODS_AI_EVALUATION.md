# Floods AI — Auditoria inicial de dados e decisão de modelação

**Data:** 22-11-2026 · **Repositório:** `dsantananet/ignispyro-floods` (commit `e557d5d`, leitura anónima, clone superficial)
**Estado:** EXPERIMENTAL — NÃO OPERACIONAL · **Âmbito:** só leitura; nenhuma branch criada, nada publicado.

## 1. Resumo

**Recomendação: interromper a modelação (RF/XGBoost) nesta fase e documentar as lacunas**, conforme a secção 1 e a instrução da secção 16 do plano. Os dados atualmente no repositório não permitem treino supervisionado com validação espacial/temporal independente.

Limitação desta auditoria: leitura focada em README, `docs/` (validação histórica, consolidação v2, piloto hidráulico), `coimbra-validation.json`, `national-readiness.json` e estrutura dos JSON de dados. Não li integralmente `engine/`, `tools/`, workflows nem `dist/*.js`. Antes de fechar a conclusão, completar essa leitura.

## 2. Evidência

| Requisito do plano | O que existe | Avaliação |
|---|---|---|
| Positivos (inundação confirmada, local+período) | 1 polígono independente: Copernicus EMSR417 AOI01 v1 (Sentinel-1A, 23/12/2019 06:43 UTC), 10,62 ha no recorte do piloto de Coimbra (9 468 ha na AOI completa, fora do piloto) | Um evento, uma bacia. Insuficiente |
| Negativos observados | Nenhum. O próprio relatório afirma que ausência de deteção SAR não prova terreno seco e que não há "controlos secos confirmados" | Em falta |
| Eventos 2001, 2016 | Apenas reconstituições do piloto (caudal diário do açude); "sem mancha independente com hora" | Não são observações; não usar como alvo |
| Charles (nov. 2026) | 341 ciclos de telemetria em arquivo privado; "aguarda mancha independente" | Features sim, alvo não |
| Eventos para separação por evento/bacia | 1 evento com referência espacial | Validação por evento/bacia impossível |
| Baseline IAS | `susceptibility.json` (3 049 freguesias) e `terrain-susceptibility.json` | Existe, mas é índice de rastreio, não verdade de referência |
| Profundidade observada | Nenhuma | Regressão de profundidade inadmissível |
| Prontidão nacional | `national-readiness.json` (24-10-2026): 155 estações, 66 com telemetria recente; bacias com `hydraulic_model: not_prepared`, bloqueios: geometria/datum, calibração e validação independente | Confirma lacunas |

Outras observações de qualidade:
- O piloto hidráulico (Coimbra) falhou o confronto espacial (interseção 0 ha em 2019) e está declarado não calibrado; não pode servir de rótulo nem de feature "verdade".
- A imagem de 2019 já foi usada para diagnóstico; segundo o próprio relatório, correções futuras exigem outro evento ou referência reservada.
- `history.json` (0,25°, 28 nós de referência, 3 653 datas) é reanálise/modelo, não observação de inundação; usar apenas como feature, rotulado como dado de modelo.
- Resolução heterogénea: CAOP/freguesias, bacias, grelha 30 m (GLO-30), nós 0,25°.
- Licenças/proveniência: README, `bgri-population.json` e o artigo mencionam licenças, mas não há inventário único (fonte, licença, resolução, cobertura, lacunas). Tem de ser criado.

## 3. Porque não treinar agora

Com 1 evento positivo e 0 negativos fiáveis, qualquer métrica de RF/XGBoost seria inflacionada por autocorrelação espacial (células vizinhas do mesmo evento) e não suportaria H1, H3 nem H4. Treinar produziria números sem valor científico, o que o plano proíbe expressamente (critérios "Não integrar se: faltam eventos observados ou negativos fiáveis").

## 4. O que desbloquearia a modelação

1. **Rótulos**: ≥ N eventos independentes (a fixar antes de ver resultados de teste; ordem de grandeza: dezenas de eventos em várias bacias) com perímetros observados e zonas observáveis/não observáveis. Fontes candidatas: Copernicus EMS (outras ativações em Portugal), cartografia APA de áreas inundáveis (com período de retorno e finalidade), arquivos municipais/Proteção Civil, marcas de cheia cotadas.
2. **Negativos**: áreas com evidência de observação adequada e secas, por evento; nunca "ausência de registo".
3. **Features alinhadas no tempo**: precipitação observada IPMA, hidrometria APA/SNIRH com fuso e qualidade, HAND/TWI/declive do GLO-30 (datum registado), COS, solos. Separar observado/estimado/modelo.
4. **Inventário de dados e licenças** (`ai/data/manifests/`).
5. **Critérios de aceitação** escritos antes do teste: baseline IAS e logística/prevalência, ROC-AUC, PR-AUC, Brier, calibração, IC por bootstrap agrupado por evento/bacia.

## 5. Próximos passos propostos (sem tocar no Floods existente)

1. Aprovar a criação da branch `feature/floods-ai-research` (esta sessão não conseguiu obter permissão de escrita no repositório).
2. Criar apenas o esqueleto `ai/` (README, `data/manifests`, testes de guarda contra fuga de dados e contra workflows de publicação) e um workflow `workflow_dispatch` isolado.
3. Fazer o inventário de eventos/fontes (Copernicus EMS PT, APA) para estimar se existe massa crítica de rótulos.
4. Só se o passo 3 for positivo: construir features e baselines; RF/XGBoost em último lugar.

**Resposta provisória à pergunta do plano (secção 17):** não demonstrável com os dados atuais; o Floods permanece inalterado.

## 6. Atualização — inventário de eventos (22-11-2026)

Pesquisa nas páginas do Copernicus EMS e da APA (detalhes por AOI não obtidos: as páginas de ativação são dinâmicas e as notícias não listam produtos).

| Evento | Ativação | O que se sabe | Estado |
|---|---|---|---|
| Dez. 2019, Mondego | EMSR417 | Em uso; já consumido no diagnóstico | Não reutilizável para aceitação |
| Tempestade Kristin, jan. 2026 | EMSR861 | Pedido de mapeamento de extensão de cheia e danos; afeta Coimbra, Leiria, Médio Tejo, Beira Baixa; evento desde 26/01/2026 | Candidato; produtos e AOIs por confirmar |
| Tempestade Leonardo, fev. 2026 | EMSR864 | Segundo a ESA/UE, 17 AOIs em Portugal; evento desde 03/02/2026 | Candidato; produtos e datas por confirmar |
| PGRI 2016-2021 (APA) | — | 63 ARPSI com cartas de zonas inundáveis e de risco | Baseline/contexto; modelado por período de retorno, não é rótulo de evento |

Leitura: há provavelmente 3 eventos Copernicus com mancha observada em Portugal continental (2019, jan. 2026, fev. 2026) e ainda 0 negativos fiáveis. As 17 AOIs de EMSR864 acrescentam áreas, não eventos independentes. É muito pouco para validação por evento/bacia; a conclusão da secção 1 mantém-se. Pode haver ativações anteriores a triar (a maioria das ativações RM em Portugal desde 2014 são incêndios).

Fontes: Copernicus EMS (mapping.emergency.copernicus.eu: EMSR861, EMSR864, EMSR417); ESA/UE "Storm Leonardo caused floods in central Portugal"; APA PGRI 2016-2021 (RH4A).

## 7. Dados obtidos e retroanálise descritiva do IAS estrutural (22-11-2026)

**Dados.** 15 pacotes de delineação Copernicus EMS descarregados (API pública; © União Europeia, Copernicus EMS): EMSR864 (tempestade Leonardo, fev. 2026) áreas Ermidas Sado, Leiria, Coimbra, Tomar e Mértola, e EMSR861 (tempestade Kristin, jan. 2026) área Coimbra. Faltam 20 AOI portuguesas de EMSR864 e as restantes de EMSR861. Rótulos por freguesia em `ai/data/labels/parish_labels_emsr.csv` (script `ai/features/emsr_parish_labels.py`, manifesto com SHA-256 dos pacotes).

**Regra de rótulo (fixada antes de ver as métricas).** Freguesia com ≥50 % da área dentro da AOI; y=1 se cheia observada ≥5 ha e ≥0,5 % da freguesia. y=0 significa "sem cheia detetada", não "seco confirmado" (limitações SAR): continua a não haver negativos observados.

**Resultado (362 freguesias, 84 positivas, prevalência 0,23; `ai/validation/static_backtest.py`):**

| Variável | ROC-AUC | PR-AUC | IC 95 % (bootstrap por AOI) |
|---|---|---|---|
| IAS estrutural (score) | 0,909 | 0,72 | 0,68–0,92 |
| IAS estrutural (classe 1–5) | 0,901 | 0,72 | 0,72–0,92 |
| Fração em zona APA T100 | 0,912 | 0,78 | 0,69–0,93 |
| Fração em zona APA T1000 | 0,902 | 0,77 | 0,69–0,92 |
| HAND < 5 m | 0,791 | 0,63 | 0,60–0,85 |
| Proximidade de rio (300 m) | 0,688 | 0,37 | 0,52–0,73 |

**Leitura.**
- A componente estrutural discrimina bem no Mondego (AUC ≈ 0,9 em EMSR861-Coimbra; 0,73–0,84 em EMSR864-Coimbra), mas isto é um diagnóstico descritivo, não validação independente: dois eventos meteorológicos, Mondego domina e os dois eventos sobrepõem-se geograficamente.
- A fração em zona APA T100 sozinha iguala ou supera o score composto (AUC 0,912 vs 0,909; PR-AUC 0,78 vs 0,72): a combinação com HAND e rio não acrescenta valor nestes dados. A proximidade de rio é a variável mais fraca.
- Onde não há zona APA (Tomar, Mértola) a componente falha (AUC 0,0–0,4, com 1–2 freguesias positivas): o IAS estrutural depende da cobertura APA.
- Não foi possível retroanalisar a ativação em tempo real (componente dinâmica): o `floodwatch.json` dessas datas não está no repositório (os artefactos do CI têm retenção de 30 dias) e a chuva observada de jan.–fev. 2026 não está acessível a partir deste ambiente.
- Portão de treino (≥10 eventos positivos, ≥4 bacias, ≥200 negativos observados): **continua por cumprir** (3 eventos; negativos observados 0). Não se treinou RF/XGBoost.
