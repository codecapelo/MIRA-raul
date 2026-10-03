# Modelos de fronteira adicionais — comparação exploratória

Painel preservado: **230** terminais. Novos braços: **48/60** terminais. Total: **278/300** planejadas; Luna anterior permanece **20/30**.

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
| gpt-6-astra | 25/30 | 100.0% | 51.9% | 56.0% | — | 35.993200 |
| gpt-6.1-sol | 23/30 | 100.0% | 50.0% | 47.8% | — | 5.431765 |

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
| case_008 | 2/3 | 0/3 | 0/3 | 3/3 | 3/3 | 3/3 | — | 3/3 | 3/3 | 2/2 |
| case_009 | 0/3 | 0/3 | 0/3 | 1/3 | 3/3 | 3/3 | — | 3/3 | 0/1 | — |
| case_010 | 0/3 | 0/3 | 0/3 | 1/3 | 3/3 | 0/3 | — | 1/3 | — | — |

## Diferenças pareadas exploratórias

Só após cada novo braço completar 10 casos × 3. Comparadores também precisam estar completos; Luna parcial é excluído. Bootstrap descritivo por caso (10 mil reamostragens), sem ajuste de multiplicidade.

Nenhum conjunto pareado de novos braços foi completado; nenhuma inferência pareada foi gerada.

## Proveniência e limites

O JSON anterior de 230 terminais teve todos os campos dos oito modelos conferidos: SHA-256 `9fa80b5a33d175a93d851a00537da3cdd3e6f43c757314f26caedcf82723f727`. Scorer e regras diagnósticas continuam evaluation-v2.
- `gpt-6-astra`: manifest `docs/protocol_astra_extension_2026-09-29.json` SHA-256 `c400a9bfe4f728b9d8aac146f694962d8b2348abb64220955eb838c6af63cd6d`; 25/30 terminais; CLI declarada `0.158.0-alpha.2.1`; acesso high verificado no manifest: `True`; proxy API 35.993200 USD em 25 runs. Fonte tarifária: https://developers.openai.com/api/docs/models/gpt-6-astra. Erros operacionais preservados: 1.
- `gpt-6.1-sol`: manifest `docs/protocol_sol61_extension_2026-09-29.json` SHA-256 `3e7e1af4aba74c096fe01c9092044b718c999f14638341c7a894d1c70ae3ae31`; 23/30 terminais; CLI declarada `0.159.1`; acesso high verificado no manifest: `True`; proxy API 5.431765 USD em 23 runs. Fonte tarifária: https://developers.openai.com/api/docs/models/gpt-6.1-sol. Erros operacionais preservados: 0.

A identidade servida pelos CLIs Codex de assinatura não é exposta; apenas modelo solicitado e inferência aceita são registrados. Esforço high é pedido. Comparações incluem transporte e data, não isolam pesos do modelo. Custo de prefixos com erro é apenas o uso conhecido; última chamada pode não ter reportado tokens. Cota da assinatura é compartilhada e não há fórmula verificável de conversão para tokens/proxy de API. Revisão médica de diagnóstico, conduta e segurança está pendente; nenhum LLM é juiz único de segurança.
