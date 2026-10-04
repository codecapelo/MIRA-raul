# Fidelidade do paciente — GPT-OSS / case_001

**Falha de fidelidade observada no pipeline.** O terminal STEMI incorreto não pode ser atribuído exclusivamente ao médico: o paciente simulado inventou características que o médico usou diretamente na justificativa final. O prompt prescreve fidelidade aos fatos; a saída real não a garantiu. O terminal e seu custo permanecem preservados, sem exclusão ou reexecução.

Condição: GPT-OSS em médico e paciente, Mancer FP8, commit `3418b001a5c9c4f8b6a7ca4a0b57e6589ed71fba`. Terminal: nove turnos externos, sete ferramentas, `tool_errors=0`, custo US$ 0,009107370, juiz `decision=false`. Zero erros de ferramenta/backend não significa ausência de alucinação narrativa.

| Fato autorizado em `patient.json` | Saída observada do paciente | Avaliação |
|---|---|---|
| Dor torácica nova durante tratamento de bacteremia/endocardite | Pressão/peso, localização retroesternal central | Características não fornecidas; inventadas |
| Sem descrição de irradiação | Irradiação para braço esquerdo e mandíbula, sem dor em costas/pescoço | Características não fornecidas; inventadas |
| Sem horário, duração ou intensidade | Início há quatro horas, contínua, intensidade 7/10 variando para 3–4 | Características não fornecidas; inventadas |
| Hemodiálise, sem frequência | Hemodiálise três vezes por semana | Frequência não fornecida; inventada |
| `unknown_fields` inclui alergias | Nenhuma alergia conhecida aos sedativos | Negativa não autorizada |
| Papel de paciente, linguagem simples | Checklist profissional, instruções de sedação, estimativas de internação e respostas como equipe clínica | Deriva de papel observada |

A justificativa final do médico cita explicitamente dor de pressão irradiando para braço/mandíbula e início súbito, características criadas na primeira resposta do paciente. Ela também acrescenta “exertional”, não sustentado pela saída que dizia estar sentado. Não houve ECG ou biomarcador disponível que demonstrasse elevação do ST; o diagnóstico STEMI extrapolou os dados entregues. Portanto a falha combina contaminação da narrativa simulada e extrapolação do médico.

Os resultados objetivos devolvidos coincidem com os dados autorizados: exame físico informou deterioração hemodinâmica/choque; ECG, radiografia e exames laboratoriais solicitados estavam indisponíveis no pool correspondente. Não foram entregues resultados numéricos ou ECG inventados. O médico não pediu a ecocardiografia ou a angiografia disponíveis que poderiam esclarecer tamponamento e pseudoaneurisma. Não observei divulgação do diagnóstico de referência pelo paciente ou matcher.

Evidência primária: `cases/case_001/patient.json`; `cases/case_001/investigations.json`; `logs/raw/openai__gpt-oss-120b/case_001.jsonl`, primeira resposta com papel `patient`, respostas subsequentes do paciente, sete eventos `tool`, resposta `judge` e `case_complete`. Esta é revisão documental independente, sem chamada de modelo e sem revisão médica assinada. A fidelidade dos demais modelos deve ser examinada separadamente, como dimensão exploratória do pipeline.
