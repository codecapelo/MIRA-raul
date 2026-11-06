# Auditoria do histórico legado e continuidade — 08-10-2026

O projeto já experimentou entrevista sequencial, paciente determinístico, controle temporal, aliases de exames, parada de loops, revisão às cegas, cascatas, critérios de julgamento diferentes e política de custo dos exames. A base de outubro também chegou a 20/20 resultados corretos segundo o juiz LLM em uma rodada. Isso deve orientar melhorias incrementais; nenhuma dessas ideias deve ser apresentada como descoberta nova.

Esta auditoria preservou `legacy/`, não fez chamadas de inferência, não leu credenciais e não executou encontros. O JSON acompanhante contém inventário com hashes de todos os arquivos, resumos de todos os traces, recomputação do painel e denominadores separados. Os números abaixo são evidência local histórica, sem consulta à conta ou confirmação de saldo vivo.

## Cobertura e limites da leitura

- **978/978 arquivos legados** lidos em bytes e conferidos com `reports/migration_manifest.json`: zero divergências, ausências ou arquivos extras.
- **366 arquivos JSONL, 23.221 registros**, todos parseados; 72 JSON, 18 CSV e 43 Python (AST) sem erros de parsing.
- **339 traces de tentativa clínica** identificados por `run_started`; todos classificados estruturalmente. Os 290 traces do painel final foram integralmente carregados e pontuados com o avaliador congelado, sem alterar os dados.
- Inspeção substantiva dos protocolos, documentação de versões e corpus, prompts, EHR, runner, avaliador, adapters de assinatura e relatórios de interpretação. O JSON distingue essa inspeção da leitura computacional do inventário.
- **Não** houve releitura visual integral dos 10 PDFs clínicos nem leitura humana linha a linha de todas as 339 conversas. Hash e parsing provam integridade/estrutura; não demonstram fidelidade clínica dos relatos nem correção de cada conduta.
- Os relatórios v3 do worktree mais recente foram inspecionados como complemento. Não foram lidos nem copiados seus traces privados, resultados individuais ou packets fechados.

## Denominadores recuperados diretamente dos traces

| Série | Tentativas com início | `run_ended` | Uso nesta análise |
|---|---:|---:|---|
| Painel base v5, `results/raw` | 150 | 150 | Painel principal |
| Sonnet/Luna, extensão 28-09 | 50 | 50 | Painel principal: 30 Sonnet + 20 Luna |
| Terra | 30 | 30 | Painel principal |
| Astra | 30 | 30 | Painel principal |
| Sol 6.1 | 30 | 30 | Painel principal |
| `exploratory_v1` | 5 | 4 | Pilotos fora do painel |
| `exploratory_v2_aborted` | 7 | 4 | Pilotos fora do painel |
| `exploratory_v2_preprotocol` | 1 | 0 | Piloto fora do painel |
| `exploratory_v3_aborted` | 12 | 10 | Pilotos fora do painel |
| `exploratory_v4_aborted` | 5 | 2 | Pilotos fora do painel |
| `pilot` | 6 | 6 | Pilotos fora do painel |
| `incomplete` base | 4 | 1 | Prefixos/tentativa operacional fora do painel |
| `incomplete` Sonnet/Luna | 3 | 2 | Duas falhas e uma interrupção pelo usuário |
| `incomplete` Terra | 5 | 5 | Falhas operacionais fora do painel |
| `incomplete` Astra | 1 | 1 | Falha operacional fora do painel |

Total: **290 terminais no painel**, **36 tentativas de piloto/exploração** e **13 prefixos/tentativas incompletas**. Não somar os 49 registros excluídos ao denominador clínico final. Há 290 combinações únicas modelo–caso–repetição, zero duplicatas. Das 300 combinações planejadas, faltam exclusivamente 10 Luna por interrupção solicitada. Os 290 incluem falhas de conclusão do próprio modelo; terminal não significa atendimento concluído com diagnóstico e disposição.

Fontes: classificação de todos os JSONL no JSON acompanhante; `legacy/outputs/benchmark/README.md:1-3`, `docs/subscription_usage_2026-09-28.md:29-34`, `results/frontier_addons_2026-09-29/summaries/FRONTIER_ADDONS_REPORT.md:1-3`.

## Resultados recompostos do legado

`Conclusão` exige diagnóstico aceito e disposição aceita. `Match` é a regra lexical congelada do alvo agudo, não avaliação clínica. Casos publicados e repetições correlacionadas impedem interpretar estes percentuais como generalização populacional.

| Modelo | Terminais observados | Conclusão do fluxo | Match lexical do alvo agudo |
|---|---:|---:|---:|
| llama3.1:8b | 30 | 0/30 | 0/30 |
| qwen3:8b | 30 | 14/30 | 0/30 |
| qwen3.5:9b-mlx | 30 | 9/30 | 2/30 |
| gpt-6-sol | 30 | 30/30 | 14/30 |
| claude-opus-5-5 | 30 | 30/30 | 24/30 |
| claude-sonnet-5-5 | 30 | 30/30 | 20/30 |
| gpt-6-luna | 20 | 20/20 | 6/20 |
| gpt-5.6-terra | 30 | 30/30 | 14/30 |
| gpt-6-astra | 30 | 30/30 | 15/30 |
| gpt-6.1-sol | 30 | 30/30 | 17/30 |

O painel tem **223/290 conclusões**. Os 100% dos sete braços frontier referem-se ao workflow entre terminais observados. Nenhum modelo teve 100% de match lexical no legado. No caso 002, nenhum braço teve match lexical do alvo, apesar de poder haver decisões sindrômicas clinicamente aceitáveis: isso exige revisão médica, não relaxamento retrospectivo silencioso do avaliador.

Os três arquivos de adjudicação têm **870 slots** (450 base, 240 extensão, 180 addons). Todos estão vazios nos campos de revisor, diagnóstico, tratamento e segurança. A revisão médica segue pendente nos 10 gabaritos/rubrics e nos resultados; não há acurácia adjudicada para extrair desses arquivos.

Fontes: `evaluation/metrics.py:121-174` e `:197-269`; `evaluation/diagnosis_concepts.py:1-6` e `:56-85`; contagem dos CSV e recomputação no JSON acompanhante.

## Modificações anteriores que precisam ser preservadas

1. **Corpus v1 invalidado:** idade exata inventada no caso 003 quando a fonte só dizia início dos 30 anos. Corpus v2/protocolos v2–v4 foram pilotos excluídos por unidades, cronologia e critérios. O corpus v3/protocolo v5 congelou o painel principal. `docs/corpus_audit.md:7-11`.
2. **Auditoria editorial dos casos:** corrigiu D-dímero em µg/mL; alvo agudo versus sepse posterior no caso 003; segunda visita no 004; PET/molecular depois da biópsia no 005; biópsia adrenal condicionada no 006; TC sem antecipar identidade cirúrgica no 009; patologia separada da laparoscopia no 010; disposição desconhecida em vez de UTI inferida nos relatos. `docs/corpus_audit.md:15-26`.
3. **Paciente determinístico já implementado no legado:** lookup de fatos, sem segundo LLM. O prompt do patient agent LLM era uma reserva para braço futuro. Isso reduz invenção do simulador, mas não mede linguagem natural realista. `SPEC.md:39-43`; `prompts/patient_agent.md:1-5`; `tools/ehr_sandbox.py:150-199`.
4. **Controle temporal já implementado:** `time_zero`, `after_procedure` e `after_any_procedure`; seguimento, retrospectiva e dias posteriores bloqueados sem progressão explícita. Pedir procedimento não abre automaticamente histologia ou ressecção diferente. `tools/ehr_sandbox.py:179-199` e `:264-307`; `evaluation/test_ehr_temporal.py`.
5. **Parada de repetição já refinada:** v3 parava três pedidos idênticos inválidos/bloqueados/indisponíveis; v4 passou a parar três idênticos de qualquer status e protegeu erros contra exposição do prompt; v5 reforçou pré-requisitos e alvo temporal. `docs/protocol_freeze_manifest.json:63-65`; `runner/run_case.py:159-208`.
6. **Scoring v2 não confunde tentativa de diagnóstico com diagnóstico aceito:** precisa `tool_result.status=ok`; ausência conta como miss no denominador principal. Campos de julgamento de segurança/adequação não são decididos automaticamente. `docs/methodology.md:64`; `evaluation/metrics.py:121-146` e `:400-404`.
7. **Assinatura já era usada:** Codex para OpenAI e Claude Code para Anthropic, com JSON emulado, sessão efêmera e esforço high. Custos eram equivalentes/proxies de API, não fatura da assinatura. Os percentuais da cota não podiam ser atribuídos por tokens. O isolamento interno do Codex legado era parcial: execução no diretório do benchmark e ausência de persistência dos eventos internos. `providers/openai.py:1-5`, `:62-77`; `docs/safety.md:28-30`; `docs/subscription_usage_2026-09-28.md:19-25`.
8. **Jev/JEF era um braço adicional planejado, não executado no legado:** chave indisponível nesse histórico; não alterava o gabarito. O worktree posterior realmente o incorporou como triagem/guarda, condição experimental distinta. `docs/jev_methodology.md:1-5` e `:13-19`.

## Recursos e custo no legado

O EHR e o avaliador legado medem contagens de analitos, imagem, procedimentos, medicações, chamadas, fatos retornados e custo de inferência. **Não foi encontrada tabela numérica implementada de custo relativo por exame, nem orçamento clínico em unidades de simulação** naquele código. A especificação cita recursos/custo por pedido, mas esse objetivo não equivale a uma política de preços implementada. `evaluation/metrics.py:173-184`, `:225-231` e `:262-268`; `tools/ehr_sandbox.py:150-307`.

O painel teve **3.868 respostas de ferramenta**, das quais **957 `not_available_in_source`** (24,7%). Isso não significa 957 pedidos clinicamente desnecessários: inclui informação ausente no artigo, nomes/aliases não reconhecidos e etapas bloqueadas. No llama3.1 houve 818 resultados inválidos e 642 repetições exatas dentro de uma run; no qwen3.5 local, 190 indisponíveis e 120 repetições. O comportamento operacional, sobretudo nos modelos locais, é um problema separado da qualidade diagnóstica.

As sete famílias frontier concluíram seu workflow, mas tiveram 598 respostas indisponíveis em 2.347 ações. Portanto, preservar a honestidade de `unknown/not_available` e melhorar roteamento pode poupar ações sem fabricar valores. A documentação de outubro já investigou esse caminho; a oportunidade atual é medir desperdício/indicação e efeito em casos novos, sem simplesmente remover exames pela ausência da fonte.

## Complemento: trabalhos de outubro no worktree atual

Fonte de leitura: `/Users/test/MIRA-RAUL/.claude/worktrees/complete-remaining-100-cases-356596`, relatórios v3 e `AGENTS.md`. Este complemento cita apenas documentos agregados existentes; não recompõe nem publica dados privados. Os números desta seção são **snapshots relatados**, sem auditoria independente dos traces/ledger daquele worktree nesta tarefa.

| Etapa | O que já foi tentado | Resultado documentado e limite |
|---|---|---|
| Extensões outubro | Qwen3.8 Prime/0902; Sonnet e Opus na assinatura; rejulgamento mais rigoroso | Juiz barato e Pro discordaram; Opus 10/10 pelo juiz original, 7–8/10 sob leitura estrita. Não comparar diretamente com matcher lexical legado. |
| v3 inicial | Sonnet paciente com regras, N=3 trocas, exame físico, espera de resultado, guarda JEF opcional | Qwen 8/10 em ambos braços; conversa 10/10; custo duplicou; guarda não mudou diagnóstico. |
| N=1/N=2 + exame inicial | Redução de trava/turnos e troca Qwen por GLM-5 | Qwen 8–9/10; GLM-5 5–7/10; custo GLM cerca de 1/5, uma execução por variante. |
| Cascata v1 | GLM → JEF → Qwen → Sonnet/Opus | 7/10; não corrigiu erros; revisor ancorado concordou com diagnóstico errado apesar de listar exames faltantes. |
| Cascata v2 | Sonnet às cegas, executar perguntas/exames antes de aceitar, Opus árbitro, resultados imediatos | 27/30; 17 revisados acertaram, escapes nos aceites e falha antes da revisão. Triagem de confiança não prova diagnóstico certo. |
| v3.2 | Mapa enxuto, pré-requisitos, aviso ferramenta, resgate, auditoria 20%, gatilho de exame definitivo | v3.2a 9/10, b 9/10, c 10/10. Critério 009 mudou com autorização: Meckel deixou obrigatório; cascata v2 reavaliada passou 27/30 → 29/30. Não atribuir essa diferença ao pipeline. |
| v3.3–v3.5 | Matcher estrito; component/panel/same; recusa genérico→específico; sweep exposições; Opus baixa confiança | Casos externos usados para ajuste: 3/5 → 4/5 → 5/5. Regressão pública 10/10. Cinco casos fechados novos após freeze: 5/5; uma execução, juiz LLM. |
| v3.6 | Aliases/famílias/painéis, LDH ≠ lactato, wrong-tool entregue, tiers de custo, cap8 com fila, primeira fala obrigatória | 20/20 juiz, proposta 15/20; testes 20,8→19,4; tiers3 45→34; API real/caso +32%. Fluxo ajustado nesses casos; não é taxa externa. |
| v3.7 | Formato da fala sem nova IA; prontuário Haiku posterior e rastreável | Fala 84% formato central em 19 mensagens; prontuário maior cobertura, mas mais números fora da fonte que GLM. Pós-processamento não muda decisão. |

Documentos: `reports/v3_design.md`, `v3_pilot_qwen38_0902.md`, `v3_n_variants_glm5.md`, `v3_cascade_pilot.md`, `v3_cascade_v2.md`, `v3_cascade_3runs_resolutions.md`, `v3_cascade_v32.md`, `v3_strict_exams.md`, `v3_validation_new_closed_cases.md`, `v3_6_order_policy_opening.md`, `v3_7_chart_note_and_speech.md`; `AGENTS.md` daquele worktree.

## Melhorias que o histórico sustenta

1. **Prosseguir sobre a base v3.7, preservando suas correções.** A primeira investigação sobre base antiga é insuficiente: políticas e avaliações novas já existem em outro worktree. Não substituir um fluxo maturado por protótipo que repete essas ideias.
2. **Explicitar custos relativos de simulação.** O v3.6 usa preços aproximados em dólares, ranking sem validação econômica; o pedido atual é unidades relativas. Separar custo API real, consumo de assinatura e unidades clínicas ajuda a avaliar o objetivo sem sugerir uma conta real de exames.
3. **Medir indicação por pedido e novidade de informação.** A política v3.6 adiou mais que reduziu: 89/97 exames na fila foram executados depois. O custo de modelo subiu. É preciso avaliar quais exames mudaram diferencial/conduta, pedidos sem justificativa, repetidos e desnecessários. Essa classificação exige estado conhecido no momento e julgamento independente.
4. **Congelar critérios e avaliar casos novos antes de calibrar mais limiares.** O JEF foi calibrado nos mesmos casos, o 009 foi reclassificado e correções foram escolhidas após erros observados. Manter 20/20 no conjunto conhecido é regressão útil; 100% esperado em casos futuros não está estabelecido.
5. **Manter a camada que coleta dados decisivos e a revisão independente.** As cascatas ganharam quando o revisor fez perguntas/exames que faltavam, e falharam quando apenas concordou com a proposta. Confiança ou concordância de dois modelos sem dados novos não é sinal suficiente para garantir acerto.
6. **Separar fidelidade, fala e nota clínica de diagnóstico.** A nota Haiku cobre mais resultados, mas o próprio relatório mostra erros numéricos; citar fonte não basta para validar correspondência. Uso da assinatura pode baixar gasto marginal OpenRouter, sem tornar quota ilimitada.

Nenhuma melhoria clínica foi validada por esta auditoria. Ela fornece o mapa do que realmente existe, os denominadores conferidos e os limites necessários para testar a próxima variante sem apagar erros ou confundir condições experimentais.
