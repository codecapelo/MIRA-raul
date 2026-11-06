# Qualidade da anamnese: da primeira versão à v5

Data: 17/10/2026. Auditoria documental exploratória, sem novas inferências pagas, sem alterar fontes ou executar encontros.

## Conclusão

A história mostra avanço na infraestrutura, no uso de informações clínicas e nas proteções do paciente simulado. Não demonstra melhora linear da entrevista. Desde o legado já existiam perguntas pertinentes sobre cronologia, medicações e fatores de risco. Nas fases seguintes aumentou a conversa, mas também surgiram perguntas para satisfazer barreiras do simulador, repetição de dados desconhecidos e falas que não chegavam ao paciente. Revisão diagnóstica posterior e fidelidade do paciente são dimensões diferentes de qualidade da coleta pelo médico.

A prioridade proposta é tornar a próxima pergunta dependente da resposta anterior, registrar incertezas e confirmar a história antes da conclusão quando a situação permitir. Aumentar apenas o mínimo de turnos pode aumentar conversação sem aumentar informação.

## Cobertura e método

Amostra intencional de 66 traces públicos, em 21 grupos técnicos: quatro primeiros pilotos, quatro encontros do painel legado, fases v1/v2, v3 e variantes de cascata, v3.2c, v3.5, v3.6, v3.7, v4 original/working/fast1–4 e v5z. Foram privilegiados os mesmos casos públicos 001, 002, 004 e 008; pilotos e variantes pequenas têm menos casos. Seleção sem usar acerto como critério. O manifesto contém caminhos e SHA-256.

Esta é uma leitura histórica dirigida das mensagens do médico, com respostas do paciente consultadas como contexto; não uma recodificação clínica cega de todos os encontros. Os quatro pilotos preservam falhas e não entram em denominador de desempenho clínico. O pacote auxiliar retém candidatos de respostas, que devem ser distinguidos das respostas aceitas na v5. Não foram exportados casos fechados.

O inventário operacional anterior de 810 registros históricos não é o denominador desta classificação: inclui repetições, modelos e protocolos diferentes. Tampouco são 810 pacientes independentes. Nem todos os modelos de cada época estão nesta amostra. Os rótulos históricos são nomes de rodadas e protocolos, não uma sequência homogênea de versões do mesmo médico. Não há teste causal de superioridade entre versões.

O grupo v1/v2 é representado pelo GLM-5 da primeira rodada consolidada; não constitui uma comparação separada v1 contra v2. O painel legado é representado pelo GPT-6 Sol. A v3 inicial usa Qwen e as variantes seguintes GLM-5; v4 Sol e Fast também mudam de modelo. Essas diferenças limitam comparações.

## Classificação de qualidade proposta

Manter seis dimensões: **A** abertura e agenda; **C** caracterização e cronologia; **X** contexto, medicamentos e exposições pertinentes; **I** integração da resposta na pergunta seguinte; **R** esclarecimento de ambiguidades e desconhecidos; **S** síntese da história confirmada pelo paciente. Avaliar cada uma como consistente, parcial, frágil ou não avaliável, sempre com evidência textual.

Não somar dimensões em uma nota de 0–100. Esta rubrica é própria, não validada e não equivale ao Revised Safer Dx. Para classificar um encontro inteiro é necessário considerar o que já estava disponível, a urgência e a oportunidade real de perguntar. Uma entrevista breve em emergência pode ser adequada. Uma pergunta não feita não é automaticamente uma falha se a informação já veio no contexto.

A tabela abaixo classifica o **perfil documental observado por fase**, e não atribui um escore retrospectivo a todos os seus encontros.

| Fase | Traces examinados | Perfil observado | Mudança prioritária |
|---|---:|---|---|
| Primeiro piloto exploratório | 1 | Consulta instrumental dirigida: pergunta sobre agente infeccioso e tratamento. Abertura e reparo conversacional não avaliáveis neste formato. | Separar recuperação de dados de habilidade de entrevista. |
| Pilotos abortados v2–v4 do legado | 3 | Fragilidade operacional: no exemplar v2 há 40 chamadas de história, quase todas repetindo a mesma solicitação; outros pilotos fazem perguntas dirigidas. | Detectar repetição sem ganho e distinguir erro de ferramenta de falha clínica. |
| Painel legado | 4 | Coleta estruturada pertinente, com cronologia, contexto e risco; interação humana pouco avaliável por resposta em blocos determinísticos. | Não interpretar retorno de um bloco HPI como habilidade comprovada de explorar o relato. |
| Rodada consolidada v1/v2, GLM-5 | 4 | Parcial: perguntas relevantes e retomadas, mas vários atributos na mesma mensagem e pouca confirmação da história. | Uma questão principal por vez e esclarecimento da resposta incompleta. |
| v3 inicial e N2 | 8 | Parcial, mais extensa: boa abrangência de medicações, contexto e cronologia, porém turnos adicionais frequentemente ligados à liberação de exames. | Medir informação obtida por pergunta; remover incentivo a preencher turnos. |
| Cascatas v1/v2 | 8 | Parcial: perguntas contextuais e mudança de hipótese; revisão posterior não comprova que o médico inicial colheu melhor a história. | Registrar separadamente coleta inicial, resgate pelo revisor e informação realmente nova. |
| v3.2c | 4 | Heterogênea: exploração de contexto em alguns casos; no caso 008 não há mensagem autônoma de história do médico no recorte, embora existam conteúdos junto de ferramentas. | Auditar entrega da pergunta ao paciente. Ausência de mensagem não prova ausência de informação no contexto. |
| v3.5/v3.6 | 8 | Parcial, mais concentrada: medicações e riscos pertinentes; aparecem esperas por respostas a perguntas que estavam em mensagens com ferramentas. | Garantir entrega e resposta antes de cobrar a informação; distinguir espera administrativa de história. |
| v3.7, formato de fala | 2 | Parcial: melhora de apresentação não comprova melhora do conteúdo. Persistem mensagens de espera e blocos extensos. | Avaliar legibilidade e integração clínica separadamente. |
| v4 Sol original/working | 8 | Coleta focal mais enxuta: em vários turnos, duas perguntas simples sobre tempo, sintomas ou medicação. Síntese confirmada não demonstrada nesta leitura dirigida. | Preservar concisão e acrescentar confirmação de lacunas relevantes. |
| v4 Fast1–4 | 12 | Parcial: roteiro legível, perguntas pertinentes; também há falas apenas explicando pedidos e perguntas para satisfazer número de trocas. | Não contar exposição de plano como nova anamnese; condicionar seguimento ao conteúdo da resposta. |
| v5z, casos públicos pareados | 4 | Parcial: respostas com fatos identificados e desconhecidos explícitos tornam a auditoria melhor; ainda há blocos amplos de exposições, respostas sem informação e pouca confirmação da história. | Usar a estrutura de incerteza para decidir quando reformular, buscar outra fonte ou parar. |

## Evidências que mudam a interpretação

1. **O problema de repetição é antigo.** O piloto legado v2 repete a mesma solicitação de características de dor. Isso é sobretudo uma falha de interação com a ferramenta; não deve virar evidência de entrevista clínica longa ou completa.
2. **A v3 aumentou o contato, mas o próprio médico menciona a regra.** Em um caso urgente, escreve que precisa de mais uma troca antes da liberação das investigações. Em outros casos explica que o sistema exige completar a história. Isso mostra um incentivo do ambiente, não demonstra que todas as perguntas adicionais eram necessárias.
3. **Pergunta gerada não é pergunta entregue.** No runner v3, o texto que segue para o paciente é o da saída sem chamadas de ferramenta, depois do ciclo de ferramentas. Conteúdo coexistente com pedidos pode permanecer apenas no histórico do médico. No recorte v3.5/caso 008, a mensagem autônoma espera respostas; é necessário verificar se as perguntas anteriores chegaram ao paciente. O relatório estrutural registra conteúdo com ferramentas separadamente, sem assumir que todo esse conteúdo continha pergunta.
4. **Há evolução útil de forma na v4 Sol.** No caso 004, perguntas sobre alívio após drenagem, retorno da dispneia, resultados anteriores e medicações são divididas entre mensagens curtas. Isso é um padrão mais fácil de responder que blocos com vários domínios, embora ainda não demonstre entrevista completa.
5. **A v5 melhora a rastreabilidade do paciente.** No caso 002, resposta estruturada preserva informação sobre mesalazina e desconhecimento de exposições. A pergunta final ainda agrupa ocupação, hobbies, viagens, animais, insetos, alimentos, medicamentos e químicos; a maior parte volta como desconhecida. O ganho de proteção contra invenção não se converte automaticamente em ganho de coleta.

## O que os PDFs e as transcrições acrescentam

A AHRQ propõe espaço inicial para o relato, seguido de aprofundamento. Para o agente em texto, a adaptação proposta é uma mensagem inicial aberta em situações estáveis, sem impor literalmente 60 segundos. Em emergência, priorizar a informação indispensável e retomar a narrativa quando houver oportunidade. Isso é adaptação nossa ao agente, não protocolo validado de chat. [Toolkit da AHRQ](https://www.ahrq.gov/diagnostic-safety/tools/engaging-patients-improve.html).

Calibrate Dx fundamenta revisão e reflexão sobre decisões; Measure Dx amplia a análise para o sistema. Portanto, uma falha pode nascer da pergunta, da simulação do paciente, da entrega de mensagens, da fila de exames ou do revisor. Acerto final não identifica sozinho qual componente melhorou. [Calibrate Dx](https://www.ahrq.gov/diagnostic-safety/tools/calibrate-dx.html), [Measure Dx](https://www.ahrq.gov/sites/default/files/wysiwyg/patient-safety/MeasureDx-guide.pdf).

O piloto anterior de transcrições humanas compreende três consultas simuladas completas PriMock57 e quatro excertos brasileiros de consultas reais de enfermagem. Não é uma amostra representativa de médicos brasileiros nem validação de um agente. As sequências mostraram localização corrigida pelo paciente, diferença entre sintoma anterior e atual, respostas globais depois qualificadas, tentativas prévias de tratamento e preocupações que reaparecem. O valor para o MIRA está em testar se ele percebe e resolve esses eventos. [PriMock57](https://aclanthology.org/2022.acl-short.65/), [Meneghel e colaboradoras](https://www.scielo.br/j/csc/a/KDhTm7gdNKz7DbYHmwzX8FR/?lang=pt).

## Propostas para a próxima versão, preservando os ganhos anteriores

**1. Garantir que a pergunta chegue ao paciente.** Registrar estados separados: redigida, enviada, respondida e incorporada. Se houver pergunta e ferramenta na mesma saída, o fluxo deve processar ambos explicitamente, sem perder a pergunta. Verificação futura: pergunta enviada uma única vez, resposta atribuída à pergunta certa e nenhuma cobrança por pergunta não enviada.

**2. Abrir espaço para a narrativa em casos estáveis.** Exemplo: “Conte o que aconteceu, desde o começo, e o que mais preocupa você.” Depois selecionar uma lacuna de cada vez. Não aplicar um roteiro longo antes de atender uma situação urgente.

**3. Tratar a resposta como evento clínico.** Para cada dado: valor, momento, fonte e estado — confirmado, negado, desconhecido, não perguntado ou contraditório. “Não sei”, “não consta” e “não” precisam permanecer diferentes. Se o início súbito ou gradual estiver incerto e isso mudar a decisão, reformular; se o registro não permite responder, reconhecer a limitação e buscar outra fonte quando disponível.

**4. Fazer seguimento seletivo.** Perguntar sobre medicação implica explorar início ou mudança quando isso for pertinente; não repetir uma lista inteira de sintomas. Uma pergunta principal por mensagem é uma preferência a testar, com exceção de blocos curtos necessários em urgência.

**5. Confirmar uma síntese curta.** “Entendi que começou após X, evoluiu assim e você usa Y. O que está incorreto ou faltando?” A confirmação deve ocorrer antes da conclusão quando viável; não confundir explicar um diagnóstico com confirmar a história.

**6. Separar qualidade do médico, fidelidade do paciente e contribuição do revisor.** Um acerto resgatado depois não corrige retrospectivamente a nota da coleta inicial. Acrescentar eventos de boa recuperação: contradição percebida, negativa indevida evitada e dado importante recuperado.

## Métricas propostas e denominadores

- **Entrega:** perguntas realmente enviadas / perguntas redigidas e destinadas ao paciente. Excluir texto interno e separar conteúdo com ferramentas.
- **Resposta:** questões pertinentes respondidas ou explicitamente mantidas como desconhecidas / questões pertinentes enviadas; não punir o médico por dado inexistente no caso.
- **Reparo:** ambiguidades relevantes esclarecidas ou justificadamente mantidas / oportunidades de reparo identificadas por revisão.
- **Integração:** pistas relevantes usadas no seguimento / pistas relevantes disponíveis. Exige codificação contextual, não contagem de palavras.
- **Fidelidade da síntese:** dados corretamente preservados e corrigidos / dados verificáveis resumidos; registrar também convite à correção.
- **Eficiência:** informação nova pertinente por troca e turnos sem ganho; separar perguntas de mensagens de plano, urgência e pausas administrativas.
- **Resultados:** julgamento diagnóstico e revisão médica em colunas próprias; não usar como substitutos dos itens anteriores.

Não há medição histórica validada dessas novas métricas. São propostas para uma avaliação futura com protocolo congelado, casos novos, anotação independente e revisão médica. Não foi autorizada nem executada nova rodada neste trabalho.

## Arquivos e rastreabilidade

- `sample_selection.json`: regra de seleção e 66 fontes públicas.
- `public_history_packet.json`: extração auxiliar das ações/mensagens e candidatos de respostas; não é transcrição clínica validada.
- `structural_summary.json`: contagens por grupo, sem nota clínica.
- Auditoria anterior: `../anamnese_quality_v5_2026-10-16/relatorio.md`.
- Piloto de transcrições: `../anamnese_sample_2026-10-16/relatorio.md`.
- Métricas históricas operacionais: `../metrics_history_2026-10-16/relatorio.md`.

Limites: um avaliador IA; amostra pequena e intencional; modelos, simuladores e regras diferentes; perguntas condicionadas por dados já fornecidos; leitura documental não substitui adjudicação médica. Os perfis não demonstram segurança clínica nem superioridade entre versões.
