# Auditoria de fidelidade — piloto v4 rápida, casos públicos001–002

Auditoria somente leitura da condição `fast1/public/run1`, commit congelado `65efa490eac32a34b7d2a21ee8216a047a199e16`. Ambos terminais completos; nenhuma referência do caso003 ativo ou dos casos fechados foi aberta. Sem inferência, alterações de código/dados/prompts ou Git. Este parecer não propõe retentativas orientadas pelo juiz.

**Achado principal:** a redução de tempo não resolve toda a fidelidade. O piloto tem2/2 diagnósticos finais aceitos, propostas0/2, mas o caso002 contém uma falha de exclusão da proposta e o caso001 chega ao rótulo etiológico provável com apenas dois resultados de fonte. Não se pode interpretar o escore como confirmação clínica.

## Integridade e entrada dos revisores

Os quatro hashes de input e de sistema conferem. Sol e Astra receberam as respostas nativas OpenRouter de médico/paciente, os resultados literais e o follow-up registrado. Todas as oito observações efetivamente retornadas (2 no001,6 no002) correspondem literalmente às fontes. Nenhum número de dose ou valor quantitativo de teste inventado foi identificado nesses retornos. As quatro liberações de fila têm SHA válido e destinatário `reviewer`; todas são vazias neste piloto, portanto não há achados de fila nem demonstração clínica desse caminho.

No002, `tool default_admission` linha70 contém a proposta Myocarditis e sua justificativa. Ambos inputs dos revisores (linhas77 e98) incluem esse registro apesar de `proposal_excluded=true`; o filtro exclui `admission`, mas não o nome `default_admission`. A fala anterior do médico linha69 também diz confirmar/diagnosticar myocarditis. Não há indicação de referência ou juízo anterior nos inputs. Excluir o parecer Sol explícito não torna Astra independente de hipóteses: os pedidos de Sol mencionam pseudoaneurisma/ruptura no001 e biópsia para miocardite atrial no002.

## Fala do paciente: fatos, desconhecidos e afirmações sem fonte

O critério é presença no registro fornecido ao paciente, não plausibilidade fisiológica. Oito afirmações específicas sem apoio foram listadas; esse total não é taxa validada nem adjudicação médica completa.

| Caso/linha do trace | Afirmação sem fonte | Evidência da fonte |
|---|---|---|
|001:9|Dor não irradia; dispneia; tontura/lightheadedness (3)|Nenhuma dessas características em patient.json1–43 ou investigations.json1–129. Choque não autoriza inventar a narrativa.|
|002:16|Mesalazina é o único medicamento regular (1)|patient.json27 lista o medicamento;31–35 deixa lista completa desconhecida.|
|002:31|Sem cardiopatia prévia, sem história familiar conhecida de evento súbito, sem viagem recente (3)|patient.json1–37 não contém esses negativos.|
|002:84|Dose de mesalazina não mudou recentemente (1)|patient.json27 não especifica dose, mudanças ou início.|

Os desconhecidos foram adequadamente mantidos no001:22 (horário exato, febre/calafrios/sudorese, acesso de diálise) e no002:84 (início da mesalazina e ECG anterior). Há também compressão temporal no002:16: a fonte patient.json15 diz evolução da dispneia duas semanas após sintomas respiratórios; o paciente passa a dizer que está assim há cerca de duas semanas. O numeral é fornecido, mas sua interpretação temporal mudou.

## Caso001: seis unidades de exames

Resultados entregues: eco `ecg_008` (5unidades; investigations.json47) e culturas `microbiology_013` (1unidade; investigations.json116). Não foram entregues coronariografia/pseudoaneurisma (`imaging_009`, fonte60), imagem intravascular (`ecg_010`,75), líquido de pericardiocentese (`procedure_result_011`,90) nem exploração do dispositivo (`procedure_result_012`,103). Os três pedidos Sol (coronary CT angiography, exploração operatória, TEE) voltaram indisponíveis no followup linha73; CT coronária não foi silenciosamente equiparada à coronariografia invasiva da fonte.

A hipótese Sol/Astra de infecção do stent/pseudoaneurisma pode ser um raciocínio probabilístico a partir de MRSA+stent+alteração regional+tamponamento, mas **não está confirmada pelo conjunto recebido**. Astra linha79 registra confiança0,55, composição do derrame, pseudoaneurisma e ruptura não comprovados, além de alternativas. A fonte de referência001 já terminal descreve stent disruption e pseudoaneurisma; esse conteúdo não foi fornecido como evidência confirmatória. Logo,6unidades não demonstram resolutividade clínica superior ou suficiência do workup; podem refletir encerramento mais cedo com hipótese específica e exames indisponíveis. O juiz aceitou o texto diagnóstico, não seu suporte/calibração/conduta.

O bloqueio de exames antes de duas respostas ainda ocorreu na linha14 apesar de choque descrito desde a apresentação. A limitação do mínimo rígido em urgência permanece e requer avaliação médica; esta auditoria não altera a execução congelada.

## Caso002: precisão e cronologia

Todos os números recebidos são da fonte:42/min (investigations8/21), troponina T31ng/L (47), pressão PA58mmHg (73), hemodinâmica65/35/28mmHg, débito5,8L/min e PVR1,2WU (112). Troponin T não foi convertida em troponina I. Eco foi pedido por request_radiology (trace49), mas a fonte especifica TTE, sem inferência de estudo distinto.

O follow-up (trace95) devolve literalmente MRI (fonte138), EP (151) e cateterismo direito (112), com35unidades novas; total42,6fontes. Biópsia dirigida indisponível. O pedido de MRI com protocolo atrial/ventricular específico não estabelece que tal protocolo foi feito: a fonte só descreve Cardiac MRI e achados. Mais material: EP está marcado `available_at=followup` (investigations152), mas é entregue durante a revisão aguda e aparece como achado verificado na resposta final sem destacar seu momento posterior. A cronologia clínica continua achatada.

O médico linha69 afirma ter confirmação de myocarditis; não há confirmação histológica naquele ponto. Astra linha101 restaura hipótese provável, histologia e causa não confirmadas, incluindo possibilidade medicamentosa. Contudo, usa dose não modificada como dado (originado da resposta sem fonte em84). Uma revisão forte pode recuperar especificidade diagnóstica e incerteza sem remover todas as invenções do paciente.

## O juiz e os limites do escore

Quatro inputs do juiz:001 linhas80/82;002 linhas102/104. Campos do caso: Ground Truth, AssistantDiagnosis e MatchingCriterion. Justificativa final, confiança, unconfirmed, next_steps e conduta não entram. Portanto2/2 aceitos não valida segurança, calibração, fidelidade ou superioridade clínica. Revisão médica cega permanece pendente.

Os hashes, linhas, entradas e oito retornos literais estão em `/private/tmp/mira_fast_public_fidelity_pilot.json`. Nenhuma recomendação específica de diagnóstico foi enviada ao executor.
