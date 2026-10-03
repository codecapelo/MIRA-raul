# Revisão clínica E8A03660BFACC

Caso: `case_002`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_002", "initial": {"age_years": 35, "chief_complaint": "Progressive exertional dyspnea, leg edema and abdominal pain.", "sex_recorded": "male"}, "setting": "emergency_department"}`

## Trajetória observável

### Passo 1: `request_physical_exam`

Argumentos: `{"region_or_system": "vital signs"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_004", "status": "reported", "value": "Peripheral edema and bradycardia, heart rate 42/min."}], "order_recorded": false}`

### Passo 2: `request_ecg_or_test`

Argumentos: `{"priority": "stat", "test_code": "12-lead ECG"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "ecg", "fact_id": "ecg_005", "status": "reported", "value": "No P waves; narrow-QRS escape rhythm at 42/min."}], "order_recorded": false}`

### Passo 3: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["potassium", "creatinine", "troponin", "NT-proBNP", "TSH"]}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "lab", "fact_id": "lab_006", "status": "reported", "value": "NT-proBNP 432 pg/mL (reference ≤125)."}, {"domain": "lab", "fact_id": "lab_007", "status": "reported", "value": "High-sensitivity troponin T 31 ng/L (reference ≤14)."}], "order_recorded": false}`

### Passo 4: `plan_reason`

Argumentos: `{"next_actions": ["Continuous monitoring with pacing pads available", "Bedside transthoracic echocardiogram", "Clarify medications, tick exposure and travel history", "Obtain potassium, creatinine and TSH results", "Atropine if unstable, then temporary pacing if needed"], "summary": "35M with progressive exertional dyspnea, leg edema and abdominal pain (possible hepatic congestion). HR 42 with no P waves and a narrow-QRS escape rhythm, which suggests high-grade AV block or sinus arrest with junctional escape. NT-proBNP is elevated at 432 and hs-troponin T is mildly elevated at 31, so there is likely structural heart disease with heart failure. Potassium, creatinine and TSH were ordered but not returned.", "working_diagnoses": ["Infiltrative or inflammatory cardiomyopathy with conduction disease (cardiac sarcoidosis or myocarditis)", "Lyme carditis with high-grade AV block", "Hyperkalemia or drug-induced bradycardia (beta-blocker, calcium channel blocker, digoxin)", "Severe hypothyroidism", "Cardiac amyloidosis or other restrictive cardiomyopathy"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 5: `request_ecg_or_test`

Argumentos: `{"priority": "stat", "test_code": "transthoracic echocardiography"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "ecg", "fact_id": "ecg_009", "status": "reported", "value": "TTE: preserved LV systolic function; dilated LA and RV; impaired RV function; severe tricuspid regurgitation; estimated systolic PA pressure 58 mm Hg; only mild mitral regurgitation."}], "order_recorded": false}`

### Passo 6: `ask_history`

Argumentos: `{"question": "What medications does the patient take (beta-blockers, calcium channel blockers, digoxin, antiarrhythmics)? Any prior cardiac history, syncope, family history of cardiomyopathy or conduction disease, tick exposure, or travel?", "topic_code": "medications"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "meds", "fact_id": "meds_003", "status": "reported", "value": "Mesalazine."}], "order_recorded": false}`

### Passo 7: `request_physical_exam`

Argumentos: `{"region_or_system": "cardiovascular and abdomen (JVP, heart sounds, murmurs, hepatomegaly, ascites)"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_004", "status": "reported", "value": "Peripheral edema and bradycardia, heart rate 42/min."}], "order_recorded": false}`

### Passo 8: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["basic metabolic panel (potassium, creatinine, urea)", "TSH"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 9: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["potassium"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 10: `request_imaging`

Argumentos: `{"body_region": "heart", "modality": "MRI", "priority": "urgent", "protocol": "Cardiac MRI with late gadolinium enhancement and T1/T2 mapping"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_014", "status": "reported", "value": "Cardiac MRI: left atrial late gadolinium enhancement and borderline T1/T2 edema; no substantial ventricular scar."}], "order_recorded": false}`

### Passo 11: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.4, "differential": ["Mesalazine-induced myopericarditis", "Cardiac sarcoidosis with conduction disease", "Infiltrative or restrictive cardiomyopathy (amyloidosis)", "Lyme carditis or other infectious myocarditis", "Chronic thromboembolic or other pulmonary hypertension with right heart failure"], "primary": "Isolated atrial myocarditis/atrial cardiomyopathy (possibly mesalazine-associated) with atrial standstill/sinus arrest and junctional escape rhythm, causing right heart failure", "supporting_fact_ids": ["physical_exam_004", "ecg_005", "ecg_009", "imaging_014", "lab_006", "lab_007", "meds_003"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 12: `disposition`

Argumentos: `{"category": "ICU", "followup_or_handoff": "Admit to ICU/CCU with continuous ECG monitoring and transcutaneous pacing pads on. Give atropine if he becomes unstable, and arrange temporary transvenous pacing if bradycardia persists or he decompensates. Cardiology and electrophysiology to review for permanent pacing and for cardiomyopathy work-up. Obtain potassium, creatinine and TSH, and consider Lyme serology. Review whether mesalazine should be stopped with the prescribing team (gastroenterology). Manage volume overload cautiously, and consider endomyocardial biopsy or PET if the cause remains unclear.", "rationale": "Symptomatic bradycardia (HR 42) with no P waves and a junctional escape rhythm, plus right heart failure (severe TR, RV dysfunction, PA systolic pressure 58 mm Hg) and elevated NT-proBNP and hs-troponin T. He needs continuous monitoring and may need temporary pacing. The likely cause is atrial myocarditis or atrial cardiomyopathy, possibly related to mesalazine. Cardiac MRI showed left atrial late gadolinium enhancement with borderline T1/T2 edema. Potassium, creatinine and TSH results were not available.", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"category": "ICU", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `12`. Ações: `12`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
