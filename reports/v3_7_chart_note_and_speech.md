# v3.7: prontuário do médico-IA e fala do médico (07-10-2026)

Pedido: (1) o prontuário do médico-IA escrito como um prontuário de verdade, rastreável; (2) a fala do médico mais estruturada e formatada, sem alterar a fala do paciente. Regra: se só com instrução o GLM-5 resolve, não pôr outra IA no fluxo. Nada daqui entra na decisão, nos revisores ou no juiz. Números agregados; os textos dos casos NEJM 011 a 020 ficam só no painel privado.

## Prontuário (8 encontros gravados da v3.6: 001, 004, 008, 013, 016, 018, 019, 020)
Mesma fonte numerada (conversa, pedidos, resultados e admissão, com o horário de cada linha, sem o mapa da consulta) e o mesmo prompt; cada afirmação cita as linhas de origem.

| Medida | GLM-5 só com a instrução | Haiku 5.5 (esforço alto) |
|---|---|---|
| JSON lido sem reparo | 8 de 8 | 4 de 8 (3 com aspas escapadas duas vezes, 1 sem a chave final; todos recuperados) |
| Resultados de exame citados (por código) | 51% | 99% |
| Números fora da fonte citada (por código) | 3 de 242 (1,2%) | 14 de 438 (3,2%) |
| Afirmações sem apoio / contradições / omissões (auditor Sonnet 5.5 às cegas, soma) | 56 / 22 / 77 | 33 / 16 / 57 |
| Organização, estilo, rastreabilidade (1 a 5) | 4,00 · 3,75 · 3,12 | 4,38 · 3,88 · 3,88 |
| Preferido pelo supervisor às cegas | 0 | 8 |
| Tempo mediano | 25 s | 53 s |
| Custo | US$ 0,008 (OpenRouter) | assinatura, cerca de US$ 0,16 em equivalente de API |

Haiku com esforço baixo (mesmos 8): 16 s, resultados citados 86%, seções 6,0 de 8, um prontuário ilegível mesmo com reparo, preferido 0 a 8 contra o esforço alto. Fica o esforço alto.

Decisão: prontuário pelo Haiku 5.5 depois do resultado (`--chart-note claude-haiku-5-5`, grava o evento `chart_note` no trace; falha vira `chart_note_failed` e não altera o encontro), com validação por código. Teste num encontro real (caso 004): prontuário válido, 40 de 40 afirmações com fonte, 15 de 15 resultados cobertos, 39 s depois do resultado, resultado final inalterado.

## Fala do médico
Instrução `SPEECH_FORMAT` (`--speech-format`): texto simples, até 110 palavras, uma frase inicial, no máximo 3 perguntas numeradas depois de "I need to ask:". Mais uma limpeza sem IA (`normalize_speech`) que tira negrito, marcadores e emoji e põe as perguntas uma por linha, sem alterar palavras.

| Medida (última mensagem de cada turno) | Antes (v3.6, 20 casos) | GLM-5 + instrução (5 casos ao vivo) | Haiku reescrevendo (mesmas falas, 5 casos) |
|---|---|---|---|
| Mensagens | 57 | 19 | 10 |
| Formato central cumprido | 1 (2%) | 16 (84%) | 8 (80%) |
| Texto simples | 2 (4%) | 19 (100%) | 10 (100%) |
| Até 110 palavras | 20 (35%) | 17 (89%) | 8 (80%) |
| Tempo extra por mensagem | 0 | 0 | +12 s mediana (máximo 79 s) |
| Conteúdo clínico | n/d | n/d | 28 itens omitidos e 10 acrescentados (auditor) |

Decisão: só o GLM-5, com a instrução e a limpeza. Efeito colateral: nos 5 casos, trocas com o paciente de 2,0 para 3,8 por encontro, implantação de US$ 0,139 para US$ 0,161, exames pedidos de 8,8 para 6,0; final 5 de 5 correto nas duas condições; propostas 3 de 5 nas duas.

## Limites
- 8 encontros no prontuário e 5 na fala (10 mensagens na reescrita do Haiku), uma execução da v3.6; sinal, não prova.
- O supervisor é o Sonnet 5.5, da mesma família do Haiku; por isso as medidas por código estão na tabela (o Haiku ganha na cobertura e perde nos números).
- O critério "I am ordering quando pede exames" estava mal definido para resultados imediatos e exames bloqueados; saiu da medida central.
- A limpeza foi validada nas mensagens gravadas, não ao vivo.
- Reprodução do atendimento no painel (versão 11): horários reais do trace, cronômetro e velocidades; pausas de mais de 2 minutos (retomadas) cortadas e indicadas.

## Custo e conta
Ledger = conta = US$ 18,965410033 em três snapshots sem cache (`reports/credits_v37_final_{1,2,3}.json`); restam US$ 1,03 do teto de US$ 20. Haiku 5.5 como médico, 1 caso (019): resultado final correto, proposta errada como a do GLM-5, 23 chamadas, custo equivalente de API cerca de US$ 2,36 contra US$ 0,04 do GLM-5; não adotado.
