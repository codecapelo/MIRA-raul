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

## Por que o 001 continuou errado
O revisor às cegas, instruído a pedir achados operatórios, pediu pericardiocentese e exploração cirúrgica (que mostram a vegetação do marca-passo), recebeu a vegetação e fechou "endocardite por MRSA com pericardite purulenta", sem pedir a angiografia coronariana que mostra o pseudoaneurisma. Na v2 (sem essa instrução) o Sonnet pedia angiografia ou CT coronariana e acertava em 3 de 3. Além disso, o GLM-5 pediu a angiografia pela ferramenta errada (`request_other_investigation`) e recebeu "não disponível". Correções já no código (**ainda sem rodar**): a instrução do revisor agora também pede a imagem ou angiografia da lesão nomeada; e a ferramenta responde `wrong_tool` com o nome da ferramenta certa quando um exame existe em outra.

## Leitura
Em custo, o v3.2b ficou 43% abaixo do v3.2a, mas acima do v2 (US$ 0,089 contra 0,061 por encontro); em acerto, 9/10 contra 29/30, sem diferença que 10 casos sustentem. Os custos extras vêm de mais pedidos de exame do GLM-5 (6 a 11 por encontro contra 3 a 5, por causa do mapa e do lembrete), de revisar mais casos (6 de 10 contra cerca de 6 de 10 na v2, com mapa no prompt) e do mapa (US$ 0,015). Ainda não há evidência de que o mapa melhore a acurácia da primeira camada (propostas 8/10 contra 22/30 na v2).

## Gasto
Ledger e conta: US$ 15,454 → 15,646 nesta execução (reconciliação das 3 chamadas da rodada interrompida: US$ 0,002242, `v32_killed_reconciliation.json`). Restam cerca de US$ 2,35 do teto de US$ 18.
