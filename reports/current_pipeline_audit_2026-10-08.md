# Auditoria de base — 150 encontros e evolução até o checkout principal

Data: 08-10-2026. Somente leitura dos dados originais; custo novo de API: US$0. Dois artefatos novos: este relatório e `current_pipeline_audit_2026-10-08.json`. O JSON contém cada um dos 150 encontros, custos por ator, todas as ferramentas e respostas do paciente com número da linha, hashes, repetição de pedidos, resultados repetidos, observações com fase avançada, inventário dos relatórios e 17 commits do principal. Nenhum histórico foi editado, nem terminal reexecutado.

**Escopo confirmado:** checkout `/Users/test/MIRA-RAUL`, `main` = `de114dde8f0083e7b858a6f4b6a36370fd84c2ac`. Os 150 arquivos do manifesto atual e os 978 do histórico migrado foram revalidados por SHA-256, sem divergência. Todos os arquivos JSONL dos sete diretórios de tentativas incompletas foram processados; os JSON dos relatórios foram parseados e inventariados. A inspeção das narrativas inclui os casos críticos e relatórios de auditoria. Isto não equivale a adjudicação médica manual de toda afirmação das 460 respostas de paciente.

**Descoberta de continuidade:** há outra ref LOCAL, `claude/complete-remaining-100-cases-356596` = `c1d3270`, contendo Qwen3.8, Sonnet/Opus pela assinatura, v3.3–v3.7, política de exames, cascata e prontuário. Não confundir `git log --all` com HEAD. O `AGENTS.md` nessa ref é posterior ao do principal e registra último snapshot financeiro de US$18,965410033, teto20. Portanto o ledger4,274237323 do checkout principal é snapshot da base, não saldo vivo da conta nem todo o trabalho recente. A revisão completa dessa ref foi repassada ao agente responsável pelo histórico; não houve checkout ou merge nesta auditoria.

## Resultados reproduzidos diretamente dos traces

150 combinações únicas run/modelo/caso; 144 julgadas, 91 positivas pelo juiz, 53 negativas; seis terminais sem julgamento. Cinco falhas de validação de ferramenta e uma ausência de admission no limite10. As falhas não foram convertidas em diagnóstico errado nem consideradas prova de insegurança clínica.

| Modelo | Juiz positivo/julgados | Sem julgamento | Custo terminal US$ | Médico | Paciente | Matcher | Juiz |
|---|---:|---:|---:|---:|---:|---:|---:|
| GPT-OSS120B | 10/25 | 5 | 0,207173805 | 0,124995000 | 0,064885000 | 0,009506555 | 0,007787250 |
| GLM4.5Air | 19/29 | 1 | 0,121011845 | 0,078509880 | 0,022955025 | 0,010479690 | 0,009067250 |
| GLM5 | 20/30 | 0 | 0,468473360 | 0,367687800 | 0,075771600 | 0,015670960 | 0,009343000 |
| Qwen3.5 | 19/30 | 0 | 1,094453110 | 0,547041200 | 0,529092500 | 0,008951410 | 0,009368000 |
| GPT5.2 | 23/30 | 0 | 2,251417260 | 1,805112050 | 0,420122500 | 0,016621460 | 0,009561250 |

Total das respostas/terminais: US$4,142529380. Médico2,923345930; paciente1,112826625; matcher0,061230075; juiz0,045126750. Paciente ocupa26,9% do custo terminal e48,3% no Qwen3.5, apesar de não decidir o diagnóstico. São1325 respostas médicas,460 do paciente,1017 do matcher e144 do juiz. Valores por ator contam `usage.cost` dos traces, sem estimar API equivalente de assinatura.

Ledger principal:3115 linhas settled, zero pending/uncertain, US$4,274237323. A diferença0,131707943 inclui preparação, piloto invalidado e interrupções; não é fuga financeira nem saldo restante atual. `run23_timeout_reconciliation.json` atribui0,030653310 no nível da conta porque13 pedidos não tinham resposta; `interrupted_cost_reconciliation.json` atribui0,000382500 por diferença estável. Essas atribuições administrativas não viram `usage.cost` inventado. Não fiz consulta nova à conta.

## Onde os casos difíceis quebram

### case001 — tamponamento identificado, mecanismo específico quase nunca investigado

Gold publicado: pseudoaneurisma coronário infectado com ruptura do stent, tamponamento e endocarditeMRSA. Rubric distingue o mecanismo publicado de oportunidades críticas: reconhecer tamponamento/choque, avaliar estrutura/coronárias, drenar; tratamento definitivo tem alternativas sob revisão. `acceptable_diagnoses=[]` e aprovação médica pendente.

Em15 encontros:13 julgados,3 positivos,2 sem julgamento. Dez receberam eco, quatro pericardiocentese, sete culturas. **Nenhum recebeu angiografia coronária, OCT/IVUS ou exploração do dispositivo**, embora esses achados existam no catálogo. A maior parte termina em pericardite purulenta/tamponamento, explicação plausível parcial que não identifica o pseudoaneurisma. Os positivos não provam resolução do mecanismo: Qwenrun1 chamou endocardite/miocardite/tamponamento; Qwenrun2 chamou endocardite/pericardite/tamponamento; GPT5.2run3 chamou pericardite/tamponamento. Os três omitem pseudoaneurisma/ruptura de stent.

Há falha de roteamento verificável: `logs/raw/z-ai__glm-4.5-air/case_001.jsonl:33` pede eco em `request_other_investigation` e recebe indisponível; linha47 o mesmo conceito em radiologia recebe eco. A ref v3.6 já corrigiu pedidos na ferramenta errada; isso não deve ser apresentado como proposta inédita.

GPT-OSSrun2 não é o piloto alucinado histórico: sua primeira resposta de paciente preserva desconhecidos, mas o médico diagnostica STEMI sem ECG disponível e deixa de obter eco por pedido mal grafado/ferramenta inadequada (`runs/run2/logs/raw/openai__gpt-oss-120b/case_001.jsonl:32`). A conclusão na linha55 extrapola o diagnóstico; não atribuir todo esse erro ao paciente. O piloto alucinado continua exclusivamente no arquivo histórico e relatório de fidelidade correspondente.

### case002 — localização atrial e bloqueio vs síndrome ampla de miocardite

Gold: miocardite atrial isolada, atrial standstill e bloqueioAV. Rubric exige oportunidades deECG, eco, avaliação de bradicardia/pacing; MRI/CTPA são recomendados, não diagnóstico final automático. Não contém lista clínica validada de diagnósticos alternativos.

Todos15 receberamECG, troponina eNT-proBNP; noveeco, trêsMRI e umestudo eletrofisiológico de followup. Só4/15 positivos. MRI torna a localização atrial visível; uma resposta GLM5run2 recebeu exatamente "left atrial late gadolinium enhancement... no substantial ventricular scar" mas fechou "Viral myocarditis... right ventricular dysfunction" (linha43). É erro/incompletude da síntese médica além da coleta de evidência, não simples ausência de exame. GPT5.2run3 obteveMRI e eletrofisiologia e nomeou atrial standstill/AVblock. A eletrofisiologia tem fasefollowup, portanto o acerto inclui compressão temporal; não mostra diagnóstico inicial autônomo.

GPT5.2run1 pede eco pela ferramenta other e recebe indisponível na linha50, mesmo com eco disponível. Ainda assimMRI permite diagnóstico atrial. GLM-Airrun1/run3 foram positivos com miocardite/bloqueio ampla, enquanto Qwen/GLM5 receberam negativos para conceitos similares: heterogeneidade do juiz além da coleta.

PacienteGLM5run2 (`runs/run2/logs/raw/z-ai__glm-5/case_002.jsonl:8,12`) acrescenta edema igual nas pernas, pior ao final do dia, ganho de peso, negativas de febre/suor noturno/doenças e cervejas nos fins de semana. Esses detalhes não existem no pacote autorizado. Isso mostra persistência de invenção fora do piloto. Não estimei uma taxa de alucinação a partir dessa amostra.

### case009 — diagnóstico de entrada não pode saber automaticamente o achado operatório

Gold: stent biliar migrado impactado no divertículo deMeckel com diverticulite/perfuração ileal. Os15 receberamCT que menciona corpo estranho/obstrução; **nenhum recebeu exploração abdominal ou ressecção**. Logo não receberam o fato que nomeiaMeckel/perfuração. Catorze julgados,3 positivos,1sem julgamento. Os três positivos têm diagnóstico amplo de obstrução por stent/ERCP, sem descrição do achado específico.

O rubric clínico exigeCT, exploração urgente e destino cirúrgico apropriado; ICU é destino pós-operatório. Não é obrigatório adivinharMeckel antes da operação. Dois eixos precisam permanecer separados: diagnóstico etiológico final completo versus reconhecimento de abdome agudo com conduta resolutiva. Uma admissão segura não basta para reivindicar diagnóstico completo; uma omissão deMeckel na fase inicial não prova conduta insegura.

**Instabilidade exata e demonstrada do juiz:** GLM5 devolve literalmente "Small bowel obstruction secondary to migrated biliary stent" nas três runs. O juiz decideFalse,True,False. O critério e o diagnóstico são os mesmos; o juiz só recebe diagnóstico/referência/critério, sem conversa ou justificativa clínica. O JSON lista as três justificativas. A diferença de escore entre essas runs não é diferença do médico.

## Repetição, indisponibilidade e custo de exames

85/150 encontros repetem pelo menos uma consulta EXATAMENTE normalizada dentro da mesma ferramenta;78 repetem pelo menos um resultado já entregue. Há403 chamadas inteiramente indisponíveis entre1237 eventos de ferramenta, incluindo150admissions. Físico repetido, alterações de condição e reavaliações podem ser justificadas: esses números são sinais de auditoria, **não contagem de exames clinicamente desnecessários**. Não foram associados a preços reais nem custo financeiro de exames.

Exemplo: GPT5.2case002run1 solicita exame físico cinco vezes (linhas3,14,21,22,31), recebe sempre os mesmos dados e pede novamente painéis indisponíveis (linhas45,64). GPT-OSScase002run1 recebeECG eeco duas vezes e biomarcadoresduas vezes; várias respostas passam pelo mesmo problema de formato. A base tem set `returned`, mas não usa esse set para impedir nova entrega ou nova chamada auxiliar; a regra depende do prompt.

Pedidos em painel misturam testes disponíveis e indisponíveis. Uma chamada com troponina/BNP/hemograma/TSH pode devolver só troponina/BNP; a resposta atual não dá estado individual para os demais. Ausência de dados não é normalidade nem teste realizado. O JSON da auditoria sinaliza indisponibilidade só quando toda a chamada foi recusada, portanto403 é limite parcial do problema.

27 encontros receberam pelo menos uma observação com fase avançada/pré-requisito. A base omite as barreiras temporais por decisão explícita de protocolo. Não classifico isso como vazamento não autorizado: é limitação conhecida da adaptação, que muda a interpretação de acurácia e simulação realista. Ter `availability_policy` estrita no JSON dos casos, código permissivo e documentação de compressão temporal torna especialmente importante mostrar a fase no replay.

## O que já foi tentado, antes de propor mudanças

Os17 commits do principal incluem: migração/pinning; congelamento; guarda de orçamento/validação; rotaDeka→Akash→Mancer; matcher sem raciocínio e limite8192; piloto invalidado porECG→eco/OCT e correção de modalidades; falhas de ferramenta terminais; retomada por hash eadmissionauto; paralelismo; exceção serializável; limite de concorrência; pacingGPT5.2; ordenação de commit administrativo; consolidação50; verificação/reconciliação; extensão100; consolidação150. Nenhuma deve ser vendida como solução nova.

Na refClaude, foram lidos oAGENTS posterior e relatóriosv3.6/v3.7: já há matcherestrito com sinônimos/painéis/famílias, auto-roteamento, política custo-benefício com fila, bloqueio de repetição no turno, abertura mínima comidade/sexo, emergência com conversa, consultoria/mapa/cascata comOpus, acordo com revisor, varredura de evidências e prontuárioHaiku após decisão. v3.6 manteve20/20pelojuiz, testes20,8→19,4/caso, tier3 45→34 e preçoaproximado−11%, mas implantação0,177→0,196/caso; v3.7instrução de fala diminuiu exames8,8→6,0 e elevou trocas2,0→3,8 numa amostrade5. São experimentos já realizados, sujeitos a seleção dos casos e juizLLM. Os preçosaproximados dessa ref não atendem à escolha atual do usuário de custo RELATIVO até serem relabelados ou substituídos; não sãoUS$deAPI.

## Próximas melhorias com valor adicional

1. **Auditoria de juiz por diagnóstico idêntico e fase:** congelar casos de decisão discordante sem novas chamadas e mostrar julgamentoLLM separado de componentes etiológicos documentados, síndrome/emergência e ações. Revisão humana das discordâncias; não afrouxar critério para fabricar100%.
2. **Estado individual de todo pedido**, mesmo painéis mistos: requested/available/not-recorded/held/already-returned, factids usados e fase. Evita que o médico ou prontuário entendam silêncio como teste normal. Verificar se refv3.7já cobre integralmente antes de implementar.
3. **Memória de redundância entre turnos e justificativa para repetir:** refv3.6já bloqueia no mesmo turno. Ampliar pararesultados imutáveis e famílias indisponíveis com cache local; só novo resultado/custo relativo quando há mudança de fase ou razão clínica explícita. Reexibir uma evidência não equivale a pedir exame novo. Testar offline contra78casos sinalizados sem alterartraces.
4. **Fidelidade factual do paciente como contrato por fato**, priorizando recuperador determinístico de fatos conhecidos/desconhecidos; a camada de expressão não pode acrescentar negativas de sintomas, números ou antecedentes. Remover o uso obrigatório do mesmo modelo caro do médico parapaciente. Benefício potencial na base:1,112826625/150, mas efeito na cascata atual precisa ser medido independentemente. A refClaude já dispõe avaliação de fidelidade; fazer diff antes de propor redesign.
5. **Critério de resolutividade condicionado à fase:** ação de transferir/surgery, reconhecer urgência e não pedir confirmação desnecessária pode encerrar a avaliação inicial; investigação definitiva pós-operatória deve ser fase separada. Preserva recuperação etiológica final sem exigir adivinhação. Exemplo obrigatório de regressão:case009 antes/depois daexploração;case001 antes/depois de drenagem/angiografia;case002 inicial/followup.
6. **Benchmark novo fechado e avaliação cega**, sem mapa contendo solução dos mesmos10casos. Não otimizar exclusivamente nos casos conhecidos nem declarar100% clínico de10/10ou20/20. Critério de aceitação: acerto final, omissões críticas, suporte factual, pedidos/retornos indisponíveis/repetidos, custoRELATIVOdeexames, APIreal, consumo deassinatura e latência apresentados separadamente.

Não iniciei novos encontros, não usei credenciais e não alterei modelo/prompts/fatos/provedor da base. OsUS$5novos autorizados e saldo/cap da ref posterior precisam ser conciliados pelo coordenador antes de quaisquer testes pagos; a auditoria não presume5disponíveis na conta.
