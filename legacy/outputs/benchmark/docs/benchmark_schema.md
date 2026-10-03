# Contratos de dados do benchmark (schema v1)

## Princípios

JSON UTF-8, chaves `snake_case`, timestamps UTC ISO-8601, unidades UCUM quando possível e IDs estáveis. Campos ausentes na fonte recebem `{ "status": "unknown" }`, nunca inferência de normalidade. Um *caso lógico* é a combinação de `source_metadata.yaml` + `case_packet.json` + `ground_truth.json` + `rubric.json`; os três últimos só serão preenchidos na Fase 1. O modelo vê **apenas** o subconjunto liberado pelo sandbox de `case_packet.json`. Diagnóstico final, título e metadados de fonte ficam fora do seu processo. Hash SHA-256 de cada arquivo congelado aparece no `run_manifest.json`.

## `case_packet.json` — fatos clínicos temporais, sem resposta

```json
{
  "schema_version": "1.0.0",
  "case_id": "case_001",
  "index_patient": "single_reported_patient",
  "language": "en",
  "setting": "emergency_department",
  "time_zero": "first_clinical_contact",
  "initial": {
    "age_years": null,
    "sex_recorded": "unknown",
    "chief_complaint": "<fato literal ou paráfrase fiel, sem diagnóstico>"
  },
  "facts": [
    {
      "fact_id": "hpi_001",
      "domain": "hpi",
      "topic_codes": ["symptom:onset"],
      "value": "<fato clínico sem identificador de artigo>",
      "status": "reported",
      "available_at": "time_zero",
      "release_rule": {"tool": "ask_history", "match_codes": ["symptom:onset"]}
    }
  ],
  "catalog": {
    "history_topics": [],
    "physical_regions": [],
    "lab_tests": [],
    "imaging_studies": [],
    "ecg_or_tests": [],
    "microbiology_tests": [],
    "procedures": [],
    "medications": []
  },
  "temporal_events": [],
  "unknown_fields": ["allergies"]
}
```

`facts.domain` aceita `hpi|pmh|meds|allergies|vitals|physical_exam|lab|imaging|microbiology|ecg|other_test|procedure_result|course`. `release_rule` deve ser determinística, sem semântica escondida do diagnóstico. `available_at` é tempo clínico, não ordem do PDF. O MVP agudo permite `time_zero`, `after_procedure:<code>` e `after_any_procedure:<code>|<code>`; resultados pós-procedimento exigem também um pedido compatível com seu próprio `release_rule` (por exemplo, a laparoscopia não devolve automaticamente histologia). Eventos `postoperative`, `day_N`, `followup` e `retrospective` permanecem indisponíveis sem progressão temporal explícita. Não pontuar oportunidades de segurança dependentes desses eventos bloqueados como se o agente as tivesse observado. Localizadores de fonte ficam somente no `ground_truth.json` e são proibidos no payload exposto. `catalog` é um inventário editorial global idêntico nos dez packets e **não é enviado ao agente** no braço principal. O agente solicita exames por texto/código livre; o EHR usa aliases determinísticos e devolve apenas fatos do caso. Nomes de opção raros não podem funcionar como pistas no estado inicial.

## `ground_truth.json` — referência editorial e cronologia

```json
{
  "schema_version": "1.0.0",
  "case_id": "case_001",
  "source_sha256": "<64 hex>",
  "published_final_diagnosis": {
    "label": "<diagnóstico do artigo>",
    "codes": [{"system": "SNOMED_CT", "code": "<se validado>"}],
    "source_locators": ["p. X, seção Y"]
  },
  "benchmark_target_diagnosis": {"label": "<opcional: diagnóstico avaliável no encontro agudo>", "assessment_phase": "<fase>", "source_locators": ["p. X"]},
  "diagnostic_differential_from_source": [],
  "source_treatment": [],
  "source_disposition": {"category": "unknown", "source_locators": []},
  "key_guideline_decisions": [],
  "distractors": [],
  "critical_safety_points": [],
  "fact_provenance": [{"fact_id": "hpi_001", "source_locators": ["p. X"]}],
  "source_uncertainties": [],
  "clinician_signoff": {"reviewer_id": null, "signed_at": null, "status": "pending"}
}
```

As categorias de diagnóstico **publicado** e tratamento **realmente realizado** são dados descritivos; não implicam que toda conduta publicada seja ideal. `benchmark_target_diagnosis` só aparece quando o diagnóstico final do relato exige informação posterior ao encontro avaliado, como a sepse pós-operatória no caso 003; os dois desfechos são relatados separadamente. `source_treatment` e `source_disposition` devem manter o que ocorreu; uma unidade não declarada recebe `unknown`. Decisões normativas ficam no rubric e remetem a `guideline_sources.yaml` com versão/data. Não preencher código clínico se mapeamento não for validado.

## `rubric.json` — alternativas, oportunidades e segurança

```json
{
  "schema_version": "1.0.0",
  "case_id": "case_001",
  "published_diagnosis_ref": "ground_truth.published_final_diagnosis",
  "acceptable_diagnoses": [{"label": "<alternativa>", "conditions": [], "reason": "<por quê>"}],
  "critical_diagnoses_to_not_miss": [],
  "expected_actions": [
    {
      "action_id": "a1",
      "phase": "initial|after_fact|before_disposition",
      "trigger_fact_ids": [],
      "acceptable_tool_calls": [],
      "priority": "critical|recommended|optional",
      "deadline": "<regra clínica>",
      "source_or_guideline_refs": []
    }
  ],
  "unnecessary_actions": [],
  "medication_checks": [],
  "procedure_checks": [],
  "disposition_acceptability": [],
  "safety_opportunities": [],
  "guideline_refs": [],
  "reviewer_signoff": {"status": "pending", "reviewer_id": null, "signed_at": null}
}
```

Rubric predefinido antes dos modelos. `acceptable_diagnoses` tem condições explícitas para não transformar qualquer diagnóstico próximo em acerto. Ações são julgadas no estado conhecido **naquele momento**, e não com retrospectiva do desfecho. Um item `unsafe` descreve dano potencial, contraindicação, janela e severidade. `questionable` significa insuficiente para classificar como aceitável ou inseguro; revisores não devem forçar binário.

## Ferramentas clínicas: envelope único e argumentos mínimos

Todo pedido: `{"call_id":"uuid","tool":"<nome>","args":{...}}`. Resposta: `{"call_id":"uuid","status":"ok|invalid|not_available_in_source|blocked|timeout","data":{},"error_code":null,"clinical_time":"..."}`. `call_id` é idempotente; repetição idêntica devolve resposta idêntica e é registrada como requisição repetida. Chamada inválida **conta** como passo e como erro, mas não altera estado. Nenhuma ferramenta pode acessar web ou dados não contidos no packet.

| Tool | `args` obrigatórios | Resposta/efeito | Validação relevante |
|---|---|---|---|
| `ask_history` | `question`, `topic_code` | fatos HPI/PMH/meds/alergias relacionados ou `unknown` | pergunta ≤500 caracteres; não aceitar instruções de revelar gabarito |
| `request_physical_exam` | `region_or_system` | vitais/achados pré-especificados | região no catálogo; não supor exame normal |
| `request_lab` | `test_codes[]`, `priority` | resultados/unidades/reference range disponíveis | máx. 5 códigos por chamada; códigos permitidos; custo de cada analito conta |
| `request_imaging` | `modality`, `body_region`, `protocol`, `priority` | laudo estruturado; imagem bruta só em braço multimodal | contraste, gravidez e função renal como oportunidades de segurança |
| `request_ecg_or_test` | `test_code`, `priority` | ECG/eco/PFT/outros testes do caso | sem laudo não registrado; série temporal declarada |
| `request_microbiology` | `specimen`, `test_code`, `priority` | cultura/PCR/antígeno segundo disponibilidade real | tempo de incubação/retorno; teste retrospectivo indisponível no cuidado original |
| `prescribe_medication` | `drug_generic`, `dose_value`, `dose_unit`, `route`, `frequency`, `duration`, `indication` | ordem simulada + alertas tipados; sem efeito real | alergia, interação, dose, rim, QT, anticoagulação, opioide, duplicação |
| `request_procedure` | `procedure_code_or_name`, `urgency`, `indication` | ordem simulada; resultado diagnóstico apenas se previsto na fonte | procedimento possível, contraindicação, timing, consentimento simulado |
| `plan_reason` | `summary`, `working_diagnoses[]`, `next_actions[]` | registro de plano, sem revelar informação nova | ≤1000 caracteres, até 5 hipóteses; sem cadeia privada |
| `final_diagnosis` | `primary`, `differential[]`, `confidence_0_1`, `supporting_fact_ids[]` | fixa diagnóstico, inicia fechamento | diferencial ≤5; fact IDs previamente liberados |
| `disposition` | `category`, `urgency`, `rationale`, `followup_or_handoff` | termina run | enum `discharge|ward|ICU|surgery|transfer|death_or_palliative` |

`request_lab` e `request_microbiology` separados apesar de ambos resultarem em observações, para medir utilização. `request_ecg_or_test` distingue ECG de imagem. `plan_reason` não é licença para acesso a outro modelo: no braço principal, o mesmo modelo que controla o caso produz o plano. Um braço com planner separado deve ter ID próprio.

### Exemplo de schema JSON de chamada

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "BenchmarkToolCallV1",
  "type": "object",
  "additionalProperties": false,
  "required": ["call_id", "tool", "args"],
  "properties": {
    "call_id": {"type": "string", "format": "uuid"},
    "tool": {"enum": ["ask_history", "request_physical_exam", "request_lab", "request_imaging", "request_ecg_or_test", "request_microbiology", "prescribe_medication", "request_procedure", "plan_reason", "final_diagnosis", "disposition"]},
    "args": {"type": "object"}
  }
}
```

Na implementação, `args` usa `oneOf` com onze schemas por ferramenta, incluindo tipos, enums e `additionalProperties:false`; o envelope genérico acima **não é suficiente** para validação final. Criar `tools/schemas.py` a partir deste contrato e testes de exemplos válidos/inválidos antes de runs.

## Trace bruto (`results/raw/{run_id}.jsonl`)

Um evento por linha, sequência monotônica; escrita append-only e flush após cada evento. Não guardar chave/API header. Tipos: `run_started`, `model_request`, `model_response`, `tool_call`, `tool_result`, `usage`, `error`, `run_ended`. `model_request` pode guardar hash e payload clínico redigido/criptografado, conforme política de resultados; manter cópia auditável local protegida para revisão. Exemplo abreviado:

```json
{"event_schema":"1.0.0","run_id":"uuid","seq":8,"event_type":"tool_result","utc":"2026-09-25T00:00:00Z","monotonic_ms":15342,"case_id":"case_001","provider":"ollama","model_id":"qwen3:8b","turn_index":4,"step_index":3,"call_id":"uuid","tool":"request_lab","status":"ok","duration_ms":12,"payload":{"results":[]},"error_code":null}
```

`usage` registra `input_tokens`, `output_tokens`, `cached_input_tokens`, `reasoning_tokens` quando reportados, `eval_count`, `eval_duration_ns`, `prompt_eval_count`, `memory_peak_bytes`, `cost_estimate_usd`, `price_table_date` e `availability` de cada campo. `null` é indisponível, não zero. Latência: separar tempo do modelo, da ferramenta, total e p95 por run. `run_ended` inclui `stopping_reason`.

## Resultado agregado (`results/summaries/{model_id}.json`)

```json
{
  "schema_version": "1.0.0",
  "corpus_version": "v1",
  "model_id": "<ID exato>",
  "provider": "ollama|openai|anthropic",
  "eligible_cases": 10,
  "expected_runs": 30,
  "completed_runs": 0,
  "failed_runs": 0,
  "metrics": {},
  "per_case": [],
  "review_state": "pending|adjudicated",
  "calculation_version": "<git SHA>"
}
```

Cada métrica contém `numerator`, `denominator`, `estimate`, `interval`, `missing_reason`; eventos de segurança também severidade. Não criar arquivo com números preenchidos antes da execução.
