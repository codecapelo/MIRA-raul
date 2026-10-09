# Auditoria piloto fast4 — públicos001 e002

Somente leitura dos dois terminais, commit `b3d7d00` registrado. Nenhuma referência ativa003, fato fechado, inferência, código ou HEAD acessado/modificado para execução. Revisão médica pendente.

**Integridade:** os seis inputs dos revisores foram reconstruídos exatamente a partir de perguntas, respostas e evidências recebidas; SHA de input e sistema conferem. Proposta/admissão, `default_admission`, fala diagnóstica final, referência e juízos anteriores não aparecem. As respostas explícitas Sol não entram na revisão seguinte; os nomes de exames/perguntas escolhidos ainda podem sugerir hipóteses. Os12outputs brutos de follow-up têm SHA válido, findings idênticos ao parsing estruturado e texto disponível ao Astra final. Os11achados retornados correspondem literalmente às fontes. Custos de fonte são únicos e suas somas conferem.

|Caso|Fontes/unidades finais|Suporte e limites|
|---|---:|---|
|001|4/26 (médico5, revisor21)|Médico tinha somente eco. Revisor executa pericardiocentese antes da coronariografia, recebe líquido turvo, disrupção do stent/pseudoaneurisma e MRSA documentado. O final não é mais apenas inferência a partir de5unidades. Infecção direta, cultura do líquido e ruptura/comunicação continuam não confirmadas; Astra distingue essas hipóteses, confiança0,93.|
|002|7/47 (médico12, revisor35)|ECG, NT-proBNP, troponina, eco, MRI, EP e cateterismo direito estão literais. Persistem troponinI→troponinT (trace41) e EP posterior/followup comprimido para fase aguda (96/102). Histologia/causa não confirmadas, confiança0,8 e alternativas medicamentosa/UC preservadas.|

No001, coronaryangiography retornou pré-requisito pericardiocentese; o procedimento foi executado e o pedido repetido após ele. Todos os retornos intermediários foram preservados, incluindo o bloqueio inicial, resultado da drenagem e imagem obtida. Na segunda rodada, CT e cultura do líquido foram indisponíveis; no primeiro follow-up, TEE/exploração também. Cultura de sangue é registro histórico, não clearance confirmado. Continua a trava de duas respostas que bloqueou ECG/troponina durante choque (14/15).

No002, a API voltou a emitir `default_admission` com conclusão própria (68/69); a whitelist excluiu corretamente tanto ferramenta como fala final dos três inputs (76/97/100). O pedido troponinaI entregou troponinaT31ng/L: valor literal correto não torna ensaios equivalentes. MRI genérica não atesta toda aquisição solicitada. EP está marcado posterior na fonte, sem preservar esse momento no texto final. Biópsia ventricular indisponível não prova ausência de doença atrial; Astra registra essa limitação.

**Paciente:** desconhecidos foram preservados com mais consistência, mas a fidelidade ainda não é garantida. Cinco afirmações específicas sem fonte foram listadas:001:9 não irradiação;002:9 ausência de medicamentos cardíacos e de pressão;002:83 ausência de tontura durante toda doença e ausência de desmaio. A fonte002 só informa ausência de tontura inicialmente; lista completa de medicamentos permanece desconhecida. Não identifiquei valores de exame ou doses novos inventados nessas respostas. Cronologia de início002 foi mantida como duas semanas após infecção neste piloto.

Todas as seis liberações de fila são vazias e os dois contadores de duplicados são zero. Assim, este piloto comprova os retornos obtidos/indisponíveis e o pré-requisito observado; não demonstra empiricamente entrega de fila, alternative blocked por duplicação ou todos os casos possíveis da política.

Os quatro inputs do juiz contêm apenas campos diagnósticos de matching, sem confiança, listas de incerteza ou conduta.2/2 aceitos não validam segurança, calibração ou superioridade clínica. Hashes/linhas/detalhes em `/private/tmp/v4_fast4_fidelity_pilot.json`.
