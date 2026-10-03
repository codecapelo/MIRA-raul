# Acesso Claude Sonnet 5.5 high — extensão 2026-09-28

## Identidade e comparabilidade

Braço adicional solicitado pelo usuário: `claude-sonnet-5-5`, esforço explícito `high`, 10 casos × 3 repetições, pela assinatura existente do Claude. Resultados devem permanecer em `results/extension_2026-09-28`, separados do painel original de 150 runs.

O identificador exato consta no [catálogo oficial Anthropic](https://platform.claude.com/docs/en/models/overview). O Claude Code documenta suporte a `high` no Sonnet 5.5 e exige CLI **2.1.284 ou superior** para esse modelo. A flag `--effort high` fixa a solicitação de esforço; a documentação explica que a escala é calibrada por modelo e que caps administrativos podem reduzir o esforço. Portanto o envelope sanitizado comprova o **esforço solicitado**, não expõe uma medida de raciocínio nem comprova independentemente ausência de caps. [Configuração oficial de modelos e esforço](https://code.claude.com/docs/en/model-config).

`providers/anthropic_sonnet.py` é uma cópia do adapter Opus congelado. A comparação textual confirmou que as únicas mudanças são a docstring inicial e a substituição de `claude-opus-5-5` por `claude-sonnet-5-5` no default e na validação. Classe, prompt, esquema JSON, normalização, timeout, flags e tratamento de erros são idênticos. Compilação Python verificada sem criar pycache.

| Arquivo | SHA-256 |
|---|---|
| `providers/anthropic.py` original preservado | `b26c0b378605637cbc78c78145b98fb2309fc35b1115da0ada38a950cdcc919d` |
| `providers/anthropic_sonnet.py` extensão | `898b6cc4b5cd3caa1505f4b3c916581ea6f6028f0db4dcdf2dbfc15f70c4f3c4` |

O transporte continua `claude_code_subscription_cli_json_action`, com `tool_transport=json_emulated`. O harness executa as ferramentas EHR; ferramentas próprias do CLI, navegador e persistência de sessão são desativados. Este braço conserva a emulação JSON do Opus e do painel comparável, sem equivalência presumida a chamadas nativas da API nem ao ambiente FHIR original MIRA.

## Verificação live sanitizada

Em 2026-09-28, o CLI instalado ainda era **2.1.282**. A exigência oficial de versão tornou necessário executar `claude update`, concluído com **2.1.284**. O adapter e corpus congelados anteriores não foram alterados. A mudança de versão do transporte deve constar como covariável da extensão em relação ao Opus anterior.

`claude auth status --json` foi processado por allowlist; email, organização e identificadores pessoais foram descartados antes de impressão. A execução precisou de acesso normal do processo oficial ao Keychain macOS fora do sandbox de arquivos. O adapter não extrai material OAuth e nenhum API key foi utilizado.

```json
{
  "verified_at": "2026-09-28T18:37:51.260563+00:00",
  "status_exit": 0,
  "loggedIn": true,
  "authMethod": "claude.ai",
  "apiProvider": "firstParty",
  "subscriptionType": "pro",
  "cli_version": "2.1.284 (Claude Code)"
}
```

## Preflight não clínico

Um único preflight solicitou `ping` com `value=pong`, usando o adapter novo e uma ferramenta fictícia. Nenhum caso clínico foi enviado neste preflight. O modelo retornado foi conferido pelo campo `modelUsage` do envelope, que a [documentação oficial](https://code.claude.com/docs/en/model-config) recomenda para identificar o modelo efetivamente usado no output JSON.

```json
{
  "verified_at": "2026-09-28T18:38:36.157665+00:00",
  "message": {
    "role": "assistant",
    "content": "{\"tool\": \"ping\", \"args\": {\"value\": \"pong\"}}",
    "tool_calls": []
  },
  "latency_ms": 3091,
  "usage": {
    "input_tokens": 2,
    "cache_creation_input_tokens": 1273,
    "cache_read_input_tokens": 0,
    "output_tokens": 113,
    "output_tokens_details": {"thinking_tokens": 0},
    "server_tool_use": {"web_search_requests": 0, "web_fetch_requests": 0},
    "cache_creation": {"ephemeral_1h_input_tokens": 1273, "ephemeral_5m_input_tokens": 0},
    "service_tier": "standard",
    "speed": "standard"
  },
  "raw": {
    "transport": "claude_code_subscription_cli_json_action",
    "tool_transport": "json_emulated",
    "subtype": "success",
    "model_requested": "claude-sonnet-5-5",
    "models_reported": ["claude-sonnet-5-5"],
    "effort_requested": "high",
    "cost_estimate_usd": 0.006226,
    "temperature_accepted": false,
    "seed_accepted": false,
    "max_output_tokens_accepted": false
  }
}
```

Não houve erro de uso, quota ou HTTP429 no preflight. **Quota restante não é observável nessa resposta**: sucesso de um ping não garante capacidade para 30 runs. O scheduler deve preservar falhas e interrupções, sem substituição silenciosa de modelo. Ausência de thinking tokens no ping simples não invalida a solicitação high; raciocínio adaptativo pode dispensar pensamento nessa tarefa.

`total_cost_usd`, exposto como `cost_estimate_usd`, é uma estimativa do CLI. Não equivale a cobrança API real nem a custo marginal demonstrado da assinatura. Tokens de input ordinário, criação e leitura de cache devem continuar em campos separados. Latência inclui inicialização do subprocesso. Não se fixam temperatura, seed ou teto de saída quando não suportados por este transporte.

## Limite da verificação

O preflight confirma autenticação por assinatura, acesso ao identificador solicitado e resposta estruturada sob flags idênticas ao adapter Opus. Não mede qualidade clínica nem conclui a extensão. Os 30 casos/repetições só serão iniciados após freeze do manifest de extensão e sinal do coordenador. Todos os arquivos congelados v5, traces e relatórios originais foram preservados.

## Execução concluída após autorização do freeze

Após sinal do coordenador, `python3 -B -m runner.run_extension --model claude-sonnet-5-5` executou o manifest `mvp10_extension_sonnet_luna_2026-09-28`, corpus `mvp10_v3_2026-09-26`, protocolo base `mvp10_closedbook_v5_2026-09-26`. Scheduler encerrou normalmente com exit code 0.

Auditoria de execução: **30/30 combinações únicas caso/repetição**, todas `completed`, todas na primeira tentativa, zero falhas do provider/runner e zero `invalid_model_outputs`. Não houve repetição de terminais. Os 335 eventos `model_response` reportaram exclusivamente `claude-sonnet-5-5`. Os 335 eventos separados `usage` contêm `server_tool_use`: somas de `web_search_requests=0` e `web_fetch_requests=0`; todas as 335 iterações declaradas têm tipo `message`. Ferramentas próprias do CLI continuaram desativadas pelas flags congeladas. A verificação final do manifest e dos hashes dos adapters passou.

| Contador nativo dos 335 eventos usage | Total |
|---|---:|
| Input ordinário | 980 |
| Criação de cache | 1.442.387 |
| Leitura de cache | 1.347.916 |
| Output | 153.113 |
| Thinking, subconjunto do output | 37.896 |
| Criação cache 1h, subconjunto da criação | 1.442.387 |
| Criação cache 5min | 0 |

Soma das estimativas `cost_estimate_usd` dos 335 responses: **US$ 7,5722212**. Trata-se de API-equivalent estimate do CLI sob assinatura, sem fatura API demonstrada. Soma de elapsed dos 30 runs: **1.857.889 ms (30,965 minutos)**, incluindo subprocessos e workflow. Esses contadores excluem o ping de preflight.

Índice preservado: `results/extension_2026-09-28/summaries/sonnet_progress.jsonl`. Traces preservados em `results/extension_2026-09-28/raw/`; log do scheduler em `results/extension_2026-09-28/logs/sonnet_runner.log`. Conclusão do workflow não equivale a acurácia, conduta adequada ou segurança clínica; os 30 runs mantêm revisão médica pendente.
