# Fluxo atual do v3.2 (escalonamento), 05-10-2026

Comando: `python3 scripts/run_v3.py --model z-ai/glm-5 --min-exchanges 2 --exam-first --immediate-results --cascade --v32`. Padrões do `--v32`: mapa e arbitragem pelo Sonnet 5.5, triagem do JEF com corte 0,86, auditoria de 20%, gatilho de exame definitivo, resgate de falhas. Claude pela assinatura Pro (CLI). Opus só com `--map-model opus` ou `--adjudicator opus`.

## 1. Início do encontro
- O paciente simulado é o Sonnet 5.5 com as regras estritas; ele recebe só o registro do caso (sem exames, sem diagnóstico).
- O médico (GLM-5) recebe a queixa e os **achados do exame físico inicial** na primeira mensagem.
- **Mapa da consulta** (1 chamada curta do Sonnet, vendo só a queixa e o exame físico, nunca a história, os exames nem a referência): urgência (`emergency`, `urgent`, `routine`), exatamente 5 diagnósticos diferenciais, no máximo 4 exames decisivos (2 nomes cada), 4 perguntas-chave e 4 passos. O mapa vai na primeira mensagem do médico.
- Se a urgência for **emergência**, os exames abrem desde o início (sem número mínimo de trocas). Nos demais casos, os exames só abrem depois de 2 trocas com o paciente.

## 2. Entrevista do GLM-5 (até 10 turnos)
- Resultados de exame voltam **na hora**, um por exame pedido: achado, "já pedido antes", "não disponível", `wrong_tool` (diz qual ferramenta é a certa) ou `requires_prior_procedure` (diz qual procedimento pedir antes, por exemplo pericardiocentese antes da angiografia coronariana, ou laparoscopia/laparotomia antes de biópsia no abdome).
- Analitos que estão dentro de um exame agrupado (bilirrubina em "Hemolysis studies") voltam direto, sem depender do associador.
- Antes de admitir, se algum exame decisivo do mapa não foi pedido, o médico recebe **um** lembrete. Depois a admissão vira só a **proposta**.
- Se o GLM-5 falhar de forma operacional (argumentos de ferramenta inválidos duas vezes, limite de turnos), vai direto ao passo 5 (resgate).

## 3. Triagem pelo JEF (cerca de US$ 0,001)
O JEF lê a transcrição e a proposta e pontua: sustentado pelos achados, causa específica nomeada, alternativas relevantes não excluídas, e "falta um exame definitivo". Escore combinado ≥ 0,86 e "falta exame definitivo" < 0,5: **aceita a proposta**, ninguém mais é chamado. Em 20% dos aceites (sorteio fixo por encontro) a revisão do passo 4 roda mesmo assim, como auditoria.

## 4. Revisão às cegas e arbitragem (só quando a triagem não aceita)
1. **Sonnet às cegas**: vê o mapa e a transcrição, **não vê a proposta**. Dá diagnóstico, confiança e o que falta (perguntas e exames).
2. Se pediu algo, roda **uma rodada** de pedidos: o paciente responde, os exames são executados, e se um pedido cai em "ferramenta errada" ou "exige procedimento antes", a própria rodada reenvia à ferramenta certa ou faz o procedimento antes (e diz isso). Depois o Sonnet lê de novo.
3. O JEF compara o diagnóstico do Sonnet com a proposta ("mesma doença?", tolerante a detalhe extra). Se forem a mesma doença e a confiança for ≥ 0,70: **fica o diagnóstico do Sonnet**.
4. Se não concordarem, o **árbitro (Sonnet)** vê a transcrição e os dois candidatos e escolhe um ou dá o próprio; pode usar a rodada de pedidos se ela ainda não foi usada.

## 5. Resgate de falha
Se o GLM-5 não concluiu, o Sonnet às cegas assume a partir da transcrição até ali (com uma rodada de pedidos) e o diagnóstico dele é o final.

## 6. Juiz
Gemini 3.1 Pro, temperatura 0, com o critério do caso 009 ("obstrução por stent migrado" vale; decisão do usuário, revisão médica pendente). Se o diagnóstico final difere da proposta, a proposta também é julgada à parte, para medir o que o escalonamento mudou.

## Quem custa o quê (v3.2b, equivalente de API por caso)
Mapa US$ 0,015; entrevista do GLM-5 mais associador cerca de US$ 0,013; JEF US$ 0,001; cada chamada do Sonnet de revisão cerca de US$ 0,048 (em geral duas por caso revisado). Aceitos pelo JEF custam cerca de US$ 0,03; revisados, US$ 0,10 a 0,24.

## Estado dos testes
Rodado nos 10 casos, uma vez por caso: v3.2b (9/10, US$ 0,089 por encontro) e v3.2c, com as correções (dica `wrong_tool`, auto-resolver de pré-requisito na rodada do revisor, instrução de pedir também a imagem da lesão): **10/10, US$ 0,070 por encontro**. O caso 001 passou a acertar já na primeira camada, graças à dica de ferramenta e aos pré-requisitos de procedimento.
