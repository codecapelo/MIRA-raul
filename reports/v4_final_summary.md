# v4 — três condições públicas separadas

A variante prospectiva tem dez novos encontros. A revisão offline reutiliza os dez encontros originais e permanece fora do denominador de novos encontros.

| Condição | Julgamento LLM | Wilson95% nos julgados | API real USD | API de implantação USD | Exames artificiais |
|---|---:|---:|---:|---:|---:|
| original_v4_sol | 9/10; 0 não julgados | 59.6%–98.2% | 0.12304050 | 0.03262650 | 247 |
| prospective_v4_sol_working | 10/10; 0 não julgados | 72.2%–100.0% | 0.11515425 | 0.03127225 | 257 |
| offline_working_review | 10/10; 0 não julgados | 72.2%–100.0% | 0.045766 | 0 | 0 |

Ledger global USD 0.28396075; diferença da conta USD 0.265806750; ledger menos conta USD 0.018154000. Teto global USD5 preservado.
Reconciliação exata: False. Respostas API únicas: 168. Entradas de ledger sem resposta durável: 0.

Hipóteses working não equivalem a confirmação. Juiz LLM não estabelece acurácia clínica, segurança ou superioridade. Revisão médica permanece pendente.

Os custos de implantação excluem juízes e paciente. Os valores de API são usage.cost recebido; o preço da assinatura é desconhecido. Exames são unidades artificiais 1/5/15.

Tokens abaixo são somas por caso, seguidas de mediana [Q1–Q3]. Cache já integra input. Chamadas CLI interrompidas sem uso durável não são zero e podem tornar essas contagens limites inferiores.

| Condição / transporte | Input mediana [Q1–Q3] | Output mediana [Q1–Q3] | Cache input mediana [Q1–Q3] |
|---|---:|---:|---:|
| original_v4_sol / api | 11543.5 [5558.75–13328] | 1251.5 [721–1487.5] | 0 [0–0] |
| original_v4_sol / subscription_cli | 172308 [150972–197233] | 3441 [3256.5–3539.25] | 30592 [9504–37280] |
| original_v4_sol / all_recorded | 189223 [161332–208852] | 4628.5 [4103.75–5281.25] | 30592 [9504–37280] |
| prospective_v4_sol_working / api | 9004 [6462–12234.8] | 1107 [818.5–1413.75] | 0 [0–0] |
| prospective_v4_sol_working / subscription_cli | 183706 [154140–204304] | 3689.5 [3520.75–3926.5] | 32256 [24064–54624] |
| prospective_v4_sol_working / all_recorded | 192464 [158191–214774] | 4760 [4324.25–5000] | 32256 [24064–54624] |
| offline_working_review / api | 624.5 [613–633.5] | 227.5 [202.5–301.5] | 0 [0–0] |
| offline_working_review / subscription_cli | 11942.5 [11839.2–12139.8] | 412.5 [387.25–426.25] | 0 [0–0] |
| offline_working_review / all_recorded | 12550 [12461.8–12774.8] | 615 [592.75–779.25] | 0 [0–0] |

O JSON contém distribuição/IQR completos, custos por ator, uso CLI desconhecido, parâmetros de identidade, hashes dos 30 traces e CSV separados.

Claude v36 histórico: 10/10 julgados; API USD 0.35023969. Comparação descritiva de condições não equivalentes.
