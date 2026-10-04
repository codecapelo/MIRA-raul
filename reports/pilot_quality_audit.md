> **Histórico: piloto técnico v1 invalidado e arquivado em `logs/incomplete/technical_invalid_v1`. Não integra a rodada corrigida.**

# Qualidade do piloto — cinco modelos, case_001

**Conclusão operacional:** cinco terminais concluídos, sem erros de backend ou ferramenta registrados nesses terminais. **Conclusão de qualidade:** esse sucesso operacional não demonstra fidelidade narrativa ou recuperação correta. Há invenção de fatos pelo paciente em três condições e divulgação de achados de outros exames após pedido de ECG em três condições. Nenhum terminal foi alterado, removido ou repetido nesta revisão.

| Modelo | Paciente: invenção observada | Respostas paciente revisadas | Logprobs médico: pedidos / retornos não vazios | Valores de ferramentas iguais ao caso | Associação semântica incorreta observada |
|---|---|---:|---:|---|---|
| GPT-OSS | Sim | 8 | 15 / 0 | Sim | Nenhum ECG→TTE/OCT observado |
| GPT-5.2 | Sim | 1 | 0 / 0 | Sim | Nenhum ECG→TTE/OCT observado |
| Qwen 3.5 | Sim | 1 | 4 / 4 | Sim | ECG→TTE e OCT/IVUS |
| GLM-4.5-Air | Desconhecido: paciente não chamado | 0 | 0 / 0 | Sim | ECG→TTE e OCT/IVUS |
| GLM-5 | Nenhuma invenção factual clara na resposta revisada | 1 | 4 / 0 | Sim | ECG→TTE e OCT/IVUS |

“Nenhuma invenção observada” é limitada à leitura da resposta disponível; não garante fidelidade geral. Solicitar logprobs não garante seu retorno: GPT-OSS e GLM-5 solicitaram, mas as respostas não continham logprobs; somente Qwen devolveu conteúdo de logprobs nesta amostra. Ausência de pedido em GPT-5.2/GLM-Air corresponde à configuração de suporte do endpoint.

## Fidelidade narrativa

GPT-OSS inventou dor em pressão retroesternal, irradiação, duração/intensidade e horário, além de frequência de diálise e negativa de alergias. O médico usou características inventadas no diagnóstico final; há também deriva do paciente para aconselhamento profissional. Evidência detalhada em `patient_fidelity_case001_gptoss.md`.

GPT-5.2 inventou dor de pressão central com irradiação ao braço, dispneia, sudorese, náusea, tontura e palpitações, ausentes de `patient.json`. A justificativa final reutiliza sintomas como dor isquêmica, dispneia e sudorese. Qwen acrescentou negativas de dispneia/cough/irradiação e fadiga sem suporte: informação desconhecida foi convertida em afirmações clínicas. GLM-5 manteve desconhecidos descritores, horário e sintomas; os antecedentes narrados estavam disponíveis. GLM-Air concluiu usando ferramentas sem chamar paciente; não existe saída de paciente para avaliar nessa trajetória.

## Valores exatos não significam exame correto

Todos os pares nome/valor devolvidos pelas ferramentas correspondem exatamente a observações de `cases/case_001/investigations.json`. Não observei fabricação de valores de ferramenta ou divulgação da string de referência pelo paciente.

Entretanto Qwen, GLM-Air e GLM-5 pediram apenas `ECG`; o matcher selecionou `ecg_008` (ecocardiografia transtóracica) e `ecg_010` (OCT/ultrassom intravascular). Isso entregou tamponamento e pseudoaneurisma sem pedido dos exames que os produzem. Eletrocardiograma não é ecocardiografia ou OCT/IVUS. Os itens estão erroneamente classificados no domínio `ecg` da adaptação e o matcher aceitou essa categoria como associação. O código valida presença da chave, mas não protege a equivalência clínica de exame. Essa falha contaminou a evidência entregue aos três médicos, portanto suas decisões positivas do juiz não constituem desempenho isolado dos modelos médicos.

Nas três condições, pedido posterior de ecocardiograma pela ferramenta radiológica retornou indisponibilidade porque a ecocardiografia estava no domínio `ecg`, demonstrando também dependência do caminho de ferramenta. Em GPT-5.2, a associação de pedido de análise/cultura/citologia pericárdica ao achado macroscópico da pericardiocentese preservou o valor original, mas mistura categorias de exame; merece revisão clínica adicional. Valores originais permanecem disponíveis para rastrear essas escolhas.

## Escopo e evidência

Revisão independente de todos os rastros terminais `logs/raw/<modelo>/case_001.jsonl`, cruzados com `cases/case_001/patient.json`, `investigations.json`, configuração e pedidos/respostas brutos. Contagens, estados, hashes dos rastros e conclusão operacional por modelo constam de `pilot_quality_audit.json`. Percursos interrompidos Deka/Akash não foram misturados com estes terminais. Não foram feitas chamadas pagas, executado o runner ou alterados código/configuração/casos ativos.

Esta auditoria é de fidelidade e integridade operacional, não adjudicação médica definitiva. O médico humano ainda precisa revisar os diagnósticos e a adequação de cada associação de exame. A condição atual permanece preservada para análise; quaisquer correções futuras exigem identificação de nova condição, sem substituição silenciosa dos resultados.
