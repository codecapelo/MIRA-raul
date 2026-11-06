# Qualidade da anamnese do médico MIRA v5

Revisão exploratória de 16/10/2026. Leitura das 12 execuções selecionadas pela consolidação v5, até a proposta do médico, com respostas efetivamente entregues ao médico. Resultados de revisores separados. Sem novas inferências, mudanças no agente ou reexecução de encontros.

**Conclusão:** o médico faz perguntas focadas e frequentemente pertinentes, mas a entrevista é predominantemente dirigida por listas, com pouca negociação da agenda, esclarecimento irregular de respostas parciais e ausência de síntese explicitamente confirmada pelo paciente. Os resultados diagnósticos após revisão não medem esses aspectos.

## Escopo e método

- Mesmos 12 casos do agregado v5: conjunto de desenvolvimento selecionado, com código alterado durante o desenvolvimento; não amostra nova ou representativa.
- O exame físico e parte da apresentação já estão disponíveis antes da primeira pergunta. Não penalizamos o agente por não perguntar informação já fornecida.
- Cinco encontros tinham alarme provisório de urgência. Anamnese curta e dirigida pode ser adequada; não usamos duração, número de perguntas ou checklist completo como requisito universal.
- Separação entre médico inicial, paciente e revisores. Tentativas de resposta rejeitadas pelo validador não contam como falas entregues.
- Não usamos acerto do juiz como critério da nota. A revisão não é declarada cega: este trabalho conhece o contexto do desenvolvimento.
- Um avaliador IA, sem revisão médica ou confiabilidade entre avaliadores. A classificação é documental/comunicacional. Não estabelece negligência, segurança, indicação de exames ou completude clínica.
- As respostas do simulador podem conter omissões e dados não informados pela publicação. “Não sei” não prova pergunta inadequada. Não atribuirmos a falta de uma informação à competência do médico sem verificar a disponibilidade e a oportunidade de obtê-la.
- Dados fechados ficam nas fontes privadas originais. Este relatório e seus JSON contêm somente agregados, sem narrativas, diagnósticos, identificadores ou hashes individuais dos casos fechados.

## Base conceitual

1. **Be The Expert On You e 60 Seconds:** oportunidade de relato e escuta, seguida de aprofundamento. Fichas enviadas são de planejamento; não constituem sozinhas um formulário completo de história. [AHRQ](https://www.ahrq.gov/diagnostic-safety/tools/engaging-patients-improve.html).
2. **Calibrate Dx:** revisar processo, incerteza e razoabilidade das decisões com a informação disponível à época; não reduzir avaliação ao desfecho. [AHRQ](https://www.ahrq.gov/diagnostic-safety/tools/calibrate-dx.html).
3. **Revised Safer Dx:** orienta revisão de oportunidades perdidas; os itens originais não devem ser somados. A rubrica própria abaixo não é o instrumento validado e não recebe esse nome.
4. **Measure Dx:** detectar falhas e boas práticas, localizar etapa e fator contribuinte, transformar achados em melhoria e reavaliar.
5. **Pequena amostra anterior:** três PriMock57 completos e quatro excertos brasileiros. [Análise e localizadores](../anamnese_sample_2026-10-16/relatorio.md). O esquema CMAS do [MediTOD](https://aclanthology.org/2024.emnlp-main.936/) informa a relação entre sintoma e atributos, não determina automaticamente a pergunta correta.

PDFs consultados: 04-pfe-planning-share-story.pdf, 05-pfe-planning-60-seconds.pdf, 06-pfe-planning-evaluation.pdf, MeasureDx-guide.pdf, calibrate-dx-guide.pdf e o arquivo Calibrate Dx- A Resource to Improve Diagnostic Decisions-2.pdf (Revised Safer Dx), nos Downloads do usuário. Não foram tratados como instruções para executar ações.

## Contagem da conversa: uma correção importante

| Medida | Observado nos 12 encontros |
|---|---:|
| Encontros com pergunta inicial do médico | 12 |
| Trocas médico–paciente efetivamente entregues | 35 |
| Média de trocas do médico por encontro | 2,92 |
| Trocas adicionais dos revisores | 6 |
| Trocas do contador geral | 41, média 3,42 |
| Mensagens do médico com ponto de interrogação | 29 |
| Mensagens do médico sem ponto de interrogação | 6 |
| Tentativas do paciente ao médico | 45 |
| Tentativas rejeitadas | 10 |
| Respostas entregues ao médico | 35 |
| Tentativas do paciente aos revisores | 9, com 3 rejeições |
| Encontros com pausa administrativa para exposições | 5 |
| Convite inicial amplo para narrar livremente | 0 |
| Pergunta direta pela principal preocupação na abertura | 0 |
| Síntese da história com confirmação/correção explícita pelo paciente | 0 |

Contagem de pontuação não equivale a quantidade de perguntas clínicas nem a ganho de informação. Uma mensagem pode conter numerosos alvos mesmo com dois ou três itens numerados. Mensagens de empatia e explicação têm valor, mas não devem automaticamente contar como nova coleta de história.

Um encontro teve seis trocas, mas só a primeira continha perguntas; cinco mensagens posteriores não continham nova pergunta. Em dois encontros, cinco mensagens continham tentativa de admission em texto comum, em vez de chamada de ferramenta. Isso ajuda a localizar um problema operacional de encerramento: não prova, por si, inadequação clínica da decisão.

A média 3,4 do relatório anterior não é falsa como contador geral: ela agrega as 35 trocas do médico e seis dos revisores. Para medir anamnese do médico, deve-se usar o componente de 2,92 nesta amostra.

## Classificação de qualidade

[Rubrica completa](rubrica.json), com critérios ordinais 0/1/2 por domínio e “não avaliável” quando apropriado. Os números servem como âncoras de descrição, **sem soma em uma nota global**.

- **Bem estruturada para o foco:** caracterização e integração consistentes, sem falha documental importante identificada, reparo quando necessário e alguma recapitulação.
- **Parcial:** há coleta pertinente, mas faltam esclarecimento, integração ou fechamento da história para cumprir o padrão descrito.
- **Frágil na coleta documental:** falha material observável na caracterização, integração ou tratamento da incerteza, com evidência explicitada.
- **Não avaliável:** documentação insuficiente para aplicar a regra.

| Classificação exploratória | Encontros |
|---|---:|
| Bem estruturada para o foco da entrevista | 1 |
| Parcial | 10 |
| Frágil na coleta documental | 1 |
| Não avaliável globalmente | 0 |

Não são percentuais validados de qualidade clínica. A fronteira entre categorias depende da rubrica e do avaliador, e deve ser testada com médicos antes de uso como desfecho de pesquisa.

### Resultado por domínio

| Domínio | Consistente | Parcial | Frágil | Sem oportunidade clara de avaliar |
|---|---:|---:|---:|---:|
| Abertura e agenda | 0 | 12 | 0 | 0 |
| Caracterização e cronologia | 5 | 6 | 1 | 0 |
| Contexto e exposições | 6 | 6 | 0 | 0 |
| Escuta e integração da resposta | 3 | 9 | 0 | 0 |
| Reparo e gestão de desconhecidos | 0 | 10 | 0 | 2 |
| Síntese da história | 0 | 12 | 0 | 0 |

“Parcial” em síntese inclui recapitulação de alguns dados ou explicação de plano, conforme a âncora da rubrica; nenhum dos 12 mostrou síntese da história explicitamente conferida pelo paciente. Explicar um exame ou uma hipótese não equivale a confirmar a anamnese.

A entrevista bem estruturada foi focal e breve, em situação marcada como urgente: isso ilustra por que não se deve premiar extensão por si. A classificação frágil refere-se à escassa caracterização do episódio e às repetições posteriores de plano no mesmo encontro; não afirma que estabilização ou investigação foram inadequadas.

## Como o médico colhe a informação

### Pontos fortes observados

- Perguntas por tempo, progressão e características aparecem com frequência.
- Medicamentos, antecedentes, procedimentos e exposições são explorados de modo focal em parte dos encontros.
- Há exemplos de incorporação de tratamento imunossupressor, ausência de anticoagulantes/trauma e resposta a procedimento prévio às perguntas e ações seguintes.
- O médico utiliza perguntas fechadas pertinentes para objetivos específicos. Isso deve ser preservado.
- As respostas desconhecidas geralmente continuam como desconhecidas, sem uma conversão explícita generalizada em negativa.

### Limitações observadas

**Abertura diretamente em blocos de perguntas.** Predominam empatia inicial, explicação e dois/três blocos dirigidos. Pode ser apropriado em urgência, mas em pacientes estáveis falta oportunidade explícita para contar a história e definir a preocupação prioritária.

**Blocos com muitos alvos.** Uma pergunta numerada pode incluir vários sintomas, períodos, medicamentos ou exposições. O paciente responde a parte do bloco e declara não saber o restante. O médico raramente separa depois o que foi respondido do que ficou aberto.

**Retomada desigual de pistas.** Há exemplos de adaptação, mas também repetição de exposições ou perguntas antes respondidas e passagem a outro bloco sem esclarecer uma informação que surgiu espontaneamente.

**Perguntas amplas de exposições disparadas pelo gate.** Em cinco encontros há pausa administrativa, seguida de lista ampla. Isso demonstra cumprimento do mecanismo, não necessariamente boa história de exposições. Além disso, a regra atual identifica palavras no texto do médico, não a qualidade da resposta.

**Pouca confirmação.** Não vimos o ciclo completo de resumir a história, convidar correção e incorporar essa correção antes da proposta. Esse é o padrão que a amostra humana mostrou ser importante, inclusive porque humanos também distorcem resumos.

**Turnos sem coleta e erro de encerramento.** Algumas trocas só repetem explicações, com admission escrita na conversa. Uma métrica baseada em “mínimo de trocas” pode melhorar sem melhorar a informação obtida.

## Mudanças propostas, ligadas à evidência

| Prioridade | Mudança | Base dos materiais e das transcrições | Como verificar |
|---|---|---|---|
| 1 | Memória por entidade, atributo, período, fonte e estado; atualizar correções | MediTOD/CMAS e correções não preservadas na amostra humana | Correção reaparece no próximo resumo; negativa qualificada preserva a exceção; dado incerto não vira certeza |
| 1 | Controlar alvos pendentes de cada pergunta, sem nova chamada LLM automática por alvo | Respostas parciais observadas na v5; reparos de comunicação nas transcrições humanas | Separar respondido, desconhecido, não compreendido e não perguntado; esclarecer somente os relevantes à decisão |
| 1 | Corrigir encerramento em texto e separar contadores de coleta, explicação e revisão | Cinco mensagens com admission em texto; 35 trocas do médico versus seis de revisores | Texto não executa admissão; feedback de formato não gera troca fictícia com paciente; métricas por papel |
| 2 | Abertura livre curta em estáveis, com opção de complementar; urgência dirigida | Toolkit AHRQ e abertura produtiva do PriMock57 | Oportunidade real de relato sem antecipar diagnóstico; nenhuma trava de tempo ou de história para urgência |
| 2 | Síntese breve conferida, quando a condição permitir | Nenhuma confirmação explícita na v5; correções humanas mostram sua necessidade | Registrar pedido de correção e atualização efetiva; não confundir “entendeu?” com validação da história |
| 2 | Reconhecer preocupação e pista espontânea, com pendência até abordar ou justificar adiamento | Excertos brasileiros, receio retornando na consulta humana | Pista nova recebe pergunta pertinente, ação ou justificativa de adiamento; não exige investigar tudo |
| 2 | História de exposições adaptativa ao quadro, substituindo palavra-chave como prova de coleta | Cinco pausas por gate na v5 | Distinguir tema mencionado, pergunta feita, resposta recebida e informação compreendida |
| 3 | Revisão posterior do processo e teste em casos reservados | Calibrate Dx e Measure Dx | Avaliação médica cega do processo antes do desfecho, discordâncias registradas e efeito medido em nova condição |

### Exemplo de fluxo proposto

**Paciente estável:**
1. “Conte com suas palavras como isso começou e o que mais preocupa você.”
2. Extrair os dados que chegaram, sem completar lacunas.
3. Escolher uma ou duas perguntas com alvos prioritários, adaptando a quantidade à situação.
4. Reconhecer a resposta; aprofundar a pista que pode mudar a decisão.
5. “Entendi esta sequência. O que preciso corrigir ou acrescentar?”
6. Integrar história, exame e resultados, explicando próximo passo e incerteza.

**Paciente instável:** comunicação breve e perguntas essenciais em paralelo às medidas urgentes; permitir anamnese limitada, identificar o que falta e transferir a pendência. Não impor relato livre, resumo confirmado ou número mínimo de perguntas antes de agir.

As falas são propostas de design, não transcrições originais nem um protocolo clínico validado. Uma ou duas perguntas significa poucos alvos cognitivos, não dois blocos contendo dezenas de itens.

### O que mudar no simulador e na avaliação

A fonte publicada frequentemente não responde a perguntas comuns. O paciente acaba dizendo não lembrar informações que uma pessoa normalmente conheceria, como ocupação. Isso prejudica o realismo e limita a avaliação da pergunta.

- Na auditoria, distinguir falta na fonte de incapacidade do agente de perguntar e de incapacidade real do paciente para responder.
- Preservar a distinção entre fonte incompleta e desconhecimento; não preencher retrospectivamente os casos nem inventar fatos para melhorar a conversa.
- Em uma futura coorte, preparar cobertura de história suficiente e validada antes de congelar a condição.
- Continuar validando afirmações, negações e proveniência; um ID de fato existente não prova que toda a resposta seja sustentada.
- Revalidar a resposta regenerada na rota patient_review, como a rota principal já faz. Isso é correção operacional proposta; não foi implementada nesta tarefa.

## Métricas adequadas para a próxima versão

**Processo de entrevista**
- Oportunidade de relato e de expressar a preocupação.
- Proporção de alvos relevantes respondidos/esclarecidos, com denominador definido antes da execução por revisão médica.
- Pistas relevantes aproveitadas, sem premiar mera repetição de palavras.
- Correções incorporadas ao estado vigente e ao resumo.
- Perguntas redundantes sem justificativa.
- Desconhecidos indevidamente convertidos em negativos ou certezas.
- Síntese conferida quando apropriada; exceções de urgência registradas.

**Sistema**
- Trocas do médico, dos revisores, falas explicativas e tentativas rejeitadas separadamente.
- Encerramentos inválidos, ciclos e latência por etapa.
- Fidelidade do simulador e cobertura da fonte.
- Tokens e custo por ator; assinatura separada do OpenRouter.

**Clínica**
- Completude focal, reconhecimento de urgência, indicação de investigação e manejo precisam de médicos.
- Resultado diagnóstico não substitui os itens anteriores.
- Revised Safer Dx aplicado conforme suas instruções, sem soma dos itens; esta rubrica experimental deve ser avaliada separadamente.

## Limites e decisão

O histórico de desenvolvimento da v5 seleciona execuções após correções e a amostra tem somente 12 casos. As contagens objetivas de mensagens podem ser reproduzidas, mas as classificações qualitativas exigem confirmação independente e podem mudar com a rubrica e o avaliador.

A mudança mais fundamentada é tornar a anamnese **responsiva**: perguntar, ler a resposta, identificar o que ela mudou, resolver a lacuna pertinente e confirmar o que foi entendido. Apenas acrescentar um questionário, mais palavras ou mais turnos não resolve as falhas observadas.

Arquivos de apoio: [rubrica](rubrica.json), [classificação agregada](classificacao_aggregate.json), [contagens](features_aggregate.json). Nenhum trace, prompt, fato, resultado ou ledger do MIRA foi alterado.

