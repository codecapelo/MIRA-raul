# v3 com exame junto da queixa: N=1 e N=2, Qwen3.8 Max 0902 e GLM-5 (05-10-2026)

Mudança: os achados do exame físico inicial entram na primeira mensagem do médico (`--exam-first`, sufixo `_xf`); o paciente nunca os vê; a ferramenta de exame devolve só um aviso de que já foram fornecidos; a trava de exames passa a exigir apenas N trocas. Demais regras da v3 inalteradas (paciente Sonnet 5.5 com regras estritas, resultado só após a próxima troca, resposta por exame, juiz Gemini 3.1 Pro). 10 casos × 1 execução por variante, sem JEF na guarda. **Julgamento por LLM, sem revisão médica; uma execução por caso não separa o efeito de N do ruído de amostragem.**

## Resultado
| Variante | Corretos | Custo OpenRouter | Trocas | Turnos | Chamadas do médico | Tokens de entrada | Erros |
|---|---:|---:|---:|---:|---:|---:|---|
| Qwen N=3 (exame por ferramenta, rodada anterior) | 8/10 | US$ 0,898 | 4,8 | 5,8 | 10,0 | 53 mil | 001, 009 |
| **Qwen N=1, exame junto** | 8/10 | **US$ 0,793** | 3,3 | 4,3 | 6,7 | 38 mil | 002, 009 |
| **Qwen N=2, exame junto** | **9/10** | US$ 0,819 | 4,1 | 5,1 | 7,7 | 42 mil | 001 |
| **GLM-5 N=1, exame junto** | 5/10 | **US$ 0,164** | 4,1 | 5,1 | 7,4 | 19 mil | 001, 002, 004, 009, 010 |
| **GLM-5 N=2, exame junto** | 7/10 | US$ 0,183 | 4,7 | 5,7 | 8,4 | 23 mil | 001, 002, 009 |
Referência antiga (v1/v2, juiz Pro): Qwen 21/30 (70%) a US$ 0,044 por encontro; GLM-5 19/30 (63%) a US$ 0,016.

- **Pedidos bloqueados:** Qwen 6,2 por encontro (N=3) → 0,2 (N=1) e 1,9 (N=2); GLM-5 0,0 e 0,2.
- **Custo e N:** tirar a trava de 3 trocas e dar o exame no início reduziu as chamadas do médico em 23% (N=2) a 33% (N=1) e os tokens de entrada em 21% a 28%, mas o custo só caiu 9% a 12% (US$ 0,898 → 0,793/0,819), porque o custo do Qwen é dominado pelo contexto reenviado e pelo raciocínio (cerca de 4 mil tokens por encontro). O que dobrou o custo em relação às runs antigas (US$ 0,044) é a conversa mais longa em si, não só a trava.
- **Modelo é a alavanca maior de custo:** o GLM-5 custa cerca de 1/5 do Qwen por encontro (US$ 0,018 contra 0,08), com 5 a 7 acertos em 10 contra 8 a 9. Custo por acerto: GLM-5 N=2 US$ 0,026; Qwen N=2 US$ 0,091.
- **Ruído:** o mesmo Qwen alterna acerto e erro nos casos 001, 002 e 009 entre variantes (001: errou/acertou/errou; 009: errou/errou/acertou); com uma execução por caso, as diferenças entre N=1, 2 e 3 (8, 8 e 9 de 10) não são distinguíveis. O caso 009 continua errado em 5 das 6 variantes v3 e em todas as de GLM-5.

## JEF como verificador de diagnóstico (60 encontros v3, sem referência)
Para cada encontro (`scripts/jef_verify.py`, `results/jef_verify_v3.json`) o JEF recebe só a conversa, os achados vistos pelo médico, o diagnóstico final e a justificativa, e pontua: "sustentado pelos achados", "nomeia causa específica" e "alternativas relevantes não excluídas".
- AUC contra o veredito do juiz Pro (15 errados em 60): sustentado 0,80; alternativas (invertida) 0,85; combinado 0,85; causa específica 0,53 (sem poder discriminativo: quase tudo "sim").
- Escalonar quando o escore combinado < 0,85 sinaliza 16/60 (27%) e pega 10 dos 15 diagnósticos errados (6 corretos escalados à toa); < 0,80 sinaliza 22% e pega 8/15. Os erros que ele não pega são sobretudo o caso 009 com escore alto (0,83 a 0,89): o médico se convence com a justificativa e o JEF concorda.
- **Limites:** 60 encontros não são independentes (os mesmos 10 casos, 6 variantes); limiares escolhidos nos mesmos dados; juiz único. Serve como sinal de triagem para testar, não como prova.
- Custo do JEF nesta etapa: cerca de US$ 0,02 de entrada documentada.

## Gasto
Ledger e conta: US$ 11,957 → 13,916 (US$ 1,96 nas 4 variantes), iguais em 3 snapshots (`credits_v3_xf_final_*.json`). Restam cerca de US$ 4,08 do teto de US$ 18 (a chave tem limite de US$ 20). Duas chamadas do Qwen interrompidas ao parar a rodada anterior foram reconciliadas (US$ 0,019244 não atribuível a chamada; `v3_killed_reconciliation.json`).
