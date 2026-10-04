# Custos observados e projeção

Piloto: 0/5 episódios concluídos, um caso por modelo. Valores reais provenientes do CSV; custos conhecidos de todas as chamadas provenientes do ledger.

| Modelo | Provedor observado | Piloto real US$ | 10 casos × 1 execução US$ | 10 casos × 5 execuções US$ |
|---|---|---:|---:|---:|
| openai/gpt-oss-120b | pendente | pendente | pendente | pendente |
| z-ai/glm-4.5-air | pendente | pendente | pendente | pendente |
| z-ai/glm-5 | pendente | pendente | pendente | pendente |
| qwen/qwen3.5-397b-a17b | pendente | pendente | pendente | pendente |
| openai/gpt-5.2 | pendente | pendente | pendente | pendente |

Custo total conhecido, incluindo tentativas arquivadas/incompletas: US$ 0.101054633. Total dos episódios completos: US$ 0.

| Ator | Chamadas | Custo conhecido US$ | Chamadas sem custo resolvido |
|---|---:|---:|---:|
| doctor | 59 | 0.074062954 | 0 |
| judge | 5 | 0.00175000 | 0 |
| matcher | 31 | 0.007396200 | 0 |
| patient | 21 | 0.017845479 | 0 |

Chamadas não liquidadas: 0; detalhes e reservas no JSON. Logs atuais e logs/incomplete são agregados por request_id, sem duplicar chamadas presentes nos dois locais.

Projeção linear baseada somente no caso 001, incluindo médico, paciente, juiz e matcher quando usados. Casos mais complexos e alterações de preço/provedor modificam o custo. Projeções futuras não incorporam novamente custos históricos de tentativas incompletas e não autorizam novas execuções. Provedor observado vem do CSV de cada episódio.
