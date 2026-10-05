# Protocolo v3 — rascunho de projeto (05-10-2026)

**Status: não implementado e não executado.** Este documento só registra as decisões tomadas até agora. As rodadas v1 (run 1), v2 (runs 2 e 3) e as extensões ficam congeladas e comparáveis entre si; a v3 é uma condição experimental nova, com diretórios e CSVs próprios (`runs/v3/<modelo>/runN`, `results/v3_<modelo>_runN.csv`), sem alterar `MODELS` nem os resultados existentes. Execução só depois da autorização do usuário, quando todos os ajustes estiverem prontos.

## Decisões confirmadas
1. **Paciente com regras estritas.** O prompt do upstream fica inalterado e o texto `RULES` de `scripts/fidelity_eval.py` é anexado ao final (usar só os fatos do registro; dizer que não sabe; no máximo 80 palavras; linguagem leiga; sem listas; sem diagnóstico). Medido offline: invenção de detalhes cai em todos os modelos (ver `fidelity_eval.md`).
2. **Paciente fixo e independente do médico:** Claude Sonnet 5.5 pela assinatura Pro (CLI), com regras estritas (2% de respostas com invenção no teste de 40 perguntas; avaliador da mesma família, ressalva registrada). Custo zero no OpenRouter, mas consome o limite do plano.
3. **Mais conversa, menos exame em cadeia:**
   - Exames (sangue, urina, bedside/ECG, imagem, microbiologia, outros) ficam **bloqueados** até o médico ter feito pelo menos N trocas com o paciente (proposta N=3) e ter pedido o exame físico. Antes disso a ferramenta responde que a história precisa ser completada. Não gasta turno.
   - **Resultado na rodada seguinte:** o exame pedido numa rodada só é entregue junto com a próxima resposta do paciente; o médico precisa falar com o paciente enquanto espera.
   - Exame físico e admissão não são bloqueados. O prompt do médico ganha um parágrafo explicando essas duas regras.
4. **Juiz:** Gemini 3.1 Pro, temperatura 0, reasoning baixo, para todos os encontros; Opus 5.5 (assinatura) como árbitro das divergências, sobretudo nos casos 001, 002, 007 e 009 e quando um segundo juiz barato (Flash-Lite temp 0) discordar. Julgamento por LLM; revisão médica continua pendente.

## Pontos em aberto
- Valor de N (3?) e se a admissão também exige N trocas; se o limite de 10 turnos fica (as regras gastam turnos) ou sobe para 12 (não escolhido pelo usuário; mantido em 10 até decisão).
- Quais modelos e quantas repetições entram na v3.
- Se algum candidato a médico novo deve entrar.
- Lista de ajustes adicionais que o usuário ainda quer fazer antes de rodar.

## Restrição de orçamento (importante)
Teto do ledger: US$ 18,00; gasto atual US$ 9,968272828 (restam cerca de US$ 8,03; a chave tem limite US$ 20, restam cerca de US$ 10). Custo médio por encontro medido nas runs v1/v2 (inclui o paciente, que passará a custo zero, e o juiz barato, que passará a Pro, +US$ 0,004):

| Modelo | US$/encontro |
|---|---:|
| GPT-OSS | 0,007 |
| GLM-4.5-Air | 0,004 |
| GLM-5 | 0,016 |
| Qwen3.5 | 0,037 |
| GPT-5.2 | 0,075 |
| Qwen3.8 Max 0902 | 0,044 |
| Qwen3.8 Max Prime | 0,092 |
| Soma dos 7 | 0,274 |

- Uma rodada (7 modelos × 10 casos × 1) custaria cerca de US$ 2,7 nas condições antigas; com mais turnos de conversa estimo 1,3 a 1,6× e mais US$ 0,3 do juiz Pro, algo como **US$ 4 a 5 por rodada**.
- **Três rodadas dos 7 modelos (cerca de US$ 12 a 15) não cabem no saldo.** Cabem uma rodada completa, ou três rodadas de um subconjunto mais barato, ou algo intermediário. O Claude (Sonnet, Opus) roda pela assinatura e não consome o ledger.
- Estimativa, não garantia; o custo real só se mede com a primeira rodada.
