# Revisão clínica R8CA0ABAA0F29

Caso: `case_009`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_009", "initial": {"age_years": 70, "chief_complaint": "Progressively worsening diffuse abdominal pain, distension and nausea.", "sex_recorded": "female"}, "setting": "emergency_department"}`

## Trajetória observável

### Passo 1: `ask_history`

Argumentos: `{"question": "When did the abdominal pain and distension begin, how have they progressed, and have you had vomiting or been unable to pass stool or gas?", "topic_code": "abdominal_symptoms"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 2: `request_physical_exam`

Argumentos: `{"region_or_system": "vital signs"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_004", "status": "reported", "value": "Signs of peritoneal irritation."}], "order_recorded": false}`

### Passo 3: `request_imaging`

Argumentos: `{"body_region": "abdomen and pelvis", "modality": "CT", "priority": "stat", "protocol": "with IV contrast; evaluate obstruction, perforation, and bowel ischemia"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_006", "status": "reported", "value": "CT: multiple small-bowel air–fluid levels and a linear hyperdense intraluminal structure consistent with a foreign body; mechanical obstruction suspected."}], "order_recorded": false}`

### Passo 4: `plan_reason`

Argumentos: `{"next_actions": ["Obtain urgent surgical evaluation for operative exploration", "Assess hemodynamic status and resuscitation needs", "Obtain focused preoperative laboratory studies"], "summary": "70-year-old woman with progressive diffuse abdominal pain, distension, nausea, peritoneal irritation, and CT showing small-bowel air–fluid levels with a linear intraluminal foreign body and suspected mechanical obstruction. Peritoneal signs raise concern for bowel injury or ischemia requiring urgent surgical evaluation.", "working_diagnoses": ["Foreign-body-related small-bowel obstruction with possible perforation", "Small-bowel ischemia", "Other mechanical small-bowel obstruction"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 5: `request_procedure`

Argumentos: `{"indication": "Peritoneal irritation and CT evidence of mechanical small-bowel obstruction with a linear intraluminal foreign body; concern for perforation or ischemia.", "procedure_code_or_name": "Emergency exploratory laparotomy with evaluation and removal of the small-bowel foreign body and repair or resection of injured bowel as indicated", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "procedure_result", "fact_id": "procedure_result_007", "status": "reported", "value": "Emergency laparoscopy converted to open operation because of purulent fluid and adhesions. A Meckel diverticulum ~40 cm proximal to ileocecal valve contained a biliary stent; its distal end perforated adjacent ileum."}, {"domain": "procedure_result", "fact_id": "procedure_result_008", "status": "reported", "value": "About 20 cm of small bowel, including diverticulum and perforation, was resected with side-to-side anastomosis, irrigation and drainage."}], "order_recorded": true}`

### Passo 6: `ask_history`

Argumentos: `{"question": "Do you have any medication allergies, particularly to penicillins, cephalosporins, or other antibiotics?", "topic_code": "allergies"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 7: `prescribe_medication`

Argumentos: `{"dose_unit": "g", "dose_value": 4.5, "drug_generic": "piperacillin-tazobactam", "duration": "4 days after surgical source control, reassess clinically", "frequency": "every 8 hours by extended infusion; adjust for renal function when available", "indication": "Perforated ileum with purulent peritonitis after operative source control", "route": "IV"}`

Resultado: `ok`

Dados retornados: `{"order_recorded": true, "safety_not_adjudicated": true}`

### Passo 8: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.99, "differential": [], "primary": "Perforated ileum caused by a biliary stent lodged in a Meckel diverticulum, with purulent peritonitis and mechanical small-bowel obstruction", "supporting_fact_ids": ["physical_exam_004", "imaging_006", "procedure_result_007", "procedure_result_008"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 9: `disposition`

Argumentos: `{"category": "ward", "followup_or_handoff": "Hand off to the surgical team for postoperative vital signs and abdominal monitoring, fluid management, review of renal function and antibiotic dosing, and reassessment for complications.", "rationale": "Following bowel resection for ileal perforation with purulent peritonitis, she requires inpatient surgical care and monitoring. No documented findings establish an ICU requirement.", "urgency": "immediate postoperative admission"}`

Resultado: `ok`

Dados retornados: `{"category": "ward", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `9`. Ações: `9`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
