# Auditoria de fidelidade dos dois pilotos v4 — 08-10-2026

Leitura somente dos dois casos públicos, respectivos `patient.json`/`investigations.json` e traces terminais em `/Users/test/.codex/worktrees/mira-review-v38/MIRA-RAUL/runs/v4/sol/run1`. Commit dos dois resultados: `25471d1e13eeff8ba03db2115cd8591581288162`. Nenhum arquivo de código, input ou HEAD alterado; nenhuma inferência ou chamada paga feita por esta auditoria; nenhum caso privado consultado. O JSON acompanhante guarda verificações, custos e referências de linhas.

## Resultado observado

| | Caso 001 | Caso 002 | Total |
|---|---:|---:|---:|
| Juiz LLM marcou correto | Sim | Não | 1/2 |
| Proposta antes da cascata correta pelo juiz | Sim | Não | 1/2 |
| Falas ao médico / ao revisor | 1 / 1 | 2 / 1 | 5 respostas |
| Fontes de exames cobradas | 4 | 5 | 9 |
| Unidades relativas executadas | 26 | 27 | 53 |
| OpenRouter, encontro inteiro | US$ 0,01788875 | US$ 0,01371400 | US$ 0,03160275 |
| OpenRouter, implantação (sem paciente/juiz) | US$ 0,00722275 | US$ 0,00274800 | US$ 0,00997075 |

Os custos OpenRouter são os valores registrados pelos traces; esta auditoria não consultou a conta/ledger ao vivo. As chamadas Codex usaram assinatura, com custo monetário desconhecido. A CLI não atestou modelo servido (`requested_only`); o ID solicitado foi `gpt-6.1-sol`. Uma execução em dois casos conhecidos não estima desempenho externo e não permite prometer 100%.

## Paciente e exames

As cinco falas foram lidas e comparadas com os registros públicos de paciente. Não encontrei novo fato clínico claramente inventado: medicação, colite controlada, infecção prévia, evolução e antibiótico IV se apoiam no registro; informações ausentes continuam desconhecidas. As falas têm 20 a 60 palavras. Isso é uma inspeção de fidelidade factual pequena, não validação médica ou teste geral de resistência à invenção.

A linguagem de ausência merece refinamento: o paciente diz “não me lembro” sobre fatos simplesmente não relatados, e no caso 001 responde que exposições “não foram mencionadas”. Preserva o desconhecimento, mas soa como um leitor de registro. Não indica presença/ausência clínica dessas exposições.

As **9 ocorrências de achados entregues** conferem literalmente com o valor da fonte correspondente. Não houve invenção de valor numérico nem trecho de outro exame identificado nessa checagem. Os eventos `exam_cost` somam os mesmos 53 pontos do resumo. Nenhuma fonte foi cobrada duas vezes; tentativas do revisor indisponíveis/repetidas não geraram custo relativo novo.

## Incidentes e limites

1. **Resultado de seguimento liberado no encontro agudo.** Caso 002, trace linha 23: `Electrophysiology study` (`ecg_015`) traz `available_at="followup"`, `prerequisites=["followup"]`, mas `unavailable_for_immediate_care=false`. A guarda trata pré-requisitos de procedimentos, não o texto simples `followup`, e liberou o estudo no turno 3. O achado é literal, mas sua cronologia é comprimida; proposta e diagnóstico final usam o estudo. Não interpretar como simulação aguda com controle temporal completo. É condição herdada da base v3, não invenção do modelo.
2. **Auto-resolução de pré-requisito redundante.** Caso 001, `followup_result`, linha 64: pedido de cultura de tecido coronário/stent recebe dica genérica “Pericardiocentesis or Cardiac device surgical exploration”. O resolver escolhe pericardiocentese já feita duas vezes; o pedido permanece bloqueado. Não houve resultado novo ou cobrança relativa, mas há redundância e dica de pré-requisito sem especificidade anatômica. Recomenda-se corrigir em condição futura, sem reclassificar esta execução.
3. **Cultura histórica, não nova coleta demonstrada.** Caso 001, linha 9: pedido de repetição de hemoculturas devolve a bacteremia MRSA já documentada. O texto informa que horário de coleta/sensibilidade são desconhecidos. A simulação entrega um registro existente; não comprova que uma nova cultura foi colhida ou voltou positiva naquele momento.
4. **Interação mínima aconteceu tarde no caso emergencial.** Caso 001 só falou com o paciente após uma tentativa de admissão bloqueada por ausência de conversa. A proteção funcionou (uma troca antes de admitir), mas os exames vieram primeiro. Não tratar esse comportamento como entrevista completa antes de investigar.

## Proposta versus diagnóstico final

No caso 001, o médico já propôs infecção do stent/pseudoaneurisma com tamponamento; o revisor manteve o núcleo e refinou a incerteza. A cascata não converteu erro em acerto neste caso.

No caso 002, o médico propôs standstill atrial/bloqueio AV e insuficiência cardíaca direita, sem fechar miocardite atrial isolada. O revisor inicialmente sugeriu **suspeita** de miocardite atrial isolada, mas pediu biópsia/histologia e cronologia da mesalazina. Os dados adicionais não estavam disponíveis; o final voltou à síndrome elétrica e causa não confirmada. O juiz marcou falso por faltar a etiologia específica exigida. Isso documenta uma falha contra o alvo do benchmark, sem demonstrar por si só que expressar essa incerteza foi uma conduta insegura.

Conclusão operacional: o piloto preservou fatos e contabilizou exames entregues corretamente, mas **não manteve 100% pelo juiz**. Antes de atribuir benefício clínico, é necessário decidir e congelar o objetivo de julgamento (diagnóstico etiológico exato versus alternativa sindrômica aceitável), validar temporalidade e testar em dados que não participaram do ajuste.
