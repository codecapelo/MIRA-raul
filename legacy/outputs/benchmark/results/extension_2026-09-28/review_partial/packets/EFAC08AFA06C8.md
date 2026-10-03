# Revisão clínica EFAC08AFA06C8

Caso: `case_006`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_006", "initial": {"age_years": 38, "chief_complaint": "Bilateral adrenal nodules found on examination, with biochemical concern for adrenal insufficiency.", "sex_recorded": "female"}, "setting": "hospital_presentation_unit_unspecified"}`

## Trajetória observável

### Passo 1: `ask_history`

Argumentos: `{"question": "What symptoms led to the concern for adrenal insufficiency, including fatigue, weight loss, nausea or vomiting, dizziness or fainting, salt craving, or skin darkening?", "topic_code": "adrenal_insufficiency_symptoms"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "hpi", "fact_id": "hpi_001", "status": "reported", "value": "Mild pigmentation over finger joints and knees; no fever, night sweats or cough."}], "order_recorded": false}`

### Passo 2: `request_physical_exam`

Argumentos: `{"region_or_system": "vital signs"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_003", "status": "reported", "value": "Mild pigmentation of hand interphalangeal joints and knees."}], "order_recorded": false}`

### Passo 3: `request_lab`

Argumentos: `{"priority": "routine", "test_codes": ["serum cortisol", "plasma ACTH", "serum sodium", "serum potassium", "serum glucose"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 4: `ask_history`

Argumentos: `{"question": "Do you have a history of tuberculosis, cancer, autoimmune disease, or prior prolonged steroid treatment?", "topic_code": "adrenal_insufficiency_risk_factors"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "pmh", "fact_id": "pmh_002", "status": "reported", "value": "Remote hospitalization for a chest opacity five years earlier without TB diagnosis or treatment; no glucocorticoid use or family hereditary disease history."}], "order_recorded": false}`

### Passo 5: `ask_history`

Argumentos: `{"question": "During the hospitalization for the chest opacity, were sputum tests or other tests done for tuberculosis, and have you had known TB exposure or treatment since then?", "topic_code": "tuberculosis_history"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "pmh", "fact_id": "pmh_002", "status": "reported", "value": "Remote hospitalization for a chest opacity five years earlier without TB diagnosis or treatment; no glucocorticoid use or family hereditary disease history."}], "order_recorded": false}`

### Passo 6: `request_physical_exam`

Argumentos: `{"region_or_system": "orthostatic vital signs"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_003", "status": "reported", "value": "Mild pigmentation of hand interphalangeal joints and knees."}], "order_recorded": false}`

### Passo 7: `ask_history`

Argumentos: `{"question": "Have you had fatigue, loss of appetite or weight, nausea or vomiting, abdominal pain, salt craving, or dizziness on standing?", "topic_code": "adrenal_insufficiency_symptoms"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "hpi", "fact_id": "hpi_001", "status": "reported", "value": "Mild pigmentation over finger joints and knees; no fever, night sweats or cough."}], "order_recorded": false}`

### Passo 8: `request_imaging`

Argumentos: `{"body_region": "abdomen/adrenal glands", "modality": "CT", "priority": "routine", "protocol": "adrenal protocol to characterize bilateral adrenal nodules"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_007", "status": "reported", "value": "CT: bilateral adrenal nodules with calcification; old tuberculosis lesions in lungs and pleura."}], "order_recorded": false}`

### Passo 9: `plan_reason`

Argumentos: `{"next_actions": ["Assess clinical stability and obtain available adrenal function and electrolyte results without repeating the unavailable panel", "Clarify any prior tuberculosis evaluation or treatment", "Use the documented evidence to determine diagnosis and safe disposition"], "summary": "Bilateral calcified adrenal nodules, old pulmonary and pleural TB lesions, and mild joint and knee pigmentation raise concern for primary adrenal insufficiency, potentially from prior adrenal tuberculosis. Vital signs and biochemical results are not available in the source.", "working_diagnoses": ["Primary adrenal insufficiency due to prior adrenal tuberculosis", "Autoimmune primary adrenal insufficiency", "Other granulomatous adrenal disease", "Adrenal neoplasm"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 10: `request_ecg_or_test`

Argumentos: `{"priority": "routine", "test_code": "ACTH (cosyntropin) stimulation test"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 11: `ask_history`

Argumentos: `{"question": "Are you currently having persistent vomiting, inability to keep fluids down, fainting, severe weakness, or confusion?", "topic_code": "adrenal_crisis_symptoms"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "hpi", "fact_id": "hpi_001", "status": "reported", "value": "Mild pigmentation over finger joints and knees; no fever, night sweats or cough."}], "order_recorded": false}`

### Passo 12: `request_lab`

Argumentos: `{"priority": "routine", "test_codes": ["plasma renin activity", "serum aldosterone"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 13: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.55, "differential": ["Autoimmune primary adrenal insufficiency", "Other granulomatous adrenal disease", "Adrenal neoplasm"], "primary": "Suspected primary adrenal insufficiency due to prior adrenal tuberculosis", "supporting_fact_ids": ["hpi_001", "physical_exam_003", "imaging_007"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 14: `disposition`

Argumentos: `{"category": "ward", "followup_or_handoff": "Admit for prompt assessment of adrenal function and electrolytes, monitoring for adrenal crisis, and endocrinology evaluation; initiate stress-dose treatment if instability or crisis features are identified.", "rationale": "Suspected primary adrenal insufficiency with bilateral calcified adrenal nodules and imaging evidence of prior tuberculosis; vital signs and confirmatory biochemical results are unavailable, so clinical stability cannot be established from the record.", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"category": "ward", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `14`. Ações: `14`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
