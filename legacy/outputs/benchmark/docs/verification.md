# Verificação do painel congelado

Executada em 26-09-2026, após o término dos três runners. Corpus `mvp10_v3_2026-09-26`, protocolo `mvp10_closedbook_v5_2026-09-26` e avaliador `evaluation-v2`.

| Verificação | Resultado |
|---|---|
| Casos estruturados | 10/10 válidos, zero erros; assinatura e revisão semântica médicas pendentes |
| Traces principais | 150/150 terminalmente válidos, zero erros de schema; 30 por modelo e três por caso/modelo |
| Duplicatas | Nenhuma combinação modelo × caso × repetição duplicada no painel principal |
| Tentativas interrompidas | Uma tentativa Sol do caso 002 por erro de provider próximo ao limite da conta, preservada em `results/incomplete/`; retry válido no painel; pilotos anteriores em `results/exploratory_*/` |
| Testes automatizados | 15 passaram (`python3 -B -m unittest discover -s . -p 'test_*.py'`) |
| Análise | 150/150 em `results/summaries/REPORT.md` e `exploratory_analysis.json`; cinco resumos por modelo |
| Revisão médica | 150 packets cegos, 450 linhas de decisão (primeira, segunda, consenso), 6.867 linhas de ação e 3.420 oportunidades; nenhuma decisão clínica preenchida |
| Integridade | Hashes do avaliador em `docs/evaluation_freeze_manifest.json`; 150 hashes de traces em `results/trace_manifest.json`; corpus e protocolo com manifests separados |
| Autenticação | Assinaturas Codex e Claude, sem API paga; crédito de reset Codex preservado |

Para reproduzir a checagem sem executar novos casos, usar `python3 -B -m evaluation.metrics validate-cases --root .`, `python3 -B -m evaluation.metrics validate-traces --root .` e `python3 -B -m unittest discover -s . -p 'test_*.py'`. Os valores clínicos diagnósticos são triagens lexicais, e segurança/adequação aguardam adjudicação médica. O braço Sol não prova isolamento estrito de ferramentas internas da CLI; ver `docs/safety.md`.
