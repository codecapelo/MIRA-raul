# Revisão clínica RD1CDB105CA38

Caso: `case_010`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_010", "initial": {"age_years": 25, "chief_complaint": "Worsening left upper abdominal pain with nausea and vomiting.", "sex_recorded": "female"}, "setting": "emergency_department"}`

## Trajetória observável

### Passo 1: `ask_history`

Argumentos: `{"question": "Please describe when the abdominal pain began, whether onset was sudden or gradual, its severity and radiation, and associated symptoms including fever, bowel changes, urinary symptoms, vaginal bleeding, or possible pregnancy.", "topic_code": "history_of_present_illness"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "hpi", "fact_id": "hpi_001", "status": "reported", "value": "Left upper quadrant pain began mildly about eight days earlier; initial noncontrast CT showed a 21 × 19 × 10 mm indeterminate lesion. Treated as gastroenteritis without improvement; now worse with nausea and vomiting."}, {"domain": "hpi", "fact_id": "hpi_002", "status": "reported", "value": "Amenorrhea and positive home urine pregnancy test; approximately five weeks gestation by dates, gravida 1 para 0."}], "order_recorded": false}`

### Passo 2: `request_physical_exam`

Argumentos: `{"region_or_system": "Vital signs and abdominal examination, including tenderness, guarding, rebound, and signs of hemodynamic instability"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_004", "status": "reported", "value": "BP 107/77 mm Hg, HR 89/min, temperature 36.7°C."}, {"domain": "physical_exam", "fact_id": "physical_exam_005", "status": "reported", "value": "Left upper abdominal tenderness; no lower abdominal tenderness, guarding or rigidity; no vaginal bleeding; cervix closed; no palpable adnexal mass or cervical motion tenderness."}], "order_recorded": false}`

### Passo 3: `request_lab`

Argumentos: `{"priority": "urgent", "test_codes": ["Quantitative serum beta-hCG", "Complete blood count", "Comprehensive metabolic panel", "Blood type, Rh status, and antibody screen"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 4: `request_imaging`

Argumentos: `{"body_region": "Abdomen and pelvis", "modality": "Ultrasound", "priority": "urgent", "protocol": "Transabdominal and transvaginal ultrasound to localize pregnancy, assess uterus and adnexa, evaluate the left upper quadrant and splenic region for the previously reported lesion, and assess for intraperitoneal free fluid."}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 5: `request_imaging`

Argumentos: `{"body_region": "Abdomen and pelvis", "modality": "MRI", "priority": "urgent", "protocol": "Without gadolinium: localize pregnancy, characterize the previously identified left upper quadrant lesion and its relationship to the spleen, and assess for ectopic implantation and intraperitoneal hemorrhage."}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 6: `request_imaging`

Argumentos: `{"body_region": "Abdomen and pelvis", "modality": "CT", "priority": "urgent", "protocol": "With intravenous contrast to characterize the left upper quadrant lesion, evaluate for splenic or other abdominal ectopic pregnancy, and assess for active bleeding or hemoperitoneum."}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_008", "status": "reported", "value": "Contrast CT showed a vascular left upper abdominal mass about 46 × 40 × 56 mm."}], "order_recorded": false}`

### Passo 7: `plan_reason`

Argumentos: `{"next_actions": ["Urgent gynecologic and general surgical assessment for diagnostic laparoscopy and management of suspected abdominal ectopic pregnancy", "Monitor hemodynamics and prepare for potential intra-abdominal hemorrhage"], "summary": "Early pregnancy with worsening left upper abdominal pain, vomiting, and a vascular left upper abdominal mass measuring 46 × 40 × 56 mm. Recorded vital signs are stable, without guarding or rigidity. Pregnancy location remains unconfirmed; laboratory and ultrasound results are unavailable.", "working_diagnoses": ["Abdominal ectopic pregnancy, possibly splenic", "Tubal ectopic pregnancy", "Vascular splenic lesion"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 8: `request_procedure`

Argumentos: `{"indication": "Suspected abdominal ectopic pregnancy: approximately five weeks pregnant with worsening left upper abdominal pain and a 46 × 40 × 56 mm vascular mass; assess implantation site and intra-abdominal bleeding, with operative management as indicated.", "procedure_code_or_name": "Urgent gynecologic and general surgical evaluation with diagnostic laparoscopy", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "procedure_result", "fact_id": "procedure_result_009", "status": "reported", "value": "Diagnostic laparoscopy: ~300 mL hemoperitoneum and actively bleeding 6 × 4 × 5 cm lesion between spleen and descending colon, involving omentum; uterus, ovaries and tubes appeared normal."}], "order_recorded": true}`

### Passo 9: `request_procedure`

Argumentos: `{"indication": "Active bleeding from a 6 × 4 × 5 cm omental lesion with approximately 300 mL hemoperitoneum in early pregnancy; normal-appearing uterus, tubes, and ovaries raise concern for omental ectopic pregnancy.", "procedure_code_or_name": "Laparoscopic excision of the bleeding omental lesion with partial omentectomy, hemostasis, evacuation of hemoperitoneum, and submission of tissue for histopathology", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"order_recorded": true, "result": "not_available_in_source"}`

### Passo 10: `request_lab`

Argumentos: `{"priority": "urgent", "test_codes": ["Histopathologic examination of the omental lesion for chorionic villi and trophoblastic tissue to confirm ectopic pregnancy"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 11: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.93, "differential": ["Other abdominal ectopic pregnancy involving the omentum", "Bleeding omental vascular lesion with coincident pregnancy of unknown location"], "primary": "Probable bleeding omental ectopic pregnancy with hemoperitoneum", "supporting_fact_ids": ["hpi_001", "hpi_002", "physical_exam_005", "imaging_008", "procedure_result_009"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 12: `disposition`

Argumentos: `{"category": "surgery", "followup_or_handoff": "Immediate gynecologic and general surgical handoff to confirm definitive excision and hemostasis, with postoperative admission and monitoring of vital signs and hemoglobin. Confirm blood type and Rh status and provide anti-D if indicated. Obtain tissue histopathology and follow quantitative beta-hCG to resolution.", "rationale": "Actively bleeding probable omental ectopic pregnancy with approximately 300 mL hemoperitoneum requires operative hemostasis. Excision was ordered, but completion and bleeding control are not documented.", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"category": "surgery", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `12`. Ações: `12`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
