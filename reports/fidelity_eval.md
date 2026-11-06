# Fidelidade do paciente simulado e escolha do juiz — avaliação offline exploratória (05-10-2026)

Nenhum encontro foi rerodado e nenhum resultado existente foi alterado. O script `scripts/fidelity_eval.py` relê os traces gravados, refaz as chamadas do juiz e do paciente em condições alternativas e grava tudo em `runs/fidelity/` e `results/fidelity_{judge,patient}.csv`. Claude (Sonnet como paciente candidato, Opus como árbitro e avaliador) rodou pela assinatura Pro (CLI, fora do ledger). **Avaliação por LLM, sem revisão médica; o Opus não é verdade de referência.**

## Custo e intercorrências
- Gasto OpenRouter da avaliação: cerca de US$ 1,60 (ledger de US$ 8,370711103 para US$ 9,968272828; conta = ledger em snapshots sem cache). Limite da chave: US$ 20 (restam cerca de US$ 10).
- Quatro chamadas rejeitadas sem custo exigiram reconciliação explícita, todas autorizadas e com 3 snapshots estáveis: 1 HTTP 503 (Google AI Studio), 2 HTTP 403 "Key limit exceeded" (falso positivo transitório: a chave tinha US$ 11,37 restantes), 1 HTTP 429 (20 RPM de conta nova do Gemini 3.1 Pro; passou a ter pacing de 3,5 s, como o GPT-5.2). Relatórios `fidelity_http{503,403,429}_reconciliation.json`.
- No 503, dois snapshots iniciais mostraram a conta US$ 0,0115 abaixo do ledger (atraso transitório) e foram descartados antes de gravar; os três de evidência convergiram. O arquivo bruto das duas chamadas 403 (`logs/incomplete/fidelity_http403_v1/`) contém o identificador da chave no corpo do erro e não foi versionado.

## 1. Juiz
Entrada: os 224 encontros julgados (204 dos 7 modelos mais 20 do braço Claude); o prompt reconstruído é idêntico ao original nos 204 com juiz gravado. Original = Gemini 3.1 Flash-Lite, temperatura 1.

| Variante | Corretos | Decisões diferentes do original |
|---|---:|---:|
| Original (Flash-Lite, temp 1) | 160 | — |
| Flash-Lite temp 1, nova rodada A / B | 159 / 159 | 9 / 11 |
| Flash-Lite temp 0, A / B | 156 / 158 | 10 / 10 |
| Gemini 3.1 Pro, temp 0, reasoning baixo | 143 | 21 (19 viram "errado", 2 viram "certo") |

- **Estabilidade:** Flash-Lite em temp 1: as duas novas rodadas diferem entre si em 8 de 224 (cerca de 4%); em temp 0, A × B diferem em 2 de 224 (cerca de 1%).
- **Árbitro Opus 5.5 (assinatura) em 31 encontros contestados** (qualquer divergência entre original, 4 Flash-Lite e Pro, ou juiz certo com a regra estrita dos casos 007/002/009 falhando): concorda com o Pro em 27/31, com o Flash-Lite temp 0 em 12–14/31, com o original em 12/31. O Opus aceita só 5 dos 31. **Viés de seleção:** o subconjunto foi escolhido onde o Flash-Lite divergia, o que o desfavorece por construção; e Pro e Opus são ambos mais rígidos, o que não prova que estejam certos.
- **Efeito no resultado:** o Pro rebaixa 19 acertos, sobretudo dos Qwen3.8 (prime 26→23, 0902 24→21), GLM-4.5-Air (19→14), Opus 5.5 (10→8) e Sonnet 5.5 (9→8); GPT-5.2 e GPT-OSS não mudam. Os casos instáveis concentram-se em 009 (Meckel), 002 (miocardite), 007 (fármaco) e 001.
- **Leitura:** o juiz original estava leniente com diagnósticos parciais, especialmente nos modelos que aceitaram "stent migrado" sem Meckel e "AHAI" sem pembrolizumabe. O ranking entre modelos muda pouco; o patamar absoluto cai.

## 2. Paciente simulado
40 perguntas reais (4 por caso, primeira fala de médicos de modelos diferentes, sorteio com semente 20261005), respondidas por 11 condições (modelo × prompt original ou com regras estritas anexadas). Um avaliador cego (Opus 5.5, ordem e rótulos embaralhados por pergunta) classifica cada resposta contra o `patient.json`. As "regras estritas" são um acréscimo ao prompt (usar só fatos listados, dizer que não sabe, no máximo 80 palavras, sem listas, sem diagnóstico).

| Condição | Respostas com detalhe inventado | Inventados por resposta | Falha em dizer "não sei" | Formato em lista | Palavras |
|---|---:|---:|---:|---:|---:|
| Sonnet 5.5 + regras | **2%** | 0,03 | 1/40 | 0% | 64 |
| Sonnet 5.5 (base) | 28% | 0,38 | 5/40 | 0% | 96 |
| GPT-5.2 + regras | 38% | 0,53 | 9/40 | 0% | 71 |
| GLM-4.5-Air + regras | 52% | 1,40 | 18/40 | 0% | 61 |
| GLM-4.5-Air (base) | 55% | 1,90 | 23/40 | 58% | 82 |
| GPT-5.2 (base) | 70% | 2,05 | 19/40 | 88% | 90 |
| Flash-Lite + regras | 80% | 2,15 | 26/40 | 0% | 70 |
| GPT-OSS + regras | 80% | 3,10 | 32/40 | 0% | 65 |
| GLM-5 (base) | 80% | 3,45 | 29/40 | 82% | 119 |
| GPT-OSS (base, condição usada nas runs) | **95%** | 5,17 | 38/40 | 90% | 122 |
| Flash-Lite (base) | 95% | 3,83 | 38/40 | 58% | 88 |

- **Verificação cruzada:** a heurística determinística (número/quantidade fora do registro) confirma o pior (GPT-OSS base 50% e GPT-5.2 base 32%, contra 12% do GPT-OSS com regras) e que as regras reduzem a invenção em todos os modelos; ela só enxerga números, então o ranking intermediário é diferente.
- **Vieses conhecidos:** o avaliador é da mesma família do Sonnet (favoritismo possível, mitigado por cegamento); 40 perguntas, uma amostra pequena; só a primeira fala (sem conversa longa); o avaliador pode errar o que é "genérico". Nenhuma resposta foi lida por médico.
- **Leitura:** o prompt de regras estritas melhora todos os modelos (maior efeito: Sonnet, GPT-5.2, GPT-OSS). O GPT-OSS como paciente, usado em 30 encontros, inventa em quase toda resposta; isso é evidência de contaminação do paciente nas runs do GPT-OSS e dos pares paciente=médico em geral.

## 3. Recomendação (a validar)
- **Juiz:** Gemini 3.1 Pro, temperatura 0 e reasoning baixo (cerca de US$ 0,004 por julgamento; US$ 0,85 para 224) como juiz principal, com Opus 5.5 (assinatura) como árbitro das divergências; Flash-Lite deixa de ser o juiz principal. Validar com revisão médica de uma amostra (casos 001, 002, 007, 009 e os 31 contestados).
- **Paciente:** modelo fixo, independente do médico, com o prompt de regras estritas. Melhor medido: Sonnet 5.5 (assinatura, custo zero no OpenRouter), com a ressalva do avaliador da mesma família. Entre os baratos pelo OpenRouter, GLM-4.5-Air + regras (52%) e GPT-5.2 + regras (38%) são os candidatos.
- **Nada disso reescreve as runs existentes.** Rerodar os encontros com paciente fixo e regras custaria uma nova rodada; decisão sua.
