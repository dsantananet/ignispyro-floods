# População presente, mobilidade e sazonalidade

Data de verificação: 24/10/2026. Estado: estudo de viabilidade; nenhum acesso Meta/operador foi obtido nem dados pessoais recolhidos.

## Resposta ao requisito

A integração é tecnicamente possível com dados agregados adequados, mas não existe aqui uma API pública de Facebook/Instagram que conte todas as pessoas presentes numa freguesia em tempo real. Meta é a empresa responsável pelo Facebook; mudar o nome para Meta não remove as condições de acesso.

O produto mais próximo para movimentos é **Facebook Movement During Crisis**, que fornece movimentos agregados de utilizadores com serviços de localização ativos, comparados com uma situação de referência, em intervalos de oito horas. A Meta indica acesso para investigadores e organizações sem fins lucrativos mediante acordo de partilha. Cobertura e ativação para Portugal, resolução, histórico, latência, possibilidade de utilização neste portal e redistribuição pública ainda não estão confirmados. Para manchas de presença deve ser pedida também disponibilidade de **Population During Crisis**, em vez de tentar transformar diretamente fluxos em ocupação.

Fonte primária: https://ai.meta.com/ai-for-good/datasets/facebook-movement-during-crisis/
Contexto oficial dos mapas de densidade e movimento: https://about.fb.com/news/2017/06/using-data-to-help-communities-recover-and-rebuild/

## Separação de grandezas

| Grandeza | Unidade | Interpretação |
|---|---|---|
| Residentes BGRI/Censos | pessoas na data censitária | Base estrutural; não mede presença atual |
| Utilizadores/dispositivos presentes | utilizadores ou dispositivos por célula e intervalo | Amostra da fonte; não equivale a população total |
| Fluxo origem-destino | deslocações/utilizadores num intervalo | Não é o stock de pessoas no destino |
| Índice relativo | rácio ou anomalia contra referência | Mudança da amostra; requer calibração para estimar pessoas |
| População presente estimada | pessoas, com intervalo de incerteza | Necessita modelo validado e correção de representatividade |
| Vulneráveis presentes estimados | pessoas por grupo | Não se obtém aplicando automaticamente a estrutura etária residente aos visitantes |

Não somar residentes + hóspedes mensais: hóspedes são chegadas ao longo do mês, não pessoas simultaneamente presentes. Dormidas/dias do mês aproximam a presença noturna média do segmento coberto, mas não medem excursionistas, alojamento informal ou o pico diário.

## Alternativas a avaliar

1. **Operadores móveis em Portugal**: dados agregados de presença, origem-destino, roaming e sazonalidade, através de acordo comercial ou científico. Verificar NOS/Smart Cities, MEO e Vodafone Business. Não há credencial nem contrato nesta entrega. Pedir demonstração para uma bacia e aferir precisão por freguesia, dispositivos por pessoa, múltiplos cartões e exclusão de pessoas sem telemóvel.
2. **INE / Turismo de Portugal / TravelBI**: hóspedes, dormidas, capacidade e ocupação por município/mês. Úteis como covariáveis sazonais; não dão mancha horária por freguesia. Referência: https://travelbi.turismodeportugal.pt/en/accommodation/short-term-accommodation-2025/ .
3. **Contadores locais e eventos**: bilhética agregada, contagens pedonais, parques de estacionamento e ocupação de equipamentos. Exigem calibração e cobertura conhecida.
4. **WorldPop/GHSL/HRSL**: distribuições modeladas da população, úteis para desagregação e cenários estruturais; não são movimentos observados em tempo real. API primária WorldPop: https://api.worldpop.org/v2/ .

## Modelo a testar

Para cada célula i e instante/intervalo t, estimar N(i,t) com uma base residente e fatores de presença separados por tipo de território, hora, dia da semana, mês e evento. Um rácio da amostra Meta face à referência só poderá multiplicar uma referência de presença calibrada, não automaticamente os Censos. Usar validação contra contadores e ocupação independente, ponderação por cobertura, intervalos por bootstrap temporal/espacial e teste específico de crises com falhas de rede.

Exposição dinâmica: E(t) = soma_i N(i,t) × fração da célula na mancha inundável. Propagar incerteza da população, posicionamento e mancha. Uma célula grande cruzada por uma ribeira pequena exige desagregação com edifícios e análise de sensibilidade, não precisão fictícia de rua.

Vulnerabilidade deve ser avaliada por grupo e fonte: idade, mobilidade, dependência e equipamentos. Dados agregados de mobilidade não identificam automaticamente crianças, idosos ou pessoas com limitações. Não inferir indivíduos nem trajetórias pessoais.

## Implementação nesta versão

O portal inclui informação de viabilidade e um contrato de dados para futuras camadas agregadas. A camada dinâmica permanece sem dados enquanto não houver fonte com acesso e utilização adequados. Não são guardados dados Meta restritos no repositório público nem expostos tokens no navegador. A futura recolha ficará num serviço privado no NAS; só produtos agregados cuja divulgação seja permitida poderão chegar ao mapa público.

Próximo passo externo: pedido institucional de acesso à Meta através de entidade de investigação, ou proposta de piloto a um operador. Esta sessão não enviou mensagens nem pedidos a terceiros.
