"""Offline study on saved v3.6 traces (no new encounters): who should write the clinical record, and who should format the physician's speech?

Record: GLM-5 with the instruction alone (OpenRouter, small cost) against Claude Haiku 5.5 (Pro subscription CLI), same source and same prompt.
Both are checked mechanically (structure, citations, numbers, coverage of results, diagnosis) and by Sonnet 5.5 blind to the author (audit and pairwise preference).
Speech: the baseline GLM messages are measured against the format rule without any model; Haiku rewrites them into the format (offline) and Sonnet audits what was added or dropped.
Outputs stay private (runs/note_study*, results/note_study_private*).
  python3 scripts/note_study.py --cases case_001 case_004 ... --stage all
"""
import argparse,glob,json,os,random,statistics as st,sys,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from mira_runner.budget import Ledger
from mira_runner.cli_client import HybridClient
from mira_runner.client import AuditLog
from mira_runner.cascade import parse_json,claude_kw,SONNET
from mira_runner.consult import CLAUDE_FORMAT
from mira_runner.chart_note import source_record,source_text,write_note,check_note,render_note,speech_check,SPEECH_FORMAT
HAIKU='claude-haiku-5-5';GLM='z-ai/glm-5'
VARIANTS=[('glm',GLM),('haiku',HAIKU)]  # --effort X replaces them with a single Haiku variant at that effort (compared with the saved high-effort note)
TRACE=ROOT/'runs/v3/glm5_xf_imm_cas_v32sjeft86a20dsxotswaglc50op5cbam1evxprv_n2/run1/logs/raw/z-ai__glm-5'
OUT=ROOT/'runs/note_study';OUT.mkdir(parents=True,exist_ok=True)
AUDIT=('You audit a clinical record against the SOURCE it was written from. The SOURCE lines are [Sn mm:ss KIND] text. List: "unsupported": statements or numbers of the record that are NOT in the source (quote them briefly); '
       '"contradictions": statements that contradict the source; "omissions": important items of the source missing from the record (abnormal results, key history, the physician\'s own reasoning). '
       'Score 1 to 5: "organization" (clear standard sections, easy to scan), "record_style" (reads like a physician\'s chart, not a chat or an essay), "traceability" (each statement cites the source lines it comes from, and they are the right ones). '
       'Return ONE JSON object: {"unsupported":[str],"contradictions":[str],"omissions":[str],"organization":int,"record_style":int,"traceability":int}.')
PAIR=('Two clinical records, X and Y, were written from the same SOURCE (lines [Sn mm:ss KIND] text). Choose the one a supervising physician would rather have in the chart: fidelity to the source first, then organization and usefulness. '
      'Return ONE JSON object: {"preferred":"X"|"Y"|"tie","reason":str (at most 30 words)}.')
REWRITE=('You reformat ONE message that a physician wrote to a patient. Keep every clinical statement and every question of the original (drop only exact repeats), add nothing new, do not change the meaning or the diagnosis wording. '
         'Use plain words. ORDERS THIS TURN lists the tests ordered in this turn, if any.'+SPEECH_FORMAT+' Return ONE JSON object: {"message": str}.')
SPEECH_AUDIT=('For each pair, ORIGINAL is a physician message and REWRITE its reformatted version. Report what the rewrite ADDED (a clinical statement, question, test or claim not in the original) and what it DROPPED (anything of the original that is missing, except exact repeats). '
              'Return ONE JSON object: {"pairs":[{"id":int,"added":[str],"dropped":[str]}]}.')

def clients():
    cfg=json.loads((ROOT/'config/run1.json').read_text());ledger=Ledger(ROOT/'logs/budget.sqlite',cfg['budget_usd'])
    key=os.getenv('OPENROUTER_API_KEY') or Path(os.getenv('OPENROUTER_KEY_FILE',ROOT/'.secrets/openrouter.key')).read_text().strip()
    return HybridClient(ledger,cfg,key),ledger

def load_events(case):return [json.loads(l) for l in open(TRACE/f'{case}.jsonl')]

def turns(ev):
    """Physician messages sent to the patient (last message of each turn) with the tests ordered in that turn."""
    out=[];orders=[];last=None
    for e in ev:
        if e['event']=='response' and e.get('role')=='doctor':
            m=e['response']['choices'][0]['message'];last=(m.get('content') or '').strip() if not m.get('tool_calls') else last
        elif e['event']=='tool' and e['name']!='admission' and e['name']!='request_physical_exam' and not (e.get('output') or '').startswith('Investigation locked'):
            a=e.get('arguments') or {};orders+=[n for n in (a.get('test_names') or [a.get('study_name')]) if n]
        elif e['event'] in('cli_call','response') and e.get('role')=='patient':
            if last:out.append({'text':last,'orders':orders});last=None;orders=[]
    return out

def stage_notes(case,client,ledger):
    ev=load_events(case);src=source_record(ev);res={}
    for var,model in VARIANTS:
        f=OUT/f'{case}_{var}.json'
        if f.exists():res[var]=json.loads(f.read_text());continue
        log=AuditLog(OUT/'logs'/f'{case}_{var}.jsonl','note_study');t0=time.monotonic()
        note,m,rep=write_note(client,model,src,log,params={'temperature':.2,'top_p':.95} if var=='glm' else {},cli=var.startswith('haiku'))
        d={'case':case,'var':var,'model':model,'latency_s':round(sum(e['latency_s'] for e in log.events() if e['event']=='cli_call') or time.monotonic()-t0,1),'cost_openrouter_usd':round(sum(float(e['response'].get('usage',{}).get('cost') or 0) for e in log.events() if e['event']=='response'),5),'repaired_json':rep,'note':note,'check':check_note(note,[(i,t,k,x) for i,t,k,x in src]),'text':render_note(note)}
        f.write_text(json.dumps(d,ensure_ascii=False,indent=1));res[var]=d
    return src,res

def cj(client,system,user,log,role,cli=True):
    m=client.call(SONNET,[{'role':'system','content':system+CLAUDE_FORMAT},{'role':'user','content':user}],log,role,{},**claude_kw(SONNET,4000));return parse_json(m.get('content') or '')

def stage_audit(case,src,res,client):
    log=AuditLog(OUT/'logs'/f'{case}_audit{TAG}.jsonl','note_study');rng=random.Random(case);s=source_text(src);out={}
    for var in res:
        out[var]=cj(client,AUDIT,'SOURCE:\n'+s+'\n\nRECORD (JSON):\n'+json.dumps(res[var]['note'],ensure_ascii=False),log,'note_audit')
    names=list(res)
    if len(names)==1 and (OUT/f'{case}_haiku.json').exists():res={**res,'haiku':json.loads((OUT/f'{case}_haiku.json').read_text())};names=[names[0],'haiku']
    if len(names)==2:
        order=names[:];rng.shuffle(order)
        pj=cj(client,PAIR,'SOURCE:\n'+s+'\n\nRECORD X:\n'+res[order[0]]['text']+'\n\nRECORD Y:\n'+res[order[1]]['text'],log,'note_pair') or {}
        p=pj.get('preferred');out['pair']={'order':order,'preferred':{'X':order[0],'Y':order[1]}.get(p,'tie'),'reason':pj.get('reason','')}
    return out

def stage_speech(case,client):
    ev=load_events(case);tl=turns(ev);log=AuditLog(OUT/'logs'/f'{case}_speech.jsonl','note_study');rows=[];pairs=[]
    for k,t in enumerate(tl):
        base=speech_check(t['text'],bool(t['orders']));row={'turn':k+1,'baseline':base,'orders':len(t['orders']),'words':len(t['text'].split())}
        if True:
            t0=time.monotonic();m=client.call(HAIKU,[{'role':'system','content':REWRITE+CLAUDE_FORMAT},{'role':'user','content':'ORDERS THIS TURN: '+(', '.join(t['orders']) or 'none')+'\n\nORIGINAL MESSAGE:\n'+t['text']}],log,'speech_rewrite',{},max_tokens=3000)
            rw=(parse_json(m.get('content') or '') or {}).get('message','');row['haiku_latency_s']=round(time.monotonic()-t0,1);row['haiku']=speech_check(rw,bool(t['orders']));row['rewrite']=rw;pairs.append({'id':k+1,'original':t['text'],'rewrite':rw})
        rows.append(row)
    audit=cj(client,SPEECH_AUDIT,json.dumps(pairs,ensure_ascii=False),log,'speech_audit') if pairs else None
    if isinstance(audit,dict):
        by={p.get('id'):p for p in audit.get('pairs',[]) if isinstance(p,dict)}
        for r in rows:r['audit']=by.get(r['turn'])
    return rows

def VARIANTS_NAMES():return [v for v,_ in VARIANTS]
TAG=''
def summarize(notes,audits,speech):
    s={'cases':len(notes)}
    for var in VARIANTS_NAMES():
        c=[n[var]['check'] for n in notes.values()];d=[n[var] for n in notes.values()];a=[audits[k][var] for k in audits if isinstance(audits[k].get(var),dict)]
        s[var]={'json_repaired':sum(bool(x.get('repaired_json')) for x in d),'parsed':sum(x.get('parsed',False) for x in c),'sections_mean':round(st.mean(x.get('sections',0) for x in c),1),'cited_share':round(sum(x.get('cited_statements',0) for x in c)/max(sum(x.get('statements',0) for x in c),1),2),
                'invalid_ids':sum(x.get('invalid_ids',0) for x in c),'numbers_not_in_cited_source':sum(x.get('numbers_not_in_cited_source',0) for x in c),'numbers':sum(x.get('numbers',0) for x in c),
                'results_cited_share':round(sum(x.get('results_cited',0) for x in c)/max(sum(x.get('results_total',0) for x in c),1),2),'dx_overlap_mean':round(st.mean(x.get('dx_overlap') or 0 for x in c),2),'chars_median':st.median(x.get('chars',0) for x in c),
                'latency_s_median':st.median(x['latency_s'] for x in d),'openrouter_usd_per_note':round(st.mean(x['cost_openrouter_usd'] for x in d),5),
                'audit_unsupported':sum(len(x.get('unsupported') or []) for x in a),'audit_contradictions':sum(len(x.get('contradictions') or []) for x in a),'audit_omissions':sum(len(x.get('omissions') or []) for x in a),
                'organization':round(st.mean(x.get('organization',0) for x in a),2) if a else None,'record_style':round(st.mean(x.get('record_style',0) for x in a),2) if a else None,'traceability':round(st.mean(x.get('traceability',0) for x in a),2) if a else None}
    pr=[a['pair']['preferred'] for a in audits.values() if 'pair' in a];s['pairwise']={k:pr.count(k) for k in [v for v,_ in VARIANTS]+(['haiku'] if len(VARIANTS)==1 else [])+['tie']}
    rows=[r for v in speech.values() for r in v]
    if rows:
        s['speech']={'turns':len(rows),'baseline_ok':sum(r['baseline']['ok'] for r in rows),'baseline_plain':sum(r['baseline']['plain'] for r in rows),'baseline_words':sum(r['baseline']['words'] for r in rows),'baseline_questions':sum(r['baseline']['questions'] for r in rows),
                     'haiku_ok':sum(r['haiku']['ok'] for r in rows if 'haiku' in r),'haiku_latency_s_median':st.median(r['haiku_latency_s'] for r in rows if 'haiku' in r),
                     'haiku_added':sum(len((r.get('audit') or {}).get('added') or []) for r in rows),'haiku_dropped':sum(len((r.get('audit') or {}).get('dropped') or []) for r in rows)}
    return s

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cases',nargs='+',required=True);ap.add_argument('--stage',default='all');ap.add_argument('--workers',type=int,default=3);ap.add_argument('--effort',default=None);a=ap.parse_args()
    global VARIANTS,TAG
    if a.effort:
        import mira_runner.cli_client as cc
        if a.stage=='notes':cc.EFFORT=a.effort  # the audit stage keeps the default effort so the auditor is the same for every variant
        VARIANTS=[('haiku_'+a.effort,HAIKU)];TAG='_'+a.effort
    _,ledger=clients();notes={};audits={};speech={};srcs={}
    def work(case):
        out={};client,ledger=clients()
        if a.stage in('all','notes','audit'):
            src,res=stage_notes(case,client,ledger);out['notes']=res;srcs[case]=src
            if a.stage in('all','audit'):out['audit']=stage_audit(case,src,res,client)
        if a.stage in('all','speech'):out['speech']=stage_speech(case,client)
        return case,out
    with ThreadPoolExecutor(a.workers) as ex:
        for case,out in ex.map(work,a.cases):
            if 'notes' in out:notes[case]=out['notes']
            if 'audit' in out:audits[case]=out['audit']
            if 'speech' in out:speech[case]=out['speech']
            print(case,'done',flush=True)
    s=summarize(notes,audits,speech) if notes else {}
    Path(ROOT/f'results/note_study_{a.stage}{TAG}_private.json').write_text(json.dumps({'summary':s,'audits':audits,'speech':speech,'checks':{c:{v:notes[c][v]['check'] for v in notes[c]} for c in notes}},ensure_ascii=False,indent=1))
    print(json.dumps(s,indent=1));print('ledger',ledger.total())
if __name__=='__main__':main()
