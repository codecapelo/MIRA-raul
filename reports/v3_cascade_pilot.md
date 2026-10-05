# Escalonamento GLM-5 → JEF → Qwen → Sonnet/Opus: rodada-teste (05-10-2026)

Estrutura de `v3_design.md` (seção "Escalonamento"), 10 casos × 1 execução, GLM-5 com N=2 e exame junto da queixa; Sonnet 5.5 e Opus 5.5 pela assinatura Pro (CLI); juiz final Gemini 3.1 Pro. **Julgamento por LLM, sem revisão médica; uma execução por caso.**

## Resultado
- **Diagnóstico final correto: 7/10; a proposta original do GLM-5 também: 7/10.** O escalonamento não corrigiu nenhum erro e não estragou nenhum acerto. Erros: 001, 002 e 009, os mesmos de antes.
- **Custo de implantação** (médico + associador + Qwen + JEF + equivalente de API do Claude; sem paciente simulado e sem juiz): US$ 0,541 em 10 casos = **US$ 0,054 por encontro**, **US$ 0,077 por caso resolvido**. Só OpenRouter: US$ 0,379 (US$ 0,038 por encontro; US$ 0,054 por caso resolvido). Em comparação, GLM-5 N=2 sozinho custou cerca de US$ 0,014 por encontro e **US$ 0,020 por caso resolvido** (7/10); Qwen N=2 sozinho, US$ 0,078 por encontro e **US$ 0,086 por caso resolvido** (9/10).
- **Onde o dinheiro foi:** a entrevista do GLM-5 custou US$ 0,118 em 10 casos (US$ 0,012 por encontro); as 5 revisões do Qwen custaram **US$ 0,260** (US$ 0,052 cada, uma delas US$ 0,098 sem resposta); Sonnet US$ 0,048 e Opus US$ 0,114 em equivalente de API (1 chamada cada); JEF US$ 0,001.

## Caminhos
| Caso | Caminho | Escore JEF | Proposta | Final |
|---|---|---:|---|---|
| 003, 004, 005, 006 | JEF aceita | 0,90 a 0,93 | certa | certa |
| 009 | JEF aceita | 0,92 | **errada** | errada |
| 007, 008, 010 | Qwen concorda | 0,89 / 0,78 / 0,55 | certa | certa |
| 001 | Qwen concorda | 0,64 | **errada** | errada |
| 002 | Qwen sem resposta → Sonnet → Opus | 0,55 | **errada** | errada |

## O que explica o resultado
1. **Triagem do JEF:** aceitou 5 de 10 sem chamar ninguém: 4 certos e 1 errado (009, com escore 0,92; o diagnóstico acerta o mecanismo, stent migrado, e perde o divertículo de Meckel).
2. **Qwen revisor ancorado na proposta:** concordou (confiança 0,82) com a proposta errada do caso 001 **mesmo listando** exames (ecocardiograma transesofágico, cultura de líquido pericárdico, ECG) e perguntas que faltavam. A regra de aceitação ignorava essas listas e a rodada de pedidos extras só existia no nível do Sonnet; nenhum pedido foi feito neste caso. Nos 3 casos em que concordou com razão (007, 008, 010) não evitou nenhum erro e custou US$ 0,04 a 0,05 cada.
3. **Qwen revisor caro e instável:** em um caso o raciocínio consumiu os 16.384 tokens e não devolveu resposta (US$ 0,098 sem uso).
4. **JEF "mesmo diagnóstico" severo demais:** no caso 002 o Sonnet aceitou a proposta (miocardite com bloqueio atrioventricular completo) e o JEF a marcou como diferente (0,17); isso chamou o Opus sem necessidade (US$ 0,11 em equivalente de API). O Opus ainda errou (não nomeou a miocardite atrial isolada).
5. **Erros que nenhum revisor corrigiu** (001, 002, 009) são os mesmos em que o Qwen e os Claude também erravam no formato antigo; podem depender de informação que a entrevista do GLM-5 não coletou, não só de raciocínio.

## Gasto
Ledger e conta: US$ 13,916 → 14,353 (US$ 0,437 no OpenRouter), iguais em 3 snapshots (`credits_v3_cascade_final_*.json`). Restam cerca de US$ 3,65 do teto de US$ 18.
