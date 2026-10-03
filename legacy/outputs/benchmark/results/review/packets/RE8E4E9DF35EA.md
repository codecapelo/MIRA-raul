# Revisão clínica RE8E4E9DF35EA

Caso: `case_006`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_006", "initial": {"age_years": 38, "chief_complaint": "Bilateral adrenal nodules found on examination, with biochemical concern for adrenal insufficiency.", "sex_recorded": "female"}, "setting": "hospital_presentation_unit_unspecified"}`

## Trajetória observável

### Passo 1: `ask_history`

Argumentos: `{"question": "What symptoms prompted evaluation, how were the bilateral adrenal nodules discovered, and what biochemical findings raised concern for adrenal insufficiency?", "topic_code": "HPI"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "hpi", "fact_id": "hpi_001", "status": "reported", "value": "Mild pigmentation over finger joints and knees; no fever, night sweats or cough."}], "order_recorded": false}`

### Passo 2: `request_physical_exam`

Argumentos: `{"region_or_system": "Vital signs, including blood pressure, heart rate, temperature, and orthostatic measurements if documented"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_003", "status": "reported", "value": "Mild pigmentation of hand interphalangeal joints and knees."}], "order_recorded": false}`

### Passo 3: `request_lab`

Argumentos: `{"priority": "urgent", "test_codes": ["morning serum cortisol", "plasma ACTH", "sodium", "potassium", "glucose"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 4: `ask_history`

Argumentos: `{"question": "What is her past medical history, including tuberculosis, cancer, autoimmune disease, adrenal disease, and any glucocorticoid use?", "topic_code": "past_medical_history"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "pmh", "fact_id": "pmh_002", "status": "reported", "value": "Remote hospitalization for a chest opacity five years earlier without TB diagnosis or treatment; no glucocorticoid use or family hereditary disease history."}], "order_recorded": false}`

### Passo 5: `request_imaging`

Argumentos: `{"body_region": "abdomen and adrenal glands", "modality": "CT", "priority": "urgent", "protocol": "Adrenal mass characterization with intravenous contrast, including noncontrast and delayed phases if documented"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_007", "status": "reported", "value": "CT: bilateral adrenal nodules with calcification; old tuberculosis lesions in lungs and pleura."}], "order_recorded": false}`

### Passo 6: `request_ecg_or_test`

Argumentos: `{"priority": "urgent", "test_code": "ACTH (cosyntropin) stimulation test with baseline and stimulated serum cortisol"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 7: `ask_history`

Argumentos: `{"question": "What adrenal function test results were documented before presentation, including any cortisol, ACTH, or stimulation-test results?", "topic_code": "prior_adrenal_biochemical_workup"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 8: `ask_history`

Argumentos: `{"question": "Has she had fatigue, weight loss, dizziness or fainting, nausea or vomiting, abdominal pain, or salt craving?", "topic_code": "adrenal_insufficiency_symptoms"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "hpi", "fact_id": "hpi_001", "status": "reported", "value": "Mild pigmentation over finger joints and knees; no fever, night sweats or cough."}], "order_recorded": false}`

### Passo 9: `request_lab`

Argumentos: `{"priority": "routine", "test_codes": ["plasma free metanephrines"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 10: `plan_reason`

Argumentos: `{"next_actions": ["Seek documented evidence of active or prior tuberculosis and adrenal pathology", "Confirm adrenal insufficiency and assess for crisis if results become available", "Exclude pheochromocytoma before considering adrenal biopsy"], "summary": "A 38-year-old woman has bilateral calcified adrenal nodules, mild joint and knee hyperpigmentation, and CT evidence of old pulmonary and pleural tuberculosis lesions. Adrenal insufficiency is suspected, but no cortisol, ACTH, electrolyte, vital-sign, or stimulation-test results are documented.", "working_diagnoses": ["Adrenal tuberculosis with possible primary adrenal insufficiency", "Other granulomatous or infectious adrenal disease", "Bilateral adrenal neoplasm or metastases", "Autoimmune primary adrenal insufficiency"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 11: `request_lab`

Argumentos: `{"priority": "routine", "test_codes": ["interferon-gamma release assay for tuberculosis"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 12: `request_lab`

Argumentos: `{"priority": "routine", "test_codes": ["24-hour urinary fractionated metanephrines"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 13: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.68, "differential": ["Other granulomatous or fungal adrenal infection", "Bilateral adrenal malignancy or metastases", "Autoimmune primary adrenal insufficiency"], "primary": "Probable adrenal tuberculosis with suspected primary adrenal insufficiency", "supporting_fact_ids": ["imaging_007", "physical_exam_003", "pmh_002"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 14: `disposition`

Argumentos: `{"category": "ward", "followup_or_handoff": "Admit for vital-sign and electrolyte monitoring, cortisol and ACTH testing, endocrine consultation, and evaluation for adrenal tuberculosis. Assess immediately for adrenal crisis and treat if clinically indicated.", "rationale": "Suspected primary adrenal insufficiency with bilateral calcified adrenal nodules and evidence of prior tuberculosis requires prompt assessment; vital signs and adrenal function results are unavailable, so clinical stability cannot be established.", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"category": "ward", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `14`. Ações: `14`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
