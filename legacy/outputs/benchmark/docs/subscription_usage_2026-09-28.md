# Consumo de assinatura: Luna e Terra

Execução encerrada a pedido do usuário. Não há runner ativo nem retomada automática autorizada. Este documento descreve uso observado, sem inferir cobrança real ou percentual de quota por modelo.

## Tokens observados

Fonte: eventos `usage` dos traces preservados. `input_tokens` já inclui `cached_input_tokens`; `output_tokens` já inclui `reasoning_output_tokens`. Colunas de cache/raciocínio são subconjuntos e não devem ser somadas novamente. Os prefixos de falhas não incluem uso da última chamada que falhou; o prefixo interrompido pelo usuário também não contém uso da chamada ativa no SIGTERM.

| Modelo | Grupo | Tentativas | Respostas | Entrada total | Cache incluído | Saída total | Raciocínio incluído |
|---|---|---:|---:|---:|---:|---:|---:|
| luna | terminal | 20 | 257 | 4,734,032 | 3,960,320 | 101,796 | 77,852 |
| luna | failed_prefix | 2 | 12 | 265,018 | 227,584 | 4,869 | 3,677 |
| luna | user_stop_prefix | 1 | 9 | 161,730 | 60,416 | 2,898 | 2,161 |
| terra | terminal | 30 | 305 | 4,929,392 | 4,295,680 | 75,997 | 50,011 |
| terra | failed_prefix | 5 | 35 | 561,896 | 512,256 | 9,604 | 6,728 |

## Por que isso consome quota

Uma trajetória agentic contém várias decisões sucessivas, não uma única resposta por caso. Terra terminou 30 trajetórias em 305 respostas; Luna terminou 20 em 257. Cada chamada envia o histórico acumulado, descrições de ferramentas e contexto da CLI; o adapter de assinatura executa uma sessão CLI para cada ação EHR. O raciocínio high aumenta trabalho e saída interna; as falhas e a interrupção podem consumir recursos mesmo sem trajetória terminal.

Tokens em cache recebem outra tarifa na estimativa de API, mas isso não prova uma redução equivalente na quota da assinatura. O limite Codex é compartilhado com este trabalho de engenharia/análise e demais tarefas da conta. A plataforma não forneceu fórmula para atribuir a porcentagem usada a cada modelo ou tentativa; não é correto transformar o somatório acima em custo real ou percentual de quota.

Antes da última retomada, a leitura da conta mostrou 1% usado na janela de cinco horas e 16% na semanal. Trata-se de snapshot histórico. Não houve resgate de crédito por agentes; o usuário reiniciou a quota manualmente.

## Retries e integridade

Terra teve 5 tentativas fechadas com erro: 1 timeout, 1 falha de JSON de argumentos confirmada e 3 causas anteriores não confirmadas. Luna teve 2 tentativas fechadas com erro de causa não confirmada e 1 prefixo separado interrompido explicitamente pelo usuário. `OpenAIAccountError` é uma classe genérica do adapter e não demonstra por si só falha de conta, quota ou autenticação.

Os schedulers pulam todas as combinações terminais. Nenhuma combinação concluída foi repetida nesta retomada. Tentativas com erro são preservadas; o último prefixo Luna foi arquivado byte a byte, sem `run_ended` sintético, e não entra no denominador clínico nem na contagem de erros do provider. Não há loop automático ativo.

Reduzir high, cortar o histórico ou mudar o formato de chamadas poderia alterar consumo, mas também mudaria a condição experimental; nenhuma dessas mudanças foi aplicada ao protocolo congelado. Para outra rodada, essas opções exigem um braço novo declarado e autorização do usuário.

## Custos

Os equivalentes de API do [relatório consolidado parcial](../results/extension_2026-09-28/summaries/PARTIAL_COMBINED_REPORT.md) usam tarifas e semântica de cache documentadas. O [Sol](../results/summaries/SOL_COST.md) permanece em US$ 4,6561284. Custos completos das chamadas com erro/interrompidas são desconhecidos; os prefixos conhecidos devem ser relatados separadamente. Assinaturas não produziram fatura API por esses runs.

As contagens tabulares também estão em [JSON](subscription_usage_2026-09-28.json). Revisão médica e segurança das tentativas interrompidas continuam pendentes.
