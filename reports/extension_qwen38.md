# Extensão: qwen/qwen3.8-max-prime e qwen/qwen3.8-max-0902 — 04-10-2026

Dois modelos adicionados depois das 150 execuções originais, 10 casos × 3 repetições cada (60 encontros). Mesmo protocolo, prompts, ferramentas, limite de 10 turnos e juiz (Gemini 3.1 Flash-Lite). Rota única fixada sem fallback: Alibaba (quantização não informada pelo provedor). Parâmetros de amostragem **assumidos iguais aos do Qwen3.5** (temperature 0,6, top_p 0,95, top_k 20; paciente temperature 0,01); logprobs foram solicitados e nenhum foi devolvido. Traces e CSVs isolados em `runs/qwen38_max_prime/`, `runs/qwen38_max_0902/` e `results/qwen38_*_run{1,2,3}.csv`; as 150 execuções anteriores e `MODELS` ficaram congelados. **Julgamento por LLM; revisão médica cega pendente; sem releitura manual destes encontros.**

| Modelo | Run 1 | Run 2 | Run 3 | Agregado | Wilson 95% (descritivo) | Custo terminais | Por encontro |
|---|---:|---:|---:|---:|---|---:|---:|
| qwen3.8-max-prime | 9/10 | 8/10 | 9/10 | 26/30 (86,7%) | 70,3%–94,7% | US$ 2,7619 | US$ 0,092 |
| qwen3.8-max-0902 | 9/10 | 8/10 | 7/10 | 24/30 (80,0%) | 62,7%–90,5% | US$ 1,3204 | US$ 0,044 |

Para comparação, no mesmo juiz: GPT-5.2 23/30 (59,1%–88,2%), GLM-5 20/30, GLM-4.5-Air 19/29, Qwen3.5 19/30, GPT-OSS 10/25. Os intervalos dos dois modelos novos se sobrepõem ao do GPT-5.2: ficaram no topo do placar, **sem base para afirmar superioridade**. Repetições do mesmo caso não são pacientes independentes.

Sem falhas operacionais, sem chamadas perdidas, ledger = conta (US$ 8,356544873 após os 60 encontros; extensão custou US$ 4,0824).

## Leitura do resultado
- **Quase não fazem anamnese.** O prime falou com o paciente em 7 de 30 encontros (média 0,23 falas) e o 0902 em 2 de 30 (0,07); os outros cinco modelos falaram em 93–100% dos encontros. Ambos terminam em 1 turno na grande maioria (28 e 23 encontros), pedindo uma bateria ampla de exames (mediana 9 chamadas, 0 erros de ferramenta) e admitindo em seguida.
- **Pedem o desfecho cirúrgico/histopatológico direto.** Heurística por palavras-chave (histopath, patholog, biops, autops, laparotom, laparoscop, operative, surgical, specimen, resect, excis, necropsy, intraoperative) nos argumentos das ferramentas: prime 18/30 encontros (60%), 0902 16/30 (53%), GPT-5.2 12/30 (40%), GLM-5 7/30, GLM-4.5-Air 5/30, Qwen3.5 2/30, GPT-OSS 1/30. Como o protocolo libera achados de qualquer momento do relato sob pedido (compressão temporal, já descrita em PROTOCOL.md), "diagnostic laparoscopy / histopathology of excised specimen" devolve o achado cirúrgico final. No caso 010 o prime fez isso nas 3 runs (3/3 corretos, duas delas sem falar com a paciente); no caso 009 run 2 pediu "exploratory laparotomy findings" e acertou, na run 3 não pediu e errou. Parte do ganho nos casos 009/010 provavelmente vem desse atalho do protocolo e **não mede raciocínio clínico equivalente ao de uma consulta**.
- **Casos difíceis permanecem difíceis.** Ambos erram 001 (pericardite purulenta por MRSA em vez de pseudoaneurisma coronariano infectado com ruptura do stent), 002 (standstill atrial por cardiomiopatia fibrótica em vez de miocardite atrial isolada) e 009 (obstrução por corpo estranho ingerido em vez de stent biliar migrado em divertículo de Meckel), exceto quando o pedido direto de exames libera o achado (prime 001 run 3, via coronariografia).
- **Consistência (descritiva):** ambos com 7 de 10 casos estáveis (mesmo veredito nas três runs).

## Limites
Amostragem assumida, não validada com o fornecedor; quantização desconhecida; um único provedor; fidelidade do paciente simulado não avaliável (quase não foi usado); sem releitura manual; juiz LLM com temperatura 1; heurística de palavras-chave grosseira. Uma segunda rodada com achados cirúrgicos/histopatológicos bloqueados até haver pedido de cirurgia mudaria o protocolo e exigiria nova execução, não autorizada aqui.
