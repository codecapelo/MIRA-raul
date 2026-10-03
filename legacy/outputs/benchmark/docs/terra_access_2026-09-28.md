# GPT-5.6 Terra high — acesso verificado em 28-09-2026

## Modalidade e isolamento

O braço usa a **assinatura ChatGPT autenticada no Codex CLI oficial**, sem chave de API e sem inferência pela OpenAI API. O harness executa as ferramentas clínicas; o Codex devolve uma única ação JSON em cada invocação. `tool_transport=json_emulated`, portanto este braço deve ser identificado como emulação de chamadas de ferramenta, como as extensões Luna/Sol que usam o mesmo transporte.

CLI: `/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex`, versão **0.158.0-alpha.2.1**. `codex login status` confirmou “Logged in using ChatGPT”. Nenhuma credencial, cookie, token ou conteúdo de identidade do cache foi impresso ou copiado. Nenhum modelo foi baixado. O crédito de reset não foi consumido.

## Modelo, esforço e evidência de disponibilidade

ID fixado: **`gpt-5.6-terra`**, esforço solicitado **`high`**. O catálogo local do cliente, recuperado em `2026-09-28T18:50:46.859707Z` (versão do catálogo `0.158.0`), contém `gpt-5.6-terra` com visibilidade `list` e níveis `low`, `medium`, `high`, `xhigh`, `max`, `ultra`. A [documentação oficial do GPT-5.6 Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra) também especifica o ID e suporte a `high`.

O preflight sintético, **sem dados clínicos**, solicitou `ping({})` pelo adapter com `model_reasoning_effort='high'`. Resultado: uma chamada `ping` com argumentos `{}`, zero eventos de erro da CLI, transporte JSON emulado e latência medida de **5.939 ms**. A CLI reportou 13.791 tokens de entrada, 27 de saída, zero de entrada em cache e zero tokens de raciocínio reportados. Esses números incluem o transporte/overhead da CLI; zero tokens de raciocínio neste probe trivial não demonstra ausência de raciocínio nos casos.

O retorno verifica que a conta aceitou a inferência com o ID/esforço solicitados. A CLI não retornou snapshot interno separado, logo não declarar verificação de snapshot ou equivalência com um endpoint API. Temperatura, seed e teto de saída pedidos pelo runner não são controles confirmados desta modalidade; o adapter não os converte silenciosamente em parâmetros suportados.

## Adapter e integridade

`providers/openai_terra.py` é uma cópia **exata** de `providers/openai_luna.py`, com apenas `GPT-6 Luna → GPT-5.6 Terra` e `gpt-6-luna → gpt-5.6-terra`. Classe exportada: `OpenAIProvider`; assinatura e resposta são idênticas às da extensão Luna. Mantém sandbox `read-only`, `--ephemeral`, `--ignore-user-config`, `--ignore-rules`, schema de saída e proibição de ferramentas internas no prompt.

| Artefato | SHA-256 no preflight |
|---|---|
| `providers/openai_terra.py` | `ffce9225043e62527cd2b121a357afd415daaf27afd346c87189f169b64d503e` |
| `providers/action_schema.json` | `21dbc529a2279b7ae79359787a1dd7a63861339c8ebc11cad28f1e568937f20d` |

O protocolo base congelado e os arquivos das extensões Sonnet/Luna não foram modificados. As 30 runs Terra terão manifest, diretório e registro de execução separados, mantendo os mesmos dez casos e protocolo v5. **Nenhum caso Terra foi executado durante este preflight.**

## Custo equivalente e limites

As tarifas API oficiais consultadas pelo responsável pelo protocolo em 28-09-2026 são US$ 2/M tokens de entrada, US$ 0,20/M entrada em cache e US$ 12/M saída; escrita de cache, 1,25× entrada = US$ 2,50/M. Para prompts acima de 272k tokens de entrada, aplicar 2× entrada e 1,5× saída conforme a documentação. Esses preços podem alimentar somente uma **estimativa equivalente**, datada; não representam cobrança de API deste braço por assinatura. [Fonte oficial](https://developers.openai.com/api/docs/models/gpt-5.6-terra).

Disponibilidade futura depende da cota compartilhada da assinatura. Falha de cota deve ser registrada e retomada sem repetir runs concluídas; não substituir modelo, usar API nem consumir crédito de reset como recuperação automática.

## Estado de execução após a primeira sessão

A extensão congelada `docs/protocol_terra_extension_2026-09-28.json` iniciou as 30 runs pelo protocolo base v5. **Sete combinações únicas terminaram**, todas com `stopping_reason=completed`; 23 permanecem pendentes. Houve duas tentativas técnicas preservadas em `results/extension_terra_2026-09-28/incomplete/`: um timeout de 600 s no fechamento de `case_002`, repetição 3, recuperado na tentativa seguinte; e um erro genérico do transporte na primeira chamada de `case_003`, repetição 2, antes de qualquer ação. Não repetir runs terminais.

Uma única inferência sintética sanitizada após a segunda falha retornou com exit code 0, sem marcadores de quota, rede, autenticação ou indisponibilidade de modelo. A causa da falha clínica transitória não foi confirmada. A consulta de uso naquele momento reportou `ordinaryUsageAllowed=true`, 96% usados na janela de cinco horas, 33% na semanal e um crédito de reset ainda disponível. O processo encerrou e a continuação pelo mesmo scheduler foi autorizada após o probe bem-sucedido, sem usar o crédito.

Validação final desta sessão: manifest e arquivos congelados íntegros; sete traces terminais, sete pares caso/repetição distintos, **70 respostas com `model_requested=gpt-5.6-terra` e `effort_requested=high`**. `model_observed` continua indisponível. As sete runs somaram 1.123.621 tokens de entrada reportados, incluindo 889.344 em cache, e 17.547 tokens de saída; duração média de 117,93 s por run. Esses totais excluem tentativas incompletas e probes. Índice: `results/extension_terra_2026-09-28/summaries/terra_progress.jsonl`; log: `results/extension_terra_2026-09-28/logs/terra_runner.log`.

`review_state=pending`: conclusão do fluxo não significa acerto diagnóstico ou segurança clínica adjudicada. Nenhuma acurácia clínica definitiva foi calculada nesta etapa.
