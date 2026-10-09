# MIRA-RAUL

<!-- V4_CURRENT_START -->
## v4 — implementação e avaliação concluídas

[Abrir artefato interativo, comparação e animação](reports/v4_comparison.html) · [relatório final](reports/v4_final_summary.md) · [auditoria factual](reports/v4_working_fidelity.md).

| Condição, mesmos dez públicos | Aceitos pelo juiz LLM | OpenRouter, todos os atores |
|---|---:|---:|
| Claude v3.6, histórico | 10/10 | US$0.35023969 |
| v4 original, Sol + cascade | 9/10 | US$0.12304050 |
| v4 com hipótese de trabalho Astra, dez novos encontros | 10/10 | US$0.11515425 |
| Revisão Astra offline dos traces originais, pós-hoc | 10/10 | US$0.045766 |

A revisão offline não é encontro novo e não substitui o resultado original. São casos conhecidos durante desenvolvimento, uma execução por caso/condição; diferenças de modelo, transporte e protocolo impedem conclusão causal ou superioridade clínica. Juiz LLM não estabelece acurácia clínica100%; revisão médica cega pendente.

OpenAI usa somente a assinatura ChatGPT/Codex; seu custo monetário é desconhecido. Gemini matcher/juiz usa OpenRouter, sem fallback. Gasto adicional global v4 **US$0.28396075**, tetoUS$5, restanteUS$4.71603925; a conta reporta adicionalUS$0.265806750, diferençaUS$0.018154000 em investigação, quatro metadados de juiz404. Custos recebidos não foram zerados. As unidades1/5/15 de exames são artificiais, com fonte deduplicada entre médico e revisores, inclusive painéis; não são dólares nem preços hospitalares.

Melhorias: extração literal qualitativa/numérica, política aplicada também à revisão, limite de pedidos respeitado pela fila, isolamento da assinatura sem ferramentas externas, replay integral por hash, revisão final que distingue hipótese de confirmação e informa achados não confirmados/próximos passos. A animação permite reproduzir horários e etapas reais, pausar, acelerar e ir ao final; o início de chamadas CLI é estimado pela latência. Os tempos são de execução do teste.

Persistem diferenças entre pedido e protocolo/ensaio retornado, achados de seguimento liberados cedo e fontes históricas devolvidas para pedidos novos. O protótipo temporal foi testado em software, mas não participa dos encontros apresentados. Os100% do juiz, quando presentes, não eliminam essas limitações. Nenhum terminal anterior foi reexecutado ou sobrescrito.

**Validação de software:** 238 testes aprovados. O [registro opcional da fila](reports/post_evaluation_release_logging.md) foi corrigido após a avaliação e não integrou estes encontros.

Base Claude correta: c1d3270(v3.7); condição nova congelada em2fac24e. [Protocolos](reports/v4_working_encounters_protocol.md), [manifesto30traces](reports/v4_all_trace_manifest.json), [conciliação](reports/v4_global_billing_reconciliation.json). Não há nova inferência pendente ou autorizada após esta consolidação.
<!-- V4_CURRENT_END -->


Avaliação exploratória de agentes diagnósticos em dez casos públicos previamente utilizados, com médico, paciente simulado, ferramentas e juiz por equivalência clínica via OpenRouter. A arquitetura deriva de [Zhang et al.](https://doi.org/10.1038/s41591-026-04609-x) e [onprem-medical-agents](https://github.com/KatherLab/onprem-medical-agents), com adaptações documentadas.

O protocolo usa limite rígido de dez turnos do médico, sem Plan, e separa fatos iniciais, exames e referências. Exames publicados são liberados mediante solicitação com compressão temporal; a condição não reproduz estritamente a disponibilidade de achados na admissão. O código upstream permite encerramento adicional após dez rodadas; esse comportamento foi excluído por solicitação do usuário. O projeto não reproduz os conjuntos completos, a infraestrutura local ou as conclusões estatísticas do artigo.

- [PROTOCOLO](PROTOCOL.md): desenho, critérios, análise e limites.
- [CHANGELOG](CHANGELOG.md): alterações e divergências.
- `cases/`: fatos separados por papel e procedência dos dez casos.
- `src/mira_runner/`: execução, orçamento e transporte OpenRouter.
- `reports/`: auditoria upstream, rotas e relatórios de execução.
- `references/`: material publicado usado na especificação.
- `legacy/`: arquivos e 290 percursos terminais do benchmark anterior preservados.

O escore lexical anterior não é diretamente comparável ao novo juiz clínico. Resultados e comandos finais devem ser publicados após validação do runner e execução; a presença desta documentação não indica que uma avaliação já foi concluída. Os modelos, provedores fixos, parâmetros, repetições e orçamento são definidos na configuração da execução, com fallback desabilitado e rastros completos.

A configuração de rotas fica em `config/run1.json`, construída a partir dos registros de endpoints em `reports/endpoints/`. A simulação está em `src/mira_runner/runner.py`; a execução sem `--execute` faz somente a conferência do cronograma. A opção `--pilot-only`, combinada com execução explícita, restringe a rodada ao piloto. A execução completa deve ocorrer apenas após a validação e autorização já registradas pelo responsável.

GPT-OSS usa Mancer FP8 (`mancer/fp8`, retornado como `Mancer 2`), selecionado explicitamente após rejeições HTTP 429 das rotas Deka BF16 e AkashML BF16. A mudança de provedor e precisão está registrada no protocolo; não habilita fallback automático. Percursos interrompidos são preservados separadamente.

**Limitação observada no piloto:** o paciente GPT-OSS inventou características clínicas que contaminaram a decisão do médico. O terminal permanece registrado; seu erro não representa uma falha isolada do médico. O prompt exige fidelidade, mas não a garante. Consulte `reports/patient_fidelity_case001_gptoss.md`; a revisão manual dos demais percursos é necessária.

Código e prompts upstream: CC BY 4.0 conforme README do repositório; atribuição a KatherLab e autores do trabalho, commit `eea2386c665c9caaa7ee093c8cb092d1c337de88`. Este projeto registra alterações de transporte, dados, contagem de turnos e isolamento de tentativas. Os direitos sobre fontes clínicas públicas e modelos permanecem próprios de cada fonte.

## Execução encerrada em04-10-2026
50/50 terminais,48 julgados e2 falhas operacionais. Revisão médica pendente. Custos: ledgerUS$1,502941443; consulta final da contaUS$1,419923378. DiferençaUS$0,083018065 ainda em investigação; não considerar reconciliação financeira concluída. Nenhuma nova execução necessária. Histórico978arquivos verificado sem divergência;50combinações únicas e manifesto de traces em reports/final_trace_manifest.json.

## Extensão autorizada —04-10-2026
Usuário autorizou runs2e3:100encontros novos, total150 (5modelos×10casos×3). Preservar run1. Mesmo protocolo/params/provedores; orçamento globalUS$18 compartilhado incluindo primeira rodada e custos técnicos. Consulta posterior credits_before_repetitions.json confirma contaUS$1,502941443 igual ledger: diferença anterior era transitória na contabilização da conta. Não reclassificar custos antigos. Projeção100novos baseada run1:US$2,803773620, estimativa não garantia. Revisão médica pendente.

## Rodadas 2 e 3 concluídas — 04-10-2026
150/150 encontros terminais (50 por rodada; 5 modelos × 10 casos × 3), sem pares duplicados ou ausentes. 144 julgados e 6 sem julgamento (falha operacional/sem diagnóstico: GPT-OSS 5, GLM-4.5-Air 1), mantidos como terminais e fora do denominador do juiz. **Julgamento por LLM; revisão médica cega pendente; sem afirmação de acurácia clínica ou superioridade.** Repetições do mesmo caso não são pacientes independentes: Wilson é descritivo.

| Modelo | Run 1 | Run 2 | Run 3 | Agregado | Wilson 95% (descritivo) | Sem julgamento |
|---|---:|---:|---:|---:|---|---:|
| openai/gpt-oss-120b | 5/8 | 3/9 | 2/8 | 10/25 | 23.4%–59.3% | 5 |
| z-ai/glm-4.5-air | 7/10 | 6/9 | 6/10 | 19/29 | 47.3%–80.1% | 1 |
| z-ai/glm-5 | 7/10 | 8/10 | 5/10 | 20/30 | 48.8%–80.8% | 0 |
| qwen/qwen3.5-397b-a17b | 6/10 | 6/10 | 7/10 | 19/30 | 45.5%–78.1% | 0 |
| openai/gpt-5.2 | 7/10 | 7/10 | 9/10 | 23/30 | 59.1%–88.2% | 0 |

Custo real total (ledger = conta, três snapshots sem cache): US$ 4.274237323. Terminais por rodada: US$ 1.401886810 / 1.313640775 / 1.427001795. Projeção para 5 rodadas ≈ US$ 6.90 em terminais (estimativa, não autorização).

Intercorrências (ver [reports/runs23_incidents.md](reports/runs23_incidents.md)): timeout de rede com 13 chamadas perdidas (US$ 0,030653310 não atribuível a nenhuma individualmente, registrado em linha própria do ledger) e um HTTP 429 do Qwen/Parasail sem cobrança. Nenhum terminal foi repetido; cada chamada perdida foi refeita uma vez após reconciliação. Análise: [reports/all_runs_summary.md](reports/all_runs_summary.md), `results/all_runs.csv`, manifesto `reports/final_trace_manifest_runs123.json`. Legacy: 978 arquivos verificados, 0 divergências.

## Extensão Qwen3.8 concluída — 04-10-2026
`qwen/qwen3.8-max-prime` (26/30 pelo juiz, US$ 2,7619) e `qwen/qwen3.8-max-0902` (24/30, US$ 1,3204): 10 casos × 3 repetições cada, rota Alibaba única, mesmo protocolo e juiz, sem falhas. Total agora 210 encontros terminais (204 julgados, 6 sem julgamento). Gasto real US$ 8.356544873 = ledger = conta (snapshots sem cache `reports/credits_qwen38_*final_*.json`); restam cerca de US$ 9,64 do teto de US$ 18, sem nova execução autorizada. Os dois modelos quase não conversaram com o paciente (23% e 7% dos encontros) e pediram achados cirúrgicos/histopatológicos finais em 60% e 53%: parte do resultado reflete a compressão temporal do protocolo. Parâmetros de amostragem assumidos iguais aos do Qwen3.5. Revisão médica pendente; sem afirmação de superioridade. Detalhes em [reports/extension_qwen38.md](reports/extension_qwen38.md); análise combinada em [reports/all_runs_summary.md](reports/all_runs_summary.md).

## Resultado do Sonnet 5.5 pela assinatura — 04-10-2026
10/10 terminais, 9 corretos pelo juiz (8/10 sob leitura rigorosa do caso 009), 0 sem julgamento, conversa com o paciente em 6 de 10 encontros. Consumo: 62 chamadas ao CLI, 408 mil tokens de entrada (407,8 mil em cache), 41,3 mil de saída, cerca de 6 minutos, custo equivalente de API US$ 1,19; gasto no OpenRouter US$ 0,0063 (associador e juiz), conta = ledger = US$ 8,362879588. Percentual consumido do limite do plano Pro não é legível pelo CLI (conferir no medidor da conta). Braço não equivalente aos demais (ferramentas em JSON, sem controle de amostragem). Detalhes em [reports/claude_sonnet_5_5_subscription_run1.md](reports/claude_sonnet_5_5_subscription_run1.md). Opus 5.5 aguardando decisão do usuário.

## Resultado do Opus 5.5 pela assinatura — 05-10-2026
`claude-opus-5-5` em high, mesmo braço de assinatura do Sonnet (ferramentas emuladas em JSON, não equivalente aos demais): 10/10 terminais, **10 corretos pelo juiz** (7 a 8 de 10 sob leitura rigorosa: 007 sem o fármaco, 002 sem miocardite, 009 sem Meckel), 0 sem julgamento, conversa com o paciente em 6 de 10 encontros. Consumo: 49 chamadas ao CLI, 194 mil tokens de entrada (194,1 mil em cache), 38,5 mil de saída, cerca de 5 minutos, custo equivalente de API US$ 1,85; gasto no OpenRouter US$ 0,0078; conta = ledger = US$ 8,370711103. O percentual consumido do limite do plano Pro não é legível pelo CLI. Detalhes e comparação com o Sonnet em [reports/claude_opus_5_5_subscription_run1.md](reports/claude_opus_5_5_subscription_run1.md). Revisão médica pendente; uma execução por caso, sem afirmação de superioridade.

## Otimização v4 autorizada em09/10

[Protocolo fast1](reports/v4_fast_protocol.md): conversa rápida Flash-Lite e revisão Sol/Astra, públicos primeiro; fechados somente após10/10 públicos na mesma condição congelada. As chamadas compartilham o teto adicionalUS$5 existente. A conciliação das três condições anteriores passou a conferir em09/10:168metadados,US$0.28396075 igual à conta, sem alterar custos.
