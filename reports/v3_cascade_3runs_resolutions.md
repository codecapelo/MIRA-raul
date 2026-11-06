# Escalonamento v2 em 3 execuções, o que falta nos casos que erram e possíveis resoluções (05-10-2026)

Variante `cas`: GLM-5 conduz (N=2, exame junto, resultados imediatos), triagem do JEF (aceita se o escore combinado for ≥ 0,90), Sonnet 5.5 revisa às cegas com uma rodada de pedidos antes de decidir, Opus 5.5 arbitra quando discorda da proposta; Sonnet e Opus pela assinatura Pro. 10 casos × 3 execuções (as execuções 2 e 3 são desta rodada). **Julgamento por LLM (Gemini Pro), sem revisão médica; 10 casos repetidos não são amostras independentes.**

## Resultado
- **Final correto: 27/30 (90%); propostas do GLM-5: 19/30 (63%).** Por execução: 8/10 (propostas 5), 10/10 (7), 9/10 (7). Dos encontros julgados com proposta errada, 8 foram corrigidos e **nenhum** acerto foi estragado.
- **Os 17 encontros revisados (Sonnet ou Opus) acertaram os 17.** Os 3 erros finais não passaram por revisão: caso 009 aceito pela triagem do JEF nas execuções 1 e 3, e caso 003 da execução 1 (falha de ferramenta do GLM-5, argumentos inválidos duas vezes).
- **Custo real de implantação** (médico, associador, JEF, revisores; sem paciente simulado e sem juiz): US$ 1,832 em 30 encontros = **US$ 0,061 por encontro, US$ 0,068 por caso resolvido** (OpenRouter US$ 0,312 = US$ 0,0104 por encontro; Claude em equivalente de API US$ 1,517 = US$ 0,051 por encontro; JEF US$ 0,003). **Só com o OpenRouter (Claude pela assinatura): US$ 0,0116 por caso resolvido.** O Sonnet custou US$ 1,078 em equivalente de API e o Opus (7 chamadas) US$ 0,439.
- **Por caminho:** triagem do JEF aceitou 12 (10 certos; US$ 0,011 cada), Sonnet aceito 10 (10 certos; US$ 0,061), Opus escolheu o Sonnet 5 (5 certos; US$ 0,161), escolheu a proposta 1 (certo; US$ 0,133), deu diagnóstico próprio 1 (certo; US$ 0,153), falha antes da revisão 1.

## O que falta nos casos que ainda erram
Contagem sobre todos os encontros v3 do GLM-5 e do Qwen que chegaram à admissão, com o exame decisivo identificado pelo trecho do valor na transcrição do médico:
| Caso | Exames decisivos | Pediu algum: certos / errados | Não pediu nenhum: certos / errados |
|---|---|---:|---:|
| 001 | angiografia coronariana, OCT/IVUS, pericardiocentese, exploração do dispositivo | 1 / 2 | 0 / 6 |
| 002 | ressonância cardíaca, estudo eletrofisiológico, cateterismo direito | 3 / 2 | 0 / 4 |
| 009 | laparoscopia/laparotomia diagnóstica (achado operatório: stent no divertículo de Meckel) | 1 / 0 | 0 / 8 |
Sem nenhum exame decisivo, o médico errou em 18 de 18; com algum, acertou 5 de 9. O erro é de coleta (o exame que mostra a causa nunca foi pedido), não de interpretação do que foi visto. Os pedidos do Sonnet às cegas (angiografia ou CT coronariana, ressonância cardíaca, CT de artérias pulmonares, ultrassom/RM abdominal) corrigem os casos 001, 002 e 010. No 009, o gabarito exige o achado operatório (Meckel), que nenhum revisor pediu; o único acerto veio da execução 2 (Sonnet revisou a CT e a proposta mudou).

## Quando o JEF não chama ninguém e o erro passa
No escalonamento, dos 12 aceites 2 estavam errados (os dois do caso 009). Nos 109 encontros v3 com transcrição, a triagem aceitaria 51 e só 2 estavam errados (o caso 009 e um caso 004 do GLM-5). Pontuei quatro perguntas candidatas do JEF sobre esses aceites (`scripts/jef_triage_study.py`, `results/jef_triage_v3.json`):
| Regra extra depois do aceite | Revisões extras | Erros pegos | À toa |
|---|---:|---:|---:|
| "falta exame definitivo" ≥ 0,5 | 5/51 (10%) | 1/2 | 4 |
| "falta exame definitivo" ≥ 0,3 | 8/51 (16%) | 1/2 | 7 |
| "diagnóstico mais específico plausível" ≥ 0,5 | 6/51 (12%) | 0/2 | 6 |
| "causa só inferida" ≥ 0,3 | 7/51 (14%) | 1/2 | 6 |
| aceite mais rígido: escore < 0,93 | 40/51 (78%) | 2/2 | 38 |
| aceite mais rígido: escore < 0,95 | 49/51 (96%) | 2/2 | 47 |
Com 2 escapes nenhum limiar pode ser calibrado; as perguntas novas têm AUC de 0,45 a 0,65 sobre os aceites (a pergunta de alternativas, já usada, tem 0,77).

## Possíveis resoluções
1. **Exigir o exame definitivo antes da admissão** (regra no prompt do GLM-5): previne o erro na origem, custa +1 a 2 pedidos de exame (centavos). Evidência: 0/18 sem exame decisivo contra 5/9 com. *Proposto, não testado.*
2. **Instruir o revisor a pedir achados operatórios e de patologia** quando o diagnóstico nomeia um mecanismo que só cirurgia ou biópsia confirma (caso 009). *Proposto, não testado.*
3. **Auditoria aleatória dos aceites do JEF** (por exemplo 20%) por um revisor às cegas (cerca de US$ 0,034 por revisão no Sonnet, equivalente de API): mede a taxa real de escape e pega uma parte. *Proposto.*
4. **Gatilho extra do JEF "falta exame definitivo ≥ 0,5"**: +10% de revisões e 1 de 2 escapes. *Medido offline, amostra mínima.*
5. **Aceite mais rígido** (escore ≥ 0,93): pega os 2 escapes, mas manda 78% dos aceites para revisão (custo próximo do Sonnet em todos). *Medido offline; caro.*
6. **Revisor às cegas em todos os casos**: teto de acurácia (os 17 revisados acertaram) a +US$ 0,034 por caso hoje aceito pelo JEF. *Proposto.*
7. **Segunda amostra do GLM-5 comparada pelo JEF**: barato (US$ 0,010), mas o GLM-5 erra o 009 do mesmo jeito; nas runs antigas a discordância pegou casos instáveis e deixou passar o erro consistente. *Fraco contra erro consistente.*
8. **Tornar o Opus opcional**: arbitrou 7 casos e foi decisivo em 1 (caso 002, execução 3: o Sonnet às cegas errou e o Opus acertou, julgado à parte pelo Pro). Sem o Opus: 26/30 em vez de 27/30 e −29% do custo dos Claude. *Medido nas 3 execuções.*
9. **Revisão médica do gabarito do caso 009**: se "obstrução por stent migrado" for aceita como conduta correta, deixa de ser erro de acurácia. *Pendente, depende de médico.*

## Gasto
Ledger e conta: US$ 14,815 → 15,181 (US$ 0,366 nas execuções 2 e 3 mais os juízes de apoio), iguais em 3 snapshots (`credits_v3_cascade3_final_*.json`). Restam cerca de US$ 2,82 do teto de US$ 18.
