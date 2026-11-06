"""JEF as a diagnosis verifier over v3 transcripts (offline, exploratory).

For every v3 encounter, JEF scores three questions about the doctor's final diagnosis given ONLY the conversation and the findings the
doctor saw (never the reference): is it explicitly supported, does it name a specific cause, do unexcluded alternatives remain. The scores are then
compared with the Gemini Pro verdicts to see whether they could trigger escalation to a stronger model. Output: results/jef_verify_v3.json.
"""
import csv,glob,json,os,sys,urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
from mira_runner.jef import URL,MODEL,JefChecker
MARK='[Results of the tests ordered earlier, now available]'
ARMS={'Q3':('qwen38_max_0902','qwen__qwen3.8-max-0902'),'Q3J':('qwen38_max_0902_jef','qwen__qwen3.8-max-0902'),'Q1':('qwen38_max_0902_xf_n1','qwen__qwen3.8-max-0902'),'Q2':('qwen38_max_0902_xf_n2','qwen__qwen3.8-max-0902'),'G1':('glm5_xf_n1','z-ai__glm-5'),'G2':('glm5_xf_n2','z-ai__glm-5')}
Q={'supported':{'type':'noul','instructions':'The `final_diagnosis` is explicitly supported by findings that appear in `conversation`, not merely compatible with them.','criteria':{'true':'Key findings in the conversation point directly to this diagnosis.','false':'The diagnosis rests on assumptions, on findings that are not in the conversation, or is only one of several fitting options.'}},
   'specific_cause':{'type':'noul','instructions':'The `final_diagnosis` names a specific underlying cause or mechanism (for example a drug, an organism, an anatomical origin or a precipitating event), not only a syndrome or a category.','criteria':{'true':'Names the specific cause or mechanism.','false':'Only a syndrome, organ-level problem or broad category.'}},
   'alternatives':{'type':'noul','instructions':'Important alternative diagnoses remain unexcluded: the findings in `conversation` fit another diagnosis as well as or better than `final_diagnosis`.','criteria':{'true':'A credible alternative explains the findings equally well or better.','false':'The findings clearly favor the final diagnosis over alternatives.'}}}

def transcript(path):
    ev=[json.loads(l) for l in open(path)]
    req=[e for e in ev if e['event']=='request' and e['role']=='doctor'][-1]['payload']['messages']
    lines=[]
    for m in req[1:]:
        r=m['role'];t=(m.get('content') or '').strip()
        if r=='user':
            head,_,res=t.partition(MARK)
            lines.append(('Patient/Chart: ' if t.startswith('My primary') else 'Patient: ')+head.strip())
            if res.strip():lines.append('Results now available: '+res.strip())
        elif r=='assistant' and t:lines.append('Doctor: '+t)
        elif r=='tool' and not t.startswith(('Investigation locked','Order placed','Case admitted','Invalid')):lines.append('Result: '+t)
    return '\n'.join(lines)

def main():
    jef=JefChecker(open(R/'.secrets/jef.key').read().strip(),R/'runs/fidelity/jef/usage.jsonl');key=jef.key
    items=[]
    for arm,(tag,mdir) in ARMS.items():
        rows={r['case_id']:r for r in csv.DictReader(open(R/f'results/v3_{tag}_run1.csv'))}
        for case,r in rows.items():
            f=R/f'runs/v3/{tag}/run1/logs/raw/{mdir}/{case}.jsonl'
            items.append((f'{arm}_{case}',{'conversation':transcript(f),'final_diagnosis':r['dx_agent'],'final_rationale':r['reasoning']},r))
    out_path=R/'results/jef_verify_v3.json';done=json.loads(out_path.read_text()) if out_path.exists() else {}
    def one(it):
        if it[0] in done:return it[0],done[it[0]]
        body={'model':MODEL,'state':it[1],'questions':Q}
        req=urllib.request.Request(URL,json.dumps(body,ensure_ascii=False).encode(),{'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=120) as r:resp=json.load(r)
        with open(R/'runs/fidelity/jef/usage.jsonl','a') as h:h.write(json.dumps({'kind':'v3_verify','input_tokens':resp['usage']['input_tokens'],'output_tokens':resp['usage']['output_tokens'],'model':resp['model']})+'\n')
        return it[0],{k:round(v['noul'],3) for k,v in resp['answers'].items()}|{'judge':it[2]['judge_correct']=='True'}
    with ThreadPoolExecutor(5) as ex:res=dict(ex.map(one,items))
    out_path.write_text(json.dumps(res,indent=1));print(json.dumps({'items':len(res),'jef_tokens_total':jef.tokens()}))
if __name__=='__main__':main()
