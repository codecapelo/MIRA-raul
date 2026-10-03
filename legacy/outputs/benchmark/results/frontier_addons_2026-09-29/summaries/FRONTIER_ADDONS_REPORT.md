# Modelos de fronteira adicionais — comparação exploratória

Painel preservado: **230** terminais. Novos braços: **60/60** terminais. Total: **290/300** planejadas; Luna anterior permanece **20/30**.

| Modelo | Terminais | Conclusão entre terminais | Alvo, média por caso | Alvo bruto observado | CLI equivalente USD | Proxy API USD |
|---|---:|---:|---:|---:|---:|---:|
| qwen3.5:9b-mlx | 30/30 | 30.0% | 6.7% | 6.7% | — | — |
| qwen3:8b | 30/30 | 46.7% | 0.0% | 0.0% | — | — |
| llama3.1:8b | 30/30 | 0.0% | 0.0% | 0.0% | — | — |
| gpt-6-sol | 30/30 | 100.0% | 46.7% | 46.7% | — | 4.656128 |
| claude-opus-5-5 | 30/30 | 100.0% | 80.0% | 80.0% | 18.170891 | — |
| claude-sonnet-5-5 | 30/30 | 100.0% | 66.7% | 66.7% | 7.572221 | — |
| gpt-6-luna | 20/30 | 100.0% | 31.0% | 30.0% | — | 0.167872 |
| gpt-5.6-terra | 30/30 | 100.0% | 46.7% | 46.7% | — | 3.038524 |
| gpt-6-astra | 30/30 | 100.0% | 50.0% | 50.0% | — | 43.229340 |
| gpt-6.1-sol | 30/30 | 100.0% | 56.7% | 56.7% | — | 7.003420 |

As células Luna faltantes não são imputadas. Os matches são triagem lexical determinística, não acurácia clínica adjudicada. Custos API são proxies hipotéticos separados de estimativas CLI e da cobrança desconhecida da assinatura. Não somar raciocínio à saída novamente. Os casos públicos podem ter contaminado treino.

## Casos

Célula = match do alvo/runs terminais observadas; `—` = ausência, sem imputação.

| Caso | qwen3.5:9b-mlx | qwen3:8b | llama3.1:8b | gpt-6-sol | claude-opus-5-5 | claude-sonnet-5-5 | gpt-6-luna | gpt-5.6-terra | gpt-6-astra | gpt-6.1-sol |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| case_001 | 0/3 | 0/3 | 0/3 | 1/3 | 2/3 | 0/3 | 0/3 | 0/3 | 1/3 | 0/3 |
| case_002 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |
| case_003 | 0/3 | 0/3 | 0/3 | 3/3 | 3/3 | 3/3 | 2/3 | 3/3 | 3/3 | 3/3 |
| case_004 | 0/3 | 0/3 | 0/3 | 0/3 | 3/3 | 2/3 | 0/3 | 0/3 | 0/3 | 1/3 |
| case_005 | 0/3 | 0/3 | 0/3 | 1/3 | 3/3 | 3/3 | 1/3 | 1/3 | 3/3 | 2/3 |
| case_006 | 0/3 | 0/3 | 0/3 | 3/3 | 3/3 | 3/3 | 2/3 | 3/3 | 3/3 | 3/3 |
| case_007 | 0/3 | 0/3 | 0/3 | 1/3 | 1/3 | 3/3 | 1/2 | 0/3 | 1/3 | 0/3 |
| case_008 | 2/3 | 0/3 | 0/3 | 3/3 | 3/3 | 3/3 | — | 3/3 | 3/3 | 3/3 |
| case_009 | 0/3 | 0/3 | 0/3 | 1/3 | 3/3 | 3/3 | — | 3/3 | 1/3 | 3/3 |
| case_010 | 0/3 | 0/3 | 0/3 | 1/3 | 3/3 | 0/3 | — | 1/3 | 0/3 | 2/3 |

## Diferenças pareadas exploratórias

Só após cada novo braço completar 10 casos × 3. Comparadores também precisam estar completos; Luna parcial é excluído. Bootstrap descritivo por caso (10 mil reamostragens), sem ajuste de multiplicidade.

| Comparação | Diferença média | IC bootstrap 95% |
|---|---:|---:|
| completed: gpt-6-astra minus qwen3.5:9b-mlx | 70.0 pp | [43.3, 93.3] pp |
| completed: gpt-6-astra minus qwen3:8b | 53.3 pp | [26.7, 76.7] pp |
| completed: gpt-6-astra minus llama3.1:8b | 100.0 pp | [100.0, 100.0] pp |
| completed: gpt-6-astra minus gpt-6-sol | 0.0 pp | [0.0, 0.0] pp |
| completed: gpt-6-astra minus claude-opus-5-5 | 0.0 pp | [0.0, 0.0] pp |
| completed: gpt-6-astra minus claude-sonnet-5-5 | 0.0 pp | [0.0, 0.0] pp |
| completed: gpt-6-astra minus gpt-5.6-terra | 0.0 pp | [0.0, 0.0] pp |
| completed: gpt-6.1-sol minus qwen3.5:9b-mlx | 70.0 pp | [43.3, 93.3] pp |
| completed: gpt-6.1-sol minus qwen3:8b | 53.3 pp | [26.7, 76.7] pp |
| completed: gpt-6.1-sol minus llama3.1:8b | 100.0 pp | [100.0, 100.0] pp |
| completed: gpt-6.1-sol minus gpt-6-sol | 0.0 pp | [0.0, 0.0] pp |
| completed: gpt-6.1-sol minus claude-opus-5-5 | 0.0 pp | [0.0, 0.0] pp |
| completed: gpt-6.1-sol minus claude-sonnet-5-5 | 0.0 pp | [0.0, 0.0] pp |
| completed: gpt-6.1-sol minus gpt-5.6-terra | 0.0 pp | [0.0, 0.0] pp |
| completed: gpt-6.1-sol minus gpt-6-astra | 0.0 pp | [0.0, 0.0] pp |
| benchmark_target_concept_match: gpt-6-astra minus qwen3.5:9b-mlx | 43.3 pp | [20.0, 66.7] pp |
| benchmark_target_concept_match: gpt-6-astra minus qwen3:8b | 50.0 pp | [23.3, 76.7] pp |
| benchmark_target_concept_match: gpt-6-astra minus llama3.1:8b | 50.0 pp | [23.3, 76.7] pp |
| benchmark_target_concept_match: gpt-6-astra minus gpt-6-sol | 3.3 pp | [-10.0, 20.0] pp |
| benchmark_target_concept_match: gpt-6-astra minus claude-opus-5-5 | -30.0 pp | [-56.7, -6.7] pp |
| benchmark_target_concept_match: gpt-6-astra minus claude-sonnet-5-5 | -16.7 pp | [-40.0, 3.3] pp |
| benchmark_target_concept_match: gpt-6-astra minus gpt-5.6-terra | 3.3 pp | [-20.0, 23.3] pp |
| benchmark_target_concept_match: gpt-6.1-sol minus qwen3.5:9b-mlx | 50.0 pp | [26.7, 73.3] pp |
| benchmark_target_concept_match: gpt-6.1-sol minus qwen3:8b | 56.7 pp | [30.0, 83.3] pp |
| benchmark_target_concept_match: gpt-6.1-sol minus llama3.1:8b | 56.7 pp | [30.0, 83.3] pp |
| benchmark_target_concept_match: gpt-6.1-sol minus gpt-6-sol | 10.0 pp | [-10.0, 30.0] pp |
| benchmark_target_concept_match: gpt-6.1-sol minus claude-opus-5-5 | -23.3 pp | [-40.0, -6.7] pp |
| benchmark_target_concept_match: gpt-6.1-sol minus claude-sonnet-5-5 | -10.0 pp | [-36.7, 13.3] pp |
| benchmark_target_concept_match: gpt-6.1-sol minus gpt-5.6-terra | 10.0 pp | [0.0, 20.0] pp |
| benchmark_target_concept_match: gpt-6.1-sol minus gpt-6-astra | 6.7 pp | [-13.3, 30.0] pp |

## Proveniência e limites

O JSON anterior de 230 terminais teve todos os campos dos oito modelos conferidos: SHA-256 `9fa80b5a33d175a93d851a00537da3cdd3e6f43c757314f26caedcf82723f727`. Scorer e regras diagnósticas continuam evaluation-v2.
- `gpt-6-astra`: manifest `docs/protocol_astra_extension_2026-09-29.json` SHA-256 `c400a9bfe4f728b9d8aac146f694962d8b2348abb64220955eb838c6af63cd6d`; 30/30 terminais; CLI declarada `0.158.0-alpha.2.1`; acesso high verificado no manifest: `True`; proxy API 43.229340 USD em 30 runs. Fonte tarifária: https://developers.openai.com/api/docs/models/gpt-6-astra. Erros operacionais preservados: 1.
- `gpt-6.1-sol`: manifest `docs/protocol_sol61_extension_2026-09-29.json` SHA-256 `3e7e1af4aba74c096fe01c9092044b718c999f14638341c7a894d1c70ae3ae31`; 30/30 terminais; CLI declarada `0.159.1`; acesso high verificado no manifest: `True`; proxy API 7.003420 USD em 30 runs. Fonte tarifária: https://developers.openai.com/api/docs/models/gpt-6.1-sol. Erros operacionais preservados: 0.

A identidade servida pelos CLIs Codex de assinatura não é exposta; apenas modelo solicitado e inferência aceita são registrados. Esforço high é pedido. Comparações incluem transporte e data, não isolam pesos do modelo. Custo de prefixos com erro é apenas o uso conhecido; última chamada pode não ter reportado tokens. Cota da assinatura é compartilhada e não há fórmula verificável de conversão para tokens/proxy de API. Revisão médica de diagnóstico, conduta e segurança está pendente; nenhum LLM é juiz único de segurança.
