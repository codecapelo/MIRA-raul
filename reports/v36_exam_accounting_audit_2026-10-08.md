# Auditoria offline do custo e dos exames v3.6/v3.7

08-10-2026. Fonte somente leitura: worktreeClaude `complete-remaining-100-cases-356596`, commitc1d3270. Script novo `scripts/audit_exam_usage.py`, resultado agregado `all_v3_exam_usage_audit_2026-10-08.json`. Nenhuma inferência, acesso a chave, chamada paga, modificação de traces ou dado fechado exportado. O script examinou25condiçõesv3,207terminais;207/207custos de terminal coincidem com soma de `usage.cost` de todos os atores.

## Twenty-case v3.6

Condição: `glm5_xf_imm_cas_v32sjeft86a20dsxotswaglc50op5cbam1evxprv_n2`. São20terminais,20positivos pelo juiz. Não existe garantia clínica de100%.

| Custo dos20 | US$ |
|---|---:|
| APIreal: médico | 0,42531708 |
| APIreal: matcher | 0,25486125 |
| APIreal: juiz final + juiz da proposta | 0,16753200 |
| **APIreal todos atores** | **0,84771033** |
| Assinatura: mapa, equivalente de API | 0,42868920 |
| Assinatura: revisores, equivalente de API | 2,80467160 |
| Assinatura: paciente e followup, equivalente de API | 0,92551280 |
| Assinatura todos atores, equivalente de API | 4,15887360 |
| Deployment conforme função histórica | 3,91807786 |

APIreal média0,0423855/caso inclui juízes;0,034do relatório antigo é o braço deployment, excluindo esses custos. Isso é diferença de denominador, não erro financeiro doledger. Deployment somaAPIreal de médico/matcher, estimativas de API dos consultores/revisores pela assinatura e estimativaJEF; não é dinheiro efetivamente debitado na contaOpenRouter.

## Fatura dos exames não inclui todo o atendimento

`Cascade.follow_up` chama `ctx['tools'].inner.execute`, em vez do wrapper deOrderPolicy. Portanto os pedidos do revisor e procedimentos auxiliares de pré-requisito não alteram `exam_cost_usd`, limites por turno ou tiers. Omatcher, quando usado, continua com custo real no trace.

Nos20encontros:21rodadasfollowup;121exames solicitados pelos revisores;136execuções incluindo15procedimentos auxiliares. As respostas incluem29itens de achados,84indisponíveis,23já relatados e7pré-requisitos. A política clínica descrita para o médico não se aplica aesses136passos. O total nominal histórico dos pedidos reviewer sob o classificador antigo seria91860pontos marcadosUS$, sem validação de preço e sem desconto por indisponibilidade/repetição. Esse número serve só para evidenciar o trecho não contado; não é custo hospitalar nem proposta de fatura corrigida.

`OrderPolicy.plan` soma o preço antes de consultar se o exame existe ou foi entregue. Na parte primária,12itens `already_ordered_earlier` apareceram em9chamadas que também exibiram fatura; trêsitens já entregues reapareceram nas filas.37pedidos canônicos repetidos foram cobrados nominalmente, incluindo novealiases com grafia distinta.159itens indisponíveis aparecem nas chamadas primárias com fatura, além de60nas filas. Esses números são problemas de contabilidade simulada, não uma adjudicação de que todo pedido era clinicamente desnecessário.

Apenas89execuções enfileiradas foram recuperadas de mensagens posteriores do médico, com deduplicação por hash do texto integral para não contar o mesmo contexto repetido em todo payload. Não reconstruí uma fila final invisível ao médico. Preços nominais poritem não somam necessariamente a fatura: painéis podem liberar mais deumregistro, e todos os pedidos internos não são eventos individuais.

## Médico pela assinatura foi omitido do deployment

No experimentoHaiku5.5 como médico, uma execução:23chamadas médicas pelaassinatura, equivalente deAPI2,3624102. `deploy_costs` só inclui eventosCLI nas roles `review_claude` e `consult_map`, por isso não inclui o médicoCLI. O resultado `deploy_cost_usd=0,363825924` está incompleto para compararHaikucomo médico comGLM5. Todososatores custaramAPIreal0,06046225 e assinaturaequivalente2,75644500; não sãoUS$decréditos novos.

## Alterações concretas para nova condição

- Definir custos em unidadesRELATIVAS como pedido pelo usuário, fora dosUS$deAPI e estimativasdeassinatura.
- O mesmoregistro contábil deve receber pedidosdomédico, filas, revisores e pré-requisitos. Planejar/faturar só quando algum exame foi realmente entregue no ambiente; `not_available` e `already_ordered_earlier` têm zerocusto de realização, podendo mostrar separadamente a consulta solicitada.
- Usar identidade semântica do exame, espécime e fase para repetir resultados sem nova cobrança. Repetição clínica justificada precisa marcar nova execução/fase; uma mera variação de nome não basta.
- Incluir médicoCLI e eventualprontuário no resumo apropriado de recursos; prontuárioapósresultado deve ficar separado do custo diagnóstico, mas continua no custo total do experimento.
- Reportar custoAPIreal todososatores, estimativadeployment e consumodeassinatura com denominadores explícitos. Não escolher umdenominador menor para apresentar redução de custo.

Essas mudanças devem criar nova condição experimental, preservando os207traces e os resultadosoriginais.
