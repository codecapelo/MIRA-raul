# Comparação aditiva Astra e eventual GPT-6.1 Sol — 29-09-2026

## Desenho preservado

O painel de referência contém **230 trajetórias terminais**: 150 do protocolo inicial, 30 Sonnet, 30 Terra e 20 Luna. A execução Luna foi encerrada a pedido do usuário. Suas dez combinações faltantes permanecem ausentes, sem imputação. Os oito modelos, métricas, traces, custos calculados e relatório parcial anteriores são preservados. Um braço Astra com 30 trajetórias levaria o observado a 260/270 planejadas; caso GPT-6.1 Sol high seja efetivamente acessível e execute 30, o observado passa a 290/300 planejadas. O denominador planejado inclui as dez Luna não executadas e não se torna um denominador de acurácia.

Os braços adicionais usam os mesmos dez packets, prompt médico, onze ferramentas, EHR sandbox, regras temporais, stopping, temperatura solicitada zero, seed nominal por repetição e `evaluation-v2`. O modelo não recebe o caso completo no início nem consulta a internet durante sua resolução. O usuário pediu assinaturas, não API; modelo solicitado e inferência aceita são registrados, enquanto o slug realmente servido não é exposto pela CLI. Essa diferença é preservada em `model_observed=null`.

O manifest Astra fica em `docs/protocol_astra_extension_2026-09-29.json`, com adapter e runner congelados por SHA-256. [A documentação oficial Astra](https://developers.openai.com/api/docs/models/gpt-6-astra) confirma `high` e preços Standard por milhão de tokens: entrada US$10, cache lido US$1, cache escrito US$12,50, saída US$50. Acima de 272 mil tokens de entrada por chamada, há outro tier: 2× entrada/cache e 1,5× saída para o pedido inteiro. O proxy calculado usa somente chamadas até esse limiar; acima dele, registra ausência com motivo, sem extrapolar tarifa curta. Cache lido integra entrada e raciocínio integra saída, portanto não se somam novamente. Cobrança real da assinatura permanece desconhecida.

O segundo braço só entra mediante argumento explícito `--additional-manifest`, apontando para um manifest próprio congelado em `docs/`. O manifest preparado `docs/protocol_sol61_extension_2026-09-29.json` declara `gpt-6.1-sol`, CLI npm 0.159.1 e acesso low verificado; no momento de preparação, **acesso high ainda não estava validado** e não havia run clínico. O modelo suporta `high` segundo sua [página oficial](https://developers.openai.com/api/docs/models/gpt-6.1-sol), mas isso não substitui a verificação de acesso da conta pelo runner. O Astra declara CLI bundled 0.158.0-alpha.2.1; versão/data/transporte são confundidores adicionais. A página de preços de API não prova cobrança ou identidade do modelo servido via assinatura.

## Validação e análise

`evaluation/analyze_frontier_addons.py` lê o painel preservado em modo somente leitura e confere **todos os campos de cada um dos oito modelos** contra `results/extension_2026-09-28/summaries/partial_combined_analysis.json`. Divergência impede a análise. Registra o SHA-256 do arquivo anterior e de cada manifest adicional. Para cada novo trace, exige index correspondente, versão de corpus/protocolo/extensão, mesmo hash de packet/prompt/schema, mesmas onze ferramentas, limites, case/repetição, modelo e esforço high solicitados em toda resposta e slug observado nulo. Rejeita duplicações de run_id ou modelo/caso/repetição. Tentativas com erro preservadas ficam em `incomplete/` e nunca no denominador clínico; uso e custo desses prefixos não incluem necessariamente a última chamada que falhou.

O relatório completo exige 30 terminais válidos por novo modelo habilitado. O modo `--partial` produz arquivos com nomes diferentes enquanto o runner está ativo; não altera resultados anteriores. Cada caso recebe o mesmo peso após três repetições; IC descritivo vem de bootstrap por dez casos, 10 mil reamostragens. Somente quando os novos braços e seus comparadores têm 10 casos × 3 runs, são calculadas diferenças pareadas exploratórias para conclusão e match conceitual provisório. Luna parcial fica fora do pareamento. Nenhum resultado lexical ou de processo equivale a acurácia clínica adjudicada, e não há score composto arbitrário. Ordem temporal, treinamento prévio nos casos públicos, diferenças entre CLIs e alta demanda de contexto impedem atribuição causal exclusiva ao modelo.

O preço API equivalente Astra é um **proxy**, assim como os proxies prévios Sol/Luna/Terra; custo equivalente Claude reportado pela CLI é outra medição. Não somar ou comparar essas colunas como cobrança real. Para GPT-6.1 Sol, a [tarifa Standard oficial](https://developers.openai.com/api/docs/models/gpt-6.1-sol) em 29-09-2026 por milhão de tokens é: entrada US$2, cache lido **US$0,10**, cache escrito US$2,50, saída US$10. Acima de 272 mil tokens por chamada, a página declara 2× entrada/cache e 1,5× saída para o pedido inteiro; chamadas assim ficam fora do proxy curto e recebem motivo. O cache lido de Sol 6.1 não usa a tarifa US$0,20 do Sol 6.0. A tarifa verificada foi registrada no manifest de Sol 6.1 **antes de qualquer run clínica**; com zero runs, o proxy calculado continua `null`. A cota Codex/ChatGPT é compartilhada com outros usos e não há fórmula confiável que converta tokens ou proxies API em porcentagem dessa cota.

## Comandos de análise preparados

Na raiz de `outputs/benchmark`:

```sh
python3 -B -m evaluation.analyze_frontier_addons --partial
python3 -B -m evaluation.analyze_frontier_addons
python3 -B -m evaluation.analyze_frontier_addons --additional-manifest docs/protocol_sol61_extension_2026-09-29.json --partial
python3 -B -m evaluation.analyze_frontier_addons --additional-manifest docs/protocol_sol61_extension_2026-09-29.json
```

O primeiro par considera Astra; o segundo, Astra e um manifest adicional, se houver acesso high e traces. O modo completo recusa menos de 30 terminais em qualquer braço incluído. A saída nova usa `results/frontier_addons_2026-09-29/summaries/`, sem sobrescrever `PARTIAL_COMBINED_REPORT.md`, `partial_combined_analysis.json` ou os relatórios base. Esses comandos somente leem/scoram traces já produzidos; não iniciam inferência.

## Revisão médica cega

`evaluation/prepare_frontier_addons_review.py` gera apenas packets das novas trajetórias terminais: 30 no round de um braço ou 60 no round de dois braços. `--partial` aceita as trajetórias já terminais em um round separado. Os diretórios públicos são `results/review_addons/round_2026_09_29_one` ou `round_2026_09_29_two`; chaves modelo/run_id ficam em `results/review_addons_internal/` no round correspondente. O nome do modelo não aparece no packet ou na fila. Há formulários primary/second/consensus, por ação, oportunidade e evento de segurança; exportação recusa regravar decisões existentes. Fonte, ground truth e rubric originais são ligados por caso. As 230 trajetórias anteriores e os prefixos preservados requerem filas/adjudicação próprias; nenhuma revisão automática determina segurança ou adequação de tratamento sem médico.

```sh
python3 -B -m evaluation.prepare_frontier_addons_review
python3 -B -m evaluation.prepare_frontier_addons_review --additional-manifest docs/protocol_sol61_extension_2026-09-29.json
```

Preparar scripts não executa revisão médica. A exportação fica pendente de 30 runs por braço incluído; decisões clínicas permanecem pendentes de revisor humano.

## Controle de cota da retomada

A automação usa invocações do scheduler com `--max-runs 1`, verifica a quota antes de cada combinação e aguarda renovação quando a janela de cinco horas atingir 85% de uso ou a semanal 90%. Isso não altera o número de ações/turnos permitido dentro da trajetória, prompts, ferramentas, rubric ou a interpretação dos runs. O limiar evita que uma invocação longa atravesse todo o restante da quota sem inspeção.
