#!/usr/bin/env python3
"""Lossless partition of frozen public case facts; no clinical inference or API calls."""
import argparse, hashlib, json
from pathlib import Path
NAMES = {
 'inflammation':'Inflammatory markers','coagulation':'Coagulation studies','echo':'Transthoracic echocardiography','coronary_angiography':'Coronary angiography','intravascular_imaging':'Optical coherence tomography and intravascular ultrasound','pericardiocentesis':'Pericardiocentesis','device_exploration':'Cardiac device surgical exploration','blood_cultures':'Blood cultures','ecg':'Electrocardiogram','nt_probnp':'NT-proBNP','troponin':'Troponin','d_dimer':'D-dimer','ctpa':'CT pulmonary angiography','coronary_ct':'Coronary CT','rhc':'Right-heart catheterization','tee':'Transesophageal echocardiography','cardiac_mri':'Cardiac MRI','electrophysiology':'Electrophysiology study','ct_abdomen':'Abdominal CT','ct_chest':'Chest CT','cbc':'Complete blood count','chemistry':'Blood chemistry','inflammation_followup':'Follow-up inflammatory markers','lactate':'Lactate','laparotomy':'Exploratory laparotomy','drain_culture':'Drain fluid culture','urine_culture':'Urine culture','research_cfdna':'Retrospective research microbial cell-free DNA','thoracentesis':'Thoracentesis and fluid examination','pleural_fluid':'Pleural fluid studies','pleural_culture':'Pleural fluid culture','ebus_biopsy':'Endobronchial ultrasound guided biopsy','chest_xray':'Chest radiograph','pleural_biopsy':'Pleural biopsy','pet':'PET imaging','tumor_genetics':'Tumor genetic testing','adrenal_hormones':'ACTH and cortisol','metabolic':'Metabolic blood testing','tspot':'T-SPOT.TB','adrenal_ct':'Adrenal CT','adrenal_ultrasound':'Adrenal ultrasound','adrenal_biopsy':'Adrenal biopsy','adrenal_tb_pcr':'Adrenal tissue tuberculosis PCR','hemoglobin':'Hemoglobin','hemolysis':'Hemolysis studies','blood_film':'Peripheral blood film','dat':'Direct antiglobulin test','blood_panel':'Blood panel','brain_mri':'Brain MRI','spine_mri':'Spinal MRI','hematoma_evacuation':'Spinal surgery','abdominal_xray':'Abdominal radiograph','laparoscopy':'Diagnostic laparoscopy','resection':'Operative resection','pregnancy_test':'Serum hCG','pelvic_ultrasound':'Pelvic ultrasound','pathology':'Surgical pathology'}
def dump(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def convert(root):
 source=root/'legacy/outputs/benchmark/cases'; out=root/'cases'; manifest=[]
 for directory in sorted(source.glob('case_*')):
  packet=json.loads((directory/'case_packet.json').read_text()); gt=json.loads((directory/'ground_truth.json').read_text()); cid=packet['case_id']; dest=out/cid; dest.mkdir(parents=True,exist_ok=True)
  history=[]; observations=[]; edits=[]
  for fact in packet['facts']:
   item={k:fact[k] for k in ('fact_id','domain','value','available_at')}; baseline=fact['available_at']=='time_zero'
   if fact['domain'] in ('pmh','hpi','meds','allergies') and baseline:
    # Historical pre-presentation imaging belongs to the objective record, not patient-agent input.
    if cid=='case_010' and fact['fact_id']=='hpi_001':
     item['value']='Left upper quadrant pain began mildly about eight days earlier. Treated as gastroenteritis without improvement; now worse with nausea and vomiting.'
     observations.append({'fact_id':'hpi_001_prior_ct','domain':'imaging','name':'Prior noncontrast abdominal CT','value':'Initial noncontrast CT showed a 21 × 19 × 10 mm indeterminate lesion.','available_at':'time_zero','prerequisites':[],'source_fact_id':'hpi_001'})
     edits.append({'fact_id':'hpi_001','action':'Split prior objective CT finding from history without removing clinical content.'})
    history.append(item)
   else:
    codes=fact.get('topic_codes',[]); item['name']=' / '.join(NAMES.get(c,c.replace('_',' ').capitalize()) for c in codes) or fact['domain'].replace('_',' ').capitalize()
    gate=fact['available_at']; item['prerequisites']=[] if baseline else [gate]
    item['unavailable_for_immediate_care']=gate=='retrospective'
    observations.append(item)
  patient={'schema_version':'1.0.0','case_id':cid,'initial':packet['initial'],'presenting_complaint':packet['initial']['chief_complaint'],'history_freetext':'\n'.join(f['value'] for f in history),'history_facts':history,'unknown_fields':packet.get('unknown_fields',[])}
  investigation={'schema_version':'1.0.0','case_id':cid,'observations':observations,'temporal_events':packet.get('temporal_events',[]),'availability_policy':'Each observation requires a requested examination/test/procedure. Non-time_zero gates must additionally be satisfied; retrospective results are never available for immediate care. No unreported results may be invented.'}
  reference={'schema_version':'1.0.0','case_id':cid,'correct_diagnosis':gt['published_final_diagnosis']['label'],'ground_truth':gt,'rubric':json.loads((directory/'rubric.json').read_text())}
  hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir() if p.is_file()}
  provenance={'schema_version':'1.0.0','case_id':cid,'source_directory':str(directory),'source_sha256':hashes,'source_metadata_text':(directory/'source_metadata.yaml').read_text(),'fact_provenance':gt.get('fact_provenance',[]),'conversion_edits':edits,'original_fact_count':len(packet['facts']),'history_fact_count':len(history),'observation_count':len(observations),'validation_scope':'Faithful conversion of legacy extracted JSON; no new independent PDF transcription or physician adjudication.'}
  for filename,data in [('patient.json',patient),('investigations.json',investigation),('reference.json',reference),('provenance.json',provenance)]: dump(dest/filename,data)
  original_ids={f['fact_id'] for f in packet['facts']}; new_ids={f['fact_id'] for f in history+observations}; assert original_ids<=new_ids
  for fact in packet['facts']:
   if cid=='case_010' and fact['fact_id']=='hpi_001': continue
   assert next(f for f in history+observations if f['fact_id']==fact['fact_id'])['value']==fact['value']
  manifest.append({'case_id':cid,'history_fact_count':len(history),'observation_count':len(observations),'source_packet_sha256':hashes['case_packet.json']})
 dump(out/'manifest.json',{'schema_version':'1.0.0','cases':manifest}); print(json.dumps(manifest,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]); convert(p.parse_args().root)
