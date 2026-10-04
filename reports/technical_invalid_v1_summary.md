# Run1: julgamento LLM, revisão médica pendente

Completos 5/50; ausências e decisões inválidas explicitadas no JSON.

| Modelo | Completos | Corretos/julgados | Wilson 95% |
|---|---:|---:|---|
| openai/gpt-oss-120b | 1/10 | 0/1 | 0.0%–79.3% |
| z-ai/glm-4.5-air | 1/10 | 1/1 | 20.7%–100.0% |
| z-ai/glm-5 | 1/10 | 1/1 | 20.7%–100.0% |
| qwen/qwen3.5-397b-a17b | 1/10 | 1/1 | 20.7%–100.0% |
| openai/gpt-5.2 | 1/10 | 0/1 | 0.0%–79.3% |

Custo conhecido ledger: US$ 0.100672133; CSV completo: US$ 0.090163470. Custos de tentativas incompletas aparecem no detalhamento por ator. Chamadas não liquidadas impedem presumir total final.

Mediana/IQR de tokens e latência, intervalos por categoria e pares ausentes estão no JSON. Tokens de raciocínio são subconjunto da conclusão; não somar novamente. Grupos clínicos descritivos possuem denominadores pequenos.

O juiz LLM avalia equivalência diagnóstica. A análise antiga é lexical, com outros modelos, transporte, ferramentas e três repetições. Não há comparação de superioridade clínica. Revisão médica cega pendente. Repetições não são pacientes independentes.

Histórico imutável: 290/300 trajetórias, métricas originais de todos os modelos preservadas no JSON. Fonte `/Users/test/MIRA-RAUL/legacy/outputs/benchmark/results/frontier_addons_2026-09-29/summaries/frontier_addons_analysis.json`, SHA-256 `023eeb5127236fd413d85bb039af4bb1acc70ca599c1bacc3c28265d45181c79`.

## Custo e consumo por modelo

Custos por modelo abaixo somam episódios concluídos, incluindo todos os atores. O custo global por ator inclui também tentativas incompletas; por isso pode exceder esta soma.

| Modelo | Episódios | Custo total US$ | Custo médio US$ | Tokens totais mediana [Q1; Q3] | Prompt mediana [Q1; Q3] | Conclusão mediana [Q1; Q3] | Raciocínio mediana [Q1; Q3] |
|---|---:|---:|---:|---|---|---|---|
| openai/gpt-oss-120b | 1 | 0.009107 | 0.009107 | 131,486 [131,486; 131,486] | 119,515 [119,515; 119,515] | 11,971 [11,971; 11,971] | 2,221 [2,221; 2,221] |
| z-ai/glm-4.5-air | 1 | 0.002339 | 0.002339 | 10,530 [10,530; 10,530] | 8,497 [8,497; 8,497] | 2,033 [2,033; 2,033] | 1,009 [1,009; 1,009] |
| z-ai/glm-5 | 1 | 0.008630 | 0.008630 | 13,019 [13,019; 13,019] | 9,863 [9,863; 9,863] | 3,156 [3,156; 3,156] | 1,706 [1,706; 1,706] |
| qwen/qwen3.5-397b-a17b | 1 | 0.020238 | 0.020238 | 14,828 [14,828; 14,828] | 10,069 [10,069; 10,069] | 4,759 [4,759; 4,759] | 3,242 [3,242; 3,242] |
| openai/gpt-5.2 | 1 | 0.049849 | 0.049849 | 17,768 [17,768; 17,768] | 14,377 [14,377; 14,377] | 3,391 [3,391; 3,391] | 1,375 [1,375; 1,375] |

## Categorias e casos

Cada linha tem seu próprio denominador; Wilson é calculado sobre julgamentos válidos. Categorias amplas foram atribuídas manualmente e não correspondem aos estratos do artigo.

| Modelo | Categoria | Completos | Corretos/julgados | Wilson 95% |
|---|---|---:|---:|---|
| openai/gpt-oss-120b | cardiovascular | 1 | 0/1 | 0.0%–79.3% |
| openai/gpt-oss-120b | endocrine_infectious | 0 | 0/0 | indisponível |
| openai/gpt-oss-120b | gastrointestinal | 0 | 0/0 | indisponível |
| openai/gpt-oss-120b | hematology | 0 | 0/0 | indisponível |
| openai/gpt-oss-120b | neurologic | 0 | 0/0 | indisponível |
| openai/gpt-oss-120b | obstetric | 0 | 0/0 | indisponível |
| openai/gpt-oss-120b | respiratory_oncology | 0 | 0/0 | indisponível |
| openai/gpt-oss-120b | urologic | 0 | 0/0 | indisponível |
| z-ai/glm-4.5-air | cardiovascular | 1 | 1/1 | 20.7%–100.0% |
| z-ai/glm-4.5-air | endocrine_infectious | 0 | 0/0 | indisponível |
| z-ai/glm-4.5-air | gastrointestinal | 0 | 0/0 | indisponível |
| z-ai/glm-4.5-air | hematology | 0 | 0/0 | indisponível |
| z-ai/glm-4.5-air | neurologic | 0 | 0/0 | indisponível |
| z-ai/glm-4.5-air | obstetric | 0 | 0/0 | indisponível |
| z-ai/glm-4.5-air | respiratory_oncology | 0 | 0/0 | indisponível |
| z-ai/glm-4.5-air | urologic | 0 | 0/0 | indisponível |
| z-ai/glm-5 | cardiovascular | 1 | 1/1 | 20.7%–100.0% |
| z-ai/glm-5 | endocrine_infectious | 0 | 0/0 | indisponível |
| z-ai/glm-5 | gastrointestinal | 0 | 0/0 | indisponível |
| z-ai/glm-5 | hematology | 0 | 0/0 | indisponível |
| z-ai/glm-5 | neurologic | 0 | 0/0 | indisponível |
| z-ai/glm-5 | obstetric | 0 | 0/0 | indisponível |
| z-ai/glm-5 | respiratory_oncology | 0 | 0/0 | indisponível |
| z-ai/glm-5 | urologic | 0 | 0/0 | indisponível |
| qwen/qwen3.5-397b-a17b | cardiovascular | 1 | 1/1 | 20.7%–100.0% |
| qwen/qwen3.5-397b-a17b | endocrine_infectious | 0 | 0/0 | indisponível |
| qwen/qwen3.5-397b-a17b | gastrointestinal | 0 | 0/0 | indisponível |
| qwen/qwen3.5-397b-a17b | hematology | 0 | 0/0 | indisponível |
| qwen/qwen3.5-397b-a17b | neurologic | 0 | 0/0 | indisponível |
| qwen/qwen3.5-397b-a17b | obstetric | 0 | 0/0 | indisponível |
| qwen/qwen3.5-397b-a17b | respiratory_oncology | 0 | 0/0 | indisponível |
| qwen/qwen3.5-397b-a17b | urologic | 0 | 0/0 | indisponível |
| openai/gpt-5.2 | cardiovascular | 1 | 0/1 | 0.0%–79.3% |
| openai/gpt-5.2 | endocrine_infectious | 0 | 0/0 | indisponível |
| openai/gpt-5.2 | gastrointestinal | 0 | 0/0 | indisponível |
| openai/gpt-5.2 | hematology | 0 | 0/0 | indisponível |
| openai/gpt-5.2 | neurologic | 0 | 0/0 | indisponível |
| openai/gpt-5.2 | obstetric | 0 | 0/0 | indisponível |
| openai/gpt-5.2 | respiratory_oncology | 0 | 0/0 | indisponível |
| openai/gpt-5.2 | urologic | 0 | 0/0 | indisponível |

| Caso | Categoria | Completos | Corretos/julgados entre modelos | Wilson 95% |
|---|---|---:|---:|---|
| case_001 | cardiovascular | 5/5 | 3/5 | 23.1%–88.2% |
| case_002 | cardiovascular | 0/5 | 0/0 | indisponível |
| case_003 | urologic | 0/5 | 0/0 | indisponível |
| case_004 | respiratory_oncology | 0/5 | 0/0 | indisponível |
| case_005 | respiratory_oncology | 0/5 | 0/0 | indisponível |
| case_006 | endocrine_infectious | 0/5 | 0/0 | indisponível |
| case_007 | hematology | 0/5 | 0/0 | indisponível |
| case_008 | neurologic | 0/5 | 0/0 | indisponível |
| case_009 | gastrointestinal | 0/5 | 0/0 | indisponível |
| case_010 | obstetric | 0/5 | 0/0 | indisponível |

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
