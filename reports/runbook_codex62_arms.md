# Braços Sol 6.2 e Astra 6.2 pela assinatura Codex: roteiro (18-11-2026)

Estado: o braço do Opus 5.5 (variante `glm_opus_v62`) roda nos 8 casos com o balcão v6.2; os dois braços abaixo estão prontos e só falta o Codex CLI aceitar os modelos 6.2.

## O que mudou
O Codex CLI global 0.159.1 recebia `model_not_found` para `gpt-6.2-sol` e `gpt-6.2-astra`. Com autorização do usuário, instalei `@openai/codex@0.170.0` (pacote oficial do npm, cerca de 370 MB com o binário nativo) numa pasta isolada, `~/.local/share/codex-0.170.0`, sem tocar no Codex global. Com ele, as duas chamadas mínimas passam pelo transporte da pipeline (`scripts/codex62_preflight.sh` → `PREFLIGHT_OK`). Os scripts põem essa pasta na frente do `PATH` (`CODEX_BIN_DIR` troca). Cada `cli_call` registra `cli_version`, que passa a ser `codex-cli 0.170.0` nesses braços; o Codex dos braços antigos não roda mais nada aqui.

## Como rodar
```bash
scripts/codex62_preflight.sh
```
```bash
nohup scripts/run_codex62_arms.sh > /Users/test/MIRA-RAUL/.claude/worktrees/complete-remaining-100-cases-356596/runs/v5/v6_qwen/v62_codex62.log 2>&1 &
```
O segundo espera o Opus terminar, repete o teste e roda `sol62` e depois `astra62`.

## Condição dos braços
- Médico GLM 5.3 Flash; balcão v6.2 (`--desk v62`); paciente Sonnet 5.5 pela assinatura; associador e juiz pelo OpenRouter, como nos outros braços.
- `sol62`: `gpt-6.2-sol` nos três pareceres. `astra62`: `gpt-6.2-astra` nos três pareceres. Effort high (`--codex-effort high`, que recompila só o guard do `fast_v4` em tempo de execução; o campo `reasoning_effort` do evento `fast_review_input` continua "medium" por ser texto fixo; o effort enviado está em `cli_call.effort`).
- Casos: 001, 002, 003, 004, 005, 011, 017, 018, uma execução por caso, variantes próprias `glm_sol62_v62` e `glm_astra62_v62`; um terminal não se repete.
- Custo no OpenRouter só do médico, associador e juiz (cerca de US$ 0,02 por encontro, 16 encontros); os revisores Codex ficam na assinatura, custo monetário desconhecido.

## Teto e conta
Ledger `runs/v5/v6_qwen/budget.sqlite`, teto US$ 2,50. Quando o Opus terminar o ledger fica perto de US$ 2,25 e a conta com perto de US$ 0,4 de crédito. Se aparecer `BudgetError`, só você pode subir o teto (backup do ledger e registro em `reports/` como nas subidas anteriores) e conferir o crédito.

## Análise de tempo e latência
```bash
python3 scripts/arm_latency.py --base /Users/test/MIRA-RAUL/.claude/worktrees/complete-remaining-100-cases-356596 --json /tmp/arm_latency.json
```
Mostra por braço: tempo do médico, de cada chamada de revisor, dos seguimentos (paciente e balcão), do juiz, total e a parte do encontro gasta nos revisores. Casos fechados entram só como números.

## Limites
Uma execução por caso por braço, casos conhecidos, juiz LLM, revisão médica pendente. O balcão v6.2 difere do v6 usado nos braços do Qwen e do Kimi: comparar acerto entre braços de balcões diferentes confunde revisor e balcão; para latência a comparação é válida.
