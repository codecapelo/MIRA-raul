# Revisão clínica R5FC98E2DC36B

Caso: `case_010`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_010", "initial": {"age_years": 25, "chief_complaint": "Worsening left upper abdominal pain with nausea and vomiting.", "sex_recorded": "female"}, "setting": "emergency_department"}`

## Trajetória observável

### Passo 1: `ask_history`

Argumentos: `{"question": "When did the left upper abdominal pain begin, how has it changed, and does it radiate anywhere? Are the nausea and vomiting accompanied by fever, bowel changes, urinary symptoms, or recent injury?", "topic_code": "abdominal_pain_hpi"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 2: `request_physical_exam`

Argumentos: `{"region_or_system": "vital signs"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_004", "status": "reported", "value": "BP 107/77 mm Hg, HR 89/min, temperature 36.7°C."}, {"domain": "physical_exam", "fact_id": "physical_exam_005", "status": "reported", "value": "Left upper abdominal tenderness; no lower abdominal tenderness, guarding or rigidity; no vaginal bleeding; cervix closed; no palpable adnexal mass or cervical motion tenderness."}], "order_recorded": false}`

### Passo 3: `request_lab`

Argumentos: `{"priority": "urgent", "test_codes": ["serum quantitative beta-hCG", "CBC", "comprehensive metabolic panel", "lipase", "urinalysis"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 4: `ask_history`

Argumentos: `{"question": "When was your last menstrual period, and could you be pregnant? Have you had a positive pregnancy test or any prior ectopic pregnancy?", "topic_code": "pregnancy_history"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "hpi", "fact_id": "hpi_002", "status": "reported", "value": "Amenorrhea and positive home urine pregnancy test; approximately five weeks gestation by dates, gravida 1 para 0."}], "order_recorded": false}`

### Passo 5: `request_imaging`

Argumentos: `{"body_region": "pelvis and abdomen", "modality": "ultrasound", "priority": "urgent", "protocol": "Transvaginal and transabdominal obstetric ultrasound to locate the pregnancy and assess for intraperitoneal free fluid, including the left upper quadrant"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 6: `request_lab`

Argumentos: `{"priority": "urgent", "test_codes": ["quantitative serum beta-hCG"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 7: `request_imaging`

Argumentos: `{"body_region": "pelvis", "modality": "ultrasound", "priority": "urgent", "protocol": "Transvaginal obstetric ultrasound to identify an intrauterine pregnancy and evaluate the adnexa and pelvic free fluid"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_007", "status": "reported", "value": "No intrauterine gestational sac; endometrium 8 mm; no adnexal abnormality."}], "order_recorded": false}`

### Passo 8: `request_imaging`

Argumentos: `{"body_region": "left upper abdomen", "modality": "ultrasound", "priority": "stat", "protocol": "Focused evaluation of the spleen and left upper quadrant for a mass or ectopic gestation and intraperitoneal free fluid"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 9: `request_imaging`

Argumentos: `{"body_region": "abdomen and pelvis", "modality": "CT", "priority": "urgent", "protocol": "With IV contrast to evaluate for extrauterine pregnancy, splenic lesion, and hemoperitoneum after nondiagnostic transvaginal ultrasound"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_008", "status": "reported", "value": "Contrast CT showed a vascular left upper abdominal mass about 46 × 40 × 56 mm."}], "order_recorded": false}`

### Passo 10: `plan_reason`

Argumentos: `{"next_actions": ["Urgent obstetrics and gynecology and surgical evaluation", "Obtain CBC, blood type and Rh status, and crossmatch if available", "Assess promptly for intra-abdominal bleeding and need for operative management"], "summary": "Approximately five weeks pregnant with worsening left upper abdominal pain, nausea and vomiting. Vital signs are stable, with left upper abdominal tenderness. Transvaginal ultrasound shows no intrauterine gestational sac or adnexal abnormality; CT shows a 46 × 40 × 56 mm vascular left upper abdominal mass. An extrauterine pregnancy is a time-sensitive concern, though its location remains unconfirmed.", "working_diagnoses": ["Left upper abdominal ectopic pregnancy, possibly splenic", "Pregnancy of unknown location with an unrelated splenic vascular lesion", "Other abdominal ectopic pregnancy"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 11: `request_imaging`

Argumentos: `{"body_region": "abdomen and pelvis", "modality": "MRI", "priority": "urgent", "protocol": "Without gadolinium; characterize the vascular left upper abdominal mass, its relationship to the spleen, and any intraperitoneal bleeding in a pregnancy of unknown location"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 12: `request_procedure`

Argumentos: `{"indication": "Pregnancy of unknown location with worsening left upper abdominal pain, no intrauterine or adnexal pregnancy on ultrasound, and a 46 × 40 × 56 mm vascular left upper abdominal mass on CT; assess for abdominal ectopic pregnancy and bleeding.", "procedure_code_or_name": "Urgent diagnostic laparoscopy with evaluation of the left upper abdominal mass and possible treatment of ectopic pregnancy", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "procedure_result", "fact_id": "procedure_result_009", "status": "reported", "value": "Diagnostic laparoscopy: ~300 mL hemoperitoneum and actively bleeding 6 × 4 × 5 cm lesion between spleen and descending colon, involving omentum; uterus, ovaries and tubes appeared normal."}], "order_recorded": true}`

### Passo 13: `request_procedure`

Argumentos: `{"indication": "Diagnostic laparoscopy documented approximately 300 mL hemoperitoneum and an actively bleeding 6 × 4 × 5 cm lesion involving the omentum in a patient with pregnancy of unknown location.", "procedure_code_or_name": "Laparoscopic excision of the bleeding left upper abdominal lesion with hemostasis and histopathologic examination", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"order_recorded": true, "result": "not_available_in_source"}`

### Passo 14: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.9, "differential": ["Other left upper abdominal ectopic pregnancy", "Bleeding omental vascular lesion with a separate pregnancy of unknown location"], "primary": "Probable omental ectopic pregnancy with hemoperitoneum", "supporting_fact_ids": ["hpi_002", "physical_exam_005", "imaging_007", "imaging_008", "procedure_result_009"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 15: `disposition`

Argumentos: `{"category": "surgery", "followup_or_handoff": "Immediate surgical and obstetric handoff for hemorrhage control, monitoring, and pathology review; confirm pregnancy resolution after treatment.", "rationale": "Laparoscopy documented approximately 300 mL hemoperitoneum and an actively bleeding left upper abdominal lesion in early pregnancy. Operative excision and hemostasis were ordered, but their outcome is not documented.", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"category": "surgery", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `15`. Ações: `15`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
