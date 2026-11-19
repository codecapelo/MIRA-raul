# v6.3: comparação de revisores com o médico congelado — resultado (18-11-2026)

Protocolo e regra de decisão (declarados antes de rodar): `reports/v63_reviewer_protocol.md`; condição congelada `config/frozen/v63.json` (Qwen entrou por `scripts/run_v63_qwen.py`, que não altera arquivos congelados). **8 casos conhecidos (5 públicos 001–005, 3 fechados 011, 017, 018, estes só em agregado), uma execução por caso e revisor, médico GLM 5.3 Flash congelado por caso, juiz LLM, sem revisão médica, rubrica de 1 a 5 em rascunho.** Os 8 casos foram escolhidos por terem errado antes (efeito de seleção). Sonnet 5.5 entrou depois (19-11-2026), com o mesmo método e a mesma condição (`scripts/run_v63_sonnet.py`); o paciente simulado também é o Sonnet 5.5 em todos os braços. Opus = os próprios encontros-fonte (fix3; o 004 vem de uma segunda execução porque a primeira falhou por limite de palavras).

## Resultado (tempo e custo por encontro, medidos a partir da entrada do primeiro revisor)

| Revisor | Juiz binário | Falhas de validação | Nota 1–5 (juiz 1 / juiz 2) | Fase do revisor, mediana (p90) | Chamada, mediana (p90) | Equivalente em API dos revisores | Gasto novo OpenRouter |
|---|---:|---:|---:|---:|---:|---:|---:|
| Opus 5.5 (Claude, assinatura) | 8/8 | 1 (primeira execução do 004) | 4,88 / 4,88 | 103 s (120) | 22 s (27) | US$ 0,27 | US$ 0,015 |
| Sonnet 5.5 (Claude, assinatura, effort high) | 6/8 (7 terminais) | 1 (caso 018) | 4,86 / 4,71 (7 encontros) | 91 s (108) | 21 s (30) | US$ 0,17 | US$ 0,013 |
| Sol 6.2 (Codex, assinatura) | 8/8 | 0 | 4,62 / 4,62 | 162 s (234) | 44 s (66) | US$ 0,13 (est.) | US$ 0,014 |
| Astra 6.2 (Codex, assinatura) | 8/8 | 0 | 4,50 / 4,38 | 104 s (143) | 23 s (36) | US$ 0,36 (est.) | US$ 0,014 |
| Kimi K3.1 Pro (OpenRouter, pago) | 8/8 | 0 | 4,75 / 4,38 | 422 s (681) | 130 s (284) | US$ 0,13 (cobrado) | **US$ 0,144** |
| Qwen 4 Max (OpenRouter, pago) | 6/8 | **2** (confiança fora de 0–1, 001 e 017) | 4,83 / 4,67 (6 encontros) | 198 s (360) | 65 s (103) | US$ 0,06 (cobrado) | US$ 0,066 |

Intervalo de Wilson 95% do juiz binário: 8/8 = 0,68–1,00; 6/8 = 0,41–0,93. O equivalente em API do Codex é **estimativa** (tokens × preço de lista do OpenRouter de 18-11-2026, com o cache que o CLI informa: 21% da entrada do Sol e 30% da do Astra; o CLI informa o cache só em parte, então uma chamada real de API poderia custar menos). Uma versão anterior deste relatório tratou toda a entrada como sem cache (Sol 0,15 e Astra 0,48); foi corrigido. O do Claude vem do CLI; Kimi e Qwen são `usage.cost` cobrado. As chamadas de Sol e Astra tiveram US$ 0 no OpenRouter (conferido nos traces). O Codex CLI não atesta o modelo servido (`requested_only`).

## Leitura
- **Acerto não separa os quatro primeiros** (8/8 com n = 8; um caso de diferença seria indistinguível). O Qwen perdeu dois encontros por falha de validação do próprio revisor no estágio final, sem retentativa.
- **Regra de decisão aplicada:** entram só braços sem falha operacional (Sol, Astra, Kimi); empate no acerto; desempate pela nota média (Sol 4,62; Kimi 4,56; Astra 4,44), depois tempo (Astra 104 s, Sol 162 s, Kimi 422 s) e equivalente em API (Sol 0,13 contra Astra 0,36). A regra escolhe o **Sol 6.2**; a vantagem de nota sobre o Astra é de 1 ponto em 2 casos (ruído com este n) e o Astra é 36% mais rápido.
- **Sonnet 5.5:** aceitou 6 dos 8 pelo juiz binário (a primeira rejeição desta comparação foi o público 003: acertou a entidade, mas o texto final trocou a sepse intra-abdominal secundária por hipovolemia e pneumonia; nos juízes de 1 a 5 recebeu 4 e 4) e falhou a validação do estágio final no 018 (item vazio na lista de próximos passos), sem retentativa. É rápido (91 s) e tem nota alta, mas pela regra fica fora (falha operacional) e com 6/8 não empata no acerto.
- Opus tem a maior nota e a mesma velocidade do Astra, mas a regra o excluiu por uma falha de validação na primeira execução do 004; vale repetir.
- Kimi é o único com custo real relevante (US$ 1,15 nos 8) e o mais lento; Qwen tem custo menor, mas dois estouros de validação.

## Operação
Gasto adicional desta fase no ledger próprio US$ 2,276 (de 2,823 para 5,099; teto 5,30, `reports/v6_qwen_cap_raise_450usd.json`, `..._500usd.json` e `..._530usd.json`; o braço do Sonnet custou US$ 0,152, dos quais US$ 0,048 são o juiz Gemini das notas, atribuído por diferença estável da conta, com cerca de US$ 0,009 sem origem conhecida), 1.806 chamadas todas liquidadas, ledger = conta (delta). Um HTTP 429 do OpenRouter no juiz do Sol 005 foi reconciliado com 3 snapshots estáveis, a diferença da conta (US$ 0,0125, parte dela anterior ao piloto e sem origem conhecida) ficou numa linha não atribuída e o juiz foi reemitido uma vez (`reports/v63_sol_429_reconciliation_2026-11-18.json`). Juiz Gemini das notas (US$ 0,2104 por diferença estável da conta, 38 notas) atribuído em linha própria. Os dois estouros do Qwen e a falha do Opus (limite de 179 palavras) são falhas dos próprios revisores, mantidas no denominador.

## Limites
Casos conhecidos, uma execução, sem testes de significância; a fase do médico é congelada mas o seguimento (pedidos ao paciente) depende do revisor; juiz LLM mede o texto diagnóstico; rubrica em rascunho; revisão médica pendente; contaminação do Qwen e de outros nos casos fechados não foi testada.

## Repetição do Sonnet 5.5 nos casos 003 e 018 (19-11-2026)
A pedido, o Sonnet foi repetido do zero nos dois casos em que a primeira execução não foi aceita (003 rejeitado; 018 falha de validação), com a mesma fase do médico congelada e a mesma condição (`scripts/run_v63_sonnet.py --rep 2`, variante `glm_sonnet_v62fix3iso2`; a primeira execução continua registrada e é a que entra na tabela acima).

| Caso | Execução 1 | Execução 2 |
|---|---|---|
| 003 (público) | juiz rejeitou; notas 4 / 4; texto final sem a sepse intra-abdominal secundária; fase 99 s | **juiz aceitou**; notas 5 / 4; texto final cita "peritonite urinária"; fase 80 s |
| 018 (fechado, só números) | falha de validação do estágio final (item vazio em `next_steps`); fase 104 s sem desfecho | **terminal e aceito**; notas 5 / 5; fase 104 s |

Os dois resultados **não se mantiveram**: com a mesma conversa do médico, uma segunda execução do mesmo revisor deu o desfecho oposto nos dois casos. Isso mostra a variação do próprio revisor (o texto final do 003 depende de uma frase) e de formato (a falha do 018 foi pontual). Com as duas execuções, o Sonnet teria 8 de 8 aceitos na melhor combinação e 6 de 8 na primeira; como a regra declarada conta uma execução por caso, a tabela principal não muda. Equivalente em API por encontro: 003 US$ 0,16 e 0,10; 018 US$ 0,23 (falhou) e 0,18. Gasto novo no OpenRouter das duas execuções US$ 0,030 mais US$ 0,016 de juiz das notas por diferença estável da conta (cerca de US$ 0,005 sem origem conhecida); ledger = conta US$ 5,143, teto 5,50 (`reports/v6_qwen_cap_raise_550usd.json`). Vale repetir os outros revisores com a mesma regra antes de concluir qualquer ordem entre os que empatam em 8/8.
