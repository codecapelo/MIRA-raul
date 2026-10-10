# v5 (desenvolvimento): exames, paciente fiel e erros de operação — 10-10-2026

Plano do Opus 5.5 executado no recorte pedido (exames, fidelidade do paciente, erros de operação), com análise e correção **depois de cada caso**. **Isto é desenvolvimento, não prova**: 12 casos que já tinham servido de ajuste, uma execução por caso, o código mudou entre os casos, juiz LLM, sem revisão médica. Só agregados; nada dos casos fechados (011 a 020) fora do cofre privado.

## O que a v5 faz (opções do `scripts/run_v5.py`, ledger próprio `runs/v5/`, teto US$ 4,80)
- **Exames, versão da v3.6** (política custo-benefício em 3 níveis, associador estrito, roteamento) mais: toda ordem leva `justification` (hipótese e o que o resultado mudaria; fica fora do que os revisores veem); o associador responde com nota (exame que não está no caso, ou resultado que difere do pedido em ensaio, contraste, região, técnica, guia; exame dinâmico nunca respondido por valor basal; nome de analito sozinho não é resultado); resultado de estágio posterior não é obtível (sem dizer o que existe); disjuntor de laço; aviso de estagnação; sincronia entre a fala e o pedido; mínimo de 1 troca com o paciente.
- **Urgência (provisória, regras de IA sem revisão médica):** sinais graves na queixa e no exame inicial (choque, déficit motor e esfíncter, qSOFA, índice de choque, hipoxemia) liberam os exames na hora, o paciente responde em voz de emergência, imagem urgente não é retida por custo, o médico é orientado a falar na primeira mensagem.
- **Paciente: Sonnet 5.5 pela assinatura** com regras estritas e resposta em JSON com os ids dos fatos usados; validador (papel quebrado, ids inexistentes, negativo sem fato, omissão de fato que a pergunta toca), uma regeneração, depois "não sei".
- Médico e associador: Gemini 3.1 Flash-Lite; revisores Sol e Astra pela conta ChatGPT/Codex; juiz Gemini 3.1 Pro (como na fast4).

## Resultado nos mesmos 12 casos (v4 fast4 contra v5 com o código final)
| | v4 fast4 | v5 |
|---|---|---|
| Final correto (juiz) | 12 de 12 | 12 de 12 (a rodada consolidada deu 11; o 012 e o 019 foram refeitos depois das duas últimas correções) |
| Proposta do médico correta | 5 de 12 | 6 de 12 (dentro do ruído; sensível à especificidade da redação) |
| Exames bloqueados por falta de história | 9 | 1 |
| Exames retidos por custo | 2 | 0 |
| Pedidos duplicados bloqueados | 14 | 0 |
| Trocas com o paciente (média) | 4,8 | 3,4 |
| Turnos (média) | 5,1 | 3,9 |
| Primeiro resultado de exame (mediana) | 10,4 s | 9,3 s |
| Tempo até o resultado (mediana) | 108 s | 108 s |
| OpenRouter por caso (todos os atores) | US$ 0,0268 | US$ 0,0255 |
| Paciente, custo equivalente de API | Flash-Lite, cerca de US$ 0,002 | Sonnet 5.5, cerca de US$ 0,040 (pela assinatura, não cobrado) |

Se o paciente Sonnet fosse cobrado pela API, o custo por caso passaria de cerca de US$ 0,026 para cerca de US$ 0,066.

## Fidelidade do paciente (auditoria cega, Opus 5.5 pela assinatura, mesmas perguntas e fatos; 49 respostas v4, 35 v5)
| | v4 | v5 |
|---|---|---|
| Negativos sem fonte | 38 | **0** |
| Quebras de papel | 7 | **1** |
| Detalhes inventados | 6 | 12 (cerca de 7 itens distintos, quase todos floreios leves; um deles se repete em 5 respostas) |
| Omissões de fatos documentados | 17 | 15 (sem melhora relevante: em geral detalhes não volunteados em respostas curtas) |
O ganho é nos negativos inventados e no papel; a invenção leve e a omissão de detalhes continuam. Auditor LLM da mesma família do paciente, sem revisão médica.

## O que cada caso mostrou e foi corrigido (um caso por vez)
1. 008: urgência não reconhecida (sem palavra-chave) e MRI retida por custo → regras de déficit motor e esfíncter; imagem urgente não é retida.
2. 004: lateralidade lida como diferença de região → retirada.
3. 006: resultado "sodium" (só o nome do analito) → falha fechada ou enunciado do associador.
4. 002: resultados de estágio posterior → engine temporal integrada (não foi exercitada nos 12 casos).
5. 005: "postcontrast" não lido como contraste → corrigido.
6. 012: choque séptico não reconhecido e exames travados → qSOFA, índice de choque, oxigênio com taquipneia; falsos positivos da leitura de sinais ("rr" e "hr" dentro de palavras) corrigidos.
7. 011 (**final errado**): uma regra de família da v3.6 fechou o exame específico decisivo do revisor por causa de dois exames genéricos que falharam → regra de subconjunto, revisores isentos; mais aviso de estagnação, pergunta de exposições antes de admitir e checagem de omissão do paciente.
8. 019 (**erro de operação**): a checagem de omissão disparava em falas sem pergunta, o médico respondia ao paciente por 6 turnos e atingia o limite de 10 → só perguntas contam; aviso de turno a partir do 6.
9. 012 (**final errado numa rodada**): o exame decisivo era uma endoscopia e os revisores pediram vias cirúrgicas → a nota do associador sugere outra via para a mesma informação.

## Limites e próximos passos
- Desenvolvimento nos mesmos casos; precisa de casos novos reservados (combinado para depois), 3 repetições e revisão médica cega. As regras de urgência são provisórias.
- A engine temporal e o aviso de "outra via" têm pouca exposição; o disjuntor de laço, a sincronia da fala e o paciente de fallback nunca dispararam.
- A proposta do médico (Flash-Lite) continua em 6 de 12: o acerto final depende dos revisores. Teste do médico mais forte e a lista de hipóteses do plano do Opus ficam pendentes.
- Custo da v5: ledger US$ 0,685754500 = delta da conta (três snapshots sem cache, `reports/credits_v5_final_{1,2,3}.json`); restam US$ 4,114 do teto de US$ 4,80 e US$ 4,157 de crédito na conta.
- Números por caso em `reports/v5_dev_summary.json`.
