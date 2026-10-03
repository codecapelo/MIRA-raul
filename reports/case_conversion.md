# Conversão dos dez casos públicos

A conversão executada por `scripts/convert_cases.py` gera dez diretórios em `cases/` e um manifesto. Os arquivos em `legacy/` foram somente lidos. Não houve chamadas pagas nem acesso a provedores.

## Separação e contrato

`patient.json` contém `schema_version`, `case_id`, `initial`, `presenting_complaint`, `history_freetext`, `history_facts` e `unknown_fields`. Somente antecedentes, sintomas, medicamentos e alergias explicitamente disponíveis no início entram no contexto do paciente. Diagnósticos preexistentes, como câncer já conhecido, são antecedentes legítimos. O diagnóstico final do episódio está exclusivamente em `reference.json`.

`investigations.json` contém `observations`: `fact_id`, `domain`, `name`, `value`, `available_at`, `prerequisites` e `unavailable_for_immediate_care`. Exame físico também é observação objetiva e deve ser solicitado. Nomes são de exames/procedimentos, sem revelar resultados no catálogo. Os códigos antigos foram usados uma única vez para nomear exames, nunca para encaminhar perguntas por palavras-chave. O executor deve selecionar exames por nome explícito ou correspondência semântica validada, sem expor o valor antes da solicitação.

`reference.json` contém `correct_diagnosis`, `ground_truth` e `rubric`; os dois últimos preservam integralmente os JSON originais. Seu conteúdo deve ser inacessível aos agentes durante a consulta. `provenance.json` contém hashes SHA-256 de todos os arquivos de origem, metadados textuais, localizadores dos fatos, contagens e alterações explícitas.

## Cronologia

Cada resultado é liberado somente depois da solicitação correspondente. `time_zero` significa potencialmente disponível no início; não significa que o paciente sabe resultados de biópsias ou cirurgias. As marcações `after_procedure:...`, `after_any_procedure:...`, `day_2`, `day_7`, `day_9`, `followup` foram preservadas como pré-requisitos adicionais. Não se deve converter número de turno em número de dia. Resultado de pesquisa retrospectiva do caso 003 é proibido na assistência imediata. Alergia observada no dia 2 foi excluída do histórico inicial.

No caso 010, a frase com o CT anterior foi separada de `hpi_001` e registrada em `hpi_001_prior_ct`, mantendo os números exatos. O paciente informa sintomas e tratamento anterior; a observação do CT precisa ser consultada como registro objetivo. Essa é a única alteração textual de um fato. Todos os demais valores foram preservados literalmente e suas identidades verificadas durante a conversão.

O conjunto contém 117 fatos originais, repartidos em 29 fatos de história e 89 observações (uma observação adicional pela divisão do CT anterior). Não se inventaram números, achados normais, medicamentos ou eventos. Os pacotes continuam tendo incertezas e aprovação médica pendente presentes no conjunto de origem.

## Relação com Zhang et al.

Fonte primária disponível localmente: `references/zhang.txt`, DOI 10.1038/s41591-026-04609-x. O artigo usa dois agentes: paciente conversacional sem ferramentas, limitado à queixa/história/medicamentos disponíveis; médico obtém informações subjetivas pelo diálogo e dados objetivos por ferramentas. O episódio termina com diagnóstico e raciocínio, ou em dez turnos. O planejamento é implícito, sem a ferramenta Plan antiga.

Os denominadores originais são MIRA-v2 551 casos de sete doenças, CDM 2.400 de quatro condições abdominais e VivaBench 990 casos de dez grupos clínicos. Nossos dez casos de relatos públicos são uma adaptação da arquitetura e não uma reprodução desses denominadores ou resultados clínicos.

A análise principal de consistência utiliza cinco execuções estocásticas independentes por caso, MiniLM e média das similaridades cosseno de todos os pares, calculada separadamente para diagnóstico e raciocínio e limitada a [0,1]. Não é uma votação para selecionar diagnóstico. Sensibilidade: N=3/5/10, temperaturas 0,01/0,3/0,6/0,9 e codificadores MiniLM/alternativos. Limiar 0,90 é um ponto operacional estudado, não validade clínica estabelecida para estes dez casos.

Configuração externa VivaBench: Qwen-3.5, temperatura 0,6, top_k 20, top_p 0,95. Configuração inicial MIRA-v2 GLM-4.5-Air: T=0,01, top_p=1, top_k=0. A tabela de modelos inclui Qwen/Qwen3.5-397B-A17B-FP8 em quatro H200; modelos menores locais e interfaces de assinatura devem ser descritos como desvios de modelo/infraestrutura, com parâmetros efetivamente usados registrados.

## Código upstream

Inspeção de `src/dataset/vivabench_dataset.py`: distingue história, exame físico, investigações, imagens, diagnósticos e diferenciais. `src/tools/tool_vivabench.py` implementa exame físico, exames por categoria, radiologia, microbiologia e finish. Ele possui correspondência determinística e fallback por LLM para nomes de exames; a cópia local deve evitar ativar automaticamente esse fallback externo/pago. A função upstream request_procedure apenas registra planejamento; a liberação de resultados de procedimentos nos nossos pacotes é uma extensão necessária para relatos de casos, a ser explicitada.

## Validação e limites

A conversão verifica cobertura de todos os IDs originais e igualdade literal de todos os fatos não divididos. Foram gerados 40 arquivos nos dez diretórios e um manifesto, com hashes de origem. A validação demonstrada é da transformação dos JSON congelados; não constitui nova extração independente dos PDFs, revisão clínica nem desempenho diagnóstico. O executor deve testar isolamento de referência e cronologia separadamente antes de uma rodada de modelos.
