# Escalonamento v2: revisor às cegas, pedidos antes da decisão, resultados imediatos (05-10-2026)

Mudanças em relação à primeira versão (`v3_cascade_pilot.md`): (1) se o revisor lista perguntas ou exames que faltam, uma rodada é executada antes de aceitar; (2) o revisor do nível 2 **não vê a proposta** do GLM-5; (3) o nível 2 passa a ser o Sonnet 5.5 pela assinatura Pro (variante `cas`) ou o Qwen3.8 com raciocínio baixo e teto de 6.000 tokens (variante `casq`, Sonnet no nível 3); (4) a pergunta "mesmo diagnóstico" do JEF ficou tolerante a detalhe extra, e quando o árbitro escolhe um dos candidatos isso conta como decisão; (5) o árbitro (Opus 5.5 pela assinatura) vê a transcrição e os dois candidatos. Por pedido do usuário, os resultados dos exames agora voltam **na hora** (`--immediate-results`). GLM-5 conduz a entrevista com N=2 e exame junto da queixa. 10 casos × 1 execução por variante, juiz final Gemini 3.1 Pro. **Julgamento por LLM, sem revisão médica; uma execução por caso.**

## Resultado
| | Proposta do GLM-5 | Final do escalonamento | Custo de implantação por encontro | Por caso resolvido |
|---|---:|---:|---:|---:|
| **`cas`: Sonnet às cegas → Opus** | 5/10 (4 de 9 julgados erradas)* | **8/10** | US$ 0,068 (OpenRouter US$ 0,009 + Claude equiv. API US$ 0,059) | US$ 0,085 (só OpenRouter, com Claude pela assinatura: US$ 0,012) |
| `casq`: Qwen baixo → Sonnet → Opus | 7/10 | 7/10 | US$ 0,022 | US$ 0,032 |
| Escalonamento v1 (rodada anterior) | 7/10 | 7/10 | US$ 0,054 | US$ 0,077 |
| GLM-5 sozinho (N=2, rodada anterior) | 7/10 | n/a | US$ 0,014 | US$ 0,020 |
| Qwen sozinho (N=2, rodada anterior) | n/a | 9/10 | US$ 0,078 | US$ 0,086 |
*O caso 003 caiu por falha de ferramenta do GLM-5 (argumentos inválidos duas vezes) antes de qualquer revisão e conta como não resolvido.

## `cas`: o que o Sonnet às cegas mudou
- **Corrigiu 3 propostas erradas e não estragou nenhuma certa:** casos 001, 002 e 010. Em 001 e 002, o Sonnet pediu exames e perguntas que faltavam (rodada de pedidos executada: 4 exames no caso 001, 4 no 002, 3 no 010), o Opus arbitrou e escolheu o diagnóstico do revisor às cegas.
- **Não corrigiu o caso 009** (stent migrado no divertículo de Meckel): a triagem do JEF aceitou a proposta com escore 0,913 e nenhum revisor foi chamado, como na primeira versão.
- **Quem foi chamado:** a triagem do JEF aceitou 3 de 10 (005, 006, 009); o Sonnet revisou 6 (001, 002, 004, 007, 008, 010) com pedidos extras em todos; o Opus arbitrou 3 (001, 002, 008, e em 008 escolheu a proposta original).
- **Custo dos Claude** (equivalente de API): Sonnet US$ 0,409 em 12 chamadas (cerca de US$ 0,034 cada), Opus US$ 0,179 em 3 (cerca de US$ 0,060 cada), 87% do custo de implantação. A entrevista do GLM-5 custou US$ 0,0995 nos 10 casos (US$ 0,010 por encontro, menos que antes porque os resultados voltam na hora e usou 3 a 5 turnos).

## `casq`: por que o Qwen barato não ajudou
O Qwen às cegas concordou com o GLM-5 em 8 de 10 casos, inclusive nos 3 errados (001, 002, 009): são modelos que erram do mesmo jeito, então a concordância não é evidência. Nenhum caso chegou ao Sonnet ou ao Opus. Custou US$ 0,0097 por revisão (12 chamadas) e não mudou nenhum resultado.

## Ressalvas
- 10 casos, uma execução por variante: a proposta do GLM-5 variou entre rodadas (7/10 antes, 5/10 aqui), então parte da diferença é ruído. A comparação mais firme é dentro da mesma rodada: o final da `cas` corrige 3 das 4 propostas julgadas erradas sem estragar as certas.
- O revisor às cegas vê as falas do médico na transcrição, que podem citar hipóteses; a ausência de âncora não é total.
- O custo dos Claude é o equivalente de API medido pelo CLI; pela assinatura Pro o custo marginal no OpenRouter é zero, mas há limite de uso do plano e o percentual consumido não é legível.
- Os limiares (JEF 0,90; confiança 0,70; concordância 0,50) foram escolhidos em dados anteriores e não foram reotimizados.

## Gasto
Ledger e conta: US$ 14,353 → 14,815 (US$ 0,462; o primeiro snapshot ficou US$ 0,0445 abaixo por atraso transitório da conta e os dois seguintes bateram com o ledger; `credits_v3_cascade2_final_*.json`). Restam cerca de US$ 3,18 do teto de US$ 18.
