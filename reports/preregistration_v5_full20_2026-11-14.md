# Pré-registro — v5 congelada, conjunto completo de 20 casos, 1 execução por caso — 14-11-2026

Escrito **antes** de qualquer chamada. Se este arquivo e o commit dele não existirem no Git antes da primeira requisição, a rodada não é pré-registrada.

## O que esta rodada é e o que não é

- **É** a primeira execução completa da condição v5 congelada (`config/frozen/v5.json`) sobre os 20 casos: 10 públicos (001 a 010) e 10 fechados (011 a 020). Serve de linha de base para as métricas por regra (`scripts/rule_metrics.py`) e para decidir o que melhorar numa v6.
- **Não é validação independente.** Os 20 casos são conhecidos. Doze deles serviram ao desenvolvimento da v5 (001, 002, 004, 005, 006, 008, 009, 011, 012, 018, 019, 020) e todos já passaram por versões anteriores. Os casos novos reservados ainda não existem no repositório e ficam para depois.
- Nenhuma frase do relatório final poderá dizer "validado", "generaliza" ou "superior". Revisão médica continua pendente e o juiz é um LLM.

## Condição

- Runner: `scripts/run_v5.py`, executado a partir do worktree `complete-remaining-100-cases-356596` (branch `claude/v5-exams-patient-fidelity`), HEAD `9ccc23e` = último commit de código do manifesto.
- Manifesto: `config/frozen/v5.json`, SHA-256 do arquivo `e7cbfd3606a58a8eea4c0f1548a23a84b575f99cc741abaad2d57337f1b588b3`.
- Verificação feita em 14-11-2026, antes deste pré-registro: `freeze_condition.py --name v5 --check` sem diferenças, e os 30 arquivos do worktree de execução conferem com o manifesto.
- Modelos: médico e associador Gemini 3.1 Flash-Lite (OpenRouter); paciente Claude Sonnet 5.5 (assinatura, custo equivalente registrado); revisores Sol 6.1 e depois Astra (assinatura ChatGPT/Codex); juiz Gemini 3.1 Pro.
- Nome da execução: variante `v5full1` (`runs/v5/v5full1/run1`, ignorado pelo Git). Ledger próprio `runs/v5/budget.sqlite`, teto US$ 4,80, já gasto US$ 0,685754500.

## Plano

- 20 encontros, **1 por caso**, em ordem crescente de id, um de cada vez (o runner é sequencial).
- Falha operacional ou do modelo é terminal e entra no denominador. Nenhum terminal é repetido; nenhuma chamada é repetida em loop.
- Nenhum arquivo de código ou configuração muda durante a rodada e o HEAD do worktree de execução não muda. Se aparecer um erro, ele é registrado e a rodada segue ou para, sem correção no meio. Qualquer correção vira uma condição nova (v6) e só vale para execuções futuras.
- Parada: guarda de orçamento do runner (conta, ledger e teto), HTTP sem resposta, ou chave sem saldo. Depois de uma parada, só se retoma com reconciliação registrada.

## Medidas (definidas agora)

Desfecho principal: encontros terminais, e aceites do juiz sobre julgados, com intervalo de Wilson 95%, **separados por coorte (público 10, fechado 10)**.

Secundárias, todas de `scripts/rule_metrics.py` sem alteração: cobertura de observações pelo médico e com revisores, entrega de fase posterior, itens "não consta", itens repetidos, itens por encontro, cobertura de história, instabilidade do juiz. Mais custo OpenRouter por encontro e uso das assinaturas (chamadas e tokens).

Casos fechados: só agregados. Nenhum diagnóstico, valor ou trecho de caso fechado em relatório, teste ou mensagem de commit.

## Orçamento e pré-condições verificadas em 14-11-2026

- OpenRouter ativa: `/credits` e `/key` responderam 200. Crédito total US$ 25, uso US$ 20,843347608, restam US$ 4,156652392. Limite da chave US$ 25, restante igual. Variação da conta desde a linha de base = ledger = US$ 0,685754500.
- Estimativa de custo: a v5z custou em média US$ 0,0242 por encontro (máximo US$ 0,0461). Para 20 encontros, cerca de US$ 0,48 e no máximo cerca de US$ 0,92 no OpenRouter. Estimativa, não garantia.
- Ledger com 642 chamadas, todas `settled`, nenhuma reserva pendente. Nenhum processo de runner vivo.

## Depois da rodada

1. `scripts/rule_metrics.py` com a nova raiz; resultado em relatório próprio.
2. Lista do que melhorar, classificada em: erro de medição ou de operação, limite do protocolo, ou hipótese de melhoria. Nada disso altera os resultados desta rodada.
3. Melhorias entram só numa v6 com nome, manifesto e denominadores próprios, e são testadas nos 12 casos de desenvolvimento antes de qualquer caso novo reservado.
