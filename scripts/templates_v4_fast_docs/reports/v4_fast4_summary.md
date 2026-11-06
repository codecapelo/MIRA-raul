# v4 rápida fast4 — resultado final

**RASCUNHO: substituir todos os placeholders somente após20 terminais únicos e conciliação.** Preparação não afirma que a execução terminou. Data final{{FINAL_DATE_LOCAL}}. Condição congelada b3d7d005a324db538b98882f6599cc33f2692eb5;321 testes passaram antes da inferência.

## Resultado e tempo

|Métrica|Públicos selecionados no desenvolvimento|Casos históricos de acesso fechado|
|---|---:|---:|
|Terminais únicos|{{PUBLIC_TERMINALS}}/10|{{CLOSED_TERMINALS}}/10|
|Juízos finais positivos|{{PUBLIC_ACCEPTED}}/10|{{CLOSED_ACCEPTED}}/10|
|Propostas iniciais positivas|{{PUBLIC_PROPOSAL_ACCEPTED}}/{{PUBLIC_PROPOSAL_JUDGED}}|{{CLOSED_PROPOSAL_ACCEPTED}}/{{CLOSED_PROPOSAL_JUDGED}}|
|Falhas operacionais/sem juízo|{{PUBLIC_OPERATIONAL}}|{{CLOSED_OPERATIONAL}}|
|Wilson95% dos aceitos/terminais|{{PUBLIC_WILSON95}}|{{CLOSED_WILSON95}}|
|Primeiro conteúdo P50/P95|{{PUBLIC_TTFT_P50_S}}/{{PUBLIC_TTFT_P95_S}}s|{{CLOSED_TTFT_P50_S}}/{{CLOSED_TTFT_P95_S}}s|
|Primeira fala completa P50/P95|{{PUBLIC_FIRST_FULL_P50_S}}/{{PUBLIC_FIRST_FULL_P95_S}}s|{{CLOSED_FIRST_FULL_P50_S}}/{{CLOSED_FIRST_FULL_P95_S}}s|
|União dos intervalos ativos P50/P95|{{PUBLIC_ACTIVE_P50_S}}/{{PUBLIC_ACTIVE_P95_S}}s|{{CLOSED_ACTIVE_P50_S}}/{{CLOSED_ACTIVE_P95_S}}s|
|Tempo de parede P50/P95|{{PUBLIC_WALL_P50_S}}/{{PUBLIC_WALL_P95_S}}s|{{CLOSED_WALL_P50_S}}/{{CLOSED_WALL_P95_S}}s|
|Latência do parecer Astra P50/P95|{{PUBLIC_ASTRA_P50_S}}/{{PUBLIC_ASTRA_P95_S}}s|{{CLOSED_ASTRA_P50_S}}/{{CLOSED_ASTRA_P95_S}}s|
|Entrada CLI por caso P50/IQR|{{PUBLIC_CLI_INPUT_P50_IQR}}|{{CLOSED_CLI_INPUT_P50_IQR}}|
|Cache/entrada/saída CLI totais|{{PUBLIC_CLI_CACHE_INPUT_OUTPUT}}|{{CLOSED_CLI_CACHE_INPUT_OUTPUT}}|
|Unidades relativas/fontes cobradas|{{PUBLIC_EXAM_UNITS_SOURCES}}|{{CLOSED_EXAM_UNITS_SOURCES}}|
|Tentativas indisponíveis/repetidas|{{PUBLIC_UNAVAILABLE_DUPLICATES}}|{{CLOSED_UNAVAILABLE_DUPLICATES}}|

Primeiro conteúdo é evento de streaming, não necessariamente uma frase completa. Tokens de CLI incluem contexto reenviado e sobrecarga do transporte; cache separado. Pausas preservadas, intervalos sobrepostos deduplicados. A comparação com versões anteriores envolve mudanças simultâneas; não é efeito causal isolado.

## Custos e histórico completo

|Condição|Denominador/resultado|OpenRouter todos os atores|
|---|---|---:|
|Claude v3.6, dez públicos exatos|10/10 juiz final;9/10 proposta|US$0.35023969|
|v4 original|9/10 final;8/10 proposta|US$0.12304050|
|v4 revisão offline posterior|10/10 pareceres julgados; não são encontros novos|US$0.045766|
|v4 novos encontros com revisão final Astra|10/10 final;9/10 proposta|US$0.11515425|
|fast1|9/10 final;4/10 proposta, falha de cegamento documentada|US$0.19446700|
|fast2 piloto|1/2; não ampliado, pré-requisito não executado por bug de parser|US$0.04537300|
|fast3 piloto|1/2; não ampliado, diagnóstico negativo preservado|US$0.04295675|
|fast4 públicos|{{PUBLIC_ACCEPTED}}/10 final|US${{PUBLIC_API_USD}}|
|fast4 fechados|{{CLOSED_ACCEPTED}}/10 final|US${{CLOSED_API_USD}}|

API de implantação (médico+matcher+outros atores clínicos cobrados; paciente simulado e juízes separados): públicosUS${{PUBLIC_DEPLOY_API_USD}}, fechadosUS${{CLOSED_DEPLOY_API_USD}}. Discriminação por ator{{ACTOR_COST_REPORT_PATH}}. Não atribuir preço fictício à assinatura. O paciente simulado é custo do benchmark; em atendimento real, a pessoa responde diretamente.

Global v4: ledgerUS${{GLOBAL_LEDGER_USD}}; delta da contaUS${{GLOBAL_ACCOUNT_DELTA_USD}}; diferençaUS${{GLOBAL_BILLING_DIFFERENCE_USD}}. Estado{{BILLING_STATUS}}, metadados{{GENERATION_RECONCILIATION_COUNTS}}, chamadas pendentes/incertas{{PENDING_UNCERTAIN_COUNT}}. Saldo conservador do tetoUS$ 5:US${{GLOBAL_CAP_REMAINING_USD}}. Pilotos e falhas incluídos; não houve reinício de orçamento. A antiga diferençaUS$0.018154 das condições v4 anteriores foi posteriormente conciliada integralmente com168 metadados e contaUS$0.283960750; checkpoint preservado.

## O que mudou e limites comprovados

Conversa leve pela API, sem mapa CLI inicial; Sol/Astra só revisam, com até três chamadas principais e follow-ups limitados. Propostas e fala final excluídas por whitelist de evidência. Pedidos atômicos passam pela mesma política externa e custo por fonte. Retornos intermediários de pré-requisitos e filas mantêm texto exato/hash/recebedor. Indisponibilidade estruturada pode justificar uma única tentativa de método alternativo, sem repetir pedido idêntico ou consultar o juiz.

O piloto fast4 auditado001–002 reconstruiu seis inputs exatamente; doze outputs brutos de follow-up/hash válidos e onze achados literais de fonte. No001, o médico tinha só eco, mas o revisor obteve pericardiocentese e coronariografia após cumprir o pré-requisito:26 unidades/4 fontes ao terminal, não apenas5 unidades. Pseudoaneurisma/disrupção do stent passaram a ter suporte direto; infecção direta, cultura do líquido e ruptura ainda permanecem hipóteses.

No002 reapareceu `default_admission` nativo, corretamente excluído dos três inputs junto da fala final. Ainda persistiram troponina I→retorno T, EP posterior recebido na fase aguda e negativos sem fonte do paciente. Cinco afirmações sem fonte foram listadas no piloto, sem representar taxa calibrada global. As seis liberações de fila eram vazias e os contadores de duplicados zero: esse piloto não demonstra empiricamente todos os caminhos de fila/alternativas bloqueadas. Auditoria final/amostral{{FINAL_FIDELITY_REPORT_PATH}} deve distinguir cobertura auditada da coorte inteira.

O juiz recebe GroundTruth, AssistantDiagnosis e MatchingCriterion, sem confiança, unconfirmed, next_steps ou manejo. Escores não validam segurança, calibração ou conformidade clínica. Confiança é autoatribuída. Protocolos/espécimes/momento pedidos não são confirmados pelo mero nome do exame ou por sua devolução literal.

Dez públicos foram usados repetidamente para desenvolvimento; fast4 é uma condição selecionada após pilotos e rodadas. Os dez fechados são históricos do próprio projeto, sem garantia de novidade para modelos. Relatar{{CLOSED_ACCEPTED}}/10 separadamente e não somar como se fossem vinte casos externos independentes. Nenhuma superioridade clínica ou acurácia100% generalizável estabelecida; revisão médica cega pendente.

## Integridade e conclusão técnica

Traces públicos manifestados em{{PUBLIC_MANIFEST_PATH}}; privacidade/identidade opaca fechada em{{CLOSED_AGGREGATE_MANIFEST_PATH}}. Não publicar conteúdo, diagnóstico individual ou narrativa fechada. Verificação dos históricos{{HISTORICAL_HASH_STATUS}}; validação final{{FINAL_VALIDATION_STATUS}}. Publicação{{PR_URL}}. Após consolidar os vinte terminais desta condição, encerrar novas inferências e pausar automação de retomada.
