# Revisão clínica EAF3F59A6CAF6

Caso: `case_004`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_004", "initial": {"age_years": 63, "chief_complaint": "Recurrent dyspnea days after drainage of a right pleural effusion.", "sex_recorded": "female"}, "setting": "emergency_department"}`

## Trajetória observável

### Passo 1: `request_physical_exam`

Argumentos: `{"region_or_system": "vital signs"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_003", "status": "reported", "value": "At the initial ED visit, tachypnea without hypoxemia and reduced right-sided breath sounds were reported; repeat-visit examination details were not supplied."}], "order_recorded": false}`

### Passo 2: `ask_history`

Argumentos: `{"question": "Tell me about the pleural effusion drainage: when it was done, how much fluid was removed, any complications, and what the fluid analysis showed. How have your symptoms changed since?", "topic_code": "HPI"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "hpi", "fact_id": "hpi_001", "status": "reported", "value": "Two weeks of dyspnea and cough, briefly improved after an initial thoracentesis removed 1.5 L of milky right pleural fluid; recurrent dyspnea led to an ED return days later. No recent trauma or thoracic surgery."}], "order_recorded": false}`

### Passo 3: `request_imaging`

Argumentos: `{"body_region": "chest", "modality": "X-ray", "priority": "stat", "protocol": "PA and lateral chest radiograph"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_004", "status": "reported", "value": "Imaging at ED return showed recurrent right pleural effusion."}], "order_recorded": false}`

### Passo 4: `request_lab`

Argumentos: `{"priority": "urgent", "test_codes": ["pleural fluid triglycerides", "pleural fluid cholesterol", "pleural fluid cell count with differential", "pleural fluid LDH and protein", "pleural fluid cytology"]}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "lab", "fact_id": "lab_006", "status": "reported", "value": "Initial thoracentesis pleural fluid (available as prior record): triglycerides 434 mg/dL, cholesterol 154 mg/dL, 82% lymphocytes, pH 7.48, protein 2.4 g/dL, LDH 83 U/L; cytology without malignant cells."}], "order_recorded": false}`

### Passo 5: `request_imaging`

Argumentos: `{"body_region": "chest, abdomen and pelvis", "modality": "CT", "priority": "urgent", "protocol": "Contrast-enhanced CT to evaluate mediastinal/retroperitoneal lymphadenopathy, mass, thoracic duct obstruction, venous thrombosis, cystic lung disease"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_008", "status": "reported", "value": "CT: bilateral hilar and mediastinal adenopathy, severe right-middle-lobe bronchial narrowing, partial atelectasis and infiltrates."}], "order_recorded": false}`

### Passo 6: `plan_reason`

Argumentos: `{"next_actions": ["Check vital signs and oxygen saturation at return visit", "Order CBC, LDH, ESR, basic metabolic panel, HIV and IGRA", "Obtain tissue by EBUS-TBNA of mediastinal nodes or bronchoscopy", "Send AFB smear, culture and TB PCR", "Therapeutic thoracentesis or chest tube if symptomatic, then low-fat or MCT diet"], "summary": "63F with 2 weeks of dyspnea and cough. Thoracentesis removed 1.5 L of milky right pleural fluid. Fluid had triglycerides 434 mg/dL, cholesterol 154 mg/dL, 82% lymphocytes, protein 2.4 g/dL, LDH 83 U/L, pH 7.48 and no malignant cells on cytology. This is a chylothorax. It recurred within days. CT shows bilateral hilar and mediastinal adenopathy with severe right middle lobe bronchial narrowing and atelectasis or infiltrates. No trauma or surgery. Most likely cause is non-traumatic chylothorax from lymphatic obstruction: lymphoma, sarcoidosis, tuberculosis or other malignancy. Cytology is negative, and tissue diagnosis is needed.", "working_diagnoses": ["Lymphoma with non-traumatic chylothorax", "Sarcoidosis with mediastinal adenopathy", "Tuberculous or fungal mediastinal lymphadenitis", "Metastatic carcinoma (e.g. lung) with thoracic duct obstruction", "Lymphangioleiomyomatosis or other lymphatic disorder"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 7: `request_lab`

Argumentos: `{"priority": "urgent", "test_codes": ["CBC with differential", "serum LDH", "basic metabolic panel", "HIV antigen/antibody", "interferon-gamma release assay (IGRA)"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 8: `request_procedure`

Argumentos: `{"indication": "Non-traumatic chylothorax with bilateral hilar/mediastinal adenopathy and severe right middle lobe bronchial narrowing; need tissue diagnosis (lymphoma, sarcoidosis, TB, carcinoma) with cytology, histology, flow cytometry, AFB and fungal studies", "procedure_code_or_name": "Bronchoscopy with EBUS-TBNA of mediastinal/hilar lymph nodes and bronchial washings/biopsy of right middle lobe narrowing", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "procedure_result", "fact_id": "procedure_result_009", "status": "reported", "value": "Bronchoscopy with endobronchial ultrasound guided biopsy established extensive-stage small cell lung carcinoma."}], "order_recorded": true}`

### Passo 9: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.93, "differential": ["Lymphoma with chylothorax", "Sarcoidosis", "Tuberculous or fungal mediastinal lymphadenitis", "Lymphangioleiomyomatosis or other lymphatic disorder"], "primary": "Extensive-stage small cell lung carcinoma with mediastinal lymphadenopathy causing non-traumatic chylothorax (thoracic duct obstruction) and right middle lobe bronchial obstruction", "supporting_fact_ids": ["hpi_001", "imaging_004", "lab_006", "imaging_008", "procedure_result_009"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 10: `disposition`

Argumentos: `{"category": "ward", "followup_or_handoff": "Admit to medical or oncology ward. Consult oncology for systemic chemotherapy with immunotherapy for extensive-stage SCLC. Consult pulmonology or thoracic surgery for recurrent chylothorax management: chest tube or indwelling pleural catheter, then pleurodesis, and consider radiation to the mediastinum to relieve thoracic duct obstruction. Get dietitian input. Complete baseline labs (CBC, CMP, LDH, HIV) and brain MRI staging. Monitor respiratory status, nutrition, lymphocyte count and electrolytes. Discuss goals of care and palliative care involvement.", "rationale": "Extensive-stage small cell lung carcinoma with recurrent right chylothorax and dyspnea, plus right middle lobe bronchial obstruction. She needs inpatient pleural drainage (chest tube or indwelling pleural catheter), a low-fat or MCT diet, nutritional support, staging completion and oncology evaluation. She was not hypoxemic at the initial visit, and repeat-visit vital signs were not supplied, so ICU-level care is not clearly needed.", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"category": "ward", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `10`. Ações: `10`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
