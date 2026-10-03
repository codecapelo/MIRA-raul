# Verificação após encerramento solicitado

Verificado UTC: 2026-09-29T00:41:43.987422+00:00. **Execução encerrada pelo usuário; nenhuma retomada autorizada.** Relatório disponível é parcial somente para Luna. Revisão médica pendente.

## Painel

- 150 traces base preservados byte a byte; scores base exatamente iguais aos do relatório anterior.
- 80 novos traces terminais únicos: Sonnet 30, Terra 30 e Luna 20. Total 230, de 240 anteriormente planejados.
- Todos os novos terminais estão no [manifesto adicional](../results/extension_2026-09-28/trace_manifest.json), com SHA-256 e combinação modelo/caso/repetição. O manifesto base não foi substituído.
- Luna: casos 001–006 ×3 e caso 007 ×2. Dez combinações não terminais não foram imputadas.
- Prefixo Luna case007 repetição 3 interrompido por SIGTERM do runner e subprocesso a pedido do usuário: bytes e hash preservados em incomplete/, sem evento terminal sintético, anotação separada. Não é erro de provider.
- Oito tentativas fechadas com erro elegíveis no inventário: Sol 1, Luna 2, Terra 5. Não são runs terminais do painel; custos dos prefixos conhecidos e categorias confirmadas são separados. Inventário histórico não prova ausência de falhas não preservadas.

## Integridade

| Manifesto | Arquivos/traces verificados | Resultado |
|---|---:|---|
| `docs/corpus_freeze_manifest.json` | 50 | Íntegros |
| `docs/protocol_freeze_manifest.json` | 10 | Íntegros |
| `docs/evaluation_freeze_manifest.json` | 7 | Íntegros |
| `docs/protocol_extension_2026-09-28.json` | 3 | Íntegros |
| `docs/protocol_terra_extension_2026-09-28.json` | 2 | Íntegros |
| `results/trace_manifest.json` | 150 | Íntegros |
| `results/extension_2026-09-28/trace_manifest.json` | 80 | Íntegros |

O avaliador da extensão verificou contratos de trace, modelo/esforço solicitados, corpus/protocolo, limites clínicos, combinações e igualdade dos campos base. O root reconferiu hashes, 230 terminais, custo Sol, prefixo interrompido e exports de revisão. Nada no corpus, protocolo clínico ou scorer congelados foi modificado.

## Execução e retomada

Checagem de processos após interrupção não encontrou runner da extensão; locks Luna/Terra estão livres. A ferramenta da aplicação confirmou automação `retomar-benchmark-mira` em **PAUSED**. O usuário pediu análise dos resultados disponíveis; heartbeat antigo não autoriza reiniciar testes após essa instrução. Nenhum reset foi resgatado por agentes; o usuário reiniciou sua cota manualmente.

## Revisão

80 pacotes adicionais cegos em [review_partial](../results/extension_2026-09-28/review_partial/), com 240 linhas para revisão primária, segunda e consenso. Chave em `review_partial_internal/`, separada. Os 150 pacotes base permanecem disponíveis. Esses exports cobrem terminais; prefixos interrompidos precisam revisão clínica separada. Não houve adjudicação médica automática.

## Custos e limites

Proxy Sol **US$ 4,6561284**, sensibilidade US$ 5,1924309, preservados. Terra **US$ 3,038524** para 30 terminais; Luna **US$ 0,1678724** para 20. Sonnet reporta **US$ 7,5722212** e Opus **US$ 18,1708912** via CLI. São equivalentes hipotéticos de API; cobrança real da assinatura não foi observada. Uso da última chamada incompleta é desconhecido. [Consumo](subscription_usage_2026-09-28.md).

Os números diagnósticos são matches automáticos do alvo, não acurácia clínica definitiva. Não demonstram segurança ou validade externa. Public-case contamination, seleção intencional de dez casos, ordem não randomizada, drift de CLI/data, instruções internas diferentes e isolamento estrito não comprovado de ferramentas Codex limitam atribuir diferenças exclusivamente ao modelo. Luna incompleto não entra em inferências pareadas globais.

[Leitura dos resultados](results_interpretation_2026-09-28.md), [relatório](../results/extension_2026-09-28/summaries/PARTIAL_COMBINED_REPORT.md), [comparação MIRA](mira_reference_results.md), [verificação estruturada](extension_verification_2026-09-28.json).
