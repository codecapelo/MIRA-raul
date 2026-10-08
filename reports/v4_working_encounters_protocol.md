# v4: validação do parecer final em novos encontros

O resultado original é9/10. Uma revisão offline posterior dos dez traces, com prompt genérico e referência oculta, obteve10/10 pelo juiz LLM. Isso motiva este teste, sem substituir qualquer resultado anterior.

Nova condição: dez encontros públicos novos em runs/v4/sol_working/run1. Mantém médico/paciente/mapa Sol medium, anamnese mínima, exame inicial, exames imediatos, componentes literais, unidades relativas, cascade original Sol/Astra, sweep e juiz/critério da v4. Adiciona uma última revisão sempre Astra medium, antes de abrir a referência ao juiz, usando exatamente SYSTEM do estudo offline.

O parecer final recebe só apresentação, exame inicial e evidências efetivamente entregues, mapa e falas. Admissão/proposta, diagnóstico dos revisores, referências e juízos são excluídos; falas clínicas podem sugerir hipóteses. Uma hipótese mais provável permanece distinguida de confirmação: confiança autoatribuída, itens não confirmados e próximos passos são guardados em working_final_review e na justificativa final.

Não usa TemporalCaseTools: a compressão temporal e equivalências de protocolo de exame continuam limitações herdadas, identificadas no relatório. Não altera dados ou critérios. São os mesmos casos de desenvolvimento, não holdout nem demonstração clínica externa. A comparação com Claude v3.6 não isola efeito causal de um componente.

Teto global v4 adicionalUS$5, sharedledger existente, contabiliza todos os atores e parciais. Estados incertos bloqueiam. Delta de conta acima ledger bloqueia; abaixo dele preserva integralmente usage.cost e registra atraso sem atribuir zero. Piloto de dois casos e despacho posterior usam mesmo manifesto de dez, commit e hashes congelados. O launcher não retenta; continuação explícita reutiliza prefixos com hash integral idêntico e pula terminais. Falha no parecer final propaga sem fallback, sem juiz e sem case_complete. Não repetir terminal.

O cache das comparações same_* é reexecutado exclusivamente pelo transporte de replay, conferindo payload e valor, para manter a sequência de respostas CLI na retomada. Essa correção operacional não muda prompt ou política. Cachedfailed sem resposta durável bloqueia.

Ao completar os dez, encerrar experimentos desta tarefa, consolidar custo/saldo, comparar denominadores, auditar fidelidade, atualizar artifact e publicar os resultados honestos. Não selecionar somente casos favoráveis nem retentar para conseguir100%.
