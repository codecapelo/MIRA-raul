# Registro de modelos e acesso — 25-09-2026

`available_local` significa arquivo instalado **e serviço Ollama consultado**. `catalog_candidate` significa que o modelo consta no catálogo público do fornecedor, **sem prova de direito de uso pela conta/API do usuário**. `codex_host_visible` significa opção apresentada pelo host Codex, sem equivalência com API faturável. Nunca converter essas classes uma na outra.

## Ollama no Mac do usuário

Verificado por `ollama list` e `ollama show`, Ollama **0.34.3**, Mac ARM64, **18 GiB RAM**. Nenhum novo modelo foi baixado.

| ID instalado | ID local abreviado | Tamanho | Arquitetura / parâmetros | Quantização | Contexto declarado | Capacidades declaradas | Estado |
|---|---|---:|---|---|---:|---|---|
| `llama3.1:8b` | `46e0c10c039e` | 4,9 GB | llama / 8,0B | Q4_K_M | 131.072 | completion, tools | `available_local`; inferência e chamada nativa de ferramenta confirmadas |
| `qwen3:8b` | `500a1f067a9f` | 5,2 GB | qwen3 / 8,2B | Q4_K_M | 40.960 | completion, tools, thinking | `available_local`; inferência e chamada nativa confirmadas com `think:false` |
| `qwen3.5:9b-mlx` | `203e30078279` | 8,9 GB | qwen3_5 / 9,4B | nvfp4 | 262.144 | completion, vision, tools, thinking | `available_local`; inferência e chamada nativa confirmadas; pico de memória ainda não medido |

Contexto declarado pelo manifesto **não é** janela efetiva segura no Mac. O runner solicita 24k tokens comuns; essa janela não foi testada até a saturação. Preflights reais em 25-09-2026 confirmaram pelo menos uma chamada de ferramenta nativa em cada modelo, sem dados clínicos; isto não prova uso correto das onze ferramentas no caso. O adapter envia `think:false` uniformemente aos três modelos para obter ações estruturadas em tempo previsível; este controle local não equivale a `high` dos braços frontier e deve constar na comparação. Traces guardam `eval_count`, `eval_duration` e `prompt_eval_count`; RSS/pico de memória e swap ainda são campos não medidos. Execução local serial; nenhuma atualização ou `pull` durante o experimento.

## OpenAI — assinatura ChatGPT/Codex, sem API

A conta ChatGPT do usuário está autenticada no Codex CLI incluído no aplicativo (`codex login status`: “Logged in using ChatGPT”; versão `codex-cli 0.155.0-alpha.16.4` observada em 26-09-2026). O modelo solicitado **`gpt-6-sol` em `high`** passou um preflight de inferência e uma chamada sintética estruturada por `providers/openai.py`. A configuração `model_reasoning_effort='high'` foi aceita. A família GPT-6 aparece no [catálogo oficial](https://developers.openai.com/api/docs/models/all), mas este braço usa a **assinatura pelo Codex CLI**, não a OpenAI API; `OPENAI_API_KEY` não foi encontrado e acesso/faturamento de API não foram verificados.

O adaptador usa `codex exec -m gpt-6-sol` com schema de saída e solicita uma ação EHR por invocação. `tool_transport=json_emulated`: o modelo devolve nome e argumentos em JSON, o runner valida e executa a ferramenta. A CLI tem ferramentas internas, mas o prompt proíbe seu uso e é invocada com sandbox `read-only`, configuração do usuário e regras ignoradas. Isso é **isolamento por instrução e permissão**, não a mesma garantia de uma API sem ferramentas internas; traces devem ser auditados por uso de ferramenta externa. O overhead de inicialização da CLI afeta latência. Temperatura e seed do runner não são parâmetros confirmados para esta modalidade; registrar como não aplicados.

O preflight reportou tokens da CLI e a conta tinha cerca de **5% da janela semanal** ainda disponível às 19:50 UTC de 25-09-2026; os percentuais mudam com uso de outras tarefas. O usuário pediu expressamente **preservar** o crédito gratuito de reset. Se a cota impedir as 30 runs, deixar `access_limited_by_subscription_quota` e retomar após a renovação semanal. Uma automação heartbeat chamada “Retomar benchmark MIRA” foi criada nesta tarefa para isso. Não assumir que limite de assinatura é preço de API.

## Anthropic

O [catálogo oficial Claude](https://platform.claude.com/docs/en/models/overview) consultado em 25-09-2026 lista **Claude Fable 5.1**, **Claude Opus 5.5** e **Claude Sonnet 5** (além de Haiku 4.5), todos com tool use segundo a página de modelos. Propomos `claude-fable-5-1` (raciocínio longo) e `claude-opus-5-5` (comparador frontier); `claude-sonnet-5` é extensão de custo/latência. Confirmar ID/snapshot, janela, esforço e resposta de ferramentas no momento do experimento.

O aplicativo Claude está instalado/aberto no Mac, mas a tentativa de inspecionar sua interface falhou por erro de captura do sistema. A primeira consulta da CLI reportou `loggedIn: false`. Em seguida, o login oficial de assinatura (`claude auth login --claudeai`) foi concluído: `authMethod=claude.ai`, assinatura Pro. A versão 2.1.193 do Claude Code rejeitou Opus 5.5 e foi atualizada pelo comando oficial para **2.1.282**. Um preflight sem dados clínicos com `claude-opus-5-5`, `--effort high`, ferramentas internas desabilitadas e saída JSON estruturada executou `ping({})` corretamente. **Acesso pela assinatura e inferência Opus 5.5 high estão verificados; API Anthropic permanece não verificada e não é necessária para este braço.** O processo deve poder acessar Keychain e rede: uma chamada sob sandbox restritivo reportou falsamente `loggedIn=false`. Não extrair cookies/credenciais do aplicativo.

**Braço solicitado sem API:** o adapter em `providers/anthropic.py` usa o Claude Code CLI 2.1.282 com `--model claude-opus-5-5 --effort high`. As ações são JSON sob controle do harness, com `tool_transport=json_emulated`; esta modalidade deve ser analisada separadamente do tool calling nativo. O ID e o esforço constam no [catálogo oficial](https://platform.claude.com/docs/en/models/opus-5-5/overview). A CLI não expõe controle de temperatura, seed ou máximo de tokens equivalente ao Ollama; registrá-los como **não aplicados**, embora constem na configuração comum solicitada pelo runner.

As contagens por turno incluem tokens de prompt criados em cache e lidos do cache; somar apenas `input_tokens` subestima o consumo. O campo `total_cost_usd` retornado pela CLI é uma **estimativa de custo equivalente**, não cobrança de API em uma assinatura Pro. A latência medida inclui a inicialização da CLI e não é diretamente comparável à latência de um transporte HTTP persistente.

## Matriz de inclusão prevista

| Braço | Modelos alvo | Estado atual | Condição para run |
|---|---|---|---|
| Local | três IDs Ollama acima | instalados | preflight de carregamento, ferramentas e limite de contexto |
| OpenAI assinatura (CLI oficial) | `gpt-6-sol` high | **autenticado e preflight estruturado concluído**, sem API | cota de assinatura e execução sequencial controlada |
| OpenAI API (fora do MVP) | não selecionado | API **não verificada** | autenticação e listagem da conta somente em braço futuro |
| Claude assinatura (CLI oficial) | `claude-opus-5-5` high | **autenticado e preflight de ação estruturada concluído**, sem API | freeze do corpus, execução controlada, monitoramento de limites de assinatura |
| Anthropic API (fora do MVP) | `claude-fable-5-1`, `claude-opus-5-5` | catálogo público; conta/API **não verificada** | chave Console própria, listagem por workspace e preflight se um braço API for autorizado depois |
| Jev opcional para auditoria de gabarito | `jev-latest` conforme código anterior | endpoint documentado; `TYPESAFE_API_KEY` ausente neste processo | chave em secret store e revisão clínica; fora do denominador principal |

Se um frontier não passar no gate, marcar `excluded_access_unverified` ou `excluded_capability`, com razão. Não substituir silenciosamente por modelo mais antigo; atualizar versão do protocolo antes da execução.

## Registro imutável por run

Persistir provider, ID e snapshot retornado, parâmetros enviados/aceitos, versionamento de SDK/API, `prompt_hash`, `tools_hash`, `corpus_version`, data/hora UTC, hardware/Ollama para local, taxa de câmbio e tabela de preços **datadas** se houver custo estimado. Nunca persistir chaves, headers de autorização, cookies ou conteúdo bruto de resposta HTTP que possa conter credenciais.

## Extensão autorizada em 28-09-2026

| Modelo adicional | Configuração | Acesso verificado | Transporte |
|---|---|---|---|
| `gpt-6-luna` | `high`, três runs por cada um dos mesmos dez casos | Autenticação ChatGPT e inferência sintética estruturada aceitas; modelo solicitado, slug servido não exposto | Codex CLI `0.158.0-alpha.2.1`, ação JSON emulada |
| `claude-sonnet-5-5` | `high`, três runs por cada um dos mesmos dez casos | Assinatura Claude Pro, inferência sintética aceita e slug Sonnet observado no envelope | Claude Code `2.1.284`, ação JSON emulada |
| `gpt-5.6-terra` | `high`, três runs por cada um dos mesmos dez casos | Autenticação ChatGPT, catálogo com high e inferência sintética aceitas; slug servido não exposto | Codex CLI `0.158.0-alpha.2.1`, ação JSON emulada |

Os adapters novos copiam os adapters congelados de Sol/Opus, alterando ID e validação do modelo; no Luna, também o caminho do executável que mudou na atualização do aplicativo. A CLI Claude precisou ser atualizada de `2.1.282` para `2.1.284`, versão mínima do Sonnet 5.5. As duas mudanças de versão de CLI e a execução em outra data são covariáveis, não efeito isolado do modelo. A temperatura/seed continuam sem controle efetivo nas CLIs; o esforço é solicitado como `high`.

Evidência e fontes oficiais: [Luna](luna_access_2026-09-28.md), [Sonnet](sonnet_access_2026-09-28.md). Manifest: `protocol_extension_2026-09-28.json`. Os novos traces/progressos ficam em `results/extension_2026-09-28/`; o painel base de 150 runs permanece intacto. O crédito de reset Codex foi usado manualmente pelo usuário em 30-09-2026 para concluir os novos braços; nenhum crédito adicional foi usado pelos runners.

Terra foi solicitado depois do início dos outros dois; [evidência de acesso](terra_access_2026-09-28.md), adapter `providers/openai_terra.py` e manifest `protocol_terra_extension_2026-09-28.json` ficam separados. Seus 30 traces são registrados em `results/extension_terra_2026-09-28/`. O identificador exato é GPT-5.6 Terra, conforme [documentação oficial](https://developers.openai.com/api/docs/models/gpt-5.6-terra), sem substituir por um modelo GPT-6.

## Solicitação adicional de 29-09-2026

Astra 6 high (`gpt-6-astra`) passou preflight estruturado via Codex CLI embutida 0.158.0-alpha.2.1. A imagem do usuário e [ajuda oficial](https://help-lb.openai.com/en/articles/20001275-chatgpt-work-and-codex) confirmam GPT-6.1 Sol como opção distinta no Work/Codex. `gpt-6.1-sol` falhou na CLI embutida, mas passou preflight sintético estruturado em high na CLI oficial npm0.159.1 autenticada. O slug servido não é exposto. Ver [evidência](astra_sol61_access_2026-09-29.md). **Ambos concluíram 30/30 trajetórias terminais**, nos mesmos dez casos e três repetições, via assinatura sem API paga. O painel consolidado tem 290/300 combinações planejadas; Luna permanece 20/30 por interrupção solicitada pelo usuário. A [análise final desta extensão](../results/frontier_addons_2026-09-29/summaries/FRONTIER_ADDONS_REPORT.md) separa taxas de conclusão, triagem lexical de diagnóstico, latência e proxies hipotéticos de tarifa API. Astra: US$ 43,229340; Sol 6.1: US$ 7,003420 para 30 runs cada, sem representar cobrança da assinatura. O usuário usou manualmente o crédito de reset em 30-09-2026. Revisão médica de diagnóstico, conduta e segurança pendente.
