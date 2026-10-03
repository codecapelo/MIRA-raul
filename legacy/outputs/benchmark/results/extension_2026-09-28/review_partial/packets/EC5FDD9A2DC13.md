# Revisão clínica EC5FDD9A2DC13

Caso: `case_004`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_004", "initial": {"age_years": 63, "chief_complaint": "Recurrent dyspnea days after drainage of a right pleural effusion.", "sex_recorded": "female"}, "setting": "emergency_department"}`

## Trajetória observável

### Passo 1: `request_physical_exam`

Argumentos: `{"region_or_system": "Vital signs and focused cardiopulmonary examination"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_003", "status": "reported", "value": "At the initial ED visit, tachypnea without hypoxemia and reduced right-sided breath sounds were reported; repeat-visit examination details were not supplied."}], "order_recorded": false}`

### Passo 2: `request_imaging`

Argumentos: `{"body_region": "Chest", "modality": "Chest radiograph", "priority": "urgent", "protocol": "Two-view chest radiograph to assess recurrent right pleural effusion and other acute cardiopulmonary findings"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_004", "status": "reported", "value": "Imaging at ED return showed recurrent right pleural effusion."}], "order_recorded": false}`

### Passo 3: `ask_history`

Argumentos: `{"question": "What was the cause/workup and pleural-fluid result from the recent right thoracentesis, and are there fever, pleuritic chest pain, cough, weight loss, or known malignancy?", "topic_code": "recent_pleural_effusion_workup_and_associated_symptoms"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 4: `plan_reason`

Argumentos: `{"next_actions": ["Obtain diagnostic and therapeutic pleural-fluid sampling if safely feasible", "Obtain targeted laboratory evaluation and assess for underlying cardiopulmonary or malignant cause"], "summary": "63-year-old woman has recurrent symptomatic right pleural effusion within days of drainage, with prior tachypnea, no documented hypoxemia, and reduced right breath sounds; etiology and prior fluid studies are unavailable.", "working_diagnoses": ["Recurrent right pleural effusion of undetermined cause", "Malignant pleural effusion", "Heart-failure-related pleural effusion", "Parapneumonic effusion/empyema", "Pulmonary embolism-associated effusion"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 5: `request_procedure`

Argumentos: `{"indication": "Recurrent symptomatic right pleural effusion causing dyspnea within days of prior drainage", "procedure_code_or_name": "Ultrasound-guided right thoracentesis with diagnostic pleural-fluid studies", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "procedure_result", "fact_id": "procedure_result_005", "status": "reported", "value": "Repeat thoracentesis on ED return removed 1.2 L of fluid with characteristics similar to the initial milky effusion."}], "order_recorded": true}`

### Passo 6: `request_lab`

Argumentos: `{"priority": "urgent", "test_codes": ["Pleural fluid triglycerides", "Pleural fluid cholesterol", "Pleural fluid chylomicrons", "Pleural fluid cell count with differential", "Pleural fluid protein and LDH with paired serum protein and LDH"]}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "lab", "fact_id": "lab_006", "status": "reported", "value": "Initial thoracentesis pleural fluid (available as prior record): triglycerides 434 mg/dL, cholesterol 154 mg/dL, 82% lymphocytes, pH 7.48, protein 2.4 g/dL, LDH 83 U/L; cytology without malignant cells."}], "order_recorded": false}`

### Passo 7: `request_imaging`

Argumentos: `{"body_region": "Chest", "modality": "CT", "priority": "urgent", "protocol": "Contrast-enhanced CT chest to evaluate for mediastinal mass, lymphadenopathy, or other thoracic cause of recurrent right chylothorax"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_008", "status": "reported", "value": "CT: bilateral hilar and mediastinal adenopathy, severe right-middle-lobe bronchial narrowing, partial atelectasis and infiltrates."}], "order_recorded": false}`

### Passo 8: `request_procedure`

Argumentos: `{"indication": "Recurrent right chylothorax with bilateral hilar and mediastinal adenopathy and severe right-middle-lobe bronchial narrowing; obtain tissue diagnosis", "procedure_code_or_name": "Bronchoscopy with endobronchial ultrasound-guided transbronchial needle aspiration of mediastinal/hilar lymph nodes", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"order_recorded": true, "result": "not_available_in_source"}`

### Passo 9: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.98, "differential": ["Lymphoma or other mediastinal malignancy causing thoracic-duct obstruction", "Sarcoidosis with mediastinal lymphadenopathy", "Other granulomatous mediastinal disease"], "primary": "Recurrent right chylothorax", "supporting_fact_ids": ["procedure_result_005", "lab_006", "imaging_008"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 10: `disposition`

Argumentos: `{"category": "ward", "followup_or_handoff": "Admit for respiratory monitoring, pulmonary/interventional evaluation, tissue diagnosis planning, and management of recurrent chylothorax.", "rationale": "Recurrent symptomatic right chylothorax required repeat large-volume thoracentesis and has associated mediastinal/hilar adenopathy with severe right-middle-lobe bronchial narrowing requiring inpatient evaluation.", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"category": "ward", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `10`. Ações: `10`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
