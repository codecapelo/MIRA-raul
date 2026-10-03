# Revisão clínica R433AADB9CD55

Caso: `case_010`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_010", "initial": {"age_years": 25, "chief_complaint": "Worsening left upper abdominal pain with nausea and vomiting.", "sex_recorded": "female"}, "setting": "emergency_department"}`

## Trajetória observável

### Passo 1: `request_physical_exam`

Argumentos: `{"region_or_system": "Vital signs, including blood pressure, heart rate, respiratory rate, temperature, oxygen saturation, and mental status"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_004", "status": "reported", "value": "BP 107/77 mm Hg, HR 89/min, temperature 36.7°C."}, {"domain": "physical_exam", "fact_id": "physical_exam_005", "status": "reported", "value": "Left upper abdominal tenderness; no lower abdominal tenderness, guarding or rigidity; no vaginal bleeding; cervix closed; no palpable adnexal mass or cervical motion tenderness."}], "order_recorded": false}`

### Passo 2: `ask_history`

Argumentos: `{"question": "When did the pain begin and how has it progressed, and when was your last menstrual period or most recent pregnancy test?", "topic_code": "abdominal_pain_and_pregnancy_history"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "hpi", "fact_id": "hpi_002", "status": "reported", "value": "Amenorrhea and positive home urine pregnancy test; approximately five weeks gestation by dates, gravida 1 para 0."}], "order_recorded": false}`

### Passo 3: `request_imaging`

Argumentos: `{"body_region": "pelvis and abdomen", "modality": "ultrasound", "priority": "urgent", "protocol": "Transvaginal and transabdominal ultrasound to locate the pregnancy, assess both adnexa, and evaluate for intraperitoneal free fluid, including the left upper quadrant."}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 4: `request_lab`

Argumentos: `{"priority": "urgent", "test_codes": ["Quantitative serum beta-hCG", "Complete blood count", "Blood type, Rh status and antibody screen", "Comprehensive metabolic panel", "Lipase"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 5: `ask_history`

Argumentos: `{"question": "Have you already been evaluated or treated for this pain or pregnancy, and were any imaging findings or test results explained to you?", "topic_code": "prior_evaluation_and_treatment"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "hpi", "fact_id": "hpi_002", "status": "reported", "value": "Amenorrhea and positive home urine pregnancy test; approximately five weeks gestation by dates, gravida 1 para 0."}], "order_recorded": false}`

### Passo 6: `ask_history`

Argumentos: `{"question": "When did the abdominal pain start, how has it changed, and does it spread to your left shoulder or occur with dizziness or fainting?", "topic_code": "abdominal_pain_course_and_associated_symptoms"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 7: `request_imaging`

Argumentos: `{"body_region": "abdomen and pelvis", "modality": "MRI", "priority": "urgent", "protocol": "Without gadolinium; evaluate pregnancy location, possible abdominal ectopic pregnancy, intraperitoneal hemorrhage, and causes of left upper abdominal pain."}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 8: `plan_reason`

Argumentos: `{"next_actions": ["Obtain urgent obstetric/gynecologic consultation for possible ectopic pregnancy", "Monitor vital signs and repeat abdominal examination", "Continue urgent hospital evaluation to establish pregnancy location and assess for intraperitoneal bleeding"], "summary": "Approximately five weeks pregnant with worsening left upper abdominal pain, vomiting, and focal tenderness. BP 107/77 mm Hg and HR 89/min, without guarding or rigidity. Pregnancy location and laboratory results remain unavailable; ectopic pregnancy cannot be excluded.", "working_diagnoses": ["Pregnancy of undetermined location with possible ectopic pregnancy", "Splenic pathology", "Pancreatitis"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 9: `request_procedure`

Argumentos: `{"indication": "Early pregnancy with worsening focal left upper abdominal pain and tenderness; pregnancy location is unconfirmed and ectopic pregnancy with intraperitoneal bleeding must be excluded.", "procedure_code_or_name": "Urgent obstetric and gynecologic consultation", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"order_recorded": true, "result": "not_available_in_source"}`

### Passo 10: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.5, "differential": ["Symptomatic early intrauterine pregnancy", "Splenic pathology", "Acute pancreatitis"], "primary": "Suspected ectopic pregnancy; pregnancy location unconfirmed", "supporting_fact_ids": ["hpi_002", "physical_exam_004", "physical_exam_005"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 11: `disposition`

Argumentos: `{"category": "ward", "followup_or_handoff": "Urgent obstetric/gynecologic assessment; establish pregnancy location with ultrasound and quantitative beta-hCG, obtain CBC and blood type/Rh status, and monitor vital signs and serial abdominal examinations. Escalate immediately to surgical evaluation for hemodynamic deterioration or peritoneal signs.", "rationale": "Early pregnancy with worsening focal abdominal pain and unconfirmed pregnancy location requires inpatient evaluation to exclude ectopic pregnancy and intraperitoneal bleeding. Documented vital signs are stable, but diagnostic imaging and laboratory results are unavailable.", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"category": "ward", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `11`. Ações: `11`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
