# v4: interação rápida e revisão concentrada —09/10/2026

Nova autorização do usuário: resolver latência/tokens, otimizar nos dez públicos até obter10/10 pelo juiz e só depois avaliar os dez casos de acesso fechado. Continua o teto adicional globalUS$5, incluindo todas as rodadas v4, falhas e atores; não é uma nova franquia. Nenhum terminal antigo será repetido ou substituído.

## Condição fast1, congelada antes da inferência

Médico conversacional e paciente simulado: Gemini3.1Flash-Lite Preview, GoogleAIStudio standard fixo, sem fallback, raciocínio mínimo, ferramentas clínicas nativas na API. Médico máximo4096tokens, paciente512 e paciente de revisão1024. Anamnese mínima de duas trocas, exame físico inicial, liberação imediata, fala concisa, componentes literais, política de pedidos e custos relativos1/5/15 deduplicados por fonte. Sem mapa pesado antes da primeira pergunta.

Sol6.1 medium: uma revisão cega das informações obtidas; pode solicitar um follow-up limitado. Astra medium: sempre um parecer final com o mesmo contrato genérico de hipótese de trabalho, achados não confirmados e próximos passos. Ambos exclusivamente pela assinatura ChatGPT/Codex. Sem comparadores diagnósticos, JEF ou resultados de juiz nos inputs clínicos. O revisor recebe falas API e resultados exatos da fila validados por SHA; não somente os eventos CLI. Proposta/admissão, referência e parecer anterior ficam excluídos.

Streaming somente nas falas API: registra primeiro frame, primeiro conteúdo, primeira ferramenta e término, com geração/ID de requisição. Deve receber uso/custo e término completo; frame final de contabilização não duplica conteúdo. Interrupção não implica custo zero e bloqueia novos envios até conciliação. Ferramentas são executadas depois da resposta montada, nunca sobre argumentos parciais. O tempo até primeiro conteúdo não é necessariamente até uma frase completa exibível. Juízes/matcher conservam o transporte anterior.

CLI: somente duas chamadas principais por caso, um executor por vez. Captura opt-in apenas contagens sanitizadas de mensagens de transporte; não persiste stderr bruto. As antigas pausas próximas de300segundos são compatíveis com espera de transporte, mas sua causa não está provada. Não foram aplicadas configurações especulativas de timeout/retry: o provedor builtin da versão instalada não aceita a sobrescrita proposta. A hipótese de melhora vem da menor exposição a chamadas e contextos CLI, além da troca da conversa para a API rápida.

## Execução e critérios

Públicos001–010: novos encontros em runs/v4/fast/fast1/public/run1, com piloto dos primeiros dois e depois os restantes, mantendo a mesma condição. Não repetir apenas erros para elevar escore. Caso o resultado seja inferior10/10, documentar todos os resultados e examinar falhas; mudanças genéricas exigem variante nova e todos os dez encontros novos, jamais dicas de alvo ou alteração de fatos/critério. Todas as tentativas contam no orçamento. No máximo três variantes iniciais e sempre dentro do teto; ausência de100% não autoriza compra de créditos, loops de chamadas ou ocultação de tentativas.

Fechados011–020: só entram depois de públicos10terminais únicos e10juízos positivos. Mesmos código/config/parâmetros/commit, com gate automático. Identidades dos vinte casos são congeladas por hashes; arquivos privados são lidos apenas para identidade opaca antes do gate, sem parsing semântico nem acesso por atores clínicos. Conteúdo de referências só chega ao juiz após parecer final. Resultados fechados são validação da condição selecionada, nunca usados para retunar essa rodada. São casos históricos já usados no projeto, não holdout externo novo.

Traces e detalhes fechados ficam somente em runs/v4/fast_private, ignorado e verificado antes do despacho. Publicação mostra apenas agregados, custos, parâmetros e integridade, sem narrativas, diagnósticos ou fatos fechados. A revisão médica permanece pendente;10/10 de um juiz não estabelece segurança ou acurácia generalizável.

Métricas: acerto do juiz por condição/coorte, falhas operacionais, tempo até primeiro conteúdo/pergunta completa, P50/P95 de falas e parecer final, tempo em chamadas versus parede, tokens por ator/cache, custoAPI real e custos da assinatura desconhecidos, unidades/exames repetidos e indisponíveis. Pausas longas permanecem no resultado; não descontá-las como se tivessem sido corrigidas.

## Continuidade

Implementação/testes e commit precedem inferência. Não alterar HEAD, fatos, código ou configuração entre públicos e fechados. Ledger runs/v4/budget.sqlite único, cap5; reservas/incertos bloqueiam, maior delta de conta bloqueia, maior usage.cost recebido é preservado. Retomada de parciais somente por hash integral idêntico, sem retry automático. Terminais são pulados.

A conciliação anterior confirmou em09/10 os168metadados e delta contaUS$0.283960750 igual ledgerUS$0.28396075; checkpoint com diferença foi preservado. Nenhum custo foi reclassificado.
