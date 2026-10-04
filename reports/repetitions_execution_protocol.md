# Repetições 2 e 3 — 04-10-2026

Autorização: adicionar 100 encontros (5 modelos × 10 casos × 2 repetições), preservando os 50 terminais da primeira rodada e teto global US$18. Cada encontro novo começa sem mensagens/respostas de outra repetição. Os inputs e código clínico continuam os mesmos; a variabilidade decorre de chamadas novas, sem seed adicional.

## Isolamento e concorrência

- `scripts/run_repetitions.py` utiliza diretamente `runner.run_case`, sem alterar prompts, parâmetros, ferramentas ou regras de término.
- Traces e locks de caso ficam em `runs/run2/logs/` e `runs/run3/logs/`. Inputs `cases`, `config`, `upstream` são links para os arquivos congelados da raiz.
- Os resultados são exportados para `results/run2.csv` e `results/run3.csv`; a rodada1 permanece intacta.
- Um único scheduler compartilha o lock global `logs/run.lock`, ledger `logs/budget.sqlite` e o espaçamento por provedor. Limite 3 encontros simultâneos por modelo, somando ambas as repetições, e 15 globais.
- Qualquer estado do ledger diferente de settled bloqueia o início. Falhas durante execução interrompem novas submissões e drenam os encontros ativos; não há loop automático de retry.
- Terminais são pulados mesmo se falha operacional. Prefixos só são retomados pelo mecanismo original de hash integral do payload.

## Continuidade

Executar `PYTHONPATH=src python3 scripts/run_repetitions.py` faz apenas preflight, sem chave ou API.
O supervisor `python3 scripts/background_repetitions.py` executa uma invocação autorizada com `--execute --parallel-cases 3 --max-workers 15 --allow-commit-transition`. Deve ser lançado com sessão independente, após commit, e nunca duplicado se houver processo ativo.
Logs contínuos: `logs/repetitions_execution.log`; estado supervisor: `logs/repetitions_status.json`. Cada novo terminal imprime repetição, modelo, caso, progresso e custo global. Após término, consolidar as três rodadas e manter revisão médica pendente.

## Verificação sem gastos

`tests/test_repetitions.py`: raízes separadas, ledger compartilhado, terminais de run2 não suprimem run3 e limite agregado por modelo respeitado para uma fila de100encontros. Não envia requisições.
