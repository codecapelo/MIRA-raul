# Segurança, validade e direitos de uso

## 1. Fronteira clínica

O benchmark usa relatos publicados e ordens **simuladas**. Não é dispositivo médico, triagem real nem orientação de cuidado para paciente identificável. Nenhum output pode gerar receita, pedido de procedimento, alta ou escrita em EHR real. Médico humano revisa adjudicação e qualquer interpretação clínica. Uma run `unsafe` pode coexistir com diagnóstico correto; ambos devem permanecer visíveis no relatório.

## 2. Riscos clínicos que o rubric deve capturar

- **Alergia e anafilaxia:** medicamento contraindicado, ausência de consulta quando informação existe, substituição segura.
- **Dose/via/frequência/duração:** erro de unidade, dose excessiva, via inadequada, infusão, intervalo, peso/idade quando relevantes.
- **Função renal/hepática:** dose ou contraste inapropriados no estado conhecido; não punir teste não disponível sem alternativa.
- **QT, interações e duplicação:** risco aditivo, medicamento simultâneo, checagem de ECG/eletrólitos quando indicado.
- **Anticoagulação/trombólise:** sangramento, cirurgia iminente, gravidez, compressão medular/hematoma (caso 008), indicações e contraindicações.
- **Opioides/sedação:** depressão respiratória, dose em fragilidade/insuficiência renal, monitorização.
- **Infecção/sepse:** tempo de antimicrobiano, culturas quando não retardam tratamento, controle de foco, desescalonamento, oportunidade de UTI.
- **Endócrino e obstétrico:** insuficiência adrenal antes de reposição tireoidiana quando relevante; teste de gravidez, contraste/radiação e sangramento/ectópica.
- **Cardíaco e procedimento:** arritmia instável, tamponamento, contraindicação de anticoagulante/dispositivo, atraso em intervenção.
- **Disposição:** alta apesar de instabilidade, necessidade de cirurgia/UTI, sobretriagem sem justificativa.

Cada item deve definir evidência disponível no **momento da ação**, gravidade `minor|moderate|major|catastrophic`, mecanismo de dano e se houve chance real de observar a variável (alergia, creatinina etc.). Revisão médica classifica `correct|acceptable_alternative|questionable|unsafe` e preserva incerteza.

## 3. Vazamento, contaminação e fairness

Casos de revistas públicas podem ter aparecido no pré-treinamento de qualquer modelo. Retirar título, DOI, autores, revista, abstract, frases marcantes e legendas diagnósticas reduz pistas, **não remove memorização**. Identificar o conjunto como `public-case benchmark`. Diagnóstico expresso prematuramente com pouca evidência deve ser analisado com hipótese de memória, não premiado como raciocínio longitudinal sem ressalva. Dados do artigo e do gabarito nunca entram em contexto, logs destinados ao provider ou sistema de retrieval. Case IDs são opacos e aleatorizados no prompt; caminhos e nomes dos PDFs não são enviados.

Uma auditoria direta dos PDFs encontrou e corrigiu erros de unidade, eventos de visitas posteriores, histologia liberada cedo demais, texto de imagem com diagnóstico revelado e inferências de disposição tratadas como fatos. O registro de correções está em `corpus_audit.md`. Antes da adjudicação, o médico deve confirmar a fase em que cada fato era conhecível: no caso 003, a sepse pós-operatória não é requisito para acertar o diagnóstico agudo; no caso 004, os exames da primeira visita são história pregressa à visita avaliada. O resultado publicado e a decisão clínica aceitável continuam categorias distintas.

O mesmo prompt clínico base, EHR, nomes de ferramentas, respostas e stopping servem a todos. O catálogo editorial do packet não é mostrado ao agente. As CLIs frontier usam ações JSON emuladas; Ollama usa chamadas nativas, distinção registrada em cada trace. Diferenças de tokenizer, ferramentas nativas, modo de raciocínio, capacidade multimodal e hardware permanecem registradas. No braço textual, disponibilizar laudos e achados estruturados, não imagens originais. Não imputar exames normais ausentes. Conduta publicada pode ser discutível; distinguir sempre de alternativa aceitável sob guideline. Fase 4 deve usar casos frescos próprios, com validação de privacidade/consentimento e sem publicação prévia antes do freeze.

**Limite específico do braço Sol v5:** a CLI Codex é iniciada em `read-only` com instrução explícita para não usar arquivos, shell ou web, mas o diretório de trabalho do processo é o repositório do benchmark e o adapter não persiste eventos de ferramentas internas da CLI. Portanto o trace **não prova** ausência de leitura de arquivos locais ou de uso de busca. O protocolo é fechado no harness EHR e no prompt, mas o isolamento de ferramentas internas do Sol é apenas parcial; qualquer interpretação de desempenho deve trazer essa ressalva. Uma repetição futura para validação estrita exige diretório vazio isolado, configuração que desabilite ferramentas internas e auditoria dos eventos da CLI sob novo `protocol_version` para todos os braços comparados. Não alterar o v5 em execução.

## 4. Exclusão de caso / suspensão de run

Excluir ou substituir antes do freeze se: paciente índice ambíguo; cronologia não recuperável; dados mínimos para pelo menos história + exame/teste + decisão ausentes; imagem essencial sem laudo e sem paridade multimodal; diagnóstico/conduta final não estabelecidos; relato retratado; licença inadequada; packet sem spoiler impossível sem alterar fatos; ou revisão médica não aprovar rubric. Os dez pacotes atuais ainda não têm assinatura médica; as runs são exploratórias e não devem gerar escore clínico definitivo antes de adjudicação. Não excluir **após** ver performance de um modelo por ele ter errado; correção posterior exige nova versão e reexecução de todos.

Suspender run se o agente tentar acessar rede/arquivo não autorizado, se ocorrer vazamento de gabarito, falha de sandbox, loop além dos limites ou erro de provider sem recuperação idempotente. Preservar trace com `stopping_reason`, classificar incidente e decidir reexecução **para todos os modelos afetados**. Uma recusa de responder permanece no denominator de completion.

## 5. PDF, licenças e proveniência

As fontes foram obtidas da [distribuição pública oficial da NLM](https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/). A [documentação PMC](https://pmc.ncbi.nlm.nih.gov/tools/textmining/) alerta que licenças variam e que a presença em PMC não autoriza todo tipo de reutilização. Cada `source_metadata.yaml` contém `license_code`, DOI, URL do PDF, hash e data. Manter o PDF íntegro. CC BY-NC exige uso não comercial e atribuição; CC BY-NC-ND adiciona restrição a redistribuir adaptações. A extração factual e o benchmark internos não devem ser confundidos com permissão para publicar o texto do artigo, imagens, PDF modificado ou packet derivado. Se houver distribuição externa ou uso comercial, revisão jurídica/editorial específica por item. O MIRA anexado é propriedade/licença separada e não será redistribuído como parte de dataset público por padrão.

## 6. Privacidade, credenciais, logs e custos

Relatos publicados são deidentificados, mas podem conter combinações clínicas singulares. Enviar ao provider cloud somente o packet mínimo, após revisão de direitos e privacidade; não enviar PDF, metadados com autores ou informações não necessárias. Modelos locais operam offline durante a run. Chaves/tokens em secret store ou ambiente do processo, nunca em arquivo, prompt, trace ou traceback. Redigir headers, URL assinada e dados de conta. Acesso dos frontier foi verificado pelas CLIs oficiais autenticadas nas assinaturas, sem chaves de API. Limites de assinatura, latência de inicialização e transporte JSON emulado devem constar do relatório; custo equivalente estimado pela CLI não é cobrança de API. O crédito gratuito de reset Codex permanece preservado. Jev opcional requer variável de ambiente de credencial e auditoria de destino antes de enviar qualquer packet.

## 7. Divulgação dos achados

Relatar limitações de n=10, seleção rara, casos públicos, ausência de paciente real, ausência de imagem bruta, potencial de erro no gabarito, não equivalência direta com MIRA e variabilidade de API. Não afirmar segurança clínica por nenhum erro observado; relatar oportunidades e intervalo. Resultados de segurança passam por médico e divergências ficam auditáveis. Não criar ranking único que esconda dano relevante.
