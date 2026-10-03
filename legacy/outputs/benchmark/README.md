# MIRA-2026 Frontier Model Benchmark — Local + Frontier

MVP retrospectivo em EHR simulado, inspirado metodologicamente em [MIRA, Nature 2026](https://doi.org/10.1038/s41586-026-10675-5). Contém dez casos públicos com PDFs oficiais, pacotes clínicos sequenciais, gabaritos/rubrics editoriais, adapters e **290 trajetórias terminais**: painel anterior de 230 em oito modelos (base 150, Sonnet 30, Terra 30, Luna 20/30) e 30 runs cada de Astra 6 e Sol 6.1. A execução Luna foi interrompida a pedido do usuário; suas dez lacunas não foram imputadas. **A revisão médica dos gabaritos e das decisões de segurança continua pendente; números clínicos antes dela são exploratórios.** O isolamento estrito de ferramentas internas do Codex CLI nos braços Codex não pôde ser provado; ver `docs/safety.md`. Nenhum sistema atende pacientes reais.

## Leitura

1. `SPEC.md` — arquitetura, decisões e gates.
2. `docs/case_selection.md` — fontes, DOI, links, licença e seleção.
3. `docs/model_registry.md` — três modelos Ollama instalados e sete braços de assinatura: Sol, Opus, Sonnet, Luna, Terra, Astra e Sol 6.1, sem API paga.
4. `docs/benchmark_schema.md` — contratos JSON, ferramentas e traces.
5. `docs/methodology.md` e `docs/safety.md` — protocolo, métricas, análise e riscos.
6. `docs/guideline_sources.yaml` — diretrizes separadas dos PDFs de caso.
7. `docs/jev_methodology.md` — Jev como auditoria editorial opcional e comparação com o desenho MIRA.
8. `docs/corpus_audit.md` — achados de fidelidade e correções antes do painel v5.
9. `docs/backlog.md` — fases e trabalho restante.
10. `docs/verification.md` — validação dos 150 traces, testes e integridade.
11. `results/summaries/REPORT.md` — análise exploratória do painel base; `results/review/review_queue.csv` — fila cega de revisão médica.
12. `docs/mira_reference_results.md` — resultados publicados do MIRA, comparação metodológica e painel dos dez casos atuais; explicita que os dez prontuários originais não são abertos.
13. `results/summaries/SOL_COST.md` — cálculo reproduzível do custo Sol equivalente à tarifa API, distinto da cobrança da assinatura.
14. `docs/extension_methodology_2026-09-28.md` — extensão com Sonnet 5.5 high, GPT-6 Luna high e GPT-5.6 Terra high.
15. `results/frontier_addons_2026-09-29/summaries/FRONTIER_ADDONS_REPORT.md` e `docs/frontier_addons_verification_2026-09-30.md` — painel consolidado e integridade dos traces.
16. `results/review_addons/round_2026_09_29_two/review_queue.csv` — 60 novos pacotes para adjudicação médica cega.

## Corpus

- `cases/case_001` a `case_010`: `source.pdf`, `source_metadata.yaml`, `case_packet.json`, `ground_truth.json`, `rubric.json`.
- `docs/source_manifest.json`: distribuição oficial PMC, URLs, DOI/licença e SHA-256 dos PDFs.
- `docs/corpus_freeze_manifest.json`: hashes dos cinquenta arquivos do corpus v3 após auditoria dos PDFs.
- `docs/protocol_freeze_manifest.json`: versão e hashes do prompt, simulador, ferramentas, adapters e runners; o painel principal usa o protocolo v5.
- `docs/evaluation_freeze_manifest.json` e `results/trace_manifest.json`: hashes do avaliador e dos 150 traces do painel.
- `docs/reference/mira_nature_2026.pdf`: artigo metodológico **fora** dos dez casos.

O modelo recebe somente `initial` e fatos liberados pela ferramenta do EHR. O catálogo de opções no arquivo é idêntico em todos os casos e não é enviado no prompt principal. PDFs, metadados, gabaritos e rubrics não entram no prompt.

## Execução e avaliação

A partir deste diretório:

```bash
python3 -B -m evaluation.metrics validate-cases --root .
python3 -B -m runner.run_case --provider ollama --model 'qwen3:8b' --case case_001 --repetitions 3
python3 -B -m runner.run_benchmark --models llama3.1:8b qwen3:8b qwen3.5:9b-mlx --repetitions 3
python3 -B -m runner.run_frontier --provider openai --model gpt-6-sol --repetitions 3
python3 -B -m runner.run_frontier --provider anthropic --model claude-opus-5-5 --repetitions 3
python3 -B -m evaluation.metrics validate-traces --root .
python3 -B -m evaluation.metrics summarize --root . --write
python3 -B -m evaluation.analyze_panel
python3 -B -m evaluation.estimate_sol_cost
python3 -B -m evaluation.prepare_review
```

OpenAI e Anthropic via CLI oficial exigem sessão da assinatura autenticada e acesso à rede/Keychain. Ver argumentos reais em `runner/run_benchmark.py` antes de repetir. O runner registra `results/raw/*.jsonl` e progresso em `results/summaries/`; pilotos e protocolos abortados ficam em `results/exploratory_*/` e não entram na análise principal. Uma tentativa encerrada por erro de provider foi preservada em `results/incomplete/` e excluída do denominador principal. As 150 trajetórias já terminaram; **não repetir** os comandos de runner para este painel. Os agentes não resgataram crédito de reset. O usuário reiniciou sua cota manualmente em 28-09-2026. A fila cega de revisão médica está em `results/review/`; a chave de identidade dos modelos está separada em `results/review_internal/` e não deve ser entregue aos revisores antes do consenso.

## Limites metodológicos

Este é um **public-case benchmark**: os casos podem constar no treinamento prévio dos modelos. Dez relatos de caso não estimam segurança clínica geral nem reproduzem a população MIMIC-IV do MIRA. Ollama usa chamadas nativas de ferramenta quando disponíveis; os sete braços de assinatura usam ação JSON emulada, controlada pelo mesmo EHR, e essa diferença de transporte precisa acompanhar os resultados. Diagnóstico textual e adequação clínica dependem de adjudicação médica cega.

## Extensão Sonnet + Luna + Terra, 28-09-2026

O usuário autorizou mais três braços, cada um com dez casos × três repetições: `claude-sonnet-5-5` high, `gpt-6-luna` high e `gpt-5.6-terra` high, via as mesmas assinaturas. A extensão usa o corpus v3 e o protocolo clínico v5 congelados, com adapters copiados dos originais e manifests adicionais `docs/protocol_extension_2026-09-28.json` e `docs/protocol_terra_extension_2026-09-28.json`. O Terra foi acrescentado após o início dos outros dois e recebe um manifest separado, preservando o primeiro freeze. As CLIs foram atualizadas desde o painel base; isso acompanha a interpretação de latência e custo. Estado da extensão: **encerrada a pedido do usuário, com Luna parcial**. Sonnet e Terra concluíram 30/30; Luna tem 20/30. Ver [checkpoint](docs/extension_execution_status_2026-09-28.md). A execução desses três braços terminou; Luna continua parcial por pedido do usuário e não será retomado. Os 150 runs anteriores não são repetidos nem alterados.

Comandos históricos da extensão, apenas para reprodutibilidade. **Não executar runners novamente sem nova autorização do usuário.** Os schedulers pulam combinações terminais e impedem dois processos do mesmo modelo:

```bash
python3 -B -m runner.run_extension --model claude-sonnet-5-5
python3 -B -m runner.run_extension --model gpt-6-luna
python3 -B -m runner.run_terra_extension --model gpt-5.6-terra
python3 -B -m evaluation.analyze_extension
```

A análise disponível está em [PARTIAL_COMBINED_REPORT.md](results/extension_2026-09-28/summaries/PARTIAL_COMBINED_REPORT.md), gerada com `python3 -B -m evaluation.analyze_extension --partial`. “Parcial” refere-se ao Luna, não aos sete outros braços já encerrados. Falhas de provider e um prefixo interrompido pelo usuário permanecem em `incomplete/`, com proveniência separada; não contam como trajetórias terminais. A revisão médica dos resultados continua pendente.

## Consolidação após interrupção solicitada

- [Relatório dos oito braços disponíveis](results/extension_2026-09-28/summaries/PARTIAL_COMBINED_REPORT.md).
- [Verificação técnica e limites](docs/extension_verification_2026-09-28.md).
- [Consumo de tokens e tentativas](docs/subscription_usage_2026-09-28.md).

Luna não foi extrapolado para 30 runs e casos ausentes não foram imputados como erro ou acerto. Segurança, alternativas aceitáveis e condutas dependem de revisão médica cega. Os 150 traces originais permanecem intactos.

### Análise após encerramento

[Leitura clínica e operacional dos resultados](docs/results_interpretation_2026-09-28.md) resume os achados, custos e limitações. A [fila adicional de revisão](results/extension_2026-09-28/review_partial/review_queue.csv) tem 80 trajetórias; os 240 registros de adjudicação estão em `review_partial/review_decisions.csv`. A chave fica em `review_partial_internal/`, separada dos pacotes cegos.

## Extensão Astra e Sol 6.1 concluída

O usuário adicionou Astra 6 e Sol 6.1 em high. Ambos concluíram **30/30 trajetórias terminais** nos mesmos dez casos e três repetições, com corpus v3 e protocolo clínico v5 preservados. Uma tentativa operacional Astra falhou imediatamente sob rede restrita, foi preservada em `incomplete/` e teve a mesma combinação concluída com acesso de rede. Os 230 terminais anteriores estão preservados. O [relatório consolidado](results/frontier_addons_2026-09-29/summaries/FRONTIER_ADDONS_REPORT.md) validou **290/300 combinações planejadas**; as dez lacunas são exclusivamente do Luna, cuja execução permanece interrompida a pedido do usuário. A [fila cega adicional](results/review_addons/round_2026_09_29_two/review_queue.csv) contém 60 trajetórias para revisão médica. Os matches de diagnóstico são triagem lexical, não acurácia clínica adjudicada. Os custos de API são proxies hipotéticos, não cobranças da assinatura. Ver [acesso e diferenças entre CLI e aplicativo](docs/astra_sol61_access_2026-09-29.md).
