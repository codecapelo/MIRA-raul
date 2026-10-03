# Revisão clínica EF394FBC00FED

Caso: `case_009`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_009", "initial": {"age_years": 70, "chief_complaint": "Progressively worsening diffuse abdominal pain, distension and nausea.", "sex_recorded": "female"}, "setting": "emergency_department"}`

## Trajetória observável

### Passo 1: `request_physical_exam`

Argumentos: `{"region_or_system": "Vital signs and abdominal examination"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "physical_exam", "fact_id": "physical_exam_004", "status": "reported", "value": "Signs of peritoneal irritation."}], "order_recorded": false}`

### Passo 2: `request_imaging`

Argumentos: `{"body_region": "abdomen and pelvis", "modality": "CT", "priority": "stat", "protocol": "CT abdomen/pelvis with IV contrast"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "imaging", "fact_id": "imaging_006", "status": "reported", "value": "CT: multiple small-bowel air–fluid levels and a linear hyperdense intraluminal structure consistent with a foreign body; mechanical obstruction suspected."}], "order_recorded": false}`

### Passo 3: `plan_reason`

Argumentos: `{"next_actions": ["Urgent surgical evaluation for operative management", "Initiate bowel-obstruction supportive management"], "summary": "Progressive abdominal pain, distension and nausea with peritoneal irritation; CT shows mechanical small-bowel obstruction with a suspected intraluminal foreign body.", "working_diagnoses": ["Mechanical small-bowel obstruction due to intraluminal foreign body", "Complicated bowel obstruction with possible ischemia or perforation"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 4: `request_procedure`

Argumentos: `{"indication": "Mechanical small-bowel obstruction with peritoneal irritation and suspected intraluminal foreign body", "procedure_code_or_name": "Exploratory laparotomy with removal of obstructing small-bowel foreign body as indicated", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"facts": [{"domain": "procedure_result", "fact_id": "procedure_result_007", "status": "reported", "value": "Emergency laparoscopy converted to open operation because of purulent fluid and adhesions. A Meckel diverticulum ~40 cm proximal to ileocecal valve contained a biliary stent; its distal end perforated adjacent ileum."}], "order_recorded": true}`

### Passo 5: `final_diagnosis`

Argumentos: `{"confidence_0_1": 0.99, "differential": ["Adhesive small-bowel obstruction", "Perforated small-bowel malignancy", "Perforated Meckel diverticulitis"], "primary": "Migrated biliary stent lodged in a Meckel diverticulum with distal-end perforation of adjacent ileum, causing mechanical small-bowel obstruction and peritonitis", "supporting_fact_ids": ["physical_exam_004", "imaging_006", "procedure_result_007"]}`

Resultado: `ok`

Dados retornados: `{"recorded": true}`

### Passo 6: `disposition`

Argumentos: `{"category": "surgery", "followup_or_handoff": "Immediate postoperative surgical care with management of intra-abdominal sepsis and monitoring for complications.", "rationale": "Operative findings confirm perforated ileum from migrated biliary stent within a Meckel diverticulum, with purulent peritonitis and mechanical small-bowel obstruction.", "urgency": "emergent"}`

Resultado: `ok`

Dados retornados: `{"category": "surgery", "recorded": true}`

## Encerramento

Concluído: `True`. Motivo: `completed`. Turnos: `6`. Ações: `6`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
