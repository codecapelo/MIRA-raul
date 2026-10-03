# Revisão clínica R43FA4E02B2AD

Caso: `case_006`

Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.

A identidade do modelo e as métricas automáticas foram ocultadas neste packet.

## Encontro inicial

`{"case_id": "case_006", "initial": {"age_years": 38, "chief_complaint": "Bilateral adrenal nodules found on examination, with biochemical concern for adrenal insufficiency.", "sex_recorded": "female"}, "setting": "hospital_presentation_unit_unspecified"}`

## Trajetória observável

### Passo 1: `ask_history`

Argumentos: `{"question": "Have you experienced any recent weight loss or changes in appetite?", "topic_code": "weight_loss"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 2: `request_physical_exam`

Argumentos: `{"topic_code": "abdomen"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 3: `ask_history`

Argumentos: `{"question": "Have you experienced any recent changes in your menstrual cycle or difficulty with urination?", "topic_code": "genitourinary"}`

Resultado: `not_available_in_source`

Dados retornados: `{}`

### Passo 4: `request_physical_exam`

Argumentos: `{"topic_code": "skin"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 5: `plan_reason`

Argumentos: `{"differential": "Adrenal insufficiency, Adrenal carcinoma, Pheochromocytoma"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 6: `request_lab`

Argumentos: `{"topic_code": "adrenal_function"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 7: `request_lab`

Argumentos: `{"topic_code": "electrolytes"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 8: `request_lab`

Argumentos: `{"topic_code": "renal_function"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 9: `request_lab`

Argumentos: `{"topic_code": "thyroid_function"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 10: `request_lab`

Argumentos: `{"topic_code": "hormone_levels"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 11: `request_lab`

Argumentos: `{"topic_code": "inflammatory_markers"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 12: `request_lab`

Argumentos: `{"topic_code": "tumor_markers"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 13: `request_lab`

Argumentos: `{"topic_code": "infection_screen"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 14: `request_lab`

Argumentos: `{"topic_code": "autoimmune_screen"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 15: `request_lab`

Argumentos: `{"topic_code": "parathyroid_function"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 16: `request_lab`

Argumentos: `{"topic_code": "calcium_levels"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 17: `request_lab`

Argumentos: `{"topic_code": "phosphate_levels"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 18: `request_lab`

Argumentos: `{"topic_code": "magnesium_levels"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 19: `request_lab`

Argumentos: `{"topic_code": "potassium_levels"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 20: `request_lab`

Argumentos: `{"topic_code": "sodium_levels"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 21: `request_lab`

Argumentos: `{"topic_code": "chloride_levels"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 22: `request_lab`

Argumentos: `{"topic_code": "bicarbonate_levels"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 23: `request_lab`

Argumentos: `{"topic_code": "anion_gap"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 24: `request_lab`

Argumentos: `{"topic_code": "osmolarity"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 25: `request_lab`

Argumentos: `{"topic_code": "urine_electrolytes"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 26: `request_lab`

Argumentos: `{"topic_code": "urine_creatinine"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 27: `request_lab`

Argumentos: `{"topic_code": "urine_ketones"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 28: `request_lab`

Argumentos: `{"topic_code": "urine_protein"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 29: `request_lab`

Argumentos: `{"topic_code": "urine_glucose"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 30: `request_lab`

Argumentos: `{"topic_code": "urine_blood"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 31: `request_lab`

Argumentos: `{"topic_code": "urine_specific_gravity"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 32: `request_lab`

Argumentos: `{"topic_code": "urine_pH"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 33: `request_lab`

Argumentos: `{"topic_code": "urine_kappa_lambda_ratio"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 34: `request_lab`

Argumentos: `{"topic_code": "urine_oxalate"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 35: `request_lab`

Argumentos: `{"topic_code": "urine_citrate"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 36: `request_lab`

Argumentos: `{"topic_code": "urine_sodium"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 37: `request_lab`

Argumentos: `{"topic_code": "urine_potassium"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 38: `request_lab`

Argumentos: `{"topic_code": "urine_chloride"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 39: `request_lab`

Argumentos: `{"topic_code": "urine_phosphate"}`

Resultado: `invalid`

Dados retornados: `{}`

### Passo 40: `request_lab`

Argumentos: `{"topic_code": "urine_magnesium"}`

Resultado: `invalid`

Dados retornados: `{}`

## Encerramento

Concluído: `False`. Motivo: `max_actions`. Turnos: `40`. Ações: `40`. Saídas inválidas do modelo: `0`.

## Classificação médica

Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.
Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.
