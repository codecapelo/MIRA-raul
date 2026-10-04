# Intercorrências nas runs 2 e 3 — 04-10-2026

Resultado: nenhuma interrupção alterou terminais, prompts, parâmetros ou provedores. Os terminais não foram repetidos; cada chamada perdida foi refeita uma única vez após reconciliação.

## 1. Timeout de rede (16:34 UTC)
- 13 chamadas da run 2 (11 de médico e 2 de paciente) enviadas entre 16:20:41 e 16:20:48 expiraram juntas no limite de 800 s (leitura sem resposta, conexões congeladas). Eventos `halt` com razão `timeout`.
- Ledger: 13 linhas `uncertain` (reserva total US$ 1,168). Três snapshots de créditos sem cache (`credits_run23_timeout_*.json`) estáveis em US$ 2,479821028 contra US$ 2,449167718 no ledger: **diferença de US$ 0,030653310**, cobrança de chamadas perdidas, impossível de atribuir a uma delas.
- Reconciliação (`scripts/reconcile_timeout_interruption.py`, `reports/run23_timeout_reconciliation.json`): backup do ledger (`budget_before_timeout_reconciliation.sqlite`), traces integrais arquivados com hash em `logs/incomplete/run23_socket_timeout_v1/`, cauda `request+halt` removida dos traces vivos, 13 linhas liquidadas a custo 0 e a diferença registrada **uma vez** na linha `unattributed_interrupted_calls`. Nenhum `usage.cost` de provedor foi inventado. Ledger passou a ser igual à conta.

## 2. HTTP 429 do Qwen/Parasail (16:49 UTC)
- Uma chamada de paciente (run 3, case_002) rejeitada em 0,6 s: "temporarily rate-limited upstream" (pool compartilhado do provedor).
- Três snapshots (`credits_run23_429_*.json`) com uso da conta exatamente igual ao ledger (US$ 3,736168178): sem cobrança. Mesmo procedimento; arquivo em `logs/incomplete/run23_http429_v1/`, evidência em `run23_http429_reconciliation.json`.

## Fechamento financeiro
Após o término, três snapshots finais (`credits_run23_final_*.json`) mostram uso US$ 4,274237323 = ledger. Um primeiro snapshot logo após o término mostrou US$ 4,266788823 e convergiu em um minuto: defasagem transitória da contabilização da conta, como já observado.

Limitação: a latência de encontros retomados reflete tempo de parede incluindo a espera do timeout. Revisão médica pendente.
