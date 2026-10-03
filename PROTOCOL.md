# MIRA-RAUL — protocolo prospectivo

Versão: 2026-10-03. Estado: preparação; os resultados devem ser preenchidos somente após execução auditada. Esta avaliação adapta a arquitetura de Zhang et al., *Nature Medicine*, DOI [10.1038/s41591-026-04609-x](https://doi.org/10.1038/s41591-026-04609-x), e o código [KatherLab/onprem-medical-agents](https://github.com/KatherLab/onprem-medical-agents), commit `eea2386c665c9caaa7ee093c8cb092d1c337de88`.

## Pergunta e população

Comparar os modelos solicitados em encontros diagnósticos com paciente simulado e ferramentas, usando os mesmos dez casos públicos do experimento anterior. São casos publicados, não prontuários privados do usuário. Este conjunto não é uma amostra de MIMIC-IV nem o VivaBench oficial completo. A avaliação é exploratória e não estabelece desempenho clínico, segurança assistencial ou equivalência ao estudo publicado.

Os 290 percursos terminais anteriores permanecem em `legacy/`, com protocolo, rótulos, resultados e rastros próprios. Não são reexecutados, substituídos ou adicionados ao denominador desta avaliação. O resultado anterior por correspondência lexical e o novo resultado por equivalência clínica são métricas distintas.

## Dados e separação dos papéis

Cada caso em `cases/` contém `patient.json`, `investigations.json`, `reference.json` e `provenance.json`. O paciente recebe somente apresentação, antecedentes e fatos subjetivos disponíveis no início; não usa ferramentas. O médico recebe a queixa inicial, respostas do paciente e observações devolvidas por ferramentas. O diagnóstico de referência permanece reservado ao juiz. A procedência deve identificar a publicação e registrar as transformações realizadas.

A narrativa inicial permanece restrita à apresentação: achados de exames, resposta terapêutica e diagnóstico final não migram para o prompt do paciente. As ferramentas, porém, disponibilizam **achados publicados quando solicitados**, segundo uma adaptação diagnóstica de VivaBench. Os metadados originais de disponibilidade e pré-requisitos são preservados, mas não impõem bloqueio geral por `time_zero`; esse bloqueio impediria acesso a achados necessários para vários diagnósticos finais. Observações marcadas `unavailable_for_immediate_care` permanecem excluídas. Nenhum resultado pode ser inventado.

Essa **compressão temporal** permite obter em um encontro simulado achados descritos ao longo do caso publicado; não representa sua latência clínica real. Portanto o experimento não é uma réplica estrita da avaliação inicial/admissão de MIRA-v2. A ação `admission` é a submissão final do agente, e não uma garantia de disponibilidade temporal de todos os exames. Incertezas de cronologia devem aparecer na procedência e no relatório.

## Encontro e limite

Usar os prompts diagnósticos de VivaBench e as ferramentas de exame físico, sangue, urina, avaliação à beira do leito, radiologia, microbiologia e outras investigações. Resultados devem vir exclusivamente dos fatos autorizados do caso; pedido indisponível recebe resposta de indisponibilidade. O médico conclui com diagnóstico e justificativa, através da ação final equivalente a `finish`/`admission`. Não há ferramenta explícita Plan nem agente crítico na condição principal.

Aplicar **limite rígido de dez turnos do médico**, conforme a decisão do usuário e o texto do artigo. Registrar separadamente chamadas do paciente, do juiz, chamadas de ferramentas e tentativas técnicas. Não executar os seis turnos adicionais de encerramento possíveis no código atual upstream. Se não houver submissão válida até o limite, registrar encontro incompleto; não inventar diagnóstico por pós-processamento. A definição operacional exata de turno e os pedidos feitos em cada turno devem constar no rastro do runner.

O artigo descreve um paciente sem ferramentas, restrito a queixa, resumo clínico e medicamentos prévios quando disponíveis; não exige um modelo de paciente universalmente independente do médico. O código atual configura o mesmo Qwen para ambos. A identidade do modelo de paciente desta execução deve ser explicitada na configuração e nos resultados, sem pressupor que os comentários históricos do código representam a configuração publicada.

## Modelos, provedores e custo

Congelar antes da execução os identificadores OpenRouter, modelo do paciente, juiz, temperatura, limites de saída, parâmetros de raciocínio suportados e número de repetições. As rotas são selecionadas por modelo na configuração do runner: provedor fixo, fallback desabilitado e parâmetros exigidos. Preservar resposta de identificação do provedor e preços verificados. Alterações de provedor, modelo ou parâmetros exigem nova identificação de condição experimental.

Não presumir que os pesos FP8 servidos localmente no artigo são idênticos à implementação hospedada. Parâmetros locais não suportados devem ser omitidos e registrados como divergência. O juiz upstream usa temperatura 0,01 e limite de 1.024 tokens; a tabela do artigo apresenta parâmetros padrão do modelo, que não substituem os parâmetros efetivos da execução.

A implementação em preparação usa o mesmo modelo da condição médica para o paciente, temperatura 0,01 e limite de 8.192 tokens. O associador auxiliar é GLM-4.5-Air (temperatura 0,01, limite de 2.048 tokens). O juiz Gemini 3.1 Flash-Lite usa temperatura 1, top_p 0,95 e limite de 8.192 tokens: isso diverge do código upstream e deve permanecer visível no relatório. O décimo turno força somente a submissão `admission`; rodadas anteriores permitem até quarenta completions internos, como o limite interno upstream. Portanto dez turnos externos não equivalem a dez solicitações pagas.

Custos do médico, paciente, juiz e eventual associador de pedidos devem ser contabilizados separadamente, com reserva prévia e interrupção no orçamento configurado. Falhas e custo de tentativas não podem desaparecer do relatório. Repetições técnicas não contam como novos casos independentes. Não há repetição automática paga de um caso inteiro. A retomada reutiliza respostas duráveis já liquidadas somente quando o hash do pedido e o commit coincidem; pedidos incertos bloqueiam chamadas novas até reconciliação. Isso difere das três tentativas automáticas do upstream, que reutilizam agentes/contexto/coletor.

## Julgamento e análise

O juiz compara diagnóstico final e referência por significado clínico, usando **o ramo AIDOC/MIMIC de `PromptBuilder` upstream**: diagnóstico de referência como string e critério de correspondência clínica, em vez do ramo VivaBench com listas de gold/diferenciais e crédito parcial. O médico e paciente usam os prompts VivaBench; o julgamento utiliza essa composição explícita de componentes, próxima à avaliação MIMIC descrita no artigo. O juiz recebe referência, diagnóstico e critério; não recebe conversa completa nem justificativa final do agente, embora esta seja preservada para revisão. Guardar decisão booleana e justificativa do juiz. Não há crédito parcial definido nessa condição. O juiz não avalia segurança do encontro nem concordância terapêutica.

Reportar por modelo: encontros planejados, tentados, completos e incompletos; concordância diagnóstica booleana; falhas de formato e ferramentas; uso de tokens, custo e tempo. O denominador primário inclui todos os encontros planejados; apresentar também a análise dos encontros completos. Não descartar falhas silenciosamente. Com dez casos, reportar contagens e intervalos de confiança de Wilson; não alegar superioridade clínica por pequenas diferenças. Se houver repetições, a unidade clínica continua sendo o caso e as observações do mesmo caso são dependentes.

As estatísticas do artigo são referências externas: MIRA-v2 tinha 551 casos, CDM 2.400 e VivaBench 990; as análises principais de consistência usaram cinco execuções por caso. O artigo informa Qwen com 90,04% no conjunto de sete doenças e 83,8% em CDM; AUC de consistência 0,860, e 49,4% de retenção com 98,9% de acerto ao limiar 0,90. Esses valores não são metas validadas nem resultados transferíveis aos dez casos. A concordância com médicos envolveu 181 casos revisados. O estudo usa DeLong, bootstrap, testes pareados e correções de multiplicidade em contextos próprios; replicar somente o formato do encontro não replica essas inferências.

## Reprodutibilidade e limites

Preservar hashes de casos/prompts/configuração, commit do projeto, modelos, provedores, parâmetros, chamadas e respostas brutas, resultados finais e falhas. Manter credenciais fora de arquivos e logs. A revisão médica cega permanece necessária antes de qualquer afirmação clínica. A execução hospedada usa somente os casos públicos autorizados; não reproduz a privacidade integral da inferência local descrita no artigo.

Artefatos da execução: configuração `config/run1.json`; livro de custos `logs/budget.sqlite`; chamadas e respostas `logs/raw/<modelo>/case_XXX.jsonl`. O orçamento global configurado é US$ 18,50; reservas pendentes impedem gastos sem reconciliação. A conferência do cronograma é feita por `PYTHONPATH=src python3 -m mira_runner.runner`; `--execute` inicia chamadas e `--pilot-only` restringe ao piloto. A execução e o teste local são estados separados e devem ser reportados separadamente.

Fontes locais: `references/zhang.txt:1080–1206`, `:1290–1360`, `:1450–1492`; auditoria detalhada em `reports/upstream_audit.md`. O upstream declara CC BY 4.0; conservar atribuição e aviso das alterações. Licenças de artigos, modelos e dependências devem ser tratadas separadamente.
