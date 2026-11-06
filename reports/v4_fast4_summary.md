# v4 rápida fast4 — resultado final

Data final09/10/2026 18:29:56. Condição congelada b3d7d005a324db538b98882f6599cc33f2692eb5;321 testes passaram antes da inferência.

## Resultado e tempo

|Métrica|Públicos selecionados no desenvolvimento|Casos históricos de acesso fechado|
|---|---:|---:|
|Terminais únicos|10/10|10/10|
|Juízos finais positivos|10/10|10/10|
|Propostas iniciais positivas|6/10|6/9|
|Falhas operacionais/sem juízo|0|0|
|Wilson95% dos aceitos/terminais|72,25%–100,00%|72,25%–100,00%|
|Primeiro conteúdo P50/P95|1,24/1,63s|1,15/1,41s|
|Primeira fala completa P50/P95|1,59/2,02s|1,52/1,86s|
|União dos intervalos ativos P50/P95|103,61/119,35s|111,98/158,47s|
|Tempo de parede P50/P95|104,20/120,06s|123,01/8.785,85s|
|Latência do parecer Astra P50/P95|17,47/19,69s|19,15/21,47s|
|Entrada CLI por caso P50/IQR|33.473,50 / 32.937,75–33.970,50 (Q1–Q3)|35.827,50 / 35.037,50–37.934,00 (Q1–Q3)|
|Cache/entrada/saída CLI totais|22656 / 336208 / 13221|67968 / 353263 / 13615|
|Unidades relativas/fontes cobradas|268 / 42|287 / 67|
|Tentativas indisponíveis/repetidas|56 / 9|51 / 11|

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
|fast4 públicos|10/10 final|US$0.210319200|
|fast4 fechados|10/10 final|US$0.284180975|

API de implantação (médico+matcher+outros atores clínicos cobrados; paciente simulado e juízes separados): públicosUS$0.101091450, fechadosUS$0.168466975. Discriminação por ator[v4_fast_summary.json](v4_fast_summary.json). Não atribuir preço fictício à assinatura. O paciente simulado é custo do benchmark; em atendimento real, a pessoa responde diretamente.

Global v4: ledgerUS$1.061257675; delta da contaUS$1.061257675; diferençaUS$0E-9. Estadoconta e ledger conciliados; custos das respostas com usage.cost confirmados pelos metadados de geração; 1 rejeição sem usage.cost atribuída a zero por evidência de conta, metadados967 metadados recebidos para 967 respostas com usage.cost; 967 custos de geração coincidentes; 1 rejeição sem usage.cost com zero atribuído; 0 IDs de geração ausentes, chamadas pendentes/incertas0. Saldo conservador do tetoUS$ 5:US$3.938742325. Pilotos e falhas incluídos; não houve reinício de orçamento. A antiga diferençaUS$0.018154 das condições v4 anteriores foi posteriormente conciliada integralmente com168 metadados e contaUS$0.283960750; checkpoint preservado.

## O que mudou e limites comprovados

Conversa leve pela API, sem mapa CLI inicial; Sol/Astra só revisam, com até três chamadas principais e follow-ups limitados. Propostas e fala final excluídas por whitelist de evidência. Pedidos atômicos passam pela mesma política externa e custo por fonte. Retornos intermediários de pré-requisitos e filas mantêm texto exato/hash/recebedor. Indisponibilidade estruturada pode justificar uma única tentativa de método alternativo, sem repetir pedido idêntico ou consultar o juiz.

O piloto fast4 auditado001–002 reconstruiu seis inputs exatamente; doze outputs brutos de follow-up/hash válidos e onze achados literais de fonte. No001, o médico tinha só eco, mas o revisor obteve pericardiocentese e coronariografia após cumprir o pré-requisito:26 unidades/4 fontes ao terminal, não apenas5 unidades. Pseudoaneurisma/disrupção do stent passaram a ter suporte direto; infecção direta, cultura do líquido e ruptura ainda permanecem hipóteses.

No002 reapareceu `default_admission` nativo, corretamente excluído dos três inputs junto da fala final. Ainda persistiram troponina I→retorno T, EP posterior recebido na fase aguda e negativos sem fonte do paciente. Cinco afirmações sem fonte foram listadas no piloto, sem representar taxa calibrada global. As seis liberações de fila eram vazias e os contadores de duplicados zero: esse piloto não demonstra empiricamente todos os caminhos de fila/alternativas bloqueadas. Auditoria final/amostral[piloto público](v4_fast4_fidelity_pilot.md), [oito públicos restantes](v4_fast4_fidelity_remaining_public.md) e [agregado fechado](v4_fast4_closed_fidelity_aggregate.json) deve distinguir cobertura auditada da coorte inteira.

O juiz recebe GroundTruth, AssistantDiagnosis e MatchingCriterion, sem confiança, unconfirmed, next_steps ou manejo. Escores não validam segurança, calibração ou conformidade clínica. Confiança é autoatribuída. Protocolos/espécimes/momento pedidos não são confirmados pelo mero nome do exame ou por sua devolução literal.

Dez públicos foram usados repetidamente para desenvolvimento; fast4 é uma condição selecionada após pilotos e rodadas. Os dez fechados são históricos do próprio projeto, sem garantia de novidade para modelos. Relatar10/10 separadamente e não somar como se fossem vinte casos externos independentes. Nenhuma superioridade clínica ou acurácia100% generalizável estabelecida; revisão médica cega pendente.

## Integridade e conclusão técnica

Traces públicos manifestados em[v4_fast_public_trace_manifest.json](v4_fast_public_trace_manifest.json); privacidade/identidade opaca fechada emv4_fast_preregistration_digests.json e v4_fast_public_trace_manifest.json (digests opacos; manifestos integrais preservados localmente). Não publicar conteúdo, diagnóstico individual ou narrativa fechada. Verificação dos históricos978/978 arquivos canônicos e 888/888 presentes no worktree sem divergência; 90 arquivos históricos ignorados ausentes no worktree; validação final345 testes Python aprovados, incluindo 321 antes da inferência; 24 verificações offline de consolidação/artifact/documentação; JavaScript validado por Node; ver v4_fast_final_validation.json. Publicaçãohttps://github.com/codecapelo/MIRA-raul/pull/7. Após consolidar os vinte terminais desta condição, encerrar novas inferências e pausar automação de retomada.


Nos fechados, o tempo de parede manteve a cauda de pausas: P95 8.785,85s e máximo 15.833,52s, incluindo interrupção pelo limite da chave e pausa solicitada. A união dos intervalos de chamadas foi P50 111,98s / P95 158,47s. As pausas não foram apagadas; tempo ativo e tempo decorrido respondem a perguntas distintas, e nenhum deles isoladamente mede a qualidade da interação.


## Fidelidade fechada agregada

Auditoria agregada dos fechados: 46 respostas do paciente; 17 continham negativos sem fonte e 5 permaneceram ambíguas. 68 trechos distintos de exames e 20 arquivos-fonte foram verificados. Divergências de identidade: 0; candidatos de divergência literal de exames: 0. Estes números refletem o escopo auditado: não houve adjudicação clínica exaustiva das afirmações narrativas positivas ou do raciocínio médico. Ausência de divergência literal não demonstra segurança, adequação do manejo ou acurácia clínica. Nenhum achado da auditoria foi usado para reajustar a condição ou reclassificar resultados.

Os manifestos originais integrais e metadados de geração por chamada permanecem locais para auditoria, ignorados no Git quando contêm identificadores privados. Os exports públicos expõem digests opacos e contagens em v4_fast_preregistration_digests.json. A conciliação consulta o ledger somente em leitura; não altera custos históricos.

## Auditoria pública adicional e próximas correções

Todos os públicos foram auditados. Nos oito restantes: 24 inputs reconstruídos, 30 outputs exatos, 35 achados de fonte; 20 grupos conservadores de enunciados sem fonte em 12 respostas de 7 casos. Não são a mesma unidade das cinco afirmações específicas do piloto. Houve pré-requisito inadequado repetido, basal representando teste específico, MRI urgente adiada e histórico de dispositivo não relatado usado no raciocínio. Protocolos, contraste e momento não são atestados por equivalência nominal.

Propostas seguintes, não validadas nesta condição: paciente estruturado com desconhecidos explícitos; correspondência de espécime, protocolo e momento; triagem de urgência antes de gates de história e custo; detecção de ciclos de pré-requisitos; julgamento médico cego de diagnóstico e manejo. Nenhum código clínico foi alterado ou caso reexecutado após observar fechados.
