# MIRA-RAUL

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
