"""G1 cases: ten primary-care vignettes derived from open-access guideline/review articles (CC BY). Writes cases_g1/ in the same schema as cases/.

  python3 scripts/build_g1_cases.py --sources-dir <dir with the PMC XML/txt files> --out cases_g1

What is real and what is authored (stated in every provenance.json and in reports/g1_protocol.md):
- the patient story, history facts and examination/test results are AUTHORED by Claude as a typical presentation of the condition; they are not from the article and not from a real patient;
- the reference diagnosis and the reference management items come from the article: every item carries a quote that is found in the article text (alphanumeric-only comparison, as scripts/pdf_audit.py does) and the section it comes from;
- nothing is clinically reviewed yet (`pending_clinician_review`).
Only items with a verified quote enter the management reference; general good practice that the article does not state is deliberately NOT scored.
No API call is made here.
"""
import argparse,hashlib,json,re,sys
from pathlib import Path

def alnum(s):return re.sub(r'[^a-z0-9]','',str(s).lower())

def fact(i,domain,value):return {'fact_id':f'{domain}_{i:03d}','domain':domain,'value':value,'available_at':'time_zero'}
ROUTE={'physical_exam':('physical_exam','request_physical_exam','clinical_examination'),'blood':('blood','request_blood_test','laboratory_blood'),'urine':('urine','request_urine_test','laboratory_urine'),
       'micro':('microbiology','request_microbiology','microbiology'),'xray':('radiology','request_radiology','radiograph'),'other':('other','request_other_investigation','other'),'spiro':('other','request_other_investigation','pulmonary_function'),
       'ecg':('bedside','request_bedside_test','electrocardiography'),'quest':('other','request_other_investigation','questionnaire')}
def obs(i,kind,name,value,test=None):
    domain,tool,modality=ROUTE[kind]
    return {'fact_id':f'{kind}_{i:03d}','domain':domain,'value':value,'available_at':'time_zero','name':name,'prerequisites':[],'unavailable_for_immediate_care':False,'original_domain':domain,
            'clinical_test':test or ('physical_examination' if kind=='physical_exam' else re.sub(r'[^a-z0-9]+','_',name.lower()).strip('_')[:60]),'modality':modality,'routing_tool':tool,'provenance':'authored_vignette_unreviewed'}

SRC={
 'g1_001':('PMC12036931','A comparison of national seasonal influenza treatment guidelines across the Asia Pacific region','Beer et al., 2025'),
 'g1_002':('PMC7839780','Evidence-based treatment recommendations for neck and low back pain across Europe: A systematic review of guidelines','Eur J Pain, 2021'),
 'g1_003':('PMC8678709','Executive summary of the 2020 clinical practice guidelines for the management of hypertension in the Philippines','2020'),
 'g1_004':('PMC6761728','Consensus recommendations for management of patients with type 2 diabetes mellitus and cardiovascular diseases','Diabetol Metab Syndr, 2019'),
 'g1_005':('PMC11099625','Therapeutic strategies for uncomplicated cystitis in women','Naber et al., 2024'),
 'g1_006':('PMC10746578','Acute pharyngitis in children and adults: descriptive comparison of current recommendations from national and international guidelines','Eur J Pediatr, 2023'),
 'g1_007':('PMC11351064','CANMAT 2023 Update on Clinical Guidelines for Management of Major Depressive Disorder in Adults','Can J Psychiatry, 2024'),
 'g1_008':('PMC9907191','Key recommendations for primary care from the 2022 Global Initiative for Asthma (GINA) update','NPJ Prim Care Respir Med, 2023'),
 'g1_009':('PMC9692772','LABA/LAMA as First-Line Therapy for COPD: A Summary of the Evidence and Guideline Recommendations','J Clin Med, 2022'),
 'g1_010':('PMC10268528','What are the core recommendations for gout management in first line and specialist care? Systematic review of clinical practice guidelines','BMC Rheumatol, 2023'),
}
def M(i,text,quote,where):return {'item_id':f'm{i}','management':text,'source_quote':quote,'source_section':where}

CASES={
'g1_001':dict(topic='influenza',age=29,sex='male',complaint='Fever, body aches and cough since yesterday.',
 facts=[('hpi','Since yesterday evening: sudden fever up to 38.9 C, shivering, severe muscle aches, headache, dry cough and sore throat. A co-worker was diagnosed with influenza last week.'),
        ('pmh','Healthy; no chronic disease, no asthma, no immunosuppression; not pregnant-related (male). No regular medication.'),
        ('hpi','No shortness of breath, no chest pain, no confusion, able to drink fluids; has not taken any medication yet.'),
        ('social','Did not receive this season\'s influenza vaccine. Non-smoker. Works in an office.')],
 obs=[('physical_exam','General and vital signs','Temperature 38.7 C, heart rate 98/min, respiratory rate 16/min, blood pressure 118/72 mm Hg, oxygen saturation 98% on room air. Looks tired but alert, hydrated.'),
      ('physical_exam','Head and neck','Mild pharyngeal erythema without exudate; no tonsillar enlargement; no tender cervical nodes.'),
      ('physical_exam','Respiratory','Clear lungs bilaterally; no wheeze or crackles; no increased work of breathing.'),
      ('micro','Rapid influenza test (nasopharyngeal swab)','Positive for influenza A.'),
      ('xray','Chest radiograph','Normal chest radiograph, no infiltrate.')],
 dx='Uncomplicated seasonal influenza (influenza A)',
 criterion='Influenza (seasonal, influenza A), uncomplicated, in a healthy adult. Any wording that names influenza / influenza-like illness due to influenza A counts as correct; viral upper respiratory infection without naming influenza does not.',
 mgmt=[M(1,'Antiviral treatment with oseltamivir may be considered for uncomplicated influenza when the patient presents within 48 hours of symptom onset; it is optional, not mandatory, in a healthy adult.','uncomplicated suspected or confirmed flu presenting within 48 hours of symptom onset','Results, comparison of national recommendations'),
       M(2,'Expected benefit of oseltamivir in a healthy adult is modest (about one day shorter and milder illness), so supportive care is an acceptable alternative.','treatment of adult influenza with oseltamivir reduces symptom severity and duration by approximately 24 hours in healthy individuals','Introduction')]),
'g1_002':dict(topic='low back pain',age=41,sex='male',complaint='Low back pain for three days after moving boxes.',
 facts=[('hpi','Three days ago he felt a sudden pull in the lower back while lifting boxes. Dull, aching pain in the low back, worse when bending forward and getting out of a chair, better when walking slowly. Rated 6/10.'),
        ('hpi','The pain does not go down the legs; no numbness, tingling or leg weakness. No fever, no weight loss, no night pain, no injury or fall, no problem passing urine, no loss of bowel control, no numbness in the groin area.'),
        ('pmh','No cancer, no osteoporosis, no steroid use, no intravenous drug use, no previous back surgery. Previous back pain episode two years ago that resolved by itself.'),
        ('meds','No regular medication. Took nothing for the pain so far. No allergies. Has been resting in bed most of the last two days.')],
 obs=[('physical_exam','General and vital signs','Afebrile, heart rate 74/min, blood pressure 126/80 mm Hg. Walks slowly with mild stiffness, no antalgic gait.'),
      ('physical_exam','Back examination','Paraspinal muscle tenderness in the lumbar region; no midline vertebral tenderness; flexion limited by pain; no deformity; no skin changes.'),
      ('physical_exam','Neurological examination of the legs','Normal strength, sensation and reflexes in both legs; straight leg raise negative bilaterally; normal perianal sensation reported.'),
      ('blood','Complete blood count','Normal.'),
      ('xray','Lumbar spine radiograph','Normal alignment, maintained disc spaces, no fracture.')],
 dx='Acute non-specific low back pain (mechanical lumbar strain) without red flags',
 criterion='Acute non-specific / mechanical low back pain (lumbar strain) without red flags or radiculopathy. Any wording that names acute mechanical or non-specific low back pain counts as correct; a specific structural diagnosis (disc herniation, fracture, infection, malignancy) does not.',
 mgmt=[M(1,'Reassure and give advice and education about the favourable course of non-specific low back pain.','reassurance; advice and education with the specific mention of physical activity and exercise','Results, summary of recommendations'),
       M(2,'Advise to remain active and to resume normal activity; do not prescribe bed rest.','AGAINST Bed rest','Results, Table of recommendations'),
       M(3,'Short-term use of NSAIDs (or paracetamol) is an option for pain relief.','NSAIDs4(3)2x O+ 1x /; 1x /* Weak FORShort-term use','Results, Table of recommendations')]),
'g1_003':dict(topic='hypertension follow-up',age=58,sex='male',complaint='Follow-up for high blood pressure; readings at home are still high.',
 facts=[('hpi','Diagnosed with high blood pressure two years ago. For the last four months his home blood pressure readings are around 150 over 92 to 156 over 96, taken seated in the morning with a validated arm cuff.'),
        ('meds','Takes amlodipine 5 mg once a day, every day; he says he has not missed doses. No other regular medicine; no anti-inflammatory use, no decongestants, no herbal products.'),
        ('pmh','No diabetes, no kidney disease, no stroke, no heart attack, no heart failure. No headaches, chest pain, palpitations or swelling in the legs apart from mild ankle swelling in the evening.'),
        ('social','Eats a lot of processed and salty food, drinks about three beers a week, ex-smoker, little exercise, sits most of the day. Mother had high blood pressure.')],
 obs=[('physical_exam','General and vital signs','Blood pressure 154/96 mm Hg in the right arm and 152/94 on repeat after five minutes; heart rate 72/min regular; BMI 29.'),
      ('physical_exam','Cardiovascular examination','Normal heart sounds, no murmur; no carotid bruit; mild bilateral ankle oedema; peripheral pulses present.'),
      ('blood','Basic metabolic panel (creatinine, eGFR, electrolytes)','Creatinine 0.9 mg/dL, eGFR 88 mL/min/1.73 m2, potassium 4.2 mmol/L, sodium 139 mmol/L, fasting glucose 96 mg/dL.'),
      ('blood','Lipid profile','Total cholesterol 214 mg/dL, LDL 132 mg/dL, HDL 44 mg/dL, triglycerides 150 mg/dL.'),
      ('urine','Urinalysis with protein','No protein, no blood, no glucose.'),
      ('ecg','Electrocardiogram','Sinus rhythm 70/min; no left ventricular hypertrophy by voltage criteria; no ischaemic changes.')],
 dx='Essential hypertension, not controlled on amlodipine monotherapy',
 criterion='Essential (primary) hypertension that is not controlled on calcium-channel-blocker monotherapy. Any wording that names uncontrolled/inadequately controlled hypertension counts as correct; a secondary cause named as the diagnosis does not.',
 mgmt=[M(1,'Intensify drug therapy with a combination: a renin-angiotensin-system blocker (ACE inhibitor or ARB) added to the calcium-channel blocker.','Ideal combination therapy includes renin-angiotensin-system (RAS) blocker with calcium channel-blocker (CCB) or thiazide/thiazide-like diuretics','Statements 4.2.2'),
       M(2,'Reinforce lifestyle changes (sodium restriction, weight and exercise) as the first line of antihypertensive treatment, together with drugs.','Healthy lifestyle choices are the first line of antihypertensive treatment','Lifestyle modification'),
       M(3,'Advise sodium restriction (as low as 1500 mg/day).','Sodium restriction to as low as 1500 mg/day','Lifestyle modification')]),
'g1_004':dict(topic='type 2 diabetes medication control',age=61,sex='male',complaint='Diabetes check-up; sugar has been running high.',
 facts=[('pmh','Type 2 diabetes for eight years. Heart attack five years ago treated with a coronary stent. High cholesterol.'),
        ('meds','Takes metformin 1000 mg twice a day, aspirin, atorvastatin 40 mg and a beta-blocker, regularly. No sulfonylurea, no insulin, no SGLT2 inhibitor or GLP-1 injection so far. No drug allergy.'),
        ('hpi','Feels well, no chest pain, no shortness of breath, no foot ulcers, no frequent urination or thirst. Home fasting glucose is usually 150 to 180 mg/dL. No episodes of low sugar.'),
        ('social','Weight has increased by 4 kg in the last year, sits most of the day, does not smoke now, no alcohol excess.')],
 obs=[('physical_exam','General and vital signs','Blood pressure 132/78 mm Hg, heart rate 68/min, weight 94 kg, BMI 31.'),
      ('physical_exam','Foot examination','Intact skin, normal pulses and normal monofilament sensation on both feet.'),
      ('blood','Glycated haemoglobin (HbA1c)','HbA1c 8.3% (stable over the last two measurements).'),
      ('blood','Basic metabolic panel (creatinine, eGFR, electrolytes)','Creatinine 1.0 mg/dL, eGFR 78 mL/min/1.73 m2, potassium 4.5 mmol/L.'),
      ('blood','Lipid profile','LDL 68 mg/dL, HDL 41 mg/dL, triglycerides 160 mg/dL.'),
      ('urine','Urine albumin-to-creatinine ratio','Albumin/creatinine 18 mg/g (normal).')],
 dx='Type 2 diabetes mellitus inadequately controlled on metformin, with established atherosclerotic cardiovascular disease',
 criterion='Type 2 diabetes mellitus not at glycaemic target on metformin, with established atherosclerotic cardiovascular disease (prior myocardial infarction). Any wording that names inadequately controlled type 2 diabetes with cardiovascular disease counts as correct.',
 mgmt=[M(1,'Add a second agent with proven cardiovascular benefit: an SGLT2 inhibitor or a GLP-1 receptor agonist, because of established cardiovascular disease.','in case of high risk for CVD, or renal issues, one can choose the best out of the SGLT2i and GLP1-RA','Recommendations, second-line therapy'),
       M(2,'Continue metformin as first-line background therapy.','Reduction in MI, all-cause mortality Extensive experience, no hypoglycaemia','Table of antihyperglycaemic agents')]),
'g1_005':dict(topic='uncomplicated cystitis',age=27,sex='female',complaint='Burning when passing urine for two days.',
 facts=[('hpi','For two days: burning on urination, passing small amounts of urine very often, urgency, mild pain above the pubic bone. The urine looks cloudy.'),
        ('hpi','No fever or chills, no back or flank pain, no nausea or vomiting, no vaginal discharge or itching, no blood in the urine, no new sexual partner. No catheter, no recent urinary procedure or hospital stay.'),
        ('pmh','Healthy. One similar episode about a year and a half ago that improved after antibiotics. No diabetes, no kidney stones, no kidney disease. Not pregnant: last period two weeks ago, uses oral contraception regularly.'),
        ('meds','Only the oral contraceptive pill. No known drug allergies.')],
 obs=[('physical_exam','General and vital signs','Temperature 36.8 C, heart rate 80/min, blood pressure 112/70 mm Hg.'),
      ('physical_exam','Abdominal and flank examination','Mild suprapubic tenderness; no costovertebral angle tenderness; abdomen otherwise soft.'),
      ('urine','Urine dipstick','Leukocyte esterase 2+, nitrite positive, blood trace, protein trace.'),
      ('urine','Urine pregnancy test','Negative.'),
      ('urine','Urine culture','Not yet resulted at the time of the consultation.')],
 dx='Acute uncomplicated cystitis (lower urinary tract infection) in a young woman',
 criterion='Acute uncomplicated cystitis / uncomplicated lower urinary tract infection in a non-pregnant woman. Any wording that names uncomplicated cystitis or lower UTI counts as correct; pyelonephritis or complicated UTI does not.',
 mgmt=[M(1,'Treat with a first-line oral antibiotic for uncomplicated cystitis: fosfomycin trometamol, nitrofurantoin or pivmecillinam (local resistance permitting).','fosfomycin trometamol, nitrofurantoin, pivmecillinam, alternatively oral cephalosporins','Therapeutic strategies, antibiotic recommendation'),
       M(2,'A urine culture is not required in a young woman with a first uncomplicated episode when the diagnosis is clear from history.','urine culture is not recommended when a robust diagnosis can be reached by patient history-taking and other potential causes of symptoms can be excluded','Diagnosis'),
       M(3,'Trimethoprim or co-trimoxazole only if the local E. coli resistance is below 20%.','Trimethoprim or cotrimoxazole are only recommended if the local resistance pattern for E. coli is <20%','Therapeutic strategies, antibiotic recommendation')]),
'g1_006':dict(topic='sore throat',age=20,sex='female',complaint='Sore throat and fever for two days.',
 facts=[('hpi','Two days of severe sore throat, pain on swallowing and fever up to 38.6 C. No cough, no runny nose, no hoarseness.'),
        ('hpi','No difficulty breathing, no drooling, can open her mouth fully, no rash, no ear pain. Roommate had a similar sore throat last week.'),
        ('pmh','Healthy, no previous rheumatic fever, no immunosuppression. No regular medication.'),
        ('meds','Allergies: none known. Has taken one dose of paracetamol.')],
 obs=[('physical_exam','General and vital signs','Temperature 38.5 C, heart rate 96/min, blood pressure 110/68 mm Hg, oxygen saturation 99%.'),
      ('physical_exam','Throat and neck examination','Enlarged erythematous tonsils with white exudate bilaterally; uvula midline, no peritonsillar bulge; tender enlarged anterior cervical lymph nodes. No cough heard, no rash.'),
      ('physical_exam','Respiratory','Clear lungs.'),
      ('micro','Rapid antigen detection test for group A streptococcus (throat swab)','Positive for group A streptococcus.'),
      ('micro','Throat culture','Pending (not available at the consultation).')],
 dx='Acute group A streptococcal pharyngitis (tonsillopharyngitis)',
 criterion='Acute group A beta-haemolytic streptococcal pharyngitis / tonsillitis (strep throat). Any wording that names streptococcal pharyngitis or tonsillitis counts as correct; viral pharyngitis or infectious mononucleosis as the final diagnosis does not.',
 mgmt=[M(1,'With a high clinical score (Centor 3-4) use a microbiological test (rapid antigen test or culture) and treat with antibiotics only when it is positive.','Positive microbiological test (RADT or culture)Penicillin V or amoxicillin10 days','Table of national and international guidelines (US ACP/CDC 2016)'),
       M(2,'First-line antibiotic is penicillin V or amoxicillin for 10 days.','Penicillin V q 6-12 hAmoxicillin q 12-24 hPenicillin G single dose10 days','Table of national and international guidelines (US ACP/CDC 2016)'),
       M(3,'Culture is the gold standard for diagnosis, but rapid antigen testing is the practical tool in the consultation.','The culture test is the gold standard for the diagnosis of GABHS pharyngitis, but it has long turn-around times and considerable costs','Diagnosis')]),
'g1_007':dict(topic='depression',age=34,sex='female',complaint='Feeling very low and tired for the last six weeks.',
 facts=[('hpi','For about six weeks: low mood most of the day, loss of interest in things she enjoyed, tiredness, trouble falling asleep and waking at 4 am, difficulty concentrating at work, and feeling guilty. Lost about 3 kg without trying.'),
        ('hpi','She says she has no thoughts of harming herself or of ending her life, and no plan. No episodes of unusually high energy or little need for sleep. No hallucinations. Heavy workload and a recent break-up.'),
        ('pmh','No previous episodes of depression or treatment. No thyroid disease, no chronic illness. Mother had depression. Not pregnant, no breastfeeding.'),
        ('social','Drinks about two glasses of wine per week, does not smoke, no recreational drugs. No regular medication, no allergies.')],
 obs=[('physical_exam','General and vital signs','Blood pressure 112/70 mm Hg, heart rate 72/min, weight 58 kg (was 61 kg). Subdued affect, normal speech, cooperative, no psychotic features.'),
      ('quest','PHQ-9 questionnaire','PHQ-9 total score 16 (moderately severe symptoms); item 9 (thoughts of death or self-harm) scored 0.'),
      ('blood','Thyroid-stimulating hormone (TSH)','Normal.'),
      ('blood','Complete blood count','Normal; haemoglobin 13.4 g/dL.'),
      ('blood','Basic metabolic panel (creatinine, eGFR, electrolytes)','Normal.')],
 dx='Major depressive disorder, first episode, moderate severity',
 criterion='Major depressive disorder (major depressive episode), first episode, of moderate severity. Any wording that names a major depressive episode/depressive disorder of moderate severity counts as correct; adjustment disorder, bipolar depression or hypothyroidism as the final diagnosis does not.',
 mgmt=[M(1,'Offer a first-line treatment: either structured psychotherapy (CBT, interpersonal therapy or behavioural activation) or a first-line antidepressant, according to preference and availability.','CBT, interpersonal therapy (IPT), and BA as first-line recommended psychological treatments for the acute treatment of MDD','Psychological treatments'),
       M(2,'Structured psychotherapies and first-line antidepressants are equally effective in the short term; choose according to patient preference.','Structured psychotherapies and first-line antidepressant medications are equally effective in treating MDD in the short term','Treatment selection'),
       M(3,'Use psychoeducation when prescribing: risks and benefits, time course of effect, and dispelling myths about medication.','Clinicians should use psychoeducation when prescribing medications, including discussing risks and benefits, the time course of effect, and dispelling myths and misbeliefs about medication use','Antidepressants'),
       M(4,'Use measurement-based care (PHQ-9) to monitor response.','can be used for subsequent monitoring during measurement-based care','Assessment')]),
'g1_008':dict(topic='asthma',age=24,sex='female',complaint='Wheezing and chest tightness; I use my blue inhaler a lot.',
 facts=[('hpi','Cough, wheeze and chest tightness for about a year, worse with exercise, cold air and cats. Uses her salbutamol (blue reliever) inhaler about 4 to 5 days a week.'),
        ('hpi','Wakes at night with cough or wheeze about twice a week. Has had no emergency visits, no oral steroids and no hospital stays in the last year.'),
        ('pmh','Childhood eczema and hay fever. No other illness. Does not smoke; no one smokes at home. Has a cat.'),
        ('meds','Takes only salbutamol as needed; does not take any daily controller medicine. No allergies to drugs.')],
 obs=[('physical_exam','General and vital signs','Respiratory rate 16/min, oxygen saturation 98%, speaks full sentences.'),
      ('physical_exam','Respiratory','Scattered expiratory wheeze on forced expiration; no crackles; no use of accessory muscles.'),
      ('spiro','Spirometry with bronchodilator test','FEV1 78% of predicted, FEV1/FVC 0.68; FEV1 increases by 15% (360 mL) after salbutamol.'),
      ('quest','Asthma Control Test','ACT score 14 (not well controlled).'),
      ('other','Inhaler technique check','Uses the metered-dose inhaler without spacer; coordination is imperfect.')],
 dx='Asthma, not well controlled, treated with as-needed salbutamol alone',
 criterion='Asthma (bronchial asthma) that is not well controlled on as-needed short-acting beta-agonist only. Any wording that names asthma counts as correct; COPD, vocal cord dysfunction or allergic rhinitis alone does not.',
 mgmt=[M(1,'Do not continue treatment with a short-acting beta-agonist alone; the patient needs a reliever/controller containing an inhaled corticosteroid (low-dose ICS-formoterol as needed, or a daily ICS).','GINA no longer recommends treatment of asthma with SABA alone (without ICS) in adults, adolescents and children >5 years','Key recommendations'),
       M(2,'Check inhaler technique and adherence, and review the patient\'s use of the reliever.','use of SABA more than two days a week should prompt review of their adherence and inhaler technique','Assessment of symptom control'),
       M(3,'Record how often the reliever inhaler is used when assessing symptom control.','record how often the patient is using their reliever inhaler','Assessment of symptom control')]),
'g1_009':dict(topic='COPD',age=67,sex='male',complaint='Cough and breathlessness climbing stairs, getting worse over the last years.',
 facts=[('hpi','Chronic cough with white sputum most mornings for years; breathless walking uphill or climbing one flight of stairs, has to stop on level ground when walking fast with people his age. No chest pain, no leg swelling, no fever.'),
        ('pmh','Smoked 40 pack-years, quit three years ago. No known heart disease. No hospital admissions for breathing. No courses of antibiotics or oral steroids for chest problems in the last year.'),
        ('meds','Uses salbutamol inhaler occasionally, about three times a week. No other regular inhalers. No drug allergies.'),
        ('social','Retired construction worker. Last influenza and pneumococcal vaccines: none in recent years.')],
 obs=[('physical_exam','General and vital signs','Respiratory rate 18/min, oxygen saturation 94% on room air, BMI 25. No cyanosis.'),
      ('physical_exam','Respiratory','Prolonged expiration with scattered end-expiratory wheeze; no crackles; no leg oedema.'),
      ('spiro','Spirometry (post-bronchodilator)','Post-bronchodilator FEV1/FVC 0.58; FEV1 62% of predicted; little reversibility.'),
      ('quest','COPD Assessment Test (CAT) and mMRC dyspnoea scale','mMRC grade 2; CAT score 17.'),
      ('xray','Chest radiograph','Hyperinflation, flattened diaphragms; no mass or consolidation.')],
 dx='COPD, symptomatic (GOLD group B), spirometry-confirmed',
 criterion='Chronic obstructive pulmonary disease confirmed by post-bronchodilator spirometry, symptomatic, with low exacerbation risk (GOLD group B). Any wording that names COPD counts as correct; asthma or chronic bronchitis without airflow obstruction does not.',
 mgmt=[M(1,'Start dual long-acting bronchodilator therapy (LABA/LAMA) as initial treatment for a symptomatic patient.','recommends initial pharmacological treatment with a long-acting muscarinic antagonist (LAMA) or a long-acting β2-agonist (LABA) for the majority of patients, and dual bronchodilator therapy (LABA/LAMA) in patients with more severe symptoms, regardless of exacerbation history','Introduction (GOLD 2022)'),
       M(2,'Ensure non-pharmacologic management and relevant vaccinations, and a short-acting bronchodilator for rescue.','optimizing non-pharmacologic management and relevant vaccinations and using a short-acting bronchodilator','Table footnote')]),
'g1_010':dict(topic='acute gout',age=52,sex='male',complaint='Very painful, swollen big toe since last night.',
 facts=[('hpi','Woke up at 3 am with severe pain, redness and swelling of the right big toe; even the bedsheet touching it hurts. Started yesterday evening, no injury. Slight fever. First time this has happened.'),
        ('pmh','High blood pressure treated with hydrochlorothiazide. No kidney disease, no kidney stones, no stomach ulcer, no heart failure, no diabetes. No previous joint swelling.'),
        ('meds','Hydrochlorothiazide 25 mg a day. No aspirin. No allergies. Has taken nothing for the pain yet.'),
        ('social','Drinks beer on weekends and a lot more last weekend at a party; eats red meat often; overweight.')],
 obs=[('physical_exam','General and vital signs','Temperature 37.8 C, heart rate 88/min, blood pressure 142/88 mm Hg, BMI 31.'),
      ('physical_exam','Joint examination','Right first metatarsophalangeal joint is red, warm, swollen and exquisitely tender; limited motion; no other joints involved; no tophi; no skin break.'),
      ('blood','Serum uric acid','Uric acid 9.1 mg/dL.'),
      ('blood','Basic metabolic panel (creatinine, eGFR, electrolytes)','Creatinine 1.0 mg/dL, eGFR 85 mL/min/1.73 m2.'),
      ('blood','Complete blood count and C-reactive protein','White cell count 11.2 x10^9/L, CRP 38 mg/L.'),
      ('xray','Foot radiograph','Soft tissue swelling around the first metatarsophalangeal joint; no erosions, no fracture.')],
 dx='Acute gout flare (podagra), first episode',
 criterion='Acute gout (gouty arthritis) of the first metatarsophalangeal joint, first episode. Any wording that names acute gout / gouty arthritis / podagra counts as correct; septic arthritis or cellulitis as the final diagnosis does not.',
 mgmt=[M(1,'Treat the flare with first-line anti-inflammatory medicines: NSAIDs, colchicine and/or corticosteroids.','non-steroidal anti-inflammatories (NSAIDs), colchicine and/or corticosteroids should be commenced as first-line medications','Recommendations for flares'),
       M(2,'Provide education and advice on elevating and resting the affected joint.','advice on elevating and resting the affected joint','Recommendations for flares'),
       M(3,'Provide education on non-pharmacological and pharmacological management options, including diet.','Patients should be provided with education on non-pharmacological and pharmacological management options','Recommendations for flares')]),
}

def build(cid,spec,src_dir,out):
    pmc,title,cite=SRC[cid];key='g1'+f'{int(cid[-3:]):02d}';text=(src_dir/(key+'.txt')).read_text()
    bad=[m['item_id'] for m in spec['mgmt'] if alnum(m['source_quote']) not in alnum(text)]
    if bad:raise SystemExit(f'{cid}: quote not found in {pmc}: {bad}')
    d=out/cid;d.mkdir(parents=True,exist_ok=True)
    facts=[];counters={}
    for dom,val in spec['facts']:
        counters[dom]=counters.get(dom,0)+1;facts.append(fact(len(facts)+1,dom,val))
    patient={'schema_version':'1.0.0','case_id':cid,'initial':{'age_years':spec['age'],'sex_recorded':spec['sex'],'chief_complaint':spec['complaint']},'presenting_complaint':spec['complaint'],
             'history_freetext':'\n'.join(f['value'] for f in facts),'history_facts':facts,'unknown_fields':['allergies','complete_home_medication_list','unreported_vital_signs','unreported_numeric_test_values']}
    obs_list=[];c={}
    for kind,name,value in spec['obs']:
        c[kind]=c.get(kind,0)+1;obs_list.append(obs(len(obs_list)+1,kind,name,value))
    inv={'schema_version':'1.0.0','case_id':cid,'observations':obs_list,'temporal_events':[],'availability_policy':'All results are available at the first consultation (primary-care outpatient visit).'}
    ref={'schema_version':'1.0.0','case_id':cid,'correct_diagnosis':spec['dx'],'matching_criterion':spec['criterion'],'condition':spec['topic'],
         'management_reference':spec['mgmt'],'management_scoring_note':'Only items with a verified source quote are scored; general good practice that the article does not state is not scored.'}
    prov={'schema_version':'1.0.0','case_id':cid,'case_type':'derived_vignette_from_open_access_guideline_or_review','authored_by':'claude-sonnet-5-5 (patient story, history facts and results); not from the article and not from a real patient',
          'source':{'pmcid':pmc,'title':title,'citation':cite,'license':'CC BY 4.0 (Europe PMC license field "cc by")' if cid!='g1_003' else 'CC BY (Europe PMC license field "cc by")','url':f'https://pmc.ncbi.nlm.nih.gov/articles/{pmc}/','xml_sha256':hashlib.sha256((src_dir/f'{key}_{pmc}.xml').read_bytes()).hexdigest()},
          'review_status':'pending_clinician_review','quotes_verified_in_source_text':True}
    pres={'text':spec['complaint'],'statement':spec['complaint'],'method':'authored with the vignette','model':'claude-sonnet-5-5'}
    for n,o in (('patient',patient),('investigations',inv),('reference',ref),('provenance',prov),('presentation',pres),('gatekeeper',{'licenses':[],'diagnosis_defining_tests':[]})):
        (d/f'{n}.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
    return {'case_id':cid,'topic':spec['topic'],'history_fact_count':len(facts),'observation_count':len(obs_list),'management_items':len(spec['mgmt']),'source':pmc}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--sources-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    rows=[build(c,s,a.sources_dir,a.out) for c,s in CASES.items()]
    (a.out/'manifest.json').write_text(json.dumps({'schema_version':'1.0.0','arm':'G1','cases':rows},indent=2)+'\n');print(json.dumps(rows,indent=1))
if __name__=='__main__':main()
