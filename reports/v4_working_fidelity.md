# MIRA v4 — auditoria factual final da candidata working_final_blind

**10/10 terminais únicos; juiz 10/10 e propostas iniciais 9/10.** Exclusivamente os encontros novos de `runs/v4/sol_working/run1`, todos no commit `2fac24e75d9ab01c2e52ab0a3409ff1434b3ee6c`. Não misturar com rodada original 9/10 ou revisão offline 10/10. Nenhum escore alterado. Sem inferência clínica/API extra, edição de código/HEAD/input, credenciais ou casos privados.

## Evidência e contabilidade

**45 achados em outputs salvos:**43 via tool do médico e 2 via seguimento do revisor. Destes, 44 são valores/substrings contíguas exatas; um combina PT 12 s e INR 1.0 literais por ponto e vírgula, sem alterar número/unidade. Eles cobrem **39 fontes distintas com output salvo**; terminais cobram 41 fontes. As duas fontes adicionais são CT e microbiologia do 004, com evidência de execução/custo e fala médica, mas sem output final persistido. Elas permanecem segregadas como fallback narrativo/custo; não são promovidas à métrica literal.

Trinta falas do paciente comparadas com patient.json. Não identifiquei fato clínico novo claramente inventado nas falas lidas; informações ausentes ficam desconhecidas, às vezes em linguagem de memória ou de leitor de registro. Isso é observação qualitativa destes traces, não garantia geral. Sete eventos reapresentados 002 (seis tool e um followup) excluídos de ocorrências novas.

| Caso | Juiz/proposta | Confiança autorreferida | Falas | Achados com fonte | Fontes com output/cobradas | Unidades | OpenRouter US$ |
|---|---|---:|---:|---:|---:|---:|---:|
| 001 | T/T | 0.93 | 2 | 4 | 4/4 | 26 | 0.01685575 |
| 002 | T/F | 0.72 | 3 | 5 | 5/5 | 27 | 0.01281250 |
| 003 | T/T | 0.78 | 2 | 4 | 4/4 | 22 | 0.01274250 |
| 004 | T/T | 0.93 | 4 | 6 | 4/6 | 36 | 0.01447600 |
| 005 | T/T | 0.96 | 3 | 3 | 3/3 | 21 | 0.01040850 |
| 006 | T/T | 0.97 | 5 | 5 | 5/5 | 35 | 0.00951100 |
| 007 | T/T | 0.92 | 4 | 7 | 4/4 | 12 | 0.006412 |
| 008 | T/T | 0.93 | 2 | 4 | 3/3 | 17 | 0.008448 |
| 009 | T/T | 0.99 | 2 | 2 | 2/2 | 20 | 0.00948975 |
| 010 | T/T | 0.99 | 3 | 5 | 5/5 | 41 | 0.01399825 |

Contabilidade canônica: **41 fontes,257 unidades relativas artificiais; US$ 0.11515425 OpenRouter total**, sendo US$ 0.03127225 implantação sem paciente/juiz. Custos/unidades vêm de case_complete, não da soma de eventos exam_cost reapresentáveis. Sem reconciliação de conta/ledger nesta auditoria; custo monetário assinatura desconhecido.

## Revisão por caso

### Caso 001

Duas falas apoiam antibióticos IV; identidade, alergias e exposições ficam desconhecidas. Não identifiquei novo fato clínico inventado.

Revisor separa infecção do stent como hipótese provável de bacteremia, ruptura do stent, pseudoaneurisma e tamponamento confirmados. Não confirma infarto, pericardite purulenta, comunicação/ruptura do pseudoaneurisma, bacteremia persistente ou endocardite concomitante. Testes indisponíveis permanecem desconhecidos, não negativos.

- **amostra_historica** (L9): Pedido Repeat blood cultures recebe bacteremia MRSA já documentada, com horário de coleta/sensibilidade desconhecidos. Não demonstra nova cultura ou persistência.
- **pre_requisito_observado** (L16, L19, L26): Angiografia bloqueada antes da pericardiocentese; liberada após ela, com texto after emergency pericardiocentesis preservado.
- **resolver_redundante** (L69): Cultura de tecido coronário/stent exige Pericardiocentesis or Cardiac device surgical exploration; resolver repete pericardiocentese já feita duas vezes e mantém cultura bloqueada. Não demonstra amostra de tecido coronário coletada.
- **interacao_emergencia** (L34, L36): Primeira admissão bloqueada antes da conversa; uma fala do paciente obtida depois dos exames.

### Caso 002

Três falas apoiam infecção respiratória antecedente, edema/dor abdominal, mesalazina para colite. Data/dose da mesalazina, síncope, ritmo prévio e outras exposições permanecem desconhecidos. Não identifiquei novo fato clínico inventado.

Hipótese final myocarditis atrial-predominante provável/postinfecciosa, confiança0.72 autorreferida. Histologia, subtipo, patógeno, causalidade mesalazina, cronicidade e mecanismo das alterações direitas ficam não confirmados; fibrose prévia é alternativa. O favorecimento pós-infeccioso é inferência de trabalho, não dado etiológico estabelecido.

- **analyte_incompatibility** (L15, L45): Pedido Cardiac troponin I recebe high-sensitivity troponin T 31 ng/L. Valores e identidadeT são literais, mas I e T são ensaios/análitos distintos; a equivalência do pedido não é estabelecida. Revisor usa troponin T corretamente em sua narrativa.
- **liberacao_temporal** (L25, L51): Estudo eletrofisiológico disponível em followup liberado no turno3; texto Subsequent study preservado. Final usa os achados elétricos como confirmados sem discutir que eram de seguimento. Blindagem final não corrige a cronologia herdada.
- **prefixo_reapresentado** (L43, L45, L47, L49, L51, L52, L55): Seis eventos tool e um followup_result repetem exatamente outputs anteriores; custo acumulado reinicia 1→27. Excluídos do número de achados/falas novas; contabilidade usada exclusivamente do terminal.
- **metadado_resgate**: proposal_correct=false ejudge_correct=true, enquanto rescued=false permanece registrado. Reportar esses campos separadamente, sem presumir que rescued contabiliza alteração pelo working_final.

### Caso 003

Duas falas apoiam pouch urinário após retirada da bexiga, interrupção de drenagem na noite anterior e dor/dispneia depois. Data cirúrgica/manipulação e outros detalhes ficam desconhecidos. Não identifiquei novo fato clínico inventado.

Ruptura/leak confirmados porCT e laparotomia; obstrução/sobredistensão iniciadoras apenas prováveis. Revisor oferece alternativa de vazamento já em evolução explicar drenagem reduzida. Não confirma peritonite bacteriana/septic shock; cultura indisponível não tratada como negativa. Não inventa viabilidade/posição/patência ou causa operatória que a fonte não relata.

- **resultado_parcial** (L16): Pedido serum creatinine and electrolytes recebe apenas creatinine1.08mg/dL; só creatinina foi retornada. Não extrapolar sódio ou painel de eletrólitos completo. Final não o extrapola.
- **pre_requisito_temporal** (L16, L32): Lactato pós-laparotomia bloqueado antes de laparotomia e não retornado depois. Nenhum day_N/followup/retrospective liberado neste encontro.
- **juiz_nao_iguala_evidencia**: Juiz chama intraperitoneal urinary leakage de clinical equivalent de secondary intra-abdominal sepsis. Essa equivalência não é demonstrada pelos achados entregues: final separa corretamente evidência de ruptura/vazamento de hipótese infecciosa não confirmada. O aceite do juiz não confirma sepse nem representa concordância médica geral.

### Caso 004

Quatro falas: recorrência da dispneia após drenagem apoiada; causa do derrame, antecedentes e exposições desconhecidos. Uma resposta apenas manifesta estar aguardando exames, sem acrescentar fato clínico.

Astra mantém obstrução linfática maligna como mecanismo mais provável, mas localização anatômica e envolvimento pleural direto não confirmados. Reconhece que CT e microbiologia só aparecem em fala médica, sem outputs subjacentes no input recebido; não declara infecção excluída. Essa prudência é observável, mas não fecha a lacuna de registro da fila.

- **fila_sem_output_persistido** (L27, L28, L30, L32, L35, L38, L41, L44, L45, L63, L65): pH/Gram/cultura/CT estavam em fila. Há respostas do matcher e exam_cost para a execução posterior, incluindo cobrança de microbiology_007 e imaging_008, mas não eventos tool com outputs liberados. Input blind mantém estados Queued, not performed e não contém CT/microbiologia literais. Fala médica L45 relata achados de CT e não sugere infecção. Isso é lacuna de logging/encaminhamento de evidência, não prova automática de invenção médica.
- **amostra_historica** (L22, L27): Fonte da toracocentese repetida relata 1.2 L; valores isolados triglicerídeos/colesterol/citologia vêm da amostra inicial, disponível como registro prévio. Texto de componentes não preserva qualificador de amostra inicial; não representam necessariamente nova análise da coleta de 1.2 L.
- **subtipo_procedimento** (L22): Pedido ultrasound-guided thoracentesis recebe fonte Thoracentesis and fluid examination, sem explicitar orientação ultrassonográfica. Volume e caráter do líquido são literais, mas técnica guiada não é atestada.
- **custo_nao_e_output**: Terminal cobra seis fontes, mas somente quatro fontes distintas estão em outputs tool/followup salvos. Fontes sem output literal são CT e microbiologia. Custos e fala médica ficam em contagens segregadas e não são promovidos a outputs literais.

### Caso 005

Três falas apoiam doença reumatoide/ILD estável cinco anos, tratamento sem alteração e exposição a asbesto. Demais detalhes desconhecidos; não identifiquei invenção clínica clara.

Astra identifica melanoma pleural com primário desconhecido; origem metastática provável, mas não confirmada, extensão e contribuição à hipoxemia pendentes. Reconhece explicitamente que CT pós-contraste não estabelece protocolo de angiografia nem exclui embolia; eco indisponível não gera conclusão cardíaca.

- **escopo_CTPA_CT** (L15, L46): CT pulmonary angiography recebe Chest CT pós-contraste genérica. Astra preserva limite: não comprova protocolo angiográfico nem exclusão de embolia. Conduta de CTA solicitada não equivale a CTA entregue.
- **painel_IHQ_excedente** (L22): Pedido Pleural fluid cytology recebe fonte inteira citologia+imuno-histoquímica, incluindo sete marcadores. Valores são literais, mas o painel amplo não foi solicitado separadamente. Biópsia distinta depois é entregue ao revisorL40 e sustenta dois marcadores em tecido.
- **amostra_e_temporalidade_ambigua** (L22, L46): Toracocentese separadamente solicitada indisponível, enquanto fonte citologia registra High-volume thoracentesis. Next_steps final diz reassess after the documented thoracentesis. Pode referir-se à drenagem documentada pela fonte, mas não demonstra nova drenagem executada nesta solicitação; cronologia exige preservar distinção.
- **biópsia_revisor** (L28, L30, L40): Biópsia foi held/duplicada no médico, depois entregue no seguimento do revisor. Final corretamente atribui positividade SOX10/Melan-A à biópsiaCT-guided entregue; não inventa outros achados de tecido.

### Caso 006

Cinco falas apoiam pigmentação leve de juntas/joelhos, ausência de corticoide, internação por opacidade torácica cinco anos antes sem diagnóstico/tratamento de TB. Sintomas de crise, data da pigmentação, outros fármacos e exposições permanecem desconhecidos; não identifiquei invenção clínica clara.

Astra distingue DNA de Mycobacterium tuberculosis detectado da viabilidade, susceptibilidade e atividade extra-adrenal não confirmadas. Reconhece expressamente que horários reais de cortisol, administração de cosyntropin e respostas estimuladas não foram estabelecidos. Não presume estabilidade ou ausência de crise sem sinais vitais/sintomas documentados; culturas indisponíveis não são negativas.

- **alias_exame_dinamico** (L17, L43): Pedido 8 AM cortisol recebe fonte basal completa ACTH+cortisol; cosyntropin baseline/30/60 min classificado already_ordered contra mesma fonte, sem dados estimulados. A fonte não atesta horário 8 AM. Astra explicita ambos os limites em reasoning e unconfirmed, sem inventar resposta dinâmica.
- **protocolo_CT_nao_atestado** (L21): Pedido Adrenal-protocol CT recebe CT adrenal genérica, sem fases/washout definidos pela fonte. Final usa nódulos/calcificações literais, sem extrapolar washout ou protocolo.
- **pre_requisito_respeitado** (L24, L31): PCR do tecido marcado after_procedure:adrenal_biopsy liberado após biópsia entregue. Fonte e valor qPCR são literais; culturas de tecido indisponíveis preservadas como desconhecidas.
- **recomendacao_nao_e_fato_paciente** (L43): Próximos passos citam rifampicin durante terapiaTB como orientação futura, não como medicamento atual do paciente. Essas recomendações não foram avaliadas pelo juiz de diagnóstico nem adjudicadas clinicamente nesta auditoria.

### Caso 007

Quatro falas apoiam fezes escuras sem melena confirmada, icterícia progressiva quatro dias, primeira dose pembrolizumab 400 mg 14 dias antes e ausência de sangramento notado/dor abdominal. História transfusional, hemólise anterior e outras exposições desconhecidas.

Astra mantém pembrolizumab como gatilho provável, sem provar causalidade; não resolve subtipo frio/misto só pela positividade C3d, não exclui sangramento gastrointestinal concomitante. Icterícia cerca de dez dias após dose é cálculo14 dias menos 4 dias, não cronologia nova inventada.

- **teste_enfileirado_nao_executado** (L15, L29): Cold agglutinin titer enfileirado, não executado antes da admissão; final preserva esse estado e subtipo pendente.
- **painel_parcial** (L11): CBC somente hemoglobina; bilirrubina total e fração não conjugada, sem inventar valor absoluto direto/indireto. Enzimas hepáticas/PT-INR indisponíveis mantidas assim.
- **inferencia_causal** (L29): Relação temporal é evidência de trabalho, não confirmação farmacológica nem exclusão de outros gatilhos; final reconhece essas limitações.

### Caso 008

Duas falas apoiam dor há dois dias, fraqueza progressiva, ausência de trauma/medicamentos. Procedimentos espinais/diátese hemorrágica e demais exposições permanecem desconhecidos.

Astra distingue mecanismo espontâneo provável de causa idiopática demonstrada; fonte de sangramento, história de procedimentos/hemorragia e lesão vascular oculta pendentes. Reconhece que DWI/whole-spine não são atestados e leucocitose não confirma infecção.

- **fragmentos_literais_unidos** (L8): PT 12 s e INR 1.0 são fragmentos exatos da fonte unidos por ponto e vírgula; valor não é substring contígua integral, mas não altera números/unidades.
- **protocolo_MRI_nao_atestado** (L5, L26): Pedido inclui diffusion-weighted sequences; fonte somente MRI cervicotorácica. Astra não presume sequência DWI ou cobertura whole-spine executada.
- **interacao_emergencia** (L10, L12): Primeira admissão bloqueada antes de conversa; uma fala do paciente após exames permite prosseguir.

### Caso 009

Duas falas mantêm timing/flatos e exposições não relatadas como desconhecidos. Linguagem weren’t mentioned expõe estilo de leitor de registro, sem afirmar ausência clínica.

Fonte operatória estabelece stent em Meckel perfurando ileum; final distingue isso de obstrução mecânica/mecanismo de adesões e gravidade sistêmica não estabelecidos. História ERCP existe no patient.json público, mas não foi entregue na entrevista/blind input; revisor honestamente a mantém desconhecida no encontro.

- **rubrica_override_herdada**: Judge matching criterion aceita obstrução, perfuração ou diverticulite causada por stent biliar migrado; não exige Meckel/site exato, decisão herdada do protocolo V3 com revisão médica pendente. Final nomeia Meckel mesmo sem exigência. Não mudar critério/escore nesta auditoria.
- **conclusao_nao_extrapolada** (L18, L32): Operação confirma perfuração e líquido purulento; não detalha ressecção/source-control completo. Revisor solicita assegurar controle de fonte sem inventar ressecção concluída ou valor de lactato ausente.

### Caso 010

Três falas apoiam dor inicialmente leve oito dias antes piorando, gestação aproximada cinco semanas e primeira gravidez. Data menstrual exata/síncope e exposições desconhecidas.

Astra separa ectopia abdominal/tecido gestacional documentados de implantação microscópica especificamente omental e primária versus secundária não confirmadas. Não presume que vitais inicialmente estáveis excluem sangramento ativo.

- **via_ultrassom_nao_atestada** (L15): Pedido transvaginal recebe fonte Pelvic ultrasound que não explicita via. Achados são literais; não presumir protocolo/avaliação completa do líquido livre.
- **pre_requisito_patologia** (L34, L41): Patologia após laparoscopia entregue e fonte literal de produtos de concepção; não inventa villi/trophoblast microscópicos só porque pedido os nomeia.
- **CT_escopo_observado** (L27): Nesta candidata, CT contrastado retorna apenas fonte CT contrastada, sem devolver concomitantemente registro CT não contrastada prévio. Observação desta execução, sem atribuir melhora a uma causa não demonstrada.

## Lacuna de evidência 004 e cegamento

Fila 004 contém pedidos pH/Gram/cultura/CT que posteriormente geram respostas do matcher e exam_cost. O input final mantém as mensagens Queued, not performed, não contém o relatório CT ou microbiologia liberados e apresenta esses achados somente em fala médica L45. FonteMRI etc não é usada para preencher retrospectivamente o que o revisor recebeu.

A leitura somente de código explica o percurso observado: `runner_v3.py:115–133` executa fila e retorna string de resultados; `runner_v3.py:310–319` acrescenta essa string à mensagem user do médico, sem evento tool persistindo a saída. `working_v4.py:29–44,103` reconstrói evidência a partir de eventos selecionados salvos. Assim, os outputs da fila não são incluídos nessa reconstrução. Matcher/custos e fala compatível com a fonte não demonstram qual foi a string exata originalmente entregue ao médico; também não constituem prova automática de alucinação. Nenhum código foi corrigido durante a condição.

Astra reconhecer falta de CT/microbiologia em seu próprio input é transparência observável, mas **não fecha a lacuna do pipeline**. Quatro fontes distintas do 004 estão em outputs salvos e seis são cobradas. Esse limite permanece explícito nas contagens do JSON.

Hashes dos dez inputs finais e dos dez traces conferidos. Todos usam system_hash `709cc4f658bb1b394828d2ef1fc83d2232c9504af1500070b93fd28070843c56`, com exclusão referência/proposta/revisões diagnósticas anteriores/juiz. Inspeção encontra apresentação, físico inicial, mapa como guidance, falas e resultados de seguimento. Mapa e pedidos dirigidos de seguimento ainda são pistas geradas pela cascata; cegamento de respostas diretas não significa independência de todo o processo.

## Juiz, critério e afirmações clínicas

O JSON de auditoria guarda separadamente os **20 payloads públicos exatos** (dez finais, dez propostas), respostas e hashes. Não são encaminhados ao revisor clínico nem reproduzidos aqui. Todos recebem apenas Ground Truth, Assistant diagnosis e Matching criterion. Assistant confere com dx_agent/proposal_dx do terminal. **Não recebem transcript, reasoning, confidence, unconfirmed ou next_steps.** Aceitação 10/10 avalia correspondência de diagnósticos segundo o critério; não avalia fidelidade temporal, veracidade de raciocínio, incerteza, calibração ou recomendações.

Caso 009 conserva override herdado V3: aceita obstrução, perfuração ou diverticulite causada por stent biliar migrado; Meckel/site exato não obrigatório. Final nomeia Meckel, mas isso não muda a permissividade do critério, cuja revisão médica permanece pendente. Nenhuma nova alteração de critério nesta rodada.

Caso 003: rationale do juiz considera vazamento urinário intraperitoneal equivalente clínico a sepse; evidência entregue confirma ruptura/vazamento, enquanto final mantém infecção/choque séptico não confirmados. Aceite do juiz não confirma sepse nem concordância médica geral. Hipóteses causais/patológicas e medidas de tratamento requerem avaliação humana independente.

## Guards, temporalidade e limites

Todos os dez working outputs obedecem diagnóstico <60 palavras, reasoning <180, confidence finita 0–1 e listas unconfirmed/next_steps. `validate_review` valida estrutura/número/limites, **não fidelidade semântica/tempo automaticamente**. Observação das saídas mostra limites preservados para CTPA versus CT 005, cortisol/cosyntropin 006, DWI/cobertura MRI 008 e implantação microscópica/primária-secundária010.

Problemas restantes não desaparecem com texto incerto: troponina I recebe T 002; estudo followup eletrofisiológico 002 ainda chega na fase aguda; componentes de amostras históricas 001/004 perdem parte da cronologia; cytology 005 entrega painel IHQ amplo; técnica guiada 004 e via TVUS 010 não são atestadas na fonte. Nenhum resultado day_N/retrospectivo entregue nesta candidata. Angiografia 001, PCR tecido 006 e patologia 010 têm pré-requisitos de procedimento observados. Procedimentos time_zero comprimem o tempo clínico.

Confianças autorreferidas não calibradas; identidade do modelo servido não atestada (Sol médico/paciente/revisor inicial; Astra final, effort medium). Transporte json_emulated validado por parser, sem stdout bruto persistido para atestação independente. Os 229 testes informados pelo agente principal não reexecutados aqui e não substituem revisão médica. Um run em dez casos conhecidos e uma cascata com Astra não estabelece desempenho externo, superioridade, segurança clínica ou ConsistencyDx. Original/offline/candidata são condições distintas.

JSON acompanha as falas, achados/IDs/linhas, hashes, incertezas completas, contagens segregadas, custos terminais e escopo exato do juiz. Revisão médica permanece pendente.
