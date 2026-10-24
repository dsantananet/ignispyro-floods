# Relatório de avaliação operacional

Versão pública: https://dsantananet.github.io/ignispyro-floods/operational-review.html

## 5. Resultados
O coeficiente obtido foi C = 1,499942 m^(1/2)/s. O RMSE de treino foi 19,26 m³/s. O confronto nos dois dias de 2019 produziu RMSE de 27,01 m³/s e viés de -25,95 m³/s. Este RMSE inclui um ponto fora do domínio de treino e é exclusivamente um diagnóstico de confronto. Dentro do domínio permaneceu apenas um ponto, com erro absoluto de 18,48 m³/s; um único ponto não demonstra capacidade de generalização.

O intervalo de cota do treino foi 17,8917–18,4783 m. A análise de exclusão de um evento de treino de cada vez produziu coeficientes entre 1,488854 e 1,506158. Esta amplitude é sensibilidade ao conjunto de eventos, não intervalo de confiança. Não foram calculados nem reivindicados erros de mancha, população atingida ou antecipação de alertas com base neste ajuste.

![Histórico de caudais médios diários](../dist/figures/09_r_historico.png)
![Ajuste preliminar da descarga](../dist/figures/10_r_descarga.png)
![Resíduos por dia e evento](../dist/figures/11_r_residuos.png)
![Perfil de projeto de 2010](../dist/figures/12_r_perfil_projeto.png)

## 6. Integração das descargas e limites da mancha
As afluências, efluências e cotas observadas do açude alimentam agora um pacote de condições de fronteira e um diagnóstico de continuidade. A integração trapezoidal das taxas entre amostras simultâneas fornece volumes estimados; intervalos superiores a duas horas não são preenchidos. Não se presume conhecer armazenamento inicial, derivações, evaporação ou todos os contributos laterais.

Aguieira é interna à cascata que termina em Raiva e não é somada novamente. Raiva, Fronhas e Ceira são mantidos separados. Falta de medição de um contributo produz total desconhecido, não uma soma incompleta apresentada como caudal total. Mesmo com amostras simultâneas, faltam tempos de viagem, armazenamento no troço e afluências não medidas para usar essa soma como fronteira calibrada.

O cálculo de inundação exige ainda terreno e batimetria atuais no mesmo referencial vertical, representação de comportas e remanso, geometria e operação de diques e estruturas de descarga, propagação temporal e verificação de balanço. As peças DWF localizadas são informação histórica e de projeto; algumas conversões apresentaram truncagem ou omissões, pelo que não foram promovidas a geometria hidráulica completa. O perfil de dragagem de 2010 serve para análise de sensibilidade e planeamento de dados, não para afirmar onde a água está hoje.

Após uma mancha datada e validada, a interseção com CAOP e BGRI permite estimar residentes e grupos etários expostos. Ponderação uniforme por área de subsecção continua a ser estimativa; crianças e idosos não esgotam a vulnerabilidade, e população censitária não equivale a população presente em tempo real.

## 7. Protocolo de avaliação operacional
Propõe-se avaliação em paralelo, sem emissão de alertas, com registo de cada execução, estado dos dados e comparação com ocorrências observadas. A aceitação deverá exigir: transformação vertical documentada; geometria atual com data e controlo de qualidade; pares instantâneos Q/H e operação das estruturas; calibração por vários eventos com um conjunto independente reservado; métricas de nível, tempo de chegada, caudal e extensão espacial; quantificação de falsos positivos e omissões nas freguesias; revisão técnica responsável. Não se definiram limites de aprovação como se fossem normas oficiais.

O mapa público é uma versão para avaliação operacional. Na vista atual, dados em falta ou uma calibração parcial não produzem cores de inundação. O ajuste de descarga e os cenários de projeto estão identificados como experimentais. A expansão às bacias nacionais reutiliza contratos e verificações; não transfere coeficientes de Coimbra para outros rios.

## 8. Reprodutibilidade e conclusão
O código tools/coimbra-analysis.R executa com R de base, sem pacotes adicionais. O CSV diário, métricas, pares, perfil de projeto e sessionInfo são publicados com quatro figuras. A obtenção do histórico está em tools/coimbra-archive.cjs e a integração das fronteiras em tools/coimbra-boundaries.py. O conjunto permite auditar o avanço realizado: foi recuperado arquivo adicional e ajustada uma componente agregada de descarga. Não foi concluída a calibração hidráulica espacial nem autorizada a sinalização operacional de freguesias atingidas.

