# Revisão clínica EF8AE620BAE7C

Caso: `case_006`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_006", "initial": {"age_years": 38, "chief_complaint": "Bilateral adrenal nodules found on examination, with biochemical concern for adrenal insufficiency.", "sex_recorded": "female"}, "setting": "hospital_presentation_unit_unspecified"}`

## Trajetória observável

### Passo 1: `ask_history`

Argumentos: `{"question": "What symptoms brought you in (fatigue, weight loss, nausea, abdominal pain, salt craving, dizziness, skin darkening), and over what time course?", "topic_code": "HPI"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "hpi", "fact_id": "hpi_001", "status": "reported", "value": "Mild pigmentation over finger joints and knees; no fever, night sweats or cough."}], "order_recorded": false}`

### Passo 2: `request_physical_exam`

Argumentos: `{"region_or_system": "vital signs"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_003", "status": "reported", "value": "Mild pigmentation of hand interphalangeal joints and knees."}], "order_recorded": false}`

### Passo 3: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["morning cortisol", "ACTH", "sodium", "potassium", "glucose"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 4: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["sodium", "potassium", "glucose"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 5: `request_imaging`

Argumentos: `{"body_region": "abdomen adrenal glands", "modality": "CT", "priority": "urgent", "protocol": "adrenal protocol, non-contrast then contrast-enhanced with washout"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_007", "status": "reported", "value": "CT: bilateral adrenal nodules with calcification; old tuberculosis lesions in lungs and pleura."}], "order_recorded": false}`

### Passo 6: `plan_reason`

Argumentos: `{"next_actions": ["Request serum cortisol and ACTH", "Check sodium, potassium and glucose", "Screen for active TB (IGRA, sputum)", "Start glucocorticoid replacement if adrenal insufficiency is confirmed or the patient is unstable"], "summary": "38F with bilateral adrenal nodules with calcification on CT, old pulmonary/pleural TB lesions, mild hyperpigmentation of finger joints and knees, and biochemical concern for adrenal insufficiency. No fever, night sweats or cough. Findings suggest chronic granulomatous adrenalitis, most likely old tuberculous Addison disease. Electrolytes and cortisol/ACTH were not available.", "working_diagnoses": ["Primary adrenal insufficiency due to adrenal tuberculosis (Addison disease)", "Other granulomatous adrenalitis (histoplasmosis, sarcoidosis)", "Autoimmune adrenalitis", "Bilateral adrenal hemorrhage or infiltrative disease (lymphoma, metastases)", "Bilateral adrenal adenomas or pheochromocytoma"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 7: `request_lab`

Argumentos: `{"priority": "urgent", "test_codes": ["cortisol", "ACTH"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 8: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.75, "differential": ["Other granulomatous adrenalitis (histoplasmosis, sarcoidosis)", "Autoimmune adrenalitis", "Bilateral adrenal infiltration (lymphoma, metastases)", "Bilateral adrenal hemorrhage", "Bilateral adrenal adenomas or pheochromocytoma"], "primary": "Primary adrenal insufficiency (Addison disease) due to chronic/old adrenal tuberculosis", "supporting_fact_ids": ["hpi_001", "physical_exam_003", "imaging_007"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 9: `disposition`

Argumentos: `{"category": "ward", "followup_or_handoff": "Handoff to endocrinology and infectious disease. Check sodium, potassium, glucose, cortisol, ACTH, renin and aldosterone. Screen for active TB (IGRA, sputum). Begin hydrocortisone replacement once adrenal insufficiency is confirmed, or immediately if the patient becomes unstable. Give sick-day rules and an emergency steroid card before discharge.", "rationale": "Bilateral calcified adrenal nodules with old TB lesions on CT and hyperpigmentation, with biochemical concern for primary adrenal insufficiency (likely adrenal tuberculosis). Cortisol, ACTH and electrolytes were not available, so the diagnosis is unconfirmed. Admission is the safe choice for confirmatory endocrine testing, electrolyte and volume assessment, and starting glucocorticoid (and mineralocorticoid) replacement with stress-dose education.", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"category": "ward", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `9`. Ações: `9`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
