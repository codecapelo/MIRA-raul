# Auditoria factual final — MIRA v4 Sol run1

08-10-2026. Escopo: casos públicos 003–010, com os incidentes dos pilotos 001–002 incorporados da auditoria anterior. Fontes: `patient.json`, `investigations.json` e traces terminais no worktree `/Users/test/.codex/worktrees/mira-review-v38/MIRA-RAUL`. Somente leitura do benchmark; saída escrita em `/private/tmp`. Nenhuma inferência/API/CLI clínica, nova execução, acesso a casos privados ou credenciais, edição de código/input/HEAD ou alteração de escore.

## Resultado e contabilidade

**10/10 terminais únicos; juiz LLM: 9/10 corretos, caso002 falso.** Esses são escores do benchmark, preservados, sem adjudicação clínica. Há **50 ocorrências de achados entregues**: 49 são valores/substrings contíguas exatas; uma une dois fragmentos literais por ponto e vírgula (PT/INR, caso008). Todos têm suporte no registro, mas os problemas de escopo e cronologia abaixo impedem equiparar isso à fidelidade integral do encontro.

A nova leitura 003–010 cobre **41 achados e 28 falas do paciente** (médico + revisor). O total, incluindo os pilotos, é 33 falas. Não identifiquei fato clínico novo claramente inventado pelo paciente nas falas novas; isso é uma inspeção qualitativa desses registros, não garantia geral contra invenção.

Contabilidade canônica de `case_complete`: **41 fontes cobradas, 247 unidades relativas artificiais**, **US$ 0.12304050 OpenRouter total** e **US$ 0.03262650 implantação sem paciente/juiz**. Custo monetário da assinatura Codex desconhecido. Esta auditoria não reconciliou conta/ledger. Dez eventos `tool` reapresentados após a interrupção de cota (seis em003, quatro em005) foram excluídos da contagem factual; eventos `exam_cost` não foram somados, evitando dupla contabilidade.

| Caso | Juiz | Falas médico/revisor | Achados apoiados | Fontes cobradas | Unidades | OpenRouter US$ |
|---|---|---:|---:|---:|---:|---:|
| 001 | T | 1/1 | 4/4 | 4 | 26 | 0.01788875 |
| 002 | F | 2/1 | 5/5 | 5 | 27 | 0.01371400 |
| 003 | T | 1/1 | 5/5 | 4 | 22 | 0.01535050 |
| 004 | T | 4/1 | 9/9 | 5 | 31 | 0.01648675 |
| 005 | T | 4/1 | 3/3 | 3 | 11 | 0.01243150 |
| 006 | T | 3/1 | 5/5 | 5 | 35 | 0.01060875 |
| 007 | T | 4/1 | 7/7 | 4 | 12 | 0.00744275 |
| 008 | T | 1/1 | 4/4 | 3 | 17 | 0.008170 |
| 009 | T | 1/1 | 2/2 | 2 | 20 | 0.00880875 |
| 010 | T | 2/1 | 6/6 | 6 | 46 | 0.01213875 |

## Comparação qualitativa por caso

### Caso 001

Prior pilot audit: no clearly invented clinical fact identified; unknown exposures phrased as record-reader language.

- **historical_sample** (L9): Repeat blood-culture request receives already documented MRSA bacteremia; not evidence of a new collection.
- **workflow** (L64): Prior audit: generic prerequisite resolver redundantly chooses already performed pericardiocentesis for coronary tissue/stent culture; result stays blocked.
- **workflow**: Emergency admission initially blocked until at least one patient exchange.

### Caso 002

Prior pilot audit: no clearly invented clinical fact identified.

- **temporal_release** (L23; ecg_015): Electrophysiology result tagged available_at=followup and prerequisites=[followup] released at acute turn3. Subsequent study wording preserved. Prior audit records proposal/final use.

### Caso 003

Two utterances compared with patient.json: drainage failure last night, pain/dyspnea afterward, MAINZ pouch after cancer cystectomy and catheterization difficulty supported; unreported details kept unknown.

- **workflow** (L30, L42, L43): Admission was attempted before patient response; first and replayed blocked attempt are one underlying event. One patient exchange then permits admission.
- **inference_boundary** (L47, L56): Reviewer proposes obstruction/overdistension as most likely mechanism, explicitly states not directly documented; do not reclassify a labeled hypothesis as a confirmed fact.

### Caso 004

Five utterances compared with patient.json: transient improvement and recurrent dyspnea supported; cancer history, fluid-test recall, medicines, weight loss, TB/exposures remain unknown. No clearly invented clinical fact identified.

- **request_scope** (L37; imaging_008): CT pulmonary angiography request receives generic Chest CT source. Angiographic protocol and PE assessment are not attested by the source; the returned findings themselves are literal.
- **historical_sample** (L22, L30, L31; lab_006, microbiology_007): Pleural-fluid tests originate in initial thoracentesis prior record; requested ultrasound-guided new thoracentesis is unavailable. Extracted cytology/pH/protein/LDH/Gram stain omit original initial-sample qualifier; doctor's fluid-results speech does not restore it. New sampling is not demonstrated.
- **request_scope** (L48; procedure_result_009): Generic Bronchoscopy request receives bronchoscopy plus EBUS-guided biopsy diagnostic result. Separate EBUS-biopsy request in same call is already_ordered. Literal bundled source; exact procedure scope should not be presumed independently equivalent.

### Caso 005

Five utterances compared with patient.json: age60s, rheumatoid arthritis, stable five-year ILD, stable baricitinib/methotrexate and asbestos exposure supported. Other details remain unknown. No clearly invented clinical fact identified.

- **request_scope** (L19, L31, L23, L33; imaging_008): CT pulmonary angiography receives postcontrast generic Chest CT; high-resolution reconstructions classified already_ordered. Source attests neither angiographic protocol nor HR reconstructions; replay lines excluded from counts.
- **request_scope** (L47; procedure_result_009): Left pleural fluid cytology request receives whole cytology/immunohistochemistry bundle, including all marker positives/negatives. Values are literal; this is broader than isolated cytology.
- **workflow** (L42, L43, L47): New ultrasound-guided thoracentesis unavailable, yet existing pleural cytology source available. Doctor explicitly acknowledges unavailable drainage; record access does not show newly performed sampling.
- **narrative_temporality** (L11): Doctor calls breathing difficulty sudden; patient.json describes one week. Abrupt onset is not directly established.

### Caso 006

Four utterances compared with patient.json: no fever/night sweats or steroid use and remote chest opacity without TB diagnosis/treatment supported. Other details remain unknown. No clearly invented clinical fact identified.

- **request_scope** (L15; lab_004): 8 AM serum cortisol request returns complete ACTH+cortisol source with earlier and admission values; source does not attest 8 AM collection. ACTH stimulation with baseline/30/60 min cosyntropin is classified already_ordered against the same basal source, but dynamic stimulation values are absent. Final physician/reviewer do not claim a performed/positive stimulation test.
- **request_scope** (L19; imaging_007): Requested adrenal CT noncontrast and contrast-enhanced protocol receives generic Adrenal CT; phases are not specified in the source.
- **temporal_prerequisite_respected** (L31, L36; microbiology_010): Adrenal-tissue PCR tagged after_procedure:adrenal_biopsy released after delivered adrenal biopsy.

### Caso 007

Five utterances compared with patient.json: progressive jaundice four days, dark stools with melena unconfirmed, no abdominal pain/reported bleeding, pembrolizumab400mg14days earlier and metastatic lung cancer supported. Other details remain unknown. No clearly invented clinical fact identified.

- **narrative_specificity** (L25, L27; lab_007): Blocked admission reasoning calls haptoglobin undetectably low, while source reports <0.3 g/L without detection-limit statement. Subsequent admitted reasoning returns to below0.3; reviewer final uses suppressed haptoglobin.
- **inference_boundary** (L29, L32): Reviewer labels pembrolizumab most likely trigger while stating causality not proven; does not claim confirmed drug causality or resolve antibody subtype without queued test.

### Caso 008

Two utterances compared with patient.json: no injury/heavy lifting and no known medication/anticoagulant use supported. Activity details, supplements and exposures kept unknown. No clearly invented clinical fact identified.

- **literal_formatting** (L8; lab_006): PT12s and INR1.0 are two exact source fragments joined by semicolon, rather than one contiguous substring. Both numeric values and units preserved.
- **request_scope** (L5; imaging_008): MRI request includes cord diffusion-weighted sequence; source specifies cervicothoracic MRI without sequence attestation. No diffusion result invented in returned finding.
- **narrative_temporality** (L3): Doctor calls initial pain sudden. Source states pain began two days earlier and weakness progressed, without explicit sudden-onset statement.
- **workflow** (L10, L12): Emergency admission initially blocked before patient response; one patient exchange then obtained.

### Caso 009

Two utterances compared with patient.json: timing/stool-flatus and lifestyle details not reported, kept unknown. No clearly invented clinical fact identified.

- **request_scope** (L11; imaging_006): Abdominopelvic CT angiography request receives generic Abdominal CT source. Vascular protocol/occlusion assessment not attested; obstruction/foreign-body text is literal.

### Caso 010

Three utterances compared with patient.json: pain mildly eight days earlier then worsening, gestation approximately five weeks supported; exact menstrual date, symptoms not reported and lifestyle details kept unknown. No clearly invented clinical fact identified.

- **request_scope** (L15; imaging_007): Transvaginal ultrasound request receives Pelvic ultrasound source; source does not explicitly state transvaginal route. Result itself literal.
- **request_scope_and_historical_result** (L25; hpi_001_prior_ct, imaging_008): One contrast CT request releases both prior noncontrast lesion and contrast CT mass sources, counted as two canonical performed sources. Original Initial noncontrast wording preserved; this is not evidence that one new contrast examination produced both.
- **workflow** (L27, L29, L31, L38, L43): Four surgical requests held before long indication-bearing laparoscopy request released. Line43 combines delivered laparoscopy and requires_prior_procedure=laparoscopy in same output; that prerequisite message is redundant after the delivered laparoscopy.
- **temporal_prerequisite_respected** (L36, L43, L48; procedure_result_010): Surgical pathology first blocked pending laparoscopy; after delivered laparoscopy, source fragment products of conception returned. No invented villi/trophoblast microscopic description despite request naming them.
- **inference_boundary** (L54, L57): Reviewer locates implantation in omentum between spleen and descending colon from operative source; explicitly leaves primary versus secondary implantation unresolved.

## Temporalidade e papéis

Caso002 continua sendo o único achado entregue com `available_at=followup`: estudo eletrofisiológico liberado no encontro agudo, incidente já registrado no piloto. Nos casos novos, nenhum achado marcado `day_N` ou `followup` foi entregue. Isso não valida uma guarda temporal geral: esses resultados não foram solicitados/liberados nesses encontros. PCR adrenal (006L36) e patologia (010L48) vieram após o respectivo procedimento; no001, angiografia veio após pericardiocentese. Procedimentos/achados operatórios rotulados `time_zero` comprimem a evolução em uma interação simulada; esses rótulos não demonstram duração clínica real.

Falhas de memória no discurso do paciente preservam o desconhecimento, mas acrescentam uma apresentação de memória que a fonte não atesta. As falas do médico/revisor incluem inferências diagnósticas; hipóteses explicitamente qualificadas (sobredistensão003, causalidade da droga007, origem do sangramento008, implantação primária/secundária010) foram separadas de fatos confirmados. Não foi julgado se uma inferência ou conduta é clinicamente correta/segura.

## Transporte e limite evidenciário

Os 152 envelopes `cli_call` guardam `tool_transport=json_emulated`. `response.message.tool_calls` representa ações clínicas em JSON, não um tool nativo da CLI. A leitura de `run_codex`/`parse_codex` (`src/mira_runner/cli_client.py:126`) confirma que stdout é validado antes do envelope ser registrado e que tipos nativos/desconhecidos são rejeitados. O agente principal informou 15 testes mockados do transporte; esta auditoria não os reexecutou.

A conclusão operacional é ausência de tool nativo aceita pelo parser. **Os stdout/stderr brutos não foram persistidos**, portanto não há atestação retrospectiva independente de todos os eventos originais. O modelo servido também não é atestado: os traces registram o solicitado `gpt-6.1-sol`, status `requested_only`. Limitações do transporte e escores do juiz devem permanecer separados da avaliação médica.

## Evidência reproduzível e limites

O JSON acompanhante inclui cada fala lida, cada achado entregue com pedido/linha/nome/valor/IDs e `available_at`, hashes dos traces e inputs, replay excluído, contabilidade terminal canônica, notas e limites. Os 50 achados contam ocorrências de saída via tool/revisor, não todos os fatos inicialmente injetados em prompts. Fontes cobradas são únicas por encontro; não são uma medida de 41 procedimentos reais novos.

A fidelidade literal dos valores foi preservada nesta leitura, enquanto equivalências de modalidade, conteúdo excessivo de painéis, amostras históricas e cronologia permanecem pontos qualitativos para uma condição futura. Não editar esta rodada nem seus escores para corrigir esses pontos. Revisão médica continua pendente; um único run em casos conhecidos não estabelece acurácia clínica, segurança, superioridade, desempenho externo ou ConsistencyDx.
