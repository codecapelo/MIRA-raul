# Revisão clínica RAF8B528ACBED

Caso: `case_007`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_007", "initial": {"age_years": 69, "chief_complaint": "Progressive jaundice, dark stools, lethargy and lightheadedness.", "sex_recorded": "male"}, "setting": "emergency_department"}`

## Trajetória observável

### Passo 1: `request_physical_exam`

Argumentos: `{"region_or_system": "Vital signs, including blood pressure, heart rate, respiratory rate, oxygen saturation, temperature, and mental status"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_005", "status": "reported", "value": "Afebrile, pale and deeply icteric; HR 92/min, RR 20/min, systolic BP 115 mm Hg."}], "order_recorded": false}`

### Passo 2: `ask_history`

Argumentos: `{"question": "Please describe the onset and progression of your symptoms, whether the dark stools are black and tarry or bloody, and any associated abdominal pain, fever, vomiting, or weight loss.", "topic_code": "history_of_present_illness"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "hpi", "fact_id": "hpi_001", "status": "reported", "value": "Four days of progressive jaundice and dark stools with lethargy and lightheadedness; no reported bleeding, fever, cough or abdominal pain."}], "order_recorded": false}`

### Passo 3: `request_lab`

Argumentos: `{"priority": "urgent", "test_codes": ["Complete blood count with differential", "Comprehensive metabolic panel", "Fractionated bilirubin", "Lactate dehydrogenase", "Haptoglobin"]}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "lab", "fact_id": "lab_008", "status": "reported", "value": "Lactate 4.2 mmol/L."}], "order_recorded": false}`

### Passo 4: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["Hemoglobin, hematocrit and platelet count", "Reticulocyte count", "Peripheral blood smear", "Liver function panel with direct and indirect bilirubin", "PT/INR and aPTT"]}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "lab", "fact_id": "lab_006", "status": "reported", "value": "Hemoglobin 45 g/L, down from 123 g/L baseline."}], "order_recorded": false}`

### Passo 5: `plan_reason`

Argumentos: `{"next_actions": ["Establish intravenous access and continuous monitoring", "Obtain blood group, antibody screen and crossmatch; arrange urgent packed red blood cell transfusion", "Clarify medication, allergy and transfusion history", "Obtain direct antiglobulin test and available hemolysis studies"], "summary": "Severe symptomatic anemia with hemoglobin 45 g/L, pallor, progressive jaundice and lactate 4.2 mmol/L. Current systolic blood pressure is 115 mm Hg. Hemolysis and gastrointestinal blood loss require urgent evaluation.", "working_diagnoses": ["Acute hemolytic anemia", "Gastrointestinal bleeding", "Hepatobiliary disease with concurrent anemia"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 6: `request_procedure`

Argumentos: `{"indication": "Severe symptomatic anemia: hemoglobin 45 g/L with lightheadedness, lethargy and lactate 4.2 mmol/L.", "procedure_code_or_name": "Type and crossmatch followed by urgent transfusion of 2 units packed red blood cells, one unit at a time with reassessment and monitoring for transfusion reactions", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"order_recorded": true, "result": "not_available_in_source"}`

### Passo 7: `ask_history`

Argumentos: `{"question": "What medical conditions do you have, what medicines have you taken recently (including new prescriptions or antibiotics), and do you have any medication allergies or recent blood transfusions?", "topic_code": "past_medical_history_medications_allergies_and_transfusions"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "pmh", "fact_id": "pmh_004", "status": "reported", "value": "Gastritis, hyperlipidemia, previous cholecystectomy; former smoker."}], "order_recorded": false}`

### Passo 8: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["Direct antiglobulin test with monospecific IgG and C3d testing"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 9: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["Reticulocyte count", "Peripheral blood smear morphology", "Total and direct bilirubin", "Serum lactate dehydrogenase", "Serum haptoglobin"]}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "lab", "fact_id": "lab_008", "status": "reported", "value": "Lactate 4.2 mmol/L."}], "order_recorded": false}`

### Passo 10: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["Peripheral blood smear morphology"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 11: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["Total and direct bilirubin"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 12: `ask_history`

Argumentos: `{"question": "Which prescription medicines, over-the-counter drugs and supplements have you taken recently, including any newly started medicines or antibiotics, and what medication allergies do you have?", "topic_code": "medications_and_allergies"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 13: `request_physical_exam`

Argumentos: `{"region_or_system": "Abdominal examination for tenderness, hepatomegaly and splenomegaly, and rectal examination for melena or visible blood"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 14: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["Reticulocyte count"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 15: `request_imaging`

Argumentos: `{"body_region": "Abdomen", "modality": "Ultrasound", "priority": "urgent", "protocol": "Assess liver, intrahepatic and extrahepatic bile ducts for obstruction, and spleen size in severe anemia with progressive jaundice."}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 16: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["Haptoglobin"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 17: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["Creatinine", "Urea", "Potassium", "Platelet count", "PT/INR"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 18: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.99, "differential": ["Acute hemolytic anemia", "Upper gastrointestinal bleeding", "Hepatobiliary disease with concurrent anemia"], "primary": "Severe symptomatic anemia of undetermined etiology", "supporting_fact_ids": ["lab_006", "lab_008", "physical_exam_005", "hpi_001"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 19: `disposition`

Argumentos: `{"category": "ward", "followup_or_handoff": "Handoff to internal medicine with urgent hematology consultation. Packed red blood cell transfusion has been ordered; completion and response are undocumented. Monitor vital signs, mental status and transfusion reactions, reassess hemoglobin and lactate, and investigate hemolysis and gastrointestinal bleeding. Escalate to ICU for hemodynamic instability or worsening organ dysfunction.", "rationale": "Severe symptomatic anemia with hemoglobin 45 g/L and lactate 4.2 mmol/L requires inpatient transfusion and evaluation. Progressive jaundice suggests possible hemolysis; gastrointestinal blood loss remains possible. Etiology is undetermined because additional diagnostic results are unavailable.", "urgency": "Urgent admission to a monitored bed"}`

Resultado: `ok`

Dados retornados: `{"category": "ward", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `19`. Ações: `19`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
