# Análise encerrada com Luna parcial — MIRA-2026 com extensão de 28-09-2026

Corpus: `mvp10_v3_2026-09-26` · Protocolo: `mvp10_closedbook_v5_2026-09-26`.

Avaliação: `evaluation-v2` · Regras diagnósticas: `diagnostic-concepts-2026-09-26-v2` (SHA-256 `b2da153cd8d65df6658f45e715b0287cc4956a040bf62fbb8ddeb09d261df9fc`).

Trajetórias terminais: **230/240**. Revisão médica: **pendente**.

| Modelo | Runs | Conclusão | Alvo do encontro, média por caso | Diagnóstico publicado, média por caso | Top-3 alvo, média por caso | Chamadas | Mediana duração |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen3.5:9b-mlx | 30/30 | 30.0% [6.7, 56.7] | 6.7% [0.0, 20.0] | 6.7% [0.0, 20.0] | 6.7% [0.0, 20.0] | 335 | 54.6 s |
| qwen3:8b | 30/30 | 46.7% [23.3, 73.3] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 256 | 25.4 s |
| llama3.1:8b | 30/30 | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 930 | 63.2 s |
| gpt-6-sol | 30/30 | 100.0% [100.0, 100.0] | 46.7% [23.3, 70.0] | 40.0% [20.0, 60.0] | 46.7% [23.3, 70.0] | 401 | 170.4 s |
| claude-opus-5-5 | 30/30 | 100.0% [100.0, 100.0] | 80.0% [56.7, 100.0] | 80.0% [56.7, 100.0] | 80.0% [56.7, 100.0] | 367 | 85.6 s |
| claude-sonnet-5-5 | 30/30 | 100.0% [100.0, 100.0] | 66.7% [36.7, 90.0] | 66.7% [36.7, 90.0] | 66.7% [36.7, 90.0] | 335 | 58.6 s |
| gpt-6-luna | 20/30 | 100.0% | 31.0% | 26.2% | 31.0% | 257 | 348.5 s |
| gpt-5.6-terra | 30/30 | 100.0% [100.0, 100.0] | 46.7% [20.0, 73.3] | 36.7% [10.0, 63.3] | 46.7% [20.0, 73.3] | 305 | 128.2 s |

Ausência de diagnóstico final **aceito pelo EHR** conta como erro nas três colunas diagnósticas acima. Cada caso recebe o mesmo peso; no painel completo de três runs por caso, a média por caso equivale à proporção das 30 runs. Os valores são triagens lexicais, não acurácia clínica adjudicada.

| Modelo | Diagnósticos aceitos pelo EHR | Match do alvo entre aceitos |
|---|---:|---:|
| qwen3.5:9b-mlx | 9/30 | 22.2% |
| qwen3:8b | 14/30 | 0.0% |
| llama3.1:8b | 0/30 | — |
| gpt-6-sol | 30/30 | 46.7% |
| claude-opus-5-5 | 30/30 | 80.0% |
| claude-sonnet-5-5 | 30/30 | 66.7% |
| gpt-6-luna | 20/20 | 30.0% |
| gpt-5.6-terra | 30/30 | 46.7% |

## Quadro operacional pós-hoc

| Modelo | Planejadas | Terminais clínicas | Concluídas | Tentativas com erro preservadas | Tentativas encerradas observadas | Concluídas/30 planejadas | Concluídas/encerradas, condicional |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen3.5:9b-mlx | 30 | 30 | 9 | 0 | 30 | 30.0% | 30.0% |
| qwen3:8b | 30 | 30 | 14 | 0 | 30 | 46.7% | 46.7% |
| llama3.1:8b | 30 | 30 | 0 | 0 | 30 | 0.0% | 0.0% |
| gpt-6-sol | 30 | 30 | 30 | 1 | 31 | 100.0% | 96.8% |
| claude-opus-5-5 | 30 | 30 | 30 | 0 | 30 | 100.0% | 100.0% |
| claude-sonnet-5-5 | 30 | 30 | 30 | 0 | 30 | 100.0% | 100.0% |
| gpt-6-luna | 30 | 20 | 20 | 2 | 22 | 66.7% | 90.9% |
| gpt-5.6-terra | 30 | 30 | 30 | 5 | 35 | 100.0% | 85.7% |

Quadro operacional descritivo pós-hoc: encerradas = terminais clínicas + erros preservados distintos e verificáveis do mesmo freeze. A taxa condicional considera somente essas tentativas observadas; retries selecionados não são independentes e não recebem IC IID. Concluídas/30 planejadas mostra a cobertura do planejamento; trajetórias ausentes após o encerramento não equivalem a falhas observadas. A completude histórica da preservação é desconhecida: zero erros preservados não demonstra ausência de erros. `unknown` indica inventário indisponível ou evidência não verificável; prefixos sem fechamento e registros de outros protocolos não entram. `OpenAIAccountError` é uma classe genérica e não prova autenticação, cota ou causa clínica.

### Diagnóstico passivo de erros — cobertura parcial

| Modelo | Falhas de formato confirmadas em tentativas com erro | Tentativas com erro sem categoria passiva confirmada |
|---|---:|---:|
| qwen3.5:9b-mlx | 0 | 0 |
| qwen3:8b | 0 | 0 |
| llama3.1:8b | 0 | 0 |
| gpt-6-sol | 0 | 1 |
| claude-opus-5-5 | 0 | 0 |
| claude-sonnet-5-5 | 0 | 0 |
| gpt-6-luna | 0 | 2 |
| gpt-5.6-terra | 1 | 4 |

Categorias vêm exclusivamente de sidecars passivos permitidos, associados ao modelo e a um único evento `error` com distância UTC de até dois segundos. Eventos `start` não contam como erro. Cobertura começa nas ativações registradas e pode ter lacunas; não inferir retrospectivamente categorias ou causas antigas. Zero outputs inválidos nos traces terminais não significa ausência de erros de formato em todas as tentativas. As causas sem evidência passiva permanecem desconhecidas; uso/custo da última chamada falha continua desconhecido.
- Sidecar `results/provider_diagnostics_2026-09-28/gpt-5.6-terra.jsonl` · SHA-256 `12448c3160d4cbf79c9ba70367a853159f4113d3752c4692b6a2f0a189b82f39` · ativações UTC: 2026-09-28T19:47:19.969821Z, 2026-09-28T20:11:01.043996Z.
- Sidecar `results/provider_diagnostics_2026-09-28/gpt-6-luna.jsonl` · SHA-256 `81245589318da27e07863db653a5d7a35be514df99c9f509affdd85eca3302b3` · ativações UTC: 2026-09-29T00:32:06.398714Z.
- `gpt-5.6-terra` · run `1727002e-8af1-46ae-92bc-d90faaf181b5` · categoria `arguments_json_invalid` em `2026-09-28T20:09:01.325548Z` · linha 2 · distância do error: 0.001022s.

**Interrupção solicitada pelo usuário:** `gpt-6-luna`, `case_007`, repetição 3; prefixo `b35ed940-14e8-41ea-b937-5011e3d5ca74` preservado sem evento run_ended. Não é erro de provider e não entra nas trajetórias terminais nem em encerradas=terminal+erro. Anotação `results/extension_2026-09-28/summaries/user_stop_2026-09-28.json` (SHA-256 `5ef83ee62093c0c860779afb599d64d5bb4fa71abaaf943af217fd0b9e960cf2`); uso da última chamada desconhecido. O JSON guarda separadamente o uso/custo parcial conhecido.

## Triagem lexical por caso

Cada célula mostra `match do alvo/runs observadas (runs concluídas/runs observadas)`; previsão: 3 runs por caso. `—` significa ausência de runs terminais após o encerramento. Match não equivale à avaliação médica.

| Caso | qwen3.5:9b-mlx | qwen3:8b | llama3.1:8b | gpt-6-sol | claude-opus-5-5 | claude-sonnet-5-5 | gpt-6-luna | gpt-5.6-terra |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| case_001 | 0/3 (0/3) | 0/3 (0/3) | 0/3 (0/3) | 1/3 (3/3) | 2/3 (3/3) | 0/3 (3/3) | 0/3 (3/3) | 0/3 (3/3) |
| case_002 | 0/3 (0/3) | 0/3 (1/3) | 0/3 (0/3) | 0/3 (3/3) | 0/3 (3/3) | 0/3 (3/3) | 0/3 (3/3) | 0/3 (3/3) |
| case_003 | 0/3 (1/3) | 0/3 (3/3) | 0/3 (0/3) | 3/3 (3/3) | 3/3 (3/3) | 3/3 (3/3) | 2/3 (3/3) | 3/3 (3/3) |
| case_004 | 0/3 (0/3) | 0/3 (2/3) | 0/3 (0/3) | 0/3 (3/3) | 3/3 (3/3) | 2/3 (3/3) | 0/3 (3/3) | 0/3 (3/3) |
| case_005 | 0/3 (3/3) | 0/3 (0/3) | 0/3 (0/3) | 1/3 (3/3) | 3/3 (3/3) | 3/3 (3/3) | 1/3 (3/3) | 1/3 (3/3) |
| case_006 | 0/3 (0/3) | 0/3 (0/3) | 0/3 (0/3) | 3/3 (3/3) | 3/3 (3/3) | 3/3 (3/3) | 2/3 (3/3) | 3/3 (3/3) |
| case_007 | 0/3 (0/3) | 0/3 (1/3) | 0/3 (0/3) | 1/3 (3/3) | 1/3 (3/3) | 3/3 (3/3) | 1/2 (2/2) | 0/3 (3/3) |
| case_008 | 2/3 (2/3) | 0/3 (3/3) | 0/3 (0/3) | 3/3 (3/3) | 3/3 (3/3) | 3/3 (3/3) | — | 3/3 (3/3) |
| case_009 | 0/3 (3/3) | 0/3 (1/3) | 0/3 (0/3) | 1/3 (3/3) | 3/3 (3/3) | 3/3 (3/3) | — | 3/3 (3/3) |
| case_010 | 0/3 (0/3) | 0/3 (3/3) | 0/3 (0/3) | 1/3 (3/3) | 3/3 (3/3) | 0/3 (3/3) | — | 1/3 (3/3) |

## Uso de ferramentas e recursos

| Modelo | Labs/run | Imagens/run | Procedimentos/run | Medicações/run | Chamadas inválidas | Chamadas falhas | Tokens de saída reportados | Tokens/s local |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen3.5:9b-mlx | 1.1 | 0.5 | 0.3 | 0.1 | 3 | 3 | 27689 | 18.3 |
| qwen3:8b | 2.9 | 0.9 | 0.0 | 0.0 | 79 | 80 | 13546 | 22.2 |
| llama3.1:8b | 9.4 | 0.1 | 0.5 | 0.0 | 818 | 818 | 29667 | 25.4 |
| gpt-6-sol | 1.5 | 1.6 | 1.8 | 0.3 | 0 | 0 | 138480 | — |
| claude-opus-5-5 | 1.8 | 1.3 | 1.2 | 0.6 | 0 | 0 | 205091 | — |
| claude-sonnet-5-5 | 2.0 | 1.4 | 0.9 | 0.5 | 0 | 1 | 153113 | — |
| gpt-6-luna | 1.5 | 1.3 | 0.9 | 0.2 | 0 | 0 | 101796 | — |
| gpt-5.6-terra | 0.9 | 1.5 | 1.5 | 0.0 | 0 | 2 | 75997 | — |

| Modelo | Input reportado | Cache lido | Cache criado | Raciocínio reportado | CLI equivalente reportado USD | API equivalente calculado USD | Cobrança assinatura USD |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen3.5:9b-mlx | 874371 | — | — | — | — | — | — |
| qwen3:8b | 559641 | — | — | — | — | — | — |
| llama3.1:8b | 2594413 | — | — | — | — | — | — |
| gpt-6-sol | 6703197 | 5630592 | — | 103778 | — | 4.656128 | — |
| claude-opus-5-5 | 744 | 592596 | 1743447 | — | 18.17 | — | — |
| claude-sonnet-5-5 | 980 | 1347916 | 1442387 | — | 7.57 | — | — |
| gpt-6-luna | 4734032 | 3960320 | — | 77852 | — | 0.167872 | — |
| gpt-5.6-terra | 4929392 | 4295680 | — | 50011 | — | 3.038524 | — |

As CLIs reportam tokens de entrada/cache com semânticas distintas; não usar as colunas como medida padronizada de eficiência entre fornecedores. Custo do Claude é estimativa equivalente fornecida pela CLI, não cobrança da assinatura. Sol, Luna e Terra têm proxies API calculados separadamente; suas CLIs não reportam cobrança. `—` significa medição indisponível ou não aplicável, nunca custo zero. Recursos locais não incluem energia. A classificação clínica de ações desnecessárias, diretrizes, medicações e segurança permanece pendente.

A cota da assinatura é compartilhada com outros usos da mesma conta. Não há fórmula verificável neste projeto para converter tokens, custo API equivalente ou número de runs em percentual da cota. Esforço high, histórico reenviado a cada ação e instruções internas/overhead da CLI contribuem para uso de contexto e raciocínio; os traces não isolam integralmente essas parcelas. Medidas de cota da conta e tokens/custos do benchmark são grandezas distintas.

Intervalos entre colchetes: bootstrap descritivo por dez casos (10 mil reamostragens), mostrado somente com 3 runs por caso. O pareamento preserva as três runs dentro de cada caso.

**Limites:** equivalência diagnóstica acima é uma triagem lexical determinística, não acurácia clínica adjudicada. No caso 003, o alvo do encontro é ruptura do reservatório antes da sepse pós-operatória; a coluna publicada mantém o diagnóstico final do relato. Condutas alternativas, segurança, adequação de pedidos e concordância com diretrizes aguardam médico. Casos públicos podem ter contaminado treinamento; a ordem de execução não foi randomizada e os transportes de ferramentas diferem entre Ollama e CLIs de assinatura. No braço Sol, a instrução de não usar arquivos/web e o modo `read-only` não comprovam isolamento estrito das ferramentas internas; ver `docs/safety.md`.

Os traces completos, os gabaritos e os rubrics permitem revisão cega por caso. Não se calculou score composto nem comparação numérica direta com MIRA.


## Extensão e custo calculado

Extensão: `combined_additive_extensions_2026-09-28`. O painel base de 150 runs não foi alterado; os três braços adicionais planejavam 90 runs, com 80 observadas. A execução foi interrompida a pedido do usuário; esta análise foi encerrada com Luna parcial.
O Sonnet tem slug observado em cada resposta. Para Luna e Terra, a CLI confirma apenas modelo solicitado e inferência aceita; o slug servido não é observado.
O esforço high é solicitado e conferido nos metadados; isso não mede a quantidade interna de raciocínio. Codex CLI mudou de 0.155 no braço Sol para 0.158.0-alpha.2.1 no Luna e Terra, com mesmas flags; isso é drift de transporte/data.
No Luna e Terra, instruções closed-book e modo read-only não provam bloqueio estrito de todas as ferramentas internas da CLI. Nenhuma diferença observada pode ser atribuída exclusivamente ao modelo.

Luna: proxy de custo API calculado **USD 0.167872**, em 20/20 runs com dados avaliáveis.
Sensibilidade Luna: toda entrada não cacheada como cache-write = USD 0.187215. Fonte/tarifa e exclusões por tier longo constam no JSON.
Terra: proxy de custo API calculado **USD 3.038524**, em 30/30 runs com dados avaliáveis.
Sensibilidade Terra: toda entrada não cacheada como cache-write = USD 3.355380. Fonte/tarifa e exclusões por tier longo constam no JSON.
Sol: proxy anterior preservado e conferido contra tokens dos 30 traces base = **USD 4.656128**; sensibilidade = USD 5.192431. [Detalhes anteriores](../../summaries/SOL_COST.md).
A estimativa calculada é separada do custo equivalente reportado pela CLI; nenhuma cobrança de assinatura foi observada. Não somar tokens de raciocínio novamente aos tokens de saída.
Custos do painel cobrem somente suas trajetórias clínicas terminais; excluem preflights, pilotos e falhas operacionais. Erros do mesmo freeze preservados em incomplete/ base/extensões: 8, detalhados separadamente no JSON. Seu uso/custo é apenas o prefixo conhecido; a última chamada falha pode ter uso não reportado. Não é custo total da tentativa nem da tarefa.
Painéis parciais não imputam runs ausentes e não produzem comparação pareada global. Médias por caso podem diferir da proporção bruta quando o número de runs varia entre casos.
