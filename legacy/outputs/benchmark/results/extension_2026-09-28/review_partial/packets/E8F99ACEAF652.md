# Revisão clínica E8F99ACEAF652

Caso: `case_007`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_007", "initial": {"age_years": 69, "chief_complaint": "Progressive jaundice, dark stools, lethargy and lightheadedness.", "sex_recorded": "male"}, "setting": "emergency_department"}`

## Trajetória observável

### Passo 1: `request_physical_exam`

Argumentos: `{"region_or_system": "Vital signs and general examination"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_005", "status": "reported", "value": "Afebrile, pale and deeply icteric; HR 92/min, RR 20/min, systolic BP 115 mm Hg."}], "order_recorded": false}`

### Passo 2: `ask_history`

Argumentos: `{"question": "Please describe the jaundice and dark stools: onset/progression, stool appearance or vomiting blood, abdominal pain, weight loss, pruritus, fever, and any anticoagulant/NSAID or alcohol use.", "topic_code": "jaundice_and_gastrointestinal_bleeding_history"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "hpi", "fact_id": "hpi_001", "status": "reported", "value": "Four days of progressive jaundice and dark stools with lethargy and lightheadedness; no reported bleeding, fever, cough or abdominal pain."}], "order_recorded": false}`

### Passo 3: `request_lab`

Argumentos: `{"priority": "urgent", "test_codes": ["Complete blood count", "Comprehensive metabolic panel", "Fractionated bilirubin", "PT/INR", "Lipase"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 4: `request_lab`

Argumentos: `{"priority": "urgent", "test_codes": ["Complete blood count"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 5: `request_physical_exam`

Argumentos: `{"region_or_system": "Abdominal examination, including hepatomegaly, palpable gallbladder, tenderness, ascites, and rectal examination"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 6: `request_imaging`

Argumentos: `{"body_region": "Right upper quadrant abdomen", "modality": "Ultrasound", "priority": "urgent", "protocol": "Hepatobiliary ultrasound to assess biliary ductal dilation, gallbladder, liver, and pancreatic head region"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 7: `ask_history`

Argumentos: `{"question": "Are the stools black and tarry (melena) versus simply dark, and have you noticed dark urine, pale stools, itching, unintentional weight loss, or prior liver/gallbladder disease?", "topic_code": "characterize_jaundice_and_stool_change"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 8: `plan_reason`

Argumentos: `{"next_actions": ["Seek source-documented cross-sectional abdominal imaging if available", "Assess for cardiac consequences of lightheadedness/anemia with ECG"], "summary": "69-year-old man with four days of progressive jaundice, dark stools, lethargy, and lightheadedness; he is pale and deeply icteric but afebrile and hemodynamically stable. He reports no bleeding, fever, cough, or abdominal pain. CBC, liver/coagulation studies, abdominal examination, and hepatobiliary ultrasound were not available in the source.", "working_diagnoses": ["Obstructive jaundice, including pancreaticobiliary malignancy", "Hepatocellular jaundice", "Hemolytic anemia or other cause of anemia with jaundice", "Occult gastrointestinal bleeding"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 9: `request_imaging`

Argumentos: `{"body_region": "Abdomen and pelvis", "modality": "CT", "priority": "urgent", "protocol": "Contrast-enhanced CT abdomen/pelvis with pancreaticobiliary protocol to evaluate obstructive jaundice or malignancy"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_011", "status": "reported", "value": "Triple-phase CT abdomen/pelvis found no hemorrhage or intra-abdominal collection."}], "order_recorded": false}`

### Passo 10: `request_ecg_or_test`

Argumentos: `{"priority": "urgent", "test_code": "12-lead ECG"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 11: `ask_history`

Argumentos: `{"question": "What are his past medical conditions, regular medications (especially anticoagulants), alcohol use, and any history of liver, biliary, pancreatic, or malignant disease?", "topic_code": "past_medical_history_and_medications"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "pmh", "fact_id": "pmh_004", "status": "reported", "value": "Gastritis, hyperlipidemia, previous cholecystectomy; former smoker."}], "order_recorded": false}`

### Passo 12: `ask_history`

Argumentos: `{"question": "When was the cholecystectomy performed, and were there any postoperative biliary complications or recent endoscopic/abdominal procedures?", "topic_code": "cholecystectomy_and_biliary_procedure_history"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 13: `request_procedure`

Argumentos: `{"indication": "Dark stools with pallor, lightheadedness, and possible occult upper gastrointestinal bleeding or hemobilia", "procedure_code_or_name": "Esophagogastroduodenoscopy (upper gastrointestinal endoscopy)", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"order_recorded": true, "result": "not_available_in_source"}`

### Passo 14: `request_procedure`

Argumentos: `{"indication": "Progressive deep jaundice with dark stools after cholecystectomy; evaluate and treat possible biliary obstruction or hemobilia", "procedure_code_or_name": "Endoscopic retrograde cholangiopancreatography (ERCP)", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"order_recorded": true, "result": "not_available_in_source"}`

### Passo 15: `request_lab`

Argumentos: `{"priority": "urgent", "test_codes": ["Liver function tests"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 16: `request_imaging`

Argumentos: `{"body_region": "Abdomen", "modality": "MRI", "priority": "urgent", "protocol": "MRCP to evaluate the biliary tree for obstruction, retained stone, stricture, or post-cholecystectomy biliary complication"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 17: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.3, "differential": ["Extrahepatic biliary obstruction", "Hepatocellular jaundice", "Hemolysis or anemia-associated jaundice", "Occult upper gastrointestinal bleeding"], "primary": "Jaundice of undetermined etiology", "supporting_fact_ids": ["hpi_001", "physical_exam_005", "imaging_011", "pmh_004"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 18: `disposition`

Argumentos: `{"category": "ward", "followup_or_handoff": "Urgent gastroenterology/hepatobiliary evaluation; complete source-available liver studies and evaluate planned endoscopic procedures.", "rationale": "Progressive deep jaundice with pallor, lethargy, and lightheadedness requires inpatient evaluation despite stable vital signs; etiology remains undetermined.", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"category": "ward", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `18`. Ações: `18`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
