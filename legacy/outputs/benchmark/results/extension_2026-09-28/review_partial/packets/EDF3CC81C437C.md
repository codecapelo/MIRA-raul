# Revisão clínica EDF3CC81C437C

Caso: `case_003`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_003", "initial": {"age_band": "early 30s", "age_years": null, "chief_complaint": "Severe lower abdominal pain and dyspnea after catheter drainage failure.", "sex_recorded": "female"}, "setting": "urology_clinic"}`

## Trajetória observável

### Passo 1: `request_physical_exam`

Argumentos: `{"region_or_system": "Vital signs and cardiopulmonary examination"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_004", "status": "reported", "value": "Cardiopulmonary decompensation on presentation; specific initial preoperative vital signs not reported."}], "order_recorded": false}`

### Passo 2: `request_imaging`

Argumentos: `{"body_region": "abdomen and pelvis", "modality": "CT", "priority": "stat", "protocol": "CT cystography with retrograde contrast via urinary catheter"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_005", "status": "reported", "value": "Urgent contrast CT with retrograde pouch contrast: large left laterodorsal reservoir defect, contrast leakage into peritoneum and free intraperitoneal fluid."}], "order_recorded": false}`

### Passo 3: `plan_reason`

Argumentos: `{"next_actions": ["Urgent urologic surgical evaluation and repair", "Supportive resuscitation and perioperative monitoring"], "summary": "Severe abdominal pain and dyspnea after catheter drainage failure with cardiopulmonary decompensation. CT cystography shows a large left laterodorsal urinary reservoir defect with intraperitoneal contrast extravasation and free fluid, consistent with intraperitoneal urinary reservoir rupture.", "working_diagnoses": ["Intraperitoneal urinary reservoir perforation with urinary ascites", "Acute cardiopulmonary decompensation secondary to intra-abdominal urinary leak", "Peritonitis"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 4: `request_procedure`

Argumentos: `{"indication": "CT-confirmed large urinary reservoir defect with intraperitoneal contrast extravasation, free fluid, severe abdominal pain, and cardiopulmonary decompensation", "procedure_code_or_name": "Emergency exploratory laparotomy with repair of intraperitoneal urinary reservoir perforation and peritoneal washout", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "procedure_result", "fact_id": "procedure_result_012", "status": "reported", "value": "Emergency laparotomy confirmed pouch rupture, which was repaired; pouch catheter fixed and nasogastric tube placed."}], "order_recorded": true}`

### Passo 5: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.99, "differential": ["Urinary ascites due to catheter drainage failure", "Peritonitis secondary to intraperitoneal urine leak", "Cardiopulmonary decompensation secondary to acute abdominal emergency"], "primary": "Intraperitoneal urinary reservoir (pouch) rupture", "supporting_fact_ids": ["imaging_005", "procedure_result_012"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 6: `disposition`

Argumentos: `{"category": "ICU", "followup_or_handoff": "Postoperative ICU monitoring with urology surgical handoff; manage pouch catheter and nasogastric tube.", "rationale": "Emergency laparotomy confirmed and repaired intraperitoneal pouch rupture after cardiopulmonary decompensation.", "urgency": "immediate postoperative monitoring"}`

Resultado: `ok`

Dados retornados: `{"category": "ICU", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `6`. Ações: `6`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
