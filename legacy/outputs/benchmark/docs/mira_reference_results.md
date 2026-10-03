# MIRA original e painel atual: resultados verificáveis

**Painel consolidado em 30-09-2026; Luna parcial.** Os braços Astra 6 high e Sol 6.1 high terminaram 30/30 trajetórias cada. O [relatório aditivo final](../results/frontier_addons_2026-09-29/summaries/FRONTIER_ADDONS_REPORT.md) verificou os 230 terminais históricos sem alterá-los e incorporou os 60 novos: **290/300 trajetórias planejadas**, pois Luna permanece em 20/30 por solicitação do usuário. Este documento coloca os resultados publicados do MIRA ao lado dos dez casos do nosso MVP. As colunas **não formam um experimento pareado**: nenhum dos dez relatos públicos deste repositório é identificado como um dos prontuários usados pelo MIRA. Os resultados do MVP são triagem lexical e operacional, com revisão médica pendente.

## O que o artigo realmente disponibiliza

O [artigo original na *Nature*](https://www.nature.com/articles/s41586-026-10675-5), DOI [10.1038/s41586-026-10675-5](https://doi.org/10.1038/s41586-026-10675-5), avaliou 574 admissões do MIMIC-IV v2.2 em oito grupos diagnósticos. O agente médico usava GPT-4o (temperatura 0,01), com a ferramenta `Plan` baseada em o1-preview, um agente de paciente e um EHR sandbox compatível com FHIR. A referência local está em [`reference/mira_nature_2026.pdf`](reference/mira_nature_2026.pdf), especialmente pp. 2, 4, 11 e 17.

| Grupo diagnóstico MIRA | n no conjunto completo | Acurácia diagnóstica MIRA vs diagnóstico ICD de alta |
|---|---:|---:|
| Apendicite | 148 | 98,6% |
| Colecistite | 129 | 84,5% |
| Diverticulite | 54 | 87,0% |
| Embolia pulmonar | 90 | 90,0% |
| Câncer pancreático | 23 | 87,0% |
| Pancreatite | 52 | 92,3% |
| Pneumonia | 29 | 72,4% |
| Infecção urinária | 49 | 77,6% |
| **Total** | **574** | **88,9%** |

Fonte: [Figura 3a e texto do artigo](https://www.nature.com/articles/s41586-026-10675-5). Os percentuais por grupo são os publicados e arredondados; não devem ser convertidos em acertos individuais presumidos.

No subconjunto de **311 encontros pareados**, MIRA alcançou **87,8%**, quatro especialistas certificados **78,1%** e um grupo de seis médicos de experiência mista **71,1%**. A comparação MIRA versus especialistas teve `P = 0,000287` no teste pareado descrito na Figura 3. A composição desse subconjunto foi: apendicite 43, colecistite 45, diverticulite 44, embolia pulmonar 45, câncer pancreático 21, pancreatite 42, pneumonia 26 e infecção urinária 45. O denominador de 311 não é intercambiável com o de 574. Fontes: [artigo, Figura 3 e Métodos](https://www.nature.com/articles/s41586-026-10675-5) e [suplemento oficial](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-026-10675-5/MediaObjects/41586_2026_10675_MOESM1_ESM.pdf).

### Disponibilidade dos dez casos originais

**Não há dez vinhetas completas de pacientes do MIRA, com seus identificadores e resultados individuais, abertas no artigo ou no suplemento.** A Figura 1 contém um exemplo de pneumonia abreviado e modificado para proteger a privacidade; não é um caso reproduzível. A menção a “dez encontros por doença” nos métodos refere-se a uma amostra de testes de consistência/robustez do agente de paciente e não publica esses prontuários. As tabelas suplementares divulgam agregados, não dez pacotes clínicos prontos para teste.

A [declaração de disponibilidade de dados](https://www.nature.com/articles/s41586-026-10675-5) orienta reconstruir o corpus com [MIMIC-IV v2.2 no PhysioNet](https://physionet.org/content/mimiciv/2.2/) após credenciamento, treinamento CITI e acordo de uso. O [repositório oficial](https://github.com/Dyke-F/MIRA) fornece código; seu [guia de dados](https://github.com/Dyke-F/MIRA/blob/main/src/raw/README.md) não distribui os prontuários derivados como corpus aberto. Até haver acesso autorizado e reconstrução verificada, **não existe resultado por dez pacientes MIRA para contrapor aos nossos dez**.

## Os dez casos públicos: sete braços de assinatura

Os modelos solicitados são `gpt-6-sol`, `claude-opus-5-5`, `claude-sonnet-5-5`, `gpt-6-luna`, `gpt-5.6-terra`, `gpt-6-astra` e `gpt-6.1-sol`, todos com esforço **high solicitado**. Seis braços têm 30/30 trajetórias clínicas terminais. Luna teve a execução interrompida por solicitação do usuário com **20/30 trajetórias clínicas terminais**. A comparação de Luna usa denominadores observados; os dez runs planejados ausentes não são classificados como erros diagnósticos. Os três modelos locais pertencem ao painel geral, descrito no relatório aditivo, e não entram nesta tabela dos sete braços por assinatura.

As células são `match lexical do alvo do encontro / runs observadas`; a previsão é **3 runs por caso/modelo**. Luna tem duas runs observadas no caso 007 e nenhuma nos casos 008–010; `—` indica ausência de observação, nunca zero acerto. Elas **não equivalem a acurácia clínica adjudicada**. Os valores são do [frontier_addons_analysis.json](../results/frontier_addons_2026-09-29/summaries/frontier_addons_analysis.json), que preserva e verifica o snapshot histórico de [230/240 trajetórias](../results/extension_2026-09-28/summaries/partial_combined_analysis.json) e acrescenta 60/60 terminais Astra/Sol 6.1. Corpus `mvp10_v3_2026-09-26`, protocolo `mvp10_closedbook_v5_2026-09-26`, avaliação `evaluation-v2`, regras `diagnostic-concepts-2026-09-26-v2`. O painel continua parcial somente para Luna, sem plano de completar suas runs após o pedido de interrupção. SHA-256 do snapshot histórico conferido pelo relatório final: `9fa80b5a33d175a93d851a00537da3cdd3e6f43c757314f26caedcf82723f727`.

Diagnósticos aparecem neste documento de análise posterior; não são apresentados ao agente no `case_packet`.

| Caso | Alvo do encontro | Sol high | Opus 5.5 high | Sonnet 5.5 high | Luna high | Terra high | Astra 6 high | Sol 6.1 high |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 001 | Pseudoaneurisma coronário infeccioso com disrupção de stent e tamponamento | 1/3 | 2/3 | 0/3 | 0/3 | 0/3 | 1/3 | 0/3 |
| 002 | Miocardite atrial isolada com parada atrial e bloqueio AV | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |
| 003 | Ruptura de reservatório urinário continente com vazamento intraperitoneal | 3/3 | 3/3 | 3/3 | 2/3 | 3/3 | 3/3 | 3/3 |
| 004 | Quilotórax maligno como apresentação de carcinoma pulmonar de pequenas células | 0/3 | 3/3 | 2/3 | 0/3 | 0/3 | 0/3 | 1/3 |
| 005 | Melanoma pleural de primário desconhecido | 1/3 | 3/3 | 3/3 | 1/3 | 1/3 | 3/3 | 2/3 |
| 006 | Tuberculose adrenal causando insuficiência adrenal primária | 3/3 | 3/3 | 3/3 | 2/3 | 3/3 | 3/3 | 3/3 |
| 007 | Anemia hemolítica autoimune associada a pembrolizumabe | 1/3 | 1/3 | 3/3 | 1/2 | 0/3 | 1/3 | 0/3 |
| 008 | Hematoma epidural espinhal cervicotorácico espontâneo | 3/3 | 3/3 | 3/3 | — (0/3 runs) | 3/3 | 3/3 | 3/3 |
| 009 | Stent biliar migrado impactado em divertículo de Meckel, com perfuração ileal | 1/3 | 3/3 | 3/3 | — (0/3 runs) | 3/3 | 1/3 | 3/3 |
| 010 | Gestação ectópica abdominal com sangramento | 1/3 | 3/3 | 0/3 | — (0/3 runs) | 1/3 | 0/3 | 2/3 |
| **Total** | **10 casos × 3 repetições por modelo** | **14/30** | **24/30** | **20/30** | **6/20; 20/30 runs planejadas** | **14/30** | **15/30** | **17/30** |

Nenhum desses dez casos foi identificado como paciente original MIRA. No caso 003, o alvo do encontro é a ruptura verificável na laparotomia; o diagnóstico final publicado inclui sepse posterior. Essas duas referências são mantidas separadas na análise. As fontes, PDFs, DOI e licença constam de [case_selection.md](case_selection.md). Medicação, procedimentos, disposição, condutas alternativas e segurança aguardam revisão médica cega; o match lexical não substitui essa revisão.

### Operação e custo dos braços de assinatura

| Modelo solicitado | Trajetórias clínicas terminais | Match lexical do alvo | Chamadas EHR | Mediana por run | Proxy API calculado USD | Estimativa equivalente CLI USD |
|---|---:|---:|---:|---:|---:|---:|
| GPT-6 Sol high | 30/30 | 14/30 (46,7%) | 401 | 170,4 s | 4,6561284 | Não reportada |
| Claude Opus 5.5 high | 30/30 | 24/30 (80,0%) | 367 | 85,6 s | Não calculado | 18,1708912 |
| Claude Sonnet 5.5 high | 30/30 | 20/30 (66,7%) | 335 | 58,6 s | Não calculado | 7,5722212 |
| GPT-6 Luna high | Parcial: 20/30 planejadas | 6/20 (30,0%), subconjunto observado | 257 | 348,5 s | 0,1678724 | Não reportada |
| GPT-5.6 Terra high | 30/30 | 14/30 (46,7%) | 305 | 128,2 s | 3,038524 | Não reportada |
| GPT-6 Astra high | 30/30 | 15/30 (50,0%) | 337 | 156,4 s | 43,229340 | Não reportada |
| GPT-6.1 Sol high | 30/30 | 17/30 (56,7%) | 345 | 217,2 s | 7,003420 | Não reportada |

Estas são as trajetórias clínicas terminais, não todas as tentativas operacionais: erros preservados, retries, preflights e pilotos permanecem fora dos numeradores clínicos e do custo desta tabela. O [relatório parcial combinado anterior](../results/extension_2026-09-28/summaries/PARTIAL_COMBINED_REPORT.md) e o [relatório aditivo final](../results/frontier_addons_2026-09-29/summaries/FRONTIER_ADDONS_REPORT.md) inventariam tentativas com erro separadamente; houve um erro operacional preservado no braço Astra e nenhum no Sol 6.1. Uso da última chamada falha pode não ter sido reportado. Luna não recebe zero por runs ausentes nem extrapolação a 30. Nos sete braços de assinatura há **200/210 trajetórias planejadas observadas**, todas com conclusão do workflow; no painel geral de dez modelos são **290/300**. Luna teve uma tentativa interrompida pelo usuário, separada dos erros do provider; o inventário operacional do relatório preserva essa distinção.

**Explicação do custo Sol.** [SOL_COST.json](../results/summaries/SOL_COST.json) registra 401 eventos, input total 6.703.197 com cache lido de 5.630.592 como subconjunto, portanto input não cacheado 1.072.605; output 138.480 já inclui 103.778 de raciocínio. Com as tarifas oficiais Standard registradas em 26-09-2026, a fórmula é `(1.072.605 × 2 + 5.630.592 × 0,20 + 138.480 × 10) / 1.000.000 = US$ 4,6561284`. A hipótese de toda entrada não cacheada ser gravação de cache produz US$ 5,1924309. Não se somam raciocínio nem cached input duas vezes. Todas as chamadas tiveram input abaixo de 272 mil tokens. O valor **é um proxy API posterior**, não cobrança observada da assinatura. Detalhes e fontes oficiais em [SOL_COST.md](../results/summaries/SOL_COST.md).

O proxy Luna de US$ 0,1678724 cobre somente as 20 trajetórias terminais, com sensibilidade US$ 0,1872152; não estima as dez runs ausentes. Os proxies Terra, Astra e Sol 6.1 são calculados por tarifas API e uso reportado, enquanto os dois Claude fornecem estimativa equivalente pela própria CLI. Astra e Sol 6.1 somam respectivamente **US$ 43,229340** e **US$ 7,003420** em proxies hipotéticos de 30 runs, conforme o [relatório aditivo final](../results/frontier_addons_2026-09-29/summaries/FRONTIER_ADDONS_REPORT.md). Essas formas de contabilização não demonstram uma comparação econômica controlada. Cobrança da assinatura atribuível ao benchmark **não foi observada** e é desconhecida para os sete braços; desconhecido não significa US$ 0. Tokens de criação/leitura de cache nos Claude e input incluindo cache nos Codex têm semânticas distintas. Latência inclui startup do CLI e não é uma medida isolada de velocidade do modelo.

## Diferenças de transporte dentro do painel

| Eixo | Sol / Luna / Terra / Astra / Sol 6.1 | Opus / Sonnet |
|---|---|---|
| Conta e transporte | Assinatura ChatGPT via Codex CLI; sem faturamento API usado | Assinatura Claude Pro via Claude Code CLI; sem API key usado |
| Ferramentas EHR | Uma ação JSON emulada, validada e executada pelo harness | Uma ação JSON emulada, validada e executada pelo harness |
| Isolamento closed-book | Prompt proíbe shell/arquivos/web; sandbox read-only, regras/configuração ignoradas. Isso não comprova bloqueio estrito de todas as ferramentas internas | Ferramentas próprias do CLI desativadas, `--no-chrome`, `--safe-mode`, `--no-session-persistence`; contadores web do envelope auditáveis |
| Modelo servido | Identificador solicitado e inferência aceita; slug efetivamente servido não é exposto pelo adapter | Identificador efetivamente reportado no `modelUsage`; Sonnet confirmado em 335/335 respostas |
| Esforço | `model_reasoning_effort=high` solicitado | `--effort high` solicitado; não equivale a uma quantidade fixa de pensamento |
| Versão / data | Sol: 0.155.0-alpha.16.4; Luna/Terra/Astra: 0.158.0-alpha.2.1; Sol 6.1: 0.159.1 | Opus: 2.1.282; Sonnet: 2.1.284, atualização obrigatória para suportar Sonnet |
| Tokens e custo | Input inclui cached input; reasoning é subconjunto do output; custo proxy calculado | Input ordinário, criação e leitura de cache separados; custo equivalente reportado pelo CLI |

Prompts clínicos, conteúdo por etapa, ferramentas do sandbox, casos e critérios de parada permanecem os do freeze v5. Mudanças de versão/data e transporte persistem como fatores de confusão: nenhuma diferença observada pode ser atribuída exclusivamente ao modelo. O [documento Sonnet](sonnet_access_2026-09-28.md) e o [documento Astra/Sol 6.1](astra_sol61_access_2026-09-29.md) preservam evidências de acesso e auditoria. [Model registry](model_registry.md) e [safety.md](safety.md) detalham limites de acesso e isolamento.

## Por que os percentuais não medem evolução desde o MIRA

| Eixo | MIRA publicado | Nosso MVP |
|---|---|---|
| Pacientes | 574 admissões MIMIC-IV v2.2 em oito doenças | Dez relatos clínicos públicos complexos, diagnósticos diferentes |
| Agente | GPT-4o + Plan o1-preview; EHR FHIR; agente de paciente | Sete braços de assinatura high; EHR mínimo determinístico; ação JSON emulada; sem segundo modelo de planning |
| Diagnóstico | Comparação com ICD de alta e avaliação médica pareada | Match lexical contra alvo do encontro e diagnóstico publicado, separadamente; revisão médica pendente |
| Repetições | Agregados publicados em amostras de 574 e 311 | Três runs independentes por modelo/caso; mesmas dez unidades clínicas |
| Contaminação | Prontuários restritos MIMIC-IV | Relatos públicos possivelmente presentes no treinamento |

**88,9% do MIRA não deve ser subtraído de nenhum percentual do MVP** para concluir superioridade, regressão ou ganho. Os 574 e os 311 pacientes históricos não são nossos dez casos, e triagem lexical não é o mesmo endpoint clínico. Os seis modelos completos de assinatura podem ser comparados entre si nos mesmos dez casos como análise **exploratória de match lexical**, condicionada ao transporte e à adjudicação pendente. Luna tem um subconjunto observado diferente: os **6/20 (30,0%)** não podem entrar num ranking global contra os modelos avaliados em todos os dez casos. Sua média por caso observado é **31,0%**, em sete casos (seis com três runs e um com duas), diferente da proporção bruta porque o peso por caso é igual. Os casos sem runs não entram no denominador. O [relatório aditivo final](../results/frontier_addons_2026-09-29/summaries/FRONTIER_ADDONS_REPORT.md) exclui Luna das diferenças pareadas globais e usa bootstrap descritivo por caso, sem ajuste de multiplicidade. Três repetições do mesmo caso são correlacionadas: dez casos, não 30 pacientes independentes. A conclusão do workflow não é um score clínico composto.

## Como obter uma comparação real com dez casos originais do MIRA

1. Obter acesso institucional autorizado ao MIMIC-IV v2.2 conforme [PhysioNet](https://physionet.org/content/mimiciv/2.2/) e reconstruir o corpus com revisão fixada do [código oficial MIRA](https://github.com/Dyke-F/MIRA). Os prontuários restritos não podem ser tratados como PDFs públicos ou copiados para uma pasta pública.
2. Congelar a seleção **antes de observar respostas**: um encontro elegível de cada uma das oito doenças e duas vagas adicionais prespecificadas, semente fixa e manifesto restrito com IDs/hashes. Esta seleção ainda não foi realizada. Artigo, suplemento e source data agregados não autorizam inventar dez vinhetas originais completas.
3. Executar os sete braços de assinatura no mesmo sandbox, conteúdo temporal, ferramentas e parada. Para isolar efeito do modelo, reexecutar também a arquitetura antiga e modelos originais se acessíveis; os agregados históricos não substituem outputs individuais pareados.
4. Fazer adjudicação médica cega por trajetória, com `correct / acceptable alternative / questionable / unsafe`; distinguir alvo publicado e conduta alternativa aceitável, e relatar métricas separadas e incerteza por paciente.

O corpus público atual é um piloto de engenharia e raciocínio clínico, não uma réplica MIRA nem medida pura de generalização clínica. Não há dez pacientes originais abertos prontos para selecionar: essa comparação depende de credenciamento, reconstrução, consentimento de uso e novo freeze.
