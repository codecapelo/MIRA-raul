"""Offline study: which cheap JEF signal catches wrong proposals that the triage would have accepted (escaped errors)?

Every v3 encounter transcript up to the doctor's final diagnosis is scored with the three triage questions plus four candidate questions
about unconfirmed or unexplained content. Labels: the Gemini Pro verdict of the diagnosis at triage time (`proposal_correct` for cascade runs,
`judge_correct` for plain v3 arms). Reference diagnoses are never sent to JEF. Output: results/jef_triage_v3.json (cached, resumable).
"""
import csv,glob,json,os,sys,urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
from mira_runner.jef import URL,MODEL,VERIFY_Q
from mira_runner.cascade import transcript
EXTRA={'unexplained':{'type':'noul','instructions':'At least one finding in `conversation` is not explained by `final_diagnosis`.','criteria':{'true':'A reported finding (a sign, an imaging result, a lab value) is left unexplained by the diagnosis.','false':'The diagnosis accounts for every reported finding.'}},
       'unconfirmed':{'type':'noul','instructions':'The key element of `final_diagnosis` (its cause, mechanism or anatomical site) is only inferred and is NOT directly demonstrated by a definitive result in `conversation` (imaging of the lesion, culture, histology, angiography or an operative finding).','criteria':{'true':'The key element is inferred, not demonstrated.','false':'A definitive result in the conversation directly demonstrates the key element.'}},
       'missing_definitive':{'type':'noul','instructions':'A definitive confirmatory study that is relevant to `final_diagnosis` (targeted imaging of the specific lesion, biopsy, culture, angiography, or operative/pathology findings) has not been obtained in `conversation`.','criteria':{'true':'A relevant definitive study has not been obtained.','false':'The relevant definitive studies are already in the conversation.'}},
       'more_specific':{'type':'noul','instructions':'A more specific diagnosis than `final_diagnosis` (naming a precise cause, mechanism or anatomical site) is plausible given the findings in `conversation`.','criteria':{'true':'A more precise diagnosis is plausible.','false':'The diagnosis is already as specific as the findings allow.'}}}
QUESTIONS={**VERIFY_Q,**EXTRA}
MODELDIR={'qwen':'qwen__qwen3.8-max-0902','glm':'z-ai__glm-5'}

def items():
    out=[]
    plain=[('Q3','qwen38_max_0902','qwen'),('Q3J','qwen38_max_0902_jef','qwen'),('Q1','qwen38_max_0902_xf_n1','qwen'),('Q2','qwen38_max_0902_xf_n2','qwen'),('G1','glm5_xf_n1','glm'),('G2','glm5_xf_n2','glm'),
           ('CASV1','glm5_xf_cas_n2','glm')]
    arms=plain+[(f'{c}{r}',f'glm5_xf_imm_{c.lower()}_n2','glm') for c in ('CAS','CASQ') for r in (1,)]
    for name,tag,m in arms:
        for r in (1,2,3):
            csvp=R/f'results/v3_{tag}_run{r}.csv'
            if not csvp.exists():continue
            for row in csv.DictReader(csvp.open()):
                label=row.get('proposal_correct') or row['judge_correct']
                dx=row.get('proposal_dx') or row['dx_agent']
                if label not in ('True','False') or not dx:continue
                f=R/f'runs/v3/{tag}/run{r}/logs/raw/{MODELDIR[m]}/{row["case_id"]}.jsonl'
                ev=[json.loads(l) for l in f.open()];reqs=[e for e in ev if e['event']=='request' and e['role']=='doctor']
                # transcript at the time of the final diagnosis: last doctor request messages (everything before admission)
                conv=transcript(reqs[-1]['payload']['messages'])
                rationale=row['reasoning']
                if row.get('proposal_dx'):
                    adm=[e for e in ev if e['event']=='tool' and e['name']=='admission' and e.get('arguments')]
                    rationale=adm[-1]['arguments'].get('reasoning','') if adm else rationale
                out.append((f'{name}_r{r}_{row["case_id"]}',{'conversation':conv,'final_diagnosis':dx,'final_rationale':rationale},label=='True',row['case_id']))
    return out

def main():
    key=(R/'.secrets/jef.key').read_text().strip();cache=R/'results/jef_triage_v3.json';done=json.loads(cache.read_text()) if cache.exists() else {}
    its=items();todo=[i for i in its if i[0] not in done]
    def one(it):
        body={'model':MODEL,'state':it[1],'questions':QUESTIONS}
        req=urllib.request.Request(URL,json.dumps(body,ensure_ascii=False).encode(),{'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=180) as r:resp=json.load(r)
        with open(R/'runs/fidelity/jef/usage.jsonl','a') as h:h.write(json.dumps({'kind':'triage_study','input_tokens':resp['usage']['input_tokens'],'output_tokens':resp['usage']['output_tokens'],'model':resp['model']})+'\n')
        a={k:round(v['noul'],3) for k,v in resp['answers'].items()};return it[0],{**a,'correct':it[2],'case':it[3]}
    with ThreadPoolExecutor(5) as ex:
        for k,v in ex.map(one,todo):done[k]=v
    cache.write_text(json.dumps(done,indent=1));print(json.dumps({'encounters':len(done),'new':len(todo)}))
if __name__=='__main__':main()
