# Caso externo privado (011): custo real do fluxo v3.2 com Claude via API

> Nota de 06-10-2026: o associador desta execução era o original (generoso). O fluxo v3.3 em diante usa o associador estrito (`reports/v3_strict_exams.md`); com ele este caso passou a errar na primeira rodada e a acertar depois das melhorias.

Execução única, 06-10-2026, commit `0c680e8`. Fluxo v3.2c idêntico ao das 10 rodadas anteriores (GLM-5 → JEF → Sonnet às cegas com mapa → adjudicador → Opus no empate), com **Sonnet 5.5 e Opus 5.5 pelo OpenRouter** (`anthropic/claude-*-5.5`, provedor Anthropic, US$ 2/10 e 4/20 por milhão, raciocínio `high`), em vez da assinatura. O paciente simulado também é Sonnet 5.5 pela API.

Fonte: NEJM Case Records of the MGH, Case 20-2026, DOI 10.1056/NEJMcpc2513544. **Artigo não aberto**: fatos, traces e resultados ficam fora do git (`cases/case_011/`, `runs/v3/*api*/`, `results/v3_*api*`). Conversão manual, sem fatos inventados; o parágrafo "Patient Perspective" (escrito após o diagnóstico) e os resultados de seguimento não foram usados.

## Resultado
- Diagnóstico final: correto pelo juiz (Gemini 3.1 Pro, temperatura 0). A proposta inicial do GLM-5 também estava correta.
- Caminho: `glm > blind:Sonnet > followup > adjudicate:Sonnet > tiebreak:Opus > own`. JEF deu 0,713 (< 0,86), então a cascata inteira foi acionada. O adjudicador Sonnet trocou o diagnóstico certo por outro (helmintíase); o Opus no desempate voltou ao diagnóstico certo, com a ressalva de coinfecção.
- 4 turnos do médico, 3 trocas com o paciente, 10 pedidos de exames, 1 troca extra do revisor com o paciente, ~4 min.

## Custo real (ledger OpenRouter, US$)
| Papel | Modelo | Chamadas | Custo |
|---|---|---:|---:|
| Revisor / adjudicador | Sonnet 5.5 | 3 | 0,0852 |
| Desempate | Opus 5.5 | 1 | 0,0660 |
| Mapa da consulta | Sonnet 5.5 | 1 | 0,0108 |
| Médico | GLM-5 | 7 | 0,0193 |
| Associador de exames | GLM-4.5-Air | 18 | 0,0013 |
| JEF (estimado, fora do OpenRouter) | | 1 | 0,0002 |
| **Custo de implantação (sem paciente nem juiz)** | | | **0,1829** |
| Paciente simulado (Sonnet, 4 chamadas) | | 4 | 0,0429 |
| Juiz (Gemini 3.1 Pro, 2 chamadas) | | 2 | 0,0070 |
| **Total do caso no OpenRouter** | | | **0,2325** |

Claude via API = US$ 0,2049 de 0,2325 (88%); só os revisores e o mapa = 0,1620 (89% do custo de implantação). GLM-5 + associador sozinhos custariam 0,0206. Custo por caso resolvido: US$ 0,183 (implantação) ou 0,2325 (com paciente e juiz). A sonda de verificação da API (2 chamadas) custou US$ 0,0020, fora do caso.

## Ressalvas
1. **Vazamento por correspondência generosa de exame.** O médico pediu "Serum IgE" (genérico, junto com 7 outros exames) e a ferramenta devolveu a observação do exame específico (IgE para o antígeno do diagnóstico). Um laboratório real devolveria IgE total. O associador (GLM-4.5-Air) tolerou a equivalência; nenhum pedido anterior do médico incluía o teste do diagnóstico e ele só falou nele depois desse resultado. O acerto, portanto, depende em parte dessa tolerância do simulador e não apenas do raciocínio. O mesmo comportamento existe nos dez casos anteriores.
2. Um único caso, uma execução: o custo de US$ 0,183 é o de um caso que escalou até o Opus; nas dez execuções anteriores a média de implantação foi US$ 0,070 (Claude contado pelo preço equivalente da API) porque a maioria é aceita pelo JEF sem revisão.
3. Juiz LLM, sem revisão médica; critério de correspondência registrado antes da execução em `reference.json` (o diagnóstico publicado e seus equivalentes; um diagnóstico genérico ou de outra família não conta).
4. Conta OpenRouter x ledger: logo após a execução a conta mostrava US$ 15,925790818 (3 snapshots iguais) contra US$ 16,064016818 no ledger; minutos depois a conta convergiu para US$ 16,064016818 (2 snapshots sem cache). Ledger = conta; restam US$ 1,94 do teto de US$ 18.
