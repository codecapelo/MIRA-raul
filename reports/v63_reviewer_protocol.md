# v6.3: comparação de revisores com o médico congelado — protocolo (18-11-2026)

Decisão do usuário (18-11-2026): consolidar o fix3 como parte da versão nova, isolar o revisor, comparar **Sol 6.2, Astra 6.2 e Kimi K3.1 Pro** (o Opus 5.5 entra com as execuções-fonte), avançar aos poucos vigiando o custo, escolher o revisor **antes** de ampliar os casos, usar a assinatura sempre que possível e informar o equivalente em API. Fora desta fase: mais casos, ablação de papéis (revisor da primeira leitura diferente do final; o ganho de custo não compensa, já testado), contaminação por memória do artigo.

## Condição v6.3
Balcão v6.2 (aviso verdadeiro de resultado posterior; resultados de acompanhamento liberados aos revisores após a admissão; entrega do registro quando o revisor pede variante mais específica) + correção genérica de prompt do revisor **fix3** (`src/mira_v6/reviewer_fix3.py`, sem conteúdo de caso) + frase final sobre a anormalidade verificada. Médico GLM 5.3 Flash, paciente Sonnet 5.5 (assinatura), associador estrito, juiz binário Gemini 3.1 Pro, esforço high nos revisores Codex. Código em `scripts/run_v63_reviewers.py`; congelamento em `config/frozen/v63.json` (`scripts/freeze_condition.py --name v63 --check`). Alterar qualquer arquivo listado cria condição nova.

## Isolamento do revisor
A fase do médico (abertura, turnos, respostas do paciente, balcão, proposta) termina antes do primeiro `fast_review_input` e não depende do revisor. Para cada caso ela é copiada **uma vez** de um encontro-fonte (`SOURCES`: os encontros do fix3 com o Opus) para o log do braço novo (`src/mira_v6/frozen_doctor.py`); o executor retoma esse log: médico, associador e paciente da parte copiada são reproduzidos das respostas armazenadas (hash do payload conferido, **sem gasto novo**) e só os estágios do revisor rodam ao vivo (primeira leitura, seguimento com paciente/balcão, leitura final), mais associador e juiz do que vier depois. Assim todos os revisores veem a mesma conversa e a variação do médico sai da comparação. O braço Opus são os próprios encontros-fonte; não precisa de execução nova.

Limites: (1) a parte do médico vem de encontros em que o Opus revisou depois; isso não a altera, mas os 8 casos foram escolhidos por terem errado antes (efeito de seleção) e 3 são fechados; (2) um uso por caso e repetição, sem retentativa; falha de revisor (inclusive limite de palavras) conta como falha do braço; (3) o seguimento depende do revisor (o que ele pede muda as respostas do paciente), então só a fase do médico é congelada.

## Medidas (por braço, por caso; `scripts/v63_report.py`)
1. **Acerto**: juiz binário (primário); proposta do médico é igual em todos os braços por construção.
2. **Nota 1 a 5** (`scripts/likert_run.py`): juiz 1 = Gemini 3.1 Pro; juiz 2 de família diferente da que escreveu o diagnóstico final (Claude Sonnet 5.5 para Codex e Kimi; GPT-6.1 Sol para o Opus). Rubrica em rascunho, sem validação médica.
3. **Tempo da fase do revisor**: do primeiro `fast_review_input` ao fim; chamadas por estágio (mediana, p90), seguimento (paciente + balcão) e juiz.
4. **Custo**: (a) gasto novo no OpenRouter (associador, juiz e, no Kimi, o revisor) vindo de `usage.cost`; (b) **equivalente em API** dos revisores por assinatura = tokens × preço de lista (Claude: valor informado pelo CLI; Codex: tokens do `cli_call` × preço da lista do OpenRouter de 18-11-2026, estimativa); (c) tokens de entrada/cache/saída e número de chamadas, como medida de uso da cota.
5. **Falhas de validação** do revisor (por exemplo limite de 179 palavras no raciocínio).

## Regra de decisão (declarada antes de rodar)
Entram só braços sem falha operacional. Escolher o revisor com **maior acerto pelo juiz**; empate (diferença de até 1 caso em 8, o que não é distinguível) decide pela **maior nota média 1–5**, depois pelo **menor tempo mediano da fase do revisor**, depois pelo **menor equivalente em API**. Nenhuma afirmação de superioridade estatística com n = 8; repetições (`--rep`) só se o desempate ficar apertado.

## Etapas e controle de custo
A) piloto: casos 003 e 005 (públicos, curtos) nos três braços, para ver custo e funcionamento do isolamento; B) restantes seis casos por braço; C) repetições, se necessário. Teto do ledger próprio US$ 4,50 (subiu de 3,00, `reports/v6_qwen_cap_raise_450usd.json`), nunca além do crédito da conta; subir de novo só com autorização e registro. Traces em `runs/v5/v6_qwen/` (fora do Git); casos fechados só como números.
