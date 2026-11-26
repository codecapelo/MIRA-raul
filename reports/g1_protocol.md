# G1: GLM 5.3 Flash em atenção primária (protocolo)

Braço extra, específico do GLM 5.3 Flash (`z-ai/glm-5.3-flash`), para medir conhecimento médico e **conduta** em casos simples e comuns de atenção primária e medicina de família. Criado em 24-11-2026 a pedido do usuário. Não faz parte do estudo v6.3 e não muda nenhuma condição congelada.

## Casos
Dez vinhetas, uma por artigo aberto (CC BY, licença conferida no campo `license` do Europe PMC), em `cases_g1/` (construídas por `scripts/build_g1_cases.py`):

| Caso | Condição | Fonte (PMCID) |
|---|---|---|
| g1_001 | Influenza não complicada | PMC12036931 |
| g1_002 | Lombalgia aguda inespecífica | PMC7839780 |
| g1_003 | Hipertensão não controlada em monoterapia | PMC8678709 |
| g1_004 | DM2 não controlado com doença cardiovascular | PMC6761728 |
| g1_005 | Cistite aguda não complicada | PMC11099625 |
| g1_006 | Faringoamigdalite estreptocócica | PMC10746578 |
| g1_007 | Depressão maior, episódio moderado | PMC11351064 |
| g1_008 | Asma mal controlada com SABA isolado | PMC9907191 |
| g1_009 | DPOC sintomática (GOLD B) | PMC9692772 |
| g1_010 | Gota aguda, primeiro episódio | PMC10268528 |

**O que é real e o que é escrito por nós.** As fontes são diretrizes, revisões e consensos, não relatos de caso (relatos de caso abertos são raros ou atípicos). A história, o exame e os resultados de cada caso são **vinhetas escritas por Claude** como apresentação típica da condição; não vêm do artigo nem de paciente real. O **diagnóstico de referência e os itens de conduta de referência vêm do artigo**: cada item tem uma citação que foi encontrada no texto do artigo (comparação só de letras e números) e a seção. Itens de boa prática que o artigo não afirma **não são pontuados**. Tudo está `pending_clinician_review`.

## Execução
Mesmo desenho do médico do v6.3: desk v6.2 (gatekeeper, justificativa e notas de entrega), paciente Sonnet 5.5 pela assinatura, associador/matcher estrito e juiz de diagnóstico Gemini 3.1 Pro como no v5. Diferenças só do G1:
1. **Sem revisores**: a admissão do médico é a resposta final (não há `proposal_correct` separado).
2. A ferramenta `admission` ganha o campo `plan` (conduta da consulta: tratamento com droga/dose/duração, exames ou encaminhamentos pendentes, orientações, retorno e sinais de alarme), registrado no evento `g1_plan`.
3. **Juiz de conduta** (Gemini 3.1 Pro, mesmos parâmetros do juiz de diagnóstico), depois do encontro: para cada item de referência dá `addressed`, `partial`, `not_addressed` ou `contradicted`, lista ações inapropriadas e dá um conceito geral (`appropriate`, `partially_appropriate`, `inappropriate`). Evento `g1_conduct_judge`. O juiz de conduta lê o plano e o diagnóstico final do médico, não a conversa.
4. Livro-razão próprio (`runs/v5/g1/budget.sqlite`) com teto de US$ 1,50 (a execução prevista custa cerca de US$ 0,15). Traços em `runs/v5/g1/` (ignorado pelo Git).

Um encontro por caso, sem retentativas. O juiz de conduta do g1_001 falhou na primeira chamada por defeito do lançador (ordinal da requisição, falha antes de qualquer envio, custo zero) e foi executado de novo uma vez, sem repetir o encontro.

## Limites
- As vinhetas foram escritas por Claude, que também é o autor do desenho do estudo; o gabarito de conduta cobre só o que o artigo afirma. Um plano pode ser clinicamente bom e ficar sem pontuar onde o artigo é silencioso.
- O juiz de conduta é um LLM e não estabelece segurança clínica; um encontro por caso; dez casos não dão intervalo de confiança útil.
- Casos comuns e bem documentados podem estar na memória do modelo: acerto não separa conhecimento de memorização.
- Revisão médica pendente.

## Lote B — dez casos cotidianos em dez especialidades (25-11-2026)
Objetivo (pedido do usuário): achar o limiar do GLM 5.3 Flash em casos simples e cotidianos. Mesmo desenho do lote A, com **uma diferença de condição**: a pausa obrigatória de admissão até perguntar exposições/viagem (`V5Tools.admission_blocked`, regra de exposição da v5) foi desligada (`scripts/run_g1.py --no-exposure-pause`); as demais regras de admissão (mínimo de trocas, exame físico antes) ficam. O prompt do médico não mudou.

| Caso | Especialidade | Condição | Fonte (PMCID) |
|---|---|---|---|
| g1_011 | Dermatologia | Urticária aguda espontânea | PMC13466004 |
| g1_012 | Pediatria | Otite média aguda (3 anos) | PMC7228535 |
| g1_013 | Ginecologia | Candidíase vulvovaginal | PMC10455317 |
| g1_014 | Cardiologia | Fibrilação atrial de início recente | PMC11666470 |
| g1_015 | Gastroenterologia | Doença do refluxo | PMC8341192 |
| g1_016 | Neurologia | Enxaqueca sem aura | PMC11409395 |
| g1_017 | Ortopedia/reumatologia | Osteoartrite de joelho | PMC8001498 |
| g1_018 | Otorrino/alergia | Rinite alérgica sazonal | PMC10623625 |
| g1_019 | Endocrinologia | Hipotireoidismo primário | PMC12518491 |
| g1_020 | Urologia | Hiperplasia prostática | PMC7109311 |

Construção: `scripts/build_g1b_cases.py` (mesmas regras do lote A: história e resultados escritos por nós, itens de conduta só com citação conferida no texto). Fontes de qualidade desigual: g1_016 vem de metanálise em rede (sem recomendação formal), g1_017 de revisão só farmacológica (exercício e perda de peso não pontuam), g1_020 de revisão de diretrizes (2 itens). O g1_012 (3 anos) tem a queixa na voz da mãe e o paciente simulado responde como mãe, mas o modelo de abertura do desk acrescenta "(I am a 3-year-old man.)" à primeira mensagem: limite de construção do caso, igual nas duas rodadas.

**Execuções (nenhuma repetida dentro da mesma variante):**
- `glm_g1b`: a pausa de exposição **ainda estava ativa** em 8 de 10 encontros (defeito do lançador: o patch pegou a subclasse criada por `desk.install()`, que herda a regra). Não vale como condição "sem pausa"; fica registrada como execução invalidada pela condição, custo contado (US$ 0,133). Resultado dessa rodada: 9/10 diagnósticos, g1_017 terminou como falha de formato de ferramenta (limite de tentativas).
- `glm_g1c`: pausa desligada de fato (0 eventos `exposure_pause` nos 10 traces; confirmado também que o `glm_g1b` tinha o evento). Esta é a rodada analisada. 10/10 diagnósticos corretos pelo juiz; conduta: 7 adequada, 2 parcialmente, 1 inadequada; custo US$ 0,147.
Livro-razão G1 = conta = US$ 0,428036370 de US$ 1,50 (lote A, repetição do g1_010, `glm_g1b` e `glm_g1c`).

Limites adicionais: dez casos por lote não dão intervalo de confiança; o juiz de conduta lê o texto do diagnóstico e o plano, não a conversa (aceitou "febre >39 C" inventada pelo médico no g1_012 para justificar antibiótico); o juiz deu veredictos opostos ao mesmo comportamento (antibiótico imediato no g1_012: "inadequada" no `glm_g1b`, "adequada" no `glm_g1c`). Revisão médica pendente.
