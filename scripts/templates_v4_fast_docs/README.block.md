## v4 rápida — conversa Flash-Lite e supervisão Sol/Astra

Condição final `fast4`, congelada no commit `b3d7d005a324db538b98882f6599cc33f2692eb5`, com321 testes aprovados antes da inferência. A conversa e o paciente simulado usam Gemini 3.1 Flash-Lite pela OpenRouter; Sol 6.1/Astra permanecem revisores pela assinatura ChatGPT/Codex, esforço medium. Não há mapa pesado antes da primeira fala, comparadores de diagnósticos ou JEF.

|Coorte|Terminais|Aceitos pelo juiz final|Proposta inicial aceita|OpenRouter, todos os atores|Mediana da primeira fala completa|Mediana do tempo em chamadas|
|---|---:|---:|---:|---:|---:|---:|
|Públicos de desenvolvimento|{{PUBLIC_TERMINALS}}/10|{{PUBLIC_ACCEPTED}}/10|{{PUBLIC_PROPOSAL_ACCEPTED}}/{{PUBLIC_PROPOSAL_JUDGED}}|US${{PUBLIC_API_USD}}|{{PUBLIC_FIRST_FULL_P50_S}}s|{{PUBLIC_ACTIVE_P50_S}}s|
|Casos de acesso fechado|{{CLOSED_TERMINALS}}/10|{{CLOSED_ACCEPTED}}/10|{{CLOSED_PROPOSAL_ACCEPTED}}/{{CLOSED_PROPOSAL_JUDGED}}|US${{CLOSED_API_USD}}|{{CLOSED_FIRST_FULL_P50_S}}s|{{CLOSED_ACTIVE_P50_S}}s|

Os fechados só foram liberados após dez terminais públicos e dez juízos positivos na mesma condição. São casos históricos já utilizados no projeto, não um holdout externo novo. Resultados de desenvolvimento, validação fechada e pilotos permanecem separados. [Resumo final](reports/v4_fast4_summary.md), [protocolo](reports/v4_fast_protocol.md) e [artifact com relógio e etapas](reports/v4_comparison.html).

Gasto global adicional v4: US${{GLOBAL_LEDGER_USD}}, incluindo condições anteriores, todos os atores e falhas, dentro do teto únicoUS$ 5. Situação financeira: {{BILLING_STATUS}}. O custo monetário da assinatura é desconhecido. Tokens de API e CLI, cache e espera são reportados separadamente; menor gasto OpenRouter não implica menor custo total.

A condição corrige o vazamento de `default_admission` para os revisores, preserva resultados brutos/hash dos pré-requisitos e mantém todos os pedidos dentro da política compartilhada de exames. Até quatro pedidos atômicos iniciais e dois adicionais; pré-requisitos podem acrescentar procedimentos cobrados. Um único segundo Sol pode buscar alternativas diante de achados novos ou indisponibilidade estruturada; Astra sempre finaliza. Não há loops orientados pelo juiz.

A revisão médica permanece pendente. O piloto auditado mostrou números literais corretos, mas ainda apresentou negativos do paciente sem fonte, troponina I mapeada para troponina T e resultado eletrofisiológico posterior entregue durante o encontro agudo. Confiança autoatribuída e conduta não fazem parte do input do juiz. Nenhum escore demonstra segurança clínica ou100% generalizável.
