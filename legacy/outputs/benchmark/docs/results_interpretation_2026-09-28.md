# Leitura dos resultados disponíveis

**Execução encerrada a pedido do usuário; 230 trajetórias terminais.** Sete braços completos (30 cada), Luna parcial (20). A automação foi pausada e não há autorização para retomar inferência. Os resultados automáticos são triagem de conceitos diagnósticos; revisão médica ainda pendente.

## Assinaturas

| Braço | Terminais / planejadas | Match do alvo observado | Duração mediana por run | Custo equivalente API dos terminais |
|---|---:|---:|---:|---:|
| claude-opus-5-5 high | 30/30 | 24/30 | 85.6 s | US$ 18.1708912 |
| claude-sonnet-5-5 high | 30/30 | 20/30 | 58.6 s | US$ 7.5722212 |
| gpt-6-sol high | 30/30 | 14/30 | 170.4 s | US$ 4.6561284 |
| gpt-5.6-terra high | 30/30 | 14/30 | 128.2 s | US$ 3.0385240 |
| gpt-6-luna high | 20/30 | 6/20 | 348.5 s | US$ 0.1678724 |

Custos Opus/Sonnet são equivalentes reportados pela CLI; Sol/Terra/Luna são calculados por tarifas Standard documentadas. Não são cobranças da assinatura. Prefixos de erros e interrupção são separados; uso da última chamada incompleta é desconhecido. Duração inclui serviço, rede e CLI, não mede somente tempo do modelo. As versões das CLIs e datas diferem entre painel base e extensão.

## O que se observa

- **Opus** apresenta mais matches automáticos do alvo nos dez casos:24/30. **Sonnet** apresenta 20/30 e a menor duração mediana entre os cinco braços de assinatura. Isso sugere uma opção operacional interessante neste conjunto; não estabelece superioridade clínica generalizável.
- **Terra e Sol** apresentam 14/30 cada, mas não nos mesmos casos. Terra coincide com o alvo nos três runs do caso 009, enquanto Sol coincide em um; Sol coincide em um run dos casos 001 e 007, enquanto Terra não coincide nesses casos. Igualdade do total não significa equivalência de trajetórias, segurança ou manejo. O custo hipotético terminal Terra é menor que Sol, sob tarifas e contabilidade descritas.
- **Luna** tem 6/20 matches. Cobre casos 001–006 com três runs e caso 007 com dois; não há resultados terminais dos casos 008–010. A proporção bruta 30,0% e a média pelos sete casos observados 31,0% usam pesos diferentes. Não extrapolar para 30, não imputar ausência como erro e não comparar esse agregado diretamente com painéis de dez casos.
- O caso 002, miocardite atrial isolada, não recebeu match do alvo em nenhum dos cinco braços de assinatura. Isso identifica um caso prioritário para verificar acesso aos fatos, equivalência terminológica, dificuldade diagnóstica e rubric; não autoriza modificar retrospectivamente o gabarito.
- Os modelos locais apresentaram forte dificuldade de conclusão/aderência às ferramentas neste harness: Qwen 3.5 concluiu 9/30 e teve 2 matches; Qwen 3 concluiu 14/30 e não teve match; Llama 3.1 não concluiu trajetórias. Esses resultados refletem modelo, formato, tamanho, implementação e condições locais deste ensaio; não são prova geral de incapacidade clínica de modelos locais.

## O que continua dependendo de médico

Diagnóstico textual pode ser diferente e ainda aceitável. Um match correto pode coexistir com terapia inadequada, atraso crítico ou disposição insegura. A análise não transforma contagem de exames em adequação, nem ausência de erro de ferramenta em segurança clínica. As rubrics distinguem gabarito publicado de alternativas aceitáveis; revisão cega deve usar `correct / acceptable alternative / questionable / unsafe`, inclusive para prefixos interrompidos.

Foram preparados 150 pacotes base e 80 adicionais para revisão, com chaves de modelo separadas. A fila adicional contém 240 registros para revisor primário, segundo revisor e consenso. Nenhum desses registros foi preenchido automaticamente como julgamento médico.

## Relação com MIRA

MIRA usou 574 admissões MIMIC-IV, GPT-4o + Plan o1-preview e EHR FHIR; nosso conjunto usa dez relatos públicos complexos e sandbox reduzido. Não há dez vinhetas originais completas abertas que permitam comparação pareada agora. Acurácia publicada 88,9% e matches deste projeto medem populações e critérios diferentes; não calcular ganho/subtração entre esses números. O [documento de referência](mira_reference_results.md) conserva os agregados publicados e a comparação por caso atual.

## Próximo passo já preparado

A revisão médica dos gabaritos e trajetórias é o próximo gate. Nenhum novo run é necessário para revisar estes dados. Eventual correção de rubric deve criar uma nova versão de avaliação, preservar outputs e permitir recalcular todos os braços sob a mesma regra. Casos próprios/fresh holdout continuam no backlog para reduzir contaminação por treinamento.

Links: [relatório completo disponível](../results/extension_2026-09-28/summaries/PARTIAL_COMBINED_REPORT.md), [tokens e interrupções](subscription_usage_2026-09-28.md), [verificação](extension_verification_2026-09-28.md).
