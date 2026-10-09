# Custos observados e projeção

Piloto: 5/5 tentativas terminais, um caso por modelo, inclusive falhas operacionais. Valores reais provenientes do CSV; custos conhecidos de todas as chamadas provenientes do ledger.

| Modelo | Provedor observado | Piloto real US$ | 10 casos × 1 execução US$ | 10 casos × 5 execuções US$ |
|---|---|---:|---:|---:|
| openai/gpt-oss-120b | mancer/fp8 | 0.000108 | 0.001075 | 0.005375 |
| z-ai/glm-4.5-air | novita/bf16 | 0.004952 | 0.049525 | 0.247624 |
| z-ai/glm-5 | streamlake/fp8 | 0.010986 | 0.109862 | 0.549310 |
| qwen/qwen3.5-397b-a17b | parasail/fp8 | 0.027347 | 0.273466 | 1.367328 |
| openai/gpt-5.2 | openai | 0.070474 | 0.704737 | 3.523683 |

Custo total conhecido, incluindo tentativas arquivadas/incompletas: US$ 1.502941443. Total das tentativas terminais: US$ 1.401886810.

| Ator | Chamadas | Custo conhecido US$ | Chamadas sem custo resolvido |
|---|---:|---:|---:|
| doctor | 549 | 1.029856654 | 0 |
| judge | 53 | 0.01655150 | 0 |
| matcher | 354 | 0.026940900 | 0 |
| patient | 178 | 0.429592389 | 0 |

Chamadas não liquidadas: 0; detalhes e reservas no JSON. Logs atuais e logs/incomplete são agregados por request_id, sem duplicar chamadas presentes nos dois locais.

Projeção linear baseada nas cinco tentativas terminais do caso 001, incluindo falhas sem diagnóstico; não exige cinco diagnósticos nem representa custo de sucesso clínico. Inclui médico, paciente, juiz e matcher quando usados. Casos mais complexos e alterações de preço/provedor modificam o custo. Projeções futuras não incorporam novamente custos históricos de tentativas incompletas e não autorizam novas execuções. Provedor observado vem do CSV de cada episódio.

## Atualização após runs 2 e 3

Custo real total US$ 4.274237323 (ledger = conta). Detalhes e projeção para 5 rodadas em [all_runs_cost_projection.md](all_runs_cost_projection.md). Esta seção substitui o gasto parcial citado acima; a projeção linear do piloto acima permanece como histórico.

## Atualização após extensão Qwen3.8

Custo real total US$ 8.356544873 (ledger = conta). A projeção para 5 repetições em [all_runs_cost_projection.md](all_runs_cost_projection.md) agora cobre 7 modelos.

## v4 — projeção a partir de encontros completos
Nova condição:10encontros, API todosatoresUS$0.11515425, médiaUS$0.011515425; projeção linear50encontrosUS$0.57577125. Apenas estimativa de API, sem autorização de novos testes, sem assinatura e sem dólares de exames. Histórico original/APIoffline adicional e falhas permanecem no globalUS$0.28396075, cap5/restanteUS$4.71603925. Não representa custo por sucesso clínico. Comparação descritivaClaudev3.6públicosUS$0.35023969 versus novaAPIUS$0.11515425; modelos/transporte/custos assinatura diferem. Fonte: v4_final_summary.json.
