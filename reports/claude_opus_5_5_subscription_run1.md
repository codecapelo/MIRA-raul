# Claude Opus 5.5 (high) pela assinatura: 10 casos × 1 execução — 05-10-2026

Mesmo braço do Sonnet 5.5 (ver `claude_sonnet_5_5_subscription_run1.md`): médico e paciente pelo CLI oficial `claude` (`--effort high`, sem ferramentas próprias, `--safe-mode`, diretório vazio), **ferramentas emuladas em JSON**, sem controle de temperatura/seed/max_tokens; associador e juiz pelo OpenRouter. **Não é equivalente aos demais modelos.** Identidade `claude-opus-5-5` observada em cada chamada. Traces em `runs/claude_opus_5_5/run1/`, CSV em `results/claude_opus_5_5_run1.csv`. **Julgamento por LLM; revisão médica pendente; sem releitura manual; uma execução** (10/10 tem Wilson de 72–100%).

## Resultado
- **10 de 10 corretos pelo juiz**, 0 sem julgamento, 0 erros de ferramenta, sem falhas ou halts.
- **Revisão do juiz:** o caso 001 é um acerto genuíno (diagnosticou pseudoaneurisma coronariano micótico com ruptura/disrupção do stent e tamponade; nenhum Qwen3.8 e só parte dos outros chegou lá). Três acertos são lenientes sob leitura rigorosa:
  - **007:** "AHAI tipo quente, DAT positivo" **sem citar o pembrolizumabe** (não conversou com o paciente nesse caso e não perguntou sobre medicamentos). O juiz aceitou mesmo escrevendo que o gabarito é a etiologia medicamentosa.
  - **002:** "miocardiopatia atrial, possivelmente inflamatória" com BAV completo, sem dizer miocardite.
  - **009:** identificou o stent biliar migrado, sem citar o divertículo de Meckel.
  Sob a regra estrita (exigir fármaco no 007, miocardite no 002, Meckel no 009): **7 de 10** (8 se o 002 for aceito).
- **Conversa com o paciente em 6 de 10 encontros** (casos 001, 003, 004, 005, 009, 010; uma fala cada); sem conversa nos casos 002, 006, 007 e 008.

## Comparação com o Sonnet 5.5 (mesmo braço, mesma régua, 1 execução cada)
| | Sonnet 5.5 | Opus 5.5 |
|---|---:|---:|
| Corretos pelo juiz | 9/10 | 10/10 |
| Regra estrita (007/002/009) | 8/10 | 7–8/10 |
| Caso 001 | errou | **acertou** |
| Caso 007 (fármaco) | acertou, citou o pembrolizumabe | aceito sem o fármaco |
| Caso 009 | stent sem Meckel (leniente) | stent sem Meckel (leniente) |
| Encontros com fala ao paciente | 6/10 | 6/10 |
| Chamadas ao CLI (médico + paciente) | 62 (50 + 12) | 49 |
| Tokens de entrada / saída | 408 mil (407,8 mil em cache) / 41,3 mil | 194 mil (194,1 mil em cache) / 38,5 mil |
| Custo equivalente de API (referência) | US$ 1,19 | US$ 1,85 (1,6×) |
| Tempo | cerca de 6 min | cerca de 5 min |

Com 10 casos e uma execução, a diferença entre os dois **não é conclusiva**: o Opus ganha no 001, o Sonnet no 007, e sob leitura rigorosa os dois ficam em 7–8 de 10, no mesmo patamar do GPT-5.2 (23/30 = 77%) e dos Qwen3.8 sob leitura rigorosa (cerca de 67–73%).

## Consumo medido
- Opus: 49 chamadas, 194 mil tokens de entrada e 38,5 mil de saída, cerca de 5 minutos; consumiu o limite do plano em proporção que o CLI não expõe (conferir no medidor da conta Pro, antes e depois).
- OpenRouter (associador e juiz): US$ 0,0078 no Opus e US$ 0,0063 no Sonnet. Conta = ledger = US$ 8,370711103. Os dois primeiros snapshots finais ficaram 0,0008 abaixo (defasagem transitória da conta); os dois seguintes bateram exatamente.
- O CLI inclui cerca de 4,7 mil tokens fixos de sistema por chamada (em cache); `prompt_tokens` dos modelos Claude no CSV não é comparável com o dos demais.

## Observação
O Opus fechou com menos chamadas ao CLI e menos tokens de entrada que o Sonnet, pedindo mais ferramentas por chamada (média de 7,0 chamadas de ferramenta por encontro contra 6,0 no Sonnet). A leitura "formato novo é compatível com os resultados da Fase 1" (Opus 27/30 e Sonnet 26/30 pela releitura) só se sustenta como ordem de grandeza: formatos, réguas e transportes são diferentes.
