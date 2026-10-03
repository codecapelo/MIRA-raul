# Auditoria de fidelidade e decisões de correção

**Estado:** revisão editorial independente concluída em 26-09-2026; segunda conferência das correções concluída. O signoff médico permanece pendente. Os PDFs originais e as licenças não foram alterados.

## Trilha de versões

| Versão | Destino dos traces | Motivo de exclusão do painel principal |
|---|---|---|
| Corpus v1 | `results/exploratory_v1/` | Idade exata criada para o caso 003 apesar de a fonte informar apenas início dos 30 anos. |
| Corpus v2, protocolos v2–v4 | `results/exploratory_v2_*`, `results/exploratory_v3_aborted/`, `results/exploratory_v4_aborted/` | Pilotos de interação e auditoria detectaram falhas de unidade, cronologia e critérios clínicos. Nenhum trace entra nas estimativas do próximo painel. |
| Corpus v3, protocolo v5 | `results/raw/` sob o manifesto congelado v5 | Correções abaixo, com dez casos e três repetições por modelo. |

## Achados e correções editoriais

| Caso | Evidência no PDF | Risco para o benchmark | Correção |
|---|---|---|---|
| 001 | JACC pp. 2–3: internação prolongada e alta; a unidade de terapia intensiva não foi especificada. *Covered stent* foi estratégia do caso, sem padrão único. | Disposição inferida marcada como fato e tratamento particular marcado obrigatório. | Disposição publicada `unknown`; UTI e cirurgia são opções condicionais para revisão médica. *Covered stent* passou a ação opcional e contextual. |
| 002 | JACC p. 3: D-dímero **2,94 µg/mL**, referência <0,5 µg/mL; houve cateterismo cardíaco direito invasivo. | Erro de unidade de 1.000 vezes e subcontagem de procedimentos. | Unidade corrigida; cateterismo liberado por `request_procedure`. |
| 003 | BMJ pp. 1–4, Tabelas 1–2: ruptura e laparotomia precedem sepse, reação a medicamentos e culturas tardias. A segunda reação ocorreu após reexposição a piperacilina–tazobactam. | Exigência de eventos futuros e inferência de segurança impossível no encontro inicial. | Alvo diagnóstico do encontro agudo é a ruptura, separado do diagnóstico final publicado com sepse. Sinais imediatos pós-cirurgia só abrem após laparotomia. Culturas tardias permanecem bloqueadas; reação corrigida e excluída da oportunidade de segurança do MVP agudo. Proveniência por página/tabela mais específica. |
| 004 | Respirology pp. 1–2: primeira toracocentese, melhora, retorno ao pronto-socorro dias depois e segunda drenagem. | Um único resultado do EHR antecipava a visita posterior; análise pleural sem coleta prévia. | `time_zero` é o retorno ao pronto-socorro. O primeiro líquido pleural é registro prévio; a segunda toracocentese libera apenas o resultado da segunda drenagem. Unidade de internação do relato não é assumida. |
| 005 | BMJ p. 1: PET e caracterização BRAF/KIT seguem citologia/biópsia pleural. | Resultado de estadiamento/molecular podia aparecer antes de haver tecido. | Ambos exigem biópsia pleural antes de serem liberados. Ausência de histologia rara antes de tecido não é erro crítico automático. |
| 006 | Frontiers pp. 2–4: biópsia adrenal descrita, mas exclusão bioquímica de feocromocitoma e unidade de internação não documentadas. | A rubrica poderia premiar biópsia como automaticamente segura e inventar disposição. | Biópsia opcional e condicionada; revisão médica deve checar feocromocitoma/benefício. Disposição publicada `unknown`. Referência normativa: [ESE 2023, R.6.3.5](https://doi.org/10.1093/ejendo/lvad066). |
| 009 | Journal of Surgical Case Reports pp. 1–2: TC pré-operatória descreve corpo estranho linear; identidade do stent surge na cirurgia. A operação começa por laparoscopia e converte para aberta; depois a paciente foi transferida intubada à UTI. | Spoiler na imagem, exigência de laparotomia como única abordagem, ressecção revelada sem ordem e disposição pós-operatória classificada incorretamente. | TC mantém apenas corpo estranho; laparoscopia ou exploração aberta são aceitas, mas ressecção exige pedido separado. UTI é destino publicado após cirurgia, enquanto cirurgia é handoff imediato clinicamente aceitável. |
| 010 | Medicine p. 2: achado intraoperatório e confirmação histológica são etapas distintas. | O EHR devolvia patologia junto com a primeira laparoscopia. | Resultado anatomopatológico exige pedido posterior de patologia; teste temporal cobre a separação. |

Casos 007 e 008 não apresentaram discrepância factual material na auditoria inicial. Em todos os dez rubrics, a lista de diagnósticos críticos foi reformulada em termos de síndromes ou ameaças reconhecíveis no ponto de avaliação; o diagnóstico histológico raro continua no desfecho diagnóstico publicado, sem virar erro de segurança antecipado.

## Regras de interpretação

Os campos `published_final_diagnosis` e `source_treatment` descrevem o relato. `acceptable_diagnoses`, `disposition_acceptability` e itens de segurança definem possibilidades de julgamento clínico **separadas** do que o artigo fez. Um resultado `not_available_in_source` não é normalidade. A checagem determinística de conceito diagnóstico é exploratória; a revisão médica cega deve julgar alternativas, oportunidade temporal, indicação de exames e dano potencial.

O corpus é público e pode ter contaminado o treinamento. Esta auditoria reduz erros do benchmark, mas não substitui uma validação clínica independente nem transforma dez relatos selecionados em estimativa populacional de segurança.
