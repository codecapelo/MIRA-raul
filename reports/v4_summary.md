# v4 — resultados exploratórios, 08-10-2026

**10/10 encontros terminais; 9/10 corretos pelo juiz LLM.** A versão não demonstrou manutenção de100%. Propostas antes da revisão: 8/10. Wilson95% do escore: 59.6%–98.2%, descritivo de dez casos conhecidos; não estima acurácia externa. Revisão médica cega continua pendente.

OpenRouter: **US$ 0.12304050** total, média US$ 0.01230405/encontro. Ledger, soma dos traces e soma dos atores conferem. Delta da conta incluindo estudos v4: US$ 0.26580675; reconciliação global v4: False; uso global v4 US$ 0.28396075. Teto adicional US$5; saldo desse teto US$ 4.71603925. A primeira rodada de testes de software não enviou casos por um erro de dispatch (zero chamadas/custo); os dois primeiros terminais foram preservados após correção da exportação. A transição de commits operacionais foi conferida por hashes de todo o código clínico/configuração; não houve alteração de prompts/fatos/condição nem repetição de terminal.

Exames: 41 fontes disponíveis primeiro entregues, **247 unidades artificiais**. Unidades1/5/15 por nível, sem preço em dólares. Médico e revisores compartilham deduplicação por fonte, incluindo componentes do mesmo painel. Tentativas indisponíveis ou repetidas não cobram. Fontes compostas contam como uma observação: isso é uma convenção de simulação, não uma fatura clínica real.

Assinatura Codex: entrada 1,801,738, saída 33,901, entrada em cache 248,704. O custo monetário da assinatura é desconhecido; não inventamos um preço equivalente de API. Modelo solicitado fica registrado, mas identidade servida não é atestada pelo CLI. Amostragem/ferramentas JSON/effort medium diferem dos antigos braços API e Claude.

| Caso público | Proposta pelo juiz | Final pelo juiz | OpenRouter US$ | Exames, unidades |
|---|---|---|---:|---:|
| case_001 | True | True | 0.017889 | 26 |
| case_002 | False | False | 0.013714 | 27 |
| case_003 | True | True | 0.015350 | 22 |
| case_004 | False | True | 0.016487 | 31 |
| case_005 | True | True | 0.012432 | 11 |
| case_006 | True | True | 0.010609 | 35 |
| case_007 | True | True | 0.007443 | 12 |
| case_008 | True | True | 0.008170 | 17 |
| case_009 | True | True | 0.008809 | 20 |
| case_010 | True | True | 0.012139 | 46 |

## Ganhos demonstrados e limites

Fidelidade da extração: agora não basta ter números compatíveis para o associador inventar uma interpretação negativa; trechos qualitativos também precisam existir na fonte. Custo inclui os revisores. A fila respeita o limite por rodada, lactato desidrogenase não recebe prioridade do lactato, e endosso genérico não libera procedimento específico. Transporte pela assinatura, replay por hash e bloqueio de ferramentas nativas foram testados.

Trocar modelos/paciente/revisores mudou o resultado: esta condição não pode ser comparada como ablação isolada da política de custos nem substituir a v3.7 alegando acerto100%. Não reclassificamos resultados desfavoráveis nem ajustamos o critério após observá-los. A exceção já existente de critério do caso009 foi mantida e identificada.

A auditoria dos pilotos encontrou cronologia comprimida (exame de seguimento liberado), tentativas redundantes de resolver um pré-requisito inespecífico e cultura histórica retornada para pedido de repetição. O protótipo temporal posterior é separado e ainda não foi avaliado nesta rodada. Informações de cirurgia/publicação continuam sujeitas aos limites documentados da simulação.

## Auditoria histórica

978 arquivos legados da cópia canônica verificados sem divergência (checkout gerenciado contém888arquivos rastreados idênticos;90caches/arquivos ignorados ausentes); 290 terminais antigos analisados estruturalmente, mais os150 iniciais e207 terminais v3 existentes na auditoria. Foram examinados AGENTS e relatórios do worktree Claude atualizado, basec1d3270, em vez do main local antigo. O escore lexical antigo e os novos juízes têm denominadores/critérios distintos. Os100% antigos de workflow não significam acerto de diagnóstico. Os20/20 v3.6 são julgamento LLM em casos usados durante desenvolvimento. Fontes e PDFs não foram todos relidos visualmente palavra por palavra.

Protocolos e evidências: [v4_protocol.md](v4_protocol.md), [v4_summary.json](v4_summary.json), [v4_trace_manifest.json](v4_trace_manifest.json), [history_legacy_audit_2026-10-08.md](history_legacy_audit_2026-10-08.md), [v36_exam_accounting_audit_2026-10-08.md](v36_exam_accounting_audit_2026-10-08.md).
