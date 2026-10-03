# Revisão clínica EF4E6F6F76BE7

Caso: `case_003`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_003", "initial": {"age_band": "early 30s", "age_years": null, "chief_complaint": "Severe lower abdominal pain and dyspnea after catheter drainage failure.", "sex_recorded": "female"}, "setting": "urology_clinic"}`

## Trajetória observável

### Passo 1: `request_physical_exam`

Argumentos: `{"region_or_system": "Vital signs and general cardiopulmonary/abdominal examination"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_004", "status": "reported", "value": "Cardiopulmonary decompensation on presentation; specific initial preoperative vital signs not reported."}], "order_recorded": false}`

### Passo 2: `request_imaging`

Argumentos: `{"body_region": "abdomen and pelvis", "modality": "CT", "priority": "stat", "protocol": "CT cystography with assessment for bladder rupture, catheter position, and intraperitoneal fluid"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_005", "status": "reported", "value": "Urgent contrast CT with retrograde pouch contrast: large left laterodorsal reservoir defect, contrast leakage into peritoneum and free intraperitoneal fluid."}], "order_recorded": false}`

### Passo 3: `plan_reason`

Argumentos: `{"next_actions": ["Obtain emergent urologic surgical evaluation for operative repair", "Initiate resuscitative assessment and monitoring", "Assess renal function, electrolytes, acid-base status, and infection markers"], "summary": "Severe lower abdominal pain and dyspnea after catheter drainage failure, with cardiopulmonary decompensation. CT cystography demonstrates a large left laterodorsal urinary reservoir defect with intraperitoneal contrast extravasation and free fluid.", "working_diagnoses": ["Intraperitoneal urinary reservoir/bladder rupture with urinary ascites", "Cardiopulmonary decompensation secondary to acute intraperitoneal urine leak", "Catheter drainage failure"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 4: `request_procedure`

Argumentos: `{"indication": "CT-confirmed large urinary reservoir defect with intraperitoneal contrast extravasation, free fluid, and cardiopulmonary decompensation", "procedure_code_or_name": "Emergency exploratory laparotomy with repair of intraperitoneal urinary reservoir rupture", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "procedure_result", "fact_id": "procedure_result_012", "status": "reported", "value": "Emergency laparotomy confirmed pouch rupture, which was repaired; pouch catheter fixed and nasogastric tube placed."}], "order_recorded": true}`

### Passo 5: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["basic metabolic panel", "complete blood count", "arterial blood gas", "serum lactate"]}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "lab", "fact_id": "lab_007", "status": "reported", "value": "Before surgery: WBC 15.3×10^9/L, hemoglobin 143 g/L, platelets 513×10^9/L."}, {"domain": "lab", "fact_id": "lab_008", "status": "reported", "value": "Before surgery: sodium 138 mmol/L, creatinine 1.08 mg/dL, eGFR 68 mL/min/1.73 m²."}, {"domain": "lab", "fact_id": "lab_011", "status": "reported", "value": "Postoperative ICU day 1 lactate 4.7 mmol/L."}], "order_recorded": false}`

### Passo 6: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.99, "differential": ["Catheter drainage failure", "Urinary ascites causing cardiopulmonary decompensation"], "primary": "Intraperitoneal urinary reservoir (pouch) rupture", "supporting_fact_ids": ["imaging_005", "procedure_result_012"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 7: `disposition`

Argumentos: `{"category": "ICU", "followup_or_handoff": "Continue postoperative monitoring, resuscitation as indicated, pouch catheter drainage, and urology/surgical ICU management.", "rationale": "Postoperative ICU care is indicated after emergency repair of intraperitoneal pouch rupture with documented cardiopulmonary decompensation and lactate 4.7 mmol/L.", "urgency": "immediate postoperative"}`

Resultado: `ok`

Dados retornados: `{"category": "ICU", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `7`. Ações: `7`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
