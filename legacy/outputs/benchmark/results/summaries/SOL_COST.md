# Estimativa de custo do GPT-6 Sol high

Análise posterior aos 30 runs completos do corpus congelado. Os traces foram executados pelo Codex CLI autenticado pela assinatura ChatGPT; **o valor abaixo não é cobrança observada**. O custo efetivo atribuível ao benchmark na assinatura não é mensurável pelos traces e não deve ser apresentado como US$ 0.

| Medida | Valor |
|---|---:|
| Eventos de uso | 401 |
| Entrada total, incluindo cache | 6,703,197 |
| Entrada lida do cache, subconjunto da anterior | 5,630,592 |
| Entrada não cacheada | 1,072,605 |
| Saída total, incluindo raciocínio | 138,480 |
| Raciocínio, subconjunto da saída | 103,778 |
| Maior entrada por chamada | 19,016 |
| **Equivalente hipotético API Standard** | **US$ 4.66** |
| Sensibilidade: toda entrada não cacheada cobrada como gravação de cache | US$ 5.19 |
| Média equivalente por run | US$ 0.155 |
| Cobrança real da assinatura | Não disponível |

Tarifas da [página oficial do GPT-6 Sol](https://developers.openai.com/api/docs/models/gpt-6-sol), consultadas em 26-09-2026: US$ 2,00/milhão de tokens de entrada comum, US$ 0,20/milhão lidos do cache, US$ 2,50/milhão de gravação de cache, US$ 10,00/milhão de saída. Todas as chamadas ficaram abaixo de 272 mil tokens de entrada, portanto foi usada a faixa curta Standard. `high` não recebe multiplicador separado: o esforço de raciocínio aparece no volume de tokens de saída.

Fórmula da estimativa principal: `(1,072,605 × 2 + 5,630,592 × 0,20 + 138,480 × 10) / 1.000.000 = US$ 4.6561`. Os eventos reportaram 0 tokens de gravação; a faixa de sensibilidade até US$ 5.19 cobre a hipótese de esses tokens terem sido classificados como entrada comum no transporte por assinatura. Não somamos os tokens de raciocínio novamente, pois já integram a saída.

O histórico foi reempacotado a cada ação EHR pelo Codex CLI. Assim, uma implementação nativa pela API pode consumir tokens e cache diferentes. O custo do Claude no relatório é estimativa fornecida pela própria CLI, calculada por outra contabilização; os dois valores não são uma comparação econômica controlada. [Assinatura Codex e cobrança API são separadas](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex).
