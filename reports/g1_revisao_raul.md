# Revisão do Raul dos 20 casos do G1 (GLM 5.3 Flash)

Este arquivo guarda **somente o que o Raul disse em revisão**. Cada caso tem uma seção; as ainda não revisadas ficam como `pendente`, sem texto. Nada aqui é análise automática ou nota do juiz LLM.

Como é atualizado: o Raul revisa um caso, o texto entra na seção do caso, o painel do artifact é regenerado com `scripts/g1_review_export.py` e a mudança é commitada. Quando o texto-base foi redigido pelo Claude e adotado pelo Raul, a linha `Autoria` diz isso.

Formato de cada seção (lido pelo exportador): linhas `Status`, `Data`, `Rótulo`, `Classe` (`good`, `warn`, `bad` ou `neutral`) e `Autoria`; depois blocos `### Título` com parágrafos e itens `- `.

Referências protegidas (como o UpToDate) não são copiadas para o repositório, que é público. As seções as citam e resumem com palavras próprias; os PDFs e imagens ficam só com o Raul.

Revisados: 1 de 20.

---

## g1_001 · Influenza
Status: pendente

## g1_002 · Lombalgia aguda
Status: pendente

## g1_003 · Hipertensão: ajuste da medicação
Status: pendente

## g1_004 · Diabetes tipo 2: controle da medicação
Status: pendente

## g1_005 · Cistite não complicada
Status: pendente

## g1_006 · Dor de garganta
Status: pendente

## g1_007 · Depressão
Status: pendente

## g1_008 · Asma
Status: pendente

## g1_009 · DPOC
Status: pendente

## g1_010 · Gota aguda
Status: pendente

## g1_011 · Urticária aguda
Status: pendente

## g1_012 · Otite média aguda
Status: revisado
Data: 2026-11-26
Rótulo: Conduta parcialmente apropriada
Classe: warn
Autoria: Texto-base redigido pelo Claude na análise de 26-11-2026 e adotado pelo Raul como sua revisão deste caso. A referência (UpToDate, algoritmo e texto sobre o tratamento inicial da otite média aguda em crianças) foi enviada pelo Raul; aqui ela está resumida com palavras próprias.

### Veredito
- Diagnóstico correto (otite média aguda direita).
- Conduta parcialmente apropriada. O antibiótico imediato é uma alternativa aceita pela referência, mas para este menino a conduta sugerida era analgesia com observação, e a decisão deveria ter sido tomada junto com a mãe. O GLM decidiu sozinho e justificou com uma febre que o caso não tem.
- A nota "apropriada" do juiz de conduta na rodada válida não se sustenta: ele aceitou a febre inventada pelo GLM. O item sobre conduta expectante (m1) deveria constar como não seguido, não como parcial.

### O que a referência diz para este caso
- Fatores de risco que tiram a criança da conduta expectante: idade abaixo de 6 meses, imunocomprometimento significativo, aspecto toxêmico e anomalia craniofacial. O menino não tem nenhum.
- Sem fator de risco, a conduta sugerida é a expectante (analgesia contínua e acompanhamento por até 72 horas). O antibiótico imediato é uma alternativa razoável. A decisão é compartilhada com os responsáveis, depois de explicar benefícios e riscos de cada caminho.
- Se a opção for observar, o médico dá instruções claras do que fazer se piorar ou não melhorar, com receita adiada ("rede de segurança") ou instruções escritas.
- Menor chance de benefício do antibiótico imediato: idade a partir de 2 anos, febre abaixo de 39 °C, dor leve a moderada que melhora com analgésico, doença unilateral sem sinal de gravidade (abaulamento não extremo, sem perfuração) e sintomas há menos de 72 horas. Maior chance: menos de 2 anos, febre a partir de 39 °C, dor intensa sem alívio, doença bilateral ou sinais graves, e mais de 72 horas de sintomas.

### O caso contra esses critérios
- Idade 3 anos: favorece observar.
- Temperatura 38,3 °C no exame e 38,5 °C em casa: favorece observar.
- Doença unilateral (só o ouvido direito): favorece observar.
- Sintomas desde a noite anterior (menos de 72 horas): favorece observar.
- Dor moderada, com o menino brincando entre as crises; ninguém perguntou se o paracetamol aliviou: indeterminado.
- Tímpano "vermelho e abaulado, imóvel": a vinheta não diz se o abaulamento é extremo. É o único ponto que poderia favorecer tratar, e é uma falha de redação da vinheta.
- Nenhum critério de maior benefício está claramente presente.

### O que o GLM fez
- Fez uma troca com a mãe e admitiu com amoxicilina imediata, sem oferecer a opção de observar e sem perguntar a preferência dela. A referência pede decisão compartilhada.
- O raciocínio registrado considerou conduta expectante e receita adiada, mas o texto final escolheu o antibiótico imediato sem explicar por quê.
- O diagnóstico escrito diz "febre >39 °C equivalente" e a justificativa cita febre; o caso tem 38,3 °C.
- Perguntou sobre vacina e creche e admitiu na mesma mensagem, então a pergunta ficou sem resposta; mesmo assim escreveu "imunizado".
- Acertos: não pediu exame algum, descartou sinais de gravidade (mastoide, rigidez de nuca, desidratação), começou pela analgesia e deu sinais de alerta para retorno.

### Antibiótico, dose, duração e seguimento (referência)
- Escolha: amoxicilina em dose alta, 90 mg/kg/dia em duas doses (máximo de 4 g/dia), para a maioria das crianças. Doses menores, em torno de 40 mg/kg/dia (máximo de 1,5 g/dia), servem em comunidades com poucos pneumococos não suscetíveis à penicilina. Amoxicilina com clavulanato se houve beta-lactâmico nos 30 dias anteriores, se há histórico de otite recorrente sem resposta à amoxicilina ou se há conjuntivite purulenta junto.
- Duração: a diretriz da AAP indica 7 dias para crianças de 2 a menos de 6 anos; um dos autores da referência trata a partir dos 2 anos por 5 dias, o outro por 5 a 7 dias.
- Rodada válida: 45 mg/kg/dia por 5 dias. Dose no nível baixo, aceitável só se a comunidade tiver pouca resistência (o caso não diz), e 5 dias dentro do que a referência admite.
- Rodada invalidada: cerca de 90 mg/kg/dia (650 mg duas vezes ao dia em 14 kg) por 10 dias. Dose certa, duração além dos 5 a 7 dias indicados para esta idade.
- Seguimento: a maioria das crianças não precisa de acompanhamento específico depois que os sintomas somem. Reotoscopia em 2 a 3 meses só para otites recorrentes, perfuração, problemas de linguagem ou aprendizado e perda auditiva. O GLM marcou reexame em 4 a 6 semanas para todos, mais do que a referência pede.
- Trocar para amoxicilina com clavulanato se não melhorar em 48 a 72 horas não é coberto pelas páginas enviadas.

### Limites desta revisão
- A fonte do caso é a revisão do BMJ Open (acesso aberto), que também recomenda observar; a referência do Raul é mais específica.
- Uma execução por caso, vinheta escrita pelo Claude, sem outro revisor. Isto não estabelece segurança clínica nem superioridade de modelo.

## g1_013 · Candidíase vulvovaginal
Status: pendente

## g1_014 · Fibrilação atrial
Status: pendente

## g1_015 · Doença do refluxo gastroesofágico
Status: pendente

## g1_016 · Enxaqueca
Status: pendente

## g1_017 · Osteoartrite de joelho
Status: pendente

## g1_018 · Rinite alérgica
Status: pendente

## g1_019 · Hipotireoidismo primário
Status: pendente

## g1_020 · Hiperplasia prostática benigna
Status: pendente
