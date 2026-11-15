# Consolidação Floods · IGNISPYRO v2

## Origem e cópia de segurança

A base auditada foi a branch `main` em `17c78695154445e11eb00fd33c4707e851fe9bf6`. O espelho Git e o bundle local com nove referências passaram `git fsck --full` e `git bundle verify`. SHA-256 do bundle: `e06033f98f8abb94b38b5c33bc7b053c1505af225c71ae0852572dd8e05559ff`.

Os três documentos de `dsantananet/ignispyro-motor-cheias` entraram em [legado-motor-cheias](legado-motor-cheias/) sem alterações de conteúdo, com a ponta original `00f93293dab1c0a3338540b0a80a61188cbad32e` como segundo pai do commit de importação. A arquitetura ArcGIS, o exemplo Python, os limiares absolutos e as percentagens fixas por freguesia são propostas históricas, sem estatuto operacional. Para integrar preservando os identificadores dos commits, usar merge com commit. Um squash perderia a ligação de ancestralidade. O repositório arquivado fica como backup.

A versão do coletor NAS proveniente do [PR #1](https://github.com/dsantananet/ignispyro-floods/pull/1) usa o parser APA/SNIRH comum. O coletor mantém as classificações de observação IPMA e estimativa ECMWF separadas. Registos de enchimento e descarga de albufeiras vêm da mesma recolha APA/SNIRH. Os boletins mensais já existentes servem de contexto. A execução isolada com `--once` terminou com as três fontes disponíveis em 15/11/2026. A execução local não alterou o coletor de produção.

## Hidráulica e simulação

O piloto existente de caudal diário/secções continua a servir a comparação histórica. O motor novo em `engine/shallow_water.py` resolve as equações bidimensionais de águas pouco profundas em grelha métrica, com fluxo de Rusanov, reconstrução hidrostática, secagem/molhagem, atrito de Manning e passo adaptativo. A interface é a mesma para uma janela histórica congelada ou uma janela recente autorizada.

Executar `python engine/run_2d.py entradas.npz resultados.npz` com NumPy. O ficheiro de entrada contém `bed_m` e `depth_m` (matrizes), `cell_m` (escalar), `seconds` (de 0 até ao último quadro, estritamente crescente) e `net_m3s` (uma matriz de taxa líquida por intervalo). Os caudais são volumes por segundo e por célula. A saída guarda profundidade por quadro, balanço de massa e volume de retirada não satisfeito. Uma reprodução exige arquivar a grelha, datum, fontes, instante UTC inicial e janela temporal juntamente com o NPZ.

A fronteira exterior reflete o escoamento. O forçamento por célula acrescenta volume sem momento imposto; a retirada retira até ao volume disponível. Os testes são sintéticos. A utilização em Coimbra exige fronteiras abertas, jusante e caudais sincronizados, batimetria atual no mesmo datum, diques e comportas representados, calibração e uma referência independente reservada. A soma bruta de descargas de um conjunto de barragens pode contar água duas vezes. Ver [diagnóstico de continuidade e fronteiras](../dist/data/coimbra-boundaries.json). A telemetria permanece disponível para consulta. A chamada ao solver é explícita e os resultados saem sempre com estatuto experimental.

## Eventos

| Evento | Evidência utilizável | Estado |
| --- | --- | --- |
| Janeiro 2001 | Caudal diário do Açude de Coimbra, cenário do piloto de 27/01 | Reconstituição exploratória congelada. Sem mancha independente com hora. |
| Janeiro e fevereiro 2016 | Caudal diário do açude, cenários do piloto de 11/01 e 14/02 | Reconstituições exploratórias congeladas. Sem mancha independente com hora. |
| Dezembro 2019 | Caudal diário e Sentinel-1A, produto Copernicus EMSR417 AOI01 v1 | O confronto na grelha de 30 m do dia da imagem deu 10,80 ha observados, 2,16 ha simulados e 0 ha de interseção. O cenário usa caudal médio diário; a imagem é de 23/12 às 06:43 UTC. |
| Charles, novembro 2026 | 341 ciclos em arquivo privado, entre 11/11 às 10:56 UTC e 14/11 às 23:54 UTC | 247 completos e 94 parciais. 334 contêm hidrometria, 320 têm pelo menos uma descarga de albufeira recente e 322 têm pelo menos uma bacia com chuva observada utilizável. Aguarda mancha independente e inputs hidráulicos. |

Os resultados 2001–2019 referem-se ao piloto original e podem ser inspecionados em [Validação histórica de Coimbra](VALIDACAO_HISTORICA_COIMBRA.md). O novo solver ainda não tem uma execução de campo aceite. [IPMA, traçado e evolução da depressão Charles](https://www.ipma.pt/pt/media/noticias/news.detail.jsp?f=Depressao_charles.html&y=2026). A auditoria pode ser repetida no ambiente autorizado com `node nas/audit-charles.mjs /state/charles-20261111`.

## Integração no portal

A rota estática `floods-v2.html` pode ser servida junto de `dist/data/` e `dist/assets/`, dentro do módulo **Hazard → Floods**. Testar com `npm start` e abrir `http://127.0.0.1:4190/floods-v2.html`. As dependências cartográficas são MapLibre 4.7.1 e mosaicos OpenStreetMap. A aplicação lê recursos no mesmo servidor e conserva a ligação à vista nacional e ao relatório completo. A timeline diária tem reprodução automática e mantém lacunas sem interpolação. A sobreposição de 2019 usa o recorte já publicado. A vista de observações atualiza a cada cinco minutos e exclui medições sem hora válida ou com mais de três horas. O modo Charles público mostra a disponibilidade do estudo, com a telemetria bruta no ambiente autenticado.

Para ativar no gateway v2, montar a pasta estática sob a rota do módulo, testar com uma sessão autenticada e verificar os cabeçalhos e os pedidos de rede. Para servir observações privadas, usar o gateway existente com as mesmas permissões do módulo. A produção e a navegação autenticada ficam para depois da validação do PR.
