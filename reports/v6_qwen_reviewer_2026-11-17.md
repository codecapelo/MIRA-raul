# Qwen4 Max como revisor, GLM 5.3 Flash como médico — 17-11-2026

Braço sobre o v6 congelado (mesa Gatekeeper v6, paciente Sonnet 5.5 pela assinatura, associador, juiz), código em `scripts/run_v6_qwen.py`. **Oito casos preparados (001 a 005, 011, 017, 018), uma execução por caso, casos conhecidos, juiz LLM, revisão médica pendente.** Casos fechados (011, 017, 018) só em agregado aqui; o detalhe fica no painel privado e nos diálogos locais.

## Condição
- Médico `z-ai/glm-5.3-flash` (Z.AI fp8, rota fixa). Revisores: `qwen/qwen4-max` (OpenRouter, rota única Alibaba, quantização não informada, US$ 1,425 / 4,275 por milhão, raciocínio `effort=high`, `max_tokens` 16000, amostragem padrão do provedor) nas duas posições (`--slot both`: 1ª leitura, leitura depois do seguimento e leitura final). O texto do raciocínio vem em cada resposta e fica no evento `response` do trace.
- Variante com Qwen só na primeira posição e Opus 5.5 (assinatura) como final: apenas o caso 011 (`--slot first`).
- Ledger próprio `runs/v5/v6_qwen/budget.sqlite`, teto US$ 0,60, **subido para US$ 1,00 por decisão do usuário** (`reports/v6_qwen_cap_raise_1usd.json`).

## Resultado agregado
| | Casos | Juiz aceitou | Proposta do médico certa |
|---|---:|---:|---:|
| Públicos (001 a 005) | 5 | 4 | 3 de 4 com registro |
| Fechados (011, 017, 018) | 3 | 3 | 2 |
| Total | 8 | 7 | 5 de 7 com registro |

Nos 7 casos em comum com o GLM da v6 (Sonnet e Fable), o Qwen sozinho teve 6 aceitos contra 7. Custo médio US$ 0,063 por encontro no OpenRouter (v5: 0,027), dos quais cerca de 67% são do revisor (≈ 2,4 a 8,5 mil tokens de raciocínio por encontro). Notas 1–5 (mesma rubrica de rascunho): Gemini 3.1 Pro e Claude Sonnet 5.5 como segundo juiz; as duas notas coincidem com o veredito binário (≥ 4 = aceito).

## Custo e reconciliação
Ledger do teste US$ 0,582125 em 251 chamadas, todas `settled`. Snapshots sem cache: gasto da conta desde a linha de base US$ 0,635781, diferença de US$ 0,053656 = juiz de 1 a 5 (Gemini 3.1 Pro pelo OpenRouter, fora do ledger, **atribuído por diferença da conta, não por `usage.cost`**) (`reports/credits_v6_qwen_2026-11-17.json`). Opus 5.5 e paciente rodam pela assinatura: no caso 011 o Opus teria custado US$ 0,0938 pelo preço de API contra US$ 0,045 das duas chamadas do Qwen.

## Desvios e ocorrências
1. A primeira tentativa com Gemini como médico (caso 011) foi parada por decisão do usuário (troca para GLM); trace arquivado fora do denominador; a chamada pendente do associador foi liquidada a zero por dois snapshots estáveis da conta, sem `usage.cost` (`reports/credits_v6_qwen_gemini_abort_2026-11-17.json`).
2. Um erro de harness (teto do ledger diferente entre o teste curto e o runner) interrompeu o primeiro lançamento do 011 antes de qualquer requisição.
3. No caso 004 o Qwen devolveu o parecer embrulhado em `{"content": "<json>"}` (formato pedido pelo prompt de emulação do CLI) e o leitor abortou o encontro com a 11ª chamada já paga. Acrescentei um desembrulho determinístico (`unwrap_content`), sem nova inferência, e o encontro foi retomado reaproveitando as chamadas pagas. A proposta do médico do 004 ficou sem registro. O código do braço mudou no meio da rodada; o desembrulho só age em respostas com um único campo `content`.
4. Falta de revisão médica, um encontro por caso e dois efeitos que não se separam (revisor e variação do médico).

## Observações
- No raciocínio do Qwen aparecem tentativas de lembrar o artigo publicado ("NEJM", "case record") em 2 dos 3 encontros fechados e em nenhum dos 5 públicos.
- O Qwen sozinho não superou o par Sonnet e Fable nos mesmos casos; o ganho de custo não existe (o revisor é a maior parte do custo).
- Pendentes: repetições, Qwen só no lugar do Fable, Qwen como médico, outros casos.
