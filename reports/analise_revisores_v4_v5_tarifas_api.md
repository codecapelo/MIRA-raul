# Análise dos revisores (Sol e Astra) nas últimas versões — chamadas, ferramentas, cache, falhas e custo a tarifas de API

Gerado em 24-11-2026 a partir dos arquivos do repositório `codecapelo/MIRA-raul` (branch `claude/focused-johnson-rmfthk`, HEAD `271ce09`). Nada foi executado no OpenRouter, no ChatGPT/Codex ou no Claude: tudo vem de traces, ledger e relatórios já gravados, repreçados em gabinete.

> **Como li o pedido.** "Revisores" = os modelos que revisam o diagnóstico do médico simulado: **Sol** (`gpt-6.1-sol`, duas chamadas por caso) e **Astra** (`gpt-6-astra`, parecer final). "Últimas versões" = **v4 rápida fast4** (a última com traces por chamada, 20 casos) e **v5** (mesmos revisores, 20 casos em `v5full1`), com as versões anteriores (v4 original, v4 working, fast1–3) como histórico de tentativas. Se você quis dizer outra coisa, me diga.

## 1. Resumo (o que importa)

| | Públicos (10) | Fechados (10) |
|---|---:|---:|
| Encontros terminais / aceitos pelo juiz (fast4) | 10 / 10 | 10 / 10 |
| Chamadas Sol + Astra (fast4) | 30 | 29 |
| Custo dos revisores **a tarifa de API** (fast4, tokens medidos) | **US$ 1,771** | **US$ 1,602** |
| … por caso | US$ 0,177 (faixa US$ 0,123–US$ 0,199) | US$ 0,160 |
| OpenRouter, médico + associador (implantação) | US$ 0,101 | US$ 0,168 |
| OpenRouter, todos os atores (inclui paciente simulado e juízes) | US$ 0,210 | US$ 0,284 |
| **Custo de implantação por caso** (revisores + médico + associador) | **US$ 0,187** | **US$ 0,177** |

Pontos centrais:

1. **O Astra é o custo.** Uma chamada do Astra por caso custa cerca de US$ 0,126, contra US$ 0,026 por chamada do Sol. Os dois Sol + o Astra somam ~US$ 0,177/caso; médico + associador via Gemini Flash-Lite somam só ~US$ 0,010/caso. **Os revisores são ≈ 90–95% do custo de implantação** a tarifas de API (95% nos públicos, 91% nos fechados).
2. **A assinatura escondia isso.** Os traces registram `monetary_cost_usd: null` para todas as chamadas do CLI (custo da assinatura desconhecido). O repositório sempre comparou "OpenRouter por caso" (US$ 0,02–0,03) — um número que **exclui** o custo dominante. Repreçado, o caso sai ≈ 7–9× mais caro (≈ US$ 0,19–0,20 em vez de US$ 0,02–0,03).
3. **Cache quase não funcionou:** só 6 de 60 chamadas de revisor acertaram cache nos traces fast1–4 públicos, sempre o mesmo bloco de 7.552 tokens. A segunda chamada do Sol nunca acertou.
4. **Parte dos tokens cobrados é sobrecarga do CLI do Codex, não conteúdo clínico.** O conteúdo enviado ao revisor (system + transcrição cega) tem mediana de ~7.758 caracteres (≈ 1,5–3 mil tokens), mas o CLI reporta ~11 mil tokens de entrada por chamada. Chamando a API diretamente, o custo dos revisores poderia cair para cerca de **US$ 0,058–US$ 0,067 por caso** (estimativa, §6).
5. **Não consegui os traces brutos da v5** (`runs/v5/` fica fora do Git) nem os dos casos fechados da fast4 por chamada. Para eles uso os agregados publicados; o que for extrapolação está marcado como **ESTIMATIVA**.

## 2. Escopo e o que está (e não está) disponível

| Fonte | Granularidade | Usada para |
|---|---|---|
| `runs/v4/**` (55 arquivos de trace) | **Por chamada** — 1.046 chamadas (376 do CLI Sol/Astra + 670 OpenRouter) | v4 original, v4 working, revisão offline, fast1, fast2 (piloto), fast3 (piloto), **fast4 públicos** |
| `reports/v4_fast_summary.json` | Agregado por papel | **fast4 fechados** (traces fechados ficam fora do Git por política do projeto) |
| `reports/v5full1_results_2026-11-14.md`, `v5_dev_summary.json`, `config/frozen/v5.json` | Agregado | **v5** (sem tokens do CLI publicados) |
| `reports/v4_fast_billing_reconciliation.json` etc. | Ledger | Conferência de custo OpenRouter |

Validação cruzada: os totais que recalculei dos traces (tokens por papel, custo OpenRouter) **batem** com `v4_fast_summary.json` e com o ledger (por exemplo fast4 públicos: Astra 112.344 tokens de entrada, 4.118 de saída, 7.552 em cache; custo OpenRouter US$ 0,2103192).

**Sobre "6.3":** você mencionou que achava que a versão era 6.3. **Nada no repositório, em nenhum commit, diz 6.3** — todo o código e todos os traces pedem `gpt-6.1-sol` e `gpt-6-astra`, e o CLI nunca confirmou qual modelo atendeu (`observed_model: null`, `model_identity_status: "requested_only; CLI did not attest served model"` em todas as 376 chamadas). Portanto os números abaixo são do modelo **solicitado** (6.1). Se de fato foi outra versão, o custo muda conforme a tabela de tarifas (ver §10).

## 3. Tarifas de API aplicadas

Em USD por 1 milhão de tokens. A saída **já inclui** os tokens de raciocínio (no `usage` do CLI, `completion_tokens` inclui `reasoning_tokens`). A entrada em cache está **contida** na entrada total (`prompt_tokens`); cobrei `(entrada − cache) × tarifa de entrada + cache × tarifa de cache` — premissa coerente com os dados (cache sempre menor que a entrada), mas não confirmada pelo CLI.

| Modelo | Entrada | Entrada em cache | Saída | Origem |
|---|---:|---:|---:|---|
| `gpt-6.1-sol` (Sol) | 2,00 | 0,10 | 10,00 | **Tabela de terceiros** (agregadores) |
| `gpt-6-astra` (Astra) | 10,00 | 1,00 | 50,00 | **Tabela de terceiros** (agregadores) |
| `gemini-3.1-flash-lite-preview` (médico, associador, paciente fast4) | 0,25 | – | 1,50 | `config/*.json` do repositório (preço do Google AI Studio via OpenRouter) |
| `gemini-3.1-pro-preview` (juiz) | 2,00 | – | 12,00 | `config/*.json` do repositório |
| Claude Sonnet 5.5 (paciente v5) | 2,00 | 0,10 (leitura) | 10,00 | tabela de preços da Anthropic usada neste ambiente (cache 24-11-2026) |

**Avisos que você precisa conhecer antes de usar estes números comercialmente:**

- **Não consegui abrir as páginas oficiais da OpenAI** (o ambiente bloqueia `openai.com`). Os preços do Sol e do Astra vêm de uma busca na web que listou agregadores (Morph, eesel, PricePerToken, CloudZero); eles concordam entre si, mas **não são a tabela oficial**. Uma das fontes ainda cita Astra acima de 272 mil tokens de entrada a US$ 20 / US$ 75 e cache write a US$ 12,50 — nenhuma chamada daqui chega perto de 272 mil nem tem cache write (`cache_write_input_tokens = 0` em todas). **Confirme na página oficial antes de usar para orçamento ou contrato.**
- **Os modelos Gemini são "preview".** Modelos em prévia costumam ter termos que limitam uso em produção comercial. Para o cálculo usei o valor efetivamente cobrado (`usage.cost`), mas **a elegibilidade para produção comercial dessas versões não foi verificada**.
- **Planos de assinatura (ChatGPT/Codex, Claude Pro) não são tarifa de API.** Por isso toda chamada do CLI foi repreçada pela tabela acima. Se os termos da assinatura permitem ou não uso comercial automatizado também não foi verificado aqui.
- Não apliquei descontos de lote (Batch ~50%) nem de prioridade.

## 4. Todas as chamadas — fast4 (última versão com traces por chamada)

### 4.1 Públicos (10 casos) — reconstruído chamada a chamada dos traces

| Papel | Modelo | Chamadas | Entrada (tokens) | Em cache | Saída | dos quais raciocínio | Latência mediana (s) | Custo | Base |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `doctor` | `gemini-3.1-flash-lite-preview` | 81 | 206.965 | 3.928 | 7.100 | 0 | 1.5 | US$ 0,06151 | cobrado (OpenRouter) |
| `patient` | `gemini-3.1-flash-lite-preview` | 36 | 40.449 | 0 | 2.683 | 0 | 1.4 | US$ 0,01414 | cobrado (OpenRouter) |
| `fast_review_sol` | `gpt-6.1-sol` | 10 | 109.794 | 15.104 | 5.042 | 2.690 | 23.5 | US$ 0,2413 | tarifa API |
| `patient_review` | `gemini-3.1-flash-lite-preview` | 8 | 11.808 | 0 | 406 | 0 | 1.4 | US$ 0,00356 | cobrado (OpenRouter) |
| `matcher` | `gemini-3.1-flash-lite-preview` | 76 | 113.738 | 0 | 7.433 | 0 | 1.4 | US$ 0,03958 | cobrado (OpenRouter) |
| `fast_review_sol_post_followup` | `gpt-6.1-sol` | 10 | 114.070 | 0 | 4.061 | 2.019 | 19.8 | US$ 0,2687 | tarifa API |
| `fast_review_astra` | `gpt-6-astra` | 10 | 112.344 | 7.552 | 4.118 | 146 | 17.5 | US$ 1,2614 | tarifa API |
| `judge` | `gemini-3.1-pro-preview` | 10 | 6.274 | 0 | 2.354 | 1.525 | 4.4 | US$ 0,04080 | cobrado (OpenRouter) |
| `judge_proposal` | `gemini-3.1-pro-preview` | 10 | 6.125 | 0 | 3.207 | 2.346 | 4.9 | US$ 0,05073 | cobrado (OpenRouter) |

Revisores (Sol ×2 + Astra): **US$ 1,7714** a tarifa de API. Resto (OpenRouter, todos os atores): **US$ 0,2103** — igual ao ledger. As chamadas do `doctor` podem incluir as 4 retentativas por argumento inválido (§8).

### 4.2 Fechados (10 casos) — só agregados publicados

| Papel | Modelo | Chamadas | Entrada (tokens) | Em cache | Saída | dos quais raciocínio | Latência mediana (s) | Custo | Base |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `doctor` | `gemini-3.1-flash-lite-preview` | 112 | 377.412 | 51.069 | 9.446 | 0 | 1.5 | US$ 0,09703 | cobrado (OpenRouter) |
| `fast_review_astra` | `gpt-6-astra` | 10 | 121.643 | 37.760 | 4.583 | 104 | 19.1 | US$ 1,1057 | tarifa API |
| `fast_review_sol` | `gpt-6.1-sol` | 10 | 119.534 | 15.104 | 5.376 | 2.768 | 25.4 | US$ 0,2641 | tarifa API |
| `fast_review_sol_post_followup` | `gpt-6.1-sol` | 9 | 112.086 | 15.104 | 3.656 | 1.664 | 19.0 | US$ 0,2320 | tarifa API |
| `judge` | `gemini-3.1-pro-preview` | 10 | 7.461 | 0 | 2.355 | 1.583 | 4.0 | US$ 0,04318 | cobrado (OpenRouter) |
| `judge_proposal` | `gemini-3.1-pro-preview` | 9 | 6.613 | 0 | 2.197 | 1.469 | 4.2 | US$ 0,03959 | cobrado (OpenRouter) |
| `matcher` | `gemini-3.1-flash-lite-preview` | 120 | 222.742 | 0 | 10.500 | 0 | 1.4 | US$ 0,07144 | cobrado (OpenRouter) |
| `patient` | `gemini-3.1-flash-lite-preview` | 41 | 95.613 | 0 | 3.316 | 0 | 1.4 | US$ 0,02888 | cobrado (OpenRouter) |
| `patient_review` | `gemini-3.1-flash-lite-preview` | 5 | 13.991 | 0 | 378 | 0 | 1.5 | US$ 0,00406 | cobrado (OpenRouter) |

Revisores: **US$ 1,6019** a tarifa de API (9 segundas chamadas do Sol, não 10: uma não ocorreu; o resumo publicado não diz o motivo). OpenRouter todos os atores: **US$ 0,2842**. Por chamada, só os agregados existem — o arquivo `chamadas_por_chamada.csv` cobre os públicos.

### 4.3 Estrutura de cada encontro (até 3 chamadas de revisor)

1. **Sol, 1ª revisão** (`fast_review_sol`): lê a conversa e os achados, dá diagnóstico, até 3 perguntas e até 4 exames que mudariam a decisão.
2. **Follow-up** (sem custo de revisor): o paciente simulado responde e os exames pedidos pelo revisor passam pela política de exames; vira `followup_result`.
3. **Sol, 2ª revisão** (`fast_review_sol_post_followup`), só se houve achado novo ou indisponibilidade estruturada.
4. **Astra, parecer final** (`fast_review_astra`): sempre finaliza.

Latência mediana: Sol 23,0 s, Sol 2ª 21,4 s, Astra 17,8 s (máx. 40,5 s / 33,6 s / 23,8 s nos fast1–4 públicos).

## 5. Custo por versão — todas as tentativas, repreçadas

Colunas de revisor: chamadas do CLI repreçadas a tarifa de API (em v4 original e v4 working o Sol também era médico, paciente e mapa — não só revisor).

| Condição | Chamadas CLI (Sol / Astra) | Entrada | Cache | Saída | Custo CLI a tarifa API | OpenRouter (cobrado) | Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| v4 original (Sol médico/paciente/revisor) | 152 / 0 | 1.801.738 | 248.704 | 33.901 | US$ 3,470 | US$ 0,123 | US$ 3,593 |
| v4 hipótese de trabalho (Sol + parecer Astra) | 143 / 11 | 1.814.689 | 386.432 | 36.502 | US$ 4,419 | US$ 0,115 | US$ 4,535 |
| v4 revisão offline (Astra) | 0 / 10 | 119.737 | 0 | 4.110 | US$ 1,403 | US$ 0,046 | US$ 1,449 |
| fast1 (10 públicos) | 10 / 10 | 225.758 | 7.552 | 8.724 | US$ 1,553 | US$ 0,194 | US$ 1,747 |
| fast2 piloto (2 casos, interrompido) | 3 / 2 | 55.617 | 0 | 2.898 | US$ 0,361 | US$ 0,045 | US$ 0,406 |
| fast3 piloto (2 casos, interrompido) | 3 / 2 | 56.297 | 15.104 | 2.942 | US$ 0,284 | US$ 0,043 | US$ 0,327 |
| fast4 públicos (10) | 20 / 10 | 336.208 | 22.656 | 13.221 | US$ 1,771 | US$ 0,210 | US$ 1,982 |
| fast4 fechados (10) | 19 / 10 | 353.263 | 67.968 | 13.615 | US$ 1,602 | US$ 0,284 | US$ 1,886 |
| **Soma** | | | | | **US$ 14,863** | **US$ 1,061** | **US$ 15,924** |

- **Tentativas adicionais até chegar à fast4:** fast1 + os pilotos fast2 e fast3 custaram US$ 2,198 em CLI a tarifa de API + US$ 0,283 no OpenRouter = **US$ 2,480**. O relatório oficial só mostra a parte OpenRouter (US$ 0,283).
- **Total de todas as chamadas do CLI (Sol/Astra, em qualquer papel) nos traces v4 e fast, mais fechados:** US$ 14,86 a tarifa de API, contra US$ 1,06 reportado como "gasto adicional v4" (que só contava OpenRouter).
- O fast2 e o fast3 foram interrompidos após 2 casos: fast2 por pré-requisito não executado (parser), fast3 por diagnóstico negativo — ambos custos reais que ficaram fora do denominador clínico.
- Resultado diagnóstico por condição (juiz LLM, sem revisão médica): fast1 9/10 · fast2 1/2 · fast3 1/2 · fast4 públicos 10/10 · fast4 fechados 10/10. Casos conhecidos, uma execução por caso — **não é prova de acurácia clínica**.

## 6. Tokens em cache — o que aconteceu e o que dá para ganhar

Glossário rápido: *token* ≈ pedaço de palavra; *entrada em cache* = parte do prompt que o provedor já tinha processado e cobra mais barato (Sol: 20× mais barato; Astra: 10×).

| Revisor | Chamadas (fast1–4 públicos + pilotos) | Chamadas com cache | Valor de cache observado |
|---|---:|---:|---|
| `fast_review_astra` (gpt-6-astra) | 24 | 3 | 0 ou 7.552 tokens |
| `fast_review_sol` (gpt-6.1-sol) | 24 | 3 | 0 ou 7.552 tokens |
| `fast_review_sol_post_followup` (gpt-6.1-sol) | 12 | 0 | sempre 0 |

Achados:

- O cache, quando aparece, é **sempre exatamente 7.552 tokens** (59 blocos de 128) — um prefixo fixo e idêntico entre casos. Nos totais por coorte todos os valores de cache são múltiplos de 7.552 (22.656 = 3×, 67.968 = 9×).
- **Cenário A — cache em todas as chamadas** (estimativa: todo revisor reaproveita o prefixo de 7.552 tokens): custo dos revisores nos 10 públicos cairia de US$ 1,771 para US$ 0,901 (−49%). Só é plausível se o prefixo for de fato idêntico e posto no início do prompt.
- Nos fechados o cache foi maior (Astra 37.760 tokens em cache de 121.643): sem nenhum cache os revisores custariam US$ 1,999 em vez de US$ 1,602 (cache economizou ~20%); nos públicos, ~5%.
- **Cenário B — chamar a API direto, sem o CLI** (estimativa grosseira): o conteúdo clínico que de fato vai ao revisor tem mediana de 7.758 caracteres. Convertendo a 3–4 caracteres/token e mantendo a saída observada, os revisores custariam **US$ 0,578–US$ 0,672** nos 10 públicos (US$ 0,058–US$ 0,067/caso), contra US$ 1,771 medido. **É uma conta de chars/token, não uma medição:** a diferença (~8–9 mil tokens por chamada) é consistente com o contexto do próprio Codex CLI (instruções de sistema, definições de ferramentas desligadas etc.), que numa integração direta não existiria. Antes de decidir, meça com um contador de tokens ou uma chamada de teste autorizada.
- Entrada domina o custo do Astra: 104.792 tokens de entrada não cacheados ≈ US$ 1,048 dos US$ 1,261 (≈ 83%). A saída do Astra quase não tem raciocínio (146 de 4.118 tokens); a do Sol é ~50% raciocínio.

## 7. Ferramentas

Ferramentas do médico no fast4 públicos: `request_radiology` 17, `request_blood_test` 15, `admission` 10, `request_bedside_test` 6, `request_other_investigation` 5, `default_admission` 4, `request_microbiology` 3, `request_physical_exam` 2.

Desfecho das chamadas de ferramenta por condição (do texto devolvido ao médico):

| Condição | Resultado entregue | Indisponível no caso | Bloqueada por história | Retida por custo | Argumento inválido (retentativa) | Admissão |
|---|---:|---:|---:|---:|---:|---:|
| v4 original (Sol médico/paciente/revisor) | 25 | 29 | 0 | 5 | 0 | 10 |
| v4 hipótese de trabalho (Sol + parecer Astra) | 29 | 18 | 0 | 3 | 0 | 11 |
| fast1 (10 públicos) | 14 | 25 | 17 | 1 | 3 | 10 |
| fast2 piloto (2 casos, interrompido) | 4 | 4 | 2 | 1 | 0 | 2 |
| fast3 piloto (2 casos, interrompido) | 3 | 5 | 1 | 0 | 0 | 2 |
| fast4 públicos (10) | 17 | 22 | 5 | 1 | 4 | 10 |

Contagens de exames dos relatórios (fast4): públicos 268 unidades relativas / 42 fontes cobradas / 56 tentativas indisponíveis / 9 repetidas; fechados 287 / 67 / 51 / 11. **Unidades relativas são contabilidade artificial do protocolo, não dólares.** Os revisores pedem exames pelas mesmas ferramentas (`request_blood_test`, `request_radiology` etc.); no fast4 públicos, 22 de 49 chamadas de ferramenta de exame (≈ 45%) voltaram "indisponível no caso" (limite do protocolo de casos publicados, não necessariamente erro do médico). Os "outros" nas contagens são ferramentas de exame físico e saídas de pré-requisito.

## 8. Falhas e tentativas adicionais

| Evento | Onde | Custo / efeito | Fonte |
|---|---|---|---|
| Chamadas Sol/Astra que falharam com uso desconhecido | fast4 públicos e fechados | **0** | `v4_fast_summary.json` (`failed_calls_with_unknown_subscription_usage`) |
| Chamada do CLI com sinais de desconexão de stream / retentativa de amostragem / timeout | fast3 piloto, `case_001`, Sol 1ª revisão (latência 40,5 s, mediana 23 s) | 1 resposta registrada (10.782 entrada, 473 saída). **Retentativa interna do CLI não é atestada** (`internal_retry_count_attested: false`): custo real pode ser maior que o registrado — o CLI só contou frases fixas no stderr | trace |
| Retentativa de ferramenta por JSON inválido do médico | fast1: 3; fast4 públicos: 4 | Cada uma gera outra chamada do médico (Flash-Lite, ~US$ 0,0007) — desprezível | trace |
| Pilotos interrompidos antes da ampliação | fast2 (parser de pré-requisito), fast3 (negativo) | Tabela §5: US$ 0,406 e US$ 0,327 | relatórios fast2/fast3 |
| Rejeição HTTP 403 (limite da chave OpenRouter) no último bloco de fechados | fast4 fechados | 1 chamada sem `usage.cost` → custo **zero atribuído por evidência de conta** (3 snapshots estáveis); encontro parcial preservado e retomado por replay exato | `v4_fast_key_limit_reconciliation.json` |
| Quatro chamadas de juiz sem metadados (404) | v4 anteriores | diferença transitória de US$ 0,018154, depois conciliada integralmente | `v4_global_billing_reconciliation.json` |
| Ledger global v4/fast | 968 chamadas | 967 respostas com custo conferido (967 metadados de geração) + 1 rejeição sem custo; pendentes/incertas 0 | `v4_fast_summary.json` |
| Pausas / cauda de tempo de parede | fast4 fechados | P95 de parede 8.786 s, máx. 15.834 s (limite de chave + pausa pedida); P95 das chamadas ativas 158 s | `v4_fast4_summary.md` |
| Cache ausente na 2ª chamada do Sol | todas | 0 acertos em 12 chamadas — ver §6 | trace |
| Latências extremas do CLI | v4 original/working (Sol médico, paciente, revisor) | picos de 308–328 s por chamada (mediana 7–26 s); não aparecem no fast4 (máx. 40,5 s) | trace |

**Pontos sem solução nos dados:** (a) o CLI não informa se houve retentativa interna, então tokens cobrados em tentativas silenciosas podem estar subcontados; (b) o custo de chamadas interrompidas do CLI pode estar ausente (o próprio relatório v4 avisa); (c) nada garante que `observed_model` seja o solicitado.

## 9. v5 — o que é medido e o que é estimativa

Fonte: `reports/v5full1_results_2026-11-14.md` e `v5_dev_summary.json`. **Não há tokens do CLI de Sol/Astra publicados para a v5**; os traces ficam em `runs/v5/` (ignorado pelo Git) e não estão neste ambiente.

**Medido (relatado):**
- 20 encontros terminais, 17 aceitos pelo juiz (públicos 9/10, fechados 8/10); 13/20 propostas do médico corretas; 0 falhas terminais do modelo.
- OpenRouter na rodada: **US$ 0,479** (ledger v5 US$ 1,164776375 em 1.063 chamadas todas `settled`), ≈ US$ 0,024 por encontro. Conta = ledger.
- Paciente Sonnet 5.5 (CLI, assinatura): custo equivalente de API registrado só nos 12 casos de desenvolvimento: US$ 0,479 (US$ 0,0399/caso).
- O validador do paciente rejeitou ≥ 1 resposta em 14 de 20 encontros; nos 12 de desenvolvimento, 10 de 45 respostas (22%) foram regeneradas → chamadas adicionais do Sonnet.
- **Falhas:** (1) sessão OAuth do CLI do Claude expirada no `case_001` — sem `case_complete`, US$ 0,0028 no OpenRouter, mesma variante relançada após novo login (o custo das chamadas do Sonnet perdidas não é medido); (2) HTTP 503 no `case_010` durante streaming (83 eventos, sem resposta, reserva incerta US$ 0,0123), conciliado a custo zero com 4 snapshots; o parcial foi arquivado e o caso **recomeçou do zero** — isso repete chamadas já feitas (inclusive, possivelmente, de revisores, mas o relatório não separa).
- Resultado do juiz por coorte: ver relatório. Casos conhecidos, 12 deles usados no desenvolvimento: linha de base, **não validação**.

**ESTIMATIVA — revisores da v5 a tarifa de API** (extrapolando o custo por caso medido na fast4; a v5 usa os mesmos dois revisores, esforço `medium`, e o pipeline de revisão é o da fast4):

| | Valor |
|---|---:|
| Revisores, fast4 medido (20 casos) | US$ 3,37 → US$ 0,169/caso |
| **Revisores v5full1 (20 casos), estimativa central** | **≈ US$ 3,37** (faixa US$ 2,46–US$ 3,97, usando o menor e o maior caso público da fast4) |
| OpenRouter v5full1 (medido) | US$ 0,479 |
| Paciente Sonnet 5.5, equivalente de API (extrapolado de 12 casos; **só no benchmark**, na vida real é uma pessoa) | ≈ US$ 0,80 |
| **Total estimado v5full1 a tarifa de API** | **≈ US$ 4,65** |

Limitações da estimativa: a v5 teve menos trocas com o paciente (3,4 vs 4,8) e transcrições mais curtas, o que reduziria um pouco a entrada; mas o prefixo fixo do CLI domina a entrada (~11 mil tokens), então o erro esperado é pequeno. O custo do Sonnet usa a estimativa do próprio CLI (`total_cost_usd`), que não consegui recomputar sem os tokens.

## 10. Sensibilidade — se o preço ou a versão do Sol/Astra for outro

Revisores nos 10 públicos fast4, tokens medidos:

| Cenário | Custo |
|---|---:|
| Tarifas desta análise | US$ 1,771 |
| Sol a metade do preço | US$ 1,516 |
| Sol ao dobro do preço | US$ 2,281 |
| Sol cobrado como Astra | US$ 3,819 |
| Astra a metade do preço | US$ 1,141 |
| Sem nenhum cache | US$ 1,868 |
| Cache em todas as chamadas (Cenário A) | US$ 0,901 |
| API direta, só o payload (Cenário B) | US$ 0,578–US$ 0,672 |

Para refazer com a tarifa oficial (ou com a versão 6.3 se existir), troque a tabela `RATES` em `scripts/commercial_cost_analysis.py` e rode de novo; o CSV por chamada traz entrada, cache, saída e raciocínio de cada chamada para recalcular em planilha.

Tokens totais dos revisores nos 10 públicos fast4 (para recalcular você mesmo): **Sol** 223.864 entrada (15.104 em cache), 9.103 saída; **Astra** 112.344 entrada (7.552 em cache), 4.118 saída. Fechados: Sol 231.620 entrada (30.208 em cache), 9.032 saída; Astra 121.643 entrada (37.760 em cache), 4.583 saída.

## 11. Limites e cuidados de interpretação

- **Nada aqui é medida de qualidade clínica.** Juiz é LLM (Gemini 3.1 Pro), revisão médica cega continua pendente, os casos são conhecidos e foram usados no desenvolvimento; os fechados são históricos do projeto, não um conjunto externo novo.
- **Ferramentas e "falhas" do paciente simulado** (negativos sem fonte, EP posterior entregue na fase aguda, troponina I → T) estão documentadas em `reports/v4_fast4_summary.md` e na auditoria de fidelidade — afetam a leitura da qualidade, não o custo.
- **Em produção real não existiria paciente simulado nem juiz**; por isso separei "implantação" (revisores + médico + associador) de "todos os atores". O paciente e os juízes são custo do benchmark.
- Tokens do CLI incluem contexto reenviado e sobrecarga de transporte; em integração direta o consumo será diferente (§6, Cenário B).
- Tarifas do Sol/Astra de **terceiros, não oficiais**; elegibilidade comercial dos modelos Gemini "preview" e dos termos de assinatura **não verificada**; versão servida **não atestada**.
- A v5 está estimada por extrapolação; o valor certo exige os traces de `runs/v5/v5full1` (rodar `scripts/commercial_cost_analysis.py` neles).

## 12. Arquivos

- Este relatório: `reports/analise_revisores_v4_v5_tarifas_api.md`
- Todas as chamadas dos traces (1.046 linhas: grupo, caso, papel, modelo, entrada, cache, saída, raciocínio, custo cobrado e custo a tarifa de lista): `reports/chamadas_por_chamada.csv`
- Agregados por condição/papel e desfecho de ferramentas: `reports/analise_agregado.json`
- Script de extração e repreçamento (sem rede, só leitura): `scripts/commercial_cost_analysis.py`
