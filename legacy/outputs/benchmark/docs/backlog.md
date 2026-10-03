# Backlog por fases

## Fase 0 — setup e corpus (concluída para uso interno)

- [x] Conferir PDF MIRA fornecido, separar de casos e registrar DOI.
- [x] Selecionar dez candidatos diversificados, baixar PDFs da fonte oficial, registrar DOI/licença/URL/SHA-256.
- [x] Inspecionar Ollama local, versão e modelos instalados.
- [x] Registrar permissões declaradas dos PDFs para pesquisa interna; antes de redistribuição pública, revisar especialmente CC BY-NC e CC BY-NC-ND.
- [x] Criar `pyproject.toml`, testes e comando de verificação do corpus. Não há dependências Python terceiras a travar em lockfile; as CLIs externas e versões constam no registro de modelos.
- [x] Verificar assinatura OpenAI/Anthropic por preflight sem caso clínico. APIs pagas foram excluídas conforme a preferência do usuário; cota de assinatura é monitorada sem usar o crédito de reset.

**Gate 0:** dez PDFs íntegros e uso interno documentado. Redistribuição pública continua condicionada a revisão de licença.

## Fase 1 — dez casos estruturados

- [x] Extrair fatos e cronologia, indexar o paciente de cada relato e auditar contra os PDFs.
- [x] Construir dez `case_packet.json` sem metadados de fonte e dez `ground_truth.json` com localizadores de PDF.
- [x] Construir dez `rubric.json` com ações críticas, alternativas aceitáveis e riscos.
- [x] Registrar diretrizes contemporâneas em `docs/guideline_sources.yaml`; revisão médica dupla formal permanece pendente.
- [x] Rodar validação estrutural, spoiler scan de metadados e consistência temporal; congelar `corpus_version` v3.

**Gate 1:** aprovação médica documentada dos dez pacotes e rubrics **pendente**; resultados automáticos são exploratórios.

## Fase 2 — runner e execução

- [x] Implementar schemas, EHR determinístico, prompts e adapters Ollama/OpenAI/Anthropic.
- [x] Implementar isolamento por configuração da CLI, trace append-only, retry técnico com semântica definida e medição; a limitação do isolamento de ferramentas internas está documentada.
- [x] Pilotar modelos sem caso clínico e registrar pilotos abortados fora do painel principal.
- [x] Executar 10 casos × 3 repetições × cinco modelos: **150/150 trajetórias terminais**, com três runs por caso/modelo.
- [x] Preservar tentativa Sol interrompida por erro de provider próximo ao limite da conta em `results/incomplete/`, com índice e motivo; o retry usa a mesma combinação.

**Gate 2:** corpus v3/protocolo v5 congelados e preflights aprovados. Execução usa assinaturas já autorizadas, sem API.

## Fase 3 — avaliação e análise

- [x] Implementar métricas automáticas, análise pareada por caso e exportador de revisão cega; gerar relatório, resumos, 150 packets de revisão e manifestos de hashes após **150/150** traces válidos.
- [ ] Concluir revisão médica cega para ambiguidade/segurança.
- [ ] Resolver discordâncias, registrar decisões e manter taxa de concordância entre revisores.
- [x] Gerar tabelas separadas por métrica, caso e modelo, intervalos descritivos por caso e diferenças pareadas automáticas.
- [ ] Auditoria de casos em que o diagnóstico foi correto com conduta insegura ou testes excessivos.
- [x] Relatório exploratório com limitações: n=10, casos públicos, seleção intencional, transporte distinto e sem comparabilidade numérica direta com MIRA.

## Fase 4 — holdout e extensões

- [ ] Desenhar casos próprios/fresh holdout com governança/consentimento/desidentificação apropriados.
- [ ] Aumentar para cinco runs por caso e adicionar braço multimodal pareado.
- [ ] Estudar retrieval/guidelines em braço separado; opcionalmente integrar JEF com arquitetura declarada.
- [ ] Só considerar avaliação prospectiva com supervisão após segurança e validade externa independentes.

## Extensão de 28-09-2026 — Sonnet, Luna e Terra

- [x] Verificar acessos e congelar adapters/runners adicionais, sem alterar corpus v3 ou protocolo clínico v5.
- [x] Sonnet 5.5 high: 30 trajetórias terminais únicas.
- [ ] GPT-6 Luna high: 20/30 terminais; interrompido a pedido do usuário, sem retomada autorizada.
- [x] GPT-5.6 Terra high: 30 trajetórias terminais únicas.
- [x] Acrescentar diagnóstico passivo externo e quadro operacional de tentativas, sem alterar scoring clínico.
- [x] Consolidar os 230 traces disponíveis de oito modelos, com Luna parcial, preservando métricas/custo Sol originais.
- [x] Exportar 80 packets cegos adicionais, 240 registros de adjudicação e chave separada; 90 era a meta anterior à interrupção.
- [x] Atualizar comparação MIRA, verificação e README após encerramento a pedido do usuário.
- [ ] Concluir revisão médica dos gabaritos, alternativas aceitáveis e segurança (mantida separada da execução técnica).
- [ ] Revisar também os prefixos clínicos elegíveis das tentativas interrompidas, separados dos denominadores principais.

A execução foi encerrada a pedido do usuário em 28-09-2026 e a automação pausada. Não retomar sem nova autorização. Qualquer retomada futura deve pular todas as combinações terminalmente concluídas. Interrupções e seus prefixos permanecem registrados fora do denominador clínico, com quadro operacional separado.

## Extensão Astra / Sol 6.1 — 29-09-2026

- [x] Verificar assinatura, preflight Astra high, modelo solicitado e schema de ação.
- [x] Testar ID `gpt-6.1-sol`: aceito em low e no preflight sintético estruturado high da CLI npm0.159.1.
- [x] Congelar adapter/runner Astra em manifesto aditivo, preservando corpus e protocolos existentes.
- [x] Executar 10 casos × 3 trajetórias Astra com inspeção de falhas e cota (30/30 terminais).
- [x] Acrescentar Astra à análise do painel disponível, sem imputar as 10 lacunas Luna.
- [x] Preparar braço aditivo Sol 6.1 separado com mesmo protocolo, sem copiar preço de Sol 6.
- [x] Validar high estruturado antes de qualquer trajetória clínica.
- [x] Executar 10 casos × 3 no Sol 6.1 high (30/30 terminais).
- [x] Validar 290 terminais do painel ampliado, preservar hashes dos 230 anteriores e exportar 60 pacotes cegos adicionais para revisão.
- [ ] Adjudicação médica cega dos novos traces.

A extensão Astra/Sol 6.1 foi concluída. O painel ampliado tem 290/300 combinações planejadas, das quais somente as dez lacunas Luna permanecem ausentes por interrupção solicitada pelo usuário. O [relatório consolidado](../results/frontier_addons_2026-09-29/summaries/FRONTIER_ADDONS_REPORT.md) é exploratório; diagnóstico, conduta e segurança permanecem sujeitos à revisão médica. A automação de execução deve ser pausada após a consolidação; não retomar Luna/Terra.
