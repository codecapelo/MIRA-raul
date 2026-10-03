# Análise exploratória — painel MIRA-2026

Corpus: `mvp10_v3_2026-09-26` · Protocolo: `mvp10_closedbook_v5_2026-09-26`.

Avaliação: `evaluation-v2` · Regras diagnósticas: `diagnostic-concepts-2026-09-26-v2` (SHA-256 `b2da153cd8d65df6658f45e715b0287cc4956a040bf62fbb8ddeb09d261df9fc`).

Trajetórias terminais: **150/150**. Revisão médica: **pendente**.

| Modelo | Runs | Conclusão | Alvo do encontro, média por caso | Diagnóstico publicado, média por caso | Top-3 alvo, média por caso | Chamadas | Mediana duração |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen3.5:9b-mlx | 30/30 | 30.0% [6.7, 56.7] | 6.7% [0.0, 20.0] | 6.7% [0.0, 20.0] | 6.7% [0.0, 20.0] | 335 | 54.6 s |
| qwen3:8b | 30/30 | 46.7% [23.3, 73.3] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 256 | 25.4 s |
| llama3.1:8b | 30/30 | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 930 | 63.2 s |
| gpt-6-sol | 30/30 | 100.0% [100.0, 100.0] | 46.7% [23.3, 70.0] | 40.0% [20.0, 60.0] | 46.7% [23.3, 70.0] | 401 | 170.4 s |
| claude-opus-5-5 | 30/30 | 100.0% [100.0, 100.0] | 80.0% [56.7, 100.0] | 80.0% [56.7, 100.0] | 80.0% [56.7, 100.0] | 367 | 85.6 s |

Ausência de diagnóstico final **aceito pelo EHR** conta como erro nas três colunas diagnósticas acima. Cada caso recebe o mesmo peso; no painel completo de três runs por caso, a média por caso equivale à proporção das 30 runs. Os valores são triagens lexicais, não acurácia clínica adjudicada.

| Modelo | Diagnósticos aceitos pelo EHR | Match do alvo entre aceitos |
|---|---:|---:|
| qwen3.5:9b-mlx | 9/30 | 22.2% |
| qwen3:8b | 14/30 | 0.0% |
| llama3.1:8b | 0/30 | — |
| gpt-6-sol | 30/30 | 46.7% |
| claude-opus-5-5 | 30/30 | 80.0% |

## Triagem lexical por caso

Cada célula mostra `match do alvo/3 (runs concluídas/3)`. Match não equivale à avaliação médica.

| Caso | qwen3.5:9b-mlx | qwen3:8b | llama3.1:8b | gpt-6-sol | claude-opus-5-5 |
|---|---:|---:|---:|---:|---:|
| case_001 | 0/3 (0/3) | 0/3 (0/3) | 0/3 (0/3) | 1/3 (3/3) | 2/3 (3/3) |
| case_002 | 0/3 (0/3) | 0/3 (1/3) | 0/3 (0/3) | 0/3 (3/3) | 0/3 (3/3) |
| case_003 | 0/3 (1/3) | 0/3 (3/3) | 0/3 (0/3) | 3/3 (3/3) | 3/3 (3/3) |
| case_004 | 0/3 (0/3) | 0/3 (2/3) | 0/3 (0/3) | 0/3 (3/3) | 3/3 (3/3) |
| case_005 | 0/3 (3/3) | 0/3 (0/3) | 0/3 (0/3) | 1/3 (3/3) | 3/3 (3/3) |
| case_006 | 0/3 (0/3) | 0/3 (0/3) | 0/3 (0/3) | 3/3 (3/3) | 3/3 (3/3) |
| case_007 | 0/3 (0/3) | 0/3 (1/3) | 0/3 (0/3) | 1/3 (3/3) | 1/3 (3/3) |
| case_008 | 2/3 (2/3) | 0/3 (3/3) | 0/3 (0/3) | 3/3 (3/3) | 3/3 (3/3) |
| case_009 | 0/3 (3/3) | 0/3 (1/3) | 0/3 (0/3) | 1/3 (3/3) | 3/3 (3/3) |
| case_010 | 0/3 (0/3) | 0/3 (3/3) | 0/3 (0/3) | 1/3 (3/3) | 3/3 (3/3) |

## Uso de ferramentas e recursos

| Modelo | Labs/run | Imagens/run | Procedimentos/run | Medicações/run | Chamadas inválidas | Chamadas falhas | Tokens de saída reportados | Tokens/s local |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen3.5:9b-mlx | 1.1 | 0.5 | 0.3 | 0.1 | 3 | 3 | 27689 | 18.3 |
| qwen3:8b | 2.9 | 0.9 | 0.0 | 0.0 | 79 | 80 | 13546 | 22.2 |
| llama3.1:8b | 9.4 | 0.1 | 0.5 | 0.0 | 818 | 818 | 29667 | 25.4 |
| gpt-6-sol | 1.5 | 1.6 | 1.8 | 0.3 | 0 | 0 | 138480 | — |
| claude-opus-5-5 | 1.8 | 1.3 | 1.2 | 0.6 | 0 | 0 | 205091 | — |

| Modelo | Input reportado | Cache lido | Cache criado | Raciocínio reportado | Custo equivalente USD |
|---|---:|---:|---:|---:|---:|
| qwen3.5:9b-mlx | 874371 | — | — | — | 0.00 |
| qwen3:8b | 559641 | — | — | — | 0.00 |
| llama3.1:8b | 2594413 | — | — | — | 0.00 |
| gpt-6-sol | 6703197 | 5630592 | — | 103778 | 4.66* |
| claude-opus-5-5 | 744 | 592596 | 1743447 | — | 18.17 |

As CLIs reportam tokens de entrada/cache com semânticas distintas; não usar as colunas como medida padronizada de eficiência entre fornecedores. Custo do Claude é estimativa equivalente fornecida pela CLI, não cobrança da assinatura. O Sol não reporta custo; `4.66*` é proxy API Standard calculada dos tokens, não cobrança da assinatura. Recursos locais não incluem energia. A classificação clínica de ações desnecessárias, diretrizes, medicações e segurança permanece pendente.

Intervalos entre colchetes: bootstrap descritivo por dez casos (10 mil reamostragens), mostrado somente com 3 runs por caso. O pareamento preserva as três runs dentro de cada caso.

**Limites:** equivalência diagnóstica acima é uma triagem lexical determinística, não acurácia clínica adjudicada. No caso 003, o alvo do encontro é ruptura do reservatório antes da sepse pós-operatória; a coluna publicada mantém o diagnóstico final do relato. Condutas alternativas, segurança, adequação de pedidos e concordância com diretrizes aguardam médico. Casos públicos podem ter contaminado treinamento; a ordem de execução não foi randomizada e os transportes de ferramentas diferem entre Ollama e CLIs de assinatura. No braço Sol, a instrução de não usar arquivos/web e o modo `read-only` não comprovam isolamento estrito das ferramentas internas; ver `docs/safety.md`.

Os traces completos, os gabaritos e os rubrics permitem revisão cega por caso. Não se calculou score composto nem comparação numérica direta com MIRA.
## Custo estimado do GPT-6 Sol — análise posterior

**US$ 4.66** para 30 runs (sensibilidade **US$ 4.66–5.19**; cobrança real pela assinatura: indisponível). Fórmula, tarifas oficiais e limites em [SOL_COST.md](SOL_COST.md).
