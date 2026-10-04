# Análise combinada: 3 runs, 5 modelos principais + extensão Qwen3.8-max-prime (180 encontros)

Terminais: 180/180; problemas de integridade: 0. **Julgamento por LLM (Gemini 3.1 Flash-Lite); revisão médica pendente. O juiz não estabelece segurança clínica nem superioridade.** Encontros sem julgamento (falha operacional/sem diagnóstico) são mostrados à parte e não contam como erro nem acerto.

Repetições do mesmo caso **não são pacientes independentes**: o Wilson sobre os julgamentos agrupados é apenas descritivo e subestima a incerteza; o bootstrap por caso (10 casos, 10 000 reamostragens, semente 20261004) é mostrado como contraste, também descritivo.

## Placar por modelo

| Modelo | Run 1 | Run 2 | Run 3 | Agregado (corretos/julgados) | Wilson 95% | Bootstrap por caso 95% | Sem julgamento |
|---|---:|---:|---:|---:|---|---|---:|
| openai/gpt-oss-120b | 5/8 | 3/9 | 2/8 | 10/25 (40.0%) | 23.4%–59.3% | 13.0%–67.9% | 5 |
| z-ai/glm-4.5-air | 7/10 | 6/9 | 6/10 | 19/29 (65.5%) | 47.3%–80.1% | 44.8%–86.2% | 1 |
| z-ai/glm-5 | 7/10 | 8/10 | 5/10 | 20/30 (66.7%) | 48.8%–80.8% | 40.0%–90.0% | 0 |
| qwen/qwen3.5-397b-a17b | 6/10 | 6/10 | 7/10 | 19/30 (63.3%) | 45.5%–78.1% | 36.7%–83.3% | 0 |
| openai/gpt-5.2 | 7/10 | 7/10 | 9/10 | 23/30 (76.7%) | 59.1%–88.2% | 53.3%–96.7% | 0 |
| qwen/qwen3.8-max-prime | 9/10 | 8/10 | 9/10 | 26/30 (86.7%) | 70.3%–94.7% | 70.0%–100.0% | 0 |

Todos os 6 modelos: 117/174 julgados (67.2%); 6 sem julgamento em 180 terminais. Cinco modelos principais: 91/144 (63.2%) em 150 terminais. `qwen/qwen3.8-max-prime` foi adicionado depois (mesmo protocolo e juiz, traces isolados em `runs/qwen38_max_prime/`; parâmetros de amostragem assumidos iguais aos do Qwen3.5).

## Consistência entre repetições (descritiva)

Casos por número de runs corretas, casos estáveis (mesmo veredito nas três runs) e concordância média par a par. Adaptação descritiva; **não** é o ConsistencyDx do artigo.

| Modelo | 0/3 | 1/3 | 2/3 | 3/3 | Estáveis | Concordância par a par |
|---|---:|---:|---:|---:|---:|---:|
| openai/gpt-oss-120b | 2 | 1 | 1 | 2 | 4/6 | 77.8% |
| z-ai/glm-4.5-air | 0 | 3 | 2 | 4 | 4/9 | 63.0% |
| z-ai/glm-5 | 2 | 1 | 2 | 5 | 7/10 | 80.0% |
| qwen/qwen3.5-397b-a17b | 2 | 1 | 3 | 4 | 6/10 | 73.3% |
| openai/gpt-5.2 | 1 | 1 | 2 | 6 | 7/10 | 80.0% |
| qwen/qwen3.8-max-prime | 0 | 1 | 2 | 7 | 7/10 | 80.0% |

Casos com algum encontro sem julgamento ficam fora desta tabela.

## Vereditos por caso (run 1, run 2, run 3; Y=correto, N=incorreto, ?=sem julgamento)

| Caso | gpt-oss-120b | glm-4.5-air | glm-5 | qwen3.5-397b-a17b | gpt-5.2 | qwen3.8-max-prime |
|---|---|---|---|---|---|---|
| case_001 | ?NN | N?N | NNN | YYN | NNY | NNY |
| case_002 | NNN | YNY | NNN | NNN | YNY | YNY |
| case_003 | Y?? | YYY | YYY | YYY | YYY | YYY |
| case_004 | YNN | YYY | YYY | NNY | YYY | YYY |
| case_005 | YYY | NYN | YYY | YYY | YYY | YYY |
| case_006 | NN? | YYY | YYY | YYY | YYY | YYY |
| case_007 | YYN | YNN | YYN | YNY | YYY | YYY |
| case_008 | YYY | YYY | YYY | YYY | YYY | YYY |
| case_009 | ?NN | YYN | NYN | NNN | NNN | YYN |
| case_010 | NNN | NNY | YYN | NYY | NYY | YYY |

## Custos

Ledger total US$ 7.036128653 (estados: {'settled': 3664}).
Conta OpenRouter (snapshots sem cache finais): uso US$ 4.274237323; igual ao ledger: False.
Soma dos terminais (CSV) US$ 6.904420710; por run: run 1 US$ 2.261111555, run 2 US$ 2.126242715, run 3 US$ 2.517066440. A diferença para o ledger vem do piloto invalidado, de tentativas arquivadas/incompletas e do custo não atribuído de chamadas perdidas.

| Ator | Execução | Chamadas | Custo US$ |
|---|---|---:|---:|
| doctor | qwen38_run1 | 51 | 0.839400 |
| doctor | qwen38_run2 | 49 | 0.781868 |
| doctor | qwen38_run3 | 51 | 1.027948 |
| doctor | run1_ou_historico | 549 | 1.029856654 |
| doctor | run2 | 437 | 0.946386615 |
| doctor | run3 | 446 | 1.021165615 |
| judge | qwen38_run1 | 10 | 0.00320200 |
| judge | qwen38_run2 | 10 | 0.00319475 |
| judge | qwen38_run3 | 10 | 0.00328475 |
| judge | run1_ou_historico | 53 | 0.01655150 |
| judge | run2 | 48 | 0.01516000 |
| judge | run3 | 48 | 0.01516525 |
| matcher | qwen38_run1 | 111 | 0.006922745 |
| matcher | qwen38_run2 | 143 | 0.008655190 |
| matcher | qwen38_run3 | 107 | 0.006375895 |
| matcher | run1_ou_historico | 354 | 0.026940900 |
| matcher | run2 | 282 | 0.017171270 |
| matcher | run3 | 412 | 0.024514105 |
| patient | qwen38_run1 | 1 | 0.0097 |
| patient | qwen38_run2 | 2 | 0.018884 |
| patient | qwen38_run3 | 4 | 0.052456 |
| patient | run1_ou_historico | 178 | 0.429592389 |
| patient | run2 | 162 | 0.334922890 |
| patient | run3 | 145 | 0.366156825 |
| unattributed_interrupted_calls | run1_ou_historico | 1 | 0.030653310 |

`run1_ou_historico` agrega a rodada 1, o piloto invalidado e tentativas incompletas anteriores. `unattributed_interrupted_calls` é a diferença de conta de US$ 0,030653310 de 13 chamadas perdidas por timeout de rede, não atribuível a nenhuma delas individualmente (`reports/run23_timeout_reconciliation.json`).

| Modelo | Custo terminais US$ | Custo médio/encontro US$ | Prompt mediana [Q1; Q3] | Conclusão | Raciocínio | Latência s | Turnos | Chamadas de ferramenta |
|---|---:|---:|---|---|---|---|---|---|
| openai/gpt-oss-120b | 0.2072 | 0.00691 | 62,810 [34,293; 130,236] | 10,312 [4,777; 17,374] | 2,390 [1,860; 3,081] | 120.1 [58.4; 206.8] | 7.0 [6.0; 10.0] | 7.0 [5.0; 7.8] |
| z-ai/glm-4.5-air | 0.1210 | 0.00403 | 16,173 [14,285; 27,931] | 3,157 [2,591; 3,808] | 1,863 [1,554; 2,199] | 45.4 [33.7; 67.1] | 2.0 [2.0; 2.8] | 5.5 [5.0; 8.0] |
| z-ai/glm-5 | 0.4685 | 0.01562 | 21,066 [13,685; 29,938] | 5,211 [3,827; 6,636] | 2,760 [2,182; 4,110] | 77.8 [51.2; 99.2] | 3.0 [2.0; 4.0] | 6.0 [5.0; 8.0] |
| qwen/qwen3.5-397b-a17b | 1.0945 | 0.03648 | 17,696 [13,225; 27,992] | 7,942 [6,201; 9,736] | 5,790 [4,277; 7,828] | 105.5 [62.4; 139.1] | 3.0 [2.0; 3.0] | 6.0 [5.0; 7.0] |
| openai/gpt-5.2 | 2.2514 | 0.07505 | 21,692 [15,364; 28,446] | 3,949 [3,301; 4,784] | 2,056 [1,522; 2,256] | 94.5 [75.6; 121.5] | 4.0 [4.0; 5.0] | 9.0 [7.2; 10.8] |
| qwen/qwen3.8-max-prime | 2.7619 | 0.09206 | 18,644 [14,850; 20,610] | 4,978 [4,099; 5,770] | 1,776 [1,303; 2,632] | 82.3 [66.7; 90.3] | 1.0 [1.0; 1.0] | 9.0 [7.0; 10.8] |

A latência de encontros retomados após interrupção reflete tempo de parede e deve ser usada com cautela.

## Parâmetros, provedores, commits e logprobs

Commits por run: {'run1': ['0a6636bc635aa87988e5b0ee5d5de6fb47eb9324', '138a1a9ae8b853dd14e2809070ae5dba79069d31', '7ae4460a51a33221c21f48a2fdf6e68720f13d7f', '9028e00d577d4e1ab83101577bcf4c2c165a394c', '9d45442ede86e805ae719d26c0989d70b9716527', 'a4b9ed3984c4b5bcd77af0b64fe08dc0480fd79b', 'cacbf96b5ff3f699a9e342173303f46b3fe14026'], 'run2': ['fa2dd4d76bb451acdd640993dd39e5f88b0182a8'], 'run3': ['fa2dd4d76bb451acdd640993dd39e5f88b0182a8'], 'runext1': ['6fac61957c9be0f1cb704e92a3c45efd03cef338'], 'runext2': ['6fac61957c9be0f1cb704e92a3c45efd03cef338'], 'runext3': ['6fac61957c9be0f1cb704e92a3c45efd03cef338']}. Provedores nos traces: {'openai/gpt-5.2': ['OpenAI'], 'openai/gpt-oss-120b': ['Mancer 2'], 'qwen/qwen3.5-397b-a17b': ['Parasail'], 'z-ai/glm-4.5-air': ['Novita'], 'z-ai/glm-5': ['StreamLake'], 'qwen/qwen3.8-max-prime': ['Alibaba']}.

| Execução | Modelo | Respostas do médico | Com logprobs recebidos |
|---|---|---:|---:|
| run1 | openai/gpt-5.2 | 87 | 0 |
| run1 | openai/gpt-oss-120b | 136 | 0 |
| run1 | qwen/qwen3.5-397b-a17b | 77 | 73 |
| run1 | qwen/qwen3.8-max-prime | 51 | 0 |
| run1 | z-ai/glm-4.5-air | 81 | 0 |
| run1 | z-ai/glm-5 | 72 | 0 |
| run2 | openai/gpt-5.2 | 90 | 0 |
| run2 | openai/gpt-oss-120b | 124 | 0 |
| run2 | qwen/qwen3.5-397b-a17b | 63 | 63 |
| run2 | qwen/qwen3.8-max-prime | 49 | 0 |
| run2 | z-ai/glm-4.5-air | 80 | 0 |
| run2 | z-ai/glm-5 | 69 | 0 |
| run3 | openai/gpt-5.2 | 88 | 0 |
| run3 | openai/gpt-oss-120b | 111 | 0 |
| run3 | qwen/qwen3.5-397b-a17b | 64 | 63 |
| run3 | qwen/qwen3.8-max-prime | 51 | 0 |
| run3 | z-ai/glm-4.5-air | 83 | 0 |
| run3 | z-ai/glm-5 | 100 | 0 |

Logprobs foram solicitados quando suportados; ausentes ficam marcados como ausentes. Nenhum ProbScore foi calculado ou inventado.

## Verificações

Hashes legacy conferidos em `/Users/test/MIRA-RAUL`: 978; divergentes: 0; ausentes: 0. Manifestos de traces: 180 arquivos no total (`reports/final_trace_manifest_runs123.json` para os 5 modelos principais e `reports/final_trace_manifest_qwen38_max_prime.json` para a extensão).

## Limites

Revisão médica cega pendente. O juiz LLM usa temperatura 1 e pode variar. A comparação com o benchmark histórico lexical (Fase 1) não é equivalente (outros modelos, ferramentas, juiz e transporte). Nenhuma afirmação de acurácia clínica ou superioridade.
