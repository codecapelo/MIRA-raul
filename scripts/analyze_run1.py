#!/usr/bin/env python3
"""Offline report generator. All inputs read-only; no network/model calls."""
import argparse,csv,hashlib,json,math,sqlite3,statistics
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
MODELS=['openai/gpt-oss-120b','z-ai/glm-4.5-air','z-ai/glm-5','qwen/qwen3.5-397b-a17b','openai/gpt-5.2']
CATEGORY=dict(zip([f'case_{i:03}' for i in range(1,11)],['cardiovascular','cardiovascular','urologic','respiratory_oncology','respiratory_oncology','endocrine_infectious','hematology','neurologic','gastrointestinal','obstetric']))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def judge(s):
 s=str(s).lower().strip();return True if s in ('true','1','correct','yes') else False if s in ('false','0','incorrect','no') else None
def wilson(k,n):
 if not n:return None
 z=1.959963984540054;p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d;return [c-h,c+h]
def quant(v,p):
 v=sorted(v);x=(len(v)-1)*p;i=int(x);return v[i]+(v[min(i+1,len(v)-1)]-v[i])*(x-i)
def stat(v):return {'n':len(v),'median':statistics.median(v),'q1':quant(v,.25),'q3':quant(v,.75)} if v else {'n':0,'median':None,'q1':None,'q3':None}
def score(rows):
 v=[judge(r.get('judge_correct')) for r in rows if judge(r.get('judge_correct')) is not None];return {'completed':len(rows),'judged':len(v),'correct':sum(v),'judge_accuracy':sum(v)/len(v) if v else None,'wilson95':wilson(sum(v),len(v))}
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def main(root):
 report=root/'reports';report.mkdir(exist_ok=True);p=root/'results/run1.csv';raw=list(csv.DictReader(p.open())) if p.exists() else [];rows=[];seen=set();duplicates=[];hashes={str(p.relative_to(root)):sha(p)} if p.exists() else {}
 for r in raw:
  key=(r['case_id'],r['model'])
  if key in seen:duplicates.append(key);continue
  rows.append(r);seen.add(key)
 calls={};malformed=[]
 for log in sorted((root/'logs/raw').glob('**/*.jsonl')):
  hashes[str(log.relative_to(root))]=sha(log)
  for lineno,line in enumerate(log.read_text().splitlines(),1):
   try:e=json.loads(line)
   except json.JSONDecodeError:malformed.append({'file':str(log),'line':lineno});continue
   rid=e.get('request_id')
   if e.get('event')=='request':calls.setdefault(rid,{}).update({'model':e['payload']['model'],'role':e.get('role'),'case_id':log.stem})
   elif e.get('event')=='response':calls.setdefault(rid,{}).update({'usage':e.get('response',{}).get('usage',{})})
 ledger=[];db=root/'logs/budget.sqlite'
 if db.exists():
  con=sqlite3.connect(f'file:{db}?mode=ro',uri=True);con.row_factory=sqlite3.Row;ledger=[dict(r) for r in con.execute('SELECT * FROM calls')];con.close()
  for e in ledger:
   c=calls.setdefault(e['id'],{});m=json.loads(e.get('metadata') or '{}');c.update({'ledger_cost':e['cost'],'ledger_state':e['state']});c.setdefault('role',m.get('role'));c.setdefault('model',m.get('model'))
 actors=defaultdict(lambda:{'calls':0,'known_cost_usd':Decimal(0),'unknown_cost_calls':0,'prompt_tokens':0,'completion_tokens':0,'reasoning_tokens':0})
 for c in calls.values():
  a=actors[c.get('role') or 'unknown'];u=c.get('usage',{});a['calls']+=1;cost=c.get('ledger_cost') if c.get('ledger_cost') is not None else u.get('cost')
  if cost is None:a['unknown_cost_calls']+=1
  else:a['known_cost_usd']+=Decimal(str(cost))
  for k in ('prompt_tokens','completion_tokens'):a[k]+=int(u.get(k,0) or 0)
  a['reasoning_tokens']+=int(u.get('completion_tokens_details',{}).get('reasoning_tokens',0) or 0)
 for a in actors.values():a['known_cost_usd']=str(a['known_cost_usd'])
 model_results=[];projection=[]
 for m in MODELS:
  rr=[r for r in rows if r['model']==m];s={'model':m,'expected':10,**score(rr)};s['categories']={c:score([r for r in rr if CATEGORY.get(r['case_id'])==c]) for c in sorted(set(CATEGORY.values()))};s['usage']={k:stat([float(r[k]) for r in rr if r.get(k)]) for k in ('prompt_tokens','completion_tokens','reasoning_tokens','latency_s')};model_results.append(s)
  pilot=[r for r in rr if r['case_id']=='case_001'];costs=[Decimal(r['cost_usd']) for r in pilot if r.get('cost_usd')];total=sum(costs,Decimal(0));projection.append({'model':m,'pilot_completed':len(pilot),'pilot_cost_usd':str(total) if costs else None,'projected_10x1_usd':str(total*10/len(costs)) if costs else None,'projected_10x5_usd':str(total*50/len(costs)) if costs else None})
 old=root/'legacy/outputs/benchmark/results/frontier_addons_2026-09-29/summaries/frontier_addons_analysis.json';historical={}
 if old.exists():
  d=json.loads(old.read_text());historical={'path':str(old),'sha256':sha(old),'expected_trajectories':d['expected_trajectories'],'observed_terminal_trajectories':d['observed_terminal_trajectories'],'models_original':d['models'],'evaluation_original':d['evaluation'],'physician_review_state_original':d['physician_review_state']}
 expected=[(c.name,m) for c in sorted((root/'cases').glob('case_*')) for m in MODELS]
 result={'schema_version':'1.0.0','completed_rows':len(rows),'expected_rows':len(expected),'missing_pairs':[k for k in expected if k not in seen],'duplicates':duplicates,'malformed_raw_log_lines':malformed,'models':model_results,'actor_breakdown_including_incomplete':dict(actors),'ledger_known_cost_usd':str(sum((Decimal(e['cost']) for e in ledger if e['cost'] is not None),Decimal(0))),'csv_known_cost_usd':str(sum((Decimal(r['cost_usd']) for r in rows if r.get('cost_usd')),Decimal(0))),'unsettled_calls':[{'id':e['id'],'state':e['state'],'reserved':e['reserved'],'known_cost':e['cost']} for e in ledger if e['state']!='settled'],'legacy_lexical_comparison':historical,'physician_review':'pending','input_sha256':hashes,'category_note':'Manually assigned broad descriptive groups, not upstream strata.'}
 write(report/'run1_summary.json',result);proj={'models':projection,'pilot_expected':5,'pilot_completed':sum(x['pilot_completed'] for x in projection),'known_all_calls_usd':result['ledger_known_cost_usd'],'unsettled_calls':result['unsettled_calls'],'assumption':'Linear extrapolation from case001 with patient/judge/matcher included; complexity differs. Projection is not execution authorization.'};write(report/'cost_projection.json',proj)
 if proj['pilot_completed']==5 and not (report/'pilot_cost_projection.json').exists():write(report/'pilot_cost_projection.json',proj)
 lines=['# Run1: julgamento LLM, revisão médica pendente','',f"Completos {len(rows)}/{len(expected)}; ausências e decisões inválidas explicitadas no JSON.",'','| Modelo | Completos | Corretos/julgados | Wilson 95% |','|---|---:|---:|---|']
 for s in model_results:
  ci=s['wilson95'];lines.append(f"| {s['model']} | {s['completed']}/10 | {s['correct']}/{s['judged']} | {f'{ci[0]:.1%}–{ci[1]:.1%}' if ci else 'indisponível'} |")
 lines+=['',f"Custo conhecido ledger: US$ {result['ledger_known_cost_usd']}; CSV completo: US$ {result['csv_known_cost_usd']}. Custos de tentativas incompletas aparecem no detalhamento por ator. Chamadas não liquidadas impedem presumir total final.",'','Mediana/IQR de tokens e latência, intervalos por categoria e pares ausentes estão no JSON. Tokens de raciocínio são subconjunto da conclusão; não somar novamente. Grupos clínicos descritivos possuem denominadores pequenos.','', 'O juiz LLM avalia equivalência diagnóstica. A análise antiga é lexical, com outros modelos, transporte, ferramentas e três repetições. Não há comparação de superioridade clínica. Revisão médica cega pendente. Repetições não são pacientes independentes.']
 if historical:lines+=['',f"Histórico imutável: {historical['observed_terminal_trajectories']}/{historical['expected_trajectories']} trajetórias, métricas originais de todos os modelos preservadas no JSON. Fonte `{old}`, SHA-256 `{historical['sha256']}`."]
 (report/'run1_summary.md').write_text('\n'.join(lines)+'\n');print(json.dumps({'completed':len(rows),'expected':len(expected),'reports':str(report)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);main(p.parse_args().root)
