# Qwen3.8 (prime e 0902): revisão do juiz, comparação com a Fase 1 e próximos passos

Data: 04-10-2026. **Revisão médica cega continua pendente.** Tudo abaixo é leitura de um modelo de linguagem sobre os dados, não parecer clínico. Interpretação do pedido: "últimas duas runs" = as duas execuções de modelos adicionadas por último (`qwen/qwen3.8-max-prime` e `qwen/qwen3.8-max-0902`, 3 runs × 10 casos cada = 60 encontros). A mesma checagem foi estendida aos outros cinco modelos só para comparação justa.

## 1. O juiz errou em algo?

Li os 60 diagnósticos contra o gabarito e a justificativa do juiz (Gemini 3.1 Flash-Lite, temperatura 1).

**Falsos negativos (juiz recusou o que devia aceitar): não encontrei nenhum claro.** Das 10 recusas, 7 são etiologias claramente diferentes do gabarito (pericardite purulenta por MRSA em vez de pseudoaneurisma coronariano infectado com ruptura de stent, no caso 001, 4 vezes; corpo estranho ingerido em vez de stent biliar migrado em divertículo de Meckel, no caso 009, 3 vezes) e 3 são do caso 002 e discutíveis (ver abaixo).

**Falsos positivos prováveis (juiz aceitou o que, lido com rigor, não bate com o gabarito): 8 dos 50 acertos, concentrados nos dois Qwen3.8.**

| Caso | Encontros | O que o diagnóstico diz | O que o gabarito exige | Observação |
|---|---|---|---|---|
| 007 | prime r1, r2; 0902 r1, r2, r3 | "Anemia hemolítica autoimune quente (DAT+)" sem citar pembrolizumabe, checkpoint ou imunoterapia | "AHAI associada ao pembrolizumabe" | O próprio juiz escreve que o diagnóstico "não menciona" a etiologia medicamentosa e aceita mesmo assim. A etiologia é o ponto clinicamente acionável (suspender o fármaco) |
| 002 | prime r3; 0902 r1 | Atrial standstill com BAV, atribuído a miocardiopatia fibrótica/atrial isolada | "Miocardite atrial isolada com atrial standstill e BAV" | Texto quase igual foi recusado em outros encontros (prime r2, 0902 r2 e r3): o mesmo conteúdo recebeu vereditos opostos, ruído do juiz com temperatura 1 |
| 009 | prime r1 | Obstrução por stent biliar migrado com peritonite/perfuração, sem citar o divertículo de Meckel | Stent migrado impactado em divertículo de Meckel | Aceitável para quem aceita "stent migrado" como núcleo; sem o Meckel é parcial |

Por que importa: o juiz foi leniente justamente com os modelos que **não fazem anamnese**. Os outros cinco modelos conversaram com o paciente e todos os acertos deles no caso 007 citam o fármaco; os Qwen3.8 quase nunca perguntaram sobre medicamentos e chegaram só à síndrome.

**Efeito no placar (heurística de palavras-chave: exigir pembrolizumabe/checkpoint/imunoterapia no 007, miocardite no 002 e Meckel no 009; é grosseira e não substitui um médico):**

| Modelo | Juiz original | Só regra do 007 | Três regras (dx + raciocínio) | Três regras (só no diagnóstico) |
|---|---:|---:|---:|---:|
| qwen3.8-max-prime | 26/30 | 24 | 22 | 21 |
| qwen3.8-max-0902 | 24/30 | 21 | 20 | 20 |
| GPT-5.2 | 23/30 | 23 | 23 | 23 |
| GLM-5 | 20/30 | 20 | 19 | 19 |
| Qwen3.5-397B | 19/30 | 19 | 19 | 19 |
| GLM-4.5-Air | 19/29 | 19 | 17 | 17 |
| GPT-OSS-120B | 10/25 | 10 | 10 | 10 |

Conclusão: **a liderança dos Qwen3.8 desaparece sob leitura rigorosa; o GPT-5.2 passa a ficar no topo ou empatado.** O ranking depende da régua do juiz, então prefiro tratar prime, 0902 e GPT-5.2 como empatados.

## 2. Resultados dos modelos de pesos abertos contra a Fase 1

Atenção: **não é uma comparação equivalente.** Fase 1: prontuário determinístico, 40 ações, 3 repetições, nuvem pela assinatura, avaliação por filtro de conceitos e **releitura do autor**. Fase 2: paciente simulado, 10 turnos, 3 repetições, OpenRouter, avaliação por **juiz LLM**. Abaixo, Fase 1 usa a releitura (a régua mais próxima de clínica) e Fase 2 o juiz.

| Modelo | Fase | Acertos | % |
|---|---|---:|---:|
| Claude Opus 5.5 | 1 (releitura) | 27/30 | 90,0% |
| Claude Sonnet 5.5 | 1 (releitura) | 26/30 | 86,7% |
| qwen3.8-max-prime | 2 (juiz) | 26/30 | 86,7% (73–80% sob leitura rigorosa) |
| qwen3.8-max-0902 | 2 (juiz) | 24/30 | 80,0% (67–70% sob leitura rigorosa) |
| GPT-6 Sol | 1 (releitura) | 23/30 | 76,7% |
| GPT-5.2 | 2 (juiz) | 23/30 | 76,7% |
| GPT-6.1 Sol | 1 (releitura) | 21/30 | 70,0% |
| GPT-6 Astra | 1 (releitura) | 20/30 | 66,7% |
| GLM-5 | 2 (juiz) | 20/30 | 66,7% |
| GLM-4.5-Air | 2 (juiz) | 19/29 | 65,5% |
| Qwen3.5-397B | 2 (juiz) | 19/30 | 63,3% |
| GPT-5.6 Terra | 1 (releitura) | 18/30 | 60,0% |
| GPT-OSS-120B | 2 (juiz) | 10/25 | 40,0% |
| Qwen3.5 9B / Qwen3 8B / Llama 3.1 8B (locais) | 1 | 3 / 0 / 0 de 30 | 10% / 0% / 0% |

Por caso (acertos em 3 runs; Fase 1 releitura, Fase 2 juiz): os casos **001, 002 e 009** continuam sendo os mais difíceis nos dois formatos. O Opus 5.5 na Fase 1 resolveu 002 (3/3) e 009 (3/3) e 001 (2/3), mas o Sonnet 5.5 errou 001 (0/3), e nenhum modelo aberto resolve os três de forma estável. O 007 (hemólise por pembrolizumabe) era difícil na Fase 1 (Opus 1/3) porque o prontuário travava o dado; no formato novo, os modelos que conversam com o paciente resolvem.

Teto com amostragem repetida (juiz original, mesmos dados): **pass@3** (alguma das 3 runs correta) e **maioria de 3** (≥2 de 3 corretas), em 10 casos:

| Modelo | pass@3 | maioria de 3 |
|---|---:|---:|
| qwen3.8-max-prime | 10/10 | 9/10 |
| qwen3.8-max-0902 | 10/10 | 7/10 |
| GPT-5.2 | 9/10 | 8/10 |
| GLM-4.5-Air | 9/10 | 6/10 |
| GLM-5 | 8/10 | 7/10 |
| Qwen3.5-397B | 8/10 | 7/10 |
| GPT-OSS-120B | 5/10 | 3/10 |

Todo caso foi resolvido por pelo menos um modelo em alguma run (001, 002 e 009 por 4 modelos cada). Isto mostra que há margem para os abertos com **mais amostras e agregação**, mas pass@3 é teto otimista (exige saber qual das 3 está certa).

**Onde os abertos estão em relação à fronteira, com cautela:** na régua do juiz, o melhor aberto (Qwen3.8) fica ao nível do GPT-5.2 e perto dos números de Opus/Sonnet 5.5 da Fase 1, mas (a) os formatos são diferentes, (b) os Qwen3.8 se apoiam em atalhos do simulador (abaixo) e (c) 10 casos dão intervalos largos (86,7% em 30 tem Wilson de 70–95%). O que realmente falta é rodar a fronteira no mesmo formato (seção 4).

## 3. Lista de melhorias para reduzir erros evitáveis e testar o quanto os abertos se aproximam da fronteira

**A. Avaliação (reduz falsos positivos/negativos)**
1. Reescrever a rubrica do juiz com **elementos obrigatórios por caso** (etiologia/mecanismo/fármaco): "AHAI" sem pembrolizumabe é parcial, não correto. Reportar acerto estrito e acerto tolerante.
2. Juiz mais forte, **temperatura 0**, e painel de 2 juízes com desempate; guardar a justificativa. Re-julgar os 210 encontros já feitos custa só cerca de US$ 1–3 (a chamada do juiz é pequena) e mede o ruído (caso 002: mesmo texto, vereditos opostos).
3. Adjudicação **médica cega** das divergências entre juízes e dos casos 002, 007 e 009.

**B. Simulador e protocolo (reduz atalhos e perdas evitáveis)**
4. Bloquear achados cirúrgicos, histopatológicos e de autópsia até haver pedido de cirurgia/biópsia no relato (hoje "laparoscopia diagnóstica" devolve o desfecho). Sem isso, modelos que pedem tudo de uma vez ganham sem raciocinar.
5. Aceitar o mesmo achado em mais de uma ferramenta (ecocardiograma em beira-leito e em outras investigações; hCG em sangue e em beira-leito) e mapear hemograma → hemoglobina, que hoje geram "não disponível" para pedidos razoáveis.
6. **Paciente simulado fixo para todos os médicos** (hoje o paciente é o próprio modelo do médico, o que confunde os resultados: paciente fraco devolve história pior). Idealmente um modelo único e forte.
7. Condição "anamnese primeiro": exigir pelo menos algumas perguntas ao paciente (medicamentos, antecedentes, contexto) antes de liberar exames, ou medir isso à parte. Os Qwen3.8 quase não conversam e perderam o pembrolizumabe.
8. Subir o limite de turnos como análise de sensibilidade (hipótese: os casos 009 e 001 pedem mais um passo, por exemplo exploração cirúrgica).

**C. Do lado dos modelos abertos**
9. Validar os **parâmetros de amostragem** com cada fornecedor (os dos Qwen3.8 foram assumidos iguais aos do Qwen3.5) e testar `reasoning_effort` mais alto nos que suportam.
10. GPT-OSS: reforçar o formato da chamada `admission` e limitar o excesso de conversa (5 encontros sem diagnóstico). GLM-4.5-Air: fecha cedo demais (2 turnos); um lembrete para perguntar sobre medicamentos antes de concluir.
11. **Agregação de 3 amostras** (maioria ou segunda instância que reconcilia diagnósticos): os dados mostram que a maioria de 3 dá 7–9/10 nos melhores abertos, acima da média por run (cerca de 8,7/10 no prime e 8/10 no 0902).
12. Etapa de "segunda opinião": depois do diagnóstico, uma passada de diagnóstico diferencial e de busca ativa de etiologia (fármacos, dispositivos implantados) antes de admitir. Este é o erro típico nos casos 001, 007 e 009.
13. Checar a quantização/rota (a Alibaba não informa) e reproduzir em um segundo provedor quando houver.

**D. Estatística**
14. Mais casos (10 é pouco: intervalos de ±15–25 pontos) e 5 repetições, com análise **por caso** (pareada) em vez de agregada; repetições do mesmo caso não são pacientes independentes.
15. Registrar logprobs quando a rota devolver (só o Qwen3.5 devolveu; sem ProbScore por enquanto).

## 4. Vale refazer com Opus 5.5 e Sonnet 5.5 no formato novo? Quanto custaria?

**Vale, sim, como calibração.** Hoje a única referência fechada no formato novo é o GPT-5.2. Sem Opus/Sonnet 5.5 no mesmo simulador não dá para dizer "até onde os abertos chegam". Eles já foram medidos na Fase 1 (90% e 87% pela releitura) e agora veríamos se mantêm isso sem prontuário determinístico, conversando com o paciente simulado. Ressalvas: com 10 encontros por modelo o intervalo é muito largo (8/10 tem Wilson de 49–94%), então serve para **calibrar e ver o comportamento** (fazem anamnese? resolvem 001, 002 e 009?), não para ranquear. Recomendo antes: (i) re-julgar com juiz mais forte e rubrica estrita (seção 3, itens 1 e 2, quase de graça) e (ii) decidir o paciente simulado fixo (item 6), pois o paciente é o próprio modelo do médico.

**Custo de 1 execução por caso (10 encontros por modelo)**, preços atuais do OpenRouter: Opus 5.5 US$ 4/M entrada e US$ 20/M saída; Sonnet 5.5 US$ 2/M e US$ 10/M. Base: tokens de médico+paciente por encontro medidos nos traces (GPT-5.2: 19 mil entrada e 3,6 mil saída; Qwen3.8: 16 mil e 5 mil), ×1,25 por o tokenizador da Anthropic gerar mais tokens (hipótese), mais US$ 0,007 de associador e juiz.

| Cenário | Tokens (entrada/saída) | Opus 5.5 por encontro / 10 encontros | Sonnet 5.5 por encontro / 10 encontros |
|---|---|---:|---:|
| Baixo (conciso) | 20 mil / 3 mil | US$ 0,15 / **US$ 1,5** | US$ 0,08 / **US$ 0,8** |
| Central (como GPT-5.2) | 24 mil / 4,5 mil | US$ 0,19 / **US$ 1,9** | US$ 0,10 / **US$ 1,0** |
| Alto | 33 mil / 7 mil | US$ 0,28 / **US$ 2,8** | US$ 0,14 / **US$ 1,4** |
| Cauda (verboso como GPT-OSS) | 99 mil / 10 mil | US$ 0,60 / **US$ 6,0** | US$ 0,31 / **US$ 3,1** |

- **Os dois, 1× por caso: cerca de US$ 3 no cenário central (faixa US$ 2,2–4,2; cauda extrema cerca de US$ 9).** O saldo do teto é cerca de US$ 9,6 (US$ 18 menos US$ 8,36 gastos), então cabe.
- Referência cruzada: na Fase 1 (outro formato, mais longo) o equivalente de API foi US$ 0,61 por trajetória no Opus e US$ 0,25 no Sonnet, o que corresponde ao cenário de cauda.
- **3× por caso para os dois ficaria em cerca de US$ 9 (central) e passaria do teto no cenário alto.** Sugiro 1× nos dois e, se o resultado for informativo e o custo ficar no central, uma 2ª rodada só do Opus.
- Cuidados operacionais: fixar rota `anthropic` sem fallback; decidir parâmetros de amostragem; cada chamada reserva até 24 576 tokens de saída no ledger (cerca de US$ 0,49 no Opus), o que é suportável com 3 encontros simultâneos.

Nada disto foi executado; é só estimativa e opinião, sem autorização de gasto.
