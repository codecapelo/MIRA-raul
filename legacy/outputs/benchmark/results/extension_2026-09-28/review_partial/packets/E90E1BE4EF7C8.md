# Revisão clínica E90E1BE4EF7C8

Caso: `case_010`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_010", "initial": {"age_years": 25, "chief_complaint": "Worsening left upper abdominal pain with nausea and vomiting.", "sex_recorded": "female"}, "setting": "emergency_department"}`

## Trajetória observável

### Passo 1: `request_physical_exam`

Argumentos: `{"region_or_system": "vital signs"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_004", "status": "reported", "value": "BP 107/77 mm Hg, HR 89/min, temperature 36.7°C."}, {"domain": "physical_exam", "fact_id": "physical_exam_005", "status": "reported", "value": "Left upper abdominal tenderness; no lower abdominal tenderness, guarding or rigidity; no vaginal bleeding; cervix closed; no palpable adnexal mass or cervical motion tenderness."}], "order_recorded": false}`

### Passo 2: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["hCG (pregnancy test)", "lipase", "CBC with differential", "comprehensive metabolic panel", "urinalysis"]}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "lab", "fact_id": "lab_006", "status": "reported", "value": "Serum hCG 10,130.28 IU/L."}], "order_recorded": false}`

### Passo 3: `request_imaging`

Argumentos: `{"body_region": "pelvis (transvaginal) plus abdomen with FAST, left upper quadrant and Morison pouch", "modality": "ultrasound", "priority": "stat", "protocol": "Locate pregnancy (intrauterine vs ectopic), evaluate adnexa, look for free fluid/hemoperitoneum, survey left upper quadrant"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 4: `request_imaging`

Argumentos: `{"body_region": "pelvis transvaginal", "modality": "ultrasound", "priority": "stat", "protocol": "Pregnancy location, adnexa, free fluid"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 5: `request_imaging`

Argumentos: `{"body_region": "abdomen", "modality": "ultrasound", "priority": "stat", "protocol": "FAST exam: free fluid in Morison pouch, splenorenal recess and pelvis; survey left upper quadrant"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 6: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["hemoglobin", "hematocrit", "blood type and Rh", "lipase", "urinalysis"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 7: `ask_history`

Argumentos: `{"question": "When was your last menstrual period, and do you have any prior ectopic pregnancy, pelvic infection, tubal surgery, IUD use, or fertility treatment? Any dizziness, fainting or shoulder pain?", "topic_code": "obstetric_gynecologic_history"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "hpi", "fact_id": "hpi_002", "status": "reported", "value": "Amenorrhea and positive home urine pregnancy test; approximately five weeks gestation by dates, gravida 1 para 0."}], "order_recorded": false}`

### Passo 8: `request_imaging`

Argumentos: `{"body_region": "abdomen and pelvis", "modality": "MRI", "priority": "stat", "protocol": "Non-contrast, pregnancy-safe; evaluate for ectopic/abdominal pregnancy, hemoperitoneum, left upper quadrant pathology"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 9: `plan_reason`

Argumentos: `{"next_actions": ["Request CT abdomen/pelvis with IV contrast (if the case permits and the benefit outweighs the risk), or other available imaging", "Establish IV access and send a type and screen", "Repeat vitals and monitor for hemodynamic instability", "Request general surgery and OB/GYN consultation"], "summary": "25-year-old G1P0, about 5 weeks by dates, with positive home pregnancy test and serum hCG 10,130 IU/L. She has worsening left upper abdominal pain with nausea and vomiting. Vitals: BP 107/77, HR 89, afebrile. Exam shows left upper quadrant tenderness. There is no guarding or rigidity, no lower abdominal or adnexal tenderness or mass, and the cervix is closed. Imaging (ultrasound, MRI) and repeat labs were not available. An hCG this high at 5 weeks by dates suggests the dates may be off or the pregnancy is abnormal. Ectopic pregnancy at an atypical site (abdominal or splenic) with possible hemorrhage must be excluded. Other causes are pancreatitis, gastritis or peptic disease, splenic pathology, and hyperemesis.", "working_diagnoses": ["Ectopic pregnancy at an atypical site (abdominal/splenic) with possible hemoperitoneum", "Acute pancreatitis", "Hyperemesis gravidarum / gastritis / peptic ulcer disease", "Splenic pathology (infarct, rupture, abscess)", "Early intrauterine pregnancy with an unrelated abdominal cause"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 10: `request_imaging`

Argumentos: `{"body_region": "abdomen and pelvis", "modality": "CT", "priority": "stat", "protocol": "IV contrast; evaluate for ectopic/abdominal pregnancy, hemoperitoneum, splenic pathology, pancreatitis"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_008", "status": "reported", "value": "Contrast CT showed a vascular left upper abdominal mass about 46 × 40 × 56 mm."}], "order_recorded": false}`

### Passo 11: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.6, "differential": ["Splenic or other vascular tumor/lesion (e.g., hemangioma, splenic artery aneurysm) with coincidental early pregnancy", "Splenic infarct, rupture or hematoma", "Acute pancreatitis or pancreatic mass", "Hyperemesis gravidarum or gastritis/peptic ulcer disease", "Early intrauterine pregnancy with unrelated abdominal pathology"], "primary": "Abdominal (extrauterine) ectopic pregnancy in the left upper abdomen (possibly splenic or omental implantation)", "supporting_fact_ids": ["physical_exam_004", "physical_exam_005", "lab_006", "hpi_002", "imaging_008"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 12: `disposition`

Argumentos: `{"category": "surgery", "followup_or_handoff": "Handoff to general surgery and OB/GYN, with vascular or interventional support if available. Establish two large-bore IV lines, send type and screen and crossmatch, and keep the patient NPO. Repeat CBC/hemoglobin, lipase and urinalysis as soon as they are available (they were not reported earlier). Monitor vitals continuously and prepare for massive transfusion if she becomes unstable. Check Rh status and give anti-D immunoglobulin if she is Rh-negative. Counsel the patient on the suspected diagnosis and the surgical plan.", "rationale": "Pregnant patient (about 5 weeks by dates, serum hCG 10,130 IU/L) with worsening left upper abdominal pain, nausea and vomiting, and left upper quadrant tenderness. Contrast CT showed a 46 x 40 x 56 mm vascular left upper abdominal mass. Findings are most consistent with an abdominal (extrauterine) ectopic pregnancy, which risks life-threatening hemorrhage. Ultrasound and MRI were not available, and the diagnosis is not confirmed. She was hemodynamically stable at presentation (BP 107/77, HR 89). She needs emergent surgical and OB/GYN evaluation for likely operative management.", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"category": "surgery", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `12`. Ações: `12`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
