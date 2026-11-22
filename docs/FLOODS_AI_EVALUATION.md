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

**Dados.** Pacotes de delineação Copernicus EMS (API pública; © União Europeia, Copernicus EMS): EMSR864 (tempestade Leonardo, fev. 2026) — 12 áreas com delineação (Ermidas Sado, Salvaterra de Magos, Leiria, Coimbra, Aveiro, Barcelos, Ponte de Lima, Chaves, Tomar, Mértola, Mira, Minho) — e EMSR861 (Kristin, jan. 2026) — Coimbra. As restantes áreas de EMSR861 são espanholas (Castelo Branco não tem delineação). Rio de Moinhos (AOI02) não gerou freguesias elegíveis. Porto, Marco de Canaveses, Peso da Régua, Santo Tirso e Silves não foram descarregadas (por obter). Rótulos em `ai/data/labels/parish_labels_emsr.csv` (script `ai/features/emsr_parish_labels.py`, manifesto com SHA-256 dos pacotes).

**Regra de rótulo (fixada antes de ver as métricas).** Freguesia com ≥50 % da área dentro da AOI; y=1 se cheia observada ≥5 ha e ≥0,5 % da freguesia. y=0 = "sem cheia detetada", não "seco confirmado": continua a não haver negativos observados.

**Resultado (562 freguesias, 177 positivas, prevalência 0.31; 13 áreas; `ai/validation/static_backtest.py`):**

| Variável | ROC-AUC | PR-AUC | IC 95 % (bootstrap por AOI) |
|---|---|---|---|
| IAS estrutural (score) | 0.88 | 0.73 | 0.77–0.91 |
| IAS estrutural (classe 1–5) | 0.87 | 0.72 | 0.76–0.90 |
| Fração em zona APA T100 | 0.86 | 0.79 | 0.74–0.91 |
| Fração em zona APA T1000 | 0.85 | 0.78 | 0.74–0.91 |
| HAND < 5 m | 0.78 | 0.66 | 0.68–0.81 |
| Proximidade de rio (300 m) | 0.68 | 0.42 | 0.54–0.72 |

**Leitura.**
- Com mais bacias (Mondego, Tejo, Sado, Vouga, Cávado, Lima, Tâmega, Mira…) a componente estrutural mantém discriminação útil (AUC 0,88; AUC por área entre 0,67 e 1,0 nas áreas com ≥5 freguesias), mas é diagnóstico descritivo, não validação independente: são só dois eventos meteorológicos e as áreas foram escolhidas pelo Copernicus por terem cheia (viés de seleção).
- A fração em zona APA T100 sozinha tem PR-AUC igual ou superior ao score composto (0,79 vs 0,73) e AUC ligeiramente inferior (0,86 vs 0,88): HAND e rio acrescentam pouco ou nada de forma consistente. A proximidade de rio é a variável mais fraca.
- Onde não há zona APA (Tomar, Mértola) a componente falha (poucos positivos: 1–2).
- Não foi possível retroanalisar a ativação em tempo real (componente dinâmica): o `floodwatch.json` dessas datas não está guardado e a chuva observada de jan.–fev. 2026 não está acessível a partir deste ambiente.
- Portão de treino (≥10 eventos, ≥4 bacias, ≥200 negativos observados): bacias já ≥4, mas **eventos = 2 e negativos observados = 0**. Não se treinou RF/XGBoost.
