# Extensões Sonnet 5.5 high + GPT-6 Luna high + GPT-5.6 Terra high — 28-09-2026

## Objetivo e escopo

Adicionar três braços à comparação existente: `claude-sonnet-5-5` pelo Claude Code autenticado na assinatura e `gpt-6-luna` / `gpt-5.6-terra` pelo Codex CLI autenticado na conta ChatGPT. Os três solicitam esforço `high`. Os três modelos locais, GPT-6 Sol e Claude Opus do painel base permanecem como referências existentes, totalizando oito modelos, dez casos e três repetições: **240 trajetórias previstas**. Nenhum modelo local novo é instalado.

O corpus continua `mvp10_v3_2026-09-26`; o protocolo clínico continua `mvp10_closedbook_v5_2026-09-26`. O manifest Sonnet/Luna mantém `mvp10_extension_sonnet_luna_2026-09-28`; Terra tem manifest próprio `mvp10_extension_terra_2026-09-28`. O primeiro manifest não é alterado para incluir Terra. Os 150 traces base, prompts, cases, EHR, schemas, runner v5, rubrics e relatório anterior são preservados. A extensão mede diferenças dentro deste corpus público; não replica os casos MIMIC-IV do MIRA e não permite calcular melhoria direta sobre os 88,9% publicados.

## Condições clínicas constantes

Mesmos fatos, gates temporais e ordem de disponibilização por solicitação; mesmo prompt de médico; mesmas onze ferramentas EHR; mesmas regras de argumento e de stopping. O catálogo não é mostrado ao modelo. O runner usa temperatura solicitada 0, saída solicitada 2.048 tokens, contexto local nominal 24.000, seed solicitada igual à repetição, 40 ações, 60 turnos, 3.600 segundos e interrupção após três solicitações idênticas consecutivas. Esses valores não provam que as CLIs de assinatura aceitem temperatura, seed ou limite de saída; distinguir solicitação do suporte real de cada transporte.

O histórico é reenviado a cada ação pela CLI, com emulação JSON de uma ação clínica por resposta. O harness executa as ferramentas. Não há braço de retrieval nesta extensão. As mesmas limitações do isolamento da CLI descritas em `safety.md` continuam válidas: instruções de closed-book e modo read-only não demonstram bloqueio perfeito de toda ferramenta interna. Esforço high é uma configuração solicitada; não equivale a um orçamento de raciocínio idêntico entre fornecedores.

O texto clínico base é igual, mas as instruções efetivas de sistema não são totalmente controladas: Claude recebe `--system-prompt`, enquanto Codex recebe as mensagens clínicas serializadas dentro de seu prompt e mantém instruções internas da CLI. Os wrappers herdados de Sol/Opus são preservados nos novos braços. Assim, esta comparação observa **modelo + transporte da assinatura**, não somente pesos de um LLM sob um sistema universal idêntico.

## Drift de transporte e identidade do modelo

O Luna passou um ping sintético independente dos casos. Codex CLI usado na extensão: **0.158.0-alpha.2.1**, executável `/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex`; o painel Sol usou versão 0.155. As mesmas flags e semântica clínica são mantidas, mas a mudança de versão/data é confundimento potencial. Registrar versão/executável no manifest da extensão; não chamar a comparação de troca pura de modelo.

Para Luna e Terra, cada resposta registra `model_requested` igual a `gpt-6-luna` ou `gpt-5.6-terra`, respectivamente, e `effort_requested=high`; a inferência aceita essa solicitação. A CLI não expõe slug servido nas respostas: `model_observed=null`, explicitamente. Não inventar verificação de modelo observado. Para Sonnet, cada resposta deve incluir `models_reported` contendo exclusivamente o slug Sonnet esperado; resposta com modelo diverso ou ausência de evidência bloqueia análise. O index contém modelo solicitado, observado quando mensurável e esforço; os headers `model_id` dos traces são identificadores do braço, não prova independente de identidade servida.

Adapters copiados do transporte base alteram apenas ID e validação específica de identidade. O manifest congela os hashes desses adapters e do scheduler de extensão. Alterações futuras exigem outro identificador ou registro explícito de revisão antes das runs.

## Arquivos e fronteira entre base e extensão

| Artefato | Caminho relativo ao benchmark |
|---|---|
| Manifest Sonnet/Luna | `docs/protocol_extension_2026-09-28.json` |
| Manifest Terra separado | `docs/protocol_terra_extension_2026-09-28.json` |
| Traces Sonnet/Luna | `results/extension_2026-09-28/raw/*.jsonl` |
| Traces Terra | `results/extension_terra_2026-09-28/raw/*.jsonl` |
| Falhas de provider preservadas | `results/extension_2026-09-28/incomplete/` |
| Index Sonnet | `results/extension_2026-09-28/summaries/sonnet_progress.jsonl` |
| Index Luna | `results/extension_2026-09-28/summaries/luna_progress.jsonl` |
| Index Terra | `results/extension_terra_2026-09-28/summaries/terra_progress.jsonl` |
| Analisador aditivo | `evaluation/analyze_extension.py` |
| Exportador de revisão dos 90 novos runs | `evaluation/prepare_extension_review.py` |
| Relatório combinado final | `results/extension_2026-09-28/summaries/COMBINED_REPORT.md` |
| Resultados combinados estruturados | `results/extension_2026-09-28/summaries/combined_analysis.json` |

O manifest declara `extension_version`, `base_protocol_version`, `corpus_version`, `models`, `files` e tarifas verificadas quando disponíveis. Cada definição de modelo declara provider, effort, adapter e progress_path. Cada trace permanece no diretório de sua extensão, com identificação da origem no agregado. Os índices usam run_id e versões para impedir mistura de tentativas ou protocolos. Falhas de conta/provider são tentativas operacionais, arquivadas sem substituir trace; não entram como falha clínica no denominador. Ausência de diagnóstico EHR aceito em uma trajetória clínica terminal entra como falha diagnóstica na triagem lexical. Nunca descartar uma trajetória por erro clínico, repetição improdutiva ou esgotamento de ações.

## Validação antes da análise

1. Verificar os bytes de todos os arquivos nos manifests base, corpus e as duas extensões, incluindo PDFs, case packets, gabaritos e rubrics.
2. Validar sintaxe, encadeamento, pairing de chamadas/resultados e evento terminal por `validate_trace`, sem mudar suas regras.
3. Conferir SHA-256 do packet, prompt e schema serializado, quantidade de ferramentas, limites clínicos e configuração solicitada em cada trace, inclusive base.
4. Cruzar cada trace novo com index do provider e modelo; conferir corpus/protocolo/extensão, provider, case_id, repetição, modelo solicitado, esforço e stopping_reason.
5. Conferir modelo/esforço solicitado em **cada** resposta, slug Sonnet observado e ausência explicitamente declarada de slug Luna/Terra observado.
6. Recusar run_id duplicado entre base/extensão e combinação duplicada de modelo/caso/repetição; aceitar apenas casos 001–010 e repetições 1–3.
7. Exportar relatório final apenas com 30 trajetórias distintas por modelo e **240 terminais**, incluindo os 90 novos traces. Painel parcial exclui somente traces ativos ou terminais ainda sem index durante flush; tais ausências ficam visíveis nas contagens.

O analisador registra hashes do scorer, regras diagnósticas, analisador e os dois manifests de extensão. Reutiliza `score_run` e `diagnosis_aliases.json` v2 sem alterar scoring. Nenhum LLM adjudica segurança de forma autônoma.

Antes de qualquer exportação, todos os campos de cada modelo base são comparados exatamente aos valores de `results/summaries/exploratory_analysis.json`, incluindo por-caso, denominadores, intervalos e recursos. Divergência interrompe a análise; o hash do artefato anterior e o resultado da verificação ficam no JSON combinado.

## Estatística e interpretação

Métricas separadas: conclusão, diagnóstico publicado e alvo do encontro por conceitos, top-3, disposition exata do relato, pedidos, erros de ferramentas, passos até identificação, duração e recursos. Comparar métricas de processo como contagens de **tentativas** de ações; pedidos bloqueados/inválidos não equivalem a exames realizados ou fármacos administrados. Adequação clínica, condutas alternativas, concordância com diretrizes e segurança continuam pendentes de médico cego.

Cada caso recebe o mesmo peso; as três repetições ficam agrupadas no caso. Bootstrap descritivo de 10.000 reamostragens dos dez casos, seed 20260925. Painel completo: média por caso equivale à proporção das 30 runs. Painel parcial: mostrar contagem bruta e casos observados, sem imputar runs ausentes; não interpretar a média dos casos observados como proporção bruta de todas as runs previstas. Intervalos só com dez casos × três repetições. Comparações pareadas globais só após completar os oito braços; todos os pares são exploratórios, sem declaração confirmatória baseada em múltiplos testes.

A identidade pública dos casos, amostra pequena/intencional, diferenças de transporte, atualização da CLI, ordem não randomizada e datas distintas limitam causalidade. Os novos modelos executados após consulta aos resultados base constituem extensão exploratória, não experimento preregistrado prospectivo. Caso 003 conserva alvo de apresentação (ruptura do reservatório) separado da sepse pós-operatória no diagnóstico publicado.

## Uso de tokens e custo

Separar três campos: **uso reportado**, **custo equivalente reportado pela CLI**, **proxy API calculado**. Nenhum deles mede cobrança real atribuível à assinatura; esse valor permanece desconhecido. Não somar entrada/cache de fornecedores distintos como métrica padronizada de eficiência. Energia local não é medida.

Tarifas Luna Standard verificadas em 28-09-2026 na [documentação oficial](https://developers.openai.com/api/docs/models/gpt-6-luna): por milhão de tokens, entrada $0,10; cache lido $0,01; cache escrito $0,125; saída $0,50. A página declara que pedidos com mais de 272.000 tokens de entrada têm outro tier (2× entrada/cache, 1,5× saída). O cálculo inicial limita-se a chamadas até esse limiar; acima dele produz ausência com motivo explícito, sem aplicar silenciosamente tarifa curta.

Tarifas Terra Standard verificadas em 28-09-2026 na [documentação oficial GPT-5.6 Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra): por milhão de tokens, entrada $2,00; cache lido $0,20; saída $12,00. A página declara cache escrito a 1,25× entrada comum, portanto $2,50/M; pedidos com mais de 272.000 tokens de entrada têm 2× entrada e 1,5× saída. Como no Luna, o cálculo inicial exclui chamadas acima do limiar em vez de extrapolar o tier curto. Evidência consultada: seção Pricing (linhas 882–923 na extração oficial), com modelo high documentado na descrição. Tarifas/URL/data também ficam congeladas no manifest Terra; são preços hipotéticos de API, não cobrança observada da assinatura.

Para Codex CLI, cache lido é subconjunto da entrada total e raciocínio é subconjunto da saída. Usar, por chamada, `((input-cached-writes)×0.10 + cached×0.01 + writes×0.125 + output×0.50)/1e6`. Para Terra, substituir os quatro coeficientes por 2,00 / 0,20 / 2,50 / 12,00, respectivamente. Não cobrar raciocínio duas vezes. Cache-write reportado usa `cache_write_input_tokens` (zero quando não reportado); apresentar sensibilidade com toda entrada não cacheada tratada como gravação. Validar subconjuntos, contagens e máximo por chamada, não o agregado de toda a trajetória. Tarifas ausentes/não verificadas ou uso incompleto produzem `null`, não custo zero.

Sonnet conserva o `cost_estimate_usd` reportado pelo Claude Code nos eventos, com semântica de estimativa equivalente. Os valores calculados Luna/Terra e reportados Claude não são comparação econômica controlada: a estrutura de reenvio/contexto/cache difere. O proxy Sol anterior é preservado na coluna calculada, importado de `results/summaries/SOL_COST.json` após verificar os totais contra os 30 traces base e recalcular a aritmética em modo somente leitura: $4,6561284 principal; $5,1924309 na sensibilidade. A coluna reportada continua indisponível para Sol; a calculada não deve desaparecer do combinado.

Os custos do painel abrangem somente suas trajetórias clínicas terminais e não representam todo o custo operacional da tarefa. Preflights, pilotos e tentativas com erros de conta/provider ficam fora. O JSON combinado lista separadamente uso/custo disponível dos traces preservados nos diretórios `incomplete/` de Sonnet/Luna e Terra, sem adicioná-los ao denominador de desempenho e sem fingir que tentativas sem uso reportado custaram zero.

## Comandos de análise (não iniciam inferência)

Executar na raiz de `outputs/benchmark`:

```sh
python3 -B -m evaluation.analyze_extension --partial
python3 -B -m evaluation.analyze_extension
python3 -B -m evaluation.prepare_extension_review
```

O primeiro escreve apenas `PARTIAL_COMBINED_REPORT.md` e `partial_combined_analysis.json`. O segundo recusa um painel incompleto e escreve os dois artefatos finais combinados. O terceiro exige os 90 novos runs completos e exporta somente esses runs para a revisão da extensão. Nenhum comando altera `results/raw`, `results/summaries/REPORT.md`, cases ou scoring; nenhum inicia runs.

## Adjudicação

Os 90 novos blind_ids são exportados por `prepare_extension_review.py` para `results/extension_2026-09-28/review/`, preservando todas as adjudicações existentes em `results/review/`. Chave de cegamento separada em `extension_2026-09-28/review_internal/`; não fornecer esse diretório aos revisores. Packet contém contexto inicial, chamadas/resultados, erros e encerramento sem provider/modelo ou métricas automáticas. Cada blind_id tem formulários primary/second/consensus e tabelas por ação, oportunidade e evento de segurança. Classes: correct / acceptable_alternative / questionable / unsafe. Revisão secundária/consenso segundo `adjudication.md`; nenhum LLM como juiz final de segurança.

O exportador recusa regravar uma fila/packet/formulário ou chave existente. Isso protege adjudicações preenchidas; para nova rodada, criar snapshot/diretório versionado, não remover decisões médicas. As extensões não modificam automaticamente a classificação clínica dos 150 runs base.

## Interrupções de conta e transporte

O usuário reiniciou a cota durante a execução da extensão em 28-09-2026; os agentes não chamaram a ferramenta de resgate de crédito. A retomada conserva os traces anteriores e reinicia somente combinações não terminais como nova tentativa, sem reutilizar contexto clínico entre tentativas.

`provider_or_runner_error` não identifica por si só a causa. No adapter Codex, `OpenAIAccountError` também abrange erro de saída da CLI, ausência de ação final, JSON malformado e argumentos inválidos. O runner preserva a classe, mas oculta a mensagem detalhada por segurança de conta. Um probe sintético aceito verifica acesso naquele momento; não demonstra a causa de uma falha clínica anterior. Não atribuir todas essas tentativas a autenticação, quota ou desempenho clínico.

Métricas principais são condicionadas às trajetórias terminais válidas. Quantidade de tentativas com erro, combinação, uso conhecido e custos de prefixos aparecem à parte. O custo disponível de um prefixo não é necessariamente o custo total da tentativa com erro. Latência de trajetória inclui demora da CLI, rede e serviço e não isola tempo de raciocínio; não subtrair atrasos ou imputar uso ausente retrospectivamente.

## Quadro operacional aditivo

O analisador combinado apresenta, separadamente das métricas clínicas, oito linhas com 30 trajetórias planejadas, terminais clínicas observadas, terminais concluídas, tentativas encerradas com erro preservadas, total de tentativas encerradas observadas, concluídas/30 planejadas e concluídas/encerradas observadas. A última taxa é **condicional e pós-hoc**, não estimativa incondicional de confiabilidade do modelo ou provider. Retries são selecionados e dependentes; não calcular IC IID para essa taxa nem misturá-la ao bootstrap clínico por caso.

Contar somente erros fechados `provider_or_runner_error` nos diretórios `results/incomplete/` e `incomplete/` das duas extensões, com identidade, sequência e evento terminal válidos, hashes do packet/prompt/schema e configuração/limites correspondentes ao freeze atual. Deduplicar por run_id; sobreposição com o painel terminal não soma outra tentativa. Registros de outro protocolo/corpus, prefixos sem fechamento, arquivos inválidos e duplicatas ficam identificados como evidência excluída. Inventário ausente ou não verificável produz `unknown`; a completude histórica da preservação continua desconhecida mesmo em diretório legível. Zero erros preservados não prova ausência de erros reais. Tentativas ativas não integram o denominador de encerradas.

Os custos e tokens de uma tentativa com erro representam apenas **uso parcial conhecido do prefixo**. A última chamada falha pode ter executado e consumido recursos sem devolver eventos de uso: não declarar que o custo do prefixo é o custo total dessa tentativa, nem interpretar ausência de eventos como zero. A classe `OpenAIAccountError` e um probe passivo posterior não identificam retrospectivamente a causa das falhas anteriores. O wrapper externo `scripts/run_with_provider_diagnostics.py` registra categorias seguras em `results/provider_diagnostics_2026-09-28/`; essas evidências prospectivas não alteram os freezes nem o scorer clínico.

Categorias passivas entram somente como observações parciais separadas. O analisador registra o hash do snapshot de cada sidecar, linha, UTC e ativações `start`; ignora essas ativações na associação de erros. Uma categoria só é atribuída a uma tentativa quando há o mesmo modelo e um **único** evento `error` com distância UTC absoluta de até dois segundos, com unicidade nos dois sentidos. Registros sem correspondência ou ambíguos não identificam a causa de nenhum trace. A cobertura é prospectiva desde as ativações registradas, possivelmente com lacunas; tentativas anteriores mantêm categoria/causa desconhecida.

`arguments_json_invalid`, `action_json_invalid`, `action_count_invalid`, `action_argument_item_invalid` e `arguments_not_object` identificam falha de formato observada pelo adapter. Essas tentativas aparecem na contagem operacional de **falhas de formato confirmadas (cobertura parcial)**, conservando seu estado operacional e o denominador clínico original. Não reclassificar retroativamente o scorer. Zero outputs inválidos nas trajetórias terminais não demonstra ausência de falhas de formato em todas as tentativas. A evidência não recupera stdout nem tokens da última chamada que falhou; seu uso e custo continuam desconhecidos.

Para avaliar segurança de todas as tentativas observadas, a revisão médica deve incluir também os prefixos clínicos elegíveis preservados em `incomplete/`, além das 240 trajetórias terminais. A fila principal de 150 + 90 packets não representa automaticamente essa revisão adicional. Ausência de adjudicação nesses prefixos não equivale a ausência de erro clínico; os denominadores clínicos principais e operacionais permanecem separados.

## Cota compartilhada da assinatura

A cota de Codex/ChatGPT pertence à conta e é compartilhada com outras tarefas e usos; um snapshot de limite não mede consumo exclusivo do benchmark. O projeto não dispõe de fórmula verificável que converta tokens reportados, preço hipotético de API ou número de runs em pontos percentuais dessa cota. Não inferir consumo da assinatura pelo proxy monetário nem atribuir toda variação de cota ao benchmark.

O protocolo solicita raciocínio `high` e reenvia o histórico clínico progressivamente maior em cada ação. A CLI também acrescenta instruções internas, serialização e overhead que o harness não controla integralmente. Isso explica por que dez casos × três repetições representam muitas chamadas e bastante contexto reprocessado, mas não estabelece uma fórmula quantitativa de cobrança de cota. Tokens de raciocínio permanecem subconjunto da saída reportada; cache é apresentado conforme semântica de cada CLI. Manter snapshots de quota da conta, uso do benchmark e custo API equivalente em campos separados, com data e cobertura explícitas.

## Consolidação parcial por solicitação do usuário

O usuário solicitou parar a execução e analisar os resultados disponíveis em 28-09-2026 local (registro de interrupção em 29-09-2026 UTC). O planejamento congelado permanece 240 trajetórias; a consolidação observada contém **230**: base 150, Sonnet 30, Terra 30 e Luna 20. As dez combinações Luna ausentes não são imputadas como zero, nem entram na proporção entre runs observadas. Luna tem 20/30 planejadas e conclusão clínica 20/20 entre suas terminais; essas frações medem aspectos diferentes. Não gerar comparações pareadas globais que dependam do braço Luna completo.

O prefixo Luna `b35ed940-14e8-41ea-b937-5011e3d5ca74`, caso 007 repetição 3 tentativa 2, foi preservado byte a byte sem sintetizar `run_ended`. A anotação `results/extension_2026-09-28/summaries/user_stop_2026-09-28.json` associa SHA-256, identidade e contagem de eventos ao motivo `user_requested_execution_stop`. Esse prefixo não é erro de provider e não integra o painel terminal ou a taxa condicional terminal+erro. Uso conhecido aparece separadamente; uso/custo da última chamada permanece desconhecido.

Exportações desta consolidação:

```sh
python3 -B -m evaluation.analyze_extension --partial
python3 -B -m evaluation.prepare_extension_review --partial
```

O relatório estruturado e legível permanece em `summaries/partial_combined_analysis.json` e `summaries/PARTIAL_COMBINED_REPORT.md` da extensão Sonnet/Luna. A revisão contém **80 novos packets terminais** em `results/extension_2026-09-28/review_partial/`, com escopo declarado em `review_scope.json`; a chave está separada em `review_partial_internal/`. Há 240 registros primary/second/consensus. Erros preservados e prefixos interrompidos exigem revisão adicional; a fila parcial não certifica sua segurança.

O modo padrão dos helpers conserva os gates 240/90 e os destinos finais. O modo parcial usa destinos separados e recusa sobrescrever quaisquer packets, formulários ou chaves existentes. Todos os scores base e o proxy Sol são preservados; nenhum freeze clínico é reescrito e nenhuma inferência é iniciada pelos comandos de análise/revisão.
