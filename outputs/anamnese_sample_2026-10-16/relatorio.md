# MIRA v5 — pequena amostra de anamneses e propostas de melhoria

Data de referência do usuário: 16/10/2026. Análise exploratória; revisão médica pendente.

**Achado central:** a oportunidade mais concreta é fazer a informação obtida sobreviver corretamente às próximas etapas. Na amostra há relatos produtivos com perguntas abertas, mas também correções que não permanecem no resumo, negativas acompanhadas de exceções e respostas incertas consolidadas sem esclarecimento. Aumentar a quantidade de perguntas ou o tamanho das respostas não resolve esses problemas por si.

## O que foi realmente analisado

- **Três consultas simuladas completas do PriMock57:** as três primeiras consultas numeradas do dia 1, selecionadas consecutivamente, sem seleção por resultado. Ambos os interlocutores foram lidos na íntegra.
- **Quatro excertos reais em português**, números 3, 4, 5 e 7 do artigo de Meneghel e colaboradoras, selecionados intencionalmente por apresentarem revelação hesitante, sintoma pouco esclarecido, sintoma adicional e pista psicossocial.
- **28 sequências comentadas:** oito em cada consulta completa e uma em cada excerto. Isso é uma anotação qualitativa focal após leitura integral das três transcrições, não codificação exaustiva de toda pergunta.
- **MediTOD:** esquema CMAS consultado como referência de representação; nenhum encontro adicional do MediTOD foi contado na amostra.
- **MIRA v5:** leitura do código no checkout de commit 9ccc23eb88774e9277caa1752cfb7bb6e28222ae. Não foi executado novo encontro, alterado prompt ou modificado ledger.

As três consultas somam aproximadamente **25 minutos e 55 segundos**, pelo fim dos últimos intervalos. O material contém 380 intervalos com texto, incluindo respostas de acompanhamento e sobreposições. Intervalos TextGrid não são turnos clínicos, perguntas ou decisões. Não foi ouvido áudio; as marcas de incerteza do transcritor foram preservadas.

Não são sete consultas completas independentes. O grupo brasileiro contém excertos do mesmo estudo, não um corpus completo disponibilizado. Este relatório não estima prevalência de falhas, acurácia diagnóstica, segurança clínica nem eficácia das propostas.

## Navegação por caso

| Unidade | Tema | Leitura e localizadores |
|---|---|---|
| P1 | Diarreia e dor abdominal | [Nota individual](casos/P1.md); 109 intervalos |
| P2 | Prurido e distribuição de lesões | [Nota individual](casos/P2.md); 130 intervalos |
| P3 | Cefaleia, fenômenos visuais e preocupação | [Nota individual](casos/P3.md); 141 intervalos |
| B01–B04 | Excertos reais de enfermagem em português | [Nota contextual](casos/BR_excertos.md) |

[Anotações estruturadas](annotations.json) · [Manifesto e hashes](source_manifest.json) · [Estatísticas descritivas](descriptive_stats.json)

## O que a leitura acrescentou à proposta inicial

### 1. A correção do paciente precisa modificar o estado vigente

Na consulta P2, o médico inclui pernas ao resumir a distribuição; o paciente restringe a localização a peito, mãos e região interna dos cotovelos. Mais tarde, a explicação cita costas, não sustentadas pelo relato legível. Na mesma consulta, a duração de três dias é corrigida para quatro.

Localizadores: **A12 e A14**, especialmente P2-T041–043, P2-T049–051 e P2-T101.

Isso mostra por que simplesmente inserir uma etapa de resumo é insuficiente: o resumo também pode adicionar ou modificar informações. O sistema precisa guardar a correção e impedir que a versão antiga reapareça como fato. A observação é restrita à transcrição; não atribui intenção nem prova o que foi visto no exame.

### 2. Negativa geral e exceção precisam coexistir

Na consulta P1, ao negar contatos com sintomas iguais, o paciente relata uma criança com vômitos sem diarreia. A representação útil preserva o contato parcialmente sintomático e o alcance da negativa. Na P3, a paciente diz não ter hábito de cefaleia, mas conta episódio semelhante semanas antes.

Localizadores: **A07 e A21**, P1-T045–046 e P3-T047–061.

A proposta é decompor essas respostas: quem, qual sintoma, qual período e com que certeza. Não se deve converter isso automaticamente nem em contradição nem em um único negativo global.

### 3. A resposta incerta é uma informação válida, mas pode deixar uma pendência

Na P3, a paciente não consegue dizer se a cefaleia começou de modo súbito ou gradual. A conversa segue para a qualidade da dor. A falta de esclarecimento é observável; sua consequência clínica depende de revisão médica.

Localizador: **A18**, P3-T016–018.

O agente deve manter “início incerto” e, se esse dado puder mudar a urgência ou o próximo passo, reformular a pergunta de forma concreta. Se continuar desconhecido, preservar a lacuna e decidir em função dessa incerteza.

### 4. Pistas podem surgir fora da pergunta prevista

Na P2, a falta de resposta a anti-histamínicos é informada depois de sua menção no plano; na P3, o receio de tumor retorna ao longo da conversa. Os excertos brasileiros mostram como a linguagem hesitante e os acréscimos espontâneos também exigem atenção.

Localizadores: **A16, A19 e B01–B04**.

A proposta é manter uma lista curta de pistas e preocupações ainda não resolvidas. Cada uma deve receber uma ação pertinente ou uma justificativa explícita para adiamento. Não é obrigatório investigar tudo na mesma consulta, nem presumir que uma pista identifica sua causa.

### 5. Reparar a comunicação faz parte da anamnese

Na P2, perguntas sobre face e alergias precisam ser repetidas. Na P3, há uma expressão estranha no texto e resposta visual pouco clara; não podemos concluir se a origem é erro de transcrição, audição ou fala.

Localizadores: **A15 e A20**.

O MIRA deve diferenciar “negado”, “não compreendido” e “transcrição incerta”. Um resultado importante com compreensão duvidosa precisa de confirmação, em vez de normalização silenciosa.

### 6. O relato livre funciona em combinação com perguntas dirigidas

Na P3, o convite para contar mais traz informações sobre alterações visuais. Na P1, o esclarecimento de termos e as perguntas focalizadas obtêm características concretas; perguntas fechadas na P3 registram negativos específicos.

Localizadores: **A01–A06, A17 e A22**.

A proposta é abertura livre breve, convite para complementar quando pertinente e aprofundamento dirigido. Não há fundamento nesta amostra para eliminar perguntas fechadas ou impor duração fixa.

## Propostas de implementação

Os identificadores M1–M6 relacionam-se às anotações. A ordem abaixo expressa prioridade de implementação proposta, não gravidade clínica validada.

| Proposta | Mudança concreta | Critério de aceitação proposto |
|---|---|---|
| **M2 — memória clínica com proveniência e correções** | Guardar entidade, atributo, valor, período, fonte, estado e histórico de correções. Fatos e interpretações separados. Correção atualiza a visão vigente, preservando versões anteriores. | Uma correção de localização ou tempo aparece nos resumos seguintes; região não sustentada não entra como relato confirmado; sintomas prévios resolvidos não desaparecem. |
| **M4 — reparo de comunicação** | Estados para não compreendido e transcrição incerta; reformulação simples; suporte à linguagem coloquial e a relato hesitante. | Resposta duvidosa não vira negativa; campo crítico incerto recebe tentativa de esclarecimento ou justificativa de conduta. |
| **M5 — fechamento conferido e compreensível** | Produzir resumo a partir da visão vigente; pedir correção focal; retomar a preocupação principal; comunicar próximo passo e incerteza. Checagem de compreensão pelo paciente em linguagem própria quando apropriado. | Resumo não contradiz correção; preocupação recebe resposta ou pendência explícita; ação futura não é descrita como já executada. |
| **M3 — fila de lacunas e perguntas com propósito** | Registrar pista, motivo para esclarecer, risco de adiamento e próxima pergunta. Red flags podem interromper a ordem usual; respostas reaproveitadas evitam repetição. | Nova pergunta tem alvo claro; dados tardios pertinentes reabrem a avaliação; tópicos já respondidos não são repetidos sem motivo. |
| **M1 — abertura adaptativa** | Uma abertura livre e aprofundamento aberto quando produtivo, seguidos de perguntas dirigidas. Urgência permite fluxo abreviado. | O agente não pressupõe diagnóstico na abertura; não exige um minuto nem um número rígido de trocas antes de agir. |
| **M6 — revisão breve da hipótese e da incerteza** | Antes de concluir, registrar hipótese, suporte, dado que não encaixa, lacuna relevante e razão para investigar mais, pedir ajuda ou concluir a etapa. | Incerteza clinicamente relevante não é apagada pela linguagem do fechamento; diagnóstico anterior não substitui avaliação das diferenças atuais. |

### Exemplo da memória proposta

Uma resposta que nega contatos “iguais” e informa criança com vômitos seria decomposta em:

- Contato domiciliar: criança.
- Vômitos no contato: presentes por relato.
- Diarreia no contato: negada por relato.
- Conjunto de sintomas idêntico ao do paciente: negado.
- Relação causal com o episódio: não estabelecida.

Esse exemplo é uma adaptação analítica de A07, não a saída atual do MIRA. O esquema CMAS do [MediTOD](https://aclanthology.org/2024.emnlp-main.936/) inspira a ligação entre atributos e sintomas; os estados de correção, contradição, compreensão e proveniência são extensões propostas aqui.

### Aplicação ao simulador e ao médico deve ser separada

**Médico:** só pode construir sua memória a partir do que recebeu durante o encontro. Não acessa os fatos ocultos do simulador nem o diagnóstico de referência.

**Simulador:** pode validar a resposta contra os fatos autorizados para a etapa e para o conhecimento do paciente. Uma abertura livre não deve descarregar todos os fatos, nem revelar exames futuros, nem impedir o paciente de expressar preocupações que estejam explicitamente autorizadas no caso.

**Auditoria:** depois do encontro, comparar perguntas, respostas, memória, resumo e decisões. A referência diagnóstica permanece fora da condução.

## Ajustes técnicos da v5 que precisam acompanhar a proposta

Constatações por leitura do código, separadas dos achados da amostra:

1. **A guarda de exposições detecta palavras na fala do médico.** Isso registra que o tema foi mencionado, não que foi perguntado, respondido ou compreendido. Proposta: acompanhar o estado de cada informação relevante; permitir desconhecido ou não aplicável, com urgência sem bloqueio indevido.
2. **A checagem de omissões usa compartilhamento de palavras.** Ela não demonstra compreensão semântica. Proposta: em desenvolvimento, avaliar paráfrases, respostas parciais e vínculos entre afirmações e fontes; não substituir o mecanismo por outro juiz LLM sem medir seus erros.
3. **IDs válidos não provam suporte a toda afirmação.** Proposta: validação por afirmação, especialmente para negações, tempos e localizações, com avaliação humana de uma amostra.
4. **Na rota patient_review, a resposta regenerada não passa novamente por validate naquele trecho.** Proposta: aplicar à segunda resposta a mesma validação e um limite explícito, registrando falha sem inventar fatos. A rota principal de resposta do paciente em runner_v3 já tem laço de validação de duas tentativas; a lacuna não deve ser generalizada a todo o paciente v5.

Arquivos inspecionados no checkout v5:
- src/mira_runner/patient_v5.py, especialmente STRICT_RULES, questions_only, relevant_unused e validate.
- src/mira_runner/v5.py, especialmente note_doctor_text e admission_blocked.
- src/mira_runner/runner_v3.py, v5_patient_turn.
- scripts/run_v5.py, V5Client.call no papel patient_review.

## O que eu não priorizaria com esta evidência

- **Aumentar imediatamente o limite de 80 palavras.** Os maiores intervalos isolados do paciente têm 44, 70 e 36 palavras, após remoção de tags. Intervalos não são turnos completos, portanto isso não prova adequação do limite; tampouco demonstra necessidade de aumentá-lo. A limitação continua sendo hipótese a testar.
- **Impor 60 segundos de narrativa no chat ou no simulador.** Tempo de áudio não equivale a número de palavras, tokens ou trocas. A amostra sustenta abertura adaptativa, sem limiar fixo demonstrado.
- **Adicionar perguntas universais longas ou novo revisor a toda fala.** Pode aumentar custo e redundância. Priorizar memória, verificações locais e perguntas relacionadas à decisão; medir antes de adicionar inferência.
- **Aprender automaticamente com todo diálogo humano como se fosse padrão-ouro.** As próprias transcrições contêm reparos, ambiguidades e oportunidades de melhoria.

## Como avaliar depois, sem misturar com o histórico

1. Fixar uma nova condição experimental e suas regras antes de executar novos encontros; manter v5 histórica e terminais existentes intactos.
2. Usar esta amostra apenas em desenvolvimento. Casos reservados para avaliação devem ser independentes, incluindo controle de duplicação entre Fareez e MediTOD.
3. Começar com verificações locais de correção, negação qualificada, cronologia, resposta incerta e comunicação falha. Cenários derivados desta amostra são testes de desenvolvimento, não validação independente.
4. Avaliar a conversa e o diagnóstico separadamente, com revisão médica cega e registro das discordâncias.
5. Medir: afirmações sem suporte; correções preservadas; negativos indevidos; pendências relevantes resolvidas; perguntas redundantes; adequação de urgência e investigação; resultado diagnóstico; tempo, tokens e custo por ator.
6. Comparar incrementalmente: v5 de referência, depois memória/reparos, depois política de perguntas. Repetições, modelos, orçamento e novos encontros exigem autorização e protocolo próprios; nada foi lançado nesta análise.

Não há estimativa de ganho percentual. A amostra permite formular hipóteses específicas e critérios verificáveis; não demonstra superioridade clínica.

## Fontes e preservação

- Papadopoulos Korfiatis A, Moramarco F, Sarac R, Savkov A. [PriMock57: A Dataset Of Primary Care Mock Consultations](https://aclanthology.org/2022.acl-short.65/). ACL, 2022. [Dados originais](https://github.com/babylonhealth/primock57). CC BY 4.0; licença preservada em sources/primock57/LICENSE.md. As seis transcrições originais foram preservadas, com Git blob SHA e SHA-256 no manifesto. Os JSON derivados ordenam intervalos por início e mantêm tags e sobreposições.
- Meneghel SN, Andrade DNP, Hesler LZ. [Conversas invisíveis: assuntos falados, mas não ouvidos em consultas ginecológicas](https://www.scielo.br/j/csc/a/KDhTm7gdNKz7DbYHmwzX8FR/?lang=pt). Ciência & Saúde Coletiva, fascículo de 2021. Excertos 3, 4, 5 e 7, em paráfrases, sem reprodução integral do artigo.
- Saley VV et al. [MediTOD: An English Dialogue Dataset for Medical History Taking with Comprehensive Annotations](https://aclanthology.org/2024.emnlp-main.936/). EMNLP, 2024. Referência de esquema, não amostra adicional.

Uma revisão por IA, não cega e sem audição do áudio ou exame dos pacientes. As sugestões de perguntas são propostas de design, não protocolos clínicos validados. Relatório e dados foram criados apenas em outputs/anamnese_sample_2026-10-16; sem commit, publicação ou alteração da execução do MIRA.

