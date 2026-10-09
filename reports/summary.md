# Run1: julgamento LLM, revisão médica pendente

Tentativas terminais 50/50, incluindo 2 falhas operacionais; julgamentos clínicos válidos: 48. Ausências explicitadas no JSON.

| Modelo | Tentativas terminais | Falhas operacionais | Corretos/julgados | Wilson 95% |
|---|---:|---:|---:|---|
| openai/gpt-oss-120b | 10/10 | 2 | 5/8 | 30.6%–86.3% |
| z-ai/glm-4.5-air | 10/10 | 0 | 7/10 | 39.7%–89.2% |
| z-ai/glm-5 | 10/10 | 0 | 7/10 | 39.7%–89.2% |
| qwen/qwen3.5-397b-a17b | 10/10 | 0 | 6/10 | 31.3%–83.2% |
| openai/gpt-5.2 | 10/10 | 0 | 7/10 | 39.7%–89.2% |

Custo conhecido ledger: US$ 1.502941443; CSV terminal: US$ 1.401886810. Custos de tentativas incompletas aparecem no detalhamento por ator. Chamadas não liquidadas impedem presumir total final.

Mediana/IQR de tokens e latência, intervalos por categoria e pares ausentes estão no JSON. Tokens de raciocínio são subconjunto da conclusão; não somar novamente. Grupos clínicos descritivos possuem denominadores pequenos.

O juiz LLM avalia equivalência diagnóstica. A análise antiga é lexical, com outros modelos, transporte, ferramentas e três repetições. Não há comparação de superioridade clínica. Revisão médica cega pendente. Repetições não são pacientes independentes.

Histórico imutável: 290/300 trajetórias, métricas originais de todos os modelos preservadas no JSON. Fonte `/Users/test/MIRA-RAUL/legacy/outputs/benchmark/results/frontier_addons_2026-09-29/summaries/frontier_addons_analysis.json`, SHA-256 `023eeb5127236fd413d85bb039af4bb1acc70ca599c1bacc3c28265d45181c79`.

## Custo e consumo por modelo

Custos por modelo abaixo somam tentativas terminais, inclusive falhas operacionais, incluindo todos os atores. O custo global por ator inclui também tentativas incompletas; por isso pode exceder esta soma.

| Modelo | Episódios | Custo total US$ | Custo médio US$ | Tokens totais mediana [Q1; Q3] | Prompt mediana [Q1; Q3] | Conclusão mediana [Q1; Q3] | Raciocínio mediana [Q1; Q3] |
|---|---:|---:|---:|---|---|---|---|
| openai/gpt-oss-120b | 10 | 0.085939 | 0.008594 | 134,122 [73,970; 167,224] | 120,234 [63,369; 148,611] | 12,163 [10,320; 18,544] | 2,546 [2,015; 3,033] |
| z-ai/glm-4.5-air | 10 | 0.036398 | 0.003640 | 21,368 [17,624; 30,703] | 18,306 [14,437; 27,434] | 3,062 [2,628; 3,594] | 1,913 [1,596; 2,260] |
| z-ai/glm-5 | 10 | 0.141193 | 0.014119 | 26,884 [18,234; 35,903] | 21,386 [14,332; 29,590] | 5,211 [3,827; 6,050] | 2,740 [2,210; 3,470] |
| qwen/qwen3.5-397b-a17b | 10 | 0.412584 | 0.041258 | 33,560 [24,733; 37,882] | 19,942 [17,295; 29,603] | 8,662 [6,790; 10,958] | 6,626 [5,107; 8,860] |
| openai/gpt-5.2 | 10 | 0.725774 | 0.072577 | 25,346 [17,264; 32,130] | 21,172 [14,519; 27,852] | 3,890 [3,348; 4,577] | 2,184 [1,578; 2,324] |

## Categorias e casos

Falhas operacionais são tentativas terminais, sem diagnóstico/julgamento; não viram decisão falsa do juiz. Cada linha tem seu próprio denominador; Wilson é calculado sobre julgamentos válidos. Categorias amplas foram atribuídas manualmente e não correspondem aos estratos do artigo.

| Modelo | Categoria | Tentativas | Corretos/julgados | Wilson 95% |
|---|---|---:|---:|---|
| openai/gpt-oss-120b | cardiovascular | 2 | 0/1 | 0.0%–79.3% |
| openai/gpt-oss-120b | endocrine_infectious | 1 | 0/1 | 0.0%–79.3% |
| openai/gpt-oss-120b | gastrointestinal | 1 | 0/0 | indisponível |
| openai/gpt-oss-120b | hematology | 1 | 1/1 | 20.7%–100.0% |
| openai/gpt-oss-120b | neurologic | 1 | 1/1 | 20.7%–100.0% |
| openai/gpt-oss-120b | obstetric | 1 | 0/1 | 0.0%–79.3% |
| openai/gpt-oss-120b | respiratory_oncology | 2 | 2/2 | 34.2%–100.0% |
| openai/gpt-oss-120b | urologic | 1 | 1/1 | 20.7%–100.0% |
| z-ai/glm-4.5-air | cardiovascular | 2 | 1/2 | 9.5%–90.5% |
| z-ai/glm-4.5-air | endocrine_infectious | 1 | 1/1 | 20.7%–100.0% |
| z-ai/glm-4.5-air | gastrointestinal | 1 | 1/1 | 20.7%–100.0% |
| z-ai/glm-4.5-air | hematology | 1 | 1/1 | 20.7%–100.0% |
| z-ai/glm-4.5-air | neurologic | 1 | 1/1 | 20.7%–100.0% |
| z-ai/glm-4.5-air | obstetric | 1 | 0/1 | 0.0%–79.3% |
| z-ai/glm-4.5-air | respiratory_oncology | 2 | 1/2 | 9.5%–90.5% |
| z-ai/glm-4.5-air | urologic | 1 | 1/1 | 20.7%–100.0% |
| z-ai/glm-5 | cardiovascular | 2 | 0/2 | 0.0%–65.8% |
| z-ai/glm-5 | endocrine_infectious | 1 | 1/1 | 20.7%–100.0% |
| z-ai/glm-5 | gastrointestinal | 1 | 0/1 | 0.0%–79.3% |
| z-ai/glm-5 | hematology | 1 | 1/1 | 20.7%–100.0% |
| z-ai/glm-5 | neurologic | 1 | 1/1 | 20.7%–100.0% |
| z-ai/glm-5 | obstetric | 1 | 1/1 | 20.7%–100.0% |
| z-ai/glm-5 | respiratory_oncology | 2 | 2/2 | 34.2%–100.0% |
| z-ai/glm-5 | urologic | 1 | 1/1 | 20.7%–100.0% |
| qwen/qwen3.5-397b-a17b | cardiovascular | 2 | 1/2 | 9.5%–90.5% |
| qwen/qwen3.5-397b-a17b | endocrine_infectious | 1 | 1/1 | 20.7%–100.0% |
| qwen/qwen3.5-397b-a17b | gastrointestinal | 1 | 0/1 | 0.0%–79.3% |
| qwen/qwen3.5-397b-a17b | hematology | 1 | 1/1 | 20.7%–100.0% |
| qwen/qwen3.5-397b-a17b | neurologic | 1 | 1/1 | 20.7%–100.0% |
| qwen/qwen3.5-397b-a17b | obstetric | 1 | 0/1 | 0.0%–79.3% |
| qwen/qwen3.5-397b-a17b | respiratory_oncology | 2 | 1/2 | 9.5%–90.5% |
| qwen/qwen3.5-397b-a17b | urologic | 1 | 1/1 | 20.7%–100.0% |
| openai/gpt-5.2 | cardiovascular | 2 | 1/2 | 9.5%–90.5% |
| openai/gpt-5.2 | endocrine_infectious | 1 | 1/1 | 20.7%–100.0% |
| openai/gpt-5.2 | gastrointestinal | 1 | 0/1 | 0.0%–79.3% |
| openai/gpt-5.2 | hematology | 1 | 1/1 | 20.7%–100.0% |
| openai/gpt-5.2 | neurologic | 1 | 1/1 | 20.7%–100.0% |
| openai/gpt-5.2 | obstetric | 1 | 0/1 | 0.0%–79.3% |
| openai/gpt-5.2 | respiratory_oncology | 2 | 2/2 | 34.2%–100.0% |
| openai/gpt-5.2 | urologic | 1 | 1/1 | 20.7%–100.0% |

| Caso | Categoria | Tentativas | Corretos/julgados entre modelos | Wilson 95% |
|---|---|---:|---:|---|
| case_001 | cardiovascular | 5/5 | 1/4 | 4.6%–69.9% |
| case_002 | cardiovascular | 5/5 | 2/5 | 11.8%–76.9% |
| case_003 | urologic | 5/5 | 5/5 | 56.6%–100.0% |
| case_004 | respiratory_oncology | 5/5 | 4/5 | 37.6%–96.4% |
| case_005 | respiratory_oncology | 5/5 | 4/5 | 37.6%–96.4% |
| case_006 | endocrine_infectious | 5/5 | 4/5 | 37.6%–96.4% |
| case_007 | hematology | 5/5 | 5/5 | 56.6%–100.0% |
| case_008 | neurologic | 5/5 | 5/5 | 56.6%–100.0% |
| case_009 | gastrointestinal | 5/5 | 1/4 | 4.6%–69.9% |
| case_010 | obstetric | 5/5 | 1/5 | 3.6%–62.4% |

Os intervalos por caso agrupam cinco configurações diferentes, sendo apenas descritivos; os modelos compartilham o mesmo caso e não são cinco pacientes independentes.

## Comparação histórica lexical

| Modelo histórico | Trajetórias observadas/previstas | Conceitos publicados encontrados/observados | Média lexical por caso |
|---|---:|---:|---:|
| qwen3.5:9b-mlx | 30/30 | 2/30 | 6.7% |
| qwen3:8b | 30/30 | 0/30 | 0.0% |
| llama3.1:8b | 30/30 | 0/30 | 0.0% |
| gpt-6-sol | 30/30 | 14/30 | 40.0% |
| claude-opus-5-5 | 30/30 | 24/30 | 80.0% |
| claude-sonnet-5-5 | 30/30 | 20/30 | 66.7% |
| gpt-6-luna | 20/30 | 6/20 | 26.2% |
| gpt-5.6-terra | 30/30 | 14/30 | 36.7% |
| gpt-6-astra | 30/30 | 15/30 | 46.7% |
| gpt-6.1-sol | 30/30 | 17/30 | 53.3% |

Valores históricos são transcritos do relatório congelado, sem reexecução do avaliador lexical. Média por caso e proporção por trajetória podem diferir com repetições ausentes. Juiz LLM e correspondência lexical são medidas distintas: não inferir superioridade ou acurácia clínica.

## Fidelidade do paciente simulado

**Falha documentada em GPT-OSS/case_001:** o paciente inventou características de dor, horário/intensidade, frequência de diálise e negativa de alergia; o médico usou elementos inventados na justificativa de STEMI. Zero erros de ferramenta não garante fidelidade narrativa. O erro e seu custo foram preservados; não foi excluído nem reexecutado.

A conclusão deste episódio reflete contaminação da narrativa simulada e extrapolação do médico. A fidelidade dos demais modelos requer análise própria. Evidência detalhada: [patient_fidelity_case001_gptoss.md](patient_fidelity_case001_gptoss.md). Revisão documental; revisão médica assinada pendente.

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

## Extensão Qwen3.8 concluída — 04-10-2026
`qwen/qwen3.8-max-prime` (26/30 pelo juiz, US$ 2,7619) e `qwen/qwen3.8-max-0902` (24/30, US$ 1,3204): 10 casos × 3 repetições cada, rota Alibaba única, mesmo protocolo e juiz, sem falhas. Total agora 210 encontros terminais (204 julgados, 6 sem julgamento). Gasto real US$ 8.356544873 = ledger = conta (snapshots sem cache `reports/credits_qwen38_*final_*.json`); restam cerca de US$ 9,64 do teto de US$ 18, sem nova execução autorizada. Os dois modelos quase não conversaram com o paciente (23% e 7% dos encontros) e pediram achados cirúrgicos/histopatológicos finais em 60% e 53%: parte do resultado reflete a compressão temporal do protocolo. Parâmetros de amostragem assumidos iguais aos do Qwen3.5. Revisão médica pendente; sem afirmação de superioridade. Detalhes em [reports/extension_qwen38.md](reports/extension_qwen38.md); análise combinada em [reports/all_runs_summary.md](reports/all_runs_summary.md).

## Resultado do Sonnet 5.5 pela assinatura — 04-10-2026
10/10 terminais, 9 corretos pelo juiz (8/10 sob leitura rigorosa do caso 009), 0 sem julgamento, conversa com o paciente em 6 de 10 encontros. Consumo: 62 chamadas ao CLI, 408 mil tokens de entrada (407,8 mil em cache), 41,3 mil de saída, cerca de 6 minutos, custo equivalente de API US$ 1,19; gasto no OpenRouter US$ 0,0063 (associador e juiz), conta = ledger = US$ 8,362879588. Percentual consumido do limite do plano Pro não é legível pelo CLI (conferir no medidor da conta). Braço não equivalente aos demais (ferramentas em JSON, sem controle de amostragem). Detalhes em [reports/claude_sonnet_5_5_subscription_run1.md](reports/claude_sonnet_5_5_subscription_run1.md). Opus 5.5 aguardando decisão do usuário.

## Resultado do Opus 5.5 pela assinatura — 05-10-2026
`claude-opus-5-5` em high, mesmo braço de assinatura do Sonnet (ferramentas emuladas em JSON, não equivalente aos demais): 10/10 terminais, **10 corretos pelo juiz** (7 a 8 de 10 sob leitura rigorosa: 007 sem o fármaco, 002 sem miocardite, 009 sem Meckel), 0 sem julgamento, conversa com o paciente em 6 de 10 encontros. Consumo: 49 chamadas ao CLI, 194 mil tokens de entrada (194,1 mil em cache), 38,5 mil de saída, cerca de 5 minutos, custo equivalente de API US$ 1,85; gasto no OpenRouter US$ 0,0078; conta = ledger = US$ 8,370711103. O percentual consumido do limite do plano Pro não é legível pelo CLI. Detalhes e comparação com o Sonnet em [reports/claude_opus_5_5_subscription_run1.md](reports/claude_opus_5_5_subscription_run1.md). Revisão médica pendente; uma execução por caso, sem afirmação de superioridade.

## Atualização v4
Resultado atual e condições distintas em [v4_final_summary.md](v4_final_summary.md), com [artefato e animação](v4_comparison.html). Resumos acima permanecem históricos.

<!-- V4_FAST4_FINAL_START -->
## Atualização v4 rápida — 09/10/2026 18:29:56

Fast4 públicos 10/10, fechados 10/10 pelo juiz, separados; condição b3d7d00, sem retuning fechado. Global v4 US$1.061257675. conta e ledger conciliados; custos das respostas com usage.cost confirmados pelos metadados de geração; 1 rejeição sem usage.cost atribuída a zero por evidência de conta. [Resumo específico](v4_fast4_summary.md), [métricas e atores](v4_fast_summary.json), [artifact animado](v4_comparison.html). Histórico e negativos preservados; revisão médica pendente.
<!-- V4_FAST4_FINAL_END -->
