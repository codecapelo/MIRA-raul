# Reparo de auditoria após a avaliação v4

Este patch é prospectivo e foi preparado após identificar uma lacuna no registro da fila de exames. Ele **não integrou os dez novos encontros avaliados** e não altera seus traces, julgamentos, resultados ou condições. Aplicar somente depois dos dez terminais e do encerramento dos trabalhadores.

`V3Tools.release()` pode executar exames antes retidos pela política e devolver os resultados na mensagem do médico, sem um evento `tool` com esse retorno. Eventos `exam_cost` registram contabilidade; não provam o texto exato entregue e não devem ser usados para inventar ou preencher resultados históricos.

O reparo acrescenta um evento `released_results` somente com `protocol='v4'` e `extras['record_released_results']=True`. O evento registra o valor exato e intacto de `release()`, SHA256 de UTF-8, turno, número de trocas e ponto de entrega (`patient_reply` ou `silent_turn`), imediatamente antes do `doctor.append` original. Texto vazio não gera evento. Flags/defaults de v3 e v4 continuam iguais; nenhum lançador passa a ativar o registro automaticamente.

Na retomada, o mesmo ponto e conteúdo não produz um segundo evento. Conteúdo diferente no mesmo ponto bloqueia a retomada sem sobrescrever o registro. A construção da mensagem, prompts, fatos, ferramentas, execução de exames e critérios clínicos permanecem intactos.

A animação v4 mostra o texto efetivamente registrado, usando o truncamento já existente e sem somar custo ou unidades de exame. Valida seu hash e suprime duplicatas exatas de importação. Não reconstrói achados a partir de `exam_cost`.

`blinded_transcript`, `review_events`, cascade e fontes de casos não são alterados. O evento adicional **não entra automaticamente nos revisores clínicos**. Uma futura mudança para ampliar o conteúdo recebido pelo revisor exige uma condição e avaliação separadas; este patch é apenas registro e apresentação.

Validação: nove testes com runner e clientes simulados, sem API ou inferência. Cobrem entrega ao médico versus texto registrado em ambos os caminhos, ausência em v3 e v4 default, ausência no input de revisão, deduplicação/imutabilidade em replay e animação sem custo adicional. Não houve aplicação ao repositório durante a avaliação.
