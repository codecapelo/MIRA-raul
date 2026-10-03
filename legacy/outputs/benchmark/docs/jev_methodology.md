# Jev (TypeSafe AI) como auditoria opcional dos gabaritos

**Estado em 25-09-2026:** Jev não foi usado para criar ou validar os dez gabaritos. Os gabaritos foram transcritos dos PDFs publicados e permanecem pendentes de assinatura médica. A integração anterior deste Mac usa `https://api.typesafe.ai/v1/systemone`, `model: jev-latest` e autenticação pela variável `TYPESAFE_API_KEY`; esta variável não está disponível no processo deste benchmark. Nenhuma credencial foi copiada, exibida ou registrada.

## Papel adequado

Jev/System One fornece perguntas estruturadas do tipo `choice`, `score` e `noul` sobre um estado textual. Pode servir como **segunda checagem editorial**: oferecer o resumo de achados e um conjunto explícito de hipóteses e apontar discrepâncias para o médico resolver. Uma alta probabilidade de `choice` não converte uma hipótese em verdade nem autoriza intervenção. Como o gabarito do *caso publicado* deriva da fonte, o endpoint não deve reescrever diagnóstico, cronologia, dose ou resultado; toda divergência deve voltar ao PDF e ao rubric.

Processo futuro opcional, separado do braço de comparação principal:

1. Congelar pacote e gabarito originados do PDF, com hashes e locadores.
2. Construir uma pergunta `choice` por caso com diagnóstico publicado e diferenciais plausíveis, sem título ou DOI, e no máximo os fatos liberados no ponto clínico avaliado.
3. Enviar só fatos de caso **já públicos**, e apenas se uma chave estiver configurada no ambiente. Não registrar cabeçalho Authorization nem corpo bruto de erro.
4. Salvar modelo servido, timestamp, hash do estado/pergunta, resposta estruturada, tokens e latência em `results/jev_audit/`, com ACL local.
5. Marcar conflito para revisão médica. Nenhum valor Jev altera rubric automaticamente.

## Comparação com MIRA e com o MVP

| Componente | MIRA publicado | MVP principal | Jev opcional para gabarito |
|---|---|---|---|
| Médico controlador | GPT-4o | Modelo avaliado, um por run | Não controla caso |
| Planejamento | `Plan` separado, o1-preview | `plan_reason` pelo próprio modelo, síntese observável | Não substitui `Plan` |
| Paciente | Patient agent ancorado na HPI | Lookup determinístico de fatos publicados | Não entrevista |
| EHR | Sandbox FHIR e ferramentas clínicas | EHR mínimo determinístico com onze ferramentas | Não emite ordens |
| Resultado | Trajetória diagnóstica e terapêutica | Mesma trajetória reduzida | Sinal de QA editorial tipado |
| Comparabilidade | Estudo original de 574 casos MIMIC-IV | Dez relatos públicos, não comparáveis numericamente | Fora do denominador do benchmark |

Se Jev for futuramente testado como planejador ou médico controlador, isso será um braço **arquitetural distinto**: terá novo `arm_id`, mesmo corpus e logs, mas não entrará na análise que busca manter controlador e fluxo constantes. O artigo MIRA de referência está em `docs/reference/mira_nature_2026.pdf`, separado dos dez PDFs clínicos.
