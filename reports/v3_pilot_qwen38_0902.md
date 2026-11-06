# Rodada-teste v3 — Qwen3.8 Max 0902, 10 casos × 1 execução, sem e com guarda do JEF (05-10-2026)

Condição nova (v3, ver `v3_design.md`): paciente fixo Sonnet 5.5 com regras estritas, exames bloqueados até 3 trocas com o paciente e exame físico, resultado só após a próxima troca, resposta por exame pedido, juiz Gemini 3.1 Pro (temp 0). Dois braços, mesmo commit e mesmos casos: **A** sem JEF; **B** com a guarda JEF (se a resposta do paciente for marcada como invenção ≥ 0,30 ou deriva ≥ 0,50, o Sonnet é chamado uma vez de novo e a segunda resposta substitui a primeira). Uma execução por caso e por braço; temperatura do médico 0,6 (amostragem). **Julgamento por LLM, sem revisão médica; n=10 por braço não permite afirmar melhora.**

## Resultado
| Condição | Corretos (juiz) | Corretos sob a regra estrita (007/002/009) | Encontros com fala ao paciente | Trocas médias | Custo OpenRouter |
|---|---:|---:|---:|---:|---:|
| Runs antigas (v1/v2), juiz original, 30 enc. | 24/30 (80%) | — | 2/30 (7%) | 0,07 | US$ 0,044/enc. |
| Runs antigas rejulgadas com o Gemini Pro | 21/30 (70%) | — | 2/30 | 0,07 | — |
| **v3 A (sem JEF)** | **8/10** | 8/10 | 10/10 | 4,8 | US$ 0,898 (0,090/enc.) |
| **v3 B (com JEF)** | **8/10** | 8/10 | 10/10 | 4,8 | US$ 0,980 (0,098/enc.) |

- **Mesmos dois erros nos dois braços:** casos 001 e 009 (o 001 já era 1/3 nas runs antigas; o 009 era 1/3). O caso 009 também falha na regra estrita nos dois braços (sem Meckel).
- **Casos que melhoraram em relação ao Qwen antigo:** 002 (1/3 → acertou nos dois braços) e 007 (0/3 pelo juiz Pro → acertou nos dois, com pembrolizumabe citado). Compatível com o médico agora conversar e com a correção da bilirrubina em "Hemolysis studies", mas com um encontro por caso não dá para atribuir causa.
- **Comparação justa:** a referência correta é a das runs antigas rejulgadas com o mesmo juiz (21/30 = 70%), contra 16/20 = 80% da v3 (os dois braços somados, que não são independentes). A diferença está dentro do ruído de 10 encontros por braço.
- **Mudança comportamental, robusta:** de 2 de 30 encontros com fala ao paciente (0,07 trocas) para 10 de 10 (4,8 trocas, 5,8 turnos). O médico ainda tentou pedir exame antes da hora: 62 respostas "Investigation locked" no braço A e 72 no B (cerca de 6 a 7 por encontro); a trava absorve o impulso sem gastar turno. Pedidos de exame efetivos: 71 e 72 (cerca de 7 por encontro).
- **Custo:** o encontro v3 custa cerca de 2× o antigo (US$ 0,09 a 0,10 contra 0,044): contexto maior com mais turnos e o juiz Pro (US$ 0,004). O paciente Sonnet pela assinatura Pro fez 48 falas por braço (e 7 retentativas no B); o consumo do limite não é legível pelo CLI.
- Ledger US$ 9,968 → 11,847 (conta = ledger em 3 snapshots, `credits_v3_pilot_final_*.json`). Restam cerca de US$ 6,15 do teto de US$ 18.

## Guarda do JEF
- 48 checagens no braço B; **7 retentativas** (3 no caso 002, 2 no 005, 2 no 009); sem falhas do JEF; custo do JEF nesta rodada abaixo de US$ 0,01 (total do JEF no projeto: US$ 0,03 de entrada documentada).
- Probabilidade de invenção estimada pelo próprio JEF sobre as 96 falas do paciente (`results/v3_patient_answers_jef_scored.json`): braço A 12/48 (25%) acima de 0,30; braço B, primeira resposta 10/48 (21%) e **resposta entregue 7/48 (15%)**. Das 7 retentativas, 4 caíram bem (ex.: 0,46 → 0,25; 0,43 → 0,26; 0,31 → 0,15), 3 ficaram iguais ou pioraram levemente (0,37 → 0,47; 0,32 → 0,38). Para comparação, o Sonnet com as regras do teste anterior ficou em 2% de invenção avaliada pelo Opus; as duas escalas (JEF no limiar 0,30 e Opus) não são equivalentes e o JEF marca também respostas limítrofes.
- **Leitura:** a guarda funciona como pretendido, mas o efeito é pequeno (cerca de 6 pontos percentuais menos respostas marcadas) e não mudou nenhum resultado diagnóstico nesta amostra. O ganho maior da v3 já vem do paciente com regras estritas.

## Limites
Uma execução por caso por braço; amostragem do médico; juiz único (Pro) sem árbitro Opus nesta rodada; os casos 001 e 009 continuam o principal ponto de erro; custo por encontro dobrou; sem revisão médica. Antes de rodar mais modelos, decidir sobre limite de 10 turnos (os pedidos bloqueados e o atraso dos resultados gastam turnos; o médico usou em média 5,8 turnos de 10, então o limite não foi restritivo neste teste).
