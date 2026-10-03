# Revisão clínica R388D3DAD4CD0

Caso: `case_001`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_001", "initial": {"age_years": 65, "chief_complaint": "New chest pain during inpatient treatment for bloodstream infection.", "sex_recorded": "male"}, "setting": "inpatient"}`

## Trajetória observável

### Passo 1: `ask_history`

Argumentos: `{"question": "Please describe the chest pain: onset, location, character, radiation, severity, duration, what makes it better or worse (breathing, position, exertion), and any associated symptoms such as dyspnea, diaphoresis, palpitations, syncope, fever or cough. Also, what is the bloodstream infection (organism, source, lines/devices, current antibiotics)?", "topic_code": "HPI"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "hpi", "fact_id": "hpi_003", "status": "reported", "value": "Methicillin-resistant Staphylococcus aureus bacteremia complicated by infective endocarditis; receiving intravenous antibiotics."}, {"domain": "hpi", "fact_id": "hpi_004", "status": "reported", "value": "Chest pain developed during treatment for the bloodstream infection."}], "order_recorded": false}`

### Passo 2: `request_ecg_or_test`

Argumentos: `{"priority": "stat", "test_code": "12-lead ECG"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 3: `request_physical_exam`

Argumentos: `{"region_or_system": "vital signs"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_005", "status": "reported", "value": "Rapid hemodynamic deterioration with cardiogenic shock."}], "order_recorded": false}`

### Passo 4: `request_ecg_or_test`

Argumentos: `{"priority": "stat", "test_code": "Transthoracic echocardiogram (urgent bedside, followed by transesophageal if non-diagnostic) - assess valves, acute regurgitation, root abscess/fistula, pericardial effusion/tamponade, regional wall motion"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "ecg", "fact_id": "ecg_008", "status": "reported", "value": "Echocardiography showed new left-ventricular wall-motion abnormalities and pericardial effusion, then tamponade."}], "order_recorded": false}`

### Passo 5: `plan_reason`

Argumentos: `{"next_actions": ["Emergent echo-guided pericardiocentesis; send fluid for cell count, Gram stain, culture, and hematocrit", "Stat troponin, lactate, CBC, coagulation profile, type and crossmatch", "Emergent cardiothoracic surgery consultation for possible surgical drainage/repair", "Continue IV anti-MRSA therapy; hemodynamic support (volume, avoid positive-pressure ventilation if possible)", "Coronary angiography/CT only once stabilized, if it will change management"], "summary": "65M with MRSA bacteremia complicated by infective endocarditis on IV antibiotics develops new chest pain with rapid hemodynamic deterioration into cardiogenic shock. Echo: new LV regional wall-motion abnormalities plus pericardial effusion progressing to tamponade. The source did not provide an ECG. Given the tamponade and shock, the immediate priority is emergent pericardial decompression, with pericardial fluid sent for analysis, followed by surgical evaluation.", "working_diagnoses": ["Cardiac tamponade complicating MRSA infective endocarditis (hemopericardium from myocardial/free-wall rupture or ruptured perivalvular abscess/pseudoaneurysm)", "Acute myocardial infarction from septic coronary embolism with new regional wall-motion abnormality", "Purulent (bacterial) pericarditis from extension of a perivalvular/myocardial abscess", "Mycotic coronary artery aneurysm rupture", "Acute severe valvular regurgitation contributing to cardiogenic shock"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 6: `request_procedure`

Argumentos: `{"indication": "Cardiac tamponade with cardiogenic shock in MRSA infective endocarditis; possible hemopericardium or purulent pericarditis", "procedure_code_or_name": "Echocardiography-guided pericardiocentesis with pericardial fluid analysis (cell count, hematocrit, Gram stain, culture)", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "procedure_result", "fact_id": "procedure_result_011", "status": "reported", "value": "Emergency pericardiocentesis yielded yellowish, turbid pericardial fluid."}], "order_recorded": true}`

### Passo 7: `request_microbiology`

Argumentos: `{"priority": "stat", "specimen": "pericardial fluid", "test_code": "Gram stain and aerobic/anaerobic culture with susceptibilities"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 8: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["high-sensitivity troponin", "pericardial fluid cell count with differential, glucose, protein, LDH", "lactate", "CBC with differential", "coagulation profile (PT/INR, aPTT)"]}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "lab", "fact_id": "lab_007", "status": "reported", "value": "Disseminated intravascular coagulation was reported; exact values were not provided."}], "order_recorded": false}`

### Passo 9: `request_ecg_or_test`

Argumentos: `{"priority": "stat", "test_code": "Transesophageal echocardiogram - evaluate for perivalvular/myocardial abscess, pseudoaneurysm, fistula to pericardium, vegetation size, and valvular regurgitation"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 10: `request_procedure`

Argumentos: `{"indication": "New LV regional wall-motion abnormalities with cardiogenic shock in MRSA infective endocarditis; evaluate for septic coronary embolism or mycotic coronary aneurysm versus myocardial abscess", "procedure_code_or_name": "Emergent coronary angiography", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_009", "status": "reported", "value": "After emergency pericardiocentesis, coronary angiography showed disruption of the prior stent and rapidly enlarging coronary pseudoaneurysm."}], "order_recorded": true}`

### Passo 11: `request_procedure`

Argumentos: `{"indication": "Coronary angiography showed a disrupted prior stent and a rapidly enlarging coronary pseudoaneurysm. Suspected infected coronary stent causing a mycotic pseudoaneurysm, with turbid pericardial effusion and tamponade. Patient has cardiogenic shock and DIC during MRSA bacteremia with infective endocarditis.", "procedure_code_or_name": "Emergency cardiac surgery: removal of the infected coronary stent, resection or ligation of the coronary pseudoaneurysm with coronary artery bypass grafting, and pericardial debridement and drainage", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"order_recorded": true, "result": "not_available_in_source"}`

### Passo 12: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.85, "differential": ["Septic coronary embolism with acute myocardial infarction and new LV wall-motion abnormality", "Purulent pericarditis from extension of a perivalvular or myocardial abscess", "Myocardial free-wall rupture with hemopericardium", "Acute severe valvular regurgitation from endocarditis causing cardiogenic shock", "Septic shock with DIC and septic cardiomyopathy"], "primary": "Infected coronary stent causing a rapidly enlarging mycotic coronary artery pseudoaneurysm, with purulent pericarditis, cardiac tamponade and cardiogenic shock, as a complication of MRSA bacteremia and infective endocarditis", "supporting_fact_ids": ["hpi_003", "hpi_004", "physical_exam_005", "ecg_008", "procedure_result_011", "imaging_009", "lab_007"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 13: `disposition`

Argumentos: `{"category": "surgery", "followup_or_handoff": "Hand off directly to cardiothoracic surgery and cardiac anesthesia for emergency surgery: stent removal, pseudoaneurysm resection or ligation, CABG, and pericardial debridement and drainage. Assess the valves and repair or replace them if endocarditis requires it. Send intraoperative tissue, stent and pericardial fluid for Gram stain and culture. Continue IV anti-MRSA therapy and consult infectious diseases. Before surgery, give blood products for DIC (platelets, FFP, cryoprecipitate guided by labs) and have blood crossmatched. Provide inotrope and vasopressor support, with mechanical circulatory support available if needed. Keep the pericardial drain in place. After surgery, admit to the cardiac surgical ICU with serial echocardiography and repeat blood cultures.", "rationale": "The patient has cardiogenic shock and DIC after pericardiocentesis for tamponade. Pericardial fluid was yellowish and turbid. Angiography showed a disrupted prior coronary stent and a rapidly enlarging coronary pseudoaneurysm. This fits an infected stent with a mycotic pseudoaneurysm during MRSA bacteremia and endocarditis. The pseudoaneurysm is at imminent risk of rupture, and the infected source can only be controlled by emergency surgery.", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"category": "surgery", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `13`. Ações: `13`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
