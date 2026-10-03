# Revisão clínica R57BD9CAF1CD7

Caso: `case_009`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_009", "initial": {"age_years": 70, "chief_complaint": "Progressively worsening diffuse abdominal pain, distension and nausea.", "sex_recorded": "female"}, "setting": "emergency_department"}`

## Trajetória observável

### Passo 1: `ask_history`

Argumentos: `{"question": "When did the abdominal pain and distension begin, how have they progressed, and have you had vomiting, fever, blood in the stool, or difficulty passing stool or gas?", "topic_code": "abdominal_pain_history"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 2: `request_physical_exam`

Argumentos: `{"region_or_system": "Vital signs and abdominal examination, including distension, tenderness, guarding, rebound, and bowel sounds"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_004", "status": "reported", "value": "Signs of peritoneal irritation."}], "order_recorded": false}`

### Passo 3: `request_imaging`

Argumentos: `{"body_region": "abdomen and pelvis", "modality": "CT", "priority": "stat", "protocol": "With intravenous contrast to evaluate for bowel obstruction, perforation, ischemia, or other causes of peritonitis"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_006", "status": "reported", "value": "CT: multiple small-bowel air–fluid levels and a linear hyperdense intraluminal structure consistent with a foreign body; mechanical obstruction suspected."}], "order_recorded": false}`

### Passo 4: `plan_reason`

Argumentos: `{"next_actions": ["Urgent surgical assessment for operative exploration given peritoneal signs", "Obtain vital signs and assess hemodynamic stability", "Obtain CBC, metabolic panel, lactate, coagulation studies and type and screen", "Keep nil by mouth and establish intravenous access"], "summary": "Progressive abdominal pain, distension and nausea with peritoneal irritation; CT shows small-bowel air–fluid levels and a linear intraluminal foreign body with suspected mechanical obstruction.", "working_diagnoses": ["Foreign-body–associated small-bowel obstruction", "Small-bowel perforation from a foreign body", "Strangulated small-bowel obstruction with ischemia"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 5: `request_procedure`

Argumentos: `{"indication": "Peritoneal irritation with CT evidence of suspected foreign-body–associated mechanical small-bowel obstruction, concerning for perforation or bowel ischemia.", "procedure_code_or_name": "Emergency surgical exploration of the abdomen", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"order_recorded": true, "result": "not_available_in_source"}`

### Passo 6: `request_lab`

Argumentos: `{"priority": "stat", "test_codes": ["Complete blood count", "Comprehensive metabolic panel", "Serum lactate", "Coagulation panel (PT/INR and aPTT)", "Type and screen"]}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 7: `request_physical_exam`

Argumentos: `{"region_or_system": "Vital signs and hemodynamic status: blood pressure, heart rate, respiratory rate, oxygen saturation, temperature, mental status and peripheral perfusion"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_004", "status": "reported", "value": "Signs of peritoneal irritation."}], "order_recorded": false}`

### Passo 8: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.85, "differential": ["Foreign-body–induced small-bowel perforation", "Strangulated small-bowel obstruction with ischemia"], "primary": "Foreign-body–associated mechanical small-bowel obstruction", "supporting_fact_ids": ["imaging_006", "physical_exam_004"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 9: `disposition`

Argumentos: `{"category": "surgery", "followup_or_handoff": "Immediate surgical and anesthesia handoff for emergency abdominal exploration, already ordered. Keep nil by mouth, establish intravenous access, and assess hemodynamic status. Vital signs and laboratory results are unavailable; operative findings are not documented.", "rationale": "Suspected foreign-body–associated mechanical small-bowel obstruction with peritoneal irritation, concerning for perforation or ischemia.", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"category": "surgery", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `9`. Ações: `9`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
