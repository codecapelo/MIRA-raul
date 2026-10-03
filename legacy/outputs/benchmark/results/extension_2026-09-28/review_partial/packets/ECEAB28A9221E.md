# Revisão clínica ECEAB28A9221E

Caso: `case_001`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_001", "initial": {"age_years": 65, "chief_complaint": "New chest pain during inpatient treatment for bloodstream infection.", "sex_recorded": "male"}, "setting": "inpatient"}`

## Trajetória observável

### Passo 1: `request_ecg_or_test`

Argumentos: `{"priority": "stat", "test_code": "12-lead ECG"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 2: `request_physical_exam`

Argumentos: `{"region_or_system": "Vital signs, including blood pressure, heart rate, respiratory rate, oxygen saturation, and temperature"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_005", "status": "reported", "value": "Rapid hemodynamic deterioration with cardiogenic shock."}], "order_recorded": false}`

### Passo 3: `plan_reason`

Argumentos: `{"next_actions": ["Urgent bedside echocardiography and cardiac injury evaluation", "Immediate critical-care assessment and hemodynamic support"], "summary": "New chest pain during inpatient treatment for bloodstream infection, with reported rapid hemodynamic deterioration and cardiogenic shock. ECG was not available in the source.", "working_diagnoses": ["Acute coronary syndrome", "Infective endocarditis with acute cardiac complication", "Septic cardiomyopathy", "Pericardial tamponade"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 4: `request_imaging`

Argumentos: `{"body_region": "heart", "modality": "bedside transthoracic echocardiography", "priority": "stat", "protocol": "urgent focused assessment of ventricular function, regional wall motion, valves, and pericardial effusion"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 5: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["high-sensitivity troponin", "lactate", "CBC", "comprehensive metabolic panel", "coagulation panel"]}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "lab", "fact_id": "lab_007", "status": "reported", "value": "Disseminated intravascular coagulation was reported; exact values were not provided."}], "order_recorded": false}`

### Passo 6: `prescribe_medication`

Argumentos: `{"dose_unit": "mcg/kg/min", "dose_value": 0.05, "drug_generic": "norepinephrine", "duration": "ongoing until shock resolves or transitioned to other support", "frequency": "continuous, titrate to hemodynamic response", "indication": "cardiogenic shock", "route": "IV infusion"}`

Resultado: `ok`

Dados retornados: `{"order_recorded": true, "safety_not_adjudicated": true}`

### Passo 7: `ask_history`

Argumentos: `{"question": "What organism was identified in the bloodstream infection, and what antimicrobial treatment is the patient receiving?", "topic_code": "bloodstream infection"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "hpi", "fact_id": "hpi_003", "status": "reported", "value": "Methicillin-resistant Staphylococcus aureus bacteremia complicated by infective endocarditis; receiving intravenous antibiotics."}], "order_recorded": false}`

### Passo 8: `request_physical_exam`

Argumentos: `{"region_or_system": "Cardiovascular examination, including heart sounds, murmurs, jugular venous pressure, and peripheral perfusion"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 9: `request_imaging`

Argumentos: `{"body_region": "heart", "modality": "transesophageal echocardiography", "priority": "stat", "protocol": "stat assessment for infective endocarditis complications, acute valvular regurgitation, ventricular function, and pericardial effusion"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 10: `request_procedure`

Argumentos: `{"indication": "MRSA infective endocarditis with new chest pain and rapid hemodynamic deterioration to cardiogenic shock; urgent evaluation for a surgically correctable cardiac complication.", "procedure_code_or_name": "Emergent cardiac surgery consultation for infective endocarditis with cardiogenic shock", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"order_recorded": true, "result": "not_available_in_source"}`

### Passo 11: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.78, "differential": ["Acute coronary syndrome", "Acute valvular complication of infective endocarditis", "Septic cardiomyopathy", "Pericardial tamponade"], "primary": "MRSA infective endocarditis complicated by cardiogenic shock", "supporting_fact_ids": ["hpi_003", "physical_exam_005", "lab_007"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 12: `disposition`

Argumentos: `{"category": "ICU", "followup_or_handoff": "Immediate ICU handoff for ongoing shock management and urgent cardiac surgery consultation; continue evaluation for acute cardiac complications.", "rationale": "MRSA infective endocarditis with new chest pain, rapid hemodynamic deterioration to cardiogenic shock, and reported disseminated intravascular coagulation.", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"category": "ICU", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `12`. Ações: `12`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
