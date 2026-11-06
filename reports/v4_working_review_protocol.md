# Revisão complementar da v4 — protocolo congelado

Este estudo é uma revisão offline, posterior à observação de 9/10 no encontro original. Não constitui novo encontro, repetição do benchmark ou substituição do resultado original. É uma hipótese de melhoria para uma próxima condição prospectiva.

Os dez casos públicos recebem o mesmo prompt genérico: distinguir hipótese etiológica mais provável de achados confirmados; ausência de exame confirmatório não prova nem exclui uma hipótese; não atribuir protocolo, momento ou espécime que o retorno não estabelece. Não há dica específica de diagnóstico ou seleção de revisões conforme o resultado do juiz.

Revisor solicitado: gpt-6-astra, medium, pela assinatura ChatGPT/Codex no mesmo transporte fechado. O input contém apresentação e exame inicial, falas do médico/paciente, mapa inicial e informações efetivamente devolvidas. Exclui referência, juízos anteriores, saída diagnóstica dos revisores e argumentos de admissão. As falas e o mapa podem sugerir hipóteses; cegamento à referência não equivale a independência do encontro.

Somente depois da resposta a referência é aberta ao Gemini Pro pela OpenRouter, com o mesmo critério da v4 e a exceção histórica do caso009 identificada. O juiz LLM e o custo dos dez pareceres são reportados separadamente. Não se consulta o juiz para selecionar entre alternativas ou retentar respostas.

Os traces têm evento working_review_complete, nunca case_complete, em runs/v4/working_diagnosis_review. Hash do trace de origem e do input são registrados; terminais anteriores permanecem intactos. O teto adicional US$5 é compartilhado com os encontros originais. Custo da assinatura é desconhecido.

O protótipo TemporalCaseTools fica fora da condição original e desta revisão. Seus testes validam bloqueios de metadados e pré-requisitos; não demonstram desempenho clínico nem resolvem todas as divergências de protocolo de exame.
