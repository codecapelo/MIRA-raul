# Verificação final — Astra 6 e Sol 6.1

Verificação UTC: 2026-09-30T21:22:13.449200+00:00. Corpus `mvp10_v3_2026-09-26` e protocolo `mvp10_closedbook_v5_2026-09-26` preservados.

- Histórico: 150 hashes do manifesto base e 80 hashes do manifesto da extensão anterior reconferidos diretamente contra os arquivos. Total histórico: **230/230**. O analisador confirmou igualdade dos campos dos oito modelos com o snapshot histórico (SHA-256 `9fa80b5a33d175a93d851a00537da3cdd3e6f43c757314f26caedcf82723f727`).
- Novos braços: **30/30 Astra** e **30/30 Sol 6.1**, dez casos × três repetições exclusivos por modelo. Os 60 traces são terminais, têm esforço `high` solicitado, paths existentes e hashes individuais registrados em [trace_manifest.json](../results/frontier_addons_2026-09-29/trace_manifest.json). Nenhuma combinação terminal foi repetida.
- Painel observado: **290/300** combinações planejadas. As dez ausências são do Luna, cuja interrupção foi solicitada pelo usuário; não são imputadas como erro.
- Análise final: [relatório](../results/frontier_addons_2026-09-29/summaries/FRONTIER_ADDONS_REPORT.md) SHA-256 `f08cc8343f4318cf37666eba3a5b147ff5d391e924ee5281cdbccf4d0081ae21` e [JSON](../results/frontier_addons_2026-09-29/summaries/frontier_addons_analysis.json) SHA-256 `023eeb5127236fd413d85bb039af4bb1acc70ca599c1bacc3c28265d45181c79`. O analisador validou contrato, identidade solicitada, eventos e integridade antes de gerar a comparação.
- Revisão: **60 pacotes cegos** preparados em [round_2026_09_29_two](../results/review_addons/round_2026_09_29_two/review_scope.json), ainda sem adjudicação médica. Uma tentativa operacional Astra com falha permanece em `incomplete/` e fora dos 60 terminais.
- Custo: proxy API do Sol 6 original permanece **US$ 4,6561284**; seu arquivo [SOL_COST.json](../results/summaries/SOL_COST.json) SHA-256 `5ced1cfb04a3981bbec3eabac13c8400278df57362c5cf49c16547546bf49028`. Proxies API Astra **US$ 43,229340** e Sol 6.1 **US$ 7,003420** não são cobranças observadas das assinaturas.

Os matches diagnósticos são triagem lexical e não acurácia clínica validada. Segurança, condutas alternativas e disposição exigem revisão médica cega. O modelo efetivamente servido pelos CLIs Codex não é exposto; a evidência registra o identificador solicitado e a inferência aceita. O painel usa casos públicos distintos dos pacientes do MIRA original.
