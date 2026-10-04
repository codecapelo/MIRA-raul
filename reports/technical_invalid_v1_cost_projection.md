# Custos observados e projeção

Piloto: 5/5 episódios concluídos, um caso por modelo. Valores reais provenientes do CSV; custos conhecidos de todas as chamadas provenientes do ledger.

| Modelo | Provedor observado | Piloto real US$ | 10 casos × 1 execução US$ | 10 casos × 5 execuções US$ |
|---|---|---:|---:|---:|
| openai/gpt-oss-120b | mancer/fp8 | 0.009107 | 0.091074 | 0.455368 |
| z-ai/glm-4.5-air | novita/bf16 | 0.002339 | 0.023390 | 0.116950 |
| z-ai/glm-5 | streamlake/fp8 | 0.008630 | 0.086300 | 0.431500 |
| qwen/qwen3.5-397b-a17b | parasail/fp8 | 0.020238 | 0.202383 | 1.011916 |
| openai/gpt-5.2 | openai | 0.049849 | 0.498488 | 2.492440 |

Custo total conhecido, incluindo tentativas arquivadas/incompletas: US$ 0.100672133. Total dos episódios completos: US$ 0.090163470.

| Ator | Chamadas | Custo conhecido US$ | Chamadas sem custo resolvido |
|---|---:|---:|---:|
| doctor | 59 | 0.073680454 | 1 |
| judge | 5 | 0.00175000 | 0 |
| matcher | 31 | 0.007396200 | 0 |
| patient | 21 | 0.017845479 | 0 |

Chamadas não liquidadas: 1; detalhes e reservas no JSON. Logs atuais e logs/incomplete são agregados por request_id, sem duplicar chamadas presentes nos dois locais.

Projeção linear baseada somente no caso 001, incluindo médico, paciente, juiz e matcher quando usados. Casos mais complexos e alterações de preço/provedor modificam o custo. Projeções futuras não incorporam novamente custos históricos de tentativas incompletas e não autorizam novas execuções. Provedor observado vem do CSV de cada episódio.
