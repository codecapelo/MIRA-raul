# Revisão clínica RB9CFD3F65DEF

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

Argumentos: `{"region_or_system": "Vital signs and cardiopulmonary examination"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_005", "status": "reported", "value": "Rapid hemodynamic deterioration with cardiogenic shock."}], "order_recorded": false}`

### Passo 3: `request_ecg_or_test`

Argumentos: `{"priority": "stat", "test_code": "Urgent bedside transthoracic echocardiography to assess ventricular function, regional wall motion, valvular pathology or vegetations, and pericardial effusion or tamponade"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "ecg", "fact_id": "ecg_008", "status": "reported", "value": "Echocardiography showed new left-ventricular wall-motion abnormalities and pericardial effusion, then tamponade."}], "order_recorded": false}`

### Passo 4: `plan_reason`

Argumentos: `{"next_actions": ["Emergency echocardiography-guided pericardial drainage with immediate cardiology and cardiothoracic surgical involvement", "Send drained fluid for microbiology", "ICU-level hemodynamic monitoring and support"], "summary": "New chest pain during treatment for bloodstream infection, with rapid deterioration into shock. Echocardiography shows new left-ventricular wall-motion abnormalities and pericardial effusion progressing to tamponade, requiring emergency drainage.", "working_diagnoses": ["Cardiac tamponade", "Purulent pericarditis associated with bloodstream infection", "Acute myocardial infarction with ventricular free-wall rupture", "Infective endocarditis with cardiac extension"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 5: `request_procedure`

Argumentos: `{"indication": "Echocardiographically documented cardiac tamponade with rapid hemodynamic deterioration and shock.", "procedure_code_or_name": "Emergency echocardiography-guided pericardiocentesis with catheter drainage and immediate cardiothoracic surgical consultation", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "procedure_result", "fact_id": "procedure_result_011", "status": "reported", "value": "Emergency pericardiocentesis yielded yellowish, turbid pericardial fluid."}], "order_recorded": true}`

### Passo 6: `request_microbiology`

Argumentos: `{"priority": "stat", "specimen": "Pericardial fluid obtained during emergency pericardiocentesis", "test_code": "Gram stain and bacterial culture with antimicrobial susceptibility testing"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 7: `ask_history`

Argumentos: `{"question": "What organism caused the bloodstream infection, what antibiotics is he currently receiving, and does he have any medication allergies?", "topic_code": "bloodstream_infection_and_current_antimicrobial_treatment"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "hpi", "fact_id": "hpi_003", "status": "reported", "value": "Methicillin-resistant Staphylococcus aureus bacteremia complicated by infective endocarditis; receiving intravenous antibiotics."}], "order_recorded": false}`

### Passo 8: `request_ecg_or_test`

Argumentos: `{"priority": "stat", "test_code": "Transesophageal echocardiography to assess infective endocarditis, valvular dysfunction, perivalvular or myocardial abscess, and extension into the pericardium"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 9: `request_imaging`

Argumentos: `{"body_region": "Heart and chest", "modality": "CT", "priority": "stat", "protocol": "Contrast-enhanced cardiac CT to assess myocardial or perivalvular abscess, rupture, and extension into the pericardium, if sufficiently stabilized for transport"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 10: `request_procedure`

Argumentos: `{"indication": "Shock with cardiac tamponade and turbid pericardial fluid during MRSA bacteremia with infective endocarditis; concern for purulent pericarditis and myocardial or perivalvular abscess extending into the pericardium.", "procedure_code_or_name": "Emergency surgical pericardial drainage and cardiac exploration for infectious source control", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"order_recorded": true, "result": "not_available_in_source"}`

### Passo 11: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["High-sensitivity cardiac troponin", "Complete blood count with differential", "Basic metabolic panel", "Serum lactate", "C-reactive protein"]}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "lab", "fact_id": "lab_006", "status": "reported", "value": "High inflammatory response; exact analyte values were not reported."}], "order_recorded": false}`

### Passo 12: `request_physical_exam`

Argumentos: `{"region_or_system": "Post-pericardiocentesis reassessment: blood pressure, heart rate, mental status, peripheral perfusion, and persistence or resolution of shock after drainage"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_005", "status": "reported", "value": "Rapid hemodynamic deterioration with cardiogenic shock."}], "order_recorded": false}`

### Passo 13: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.88, "differential": ["Myocardial abscess with extension or rupture into the pericardium", "Infectious myopericarditis", "Acute myocardial infarction with ventricular free-wall rupture"], "primary": "Probable purulent pericarditis complicated by cardiac tamponade and shock, associated with MRSA bacteremia and infective endocarditis", "supporting_fact_ids": ["hpi_003", "physical_exam_005", "ecg_008", "procedure_result_011", "lab_006"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 14: `disposition`

Argumentos: `{"category": "ICU", "followup_or_handoff": "Immediate critical care, cardiology, cardiothoracic surgery, and infectious disease handoff. Maintain continuous hemodynamic monitoring, reassess for recurrent tamponade, continue intravenous MRSA-directed antibiotics, and urgently execute the ordered surgical drainage and cardiac exploration for source control.", "rationale": "Cardiac tamponade with shock requiring emergency pericardiocentesis, with probable purulent pericarditis during MRSA bacteremia and infective endocarditis; stabilization after drainage is not documented.", "urgency": "Immediate"}`

Resultado: `ok`

Dados retornados: `{"category": "ICU", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `14`. Ações: `14`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
