# MIRA-RAUL — métricas desde o início até a v5

Conferência em 16/10/2026. Última versão publicada confirmada por consulta somente leitura ao GitHub: [merge do PR 8](https://github.com/codecapelo/MIRA-raul/commit/5146c4491d3a1086c8a3e75fb0b90486d764a881), 10/10/2026. Código de origem v5 local 9ccc23e. Nenhuma nova inferência, alteração de resultado ou consulta de credenciais/conta foi realizada.

**A v5 tem 12/12 juízos positivos em um agregado selecionado após correções, e 6/12 propostas iniciais positivas. A rodada conjunta v5z, preservada, foi 11/12; todas as 29 execuções de desenvolvimento da v5 totalizam 27 positivas e 2 negativas. Nenhum desses percentuais é acurácia clínica validada.**

## Regras de leitura

- **Legado:** match lexical congelado do alvo agudo, separado da conclusão do fluxo.
- **Fase OpenRouter e posteriores:** veredito de juiz LLM. Juiz barato, juiz Pro e critérios de especificidade mudaram; não são uma única escala.
- **Proposta inicial:** resultado do médico antes da supervisão. **Final:** resultado do sistema após revisão quando existente.
- **Terminais:** registros encerrados, incluindo falhas e execuções de desenvolvimento; não equivalem a pacientes distintos.
- **Custos:** separar OpenRouter real, custo da assinatura desconhecido, estimativa equivalente de API e unidades artificiais de exames.
- A proposta de anamnese feita nesta conversa é análise de design: não foi implementada ou avaliada no MIRA e não altera as métricas.

## 1. Painel legado — setembro de 2026

290 terminais de 300 planejados; as dez ausências pertencem ao braço interrompido pelo usuário. 223/290 conclusões do fluxo e 112/290 matches lexicais, reconstituídos na auditoria histórica. Não interpretar 112/290 como diagnóstico adjudicado; nem 223/290 como acurácia.

| Modelo, nome preservado no projeto | Terminais | Fluxo concluído | Match lexical |
|---|---:|---:|---:|
| Llama 3.1 8B | 30 | 0/30 | 0/30 |
| Qwen3 8B | 30 | 14/30 | 0/30 |
| Qwen3.5 9B MLX | 30 | 9/30 | 2/30 |
| GPT-6 Sol | 30 | 30/30 | 14/30 |
| Claude Opus 5.5 | 30 | 30/30 | 24/30 |
| Claude Sonnet 5.5 | 30 | 30/30 | 20/30 |
| GPT-6 Luna | 20 | 20/20 | 6/20 |
| GPT-5.6 Terra | 30 | 30/30 | 14/30 |
| GPT-6 Astra | 30 | 30/30 | 15/30 |
| GPT-6.1 Sol | 30 | 30/30 | 17/30 |

No legado há 870 campos de adjudicação previstos ainda vazios segundo a auditoria. O “protocolo v5” do legado não deve ser confundido com o agente MIRA-RAUL v5 de outubro.

Fonte: [auditoria histórica](../../reports/history_legacy_audit_2026-10-08.md). Este documento não refez os hashes dos 978 arquivos; usa a auditoria existente para esse painel.

## 2. Primeira fase OpenRouter — rodada base e extensões

Cinco modelos × dez casos × três repetições = 150 terminais. Juiz positivo em 91/144 julgados (63,2%), seis sem julgamento. Com dois Qwen3.8 adicionais: 210 terminais, 141/204 positivos (69,1%), os mesmos seis sem julgamento.

| Modelo | Positivos/julgados | Percentual | Sem julgamento | OpenRouter médio por terminal |
|---|---:|---:|---:|---:|
| GPT-OSS 120B | 10/25 | 40,0% | 5 | US$ 0,00691 |
| GLM-4.5-Air | 19/29 | 65,5% | 1 | US$ 0,00403 |
| GLM-5 | 20/30 | 66,7% | 0 | US$ 0,01562 |
| Qwen3.5 397B | 19/30 | 63,3% | 0 | US$ 0,03648 |
| GPT-5.2 | 23/30 | 76,7% | 0 | US$ 0,07505 |
| Qwen3.8 Max Prime | 26/30 | 86,7% | 0 | US$ 0,09206 |
| Qwen3.8 Max 0902 | 24/30 | 80,0% | 0 | US$ 0,04401 |

Custos médios da tabela: terminais, todos os atores, sem rateio de todos os pilotos. Snapshot financeiro ao fechar 150: US$ 4,274237323, incluindo custos técnicos. Ao fechar 210: US$ 8,356544873.

Nos Qwen3.8, conversa com o paciente em apenas 23% e 7% dos encontros; achados cirúrgicos/histopatológicos finais pedidos em 60% e 53%. A compressão temporal limita a interpretação desses escores como qualidade de anamnese.

Extensões pela assinatura:
- Sonnet 5.5: 9/10 pelo juiz original; 8/10 na leitura estrita documentada; OpenRouter US$ 0,0063 e equivalente de API do CLI cerca de US$ 1,19.
- Opus 5.5: 10/10 pelo juiz original; 7–8/10 na leitura estrita documentada; OpenRouter US$ 0,0078 e equivalente de API do CLI cerca de US$ 1,85.
- Ferramentas emuladas em JSON e controle de amostragem distintos dos braços API. As leituras estritas não são revisão médica independente.

Fonte: [análise combinada](../../.claude/worktrees/complete-remaining-100-cases-356596/reports/all_runs_summary.md), [Sonnet](../../.claude/worktrees/complete-remaining-100-cases-356596/reports/claude_sonnet_5_5_subscription_run1.md), [Opus](../../.claude/worktrees/complete-remaining-100-cases-356596/reports/claude_opus_5_5_subscription_run1.md).

## 3. Evolução da arquitetura

Todos os resultados finais abaixo são de juiz LLM; coortes e critérios diferem.

| Etapa | Resultado documentado | Proposta inicial quando disponível | Limite central |
|---|---|---|---|
| v3, Qwen e entrevista obrigatória, sem/com JEF | 8/10 em cada braço | Não separado do final | Dez casos conhecidos por braço; JEF não mudou o diagnóstico |
| v3, Qwen N=1/N=2 e exame inicial | 8/10; 9/10 | Não separado do final | Uma execução por configuração |
| v3, GLM-5 N=1/N=2 | 5/10; 7/10 | Não separado do final | Custo menor, resultado variável |
| Primeira cascata | 7/10 | 7/10 | Não corrigiu os erros nessa amostra |
| Cascata com revisor cego, três repetições | 27/30 inicialmente; 29/30 após mudança do critério | 19/30 inicialmente; 22/30 no critério posterior | A mudança de escore não é ganho de código |
| v3.2a / b / c | 9/10; 9/10; 10/10 | 8/9; 8/10; 9/10 | Correções e configurações diferentes |
| v3.3 / v3.4 / v3.5, cinco casos usados no ajuste | 3/5 → 4/5 → 5/5 | Não resumido uniformemente | Desenvolvimento nos mesmos casos |
| v3.5, cinco casos novos após freeze | 5/5 | 4/5 | Sinal externo àquele ajuste, mas n=5, uma execução e juiz LLM |
| v3.5 / v3.6, conjunto de vinte | 20/20 em cada versão | 15/20 em cada | Casos conhecidos, não taxa de generalização |
| v3.7, mudança de fala/prontuário | 5/5 no pequeno teste de fala, antes/depois | 3/5 em cada | Teste de apresentação, não validação diagnóstica nova |
| v4 original | 9/10 | 8/10 | Dez públicos conhecidos |
| v4 com revisão final working | 10/10 em novos encontros | 9/10 | Rodada distinta; revisão offline de 10/10 não soma novos encontros |
| v4 fast1 | 9/10 | 4/10 | Falha de cegamento documentada |
| v4 fast2 / fast3 | 1/2; 1/2 | — | Pilotos preservados, não ampliados |
| v4 fast4 | 10/10 públicos; 10/10 fechados históricos | 6/10; 6/9 julgadas | Fechados já usados no projeto; não holdout externo novo |
| v5, rodada conjunta v5z | 11/12 | 5/11 julgadas | Uma proposta sem julgamento; falhas finais preservadas |
| v5, agregado selecionado após correções | 12/12 | 6/12 | Seleção de execuções e alterações entre casos |
| v5, todas as variantes de desenvolvimento | 27/29 | 13/28 julgadas | Mistura condições e repetições; inventário, não um benchmark único |

A revisão final tem papel importante na condição atual: 6/12 propostas iniciais positivas e 12/12 finais no agregado selecionado. Não converter isso em “o médico sozinho tem 100%”.

Fontes: relatórios v3_pilot_qwen38_0902, v3_n_variants_glm5, v3_cascade_pilot, v3_cascade_3runs_resolutions, v3_cascade_v32, v3_strict_exams, v3_validation_new_closed_cases, v3_6_order_policy_opening, v3_7_chart_note_and_speech, v4_final_summary, v4_fast4_summary e v5_dev_report, em .claude/worktrees/complete-remaining-100-cases-356596/reports/. O inventário v5z e todas as variantes foi recontado dos eventos case_complete nesta conferência.

## 4. Métricas operacionais e de recursos

### v3.5 para v3.6, vinte casos conhecidos

| Medida | v3.5 | v3.6 |
|---|---:|---:|
| Exames executados por caso | 20,8 | 19,4 |
| Total de exames nível 3 | 45 | 34 |
| Trocas com o paciente, média | 2,05 | 2,85 |
| OpenRouter real por caso, arredondado | US$ 0,026 | US$ 0,034 |
| Resultado final / proposta | 20/20 / 15/20 | 20/20 / 15/20 |

A política reduziu exames, mas aumentou gasto de inferência; 89 de 97 itens em fila acabaram executados. Os preços clínicos aproximados da v3.6 não são conta real de exames.

### v3.6, v4 working e fast4 nos dez públicos

| Medida | v3.6 | v4 working | fast4 |
|---|---:|---:|---:|
| Mediana de tempo ativo | 158,46 s | 515,93 s | 103,61 s |
| OpenRouter dos dez encontros | US$ 0,35024 | US$ 0,11515 | US$ 0,21032 |
| Entrada CLI mediana por caso | 34.522,5 | 183.706,5 | 33.473,5 |

São comparações históricas descritivas, com mudanças de modelos, transporte, contexto e cache. Tempo ativo não equivale a tempo de parede. Na fast4 fechada, P95 de parede foi 8.785,85 s por pausas/interrupções; P95 ativo, 158,47 s. A primeira fala completa na fast4 teve mediana 1,59 s públicos / 1,52 s fechados.

### v4 fast4 versus v5, mesmos doze casos selecionados

| Medida | fast4 | v5 |
|---|---:|---:|
| Final positivo | 12/12 | 12/12 |
| Proposta inicial positiva | 5/12 | 6/12 |
| Trocas com paciente, média | 4,8 | 3,4 |
| Turnos do médico, média | 5,1 | 3,9 |
| Pedidos de investigação, média | 8,6 | 7,0 |
| Primeiro resultado de exame, mediana | 10,4 s | 9,3 s |
| Tempo até resultado final, mediana relatada | 108 s | 108 s |
| OpenRouter por caso | US$ 0,0268 | US$ 0,0255 |
| Bloqueios por falta de história | 9 | 1 |
| Retenções por custo | 2 | 0 |
| Pedidos duplicados bloqueados | 14 | 0 |
| Pedidos sem resultado disponível, contador do resumo | 33 | 45 |

Pedidos de investigação não equivalem a fontes/exames efetivamente executados; “duplicados bloqueados = 0” não é garantia de ausência de redundância clínica. Aumento de indisponíveis merece acompanhamento.

Paciente Sonnet da v5: equivalente de API cerca de US$ 0,0399/caso, usado pela assinatura. Não é débito adicional OpenRouter observado. Se cobrado como API, a soma ilustrativa com os US$ 0,0255 seria cerca de US$ 0,0654/caso, sem equivaler a uma cotação integral de produção. O preço monetário atribuível à assinatura permanece desconhecido.

## 5. Fidelidade e comunicação

Na auditoria LLM cega de respostas às mesmas perguntas, **49 respostas v4 e 35 v5**:

| Tipo de ocorrência | v4 | v5 |
|---|---:|---:|
| Negativos sem fonte | 38 | 0 |
| Quebras de papel | 7 | 1 |
| Detalhes inventados | 6 | 12 |
| Omissões de fatos documentados | 17 | 15 |

São contagens de ocorrências, não percentuais de respostas nem taxas populacionais. O auditor é da mesma família do paciente e a revisão médica está pendente. A v5 melhora determinados problemas nessa amostra, mas não demonstra ausência geral de invenção ou melhora relevante de omissões.

Na auditoria específica dos fechados fast4: 17 de 46 respostas continham negativos sem fonte, cinco eram ambíguas; 68 trechos de exame foram conferidos sem candidatos de divergência literal. Essa é outra amostra/método; não misturar suas unidades com a tabela acima.

Na v3.7: formato central da fala cumprido em 16/19 mensagens (84%), contra 1/57 antes. No estudo de prontuário de oito encontros, Haiku cobriu 99% dos resultados contra 51% do GLM, mas teve 14/438 números fora da fonte contra 3/242. Melhor cobertura não significou melhor fidelidade numérica.

## 6. Volume do histórico

Recontagem dos arquivos presentes, com deduplicação de cópias idênticas por SHA-256, somada ao painel legado já auditado:

| Grupo | Terminais |
|---|---:|
| Painel legado | 290 |
| Primeira fase OpenRouter, incluindo Qwen e dois Claude | 230 |
| Variantes v3 | 207 |
| Variantes de encontros v4 | 54 |
| Variantes v5 | 29 |
| **Inventário total dessas séries** | **810** |

Os 520 posteriores ao legado foram recontados nesta tarefa. Este inventário exclui pilotos legados fora do painel, prefixos incompletos, juiz/revisor como chamada separada e análises offline sem novo encontro. Não é denominador de uma taxa global. Não significa 810 pacientes independentes ou 810 casos diferentes; há reutilização extensa dos casos.

## 7. Financeiro: o que é verificável agora

Ledgers locais consultados em modo somente leitura:

| Bloco | Chamadas registradas | Estado | Total |
|---|---:|---|---:|
| Base e desenvolvimento até v3.7 | 10.811 | Todas settled | US$ 18,965410033 |
| v4 compartilhada | 968 | Todas settled | US$ 1,061257675 |
| v5 | 642 | Todas settled | US$ 0,685754500 |
| **Subtotal dos três ledgers** | **12.421** | Sem linhas pendentes nesses arquivos | **US$ 20,712422208** |

Três snapshots finais históricos da conta após a v5 registram uso acumulado **US$ 20,843347608**. Não foi feita consulta viva de saldo. A diferença para o subtotal dos ledgers localizados é **US$ 0,130925400**.

Essa diferença já existe entre o fechamento anterior e o baseline de entrada da v5: 20,157593108 − 18,965410033 − 1,061257675. Sua origem não foi estabelecida nesta consolidação; não foi atribuída a zero nem a um ator. O custo incremental da v5, US$ 0,685754500, confere com a diferença entre seus snapshots antes/depois.

Logo, não é correto chamar o uso acumulado da conta de “custo total integralmente atribuído ao MIRA”. Também não inclui custo monetário das assinaturas nem os equivalentes de API do legado. Tetos antigos foram alterados em momentos documentados; esta tarefa não altera orçamento nem autoriza inferência.

## 8. Métricas ainda ausentes ou não validadas

- Acurácia, segurança e adequação de manejo adjudicadas por médicos.
- Desempenho da v5 em amostra independente suficiente e com condição congelada.
- Calibração clínica de confiança, curvas de confiabilidade ou Brier clínico validados.
- ConsistencyDx original; a base tem estabilidade descritiva do veredito em três repetições, não equivalência semântica integral.
- ProbScore comparável entre modelos: logprobs frequentemente ausentes; não foram inventados.
- Efeito causal isolado de cada mudança de versão.
- Métrica prospectiva da melhoria de anamnese proposta nesta conversa.
- Custo total monetário atribuível à assinatura.

**Leitura prática:** houve avanços operacionais em entrevista, roteamento, supervisão e velocidade. Os resultados atuais de desenvolvimento são altos após revisão, enquanto a proposta inicial da v5 permanece em 6/12. O próximo avanço de evidência depende de preservar os resultados desfavoráveis e testar uma versão congelada em casos reservados com revisão médica.

## Evidência da consolidação

[JSON agregado desta conferência](audit_aggregate.json). Contém apenas agregados, sem fatos ou diagnósticos individuais dos casos de acesso fechado. Fontes locais históricas foram lidas, mas os ledgers não foram modificados. Não houve commit nem publicação.

