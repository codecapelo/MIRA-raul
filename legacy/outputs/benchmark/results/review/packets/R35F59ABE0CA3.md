# Revisão clínica R35F59ABE0CA3

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

### Passo 2: `ask_history`

Argumentos: `{"question": "When was your last menstrual period, and is there any chance you are pregnant or have had a positive pregnancy test?", "topic_code": "pregnancy_history"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "hpi", "fact_id": "hpi_002", "status": "reported", "value": "Amenorrhea and positive home urine pregnancy test; approximately five weeks gestation by dates, gravida 1 para 0."}], "order_recorded": false}`

### Passo 3: `request_imaging`

Argumentos: `{"body_region": "pelvis", "modality": "ultrasound", "priority": "urgent", "protocol": "Transvaginal and transabdominal obstetric ultrasound to assess pregnancy location, adnexa, and free fluid"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 4: `ask_history`

Argumentos: `{"question": "When did the left upper abdominal pain begin, did it start suddenly, and have you had fainting, dizziness, or shoulder-tip pain?", "topic_code": "abdominal_pain_associated_symptoms"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 5: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["quantitative serum beta-hCG", "complete blood count", "blood type and Rh", "type and screen"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 6: `ask_history`

Argumentos: `{"question": "Please describe the full course of your abdominal pain and any associated symptoms or prior evaluation for this pregnancy.", "topic_code": "broad_hpi"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "hpi", "fact_id": "hpi_002", "status": "reported", "value": "Amenorrhea and positive home urine pregnancy test; approximately five weeks gestation by dates, gravida 1 para 0."}], "order_recorded": false}`

### Passo 7: `request_imaging`

Argumentos: `{"body_region": "abdomen", "modality": "ultrasound", "priority": "stat", "protocol": "Focused left upper quadrant and FAST examination for splenic pathology and intraperitoneal free fluid in early pregnancy"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 8: `request_imaging`

Argumentos: `{"body_region": "abdomen and pelvis", "modality": "CT", "priority": "stat", "protocol": "CT abdomen and pelvis with IV contrast to evaluate left upper quadrant pain, possible abdominal ectopic pregnancy, and intraperitoneal bleeding after ultrasound results were unavailable"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_008", "status": "reported", "value": "Contrast CT showed a vascular left upper abdominal mass about 46 × 40 × 56 mm."}], "order_recorded": false}`

### Passo 9: `plan_reason`

Argumentos: `{"next_actions": ["Obtain urgent gynecologic and surgical assessment for possible abdominal ectopic pregnancy", "Monitor hemodynamic status closely and pursue definitive evaluation"], "summary": "Approximately five weeks pregnant with worsening left upper abdominal pain, nausea, vomiting, focal tenderness, and a 46 × 40 × 56 mm vascular left upper abdominal mass on contrast CT. BP 107/77 mm Hg and HR 89/min; no guarding or rigidity. Pregnancy location and bleeding status remain unconfirmed because ultrasound and laboratory results were unavailable.", "working_diagnoses": ["Abdominal ectopic pregnancy, possibly splenic", "Vascular splenic lesion", "Other abdominal mass or hemorrhage in early pregnancy"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 10: `request_procedure`

Argumentos: `{"indication": "Early pregnancy with worsening left upper abdominal pain and a 46 × 40 × 56 mm vascular left upper abdominal mass on CT; possible abdominal ectopic pregnancy and risk of hemorrhage.", "procedure_code_or_name": "Urgent diagnostic laparoscopy with inspection of pelvis and left upper abdomen, with surgical management of suspected ectopic implantation if confirmed", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "procedure_result", "fact_id": "procedure_result_009", "status": "reported", "value": "Diagnostic laparoscopy: ~300 mL hemoperitoneum and actively bleeding 6 × 4 × 5 cm lesion between spleen and descending colon, involving omentum; uterus, ovaries and tubes appeared normal."}], "order_recorded": true}`

### Passo 11: `request_procedure`

Argumentos: `{"indication": "Diagnostic laparoscopy found approximately 300 mL hemoperitoneum and an actively bleeding 6 × 4 × 5 cm lesion between the spleen and descending colon involving the omentum in a five-week pregnancy.", "procedure_code_or_name": "Laparoscopic excision of the bleeding left upper abdominal omental lesion with surgical hemostasis", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"order_recorded": true, "result": "not_available_in_source"}`

### Passo 12: `request_procedure`

Argumentos: `{"indication": "Early pregnancy with hemoperitoneum and an actively bleeding omental lesion; determine whether the lesion contains ectopic gestational tissue.", "procedure_code_or_name": "Histopathologic examination of the left upper abdominal omental lesion, if tissue was obtained during surgery", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"order_recorded": true, "result": "not_available_in_source"}`

### Passo 13: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.88, "differential": ["Other abdominal ectopic pregnancy involving the left upper abdomen", "Bleeding omental vascular lesion"], "primary": "Ruptured omental ectopic pregnancy with hemoperitoneum", "supporting_fact_ids": ["hpi_002", "physical_exam_005", "imaging_008", "procedure_result_009"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 14: `disposition`

Argumentos: `{"category": "surgery", "followup_or_handoff": "Immediate handoff to gynecologic and general surgery teams for hemostasis, hemodynamic monitoring, and confirmation of pathology when available.", "rationale": "Laparoscopy documented approximately 300 mL hemoperitoneum and an actively bleeding left upper abdominal omental lesion in early pregnancy. Definitive hemostasis and postoperative monitoring are required; completion of excision was not documented.", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"category": "surgery", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `14`. Ações: `14`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
