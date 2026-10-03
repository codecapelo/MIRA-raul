import json
from pathlib import Path
ROOT=Path.cwd()

def read(c,name): return json.loads((ROOT/'cases'/f'case_{c}'/name).read_text())
def write(c,name,obj): (ROOT/'cases'/f'case_{c}'/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def fact(packet,fid): return next(x for x in packet['facts'] if x['fact_id']==fid)
def action(rubric,aid): return next(x for x in rubric['expected_actions'] if x['action_id']==aid)
def provenance(truth,fid): return next(x for x in truth['fact_provenance'] if x['fact_id']==fid)

# 001: the publication reports a long admission and eventual discharge, not an ICU unit.
p=read('001','case_packet.json');g=read('001','ground_truth.json');r=read('001','rubric.json')
g['source_disposition']['category']='unknown'
g['source_uncertainties'].append('The source does not identify a specific ICU/ward placement during the acute event; ICU is a clinical option, not a published disposition fact.')
r['disposition_acceptability']=[{'category':'ICU','conditions':['Acceptable for cardiogenic shock/tamponade after emergency stabilization; unit is not explicit in source.']},{'category':'surgery','conditions':['Acceptable as immediate handoff for urgent coronary/pericardial source control, with critical-care monitoring.']}]
a=action(r,'a3');a['acceptable_tool_calls'].append({'tool':'request_procedure','code_or_concept':'coronary_angiography'})
a=action(r,'a4');a['priority']='optional';a['deadline']='Only after angiographic definition, multidisciplinary review and explicit clinical indication; covered stent is source treatment, not a universal mandate.'
r['critical_diagnoses_to_not_miss']=['Cardiac tamponade with shock','Complicated infective endocarditis with coronary/pericardial involvement']
for name,obj in [('case_packet.json',p),('ground_truth.json',g),('rubric.json',r)]:write('001',name,obj)

# 002: PDF p.3 has micrograms, and right-heart catheterization is an invasive procedure.
p=read('002','case_packet.json');g=read('002','ground_truth.json');r=read('002','rubric.json')
fact(p,'lab_008')['value']='D-dimer 2.94 µg/mL (reference <0.5 µg/mL).'
f=fact(p,'ecg_012');f['fact_id']='procedure_result_012';f['domain']='procedure_result';f['release_rule']={'tool':'request_procedure','match_codes':['rhc']}
provenance(g,'ecg_012')['fact_id']='procedure_result_012';provenance(g,'lab_008')['source_locators']=['PDF p. 3, paragraph following Figure 2']
provenance(g,'procedure_result_012')['source_locators']=['PDF p. 3, right-heart catheterization paragraph']
r['critical_diagnoses_to_not_miss']=['Clinically significant bradycardia or atrioventricular block','Atrial mechanical dysfunction with thromboembolic risk']
for name,obj in [('case_packet.json',p),('ground_truth.json',g),('rubric.json',r)]:write('002',name,obj)

# 003: distinguish preoperative rupture from later sepsis/drug reaction and preserve times.
p=read('003','case_packet.json');g=read('003','ground_truth.json');r=read('003','rubric.json')
for fid in ('lab_011','physical_exam_013'):fact(p,fid)['available_at']='after_procedure:laparotomy'
fact(p,'microbiology_015')['available_at']='followup'
fact(p,'allergies_018')['value']='ICU day 2: pruritus, flushing, wheeze and agitation shortly after meropenem plus fluconazole; a second reaction followed piperacillin–tazobactam re-challenge. The offending component was not established.'
g['source_uncertainties'].extend(['Secondary sepsis and antimicrobial hypersensitivity developed after emergency surgery and are not preoperative diagnostic requirements in this MVP.','The combined drain-culture narrative is delayed follow-up and is not released by the time-zero EHR.'])
g['benchmark_assessment_scope']='Acute presentation through emergency laparotomy and immediate postoperative stabilization. Published later sepsis is a separate source outcome, not required to call the preoperative diagnosis clinically acceptable.'
r['acceptable_diagnoses'].append({'label':'Ruptured continent urinary diversion pouch with intraperitoneal leak or peritonitis before later sepsis is established','conditions':['Recognizes pouch rupture/leak as the acute cause and arranges urgent source control.'],'adjudication':'manual'})
r['critical_diagnoses_to_not_miss']=['Acute urinary reservoir rupture with intraperitoneal leak/peritonitis and need for source control']
r['disposition_acceptability']=[{'category':'surgery','conditions':['Acceptable immediate preoperative destination for urgent laparotomy.']},{'category':'ICU','conditions':['Source-supported immediate postoperative destination after emergency repair.']}]
a=action(r,'a4');a['priority']='recommended';a['phase']='after_procedure';a['trigger_fact_ids']=['procedure_result_012'];a['deadline']='After emergency laparotomy for postoperative monitoring when clinically indicated.'
r['medication_checks']=[x for x in r['medication_checks'] if 'hypersensitivity' not in x['description']]
r['safety_opportunities']=[x for x in r['safety_opportunities'] if 'hypersensitivity' not in x['description']]
r['reviewer_guidance']='Do not penalize lack of day-2 allergy recognition or microbiology during the acute time-zero trajectory; these events are not available until a later phase. Judge immediate source control and perioperative antimicrobial appropriateness separately.'
for x in g['fact_provenance']:
 fid=x['fact_id']
 if fid.startswith(('pmh_','hpi_','physical_exam_004')): loc='PDF p. 1, case presentation'
 elif fid in {'imaging_005','imaging_006','procedure_result_012','physical_exam_013','allergies_018'}: loc='PDF p. 2, case presentation/investigations; allergy sequence also Table 2 on PDF p. 4'
 elif fid.startswith('lab_'): loc='PDF p. 3, Table 1'
 elif fid.startswith('microbiology_'): loc='PDF p. 4, Table 2 and investigations on PDF pp. 2–3'
 else: loc='PDF pp. 1–2 and p. 4, research cfDNA description and Table 2'
 x['source_locators']=[loc]
for name,obj in [('case_packet.json',p),('ground_truth.json',g),('rubric.json',r)]:write('003',name,obj)

# 004: anchor time zero at the second ED visit so prior fluid results are genuinely available.
p=read('004','case_packet.json');g=read('004','ground_truth.json');r=read('004','rubric.json')
p['time_zero']='return_to_ed_days_after_initial_thoracentesis'
p['initial']['chief_complaint']='Recurrent dyspnea days after drainage of a right pleural effusion.'
fact(p,'hpi_001')['value']='Two weeks of dyspnea and cough, briefly improved after an initial thoracentesis removed 1.5 L of milky right pleural fluid; recurrent dyspnea led to an ED return days later. No recent trauma or thoracic surgery.'
fact(p,'physical_exam_003')['value']='At the initial ED visit, tachypnea without hypoxemia and reduced right-sided breath sounds were reported; repeat-visit examination details were not supplied.'
fact(p,'imaging_004')['value']='Imaging at ED return showed recurrent right pleural effusion.'
fact(p,'procedure_result_005')['value']='Repeat thoracentesis on ED return removed 1.2 L of fluid with characteristics similar to the initial milky effusion.'
fact(p,'lab_006')['value']=fact(p,'lab_006')['value'].replace('Pleural fluid:','Initial thoracentesis pleural fluid (available as prior record):')
fact(p,'microbiology_007')['value']='Initial thoracentesis pleural fluid: Gram stain and culture negative.'
g['source_disposition']['category']='unknown'
g['source_uncertainties'].append('The acute ED return is the benchmark time zero. Initial thoracentesis and its fluid studies are prior records; the article does not document a specific inpatient ward disposition for this return.')
r['disposition_acceptability']=[{'category':'ward','conditions':['Acceptable if recurrent symptomatic effusion or malignancy workup requires admission; source unit not specified.']},{'category':'discharge','conditions':['Only if clinically stable with expedited drainage/workup and safe follow-up; requires physician adjudication.']}]
r['critical_diagnoses_to_not_miss']=['Large symptomatic recurrent pleural effusion requiring drainage and etiologic evaluation']
r['reviewer_guidance']='Do not require immediate identification of small cell histology before EBUS tissue is obtained. Pleural fluid studies are from the first visit and available as prior records at the benchmark return visit.'
for fid,loc in [('procedure_result_005','PDF p. 1, second ED visit and repeat thoracentesis'),('lab_006','PDF p. 1, initial thoracentesis and Table 1'),('microbiology_007','PDF p. 1, Table 1')]:provenance(g,fid)['source_locators']=[loc]
for name,obj in [('case_packet.json',p),('ground_truth.json',g),('rubric.json',r)]:write('004',name,obj)

# 005: PET and mutation profile follow tumor sampling, not the initial presentation.
p=read('005','case_packet.json');g=read('005','ground_truth.json');r=read('005','rubric.json')
for fid in ('imaging_012','other_test_013'):fact(p,fid)['available_at']='after_procedure:pleural_biopsy'
g['source_uncertainties'].append('PET staging and BRAF/KIT status follow pleural cytology/biopsy in the report and are gated after biopsy in the MVP.')
r['critical_diagnoses_to_not_miss']=['Malignant pleural effusion requiring tissue diagnosis after an inconclusive initial evaluation']
r['reviewer_guidance']='Before cytology/biopsy, recognizing malignancy and obtaining tissue is clinically appropriate; do not score omission of melanoma histology itself as an early critical safety miss.'
for fid in ('imaging_012','other_test_013'):provenance(g,fid)['source_locators']=['PDF p. 1, post-biopsy staging and molecular characterization']
for name,obj in [('case_packet.json',p),('ground_truth.json',g),('rubric.json',r)]:write('005',name,obj)

# 006: biopsy is conditional, and ward admission is not proven by the case report.
p=read('006','case_packet.json');g=read('006','ground_truth.json');r=read('006','rubric.json')
g['source_disposition']['category']='unknown'
g['source_uncertainties'].append('No explicit ward admission or unit is documented. The report does not describe biochemical exclusion of pheochromocytoma before biopsy.')
r['disposition_acceptability']=[{'category':'ward','conditions':['Acceptable for adrenal crisis risk, unstable patient or initiation of complex therapy; not a documented source unit.']},{'category':'discharge','conditions':['Potentially acceptable only after stability, glucocorticoid replacement, crisis education and reliable endocrine/TB follow-up; clinician review required.']}]
a=action(r,'a3');a['priority']='optional';a['deadline']='Only if tissue result changes management and pheochromocytoma has been appropriately excluded; source biopsy alone does not establish guideline concordance.';a['source_or_guideline_refs']=['source_case','ese_adrenal_incidentaloma_2023']
r['safety_opportunities'].append({'description':'Before adrenal biopsy, assess hormonal activity and exclude pheochromocytoma; if the source does not report this, mark unknown rather than safe by default.','source_or_guideline_refs':['ese_adrenal_incidentaloma_2023'],'adjudication':'manual'})
r['critical_diagnoses_to_not_miss']=['Primary adrenal insufficiency with risk of adrenal crisis']
r['guideline_refs'].append('ese_adrenal_incidentaloma_2023')
for name,obj in [('case_packet.json',p),('ground_truth.json',g),('rubric.json',r)]:write('006',name,obj)

# 009: preoperative CT reported a foreign body, not its biliary-stent identity.
p=read('009','case_packet.json');g=read('009','ground_truth.json');r=read('009','rubric.json')
fact(p,'imaging_006')['value']='CT: multiple small-bowel air–fluid levels and a linear hyperdense intraluminal structure consistent with a foreign body; mechanical obstruction suspected.'
g['source_disposition']['category']='ICU'
g['source_uncertainties'].append('The CT case-presentation description identified a foreign body; the migrated biliary stent identity was established intraoperatively. After surgery the patient was transferred intubated to ICU.')
r['disposition_acceptability']=[{'category':'surgery','conditions':['Appropriate immediate destination from acute evaluation for perforation/peritonitis.']},{'category':'ICU','conditions':['Source-supported postoperative destination after emergency operation, with intubation and respiratory support.']}]
r['critical_diagnoses_to_not_miss']=['Small-bowel obstruction with perforation or peritonitis requiring emergency surgery']
a=action(r,'a3');a['acceptable_tool_calls'].append({'tool':'disposition','code_or_concept':'ICU'});a['deadline']='Surgery is the immediate handoff; ICU is source-supported after operation.'
provenance(g,'imaging_006')['source_locators']=['PDF pp. 1–2, preoperative CT description in case presentation']
for name,obj in [('case_packet.json',p),('ground_truth.json',g),('rubric.json',r)]:write('009',name,obj)

# For all cases, the critical safety target is a syndrome/action available at the tested phase.
for c,critical in {
 '007':['Severe immune-mediated hemolytic anemia with hemodynamic or tissue hypoxia risk'],
 '008':['Acute spinal cord compression from epidural hematoma requiring urgent MRI and neurosurgical assessment'],
 '010':['Ectopic pregnancy with intra-abdominal hemorrhage requiring urgent surgical evaluation'],
}.items():
 r=read(c,'rubric.json');r['critical_diagnoses_to_not_miss']=critical;write(c,'rubric.json',r)
print('Revised cases 001-010; PDFs and source metadata untouched.')
