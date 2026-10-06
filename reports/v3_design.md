# Protocolo v3 — rascunho de projeto (05-10-2026)

**Status: implementado e testado (51 testes), nenhuma rodada executada.** Este documento registra as decisões e o plano. As rodadas v1 (run 1), v2 (runs 2 e 3) e as extensões ficam congeladas e comparáveis entre si; a v3 é uma condição experimental nova, com diretórios e CSVs próprios (`runs/v3/<modelo>/runN`, `results/v3_<modelo>_runN.csv`), sem alterar `MODELS` nem os resultados existentes. Execução só depois da autorização do usuário, quando todos os ajustes estiverem prontos.

## Decisões confirmadas
1. **Paciente com regras estritas.** O prompt do upstream fica inalterado e o texto `RULES` de `scripts/fidelity_eval.py` é anexado ao final (usar só os fatos do registro; dizer que não sabe; no máximo 80 palavras; linguagem leiga; sem listas; sem diagnóstico). Medido offline: invenção de detalhes cai em todos os modelos (ver `fidelity_eval.md`).
2. **Paciente fixo e independente do médico:** Claude Sonnet 5.5 pela assinatura Pro (CLI), com regras estritas (2% de respostas com invenção no teste de 40 perguntas; avaliador da mesma família, ressalva registrada). Custo zero no OpenRouter, mas consome o limite do plano.
3. **Mais conversa, menos exame em cadeia:**
   - Exames (sangue, urina, bedside/ECG, imagem, microbiologia, outros) ficam **bloqueados** até o médico ter feito pelo menos N trocas com o paciente (proposta N=3) e ter pedido o exame físico. Antes disso a ferramenta responde que a história precisa ser completada. Não gasta turno.
   - **Resultado na rodada seguinte:** o exame pedido numa rodada só é entregue junto com a próxima resposta do paciente; o médico precisa falar com o paciente enquanto espera.
   - Exame físico e admissão não são bloqueados. O prompt do médico ganha um parágrafo explicando essas duas regras.
4. **Juiz:** Gemini 3.1 Pro, temperatura 0, reasoning baixo, para todos os encontros; Opus 5.5 (assinatura) como árbitro das divergências, sobretudo nos casos 001, 002, 007 e 009 e quando um segundo juiz barato (Flash-Lite temp 0) discordar. Julgamento por LLM; revisão médica continua pendente.

## Decisões de 05-10-2026 (segunda rodada de ajustes)
- **N = 3** trocas com o paciente (mais o exame físico) para liberar exames; a admissão não é bloqueada; limite de 10 turnos mantido.
- **Qwen3.8 Max Prime fora** da v3 (o mais caro).
- **Rodada-teste primeiro:** um modelo barato de bom desempenho anterior, 10 casos × 1 execução, para medir se melhora e quanto. Modelo proposto: **Qwen3.8 Max 0902** (cerca de US$ 0,044 por encontro nas runs antigas; 24/30 pelo juiz original e 21/30 com o Gemini Pro; quase não conversava com o paciente, 7% dos encontros, então é o que mais deve mudar). Comparação de base: suas 30 execuções anteriores, rejulgadas com o mesmo juiz Pro.
- Custo estimado da rodada-teste: cerca de US$ 0,6 a 0,9 (OpenRouter), mais uma centena de falas de paciente pelo limite do plano Pro.

## Implementação
`src/mira_runner/runner_v3.py` (protocolo), `scripts/run_v3.py` (agendador isolado, dry-run por padrão), `tests/test_v3.py`; `CaseTools.validate` foi extraído de `execute` sem mudar comportamento. Resultados em `runs/v3/<modelo>/runN` e `results/v3_<modelo>_runN.csv`, com colunas extras `protocol, patient_model, judge_model, patient_exchanges, gated_requests, investigation_orders, unread_orders`. O Opus como árbitro do juiz continua sendo uma etapa offline separada (`fidelity_eval.py`), a adaptar quando houver resultados.

## Correção das respostas de exame (apontada pelo usuário em 05-10-2026)
O usuário observou exames que existiam no caso sem retorno por nome e repetições sem aviso. Auditoria dos 1.349 pedidos de investigação nas 230 execuções (v1/v2 e extensões, heurística offline):
- **623 (46%)** voltaram como "Requested findings are not available" genérico, sem dizer quais exames; em pedidos com vários exames, os não encontrados simplesmente **sumiam** da resposta (ex.: pedido de hemograma e metabólico respondido só com troponina e NT-proBNP).
- **158 pedidos repetidos** de um mesmo exame, sem nenhum aviso de que já tinham sido pedidos.
- **Falsos negativos reais:** no caso 007, 'Hemolysis studies' contém bilirrubina e reticulócitos, mas pedidos de bilirrubina total/direta e de reticulócitos voltaram "não disponível" ou omitidos porque o associador LLM (GLM-4.5-Air) não os ligou: 54 ocorrências em 12 encontros. Outros casos de associação fraca existem (por exemplo, "Abdominal CT" da região adrenal não ligado a "Adrenal CT" no caso 006) e dependem do associador.
- **v1/v2 não são corrigidas** (permanecem como foram executadas); o efeito mais provável é no caso 007 (menos evidência de hemólise para o médico).

**v3** (`src/mira_runner/tools_v3.py`, `V3CaseTools`; `CaseTools` da v1/v2 só ganhou `validate` e `pool_for`, extraídos sem mudar comportamento):
1. Resposta **por exame pedido**: `findings` (com o nome pedido e o exame correspondente), `already_ordered_earlier` (não repete o dado) e `not_available_in_this_case` (cada exame ausente citado por nome). Mencionado no prompt do médico.
2. Analito literalmente presente num exame agrupado (ex.: bilirrubina em 'Hemolysis studies') volta **de forma determinística**, sem depender do associador; guarda de espécime impede pedido de urina/líquido de casar com valor sérico. Reprodução offline sobre os pedidos gravados: só 7 pedidos distintos mudam (todos no caso 007) e nenhum falso positivo novo apareceu.
3. Repetição só é "já pedido" se o mesmo dado (mesmo fato e mesmo analito) já foi retornado; outro analito do mesmo agrupamento conta como informação nova.
Limite: o resto da associação continua com o GLM-4.5-Air (v1/v2 idêntico); casos como "Abdominal CT" → "Adrenal CT" não são resolvidos aqui.

## Braço com JEF (guarda do paciente) — 05-10-2026
JEF (TypeSafe Jev, `jev-latest` → `jev-1.13.0`) devolve probabilidades tipadas, não texto. Validação offline sobre os dados gravados (custo US$ 0,03 para 224 + 440 itens):
- **Juiz:** a probabilidade de "mesma condição que a referência" concorda com o Gemini 3.1 Pro em 97% dos 224 (AUC 0,999) e com o juiz original em 89% (AUC 0,976). Escalonando ao Opus (assinatura) os 38 itens incertos ou em que o JEF diverge do Pro, o Opus arbitrou 55 itens no total: Pro concorda com o Opus em 50/55, JEF em 44/55, juiz original em 35/55, Flash-Lite temp 0 em 37/55. Veredito em cascata: 141/224 corretos (Pro 143, original 160); só 4 decisões mudam em relação ao Pro. Esse subconjunto foi escolhido por ser difícil; o Opus não é verdade de referência.
- **Paciente:** detecta "inventa detalhe fora do registro" com AUC 0,90 contra as marcações do Opus (270 positivas, 170 negativas); no limiar 0,30: precisão 0,88, recall 0,82. Deriva para linguagem de equipe: 2 positivos apenas.
**Guarda na v3 (`--jef`, braço separado `*_jef`):** após cada fala do paciente o JEF estima invenção e deriva; se invenção ≥ 0,30 ou deriva ≥ 0,50, o paciente (Sonnet) é chamado **uma vez** de novo com um lembrete e a segunda resposta substitui a primeira. Falha do JEF não bloqueia o encontro (resposta aceita, contada em `jef_failures`). Checagens ficam no log e são reaproveitadas na retomada. Colunas: `jef_guard, jef_checks, jef_retries, jef_failures`. Limite de gasto do JEF: US$ 5 (contabilidade a 6× o preço documentado de US$ 0,042 por milhão de tokens de entrada).

## Escalonamento GLM-5 → JEF → Qwen → Sonnet/Opus (`--cascade`, 05-10-2026)
Meta do usuário: manter os benefícios e reduzir o **custo por caso resolvido**. Implementado em `src/mira_runner/cascade.py` (braço novo, `*_cas`; as variantes v3 comuns não mudam):
1. **GLM-5 conduz a entrevista** como na v3 (exame junto, N=2). A chamada `admission` vira apenas uma **proposta**.
2. **Triagem pelo JEF** (cerca de US$ 0,001): escore combinado de "sustentado", "causa específica" e "sem alternativas relevantes" sobre a transcrição e a proposta. Se ≥ 0,90, a proposta é aceita e nenhum modelo mais forte é chamado (nos dados anteriores, esse corte aceitava 29 de 60 encontros com 1 erro).
3. **Qwen3.8 revisa em uma chamada** (sem ferramentas): concorda ou propõe outro diagnóstico e lista perguntas e exames que faltam. Aceita se concordar com confiança ≥ 0,70 e o JEF disser que é a mesma condição.
4. **Sonnet 5.5 (assinatura Pro, CLI)** vê as duas propostas e pode pedir **uma rodada** de perguntas ao paciente e exames antes de decidir; o **Opus 5.5 (assinatura Pro)** só desempata se o diagnóstico do Sonnet não coincidir com nenhum dos anteriores.
Os revisores veem só a transcrição, nunca a referência. Cada encontro grava o caminho percorrido (`cascade_path`), a proposta original e se ela estaria correta (`proposal_correct`, julgada à parte quando o final difere), e o **custo de implantação** (`deploy_cost_usd` = médico + associador + Qwen + JEF + custo equivalente de API dos Claude; o paciente simulado e o juiz são sobrecarga do benchmark e ficam fora). Resultado final julgado pelo Gemini Pro como nas demais variantes.

## Protocolo v3.2 (`--cascade --v32`, 05-10-2026)
Correções dos 7 pontos do relatório `v3_cascade_3runs_resolutions.md` e de dois pedidos do usuário. Tudo novo é opcional e as variantes anteriores não mudam.
1. **Exame definitivo antes da admissão:** o Opus faz um **mapa da consulta** no começo, com pouco contexto (só a queixa e o exame físico inicial; sem história, exames nem referência): urgência, 5 diagnósticos diferenciais com o que confirmaria cada um, exames decisivos (procedimentos e biópsias incluídos) e perguntas-chave. O GLM-5 recebe o mapa na primeira mensagem. Antes de admitir, se algum exame decisivo do mapa não foi pedido, o médico é lembrado **uma vez** (`nudged`).
2. **Achados operatórios e de patologia:** os revisores são instruídos a pedi-los quando o diagnóstico nomeia um mecanismo que só cirurgia ou biópsia confirma. Para isso funcionarem, os **pré-requisitos de procedimento** dos casos (`after_procedure:...`) agora são aplicados: uma biópsia ou um exame que exige procedimento antes é recusado e o médico é **informado de qual procedimento** pedir primeiro (por exemplo laparoscopia ou laparotomia antes de biópsia no abdome; pericardiocentese antes da angiografia coronariana). Só nas variantes com `--v32`.
3. **Auditoria aleatória dos aceites do JEF** (`--audit-rate`, sorteio determinístico por encontro).
4. **Gatilho extra do JEF** "falta exame definitivo relevante" ≥ 0,5 (`--definitive-trigger`), com a pergunta nova no `verify`.
5. **Revisor às cegas em todos os casos:** `--triage none` (padrão do `--v32`); `--triage jef` mantém a triagem. O revisor às cegas vê o mapa, não a proposta.
6. **Opus só na discordância:** o árbitro (Opus) é chamado apenas quando o Sonnet às cegas discorda da proposta ou tem confiança baixa, como antes, mais a chamada única do mapa. Isso muda o custo: o mapa custa uma chamada curta em **todos** os casos; a arbitragem custava uma chamada longa em cerca de 1 de cada 4. O saldo só se mede rodando.
7. **Gabarito do caso 009:** por decisão do usuário, "obstrução por stent migrado" passa a valer como correto nas rodadas v3.2 (`config/judge_overrides_v3.json`, `--v32`); o nome do divertículo de Meckel deixa de ser exigido. Vale só para essas rodadas (campo `rubric`), as anteriores permanecem como foram julgadas; revisão médica do critério segue pendente.
8. **Emergência sem N mínimo:** se o mapa do Opus marcar a urgência como `emergency`, os exames ficam liberados desde o início (sem exigir N trocas); nos demais casos o N=2 continua.
Campos novos nas tabelas: `consult_model, consult_urgency, nudged, prereq_blocks, rubric, audited`.

## Pontos em aberto
- Se o limite de 10 turnos deve subir para 12 depois de ver a rodada-teste (as regras gastam turnos).
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
