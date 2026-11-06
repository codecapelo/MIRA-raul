# Protocolo v3.2: mapa da consulta, pré-requisitos de procedimento, Sonnet no lugar do Opus (05-10-2026)

Resumo das duas execuções do v3.2 (10 casos × 1 por configuração, GLM-5 conduz com N=2, exame junto, resultados imediatos; juiz Gemini 3.1 Pro com o critério v3 do caso 009; Claude pela assinatura Pro). **Julgamento por LLM, sem revisão médica; uma execução por caso.** Comparar sempre com o escalonamento v2 reavaliado com o mesmo critério do caso 009.

| Configuração | Corretos | Propostas do GLM-5 | Custo de implantação por encontro (equiv. API) | Por caso resolvido | Só OpenRouter por caso resolvido |
|---|---:|---:|---:|---:|---:|
| Escalonamento v2 (sem mapa; JEF 0,90; Sonnet às cegas; Opus arbitra), 3 execuções, critério v3 do 009 | 29/30 | 22/30 | US$ 0,061 | US$ 0,063 | US$ 0,011 |
| v3.2a (mapa do Opus longo, Sonnet em todos, Opus arbitra) | 9/10 (1 falha de ferramenta) | 8/9 | US$ 0,156 | US$ 0,173 | US$ 0,016 |
| **v3.2b** (mapa do Sonnet enxuto, JEF 0,86 + auditoria 20% + gatilho, Sonnet arbitra, resgate de falhas) | **9/10** | 8/10 | **US$ 0,089** | **US$ 0,099** | **US$ 0,014** |

## O que as correções fizeram
- **Trocar o Opus pelo Sonnet no mapa e enxugar o mapa:** o mapa caiu de US$ 0,059 para US$ 0,015 por caso. O mapa longo do Opus listava até 14 exames por item e atrapalhava (lembretes frequentes, mais pedidos de exame).
- **Triagem do JEF com corte 0,86** (escolhido nos 103 encontros com transcrição, com o 009 reclassificado: aceita 66% com 1 erro entre os 68 aceitos; ajuste feito nos mesmos dados): aceitou 4 de 10 (003, 004, 005, 009), todos certos. A auditoria de 20% não sorteou nenhum aceite.
- **Sonnet às cegas** revisou 6 casos (13 chamadas, US$ 0,618 em equivalente de API, cerca de US$ 0,048 por chamada); o Sonnet arbitrou 1 (caso 002, escolheu o revisor) e corrigiu a proposta errada do 002. O caso 001 continuou errado.
- **Resgate de falhas:** implementado (o revisor assume se o GLM-5 não concluir); não foi preciso nesta execução (nenhuma falha de ferramenta).
- **Pré-requisitos de procedimento:** bloquearam pedidos em 2 casos (003 e 004), com o médico informado do procedimento a pedir antes. **Emergência sem N mínimo:** 5 casos marcados como emergência.

## Rodada com as correções (execução 2 da mesma configuração, commit `13e9179`)
**10/10 corretos; propostas do GLM-5 9/10** (só o 002 precisou de correção, feita pelo Sonnet às cegas e pelo árbitro). Custo de implantação **US$ 0,070 por encontro e por caso resolvido** (OpenRouter US$ 0,0126 por caso resolvido; Claude em equivalente de API US$ 0,057 por encontro). A triagem do JEF aceitou 6 de 10 (a auditoria de 20% não sorteou nenhum aceite, o que acontece com probabilidade de 11% em 10 encontros), o Sonnet revisou 3 e o árbitro 1. **O caso 001 passou a acertar na primeira camada:** o GLM-5 pediu a angiografia pela ferramenta errada, a resposta `wrong_tool` indicou `request_radiology`, e antes disso o pedido de tomografia exigiu a pericardiocentese, que ele fez (pré-requisito de procedimento); com a angiografia mostrando o pseudoaneurisma, a proposta saiu correta e o JEF aceitou (escore 0,90). Os 5 casos emergenciais e os lembretes de exame decisivo (6 de 10) seguiram ativos. Uma execução por caso; o resultado do 001 pode variar com a amostragem do GLM-5.

| Configuração | Corretos | Propostas | Por encontro (equiv. API) | Por caso resolvido | Só OpenRouter por caso resolvido |
|---|---:|---:|---:|---:|---:|
| v2, 3 execuções | 29/30 | 22/30 | US$ 0,061 | US$ 0,063 | US$ 0,011 |
| v3.2a | 9/10 | 8/9 | US$ 0,156 | US$ 0,173 | US$ 0,016 |
| v3.2b | 9/10 | 8/10 | US$ 0,089 | US$ 0,099 | US$ 0,014 |
| **v3.2c (com as correções)** | **10/10** | **9/10** | **US$ 0,070** | **US$ 0,070** | **US$ 0,013** |

## Por que o 001 continuou errado (antes das correções)
O revisor às cegas, instruído a pedir achados operatórios, pediu pericardiocentese e exploração cirúrgica (que mostram a vegetação do marca-passo), recebeu a vegetação e fechou "endocardite por MRSA com pericardite purulenta", sem pedir a angiografia coronariana que mostra o pseudoaneurisma. Na v2 (sem essa instrução) o Sonnet pedia angiografia ou CT coronariana e acertava em 3 de 3. Além disso, o GLM-5 pediu a angiografia pela ferramenta errada (`request_other_investigation`) e recebeu "não disponível". Correções já no código (**ainda sem rodar**): a instrução do revisor agora também pede a imagem ou angiografia da lesão nomeada; e a ferramenta responde `wrong_tool` com o nome da ferramenta certa quando um exame existe em outra.

## Leitura
Em custo, o v3.2b ficou 43% abaixo do v3.2a, mas acima do v2 (US$ 0,089 contra 0,061 por encontro); em acerto, 9/10 contra 29/30, sem diferença que 10 casos sustentem. Os custos extras vêm de mais pedidos de exame do GLM-5 (6 a 11 por encontro contra 3 a 5, por causa do mapa e do lembrete), do mapa dentro de cada prompt de revisão (prompts maiores; a fração revisada é parecida: 6 de 10 contra 17 de 30 na v2) e do próprio mapa (US$ 0,015). Ainda não há evidência de que o mapa melhore a acurácia da primeira camada (propostas 8/10 contra 22/30 na v2).

## Gasto
Ledger e conta: US$ 15,454 → 15,646 na execução 1 e → 15,830 na execução 2 (corrigida). Na execução 2, os três primeiros snapshots ficaram US$ 0,0148 abaixo do ledger (atraso transitório da conta) e os três seguintes, após uma pausa, bateram exatamente (`credits_v32c_final_b*.json`). A primeira (reconciliação das 3 chamadas da rodada interrompida: US$ 0,002242, `v32_killed_reconciliation.json`). Restam cerca de US$ 2,35 do teto de US$ 18.
