# Transportes de modelos

Contrato do harness: `generate(messages, tools, config) -> {message, usage, latency_ms, raw}`. O runner normaliza uma única ação EHR por turno e conserva o transporte no trace.

## Anthropic pela conta Claude, sem API

`anthropic.py` usa a **CLI oficial Claude Code 2.1.282** com autenticação de assinatura Claude (`claude auth login --claudeai`), `--model claude-opus-5-5`, `--effort high` e `--print --output-format json`. O CLI não lê credenciais no projeto; o adaptador não acessa tokens, cookies ou chave de API. Antes de cada execução, verifica apenas o booleano de `claude auth status --json`. O modelo só recebe o histórico do caso e os schemas; ferramentas internas e Chrome do Claude Code ficam desabilitados. O harness executa as ações do EHR.

**Estado observado em 25-09-2026:** autenticação oficial pela assinatura concluída (`authMethod=claude.ai`, tipo Pro). A versão anterior 2.1.193 rejeitava Opus 5.5; a CLI foi atualizada pelo comando oficial para 2.1.282. Um preflight sem dados de paciente com `claude-opus-5-5`, esforço `high` e ação estruturada `ping({})` foi bem-sucedido. Acesso a este modelo pela assinatura está verificado. O processo de execução precisa ter acesso ao Keychain do macOS e à rede; uma chamada dentro do sandbox sem ele reporta falsamente `loggedIn=false`.

O canal CLI retorna ações em JSON estruturado, rotuladas `tool_transport=json_emulated`. Ele **não é equivalente** a chamadas nativas de ferramentas da API Anthropic ou do Ollama. Relatórios devem preservar e estratificar o transporte, sobretudo métricas de validade de ferramenta e latência. O CLI pode fornecer contagens de tokens e uma estimativa de custo, mas esta estimativa não corresponde a uma cobrança de API da conta de assinatura.

Uma assinatura `claude.ai`/Claude Code e uma conta Anthropic Console são caminhos de faturamento distintos. O braço solicitado pelo usuário usa a assinatura; não depende de `ANTHROPIC_API_KEY`. O endpoint `GET /v1/models` da API exige Console e não atesta o acesso pela assinatura. [Documentação oficial da CLI e login](https://code.claude.com/docs/en/cli-reference), [catálogo oficial Claude Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/overview).

## Gate de execução

O preflight foi concluído. Antes dos casos, congelar hash de prompt, ferramentas e corpus e executar o runner sob acesso autorizado ao Keychain/rede. Se um run falhar, marcar o erro sem substituição silenciosa de modelo. Não simular resultados Opus 5.5 com outro modelo.
