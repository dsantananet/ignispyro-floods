# IgnispyroFloods

Portal experimental de chuva, escoamento e exposição populacional em Portugal continental.

- **Mapa cloud:** https://dsantananet.github.io/ignispyro-floods/
- **Relatório com figuras:** https://dsantananet.github.io/ignispyro-floods/report.html
- [Artigo em desenvolvimento](docs/ARTIGO_EM_DESENVOLVIMENTO.md)
- [População presente, Meta e operadores](docs/MOBILIDADE_E_POPULACAO_PRESENTE.md)

## Ligação SNIRH — atualização 24/10/2026

Medições reais APA/InfoÁgua de níveis, caudais, afluentes e efluentes: 155 estações do catálogo hidrométrico/albufeiras. Recolha automática de 48 h com datas por grandeza; ausências e dados antigos permanecem distintos de zero. Adaptador de páginas públicas, não API contratual documentada. Ver [calibração e expansão](docs/SNIRH_CALIBRACAO_EXPANSAO.md).

Santa Clara: zero de régua 15,45 m confirmado na ficha SNIRH; 3233 níveis diários em 2016–2025, zero caudais e zero pares utilizáveis no conjunto consultado. Não foi possível aceitar a calibração hidráulica. As descargas estão ligadas para consulta, ainda sem assimilação na mancha; não somar Aguieira e Raiva. A vista atual mantém a sinalização das freguesias bloqueada até validação.

Preparado inventário espacial para 262 bacias continentais, com medições e pendências por bacia; Açores/Madeira requerem fontes regionais. Comandos: `node tools/snirh.cjs`, `node tools/snirh-history.cjs` (histórico, ocasional), `node tools/readiness.cjs`, `python tools/expansion.py`. Ajustador de curva com separação de eventos e sem extrapolação em `engine/calibration.py`; nunca converte um teste sintético em calibração real.

## Estado real

Chuva IPMA, bacias/rios APA, CAOP2025 e BGRI2021 integrados. Volumes precipitados e escoamento SCS-CN recalculados automaticamente. ECMWF completa bacias sem observações suficientes; ERA5 2016–2025 fornece referência estimada de dez anos. Os dados de modelo são identificados.

**A vista atual não classifica freguesias como inundadas sem mancha hidráulica atual validada.** Os cenários APA T20/T100/T1000 são consultados separadamente. T10 de mancha não está ligado. O estudo Q10 diário GloFAS não é Q10 de pico instantâneo nem um modelo de profundidade na freguesia.

Os boletins de armazenamento SNIRH/ARBCAS têm datas mensais/diárias; não substituem telemetria de afluências e descargas. O cálculo hidráulico calibrado, a assimilação de barragens e a validação operacional estão pendentes. Não se assume ausência de risco quando faltam dados.

## Atualizações e execução

Node24; dependência Turf7.2.0. Instalar com `npm install` ou `pnpm install`. Depois:

```text
node tools/update.cjs
node tools/reservoirs.cjs
node tools/estimates.cjs
node tools/simulate.cjs
node tools/compress.cjs
node --test test/*.test.cjs
node serve.cjs
```

O mapa local abre em http://127.0.0.1:4190/. GitHub Actions recolhe e publica de 15 em 15 minutos; a fonte IPMA é horária, o ECMWF é reutilizado até6h. A agenda pode atrasar. Os ficheiros publicados contêm hora de consulta e validade. Não há alertas automáticos a pessoas nem notificações externas.

## Versão 0.3 — monitorização em tempo real da suscetibilidade (IAS)

Vista predefinida «Monitorização em tempo real · suscetibilidade»: cada freguesia recebe cinco classes de cor (Baixa → Crítica) que mudam a cada 15 min com a chuva, o escoamento, a previsão, as albufeiras e a subida dos níveis. **É um rastreio: não é altura de água, mancha, probabilidade nem aviso oficial.** A vista «Observações reais» mantém o bloqueio da mancha hidráulica sem validação.

```text
IAS = matriz[ suscetibilidade estrutural 1..5 , ativação da bacia 1..4 (+1 albufeira ≥90 % ou nível a subir) ]
```

- **Estrutural** (`tools/susceptibility.py` → `dist/data/susceptibility.json`): fração da freguesia em zonas APA T20/T100/T1000 e a ≤300 m de rios; com MDT (`tools/terrain-susceptibility.py`, workflow manual *terrain*) junta a fração com altura acima da drenagem mais próxima <5 m (HAND por vizinho mais próximo, Copernicus GLO-30). Pesos de especialista (zona 0,5 · MDT 0,3 · rio 0,2), não ajustados. Sem zona APA a classe não passa de «Elevada».
- **Ativação** (`tools/floodwatch.cjs`, `dist/floodwatch-core.js`): pior de chuva 1/6/24 h e escoamento SCS-CN; CN 75 corrigido pela chuva das 24 h anteriores (proxy de humidade antecedente AMC I/II/III); previsão ECMWF sobe no máximo uma classe; ponta por hidrograma unitário SCS apenas como ordem de grandeza (bacias ≤500 km²). Dados com mais de 3 h anulam a bacia; índice com mais de 12 h suspende as cores.
- **Albufeiras e hidrométricas**: enchimento (boletins SNIRH/ARBCAS, ignorados se >35 dias) e tendência de subida (APA/InfoÁgua). Não há limiares de caudal por estação, logo não há classificação absoluta.
- **População**: residentes × fração da freguesia em zona T100 (estimativa por área; as subsecções BGRI não são intersetadas nesta vista).
- **Motor hidráulico** (`engine/hydraulics.py`): acrescentado o princípio 1D estacionário do HEC-RAS — subdivisão de condutância (margens/canal), coeficiente de energia α, método *standard step* (equação de energia, perda por atrito com condutância média, perdas de contração 0,1/expansão 0,3). Regime subcrítico, sem pontes/açudes; sinaliza secções críticas. Ainda **não ligado** ao piloto de Coimbra nem à calibração.

Comandos: `node tools/floodwatch.cjs` (ciclo de 15 min no CI), `python tools/susceptibility.py` (ocasional), `FLOODWATCH_NOW=<ISO> node tools/floodwatch.cjs` para reprocessar um instantâneo antigo. Testes: `node --test test/*.test.cjs` e `python -m unittest discover -s engine -p 'test_*.py'`.

## Estudos históricos

`tools/history.cjs`: 28 referências ERA5, 3653dias, IDW3 para262bacias; preserva séries e estatísticas.
`tools/t10.cjs`: dez máximos anuais GloFAS, Gumbel por momentos e bootstrap. A referência Régua requer correção da célula e é excluída da interpretação.
`tools/spatial.py`: junções de cenários, comparação CAOP2021/2025, simplificação de visualização. Requer Shapely em ambiente isolado. Os dados originais são preservados localmente em `research/raw`, fora do Git.
`tools/report.py`: gera PNG/SVG e relatórioHTML a partir dos snapshots; requer Matplotlib. As figuras são datadas e não se fazem passar por relatório vivo.

## População

A BGRI obtida de cópia pública ArcGIS soma10 343 066residentes na geografia2021. Para versões administrativas2025,2 726freguesias têm compatibilidade geométrica≥99,5%;323requerem harmonização. O botão de exposição efetua interseções de subsecções e estima por ponderação de área. Crianças0–14e65+ são apresentados separadamente; não se presume que estes grupos representem todas as pessoas vulneráveis.

O contrato `shared/population-presence.cjs` pode ser reutilizado nas plataformas de incêndio e outros riscos. Não há dados Meta ou de operadores ligados. Dados restritos não são publicados neste repositório.

## Fontes e licenças

Fontes: IPMA; APA/SNIRH; DGT/CAOP; INE/BGRI; ARBCAS; Copernicus ERA5/GloFAS via Open-Meteo. Ver URLs/proveniência nos dados e no artigo. O espelho BGRI é alojado por DefSegMar em ArcGIS; metadados da cópia sem licença explícita, pelo que a redistribuição comercial deve ser confirmada com a fonte original. Este portal disponibiliza agregados e consulta a camada pública, sem republicar integralmente as subsecções.

A API pública Open-Meteo destina-se a utilização não comercial; utilização comercial exige serviço adequado ou alojamento próprio. Código do projeto não altera direitos sobre dados, marca ou bibliotecas. Credenciais e dados privados não pertencem ao repositório.

## Versão 0.2 publicada para avaliação operacional

[Relatório e análise em R](https://dsantananet.github.io/ignispyro-floods/operational-review.html) · [Artigo](https://dsantananet.github.io/ignispyro-floods/article.html). Ver docs/ARTIGO_AVALIACAO_OPERACIONAL.md. Arquivo adicional Açude-Ponte1987–2025, peças DWF históricas e perfil de projeto2010 localizados. Ajuste preliminar de descarga com cinco dias de treino e dois de confronto, um fora do domínio. NÃO valida a mancha operacional.

Reproduzir: `node tools/export-r.cjs`; `Rscript --vanilla tools/coimbra-analysis.R`; `node tools/package-review.cjs`; `node tools/review-document.cjs`. R de base, sem pacotes adicionais. O CI R reproduz a análise em cada alteração relevante; o cálculo histórico não é reajustado a cada15min. Descargas reais alimentam tools/coimbra-boundaries.py e o pacote de fronteiras/continuidade; a assimilação espacial fica bloqueada até validação.
# Confronto histórico de Coimbra — 24/10/2026

Resultados e dados em falta: [validation.html](https://dsantananet.github.io/ignispyro-floods/validation.html).
EMSR417 fornece uma observação SAR de 23/12/2019 06:43 UTC. As reconstituições com caudais médios diários de 2001, 2016 e 2019 são cenários exploratórios: o piloto **não obteve aceitação espacial**. As métricas de 2019 são diagnósticas e assíncronas; ausência SAR não confirma terreno seco. A população BGRI2021 representa exposição estimada, não pessoas atingidas em 2019.

Reprodução na raiz (dependências hidráulicas do projeto e matplotlib; o cache BGRI é preparado por `engine/run.py`):

```text
node --use-system-ca tools/fetch-validation.cjs
python -m zipfile -e research/emsr417-vector.zip research/emsr417
python tools/validate-coimbra.py
Rscript --vanilla tools/coimbra-validation.R
python tools/validation-document.py
```

O ZIP oficial é verificado por SHA256 antes da extração. A análise histórica fica congelada e não integra o ciclo de telemetria de 15 minutos. Código R apenas com bibliotecas base; métricas, GeoJSON e gráficos publicados em `dist/`. Testes mantêm bloqueada a aceitação operacional e proíbem inventar métricas para eventos sem mancha observada.
