# Revisão clínica R0EC8845DA9FE

Caso: `case_006`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_006", "initial": {"age_years": 38, "chief_complaint": "Bilateral adrenal nodules found on examination, with biochemical concern for adrenal insufficiency.", "sex_recorded": "female"}, "setting": "hospital_presentation_unit_unspecified"}`

## Trajetória observável

### Passo 1: `ask_history`

Argumentos: `{"question": "What prompted the adrenal evaluation, and what symptoms have you experienced, including fatigue, weight loss, nausea or vomiting, abdominal pain, dizziness or fainting, and skin darkening?", "topic_code": "history_of_present_illness"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "hpi", "fact_id": "hpi_001", "status": "reported", "value": "Mild pigmentation over finger joints and knees; no fever, night sweats or cough."}, {"domain": "pmh", "fact_id": "pmh_002", "status": "reported", "value": "Remote hospitalization for a chest opacity five years earlier without TB diagnosis or treatment; no glucocorticoid use or family hereditary disease history."}], "order_recorded": false}`

### Passo 2: `request_physical_exam`

Argumentos: `{"region_or_system": "Vital signs, including blood pressure, orthostatic blood pressure and pulse if safe, heart rate, temperature, respiratory rate, oxygen saturation, and assessment of hydration and mental status"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_003", "status": "reported", "value": "Mild pigmentation of hand interphalangeal joints and knees."}], "order_recorded": false}`

### Passo 3: `request_lab`

Argumentos: `{"priority": "urgent", "test_codes": ["8 AM serum cortisol", "Plasma ACTH", "Basic metabolic panel", "Plasma renin", "Serum aldosterone"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 4: `request_imaging`

Argumentos: `{"body_region": "abdomen with adrenal assessment", "modality": "CT", "priority": "urgent", "protocol": "Noncontrast and contrast-enhanced imaging to characterize bilateral adrenal nodules, including size, enhancement, necrosis, calcification, and associated lymphadenopathy"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_007", "status": "reported", "value": "CT: bilateral adrenal nodules with calcification; old tuberculosis lesions in lungs and pleura."}], "order_recorded": false}`

### Passo 5: `request_ecg_or_test`

Argumentos: `{"priority": "urgent", "test_code": "Short ACTH (cosyntropin) stimulation test with baseline and 30- and 60-minute serum cortisol"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 6: `ask_history`

Argumentos: `{"question": "What prior hormone test results or endocrine diagnoses led to the concern for adrenal insufficiency, and are you currently taking any hormone replacement?", "topic_code": "prior_endocrine_evaluation_and_treatment"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 7: `request_lab`

Argumentos: `{"priority": "urgent", "test_codes": ["Tuberculosis interferon-gamma release assay (T-SPOT.TB)"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 8: `request_lab`

Argumentos: `{"priority": "routine", "test_codes": ["Plasma free metanephrines"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 9: `plan_reason`

Argumentos: `{"next_actions": ["Arrange monitored evaluation with endocrinology and infectious diseases consultation.", "Confirm adrenal function and assess tuberculosis activity before selecting definitive treatment.", "If hemodynamic instability or other features of adrenal crisis emerge, initiate immediate hydrocortisone and fluid resuscitation."], "summary": "Bilateral calcified adrenal nodules, pulmonary and pleural lesions described as old tuberculosis, and mild joint pigmentation suggest adrenal tuberculosis with possible primary adrenal insufficiency. Hormonal confirmation and vital signs are unavailable; adrenal crisis has not been established.", "working_diagnoses": ["Adrenal tuberculosis", "Primary adrenal insufficiency", "Other granulomatous adrenal infection", "Bilateral adrenal neoplasm"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 10: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.75, "differential": ["Adrenal histoplasmosis or another granulomatous infection", "Autoimmune primary adrenal insufficiency with incidental adrenal nodules", "Adrenal lymphoma", "Bilateral adrenal metastases"], "primary": "Probable bilateral adrenal tuberculosis with suspected primary adrenal insufficiency", "supporting_fact_ids": ["imaging_007", "physical_exam_003", "hpi_001", "pmh_002"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 11: `disposition`

Argumentos: `{"category": "ward", "followup_or_handoff": "Monitored inpatient evaluation with endocrinology and infectious diseases. Obtain vital signs, electrolytes, glucose, cortisol and ACTH; assess tuberculosis activity. If adrenal crisis is suspected clinically, give immediate parenteral hydrocortisone and isotonic fluids without waiting for confirmatory testing.", "rationale": "Probable bilateral adrenal tuberculosis with suspected primary adrenal insufficiency; unavailable vital signs and hormonal results prevent safe exclusion of clinically significant adrenal insufficiency.", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"category": "ward", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `11`. Ações: `11`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
