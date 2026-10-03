# Avaliação determinística

Execute na raiz de `benchmark/`:

```bash
python3 -B -m evaluation.metrics validate-cases --root .
python3 -B -m evaluation.metrics validate-cases --root . --require-signoff
python3 -B -m evaluation.metrics validate-traces --root .
python3 -B -m evaluation.metrics summarize --root . --write
python3 -B -m unittest evaluation.test_metrics -v
```

`validate-cases` confere IDs, campos obrigatórios, fatos únicos, proveniência de todos os fatos, hash do PDF, estrutura do rubric e identificadores explícitos de fonte no packet. Não verifica fidelidade clínica nem spoilers semânticos. `--require-signoff` reprova gabaritos e rubrics ainda não aprovados por médico. `validate-traces` confere sequência, identidade da run, tipos de evento e pareamento de chamadas e resultados. Tentativas de ferramentas inexistentes ficam no trace como observações e entram na contagem de erros.

`summarize` calcula contagens de ações, fatos novos, diagnóstico publicado por **correspondência textual exata** com sinônimos previamente congelados, disposição publicada, uso de tokens, latência, conclusão e consistência entre repetições. A correspondência textual é apenas um indicador provisório; uma formulação clinicamente correta com palavras diferentes pode não coincidir. A média de passos até diagnóstico usa somente runs que mencionaram a string, e a taxa de menção informa a censura. `results/summaries/*.json` declara `review_state: pending` e mantém adequação de conduta, segurança, alternativas diagnósticas, omissões críticas e concordância com guideline como `requires_physician_adjudication` até a revisão médica.

`diagnosis_aliases.json` define uma segunda leitura provisória, versionada **fora dos casos congelados**. Cada caso tem conceitos obrigatórios, expressos por sinônimos/regex, que devem aparecer na mesma hipótese diagnóstica; conceitos secundários medem granularidade sem mudar o acerto central. O relatório separa `published_diagnosis_exact_match` de `published_diagnosis_concept_match`, incluindo top-3/top-5 e passos até a primeira menção. O caso 001 demonstra o motivo: a formulação de Claude no trace clínico não coincide literalmente com o artigo, mas contém infecção, pseudoaneurisma coronário, complicação do stent e tamponamento. Essa leitura lexical continua sujeita a falso positivo/negativo e **não substitui** a classificação do médico.

Nenhum LLM é usado como juiz de segurança clínica. O formulário e a política de dupla revisão estão em `adjudication.md`.
