# Coletor do Floods no NAS
Node.js com módulos ES e fetch. O ponto de entrada é collector.mjs. O coletor requer o diretório /seed com basins.geojson, simulation.json, rainfall-estimates.json e snirh-observations.geojson e um diretório persistente /state gravável. A recolha de IPMA e APA/SNIRH e a chuva estimada ECMWF correm em ciclos de 15 minutos. Os estados de observação, estimativa e indisponibilidade seguem o contrato simulation/2.

A janela de arquivo experimental da depressão Charles é 10–14 de novembro de 2026 UTC. Cada ciclo arquivado contém os acumulados IPMA e as séries horárias disponíveis, telemetria SNIRH da mesma recolha quando disponível, simulação e estado da recolha. A data do ficheiro é a hora UTC de conclusão. Cada cálculo continua experimental. O arquivo não emite alertas.

Teste offline: node nas/archive-charles.test.mjs.

Para um ciclo isolado, executar node nas/collector.mjs --once com FLOODS_SEED_DIR e FLOODS_STATE_DIR apontados para pastas separadas da produção. O parser APA/SNIRH é partilhado em shared/snirh.cjs. A seed também deve incluir stations.geojson para fallback IPMA.
