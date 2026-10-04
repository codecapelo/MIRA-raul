
## Execução encerrada em04-10-2026
50/50 terminais,48 julgados e2 falhas operacionais. Revisão médica pendente. Custos: ledgerUS$1,502941443; consulta final da contaUS$1,419923378. DiferençaUS$0,083018065 ainda em investigação; não considerar reconciliação financeira concluída. Nenhuma nova execução necessária. Histórico978arquivos verificado sem divergência;50combinações únicas e manifesto de traces em reports/final_trace_manifest.json.

## Rodadas 2 e 3 concluídas — 04-10-2026
150/150 encontros terminais (50 por rodada; 5 modelos × 10 casos × 3), sem pares duplicados ou ausentes. 144 julgados e 6 sem julgamento (falha operacional/sem diagnóstico: GPT-OSS 5, GLM-4.5-Air 1), mantidos como terminais e fora do denominador do juiz. **Julgamento por LLM; revisão médica cega pendente; sem afirmação de acurácia clínica ou superioridade.** Repetições do mesmo caso não são pacientes independentes: Wilson é descritivo.

| Modelo | Run 1 | Run 2 | Run 3 | Agregado | Wilson 95% (descritivo) | Sem julgamento |
|---|---:|---:|---:|---:|---|---:|
| openai/gpt-oss-120b | 5/8 | 3/9 | 2/8 | 10/25 | 23.4%–59.3% | 5 |
| z-ai/glm-4.5-air | 7/10 | 6/9 | 6/10 | 19/29 | 47.3%–80.1% | 1 |
| z-ai/glm-5 | 7/10 | 8/10 | 5/10 | 20/30 | 48.8%–80.8% | 0 |
| qwen/qwen3.5-397b-a17b | 6/10 | 6/10 | 7/10 | 19/30 | 45.5%–78.1% | 0 |
| openai/gpt-5.2 | 7/10 | 7/10 | 9/10 | 23/30 | 59.1%–88.2% | 0 |

Custo real total (ledger = conta, três snapshots sem cache): US$ 4.274237323. Terminais por rodada: US$ 1.401886810 / 1.313640775 / 1.427001795. Projeção para 5 rodadas ≈ US$ 6.90 em terminais (estimativa, não autorização).

Intercorrências (ver [reports/runs23_incidents.md](reports/runs23_incidents.md)): timeout de rede com 13 chamadas perdidas (US$ 0,030653310 não atribuível a nenhuma individualmente, registrado em linha própria do ledger) e um HTTP 429 do Qwen/Parasail sem cobrança. Nenhum terminal foi repetido; cada chamada perdida foi refeita uma vez após reconciliação. Análise: [reports/all_runs_summary.md](reports/all_runs_summary.md), `results/all_runs.csv`, manifesto `reports/final_trace_manifest_runs123.json`. Legacy: 978 arquivos verificados, 0 divergências.
