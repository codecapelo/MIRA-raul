# Resultados de três repetições

150/150 encontros terminais. Avaliação exploratória por juiz LLM; revisão médica pendente.

| Modelo | Corretos/julgados | Falhas operacionais | Casos corretos em 3/3 | Custo dos encontros US$ |
|---|---:|---:|---:|---:|
| openai/gpt-oss-120b | 10/25 | 5 | 2/10 | 0.207174 |
| z-ai/glm-4.5-air | 19/29 | 1 | 4/10 | 0.121012 |
| z-ai/glm-5 | 20/30 | 0 | 5/10 | 0.468473 |
| qwen/qwen3.5-397b-a17b | 19/30 | 0 | 4/10 | 1.094453 |
| openai/gpt-5.2 | 23/30 | 0 | 6/10 | 2.251417 |

Custo global reconciliado: US$4.274237323, incluindo pilotos e interrupções. Saldo: US$15.725762677.

“Corretos em 3/3” mede estabilidade do julgamento contra referência; não equivale à concordância semântica entre os três diagnósticos nem ao ConsistencyDx original. Falhas operacionais não são julgamentos negativos. As três repetições do mesmo caso são dependentes; a unidade amostral é o caso (10), não150 pacientes. Não inferir superioridade clínica desses números.

A comparação histórica e as categorias da primeira rodada permanecem em summary.md; sua métrica lexical não é equivalente ao juiz atual. Traces originais e978 arquivos históricos preservados por SHA-256.
