# v5 congelada, 20 casos, 1 execução por caso (`v5full1`) — 14-11-2026

Rodada pré-registrada em `reports/preregistration_v5_full20_2026-11-14.md`. Condição: `config/frozen/v5.json`, HEAD `9ccc23e`. **Os 20 casos são conhecidos e 12 serviram ao desenvolvimento: isto é linha de base, não validação.** Casos fechados (011 a 020): só agregados. Juiz LLM, sem revisão médica.

## Resultado

| | Encontros terminais | Aceitos pelo juiz | Wilson 95% | Proposta do médico correta |
|---|---:|---:|---:|---:|
| Públicos (001–010) | 10 | 9 | 60–98% | 6 |
| Fechados (011–020) | 10 | 8 | 49–94% | 7 |
| Total | 20 | 17 | 64–95% | 13 (43–82%) |

Nenhuma falha terminal por modelo. A diferença entre propostas (13/20) e juiz final (17/20) é o ganho da cascata de revisores.

## Métricas por regra (`scripts/rule_metrics.py`, sem alteração)

| | Públicos | Fechados |
|---|---:|---:|
| Cobertura de observações pelo médico | 40% | 30% |
| Com revisores | 57% | 35% |
| Itens "não consta" | 59% | 37% |
| Itens repetidos | 7% | 3% |
| Chamadas bloqueadas (história antes de exame) | 15% | 9% |
| Itens pedidos por encontro | 8,3 | 11,4 |
| História revelada pelo paciente | 97% | 85% |
| Fase posterior entregue | 18% | – |

Para comparação, a v5z (casos de desenvolvimento, código 3 arquivos antes do congelado): públicos 7/7, cobertura 37% / 55% com revisores, "não consta" 57%; fechados 4/5.

## Custo

Ledger v5 após a rodada: US$ 1,164776375 (1063 chamadas, todas `settled`), isto é, US$ 0,479 nesta rodada, incluindo o parcial do `case_001` (US$ 0,0028) e o parcial do `case_010`. Média por encontro terminal ≈ US$ 0,024. Paciente Sonnet, Sol e Astra pelas assinaturas, custo monetário não medido. Conciliação: logo após o último encontro a conta estava US$ 0,0100 abaixo do ledger (atraso de contabilização já visto antes); minutos depois, três leituras sem cache às 14:08 deram variação da conta desde a linha de base = US$ 1,164776375 = ledger. Restam US$ 3,64 no cap da v5 e US$ 3,69 de crédito na conta.

## Intercorrências (todas fora da decisão clínica)

1. **Sessão OAuth do CLI do Claude expirou** no `case_001` (sem `case_complete`, US$ 0,0028). Login refeito, mesma variante relançada.
2. **HTTP 503 do OpenRouter** durante streaming no `case_010` (83 eventos, sem resposta). Conciliado a custo zero com quatro snapshots iguais e conta = ledger (`reports/v5full1_case010_http503_reconciliation.json`, `scripts/reconcile_http503_zero_cost.py`). O cliente congelado só retoma pedido sem resposta após erro 4xx; o parcial foi arquivado em `runs/v5/v5full1/incomplete/` e o `case_010` recomeçou do zero (o parcial não era terminal).

## O que se vê e o que isso significa

1. **Resultado e reprodutibilidade.** O `case_004`, aceito pelo juiz na v5z, foi rejeitado agora: o texto trocou "quilotórax" por "derrame pleural" e dizia que o envolvimento maligno não estava confirmado. Com uma execução por caso, uma diferença de um caso é ruído. Nenhuma comparação entre condições é possível sem repetições.
2. **O desfecho depende dos revisores.** O médico (Gemini 3.1 Flash-Lite) cobre 30–40% das observações; os revisores levam o conjunto público a 57%. Em quatro dos vinte casos a cascata corrigiu a proposta.
3. **Mais da metade do que o médico pede não existe no caso público (59%).** É limite do protocolo de casos publicados, não necessariamente erro do médico, e é a principal diferença para benchmarks como o SDBench, que devolve resultado sintético.
4. **15% das chamadas públicas foram bloqueadas** pela regra de história mínima antes de exame; vale medir se isso atrasa casos urgentes.
5. **O validador do paciente rejeitou pelo menos uma resposta em 14 de 20 encontros.** A resposta final passa na checagem de fatos (história revelada 97% / 85%), mas o primeiro texto do Sonnet viola as regras em boa parte das vezes.

## Hipóteses de melhoria (nada aplicado; exigem uma v6 com nome novo)

| Tipo | Hipótese | Como testar |
|---|---|---|
| Medição | Repetições: rodar a v5 congelada mais 2 vezes (`v5full2`, `v5full3`) para medir variação por caso antes de mexer em qualquer coisa. | Custo estimado ≈ US$ 0,96, dentro do cap. |
| Operação | Retomada após 5xx e checagem de login antes de lançar. | Mudança de transporte, condição nova. |
| Protocolo | Braço rotulado com resultado sintético para exame ausente, comparável ao SDBench. | Só em braço separado. |
| Médico | Trocar o médico (Flash-Lite) por modelo mais forte mantendo o resto. | Mesmos 20 casos, 3 repetições. |
| Revisão | Reduzir a dependência dos revisores no primeiro ponto de decisão. | Medir ganho dos revisores por caso. |

## Limites

- Casos conhecidos, uma execução por caso, juiz LLM sem códigos ICD-10, sem revisão médica cega.
- A v5z e a v5full1 diferem em 3 arquivos (14 linhas); não somar as duas.
