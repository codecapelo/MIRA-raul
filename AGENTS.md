# MIRA-RAUL — instruções de continuidade

## Objetivo e autorização
Concluir 10 casos publicados × 5 modelos × 1 execução = 50 encontros terminais, com pipeline adaptado de Zhang et al., DOI 10.1038/s41591-026-04609-x. O usuário autorizou OpenRouter pago, paralelismo de todos os casos, retomada automática e publicação em git@github.com:codecapelo/MIRA-raul.git. **Teto global atual: US$18,00**, incluindo pilotos invalidados, paciente, associador, juiz e falhas. Não aumentar o teto ou comprar créditos. Não repetir terminais, mesmo falhas operacionais.

## Fonte de verdade (ler antes de agir)
- `logs/raw/<model>/<case>.jsonl`: eventos `case_complete` são terminais; falha operacional tem diagnóstico/juiz vazios.
- `logs/budget.sqlite`: custos `usage.cost`, reservas e estados pendentes/incertos. Consulta somente leitura enquanto ativo.
- `results/run1.csv`: exportação dos terminais, pode estar alguns segundos atrás dos logs.
- `config/run1.json`: modelos, endpoints fixos, parâmetros e orçamento.
- `logs/background_status.json`, `logs/background_execution.log`: estado do supervisor.
- Processos, `logs/run.lock` e `logs/case_locks/`: verificar antes de lançar. Existência do arquivo não significa lock adquirido.
- `PROTOCOL.md`, `CHANGELOG.md`, `reports/`: decisões, desvios, auditorias. Números em documentos são snapshots.

Checkpoint em 04-10-2026 antes do paralelismo total: 14/50 terminais; GPT-OSS 10/10, demais quatro modelos 1/10 cada. Total conciliado US$0,300752618. Todos os registros do ledger estavam settled. Confirmar novamente; não usar este snapshot como estado vivo.

## Modelos e dados
Médicos: openai/gpt-oss-120b (Mancer FP8), z-ai/glm-4.5-air (Novita BF16), z-ai/glm-5 (StreamLake FP8), qwen/qwen3.5-397b-a17b (Parasail FP8), openai/gpt-5.2 (OpenAI). Paciente usa modelo do médico. Juiz: google/gemini-3.1-flash-lite-preview. Associador: GLM-4.5-Air, raciocínio desativado. Rotas sem fallback; não trocar silenciosamente. Cada requisição inclui usage.include=true.
`cases/` contém os mesmos dez casos públicos do estudo anterior, separados em paciente, investigações, referência e proveniência. Referência só é aberta para juiz após o encontro. Não modificar fatos/prompts/condição durante execução. Não oferecer internet ao médico simulado.
Upstream fixado como submódulo em `upstream/onprem-medical-agents`, commit eea2386c665c9caaa7ee093c8cb092d1c337de88; prompts reaproveitados. Não atualizar submódulo durante a rodada.

## Execução independente da cota Codex
O runner usa Python/HTTP OpenRouter, sem chamadas à assinatura Codex. Uma vez lançado, continua enquanto o Mac e o processo estiverem ativos. Não confundir falta de cota Codex com falta de crédito OpenRouter.
Diretório: `/Users/test/MIRA-RAUL`.
Comando autorizado atual:
```sh
PYTHONPATH=src python3 -u -m mira_runner.runner --execute --parallel-models --parallel-cases 3 --max-workers 12 --allow-commit-transition
```
Todos os encontros restantes entram na fila automática, com os modelos em paralelo (limites: 3 casos/modelo, 12 globais). O lançamento simultâneo de 36 encontrou HTTP429 no Parasail; a concorrência foi reduzida por esse limite observado. O agendador pula terminais. Não lançar outra instância se houver executor/supervisor/worker vivo.
Preferir `python3 scripts/background_run.py` para supervisionar em background; o lançador deve ser iniciado com sessão independente, com saída em arquivo. Ele NÃO faz retries: encerra e registra falha, exporta relatórios. Não repetir lançamento automaticamente sem verificar logs/locks.
O orçamento soma custos reais + reservas de todas as chamadas ativas antes de enviar novas. Estados incertos bloqueiam novos envios. Em erro, workers ativos terminam a chamada em andamento e o agendador não inicia novos trabalhos. Não matar processos apenas porque a conversa acabou.

## Retomada e falhas
1. Inspecionar processos/locks e ledger. Se ativo, apenas acompanhar.
2. Se parado, identificar causa nos últimos eventos. Nunca assumir que um erro HTTP é erro de conta ou diagnóstico incorreto.
3. HTTP sem resposta/custo exige reconciliação: consultar `/api/v1/credits` sem cache, comparar soma do ledger e os IDs/erros. Não imprimir Authorization/chave. Não marcar cobrança incerta como zero sem evidência.
4. Há script explícito `scripts/reconcile_zero_cost.py`; ler seus argumentos e validações. Preservar prefixos e registrar evidência/commit. Retentativas pagas em loop são proibidas.
5. Respostas já pagas só são reutilizadas com hash integral de payload idêntico. `--allow-commit-transition` registra transição; não autoriza mudar prompts/fatos para reaproveitar respostas incompatíveis.
6. Falha do próprio modelo após limite de correção ou de turnos é terminal, com juiz vazio; não rerodar. Erro de provedor/custo não é terminal clínico.
7. Não alterar HEAD durante execução: cada resultado registra commit. Fazer novos commits de implementação antes de relançar.

## Credencial e Git
A credencial fica somente em `.secrets/openrouter.key`, modo0600, pasta ignorada. Nunca copiar para documentos, argumentos visíveis, stdout ou Git. Não ler/exibir tokens de outras contas.
Antes de push, verificar arquivos staged e buscar padrões de segredos sem imprimir os valores. O repositório GitHub é público. Fontes/licenças/atribuições estão em THIRD_PARTY_NOTICES.md e metadados dos casos. Não publicar novos dados pessoais privados.

## Histórico imutável e falhas já resolvidas
- `legacy/`: cópia integral preservada do benchmark anterior (290 terminais). Validar `reports/migration_manifest.json`; não editar.
- `logs/incomplete/technical_invalid_v1` e `results/technical_invalid_v1.csv`: piloto invalidado por ECG liberando ecocardiografia/OCT. Fora do denominador, custos continuam no total.
- Domínios corrigidos: ECG, eco e imagem invasiva separados; guardas bloqueiam incompatibilidades, pedidos livres continuam no associador semântico. Exame físico inicial não devolve pós-operatório.
- Paciente simulado pode inventar narrativa apesar do prompt. Evidências em reports/patient_fidelity_case001_gptoss.md e pilot_quality_audit.md (este último refere-se ao piloto invalidado). Não afirmar fidelidade clínica garantida.
- GPT-OSS e GLM-5 podem não retornar logprobs embora solicitado. Marcar ausente; não inventar ProbScore.
- Turno10 oferece somente admission com tool_choice=auto; seleção forçada não era aceita pelo provedor. Sem admission = falha terminal.
- US$0,0003825 de chamada interrompida foi atribuído por diferença estável da conta, não por usage.cost recebido; documentado em reports/interrupted_cost_reconciliation.json.

## Consolidação obrigatória
Ao haver 50 `case_complete` únicos (inclusive falhas):
1. Executar `python3 scripts/analyze_run1.py`.
2. Conferir CSV, unicidade modelo/caso, custos por ator, falhas separadas de casos julgados, parâmetros/commits/provedores, logprobs efetivamente recebidos.
3. Consultar créditos finais sem cache e reconciliar com ledger/usage.cost; relatar diferenças ou atribuições.
4. Validar hashes legacy e criar manifesto dos novos traces; não misturar pilotos inválidos.
5. Completar README, PROTOCOL, CHANGELOG, reports/summary.md, reports/cost_projection.md e results/run1.csv. Summary: Wilson95%, categorias, custos total/médio, tokens mediana/IQR, comparação histórica lexical rotulada não equivalente, projeção5runs.
6. Revisão médica permanece pendente. Juiz LLM não estabelece segurança clínica ou superioridade. Um run não permite ConsistencyDx.
7. Secret scan, commit e push origin main. Pausar automação `concluir-mira-raul-openrouter`. Avisar usuário com resultados operacionais, custo real e links, sem declarar acurácia clínica definitiva.

## Interrupção do paralelismo em 04-10-2026
A primeira tentativa de 36 workers recebeu HTTP429 de Parasail. A exceção HTTPFailure não era serializável entre processos e derrubou o pool, deixando 36 custos sem resposta. Não retomar sem reconciliação registrada em reports/. Nenhum terminal deve ser repetido. A correção é operacional; não muda mensagens, modelos ou critérios clínicos.

Reconciliação dessa interrupção concluída: reports/parallel_interruption_reconciliation.json e parallel_interruption_checkpoint.md. Três snapshots sem cache confirmaram gasto inalterado US$0,300752618;36 requests sem resposta arquivados com hashes em logs/incomplete/parallel_pool_interruption_v1, custo zero atribuído por conta (não usage.cost observado). Ledger486settled antes da retomada. HTTPFailure corrigido;33testes passaram.

Checkpoint posterior:429 GPT5.2 new-account20RPM conciliadozero (reports/credits_gpt52_rpm_reconciliation.json); gasto US$0,465398503. Client agora espaça envios GPT5.2 em3,5segundos globalmente via SQLite. Prefixos pagos reaproveitados por hash, sem reexecutar terminais.

Checkpoint25/50, US$0,658732568,674settled. Falha na ordenação de commit ausente em evento administrativo corrigida; eventos originais preservados.
