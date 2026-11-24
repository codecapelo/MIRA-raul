# Auditoria dos PDFs dos 10 casos públicos: o que o artigo traz e a conversão não tem — 14-11-2026

Leitor: Claude Sonnet 5.5 (high) pela assinatura, sobre o texto extraído do PDF (`pdftotext`), com `scripts/pdf_audit.py`. Cada achado traz uma citação literal do artigo; a citação foi procurada no texto do PDF e marcada como **verificada** ou **não verificada** (quebra de coluna, número ou símbolo no PDF). **É uma lista para revisão médica, não uma correção.** Nada foi alterado em `cases/`.

**Limites:** só o texto do PDF foi lido (figuras e tabelas em imagem não); um leitor LLM pode deixar itens passarem, então "nenhum item" não prova completude; os itens "só qualitativo" (por exemplo "exames normais") são candidatos a licença de normalidade para o gatekeeper.

| Caso | Observações extraídas | Itens ausentes (verificados / total) | Resultado na apresentação | Resultado depois | Só qualitativo | Contradições |
|---|---:|---:|---:|---:|---:|---:|
| case_001 | 9 | 2 / 2 | 0 | 1 | 1 | 0 |
| case_002 | 12 | 7 / 8 | 0 | 5 | 2 | 1 |
| case_003 | 15 | 23 / 24 | 4 | 14 | 4 | 0 |
| case_004 | 8 | 4 / 6 | 2 | 2 | 0 | 0 |
| case_005 | 10 | 2 / 2 | 1 | 0 | 1 | 0 |
| case_006 | 8 | 5 / 6 | 4 | 0 | 1 | 0 |
| case_007 | 7 | 7 / 8 | 4 | 3 | 0 | 0 |
| case_008 | 7 | 5 / 5 | 2 | 0 | 3 | 0 |
| case_009 | 5 | 2 / 2 | 0 | 0 | 2 | 0 |
| case_010 | 8 | 3 / 3 | 1 | 1 | 1 | 0 |

Total verificado: 60 itens ausentes, dos quais 18 com resultado já na apresentação do caso, 26 com resultado posterior e 15 só qualitativos.

## Itens por caso

### case_001
- **imaging: Final coronary angiography after covered stent deployment** (result, later, citação verificada). Artigo: Confirmed complete exclusion of the pseudoaneurysm
- **laboratory: Laboratory markers and vital signs after drainage and covered stent implantation** (qualitative_only, later, citação verificada). Artigo: Laboratory marker levels and vital signs improved; no values given

### case_002
- **lab: Liver enzymes** (qualitative_only, presentation, citação verificada). Artigo: Mild elevations noted at presentation (no values)
- **lab: Inflammatory markers** (qualitative_only, presentation, citação verificada). Artigo: Mildly elevated at presentation (no values or specific markers)
- **echo: Post-pacemaker-implantation transthoracic echocardiography** (result, later, citação verificada). Artigo: Absence of A-wave in mitral inflow, mildly reduced RV systolic function, massive tricuspid regurgitation
- **procedure: Atrial pacing attempts during CRT pacemaker implantation** (result, later, citação verificada). Artigo: Atrial pacing attempted at multiple sites; all unsuccessful
- **lab: High-sensitivity troponin T at readmission** (result, later, citação verificada). Artigo: 11 ng/L
- **lab: NT-proBNP at readmission** (result, later, citação NÃO verificada). Artigo: 95 pg/mL
- **echo: Follow-up transthoracic echocardiography 6 weeks postdischarge** (result, later, citação verificada). Artigo: No left atrial activity; RV mildly dilated with normal systolic function; mild TR; normal systolic PA pressure (29 mm Hg)
- **device: Pacemaker device interrogation** (result, later, citação verificada). Artigo: 100% biventricular pacing
- **Possível contradição em lab_008**: Article reports D-dimer unit as mg/mL, extracted list says µg/mL (likely a typo in the article, but it differs as written). (citação NÃO verificada)

### case_003
- **imaging: Abdominal ultrasound** (result, presentation, citação verificada). Artigo: Small volume of free fluid in the pelvic cavity (Koller pouch), no further abnormalities
- **imaging: Supine chest radiograph** (result, presentation, citação verificada). Artigo: Enlarged cardiac silhouette, left lower lobe consolidation with positive bronchopneumogram consistent with pneumonia, right-sided pleural effusion
- **echocardiography: Transthoracic echocardiography** (result, presentation, citação verificada). Artigo: Volume-depleted state with kissing ventricles and a collapsible inferior vena cava
- **monitoring: Continuous ICU physiological monitoring (5-lead ECG, invasive/non-invasive BP, respiratory rate, temperature)** (mention_only, later, citação verificada). Artigo: Done throughout ICU stay; summarised in figures 2 and 3
- **endoscopy: Pouchoscopy** (result, unclear, citação verificada). Artigo: Mucosal swelling at the stoma site (weeks before admission)
- **laboratory: Blood gas analysis (pH, pCO2, pO2, HCO3, BE, sO2)** (result, presentation, citação verificada). Artigo: Serial values Day 1 post-op to Day 6, e.g. post-op pH 7.42 (art), pCO2 30, pO2 100, HCO3 21.1, BE -4.0, sO2 98.5%
- **laboratory: Interleukin-6** (result, later, citação NÃO verificada). Artigo: 117 pg/mL on Day 3 (normal <7)
- **laboratory: D-dimer** (qualitative_only, presentation, citação verificada). Artigo: Normal
- **laboratory: Serum beta-D-glucan** (qualitative_only, later, citação verificada). Artigo: Measured on Days 2 and 6; borderline or non-diagnostic ranges (Table 3 lists positive on Day 3)
- **laboratory: Prothrombin time** (result, later, citação verificada). Artigo: PT decreased to 30% on Day 3
- **imaging: Lung ultrasound (Day 3)** (result, later, citação verificada). Artigo: Bilateral diaphragmatic elevation, basal atelectasis, small pleural effusion
- **imaging: Chest radiograph (Day 4)** (result, later, citação verificada). Artigo: Bilateral diaphragmatic elevation, pleural effusions
- **microbiology: Conduit urine culture (Day 2)** (result, later, citação verificada). Artigo: Negative for bacterial growth
- **microbiology: Catheterised urine culture (Day 7)** (result, later, citação verificada). Artigo: No microbial growth
- **microbiology: Drain fluid culture, Day 5 sample** (result, later, citação verificada). Artigo: No microbial growth
- **microbiology: Antimicrobial susceptibility testing of Klebsiella oxytoca and Pseudomonas aeruginosa** (result, later, citação verificada). Artigo: Klebsiella susceptible to most antibiotics except ampicillin; Pseudomonas susceptible to meropenem, tobramycin, amikacin, resistant to piperacillin/tazobactam, ceftazidime, cefepime
- **microbiology: Antimicrobial susceptibility of vancomycin-resistant Enterococcus faecium** (result, later, citação verificada). Artigo: Resistant to ampicillin, ampicillin/sulbactam, imipenem, vancomycin, levofloxacin; susceptible to teicoplanin, linezolid, tigecycline
- **physical_exam: Vital signs Day 1 ICU** (result, later, citação verificada). Artigo: HR up to 150 bpm, hypotension
- **physical_exam: Abdominal exam Day 2** (result, later, citação verificada). Artigo: Soft, tender, no peritonitis
- **laboratory: Lactate Day 2** (result, later, citação verificada). Artigo: 3.2 mmol/L
- **physical_exam: Wound drainage Day 5** (result, later, citação verificada). Artigo: Purulent wound drainage collected
- **physical_exam: Vital signs Day 6** (result, later, citação verificada). Artigo: BP 110/70 mm Hg, HR 100 bpm
- **laboratory: Follow-up laboratory parameters at 4 weeks (white cell count, CRP)** (qualitative_only, later, citação verificada). Artigo: Normalised
- **physical_exam: Surgical wound inspection** (qualitative_only, later, citação verificada). Artigo: Wound healed per primam intentionem

### case_004
- **imaging: Initial chest X-ray** (result, presentation, citação verificada). Artigo: Large right pleural effusion with meniscus sign at first presentation (the extracted chest radiograph entry covers only the ED return).
- **procedure: Initial diagnostic thoracentesis** (result, presentation, citação verificada). Artigo: Yielded 1.5 L of milky fluid. The extracted entry covers only the repeat thoracentesis.
- **lab: Pleural fluid total white cell count** (result, presentation, citação NÃO verificada). Artigo: 1068/μL (reference <1000/μL)
- **imaging: Follow-up PET scan** (result, later, citação verificada). Artigo: Decreased size of subcarinal and right hilar nodes, improved right middle lobe collapse and bronchial narrowing, consistent with partial response to therapy.
- **lab: Peripheral blood count at terminal febrile illness** (result, later, citação NÃO verificada). Artigo: White cell count 28.8 K/cumm with 87% neutrophils (neutrophilic leukocytosis); platelets 1020 K/cumm (thrombocytosis).
- **imaging: Imaging during final febrile illness** (result, later, citação verificada). Artigo: Bilateral lower lobe infiltrates suggestive of pneumonia.

### case_005
- **physical_exam: Cardiovascular examination** (qualitative_only, presentation, citação verificada). Artigo: Normal
- **physical_exam: Calf examination / peripheral oedema** (result, presentation, citação verificada). Artigo: Calves soft and non-tender, no subcutaneous oedema

### case_006
- **laboratory: Renin-angiotensin-aldosterone ratio (ARR)** (result, presentation, citação verificada). Artigo: ARR 0.09, consistent with adrenal insufficiency
- **laboratory: 25-hydroxyvitamin D** (result, presentation, citação verificada). Artigo: Low, 20.6 nmol/L (reference 47.7-144 nmol/L)
- **pathology: Immunohistochemistry of adrenal biopsy (CD68PG-M1, SMA, S100)** (result, presentation, citação verificada). Artigo: CD68PG-M1 positive; SMA and S100 negative
- **imaging: Right adrenal gland morphology on imaging** (result, presentation, citação verificada). Artigo: Right adrenal mass was thin and strip-shaped, unsuitable for biopsy
- **imaging: Follow-up abdominal ultrasound and chest CT** (mention_only, later, citação NÃO verificada). Artigo: Regular abdominal ultrasound and chest CT were done during follow-up, no specific results given
- **laboratory: Follow-up hormone levels** (qualitative_only, later, citação verificada). Artigo: Hormone levels gradually stabilizing, no values given

### case_007
- **lab: Serum ferritin** (result, presentation, citação verificada). Artigo: 2441 ng/ml (markedly elevated; normal 15-300)
- **lab: INR (coagulation)** (result, presentation, citação verificada). Artigo: INR 1.4 on day 1 (normal 0.8-1.2), 1.3 day 2, 1.1 day 4 and at 2 weeks
- **lab: Serum immunoglobulins (IgA, IgG, IgM)** (result, presentation, citação verificada). Artigo: Day 1: IgA 6.5 (high), IgG 17.8 g/l (high), IgM 0.6; day 4: IgA 6.3, IgG 18.4, IgM 0.6
- **lab: Complement levels C3 and C4** (result, presentation, citação NÃO verificada). Artigo: C3 1.0 g/l (normal 0.9-1.80); C4 0.12 g/l (low; normal 0.14-0.54)
- **lab: Direct agglutination at 30°C (cold agglutinin screen)** (result, presentation, citação verificada). Artigo: Reactions of no specificity detected
- **pathology: PD-L1 tumor proportion score by immunohistochemistry (tumor molecular analysis)** (result, unclear, citação verificada). Artigo: High PD-L1 TPS of 70%
- **lab: Hemoglobin follow-up trend** (result, later, citação verificada). Artigo: 67 g/l day 2, 86 g/l day 4, 93 g/l day 5, 114 g/l 2 weeks after discharge
- **lab: Follow-up bilirubin and LDH** (result, later, citação verificada). Artigo: Bilirubin 54 (day 2), 26 (day 4), 16 (day 5), 9 umol/l at 2 weeks; LDH 1128 (day 5), 860 u/l at 2 weeks

### case_008
- **imaging: Chest X-ray** (qualitative_only, presentation, citação verificada). Artigo: Performed and normal
- **lab: Lymphocyte count (differential)** (result, presentation, citação verificada). Artigo: Slightly decreased, 10 % (normal 24–45 %)
- **lab: Hemoglobin, renal function and other hematological/biochemical parameters** (qualitative_only, presentation, citação verificada). Artigo: Within normal limits
- **physical_exam: General examination (pallor, icterus, cyanosis, lymphadenopathy, dehydration)** (result, presentation, citação verificada). Artigo: No signs of pallor, icterus, cyanosis, lymphadenopathy, or dehydration
- **physical_exam: Follow-up neurological assessment at 4 and 8 weeks** (qualitative_only, later, citação verificada). Artigo: Fully recovered without any neurological deficit

### case_009
- **laboratory: Serum sodium (hypernatremia episodes)** (qualitative_only, later, citação verificada). Artigo: Episodes of hypernatremia occurred postoperatively and were treated medically; no values given
- **laboratory: Serum calcium (hypercalcemia episodes)** (qualitative_only, later, citação verificada). Artigo: Episodes of hypercalcemia occurred postoperatively and were treated medically; no values given

### case_010
- **laboratory: Home urine pregnancy test (self-test)** (result, presentation, citação verificada). Artigo: Patient self-tested positive for urinary pregnancy on April 6
- **laboratory: Follow-up serum HCG** (result, later, citação verificada). Artigo: Declined to normal range (<5 IU/L) within 1 month of follow-up
- **physical examination: External genitalia examination** (qualitative_only, presentation, citação verificada). Artigo: Normal external female genitalia

