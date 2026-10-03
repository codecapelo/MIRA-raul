# Revisão clínica RFB1CCDDDF8F5

Caso: `case_009`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_009", "initial": {"age_years": 70, "chief_complaint": "Progressively worsening diffuse abdominal pain, distension and nausea.", "sex_recorded": "female"}, "setting": "emergency_department"}`

## Trajetória observável

### Passo 1: `ask_history`

Argumentos: `{"question": "What is the character and location of the abdominal pain?", "topic_code": "abdominal_pain_character_location"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 2: `ask_history`

Argumentos: `{"question": "Have you had any recent changes in bowel habits or stool characteristics?", "topic_code": "bowel_habits_stool_characteristics"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 3: `ask_history`

Argumentos: `{"question": "Do you have a history of abdominal surgeries or hernias?", "topic_code": "surgical_history_hernias"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 4: `request_physical_exam`

Argumentos: `{"region_or_system": "abdomen"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_004", "status": "reported", "value": "Signs of peritoneal irritation."}], "order_recorded": false}`

### Passo 5: `plan_reason`

Argumentos: `{"next_actions": ["CT abdomen pelvis with contrast", "IV fluid resuscitation", "NPO status", "Urgent surgical consultation"], "summary": "70-year-old female presenting with progressively worsening diffuse abdominal pain, distension and nausea. Physical exam reveals signs of peritoneal irritation. This is concerning for an acute surgical abdomen until proven otherwise.", "working_diagnoses": ["Acute appendicitis", "Small bowel obstruction", "Perforated viscus", "Diverticulitis with perforation", "Gastrointestinal bleed"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 6: `request_imaging`

Argumentos: `{"body_region": "abdomen pelvis", "modality": "CT", "priority": "stat", "protocol": "with contrast"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_006", "status": "reported", "value": "CT: multiple small-bowel air–fluid levels and a linear hyperdense intraluminal structure consistent with a foreign body; mechanical obstruction suspected."}], "order_recorded": false}`

### Passo 7: `plan_reason`

Argumentos: `{"next_actions": ["IV fluid resuscitation", "NPO status", "Urgent surgical consultation", "Consider nasogastric decompression"], "summary": "70-year-old female with progressively worsening diffuse abdominal pain, distension and nausea. Physical exam shows signs of peritoneal irritation. CT abdomen pelvis reveals multiple small-bowel air-fluid levels and a linear hyperdense intraluminal structure consistent with a foreign body; mechanical obstruction suspected. This is concerning for small bowel obstruction with possible perforation given peritoneal signs.", "working_diagnoses": ["Small bowel obstruction with foreign body", "Perforated viscus", "Acute appendicitis", "Diverticulitis with perforation", "Gastrointestinal bleed"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 8: `request_procedure`

Argumentos: `{"indication": "Small bowel obstruction with distension and nausea", "procedure_code_or_name": "nasogastric decompression", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"order_recorded": true, "result": "not_available_in_source"}`

### Passo 9: `prescribe_medication`

Argumentos: `{"dose_unit": "mL", "dose_value": 1000, "drug_generic": "lactated ringers", "duration": "continue as needed", "frequency": "bolus", "indication": "Fluid resuscitation for small bowel obstruction", "route": "IV"}`

Resultado: `ok`

Dados retornados: `{"order_recorded": true, "safety_not_adjudicated": true}`

### Passo 10: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.85, "differential": ["Perforated viscus", "Acute appendicitis", "Diverticulitis with perforation", "Gastrointestinal bleed"], "primary": "Small bowel obstruction with foreign body", "supporting_fact_ids": ["physical_exam_004", "imaging_006"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 11: `disposition`

Argumentos: `{"category": "surgery", "followup_or_handoff": "Transfer to surgery for urgent evaluation and management of small bowel obstruction", "rationale": "70-year-old female with small bowel obstruction and signs of peritoneal irritation requiring urgent surgical evaluation and possible intervention", "urgency": "urgent"}`

Resultado: `ok`

Dados retornados: `{"category": "surgery", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `7`. Ações: `11`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
