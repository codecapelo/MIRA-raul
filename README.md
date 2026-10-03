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

GPT-OSS usa AkashML BF16 (`akashml/bf16`), selecionado explicitamente após rejeições HTTP 429 da rota Deka BF16. Essa mudança está registrada no protocolo e no relatório de recuperação; não habilita fallback automático.

Código e prompts upstream: CC BY 4.0 conforme README do repositório; atribuição a KatherLab e autores do trabalho, commit `eea2386c665c9caaa7ee093c8cb092d1c337de88`. Este projeto registra alterações de transporte, dados, contagem de turnos e isolamento de tentativas. Os direitos sobre fontes clínicas públicas e modelos permanecem próprios de cada fonte.
