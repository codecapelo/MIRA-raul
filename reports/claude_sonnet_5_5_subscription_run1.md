# Claude Sonnet 5.5 (high) pela assinatura: 10 casos × 1 execução — 04-10-2026

Braço de assinatura executado a pedido do usuário para medir consumo antes de decidir sobre o Opus 5.5. **Não é equivalente aos demais modelos**: médico e paciente rodaram pelo CLI oficial `claude` (`--effort high`, `--tools ""`, `--safe-mode`, diretório vazio) com **ferramentas emuladas em JSON**, não tool use nativo da API; o CLI não aceita temperatura, seed nem max_tokens; associador (GLM-4.5-Air) e juiz (Gemini 3.1 Flash-Lite) seguiram pelo OpenRouter, idênticos aos outros modelos. Identidade do modelo observada em cada chamada (`claude-sonnet-5-5`). Traces em `runs/claude_sonnet_5_5/run1/`, CSV em `results/claude_sonnet_5_5_run1.csv`. **Julgamento por LLM; revisão médica pendente; sem releitura manual.** Uma única execução: serve para calibrar, não para ranquear (9/10 tem Wilson de 60–98%).

## Resultado
- **9 de 10 corretos pelo juiz**, 0 sem julgamento, 0 erros de ferramenta, nenhuma falha ou halt. Errou o caso 001 (propôs êmbolo séptico coronariano com infarto e hemopericárdio em vez de pseudoaneurisma coronariano infectado com ruptura de stent).
- **Conversa com o paciente em 6 de 10 encontros** (12 falas do paciente no total), mais do que os Qwen3.8 (23% e 7%) e menos que os modelos que mais conversam. Os 4 encontros sem conversa foram os casos 001, 002, 004 e 008. Nos casos em que perguntou, **citou o pembrolizumabe no 007** (que os Qwen3.8 perderam) e identificou o **stent biliar migrado no 009** (que nenhum Qwen3.8 acertou sem pedir o achado cirúrgico).
- **Revisão do juiz:** sem falso negativo evidente. Um acerto é leniente sob leitura rigorosa: caso 009 (identificou o stent migrado com possível perfuração, **sem citar o divertículo de Meckel**), o que daria **8/10 pela regra estrita**. Caso 002: nomeou "miocardite atrial isolada", coerente com o gabarito. Casos 007 e 010 aceitáveis.
- Comparação: Fase 1 (outro formato, releitura do autor) Sonnet 5.5 acertou 26/30 (86,7%); aqui 9/10, mesma ordem de grandeza, mas formatos e réguas diferentes.

## Consumo medido
| Item | Valor |
|---|---|
| Encontros / chamadas ao CLI | 10 / 62 (50 do médico, 12 do paciente) |
| Tempo de execução (2 encontros em paralelo) | cerca de 6 minutos |
| Tokens de entrada reportados pelo CLI | 408 mil, dos quais 407,8 mil em cache |
| Tokens de saída | 41,3 mil (inclui raciocínio em high) |
| Custo equivalente de API (referência, não é cobrança) | US$ 1,19 (médico 1,06; paciente 0,13) |
| Gasto no OpenRouter (associador + juiz) | US$ 0,0063; conta = ledger = US$ 8,362879588 |

Cada chamada do CLI reenvia o contexto inteiro (prompt de sistema, definições de ferramentas e conversa) mais a sobrecarga do próprio CLI; o menor prompt observado foi de cerca de 2 mil tokens (paciente) e 3 mil (médico) e a média das chamadas do médico foi de 7,4 mil no Sonnet e 4,2 mil no Opus, quase tudo vindo de cache. Por isso `prompt_tokens` dos modelos Claude no CSV não é comparável com o dos demais.

## Para decidir o Opus 5.5
Mesma forma de execução com o Opus 5.5 deve produzir tokens parecidos (um pouco mais de raciocínio) e custo equivalente de API da ordem de 2× o do Sonnet (cerca de US$ 2–3); o Opus pesa mais no limite do plano que o Sonnet, então o percentual do Sonnet no medidor é um piso, não uma proporção. Sem retries automáticos: se o limite estourar, a execução para e retoma depois sem repetir chamadas já respondidas.
