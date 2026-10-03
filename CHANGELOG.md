# Histórico de alterações

## 2026-10-03 — protocolo MIRA-RAUL

- Preservado o experimento anterior em `legacy/`, incluindo 290 percursos terminais; novo experimento possui denominador independente.
- Adaptados os mesmos dez casos públicos para fatos do paciente, investigações, referências e procedência separadas. Estes casos não são prontuários privados nem o conjunto completo usado por Zhang et al.
- Adotada a variante diagnóstica VivaBench, com paciente sem ferramentas, médico com ferramentas e juiz por equivalência clínica. O julgamento novo não é intercambiável com o escore lexical anterior.
- Limite rígido de dez turnos do médico por decisão do usuário. Diverge do código upstream auditado, que oferece encerramento adicional; coincide com o limite descrito no texto do artigo.
- Ausência de Plan mantida conforme estratégia de planejamento implícito do artigo e ferramentas ativas upstream.
- Narrativa inicial limitada à apresentação, com exames publicados disponíveis sob solicitação e compressão temporal. Preservados os metadados originais de disponibilidade/pré-requisitos; sem bloqueio geral `time_zero`, mantendo exclusão de `unavailable_for_immediate_care`. Não é réplica estrita da admissão MIRA-v2.
- Julgamento usa o ramo AIDOC/MIMIC upstream com diagnóstico de referência e critério clínico como strings; não usa o ramo VivaBench de gold/diferenciais ou crédito parcial. Médico e paciente mantêm prompts VivaBench.
- Transporte adaptado para OpenRouter, com seleção explícita de modelo/provedor, fallback desabilitado, verificação de preços e controle de orçamento.
- Submissão final denominada `admission`, equivalente ao `finish` upstream, forçada no décimo turno. Juiz configurado com temperatura 1 e teto de 8.192 tokens; associador com temperatura 0,01 e teto de 2.048 tokens. São divergências de parâmetros em relação ao código upstream e devem ser reportadas.
- Sem repetição automática de um caso inteiro; falhas, respostas e custos permanecem no rastro. Diverge do upstream, que permite três tentativas e pode reutilizar agentes/contexto/coletor.
- Auditoria do commit upstream `eea2386c665c9caaa7ee093c8cb092d1c337de88` preservada em `reports/upstream_audit.md`. Nenhum resultado de inferência é declarado nesta entrada.

## 2026-10-03 — rota GPT-OSS antes de completar o piloto
DekaLLM BF16 recusou chamadas com HTTP429 (pool compartilhado). Tentativa incompleta preservada; US$0,00031545 contabilizados e saldo reconciliado. Rota fixa substituída por AkashML BF16, com logprobs e sem fallback. O caso incompleto reinicia, sem repetir encontros terminais. A mudança afeta latência/implementação do provedor; não altera fatos ou prompts.
