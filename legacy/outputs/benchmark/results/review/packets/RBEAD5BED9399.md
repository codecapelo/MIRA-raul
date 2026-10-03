# Revisão clínica RBEAD5BED9399

Caso: `case_005`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_005", "initial": {"age_band": "60s", "age_years": null, "chief_complaint": "One week of dyspnea and a new dry cough.", "sex_recorded": "female"}, "setting": "emergency_department"}`

## Trajetória observável

### Passo 1: `ask_history`

Argumentos: `{"question": "What are the patient's age, and do they have any past medical history, medications, or allergies?", "topic_code": "history_of_present_illness"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "hpi", "fact_id": "hpi_001", "status": "reported", "value": "Woman in her 60s with one week of dyspnea and new nonproductive cough."}, {"domain": "pmh", "fact_id": "pmh_002", "status": "reported", "value": "Rheumatoid arthritis and stable connective-tissue-disease-associated interstitial lung disease for five years; asbestos-material exposure."}], "order_recorded": false}`

### Passo 2: `request_physical_exam`

Argumentos: `{"region_or_system": "respiratory"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_004", "status": "reported", "value": "Hypoxemic, requiring 4 L/min nasal oxygen for saturation >92%; diminished left basal breath sounds and diffuse fine inspiratory crackles; other vitals normal."}], "order_recorded": false}`

### Passo 3: `plan_reason`

Argumentos: `{"next_actions": ["Chest X-ray", "CT chest", "Arterial blood gas", "Complete blood count", "Urinalysis"], "summary": "Woman in her 60s presenting with one week of dyspnea and new dry cough. History of rheumatoid arthritis and stable connective-tissue-disease-associated interstitial lung disease for five years, plus asbestos exposure. Physical exam shows hypoxemia requiring 4 L/min nasal oxygen for saturation >92%, diminished left basal breath sounds, and diffuse fine inspiratory crackles.", "working_diagnoses": ["Interstitial lung disease exacerbation", "Pneumonia", "Heart failure", "Lung cancer"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 4: `request_imaging`

Argumentos: `{"body_region": "chest", "modality": "CT", "priority": "urgent", "protocol": "contrast-enhanced chest CT with thin slices"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_008", "status": "reported", "value": "Postcontrast chest CT: moderate left effusion and nodular circumferential pleural thickening, including mediastinal pleura."}], "order_recorded": false}`

### Passo 5: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["CBC", "CMP", "ABG"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 6: `plan_reason`

Argumentos: `{"next_actions": ["Chest ultrasound for effusion assessment", "Thoracentesis if feasible", "Oxygen therapy optimization", "Consider oncology consultation"], "summary": "Woman in her 60s presenting with one week of dyspnea and new dry cough. History of rheumatoid arthritis and stable connective-tissue-disease-associated interstitial lung disease for five years, plus asbestos exposure. Physical exam shows hypoxemia requiring 4 L/min nasal oxygen for saturation >92%, diminished left basal breath sounds, and diffuse fine inspiratory crackles. CT chest shows moderate left effusion and nodular circumferential pleural thickening including mediastinal pleura.", "working_diagnoses": ["Malignant pleural mesothelioma", "Metastatic lung cancer with pleural involvement", "Connective tissue disease-associated interstitial lung disease exacerbation", "Pneumonia"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 7: `request_procedure`

Argumentos: `{"indication": "symptomatic left pleural effusion causing hypoxemia", "procedure_code_or_name": "thoracentesis left pleural space", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "procedure_result", "fact_id": "procedure_result_009", "status": "reported", "value": "High-volume thoracentesis: atypical epithelioid and spindle cells; SOX10, Melan-A and S100 positive; calretinin, EMA, p40 and WT1 negative."}], "order_recorded": true}`

### Passo 8: `plan_reason`

Argumentos: `{"next_actions": ["Oncology consultation", "Chemotherapy planning", "Supportive care optimization"], "summary": "Woman in her 60s presenting with one week of dyspnea and new dry cough. History of rheumatoid arthritis and stable connective-tissue-disease-associated interstitial lung disease for five years, plus asbestos exposure. Physical exam shows hypoxemia requiring 4 L/min nasal oxygen for saturation >92%, diminished left basal breath sounds, and diffuse fine inspiratory crackles. CT chest shows moderate left effusion and nodular circumferential pleural thickening including mediastinal pleura. Thoracentesis revealed atypical epithelioid and spindle cells with SOX10, Melan-A and S100 positive; calretinin, EMA, p40 and WT1 negative.", "working_diagnoses": ["Malignant pleural mesothelioma", "Metastatic lung cancer with pleural involvement", "Connective tissue disease-associated interstitial lung disease exacerbation", "Pneumonia"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 9: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.85, "differential": ["Metastatic lung cancer with pleural involvement", "Connective tissue disease-associated interstitial lung disease exacerbation", "Pneumonia", "Lymphoma"], "primary": "Malignant pleural mesothelioma", "supporting_fact_ids": ["hpi_001", "physical_exam_004", "imaging_008", "procedure_result_009"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 10: `disposition`

Argumentos: `{"category": "ward", "followup_or_handoff": "Oncology consultation, palliative care support, respiratory therapy monitoring", "rationale": "Patient with malignant pleural mesothelioma requiring oncology consultation and supportive care management for hypoxemia and respiratory symptoms.", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"category": "ward", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `7`. Ações: `10`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
