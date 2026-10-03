# Novos braços Astra e Sol 6.1 — execução concluída

Verificação UTC: 2026-09-30T21:22:13Z. O corpus `mvp10_v3_2026-09-26` e o protocolo clínico `mvp10_closedbook_v5_2026-09-26` permaneceram congelados. Cada novo modelo percorreu os dez casos, com três repetições por caso.

| Braço | Trajetórias terminais | Tentativas operacionais incompletas | Acesso |
|---|---:|---:|---|
| `gpt-6-astra` high | 30/30 | 1, preservada fora do denominador | assinatura Codex CLI, sem API paga |
| `gpt-6.1-sol` high | 30/30 | 0 | assinatura Codex CLI, sem API paga |

O [manifesto de traces](../results/frontier_addons_2026-09-29/trace_manifest.json) verificou os **230 terminais anteriores** e os **60 novos**, totalizando **290/300 combinações planejadas**. As dez ausências correspondem somente ao Luna, encerrado em 20/30 por solicitação do usuário. Nem Luna nem Terra foram retomados. A tentativa Astra que falhou imediatamente sob rede restrita foi preservada em `incomplete/`; a mesma combinação foi posteriormente concluída com acesso de rede.

O [relatório consolidado](../results/frontier_addons_2026-09-29/summaries/FRONTIER_ADDONS_REPORT.md) apresenta métricas exploratórias e comparações pareadas. Os matches de diagnóstico são triagem lexical determinística, **não acurácia clínica adjudicada**. A [fila cega adicional](../results/review_addons/round_2026_09_29_two/review_queue.csv) contém 60 trajetórias. Revisão médica de diagnóstico, alternativas aceitáveis, conduta e segurança está pendente; nenhum LLM foi utilizado como juiz único de segurança.

Os proxies equivalentes à tarifa API foram US$ 43,229340 para Astra e US$ 7,003420 para Sol 6.1 em 30 runs cada. São estimativas hipotéticas, distintas de cobrança real da assinatura, que não é observável por run. O proxy original de Sol 6 permanece US$ 4,6561284. O usuário utilizou manualmente o reset da cota em 30-09-2026; nenhum teste adicional está pendente para Astra ou Sol 6.1.

[Manifesto Astra](protocol_astra_extension_2026-09-29.json), [manifesto Sol 6.1](protocol_sol61_extension_2026-09-29.json) e [registro de acesso](astra_sol61_access_2026-09-29.md) documentam os modelos solicitados, versões de CLI e limites do transporte JSON emulado. O identificador servido internamente pela CLI não é exposto.
