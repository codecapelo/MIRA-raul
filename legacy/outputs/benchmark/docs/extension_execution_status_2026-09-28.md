# Execução encerrada a pedido do usuário

Snapshot UTC: 2026-09-29T00:38:38.837121+00:00. **Luna parcial; não retomar testes sem nova autorização.** Automação `retomar-benchmark-mira` pausada pela ferramenta da aplicação, com confirmação. Locks Luna e Terra livres; checagem de processos não encontrou runners da extensão após SIGTERM do executor Luna e filho.

## Painel disponível

150 trajetórias base + 80 novas = **230 terminais em oito modelos**. Sete braços têm 30 trajetórias; Luna tem 20/30.

| Braço adicional | Terminais / 30 | Concluídas | Erros de provider/runner fechados |
|---|---:|---:|---:|
| luna high | 20/30 | 20 | 2 |
| sonnet high | 30/30 | 30 | 0 |
| terra high | 30/30 | 30 | 5 |

Luna cobre casos 001–006 com três runs e caso 007 com dois. Caso007 repetição 3 e casos 008–010 não têm resultado terminal; não imputar acerto/erro a esses slots. O prefixo Luna interrompido pelo usuário fica separado dos dois erros anteriores: [anotação](../results/extension_2026-09-28/summaries/user_stop_2026-09-28.json). Bytes preservados sem fechamento sintético. Todas as tentativas incompletas ficam fora do denominador clínico.

## Análise e revisão

[Relatório consolidado parcial](../results/extension_2026-09-28/summaries/PARTIAL_COMBINED_REPORT.md): completo para sete braços, parcial para Luna. Os índices/traces são fonte de progresso; este arquivo é snapshot. Métricas são exploratórias e a revisão médica permanece pendente, incluindo condutas dos prefixos interrompidos.

[Consumo registrado](subscription_usage_2026-09-28.md) distingue tokens terminais, prefixos e quota compartilhada sem fórmula de conversão. Proxy Sol de US$ 4,6561284 preservado; custos estimados de API não são cobranças da assinatura. Nenhum crédito de reset foi resgatado por agentes; o usuário reiniciou a cota manualmente em 28-09-2026.

Verificados 50 arquivos do corpus, 10 do protocolo, 7 do avaliador, 5 de runtimes adicionais e 150 hashes base, sem diferenças. [Manifesto adicional](../results/extension_2026-09-28/trace_manifest.json) registra somente 80 novos terminais, preservando o manifesto base.
