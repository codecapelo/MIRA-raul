# v4 — condição experimental da assinatura, 08-10-2026

Base: Claude v3.7, commit c1d3270. Os defaults e traces das versões anteriores ficam preservados. Esta condição não é uma repetição equivalente ao v3.6: mudou transporte/modelos de paciente, mapa, médico e revisores, a política e a fidelidade dos componentes.

## Implementação congelada
- Médico, paciente, mapa e revisor cego: gpt-6.1-sol pela assinatura ChatGPT/Codex, esforço medium. Astra adjudica/escalona. Alternativa GLM-5 disponível, sempre com braço separado. Sem JEF externo.
- Codex em diretório temporário vazio, config do usuário ignorada, sem ferramentas locais/web/apps/memória. Schema JSON emula apenas as ferramentas da simulação. Identidade servida não confirmada quando o CLI não a informa; modelo solicitado é registrado. Amostragem da API não é equivalente à assinatura.
- Matcher estrito Gemini Flash Lite e juiz Gemini Pro pela OpenRouter com rotas fixas, usage.cost e reservas conservadoras. O juiz só recebe referência após o encontro. Mesma exceção de critério do caso009 do v3.
- Sempre revisão cega; diagnóstico proposto não aparece ao revisor, mas o mapa inicial aparece e pode influenciá-lo. Concordância semântica não é prova de correção.
- Componentes só devolvem conteúdo literal da fonte: não basta coincidir números para aceitar uma conclusão qualitativa.
- Unidades artificiais de exame: primeiro nível1, direcionado5, caro/invasivo15. Cada observação-fonte disponível primeiro entregue conta uma vez, inclusive revisores. Componentes de um mesmo painel compartilham uma cobrança. Indisponíveis/repetidos não cobram. Procedimentos/fontes distintos contam separadamente. Não são preços reais.
- Limite8 exames não críticos/não endossados por turno; fila também respeita o limite no turno seguinte. Lactato desidrogenase não recebe a exceção de urgência do lactato; endosso exige identidade específica.
- Conversa antes da admissão inclusive urgência; anamnese e exame inicial, resultados imediatos, fala formatada sem um LLM extra para reescrever.

## Orçamento e execução
Autorização atual do usuário: US$5 adicionais. Ledger exclusivo runs/v4/budget.sqlite, compartilhado entre braços v4, incluindo matcher/juiz/falhas. Ledger histórico não é editado. Saldo conta anterior confirmado18.965410033. Não há chamadas OpenRouter para modelos OpenAI. Tokens da assinatura contam separadamente; custo monetário da assinatura desconhecido, e não preço de API inventado.

`PYTHONPATH=src python3 scripts/run_v4.py` é dry-run. `--execute --max-cases 2` despacha somente os dois primeiros pendentes sem mudar o manifesto de10; depois `--execute` continua os restantes. Sem retentativa automática em erro. Não trocar commit durante execução.

## Critério de validação
Testes de regressão e integração precedem chamadas pagas. Dez casos públicos já usados no desenvolvimento são teste exploratório de regressão, não holdout. Relatar conclusão operacional, decisões do juiz, custo API, unidades de exames, tokens e incertezas separadamente. 10/10 ou20/20 não garantem acurácia clínica100%; revisão médica cega segue pendente.
