# SPEC — MIRA-2026 Frontier Model Benchmark — Local + Frontier

**Versão:** 0.2, 25-09-2026  
**Estado:** especificação, corpus de dez casos e harness implementados; execuções em andamento; adjudicação médica pendente  
**Proprietário clínico:** usuário médico; adjudicação médica obrigatória antes de qualquer score clínico  
**Tipo:** benchmark de casos públicos, closed-book, retrospectivo, em sandbox; não é validação clínica prospectiva

## 1. Pergunta, escopo e interpretação

Pergunta principal: quando submetidos ao **mesmo EHR simulado e sequencial**, como modelos locais já instalados no Mac e modelos frontier de OpenAI e Anthropic diferem em diagnóstico, escolha de dados, tratamento, segurança, disposição, uso de ferramentas e recursos?

O MVP contém **dez casos publicados**, três execuções independentes por par modelo–caso e apenas texto/descrições estruturadas no braço primário. PDFs e imagens originais alimentam o gabarito; uma imagem só poderá ser mostrada ao agente quando houver mecanismo multimodal equivalente para todos os modelos participantes de um braço separado. Não há acesso à internet nem consulta dinâmica a diretrizes na resolução. O benchmark **não replica os números do MIRA**: muda fonte de casos (relatos públicos em vez de MIMIC-IV), distribuição diagnóstica, paciente simulado e implementação do EHR. Qualquer comparação com MIRA será arquitetural e descritiva, nunca uma diferença de performance causal.

O artigo de Ferber et al. descreve um agente médico em loop com patient agent, ferramenta `Plan`, ações estruturadas e EHR compatível com FHIR em casos MIMIC-IV; a avaliação foi feita em 574 casos de oito grupos diagnósticos, com comparação pareada de 311 casos com médicos. Aqui preservamos a **sequência clínica controlada** e a auditoria de ações, mas usamos um EHR mínimo determinístico e um corpus pequeno. [Artigo MIRA](https://doi.org/10.1038/s41586-026-10675-5).

### Fora do MVP

Atendimento real, escrita em prontuário real, FHIR completo, extração automática de gabarito sem revisão, RAG/guidelines durante os casos, ferramentas web, amostragem de centenas de casos, comparação formal com médicos e publicação de score único. O braço Jev permanece opcional e tem desenho próprio (§10).

## 2. Unidade experimental e gates

- **Caso:** um episódio clínico indexado por `case_id`, com fatos e linha temporal auditáveis no PDF.
- **Run:** trajetória completa de um modelo em um caso, com `run_id`, configuração congelada e trace append-only.
- **Unidade de comparação:** mesmo caso e repetição índice 1–3 para todos os modelos; semente comum quando o provedor aceitar, sem prometer determinismo.
- **Gates:** G0 fontes íntegras/licença; G1 packet e rubric aprovados por médico; G2 preflight de tool use e isolamento; G3 disponibilidade real/autorização de API e teto financeiro; G4 execução; G5 adjudicação clínica cega; G6 análise.

Uma fonte **não entra na execução** se o PDF não permitir reconstruir dados suficientes, o caso tiver vários pacientes sem indexação inequívoca, o desfecho for ambíguo, a licença impedir a utilização pretendida ou faltarem dados críticos para avaliar conduta. Substituição exige congelar novo `corpus_version`, registrar motivo e manter todos os modelos nos mesmos dez casos.

## 3. Corpus e separação de spoilers

Os dez PDFs e metadados estão em `cases/case_001`…`case_010`; seleção e justificativas em `docs/case_selection.md`. Os PDFs vieram da distribuição oficial **PMC Article Datasets**, com URL por versão, licença do arquivo, checksum e data registrados. A página pública da NEJM foi priorizada na busca, mas os casos examinados não tinham PDF legitimamente recuperável e licenciável nesta coleta. Não empregar espelhos não autorizados ou contornar paywall. O artigo MIRA do usuário fica em `docs/reference/`, **fora** dos dez casos.

Os dez `case_packet.json`, `ground_truth.json` e `rubric.json` foram preparados a partir dos PDFs e congelados em `docs/corpus_freeze_manifest.json`. Um médico ainda precisa revisar e assinar a fidelidade, os pontos de segurança e as alternativas aceitáveis. O protocolo de produção requer revisão independente, ao menos uma por médico. Remover do packet título, autores, DOI, revista, identificadores de PDF, resumo, discussão, legenda que nomeia doença e formulações distintivas copiadas do artigo. **Não alterar idade, sexo, datas relativas, sintomas, exames, valores, unidades, tratamentos, efeitos ou sequência temporal.** Para cada item, guardar `source_locator` (página/seção) e `available_at`/`release_rule`. Dado não relatado é `unknown`, nunca normal por suposição. O `ground_truth` e `rubric` ficam inacessíveis ao agente.

As permissões CC BY-NC e CC BY-NC-ND em parte do corpus impõem revisão de redistribuição: guardar o PDF original íntegro, atribuir autor/fonte e não publicar derivados ou versões traduzidas desses artigos sem análise de licença. A versão sem spoiler deve ser uma **extração factual estruturada para uso interno**, não uma edição do PDF redistribuída. Ver `docs/safety.md`.

## 4. EHR sandbox mínimo

Implementação atual em Python 3.9+ com `tools/ehr_sandbox.py` determinístico e interface `providers/{ollama,openai,anthropic}.py`. Uma máquina de estados mantém fatos disponíveis por momento clínico, ordens já realizadas, efeitos de ações e limite de recursos. `ask_history` revela apenas HPI/PMH/medicações/alergias vinculados à pergunta; `request_physical_exam` revela vitais e achados registrados; exames revelam seus resultados **pré-especificados**. Sem resultado na fonte: resposta `not_available_in_source`, com custo de requisição contado, sem inventar valor. Exames/ações não podem invocar conhecimento externo. Paciente simulado no MVP é **lookup determinístico** de fatos, com linguagem padronizada, não um segundo LLM. Um patient agent LLM pode ser braço posterior após testes de fidelidade e vazamento, para aproximar mais o MIRA.

Ferramentas obrigatórias: `ask_history`, `request_physical_exam`, `request_lab`, `request_imaging`, `request_ecg_or_test`, `request_microbiology`, `prescribe_medication`, `request_procedure`, `plan_reason`, `final_diagnosis`, `disposition`. `plan_reason` registra **síntese clínica curta e hipóteses explícitas**, nunca cadeia de pensamento privada. Em `final_diagnosis`, o modelo informa hipótese principal, diferencial ordenado (máx. cinco), confiança calibrável e evidências; em `disposition`, uma das categorias `discharge|ward|ICU|surgery|transfer|death_or_palliative`, tempo e justificativa. Prescrição e procedimento **simulam ordem**, sem execução física. Contratos, enums, idempotência e eventos constam em `docs/benchmark_schema.md`.

Cada chamada recebe `step_index`, `call_id` e timestamp monotônico; validação JSON estrita. Retornar resultado ou erro tipado; registrar inclusive chamadas inválidas, tentativas repetidas, timeout, recusa e truncamento. Toda ação pode ser revisada por médico. O runner não inclui PDF/gabarito no prompt e desabilita consulta externa do caso. No transporte por CLI de assinatura, isolamento contra leitura arbitrária de arquivos depende de sandbox e instrução, e deve ser auditado; não é equivalente a uma API isolada. Incluir teste de canário de spoiler e teste de que `ground_truth` não aparece no contexto.

## 5. Adapters e elegibilidade de modelos

Interface comum: `generate(turns, tools, config) -> assistant_message, tool_calls, usage, latency, provider_metadata`. Identidade de provider, modelo **ID exato/snapshot**, versão do runtime, modos de raciocínio/visão, parâmetros aceitos e falhas devem ser persistidos. Ferramentas são representadas em JSON Schema e traduzidas para a API nativa; adaptador Ollama aceita chamadas nativas ou JSON estrito com parser e validação idênticos, sem vantagem de recuperação exclusiva.

Local: somente `llama3.1:8b`, `qwen3:8b`, `qwen3.5:9b-mlx`, já presentes e confirmados em Ollama 0.34.3. Não baixar nem atualizar modelos no decorrer do MVP. A máquina é ARM64 com 18 GiB de RAM; `qwen3.5:9b-mlx` requer preflight de carregamento e memória. Os IDs, capacidades e fontes da verificação estão em `docs/model_registry.md`.

OpenAI: o braço solicitado usa **`gpt-6-sol` em `high` via conta ChatGPT/Codex**, sem API. O adaptador `providers/openai.py` invoca o Codex CLI oficial, obtém uma ação JSON e delega sua execução ao mesmo EHR. Inferência e saída estruturada passaram preflight. A API OpenAI não foi verificada nem é necessária aqui. Há limite de assinatura; o crédito de reset permanece preservado por escolha do usuário. O trabalho será retomado após a renovação semanal caso a cota impeça a execução integral.

Anthropic: o braço solicitado usa **`claude-opus-5-5` em `high` via assinatura Claude Pro/Claude Code CLI**, sem API. Autenticação e preflight de ação estruturada passaram; `providers/anthropic.py` executa o transporte. O agente de benchmark usa a mesma ferramenta externa, porém a chamada é **JSON emulado** em ambos os frontier; Ollama usa tool calls nativas quando disponíveis. Essa diferença deve ser informada em toda comparação e impede atribuir isoladamente diferenças observadas à capacidade dos modelos. IDs e comprovantes de acesso estão em `docs/model_registry.md`.

Jev/System One não é um modelo médico controlador substituto neste desenho. O endpoint e contrato de perguntas tipadas foram encontrados em trabalho anterior, mas `TYPESAFE_API_KEY` não está definido neste processo; eventual auditoria dos gabaritos será adicional e revisada pelo médico. Ver `docs/jev_methodology.md`.

## 6. Protocolo fechado

Congelar versão de corpus, prompt, schema, runtime e rubric antes da primeira run. Todos os modelos recebem o mesmo prompt clínico, conjunto de ferramentas, informação inicial mínima e respostas determinísticas. Mesma ordem de disponibilidade temporal; ordem de pedidos é escolha do agente. Executar três repetições independentes; campo `replication_target=5` permite expansão futura. Sem memória entre runs, sem reaproveitar cache sem registro. Braços multimodal ou retrieval seriam novos experimentos, nunca misturados ao principal. O painel v5 executa Ollama serialmente por modelo e os dois frontier em paralelo; **não há randomização da ordem de execução**. A permutação por caso permanece melhoria de desenho para uma versão posterior, e a deriva de tempo/carga é limitação declarada.

Configuração alvo: temperatura 0 onde aceita; quando API de raciocínio não aceita temperatura, omitir e registrar. Raciocínio frontier em `high` conforme solicitado, **quando suportado**, declarando explicitamente ausência de equivalência entre provedores. Limite `max_actions=40`, `max_model_turns=60`, `max_context_tokens=24000`, `max_output_tokens_per_turn=2048`, `max_wall_seconds=3600`; valores finais dependem de preflight comum, sem ajuste específico por modelo. Término: `final_diagnosis` seguido de `disposition`, limite de ações/tempo, falha técnica irrecuperável ou recusa. Não forçar diagnóstico após falha. Exigir um `plan_reason` antes da primeira ação terapêutica, sem expor gabarito.

## 7. Avaliação e métricas

O gabarito por caso deriva do PDF com localizadores; guideline contemporânea só entra em arquivo `guideline_sources.yaml` separado, citada e datada, **não acessível ao agente**. Distinguir diagnóstico publicado de alternativas clinicamente aceitáveis. Um médico revisa, cego ao modelo, ações críticas e divergências, com classes `correct|acceptable_alternative|questionable|unsafe`; segundo médico resolve discordâncias de segurança grave. Avaliação automática valida schema, tempo, uso de dados, equivalências diagnósticas preaprovadas e contagens; LLM **não** é juiz único de segurança. Rubric e detalhes em `docs/methodology.md`.

Reportar métricas separadas: diagnóstico final, cobertura top-3/top-5, omissão de diagnóstico crítico, taxa de próxima ação apropriada, eficiência de informação e requisições, utilização de laboratório/imagem, adequação de procedimento/medicamento, concordância com guideline, erros de alergia/dose/ajuste renal/QT/interação/anticoagulação/opioide/contraindicação/duplicação, disposição, validade de tool call, conclusão longitudinal, consistência das três runs, latência, tokens/custo frontier, throughput/memória local, passo até hipótese correta e ações desnecessárias. Informar denominadores por oportunidade; não agregar em score arbitrário. Estatística descritiva e limites em `docs/methodology.md`.

## 8. Produto técnico previsto

```text
benchmark/
  README.md  SPEC.md
  cases/case_001..case_010/
    source.pdf  source_metadata.yaml
    case_packet.json  ground_truth.json  rubric.json       # Fase 1
  docs/
    reference/mira_nature_2026.pdf  source_manifest.json
    case_selection.md  model_registry.md  benchmark_schema.md
    methodology.md  safety.md  backlog.md
    guideline_sources.yaml                                  # Fase 1
  prompts/physician_agent.md  prompts/patient_agent.md  prompts/evaluator.md
  tools/schemas.py  tools/ehr_sandbox.py
  providers/openai.py  providers/anthropic.py  providers/ollama.py
  runner/run_case.py  runner/run_benchmark.py
  evaluation/metrics.py  evaluation/adjudication.md
  results/raw/  results/summaries/
  templates/                                                # rascunhos não clínicos
```

`results/` deve ficar fora de commits públicos por padrão. PDF fonte e caso indexado nunca entram em prompt bruto. `source_metadata.yaml` conserva atribuição e hash; o packet só fatos progressivos; gabarito/rubric são arquivos de avaliador. A implementação poderá trocar Python por TypeScript sem mudar o schema JSON v1.

## 9. Critérios de aceitação da próxima etapa

Fase 1 aceita quando cada caso tem (a) PDF e hash estáveis, (b) packet fiel com todos os campos obrigatórios ou `unknown`, (c) cada fato com localizador e etapa de liberação, (d) gabarito e rubric aprovados, (e) spoiler scan humano e automático, (f) guideline separada quando utilizada. Fase 2 aceita quando preflight de todos os modelos elegíveis prova tool calling, isolamento e logs sem credenciais, e um caso piloto é revisado antes das 30 runs por modelo. Fase 3 aceita quando traces brutos, decisões médicas e cálculos são reproduzíveis a partir dos artefatos congelados. Ver backlog.

## 10. Braço opcional JEF

O usuário informou acesso ao Jev/JEF. O endpoint e contrato foram identificados em código anterior, mas a credencial `TYPESAFE_API_KEY` não está disponível no processo atual; **não presumir integração autenticada**. Especificar `providers/jef.py` apenas como extensão opt-in, com preflight de contrato e privacidade. Duas possibilidades devem ser **rotuladas separadamente**: (A) JEF como modelo controlador usando as mesmas onze ferramentas/EHR/prompt; (B) JEF como orquestrador ou apoio ao `plan_reason`. O braço B muda arquitetura, portanto não deve entrar na comparação “troca apenas do modelo” do MVP. Comparação com o MIRA: relatar se JEF usa patient agent, Plan separado, EHR estruturado/FHIR, terminologia codificada, regras de validação e fontes externas. Se usar retrieval, criar braço `with_retrieval` isolado. Nunca enviar PDFs com dados clínicos reais a JEF sem revisar destino e permissões.

## 11. Backlog e decisão de lançamento

Sequência completa em `docs/backlog.md`. Esta etapa iniciou pilotos e runs com gabaritos editoriais pendentes de revisão médica. Os traces podem ser analisados descritivamente, mas nenhuma acurácia clínica definitiva deve ser publicada antes da adjudicação. O crédito semanal de reset da conta Codex não será usado; a automação de retomada já está configurada.
