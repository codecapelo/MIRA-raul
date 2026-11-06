# Auditoria fast4 — públicos003–010

Leitura dos oito terminais públicos, commit registrado b3d7d00. O010 só foi examinado após case_complete. Nenhuma inferência, alteração de código/HEAD, referência diagnóstica ou conteúdo fechado foi acessado. Comparação contra patient.json e investigations.json públicos autorizados; não houve nova extração independente dos artigos originais. Revisão médica pendente.

**Integridade confirmada:** 24 inputs de revisão reconstruídos exatamente, com hashes de texto e sistema válidos. Os 30 outputs brutos de follow-up têm SHA válido, parsing de findings igual ao registrado e bytes preservados no Astra. Os 35 achados são valores integrais ou componentes literais das fontes; nenhum número novo identificado. Proposta/admissão/default_admission, resposta diagnóstica de revisores anteriores, referência e juiz não entram na whitelist. Isso não elimina sugestão por perguntas/exames nem fatos sem fonte nas falas do paciente.

|Caso|Fontes únicas / unidades|Médico / revisor|Indisponíveis|Duplicados do contador|Confiança final declarada|
|---|---:|---:|---:|---:|---:|
|003|4 / 22|7 / 15|3|0|0.86|
|004|5 / 31|6 / 25|5|4|0.96|
|005|3 / 21|6 / 15|14|0|0.96|
|006|4 / 30|10 / 20|7|2|0.88|
|007|4 / 12|12 / 0|9|0|0.9|
|008|4 / 22|16 / 6|3|2|0.96|
|009|3 / 21|6 / 15|4|1|0.99|
|010|4 / 36|6 / 30|1|0|0.9|

Somam 31 fontes cobradas, 195 unidades artificiais (69 médico / 126 revisor), 46 itens indisponíveis, 9 duplicados e 3 retornos de pré-requisito. Todas as fontes cobradas são únicas por caso; as somas conferem. Duplicados incluem componentes da mesma fonte, não apenas pedidos clínicos repetidos. Unidades não são dólares ou preços clínicos validados. A classificação atribui cirurgia espinal 5 mas laparotomia 15; a assimetria do catálogo ainda impede interpretar custo como valor econômico real.

**Desvios confirmados mais relevantes:**

- 004: histopatologia de aspirado mediastinal exige erroneamente toracocentese após EBUS já obtido. Foram três bloqueios idênticos, uma toracocentese executada e uma repetição sem nova cobrança (trace110). O diagnóstico oncológico veio do EBUS literal. Fragmentos de fluido do primeiro procedimento perderam a marca “registro prévio” (60/85), permitindo confusão com a nova amostra.
- 006: cosyntropin foi marcado já realizado por cortisol/ACTH basal (79). O Astra reconhece ausência de teste dinâmico; a ferramenta ainda comunica identidade errada. CT-guided biopsy indisponível seguida de histopatologia entrega biópsia documentada como US-guided (94).
- 008: MRI em paciente com paraplegia/incontinência foi bloqueada pela história (14), depois adiada por custo (27), e entregue após hemograma (47). O atraso operacional está demonstrado; dano clínico não foi medido. Pedido whole-spine entrega somente fonte cervicotorácica; repetição com contraste não prova aquisição contrastada. Astra reconhece esse limite.
- 005: HRCT recebe CT pós-contraste (86); toracoscopia indisponível seguida de histologia entrega biópsia CT-guided. PET/CT whole-body permanece indisponível sem inventar estágio. Três testes microbiológicos em fila foram liberados na rodada seguinte, todos indisponíveis e sem custo (54/72): entrega real da fila foi exercitada uma vez.
- 009: ausência de retirada/troca do stent foi afirmada pelo paciente sem história de seguimento na fonte (60) e usada no raciocínio final. Meckel/perfuração, em contraste, chegaram literalmente na laparotomia (69). CT não informa ponto de transição e isso permanece explicitamente incerto no final.

**Evidência exata do009:** paciente, trace60: “No, it was not removed or exchanged after that procedure a year ago. I don't know anything else about it.” A fonte pmh_003 só registra “ERCP for choledocholithiasis one year earlier, with 10F × 10 cm plastic biliary stent left after stone extraction.” O Astra, trace76, reutilizou a afirmação: “The plastic biliary stent placed one year earlier was never removed or exchanged, strongly supporting delayed distal migration as the causal mechanism.” A laparotomia no69, entretanto, documenta independentemente o stent em divertículo de Meckel e a perfuração ileal. O desvio de história não transforma o achado operatório literal em invenção.

**Paciente:** identifiquei 20 grupos conservadores de afirmações sem fonte em 12 respostas de 7 casos. Exemplos:006 sem medicamentos/suplementos ou novos desejos por sal;007 sem prurido/confusão/edema/dispneia em repouso;008 sem parestesias, infecção ou viagem;009 sem febre/vômitos/tontura e sem retirada do stent;010 sem medicamentos regulares ou episódio semelhante. Não são fatos contraditos por valores conhecidos, mas desconhecidos convertidos em negativos.003 preservou os desconhecidos examinados. Lista com linhas e critério está noJSON; não é uma taxa exaustiva de todas as possíveis alucinações.

**Cronologia e incerteza:** não encontrei retorno de observação marcada day_N/followup/retrospective nesses oito casos. Laparoscopia antecedeu patologia no010 (55); tempo de cirurgia/laudo permanece comprimido. Procedimentos do003/004/005/006/008/009 vieram como fatos do caso, sem validar duração ou execução médica real. No005 o exame dermatológico/ocular já estava na apresentação por available_at=time_zero, antes da investigação tumoral; origem dessa classificação exige conferência independente. Os revisores finais preservaram várias distinções entre síndrome confirmada, causa provável, exame indisponível e resultado negativo. Confiança até 0,99 é autodeclarada e não calibrada.

**Piloto001–002 por referência, fora destes contadores:** [auditoria piloto](/private/tmp/v4_fast4_fidelity_pilot.md), [evidências piloto](/private/tmp/v4_fast4_fidelity_pilot.json). O piloto já havia documentado cinco afirmações do paciente sem fonte, troca troponinaI→T, EP posterior comprimido, emergência bloqueada por história e reparo da exclusão de propostas. Não foi recontado ou reexecutado aqui. As cinco afirmações individuais do piloto e os 20 grupos deste relatório têm unidades de contagem distintas e não devem ser somados como 25 alucinações equivalentes.

8/8 aceitos pelo juiz e os 2/2 do piloto não estabelecem segurança clínica, justificativa de exames, acurácia independente ou generalização. O próximo reparo deve corrigir identidade/procedimento/timing e fatos desconhecidos sem adaptar diagnóstico ao gabarito. Nenhum dado fechado foi usado nesta auditoria.

Evidências e hashes: [JSON](/private/tmp/v4_fast4_fidelity_remaining_public.json).
