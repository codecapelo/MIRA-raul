# Métricas por regra sobre os traces existentes e congelamento da v5 — 11-11-2026

Sem nenhuma chamada de modelo e sem custo de API. Tudo aqui sai de regras de texto determinísticas aplicadas aos traces já gravados e aos arquivos dos casos (`scripts/rule_metrics.py`). O veredito do juiz LLM aparece só como referência copiada do trace.

**O que estas métricas são:** sinais do processo (o que foi pedido, o que foi entregue, o que se repetiu). **O que não são:** julgamento clínico. Cobertura alta não significa conduta melhor, e um pedido sem resultado no caso não era necessariamente desnecessário. Revisão médica continua pendente.

## Resultado principal

1. **O ganho de acerto entre a v3 e a v5 não veio de o médico coletar mais.** A cobertura de observações pelo médico caiu de 47–55% (v3) para 32–37% (v4 rápida e v5), enquanto o aceite pelo juiz subiu para 10/10. Na v4 rápida e na v5, os revisores levam a cobertura a 55%. Ou seja, o resultado final depende dos revisores.
2. **De um terço a mais da metade dos itens pedidos não existe no caso.** A taxa de "não consta" fica entre 25% e 60% em todas as condições mensuráveis, e é de 57% nos casos públicos da v5.
3. **Resultados de fase posterior chegam ao médico na consulta inicial.** Nos dois Qwen3.8, 49% e 57% das observações de fase posterior foram entregues. Parte do acerto desses modelos reflete compressão temporal.
4. **A repetição de pedidos caiu na v5** (3% dos itens, contra 9–22% na v4).
5. **O juiz deu vereditos opostos para um texto idêntico em 1 de 16 grupos.** É o caso 009 com o GLM-5 (falso, verdadeiro, falso nas runs 1, 2 e 3).
6. **A v5 congelada nunca rodou um conjunto completo.** Os 12 traces da v5z foram gerados no commit `c8cd6be`; o código final (`9ccc23e`) difere em 3 arquivos e 14 linhas.

## Tabela (casos públicos)

| Condição | Encontros | Juiz + / julgados | Cobertura pelo médico | Com revisores | Fase posterior entregue | Itens "não consta" | Itens repetidos | Itens por encontro | História (v5) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Runs 1–3 · gpt-oss-120b | 30 | 10/25 | 40% | – | 8% | 33% | 6% | 14,4 | – |
| Runs 1–3 · glm-4.5-air | 30 | 19/29 | 50% | – | 20% | 43% | 5% | 14,2 | – |
| Runs 1–3 · glm-5 | 30 | 20/30 | 54% | – | 12% | 47% | 10% | 21,3 | – |
| Runs 1–3 · qwen3.5 | 30 | 19/30 | 52% | – | 25% | 41% | 2% | 13,3 | – |
| Runs 1–3 · gpt-5.2 | 30 | 23/30 | 67% | – | 33% | 31% | 8% | 22,5 | – |
| Qwen3.8 max-prime ×3 | 30 | 26/30 | 75% | – | 57% | 34% | 0% | 24,8 | – |
| Qwen3.8 max-0902 ×3 | 30 | 24/30 | 73% | – | 49% | 35% | 0% | 24,2 | – |
| Sonnet 5.5 (assinatura) | 10 | 9/10 | 56% | – | 12% | 36% | 0% | 12,3 | – |
| Opus 5.5 (assinatura) | 10 | 10/10 | 63% | – | 41% | 25% | 0% | 15,7 | – |
| v3 base (GLM-5, 2 trocas) | 10 | 7/10 | 47% | – | 12% | – | 5% | 13,1 | – |
| v3 cascata ×3 | 30 | 27/29 | 46% | – | 18% | 49% | 16% | 12,0 | – |
| v3.2 cascata + JEF ×2 | 20 | 19/20 | 51% | – | 12% | 60% | 8% | 15,1 | – |
| v3.5 | 10 | 10/10 | 55% | – | 18% | 51% | 10% | 17,0 | – |
| v4 Sol | 10 | 9/10 | 45% | 46% | 24% | 36% | 17% | 11,7 | – |
| v4 Sol working | 10 | 10/10 | 42% | 44% | 24% | 38% | 8% | 10,2 | – |
| v4 fast1 | 10 | 9/10 | 33% | 47% | 6% | 40% | 22% | 10,3 | – |
| v4 fast4 | 10 | 10/10 | 32% | 55% | 18% | 51% | 9% | 7,7 | – |
| v5z (7 públicos) | 7 | 7/7 | 37% | 55% | 25% | 57% | 3% | 8,7 | 89% |

Casos fechados (só agregado, v5z, 5 encontros): juiz 4/5, cobertura pelo médico 44%, com revisores 47%, "não consta" 29%, repetidos 8%, história 88%. As v3.6 e v3.7 e os fechados da v4 não entram: os traces ficam fora do Git e não foram lidos nesta rodada.

"–" significa que o trace não permite medir: revisores sem registro da rodada (v3), resultados entregues com atraso dentro de mensagem (v3 base) ou paciente sem ids de fatos (tudo antes da v5).

## Como cada número é calculado

- **Cobertura pelo médico:** uma observação do caso conta como entregue quando o valor registrado aparece, literalmente, no que o médico recebeu (mensagens das requisições dele e saídas de ferramenta). Entrega parcial (um analito de um painel) conta e é marcada. Observações já presentes na primeira requisição saem do denominador.
- **Com revisores:** soma o que a cascata de revisão obteve depois da proposta.
- **Fase posterior entregue:** observações com `available_at` diferente de `time_zero` que chegaram a alguém.
- **"Não consta":** itens respondidos como ausentes do caso, sobre itens pedidos.
- **Repetidos:** itens marcados como já pedidos mais chamadas idênticas, sobre itens pedidos.
- **História:** fatos de `history_facts` cujos ids o paciente da v5 registrou em respostas aceitas.

## Limites

- **Unidade amostral:** são 10 casos públicos. As repetições do mesmo caso são dependentes. Não há intervalo de confiança nesta tabela e não cabe teste entre condições.
- **Denominadores diferentes:** a partir da v3 o exame físico inicial já vem na abertura e sai do denominador; nas runs 1–3 ele precisa ser pedido. Comparar cobertura entre esses dois grupos exige cuidado.
- **História é uma medida grossa:** cada caso tem de 2 a 4 fatos de história, longos e compostos. Os 89% dizem que o paciente usou quase todos, não que a entrevista foi boa.
- **Sem pesos:** ao contrário do ClinVerse (pesos 3/2/1), todos os fatos e observações valem o mesmo. Pesos exigem revisão médica.
- **Diagnóstico ainda é pelo juiz LLM:** os casos não têm códigos ICD-10 (`codes` está vazio), então não há acerto de diagnóstico por regra.
- **Casos de ajuste:** os 12 casos da v5 serviram ao desenvolvimento. Nada aqui é validação.

## Congelamento da v5

`config/frozen/v5.json` registra o SHA-256 de 30 arquivos (todo `src/mira_runner/`, `scripts/run_v5.py`, `config/v5.json`, `config/judge_overrides_v3.json`), as opções lidas do runner e o commit do upstream. O último commit que tocou esses arquivos é `9ccc23e`.

```bash
PYTHONPATH=src python3 scripts/freeze_condition.py --name v5 --check
```

A verificação falha se qualquer arquivo ou opção mudar, e o teste `tests/test_rule_metrics.py` repete essa verificação. Mudança de código passa a exigir um nome novo de condição, com denominadores próprios. O manifesto não é reescrito.

## Como reproduzir

```bash
python3 scripts/rule_metrics.py
```

Esse comando cobre os 430 traces públicos rastreados. Para incluir a v5z, que fica fora do Git, passar `--root v5/v5z=<caminho>/runs/v5/v5z/run1 --cases-dir <caminho>/cases`. Saídas: `results/rule_metrics.csv` (437 encontros públicos, um por linha) e `reports/rule_metrics_summary.json` (48 grupos por condição e modelo, mais o detalhe do conflito do juiz).

## Próximo passo

Rodar a v5 congelada nos casos novos reservados, com 3 repetições, e aplicar estas mesmas métricas. Isso exige autorização de gasto e não foi iniciado.
