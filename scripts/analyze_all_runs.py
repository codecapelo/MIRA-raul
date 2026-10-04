#!/usr/bin/env python3
"""Offline combined analysis of run1+run2+run3. Read-only inputs; no network/model calls."""
import argparse,csv,hashlib,json,math,random,sqlite3,statistics
from collections import Counter,defaultdict
from decimal import Decimal
from itertools import combinations
from pathlib import Path
CORE=['openai/gpt-oss-120b','z-ai/glm-4.5-air','z-ai/glm-5','qwen/qwen3.5-397b-a17b','openai/gpt-5.2']
EXT='qwen/qwen3.8-max-prime'  # extension model: isolated traces/CSVs, same protocol
MODELS=CORE+[EXT]
RUNS=(1,2,3)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def judge(s):
 s=str(s).strip().lower();return True if s in('true','1') else False if s in('false','0') else None
def wilson(k,n):
 if not n:return None
 z=1.959963984540054;p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d;return [c-h,c+h]
def quant(v,p):
 v=sorted(v);x=(len(v)-1)*p;i=int(x);return v[i]+(v[min(i+1,len(v)-1)]-v[i])*(x-i)
def stat(v):
 v=[float(x) for x in v]
 return {'n':len(v),'median':statistics.median(v),'q1':quant(v,.25),'q3':quant(v,.75)} if v else {'n':0,'median':None,'q1':None,'q3':None}
def fs(s,d=0):return 'n/d' if not s['n'] else f"{s['median']:,.{d}f} [{s['q1']:,.{d}f}; {s['q3']:,.{d}f}]"
def fci(ci):return 'n/d' if not ci else f"{ci[0]:.1%}–{ci[1]:.1%}"
def load(root):
 rows=[];issues=[];cases=sorted(c.name for c in (root/'cases').glob('case_*'))
 for run in RUNS:
  seen=set()
  for src in (root/'results'/f'run{run}.csv',root/'results'/f'qwen38_max_prime_run{run}.csv'):
   for r in csv.DictReader(src.open()):
    k=(r['case_id'],r['model'])
    if k in seen:issues.append(['duplicate',run,list(k)]);continue
    seen.add(k);r['run']=run;r['verdict']=judge(r['judge_correct']);rows.append(r)
  for c in cases:
   for m in MODELS:
    if (c,m) not in seen:issues.append(['missing',run,[c,m]])
 return rows,issues,cases
def score(rr):
 v=[r['verdict'] for r in rr if r['verdict'] is not None];k=sum(v)
 return {'attempts':len(rr),'unjudged':len(rr)-len(v),'judged':len(v),'correct':k,'accuracy':k/len(v) if v else None,'wilson95':wilson(k,len(v))}
def cluster_boot(rr,cases,n=10000,seed=20261004):
 rnd=random.Random(seed);by=defaultdict(list)
 for r in rr:by[r['case_id']].append(r['verdict'])
 vals=[]
 for _ in range(n):
  k=m=0
  for c in (rnd.choice(cases) for _ in cases):
   v=[x for x in by[c] if x is not None];k+=sum(v);m+=len(v)
  if m:vals.append(k/m)
 vals.sort();return [vals[int(.025*len(vals))],vals[int(.975*len(vals))-1]] if vals else None
def trace_stats(root):
 out=defaultdict(lambda:{'doctor_responses':0,'with_logprobs':0});commits=defaultdict(set);providers=defaultdict(set);manifest={}
 for run,clab,d in(('1','1',root/'logs/raw'),('2','2',root/'runs/run2/logs/raw'),('3','3',root/'runs/run3/logs/raw'))+tuple((r,'ext'+r,root/f'runs/qwen38_max_prime/run{r}/logs/raw') for r in '123'):
  for log in sorted(d.glob('*/*.jsonl')):
   manifest[str(log.relative_to(root))]=sha(log);req={};model=log.parent.name.replace('__','/')
   for line in log.read_text().splitlines():
    e=json.loads(line);commits[clab].add(e.get('commit'))
    if e.get('event')=='request':req[e['request_id']]=e.get('role')
    elif e.get('event')=='response' and req.get(e['request_id'])=='doctor':
     ch=(e['response'].get('choices') or [{}])[0];s=out[(run,model)];s['doctor_responses']+=1;s['with_logprobs']+=1 if ch.get('logprobs') else 0
     if e['response'].get('provider'):providers[model].add(e['response']['provider'])
 return out,commits,providers,manifest
def legacy_check(root):
 leg={'checked':0,'mismatch':[],'missing':[]};p=root/'reports/migration_manifest.json'
 if not p.exists():return leg
 man=json.loads(p.read_text());files=man.get('files',man) if isinstance(man,dict) else man
 items=files.items() if isinstance(files,dict) else [(f.get('path'),f.get('sha256')) for f in files if isinstance(f,dict)]
 for path,h in items:
  if isinstance(h,dict):h=h.get('sha256')
  if not isinstance(h,str) or len(h)!=64:continue
  f=root/path
  if not f.exists():leg['missing'].append(str(path));continue
  leg['checked']+=1
  if sha(f)!=h:leg['mismatch'].append(str(path))
 return leg
def main(root,write=True,legacy_root=None):
 rows,issues,cases=load(root);out=root/'reports'
 res={'schema_version':'1.0.0','terminal_rows':len(rows),'expected_rows':len(MODELS)*len(cases)*len(RUNS),'integrity_issues':issues,'physician_review':'pending'}
 per={}
 for m in MODELS:
  rr=[r for r in rows if r['model']==m];mm={'by_run':{run:score([r for r in rr if r['run']==run]) for run in RUNS},'pooled':score(rr),'cluster_bootstrap95':cluster_boot(rr,cases)}
  dist=Counter();stable=full=0;pair=[]
  for c in cases:
   v=[next((r['verdict'] for r in rr if r['case_id']==c and r['run']==run),None) for run in RUNS]
   if None in v:continue
   full+=1;dist[sum(v)]+=1;stable+=sum(v) in(0,3);pair+=[a==b for a,b in combinations(v,2)]
  mm['consistency']={'cases_with_3_judged_runs':full,'correct_count_distribution':{str(k):dist.get(k,0) for k in range(4)},'stable_cases_all_same_verdict':stable,'mean_pairwise_agreement':sum(pair)/len(pair) if pair else None,'note':'Descriptive agreement across repeated judged verdicts; not the original paper ConsistencyDx.'}
  mm['usage']={k:stat([r[k] for r in rr if r.get(k) not in('',None)]) for k in('prompt_tokens','completion_tokens','reasoning_tokens','latency_s','n_turns','n_tool_calls','tool_errors')}
  cc=[Decimal(r['cost_usd']) for r in rr if r.get('cost_usd')];mm['cost_terminal_usd']=str(sum(cc,Decimal(0)));mm['cost_mean_per_encounter_usd']=str(sum(cc,Decimal(0))/len(cc))
  mm['by_run_cost_usd']={run:str(sum((Decimal(r['cost_usd']) for r in rr if r['run']==run and r['cost_usd']),Decimal(0))) for run in RUNS}
  mm['providers_csv']=sorted({r['provider'] for r in rr});per[m]=mm
 res['models']=per
 con=sqlite3.connect(f"file:{root/'logs/budget.sqlite'}?mode=ro",uri=True);led=[dict(zip(('id','state','reserved','cost','metadata'),r)) for r in con.execute('SELECT * FROM calls')];con.close()
 actor=defaultdict(lambda:defaultdict(lambda:[0,Decimal(0)]));total=Decimal(0);states=Counter()
 for e in led:
  states[e['state']]+=1
  if e['cost'] is None:continue
  m=json.loads(e['metadata'] or '{}');log=m.get('log','');run='run2' if '/runs/run2/' in log else 'run3' if '/runs/run3/' in log else 'qwen38_run'+log.split('/runs/qwen38_max_prime/run')[1][0] if '/runs/qwen38_max_prime/run' in log else 'run1_ou_historico'
  a=actor[m.get('role') or 'unknown'][run];a[0]+=1;a[1]+=Decimal(e['cost']);total+=Decimal(e['cost'])
 res['ledger']={'states':dict(states),'total_usd':str(total),'by_actor_and_run':{r:{k:{'calls':v[0],'cost_usd':str(v[1])} for k,v in d.items()} for r,d in actor.items()}}
 snaps=sorted((root/'reports').glob('credits_run23_final_*.json'))
 if snaps:
  last=json.loads(snaps[-1].read_text())['response']['data'];res['account_final']={'total_usage_usd':str(last['total_usage']),'total_credits_usd':str(last['total_credits']),'snapshots':[s.name for s in snaps],'equals_ledger':Decimal(str(last['total_usage']))==total}
 res['terminal_csv_cost_usd']=str(sum((Decimal(r['cost_usd']) for r in rows if r['cost_usd']),Decimal(0)))
 res['cost_by_run_terminal_usd']={run:str(sum((Decimal(r['cost_usd']) for r in rows if r['run']==run and r['cost_usd']),Decimal(0))) for run in RUNS}
 tr,commits,providers,manifest=trace_stats(root)
 res['logprobs_doctor_responses']={f"run{k[0]}|{k[1]}":v for k,v in sorted(tr.items())}
 res['commits_per_run']={f'run{k}':sorted(c for c in v if c) for k,v in sorted(commits.items())};res['providers_in_traces']={k:sorted(v) for k,v in providers.items()}
 def mark(c,m,run):
  r=next((x for x in rows if x['case_id']==c and x['model']==m and x['run']==run),None);return '?' if r is None or r['verdict'] is None else 'Y' if r['verdict'] else 'N'
 res['verdict_triples_run1_run2_run3']={c:{m:''.join(mark(c,m,run) for run in RUNS) for m in MODELS} for c in cases}
 res['pooled_all_models']=score(rows);res['pooled_core5_models']=score([r for r in rows if r['model'] in CORE])
 pr=[Decimal(v) for v in res['cost_by_run_terminal_usd'].values()];mean=sum(pr)/3
 res['projection_5_runs']={'method':'mean terminal cost of the 3 observed runs x 5; excludes invalidated pilot, incomplete attempts and unattributed cost','mean_terminal_cost_per_run_usd':str(mean),'projected_5_runs_terminal_usd':str(mean*5),'additional_2_runs_estimate_usd':str(mean*2),'per_model_projected_5_runs_usd':{m:str(sum((Decimal(v) for v in per[m]['by_run_cost_usd'].values()),Decimal(0))/3*5) for m in MODELS},'not_an_authorization':True}
 res['legacy_verification']=legacy_check(legacy_root or root);res['legacy_verification']['root_checked']=str(legacy_root or root);res['trace_manifest_files']=len(manifest)
 if not write:return res
 (out/'all_runs_summary.json').write_text(json.dumps(res,indent=2,ensure_ascii=False)+'\n')
 ext_m={k:v for k,v in manifest.items() if '/qwen38_max_prime/' in k};core_m={k:v for k,v in manifest.items() if k not in ext_m}
 (out/'final_trace_manifest_runs123.json').write_text(json.dumps({'description':'sha256 of every raw trace used (run1 logs/raw, run2/run3 runs/*/logs/raw)','files':core_m},indent=2)+'\n')
 (out/'final_trace_manifest_qwen38_max_prime.json').write_text(json.dumps({'description':'sha256 of raw traces of qwen/qwen3.8-max-prime (runs/qwen38_max_prime/run*/logs/raw)','files':ext_m},indent=2)+'\n')
 with (root/'results/all_runs.csv').open('w',newline='') as h:
  keys=['run']+[k for k in rows[0] if k not in('run','verdict')];w=csv.DictWriter(h,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(rows)
 (out/'all_runs_summary.md').write_text(render(res)+'\n');(out/'all_runs_cost_projection.md').write_text(render_cost(res)+'\n')
 print(json.dumps({'rows':len(rows),'issues':len(issues),'ledger_total':res['ledger']['total_usd'],'legacy_checked':res['legacy_verification']['checked'],'legacy_mismatch':len(res['legacy_verification']['mismatch']),'legacy_missing':len(res['legacy_verification']['missing'])}))
 return res
def render(res):
 per=res['models'];L=['# Análise combinada: 3 runs, 5 modelos principais + extensão Qwen3.8-max-prime (%d encontros)' % res['terminal_rows'] + '','',
 f"Terminais: {res['terminal_rows']}/{res['expected_rows']}; problemas de integridade: {len(res['integrity_issues'])}. **Julgamento por LLM (Gemini 3.1 Flash-Lite); revisão médica pendente. O juiz não estabelece segurança clínica nem superioridade.** Encontros sem julgamento (falha operacional/sem diagnóstico) são mostrados à parte e não contam como erro nem acerto.","",
 'Repetições do mesmo caso **não são pacientes independentes**: o Wilson sobre os julgamentos agrupados é apenas descritivo e subestima a incerteza; o bootstrap por caso (10 casos, 10 000 reamostragens, semente 20261004) é mostrado como contraste, também descritivo.','',
 '## Placar por modelo','','| Modelo | Run 1 | Run 2 | Run 3 | Agregado (corretos/julgados) | Wilson 95% | Bootstrap por caso 95% | Sem julgamento |','|---|---:|---:|---:|---:|---|---|---:|']
 for m,x in per.items():
  b=[f"{x['by_run'][r]['correct']}/{x['by_run'][r]['judged']}" for r in RUNS];p=x['pooled'];L.append(f"| {m} | {b[0]} | {b[1]} | {b[2]} | {p['correct']}/{p['judged']} ({p['accuracy']:.1%}) | {fci(p['wilson95'])} | {fci(x['cluster_bootstrap95'])} | {p['unjudged']} |")
 a=res['pooled_all_models'];c5=res['pooled_core5_models'];L+=['',f"Todos os 6 modelos: {a['correct']}/{a['judged']} julgados ({a['accuracy']:.1%}); {a['unjudged']} sem julgamento em {a['attempts']} terminais. Cinco modelos principais: {c5['correct']}/{c5['judged']} ({c5['accuracy']:.1%}) em {c5['attempts']} terminais. `qwen/qwen3.8-max-prime` foi adicionado depois (mesmo protocolo e juiz, traces isolados em `runs/qwen38_max_prime/`; parâmetros de amostragem assumidos iguais aos do Qwen3.5).",'','## Consistência entre repetições (descritiva)','','Casos por número de runs corretas, casos estáveis (mesmo veredito nas três runs) e concordância média par a par. Adaptação descritiva; **não** é o ConsistencyDx do artigo.','','| Modelo | 0/3 | 1/3 | 2/3 | 3/3 | Estáveis | Concordância par a par |','|---|---:|---:|---:|---:|---:|---:|']
 for m,x in per.items():
  c=x['consistency'];d=c['correct_count_distribution'];ag=c['mean_pairwise_agreement'];L.append(f"| {m} | {d['0']} | {d['1']} | {d['2']} | {d['3']} | {c['stable_cases_all_same_verdict']}/{c['cases_with_3_judged_runs']} | {f'{ag:.1%}' if ag is not None else 'n/d'} |")
 L+=['','Casos com algum encontro sem julgamento ficam fora desta tabela.','','## Vereditos por caso (run 1, run 2, run 3; Y=correto, N=incorreto, ?=sem julgamento)','','| Caso | '+' | '.join(m.split('/')[-1] for m in MODELS)+' |','|---|'+'---|'*len(MODELS)]
 for c,row in res['verdict_triples_run1_run2_run3'].items():L.append(f"| {c} | "+' | '.join(row[m] for m in MODELS)+' |')
 L+=['','## Custos','',f"Ledger total US$ {res['ledger']['total_usd']} (estados: {res['ledger']['states']})."]
 if 'account_final' in res:L.append(f"Conta OpenRouter (snapshots sem cache finais): uso US$ {res['account_final']['total_usage_usd']}; igual ao ledger: {res['account_final']['equals_ledger']}.")
 L+=[f"Soma dos terminais (CSV) US$ {res['terminal_csv_cost_usd']}; por run: "+', '.join(f"run {k} US$ {v}" for k,v in res['cost_by_run_terminal_usd'].items())+'. A diferença para o ledger vem do piloto invalidado, de tentativas arquivadas/incompletas e do custo não atribuído de chamadas perdidas.','','| Ator | Execução | Chamadas | Custo US$ |','|---|---|---:|---:|']
 for role,d in sorted(res['ledger']['by_actor_and_run'].items()):
  for run,v in sorted(d.items()):L.append(f"| {role} | {run} | {v['calls']} | {v['cost_usd']} |")
 L+=['','`run1_ou_historico` agrega a rodada 1, o piloto invalidado e tentativas incompletas anteriores. `unattributed_interrupted_calls` é a diferença de conta de US$ 0,030653310 de 13 chamadas perdidas por timeout de rede, não atribuível a nenhuma delas individualmente (`reports/run23_timeout_reconciliation.json`).','','| Modelo | Custo terminais US$ | Custo médio/encontro US$ | Prompt mediana [Q1; Q3] | Conclusão | Raciocínio | Latência s | Turnos | Chamadas de ferramenta |','|---|---:|---:|---|---|---|---|---|---|']
 for m,x in per.items():
  u=x['usage'];L.append(f"| {m} | {float(x['cost_terminal_usd']):.4f} | {float(x['cost_mean_per_encounter_usd']):.5f} | {fs(u['prompt_tokens'])} | {fs(u['completion_tokens'])} | {fs(u['reasoning_tokens'])} | {fs(u['latency_s'],1)} | {fs(u['n_turns'],1)} | {fs(u['n_tool_calls'],1)} |")
 L+=['','A latência de encontros retomados após interrupção reflete tempo de parede e deve ser usada com cautela.','','## Parâmetros, provedores, commits e logprobs','',f"Commits por run: {res['commits_per_run']}. Provedores nos traces: {res['providers_in_traces']}.",'','| Execução | Modelo | Respostas do médico | Com logprobs recebidos |','|---|---|---:|---:|']
 for k,v in res['logprobs_doctor_responses'].items():
  r,m=k.split('|');L.append(f"| {r} | {m} | {v['doctor_responses']} | {v['with_logprobs']} |")
 L+=['','Logprobs foram solicitados quando suportados; ausentes ficam marcados como ausentes. Nenhum ProbScore foi calculado ou inventado.','','## Verificações','',f"Hashes legacy conferidos em `{res['legacy_verification']['root_checked']}`: {res['legacy_verification']['checked']}; divergentes: {len(res['legacy_verification']['mismatch'])}; ausentes: {len(res['legacy_verification']['missing'])}. Manifestos de traces: {res['trace_manifest_files']} arquivos no total (`reports/final_trace_manifest_runs123.json` para os 5 modelos principais e `reports/final_trace_manifest_qwen38_max_prime.json` para a extensão).",'','## Limites','','Revisão médica cega pendente. O juiz LLM usa temperatura 1 e pode variar. A comparação com o benchmark histórico lexical (Fase 1) não é equivalente (outros modelos, ferramentas, juiz e transporte). Nenhuma afirmação de acurácia clínica ou superioridade.']
 return '\n'.join(L)
def render_cost(res):
 p=res['projection_5_runs'];L=['# Custos e projeção (runs 1 a 3)','',f"Custo real total (ledger = conta): US$ {res['ledger']['total_usd']}. Terminais por run: "+', '.join(f"run {k} US$ {v}" for k,v in res['cost_by_run_terminal_usd'].items())+'.','',f"Projeção para 5 repetições: média dos terminais observados US$ {float(p['mean_terminal_cost_per_run_usd']):.4f}/run × 5 = US$ {float(p['projected_5_runs_terminal_usd']):.2f} (duas runs adicionais ≈ US$ {float(p['additional_2_runs_estimate_usd']):.2f}). Exclui piloto invalidado, tentativas incompletas e custo não atribuído. **Estimativa, não autorização de nova execução.**",'','| Modelo | Custo médio/encontro US$ | 5 runs projetadas US$ |','|---|---:|---:|']
 for m,x in res['models'].items():L.append(f"| {m} | {float(x['cost_mean_per_encounter_usd']):.5f} | {float(p['per_model_projected_5_runs_usd'][m]):.3f} |")
 return '\n'.join(L)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--dry',action='store_true');ap.add_argument('--legacy-root',type=Path,help='checkout holding git-ignored legacy files (.DS_Store/.pyc) for the full hash check');a=ap.parse_args()
 r=main(a.root.resolve(),write=not a.dry,legacy_root=a.legacy_root.resolve() if a.legacy_root else None)
 if a.dry:print(json.dumps({k:r[k] for k in('terminal_rows','integrity_issues','legacy_verification','trace_manifest_files')},indent=1,default=str))
